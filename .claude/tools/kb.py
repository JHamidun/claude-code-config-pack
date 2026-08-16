#!/usr/bin/env python3
"""
Knowledge Base — local personal search engine.
SQLite FTS5 full-text search across meetings, emails, chats, and more.

Usage:
    python kb.py ingest tldv                 # Index tl;dv transcripts
    python kb.py ingest spark                # Index Spark Mail transcripts
    python kb.py ingest telegram <file.json> # Import Telegram export
    python kb.py ingest outlook [days]       # Index Outlook emails (default: 90 days)
    python kb.py ingest gmail [days]         # Index Gmail emails (default: 90 days)
    python kb.py ingest gcalendar [days]     # Index Google Calendar (default: 365 days)
    python kb.py search "query"              # Search all sources
    python kb.py search "query" --source tldv --after 2025-01-01 --speaker "Name"
    python kb.py stats                       # Index statistics
    python kb.py sources                     # Per-source breakdown
    python kb.py doc <id>                    # Show full document
    python kb.py reindex <source>            # Force re-index
"""

import hashlib
import json
import os
import re
import sqlite3
import sys
import time
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Optional

# --- Config ---
# Пути ниже были прописаны машиной автора и при обезличивании стали литералами
# "${HOME}/…" и "${WORKSPACE}/…". Python таких подстановок не делает (на Windows
# переменной HOME обычно нет вовсе), поэтому база заводилась в каталоге со скобками
# в имени, а транскрипты «не находились» — молча, без единой ошибки. Резолвим сами.
HOME = Path.home()
WORKSPACE = Path(os.environ.get("WORKSPACE") or os.getcwd())
CREDENTIALS_ENV = HOME / ".claude" / ".credentials.master.env"
GOOGLE_TOKEN = HOME / ".claude" / "google_oauth_token.json"

DB_PATH = WORKSPACE / ".claude" / "kb.db"
TLDV_DIR = HOME / "tldv-export" / "transcripts"
SPARK_MESSAGES_DB = Path(os.environ.get("LOCALAPPDATA", "")) / "Spark Desktop/core-data/databases/messages.sqlite"
SPARK_CACHE_DB = Path(os.environ.get("LOCALAPPDATA", "")) / "Spark Desktop/core-data/databases/cache.sqlite"

CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200


# --- HTML parser for Spark ---
class SparkHTMLParser(HTMLParser):
    """Extract text from Spark meeting HTML, preserving speaker/timestamp structure."""

    def __init__(self):
        super().__init__()
        self.sections = []
        self.current_section = None
        self.current_text = []
        self.in_transcript = False
        self.in_summary = False
        self.skip = False

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        name = attrs_dict.get("name", "")
        if name == "meetingTranscriptSparkSection":
            self.in_transcript = True
            self.current_section = "transcript"
        elif name == "meetingSummarySparkSection":
            self.in_summary = True
            self.current_section = "summary"
        if tag in ("style", "script"):
            self.skip = True

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self.skip = False
        if tag in ("p", "div", "li", "h3", "h4", "span") and not self.skip:
            text = "".join(self.current_text).strip()
            if text:
                self.sections.append((self.current_section or "other", text))
            self.current_text = []

    def handle_data(self, data):
        if not self.skip:
            self.current_text.append(data)

    def get_summary(self):
        return "\n".join(text for section, text in self.sections if section == "summary")

    def get_transcript(self):
        return "\n".join(text for section, text in self.sections if section == "transcript")

    def get_all_text(self):
        return "\n".join(text for _, text in self.sections)


def parse_spark_html(html_bytes):
    """Parse Spark meeting HTML blob into summary + transcript text."""
    try:
        html = html_bytes.decode("utf-8")
    except (UnicodeDecodeError, AttributeError):
        return "", ""

    parser = SparkHTMLParser()
    parser.feed(html)
    return parser.get_summary(), parser.get_transcript() or parser.get_all_text()


# --- Database ---
def get_db() -> sqlite3.Connection:
    """Get or create SQLite database with FTS5."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(DB_PATH))
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    db.execute("PRAGMA foreign_keys=ON")

    db.executescript("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            title TEXT NOT NULL,
            date TEXT NOT NULL,
            duration INTEGER,
            participants TEXT,
            extra TEXT,
            content_hash TEXT,
            chunk_count INTEGER DEFAULT 1,
            created_at TEXT NOT NULL,
            UNIQUE(source, source_id)
        );

        CREATE INDEX IF NOT EXISTS idx_documents_source ON documents(source);
        CREATE INDEX IF NOT EXISTS idx_documents_date ON documents(date);

        CREATE TABLE IF NOT EXISTS chunks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doc_id INTEGER NOT NULL,
            chunk_index INTEGER NOT NULL DEFAULT 0,
            content TEXT NOT NULL,
            speaker TEXT,
            timestamp_start TEXT,
            FOREIGN KEY (doc_id) REFERENCES documents(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_chunks_doc_id ON chunks(doc_id);

        CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
            content,
            speaker UNINDEXED,
            doc_id UNINDEXED,
            content='chunks',
            content_rowid='id',
            tokenize='unicode61'
        );

        CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
            INSERT INTO chunks_fts(rowid, content, speaker, doc_id)
            VALUES (new.id, new.content, new.speaker, new.doc_id);
        END;

        CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
            INSERT INTO chunks_fts(chunks_fts, rowid, content, speaker, doc_id)
            VALUES ('delete', old.id, old.content, old.speaker, old.doc_id);
        END;

        CREATE TABLE IF NOT EXISTS ingest_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            run_at TEXT NOT NULL,
            items_total INTEGER DEFAULT 0,
            items_new INTEGER DEFAULT 0,
            items_skipped INTEGER DEFAULT 0,
            items_error INTEGER DEFAULT 0,
            duration_sec REAL DEFAULT 0
        );
    """)
    return db


# --- Chunking ---
def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into chunks at line boundaries with overlap."""
    if len(text) <= chunk_size:
        return [{"text": text, "index": 0, "speaker": None, "ts": None}]

    chunks = []
    lines = text.split("\n")
    current_chunk = []
    current_len = 0
    first_speaker = None
    first_ts = None

    for line in lines:
        line_len = len(line) + 1

        if current_len + line_len > chunk_size and current_chunk:
            chunk_text_str = "\n".join(current_chunk)
            chunks.append({
                "text": chunk_text_str,
                "index": len(chunks),
                "speaker": first_speaker,
                "ts": first_ts,
            })
            # Overlap: keep tail lines
            overlap_lines = []
            overlap_len = 0
            for prev in reversed(current_chunk):
                if overlap_len + len(prev) > overlap:
                    break
                overlap_lines.insert(0, prev)
                overlap_len += len(prev) + 1
            current_chunk = overlap_lines
            current_len = overlap_len
            first_speaker = None
            first_ts = None

        # Parse speaker/timestamp
        ts_match = re.match(r"^(\d{2}:\d{2}:\d{2})\s+(.+?):", line)
        if ts_match:
            if first_ts is None:
                first_ts = ts_match.group(1)
            if first_speaker is None:
                first_speaker = ts_match.group(2)

        current_chunk.append(line)
        current_len += line_len

    if current_chunk:
        chunks.append({
            "text": "\n".join(current_chunk),
            "index": len(chunks),
            "speaker": first_speaker,
            "ts": first_ts,
        })

    return chunks


# --- tl;dv header parsing ---
def parse_tldv_header(text):
    """Parse tl;dv transcript file header."""
    header = {}
    for line in text.split("\n")[:10]:
        line = line.strip()
        if line.startswith("# Date:"):
            header["date"] = line.split(":", 1)[1].strip()
        elif line.startswith("# Meeting ID:"):
            header["meeting_id"] = line.split(":", 1)[1].strip()
        elif line.startswith("# Duration:"):
            dur_str = line.split(":", 1)[1].strip().rstrip("s")
            try:
                header["duration"] = int(float(dur_str))
            except ValueError:
                pass
        elif line.startswith("# ") and "title" not in header:
            # First # line without a colon-prefix key is the title
            candidate = line[2:].strip()
            if ":" not in candidate[:15]:
                header["title"] = candidate
    return header


def extract_tldv_body(text):
    """Extract body (after header) from tl;dv transcript."""
    lines = text.split("\n")
    for i, line in enumerate(lines):
        if re.match(r"^\d{2}:\d{2}:\d{2}\s+", line):
            return "\n".join(lines[i:])
    # Fallback: skip header lines
    for i, line in enumerate(lines):
        if line.strip() == "" and i > 0:
            return "\n".join(lines[i + 1:])
    return text


def extract_participants(text):
    """Extract unique speaker names from transcript."""
    speakers = set()
    for m in re.finditer(r"^\d{2}:\d{2}:\d{2}\s+(.+?):", text, re.MULTILINE):
        name = m.group(1).strip()
        if name and len(name) < 60:
            speakers.add(name)
    return sorted(speakers)


# --- Ingest: tl;dv ---
def ingest_tldv(force=False):
    """Ingest tl;dv transcripts from local export."""
    if not TLDV_DIR.exists():
        print(f"[ERROR] tl;dv directory not found: {TLDV_DIR}")
        return

    db = get_db()
    start = time.time()

    # Load meetings index for fallback metadata
    index_path = TLDV_DIR / "_meetings_index.json"
    meetings_index = {}
    if index_path.exists():
        with open(index_path, "r", encoding="utf-8") as f:
            for m in json.load(f):
                meetings_index[m["id"]] = m

    txt_files = sorted(TLDV_DIR.glob("*.txt"))
    total = len(txt_files)
    new_count = 0
    skipped = 0
    errors = 0

    print(f"[INGEST] tl;dv: {total} files in {TLDV_DIR}")

    for filepath in txt_files:
        try:
            text = filepath.read_text(encoding="utf-8", errors="replace")
            if len(text) < 50:
                skipped += 1
                continue

            header = parse_tldv_header(text)
            source_id = header.get("meeting_id") or filepath.stem
            content_hash = hashlib.md5(text.encode()).hexdigest()

            # Check if already indexed
            existing = db.execute(
                "SELECT id, content_hash FROM documents WHERE source='tldv' AND source_id=?",
                (source_id,),
            ).fetchone()

            if existing and not force:
                if existing[1] == content_hash:
                    skipped += 1
                    continue
                # Content changed — re-index
                db.execute("DELETE FROM chunks WHERE doc_id=?", (existing[0],))
                db.execute("DELETE FROM documents WHERE id=?", (existing[0],))

            # Metadata
            meta = meetings_index.get(source_id, {})
            title = header.get("title") or meta.get("name") or filepath.stem
            date = header.get("date") or (meta.get("date", "")[:10])
            duration = header.get("duration") or int(meta.get("duration", 0))
            body = extract_tldv_body(text)
            participants = extract_participants(body)

            # Insert document
            cursor = db.execute(
                """INSERT INTO documents
                   (source, source_id, title, date, duration, participants, extra, content_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "tldv", source_id, title, date, duration,
                    ", ".join(participants),
                    json.dumps({"filename": filepath.name}),
                    content_hash,
                    datetime.now().isoformat(),
                ),
            )
            doc_id = cursor.lastrowid

            # Chunk and insert
            chunks = chunk_text(body)
            for chunk in chunks:
                db.execute(
                    """INSERT INTO chunks (doc_id, chunk_index, content, speaker, timestamp_start)
                       VALUES (?, ?, ?, ?, ?)""",
                    (doc_id, chunk["index"], chunk["text"], chunk.get("speaker"), chunk.get("ts")),
                )

            db.execute("UPDATE documents SET chunk_count=? WHERE id=?", (len(chunks), doc_id))
            new_count += 1

            if new_count % 50 == 0:
                db.commit()
                print(f"  ... {new_count} indexed")

        except Exception as e:
            print(f"  [ERROR] {filepath.name}: {e}")
            errors += 1

    db.commit()
    elapsed = time.time() - start

    db.execute(
        """INSERT INTO ingest_log (source, run_at, items_total, items_new, items_skipped, items_error, duration_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("tldv", datetime.now().isoformat(), total, new_count, skipped, errors, elapsed),
    )
    db.commit()

    print(f"\n[DONE] tl;dv: {new_count} new, {skipped} skipped, {errors} errors ({elapsed:.1f}s)")


# --- Ingest: Spark ---
def ingest_spark(force=False):
    """Ingest Spark Mail meeting transcripts."""
    if not SPARK_MESSAGES_DB.exists():
        print(f"[ERROR] Spark messages.sqlite not found: {SPARK_MESSAGES_DB}")
        return
    if not SPARK_CACHE_DB.exists():
        print(f"[ERROR] Spark cache.sqlite not found: {SPARK_CACHE_DB}")
        return

    db = get_db()
    start = time.time()

    msg_conn = sqlite3.connect(f"file:///{SPARK_MESSAGES_DB}?mode=ro", uri=True)
    cache_conn = sqlite3.connect(f"file:///{SPARK_CACHE_DB}?mode=ro", uri=True)

    meetings = msg_conn.execute(
        "SELECT summary, startDate, messagePk FROM meetTranscriptEvent ORDER BY startDate"
    ).fetchall()

    total = len(meetings)
    new_count = 0
    skipped = 0
    errors = 0

    print(f"[INGEST] Spark: {total} meetings")

    for summary, start_date, message_pk in meetings:
        try:
            source_id = str(message_pk)

            # Check existing
            existing = db.execute(
                "SELECT id FROM documents WHERE source='spark' AND source_id=?",
                (source_id,),
            ).fetchone()

            if existing and not force:
                skipped += 1
                continue

            # Get HTML content
            row = cache_conn.execute(
                "SELECT data FROM messageBodyHtml WHERE messagePk=?",
                (message_pk,),
            ).fetchone()

            if not row or not row[0]:
                skipped += 1
                continue

            ai_summary, transcript = parse_spark_html(row[0])
            full_text = ""
            if ai_summary:
                full_text += f"[AI Summary]\n{ai_summary}\n\n"
            if transcript:
                full_text += f"[Transcript]\n{transcript}"

            if len(full_text.strip()) < 50:
                skipped += 1
                continue

            content_hash = hashlib.md5(full_text.encode()).hexdigest()

            # Delete old if force
            if existing and force:
                db.execute("DELETE FROM chunks WHERE doc_id=?", (existing[0],))
                db.execute("DELETE FROM documents WHERE id=?", (existing[0],))

            # Date from unix timestamp
            dt = datetime.fromtimestamp(start_date)
            date_str = dt.strftime("%Y-%m-%d")

            title = summary or f"Spark Meeting {date_str}"

            cursor = db.execute(
                """INSERT INTO documents
                   (source, source_id, title, date, duration, participants, extra, content_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "spark", source_id, title, date_str, None,
                    "",
                    json.dumps({"messagePk": message_pk}),
                    content_hash,
                    datetime.now().isoformat(),
                ),
            )
            doc_id = cursor.lastrowid

            chunks = chunk_text(full_text)
            for chunk in chunks:
                db.execute(
                    """INSERT INTO chunks (doc_id, chunk_index, content, speaker, timestamp_start)
                       VALUES (?, ?, ?, ?, ?)""",
                    (doc_id, chunk["index"], chunk["text"], chunk.get("speaker"), chunk.get("ts")),
                )

            db.execute("UPDATE documents SET chunk_count=? WHERE id=?", (len(chunks), doc_id))
            new_count += 1

            if new_count % 50 == 0:
                db.commit()
                print(f"  ... {new_count} indexed")

        except Exception as e:
            print(f"  [ERROR] pk={message_pk}: {e}")
            errors += 1

    db.commit()
    msg_conn.close()
    cache_conn.close()

    elapsed = time.time() - start
    db.execute(
        """INSERT INTO ingest_log (source, run_at, items_total, items_new, items_skipped, items_error, duration_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("spark", datetime.now().isoformat(), total, new_count, skipped, errors, elapsed),
    )
    db.commit()

    print(f"\n[DONE] Spark: {new_count} new, {skipped} skipped, {errors} errors ({elapsed:.1f}s)")


# --- Ingest: Telegram ---
def ingest_telegram(json_path, force=False):
    """Ingest exported Telegram chat JSON."""
    filepath = Path(json_path)
    if not filepath.exists():
        print(f"[ERROR] File not found: {json_path}")
        return

    db = get_db()
    start = time.time()

    with open(filepath, "r", encoding="utf-8") as f:
        messages = json.load(f)

    chat_name = filepath.stem.replace("chat_export_", "").replace("_", " ")

    # Group messages by day for chunking
    days = {}
    for msg in messages:
        text = msg.get("text", "")
        if not text or len(text) < 10:
            continue
        date = msg.get("date", "")[:10]
        if date not in days:
            days[date] = []
        sender = msg.get("sender_name", "Unknown")
        days[date].append(f"{msg.get('date', '')[-5:]} {sender}: {text}")

    total = len(days)
    new_count = 0
    skipped = 0
    errors = 0

    print(f"[INGEST] Telegram: {chat_name} ({len(messages)} messages, {total} days)")

    for date, day_messages in sorted(days.items()):
        try:
            source_id = f"tg_{chat_name}_{date}"
            day_text = "\n".join(day_messages)
            content_hash = hashlib.md5(day_text.encode()).hexdigest()

            existing = db.execute(
                "SELECT id, content_hash FROM documents WHERE source='telegram' AND source_id=?",
                (source_id,),
            ).fetchone()

            if existing and not force:
                if existing[1] == content_hash:
                    skipped += 1
                    continue
                db.execute("DELETE FROM chunks WHERE doc_id=?", (existing[0],))
                db.execute("DELETE FROM documents WHERE id=?", (existing[0],))

            participants = sorted(set(
                m.get("sender_name", "") for m in messages
                if m.get("date", "")[:10] == date and m.get("sender_name")
            ))

            cursor = db.execute(
                """INSERT INTO documents
                   (source, source_id, title, date, duration, participants, extra, content_hash, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    "telegram", source_id,
                    f"{chat_name} — {date}",
                    date, None,
                    ", ".join(participants),
                    json.dumps({"chat": chat_name, "message_count": len(day_messages)}),
                    content_hash,
                    datetime.now().isoformat(),
                ),
            )
            doc_id = cursor.lastrowid

            chunks = chunk_text(day_text)
            for chunk in chunks:
                db.execute(
                    """INSERT INTO chunks (doc_id, chunk_index, content, speaker, timestamp_start)
                       VALUES (?, ?, ?, ?, ?)""",
                    (doc_id, chunk["index"], chunk["text"], chunk.get("speaker"), chunk.get("ts")),
                )

            db.execute("UPDATE documents SET chunk_count=? WHERE id=?", (len(chunks), doc_id))
            new_count += 1

        except Exception as e:
            print(f"  [ERROR] {date}: {e}")
            errors += 1

    db.commit()
    elapsed = time.time() - start

    db.execute(
        """INSERT INTO ingest_log (source, run_at, items_total, items_new, items_skipped, items_error, duration_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("telegram", datetime.now().isoformat(), total, new_count, skipped, errors, elapsed),
    )
    db.commit()

    print(f"\n[DONE] Telegram '{chat_name}': {new_count} new, {skipped} skipped, {errors} errors ({elapsed:.1f}s)")


# --- Ingest: Outlook ---
def ingest_outlook(days=90, force=False):
    """Ingest Outlook emails via Exchange Web Services."""
    try:
        from exchangelib import Credentials, Account, Configuration, DELEGATE, EWSTimeZone, EWSDateTime
    except ImportError:
        print("[ERROR] exchangelib not installed. Run: pip install exchangelib")
        return

    from dotenv import load_dotenv
    load_dotenv(CREDENTIALS_ENV)

    password = os.getenv("EXCHANGE_PASSWORD")
    if not password:
        print("[ERROR] EXCHANGE_PASSWORD not found in credentials")
        return

    db = get_db()
    start = time.time()

    print(f"[INGEST] Outlook: connecting to Exchange...")
    try:
        credentials = Credentials(
            username="your-work-email@company.com",
            password=password,
        )
        config = Configuration(
            server="mail.company.com",
            credentials=credentials,
        )
        account = Account(
            primary_smtp_address="your-work-email@company.com",
            config=config,
            autodiscover=False,
            access_type=DELEGATE,
        )
    except Exception as e:
        print(f"[ERROR] Exchange connection failed: {e}")
        return

    from datetime import timedelta
    cutoff = datetime.now() - timedelta(days=days)
    since = EWSDateTime(cutoff.year, cutoff.month, cutoff.day, tzinfo=EWSTimeZone.localzone())

    print(f"[INGEST] Outlook: fetching emails from last {days} days...")

    total = 0
    new_count = 0
    skipped = 0
    errors = 0

    # Collect all mail folders: main mailbox + archive
    folders_to_scan = []
    for folder in account.msg_folder_root.children:
        try:
            if folder.total_count and folder.total_count > 0:
                folders_to_scan.append(("main", folder.name, folder))
        except Exception:
            pass
    try:
        if account.archive_root:
            for folder in account.archive_root.children:
                try:
                    if folder.total_count and folder.total_count > 0:
                        folders_to_scan.append(("archive", folder.name, folder))
                except Exception:
                    pass
    except Exception as e:
        print(f"  [WARN] Archive not accessible: {e}")

    print(f"  Folders to scan: {len(folders_to_scan)}")
    for loc, name, f in folders_to_scan:
        print(f"    [{loc}] {name}: {f.total_count} items")

    for loc, folder_name, folder in folders_to_scan:
        folder_label = f"[{loc}] {folder_name}"
        try:
            items = folder.filter(datetime_received__gt=since).order_by("-datetime_received")
        except Exception:
            try:
                items = folder.all().order_by("-datetime_received")
            except Exception as e:
                print(f"  [SKIP] {folder_label}: {e}")
                continue

        print(f"  Scanning {folder_label}...")
        for item in items:
            total += 1
            try:
                source_id = item.id or f"outlook_{total}"

                existing = db.execute(
                    "SELECT id FROM documents WHERE source='outlook' AND source_id=?",
                    (source_id,),
                ).fetchone()

                if existing and not force:
                    skipped += 1
                    continue

                sender = ""
                if item.sender:
                    sender = item.sender.email_address or str(item.sender)

                subject = item.subject or "(no subject)"
                body_text = ""
                if item.text_body:
                    body_text = item.text_body[:10000]
                elif item.body:
                    # Strip HTML tags from body
                    body_text = re.sub(r"<[^>]+>", " ", str(item.body))
                    body_text = re.sub(r"\s+", " ", body_text).strip()[:10000]

                if len(body_text) < 20:
                    skipped += 1
                    continue

                dt = item.datetime_received
                date_str = dt.strftime("%Y-%m-%d") if dt else ""

                recipients = []
                if item.to_recipients:
                    recipients = [r.email_address for r in item.to_recipients if r.email_address]

                full_text = f"From: {sender}\nTo: {', '.join(recipients)}\nSubject: {subject}\nDate: {date_str}\n\n{body_text}"
                content_hash = hashlib.md5(full_text.encode()).hexdigest()

                if existing and force:
                    db.execute("DELETE FROM chunks WHERE doc_id=?", (existing[0],))
                    db.execute("DELETE FROM documents WHERE id=?", (existing[0],))

                participants = [sender] + recipients
                participants = [p for p in participants if p]

                cursor = db.execute(
                    """INSERT INTO documents
                       (source, source_id, title, date, duration, participants, extra, content_hash, created_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        "outlook", source_id, subject, date_str, None,
                        ", ".join(participants[:5]),
                        json.dumps({"sender": sender, "has_attachments": bool(item.has_attachments), "folder": folder_name, "location": loc}),
                        content_hash,
                        datetime.now().isoformat(),
                    ),
                )
                doc_id = cursor.lastrowid

                chunks = chunk_text(full_text)
                for chunk in chunks:
                    db.execute(
                        """INSERT INTO chunks (doc_id, chunk_index, content, speaker, timestamp_start)
                           VALUES (?, ?, ?, ?, ?)""",
                        (doc_id, chunk["index"], chunk["text"], sender, None),
                    )

                db.execute("UPDATE documents SET chunk_count=? WHERE id=?", (len(chunks), doc_id))
                new_count += 1

                if new_count % 100 == 0:
                    db.commit()
                    print(f"  ... {new_count} indexed ({total} processed)")

            except Exception as e:
                errors += 1
                if errors <= 3:
                    print(f"  [ERROR] {e}")

        db.commit()
        print(f"    {folder_label}: done")

    db.commit()
    elapsed = time.time() - start

    db.execute(
        """INSERT INTO ingest_log (source, run_at, items_total, items_new, items_skipped, items_error, duration_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("outlook", datetime.now().isoformat(), total, new_count, skipped, errors, elapsed),
    )
    db.commit()

    print(f"\n[DONE] Outlook: {new_count} new, {skipped} skipped, {errors} errors ({elapsed:.1f}s)")


# --- Ingest: Gmail ---
def ingest_gmail(days=90, force=False):
    """Ingest Gmail emails via Google API."""
    try:
        from google.oauth2.credentials import Credentials as GoogleCredentials
        from googleapiclient.discovery import build
    except ImportError:
        print("[ERROR] google-api-python-client not installed.")
        return

    import base64

    token_path = str(GOOGLE_TOKEN)
    if not os.path.exists(token_path):
        print(f"[ERROR] Google OAuth token not found: {token_path}")
        return

    db = get_db()
    start = time.time()

    print(f"[INGEST] Gmail: connecting...")
    with open(token_path, "r") as f:
        token_data = json.load(f)
    creds = GoogleCredentials.from_authorized_user_info(token_data)

    try:
        gmail = build("gmail", "v1", credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"[ERROR] Gmail API build failed: {e}")
        return

    cutoff = datetime.now() - __import__("datetime").timedelta(days=days)
    query = f"after:{cutoff.strftime('%Y/%m/%d')}"

    print(f"[INGEST] Gmail: fetching emails from last {days} days (query: {query})...")

    total = 0
    new_count = 0
    skipped = 0
    errors = 0
    page_token = None

    try:
        while True:
            results = gmail.users().messages().list(
                userId="me", q=query, maxResults=100, pageToken=page_token,
            ).execute()

            messages = results.get("messages", [])
            if not messages:
                break

            for msg_ref in messages:
                total += 1
                try:
                    msg_id = msg_ref["id"]

                    existing = db.execute(
                        "SELECT id FROM documents WHERE source='gmail' AND source_id=?",
                        (msg_id,),
                    ).fetchone()

                    if existing and not force:
                        skipped += 1
                        continue

                    msg = gmail.users().messages().get(
                        userId="me", id=msg_id, format="full",
                    ).execute()

                    headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
                    subject = headers.get("Subject", "(no subject)")
                    sender = headers.get("From", "")
                    date_raw = headers.get("Date", "")
                    to = headers.get("To", "")

                    # Parse date
                    date_str = ""
                    if date_raw:
                        # Try to extract YYYY-MM-DD
                        for fmt in ["%a, %d %b %Y %H:%M:%S", "%d %b %Y %H:%M:%S"]:
                            try:
                                dt = datetime.strptime(date_raw[:25].strip().rstrip(","), fmt)
                                date_str = dt.strftime("%Y-%m-%d")
                                break
                            except ValueError:
                                continue
                        if not date_str:
                            # Fallback: extract from internalDate
                            internal = msg.get("internalDate")
                            if internal:
                                date_str = datetime.fromtimestamp(int(internal) / 1000).strftime("%Y-%m-%d")

                    # Extract body
                    body_text = _extract_gmail_body(msg.get("payload", {}))
                    if len(body_text) < 20:
                        skipped += 1
                        continue

                    full_text = f"From: {sender}\nTo: {to}\nSubject: {subject}\nDate: {date_str}\n\n{body_text[:10000]}"
                    content_hash = hashlib.md5(full_text.encode()).hexdigest()

                    if existing and force:
                        db.execute("DELETE FROM chunks WHERE doc_id=?", (existing[0],))
                        db.execute("DELETE FROM documents WHERE id=?", (existing[0],))

                    # Clean sender for participants
                    sender_clean = re.sub(r"<[^>]+>", "", sender).strip().strip('"')
                    to_clean = re.sub(r"<[^>]+>", "", to).strip().strip('"')

                    cursor = db.execute(
                        """INSERT INTO documents
                           (source, source_id, title, date, duration, participants, extra, content_hash, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            "gmail", msg_id, subject, date_str, None,
                            f"{sender_clean}, {to_clean}"[:200],
                            json.dumps({"sender": sender, "labels": msg.get("labelIds", [])}),
                            content_hash,
                            datetime.now().isoformat(),
                        ),
                    )
                    doc_id = cursor.lastrowid

                    chunks = chunk_text(full_text)
                    for chunk in chunks:
                        db.execute(
                            """INSERT INTO chunks (doc_id, chunk_index, content, speaker, timestamp_start)
                               VALUES (?, ?, ?, ?, ?)""",
                            (doc_id, chunk["index"], chunk["text"], sender_clean, None),
                        )

                    db.execute("UPDATE documents SET chunk_count=? WHERE id=?", (len(chunks), doc_id))
                    new_count += 1

                    if new_count % 100 == 0:
                        db.commit()
                        print(f"  ... {new_count} indexed ({total} processed)")

                except Exception as e:
                    errors += 1
                    if errors <= 3:
                        print(f"  [ERROR] {e}")

            page_token = results.get("nextPageToken")
            if not page_token:
                break

    except Exception as e:
        print(f"[ERROR] Gmail fetch failed: {e}")

    db.commit()
    elapsed = time.time() - start

    db.execute(
        """INSERT INTO ingest_log (source, run_at, items_total, items_new, items_skipped, items_error, duration_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("gmail", datetime.now().isoformat(), total, new_count, skipped, errors, elapsed),
    )
    db.commit()

    print(f"\n[DONE] Gmail: {new_count} new, {skipped} skipped, {errors} errors ({elapsed:.1f}s)")


def _extract_gmail_body(payload):
    """Extract plain text body from Gmail API payload."""
    import base64

    if "body" in payload and payload["body"].get("data"):
        try:
            return base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8")
        except Exception:
            pass

    if "parts" in payload:
        for part in payload["parts"]:
            mime = part.get("mimeType", "")
            if mime == "text/plain" and part.get("body", {}).get("data"):
                try:
                    return base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                except Exception:
                    pass
            # Recurse into multipart
            if "parts" in part:
                result = _extract_gmail_body(part)
                if result:
                    return result

    # Fallback: try HTML and strip tags
    if "parts" in payload:
        for part in payload["parts"]:
            if part.get("mimeType") == "text/html" and part.get("body", {}).get("data"):
                try:
                    html = base64.urlsafe_b64decode(part["body"]["data"]).decode("utf-8")
                    text = re.sub(r"<[^>]+>", " ", html)
                    return re.sub(r"\s+", " ", text).strip()
                except Exception:
                    pass

    return ""


# --- Ingest: Google Calendar ---
def ingest_gcalendar(days=365, force=False):
    """Ingest Google Calendar events."""
    try:
        from google.oauth2.credentials import Credentials as GoogleCredentials
        from googleapiclient.discovery import build
    except ImportError:
        print("[ERROR] google-api-python-client not installed.")
        return

    token_path = str(GOOGLE_TOKEN)
    if not os.path.exists(token_path):
        print(f"[ERROR] Google OAuth token not found: {token_path}")
        return

    db = get_db()
    start = time.time()

    print(f"[INGEST] Google Calendar: connecting...")
    with open(token_path, "r") as f:
        token_data = json.load(f)
    creds = GoogleCredentials.from_authorized_user_info(token_data)

    try:
        calendar = build("calendar", "v3", credentials=creds, cache_discovery=False)
    except Exception as e:
        print(f"[ERROR] Calendar API build failed: {e}")
        return

    cutoff = datetime.now() - __import__("datetime").timedelta(days=days)
    time_min = cutoff.isoformat() + "Z"
    time_max = datetime.now().isoformat() + "Z"

    print(f"[INGEST] Google Calendar: fetching events from last {days} days...")

    total = 0
    new_count = 0
    skipped = 0
    errors = 0
    page_token = None

    try:
        while True:
            results = calendar.events().list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=250,
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token,
            ).execute()

            events = results.get("items", [])
            if not events:
                break

            for event in events:
                total += 1
                try:
                    event_id = event["id"]

                    existing = db.execute(
                        "SELECT id FROM documents WHERE source='gcalendar' AND source_id=?",
                        (event_id,),
                    ).fetchone()

                    if existing and not force:
                        skipped += 1
                        continue

                    summary = event.get("summary", "(no title)")
                    description = event.get("description", "")
                    location = event.get("location", "")

                    start_raw = event.get("start", {})
                    start_dt = start_raw.get("dateTime", start_raw.get("date", ""))
                    end_raw = event.get("end", {})
                    end_dt = end_raw.get("dateTime", end_raw.get("date", ""))

                    date_str = start_dt[:10] if start_dt else ""
                    time_str = start_dt[11:16] if len(start_dt) > 11 else ""
                    end_time = end_dt[11:16] if len(end_dt) > 11 else ""

                    attendees = []
                    if event.get("attendees"):
                        attendees = [
                            a.get("displayName") or a.get("email", "")
                            for a in event["attendees"]
                        ]

                    # Build text
                    parts = [f"Event: {summary}"]
                    if time_str:
                        parts.append(f"Time: {time_str} - {end_time}")
                    if location:
                        parts.append(f"Location: {location}")
                    if attendees:
                        parts.append(f"Attendees: {', '.join(attendees[:10])}")
                    if description:
                        # Strip HTML
                        desc_text = re.sub(r"<[^>]+>", " ", description)
                        desc_text = re.sub(r"\s+", " ", desc_text).strip()
                        parts.append(f"\n{desc_text[:5000]}")

                    full_text = "\n".join(parts)

                    if len(full_text) < 20:
                        skipped += 1
                        continue

                    content_hash = hashlib.md5(full_text.encode()).hexdigest()

                    if existing and force:
                        db.execute("DELETE FROM chunks WHERE doc_id=?", (existing[0],))
                        db.execute("DELETE FROM documents WHERE id=?", (existing[0],))

                    # Duration in seconds
                    duration = None
                    try:
                        if "T" in start_dt and "T" in end_dt:
                            from datetime import datetime as dt_cls
                            s = dt_cls.fromisoformat(start_dt.replace("Z", "+00:00"))
                            e = dt_cls.fromisoformat(end_dt.replace("Z", "+00:00"))
                            duration = int((e - s).total_seconds())
                    except Exception:
                        pass

                    cursor = db.execute(
                        """INSERT INTO documents
                           (source, source_id, title, date, duration, participants, extra, content_hash, created_at)
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            "gcalendar", event_id, summary, date_str, duration,
                            ", ".join(attendees[:5]),
                            json.dumps({"location": location, "status": event.get("status")}),
                            content_hash,
                            datetime.now().isoformat(),
                        ),
                    )
                    doc_id = cursor.lastrowid

                    chunks = chunk_text(full_text)
                    for chunk in chunks:
                        db.execute(
                            """INSERT INTO chunks (doc_id, chunk_index, content, speaker, timestamp_start)
                               VALUES (?, ?, ?, ?, ?)""",
                            (doc_id, chunk["index"], chunk["text"], None, time_str or None),
                        )

                    db.execute("UPDATE documents SET chunk_count=? WHERE id=?", (len(chunks), doc_id))
                    new_count += 1

                except Exception as e:
                    errors += 1
                    if errors <= 3:
                        print(f"  [ERROR] {e}")

            page_token = results.get("nextPageToken")
            if not page_token:
                break

    except Exception as e:
        print(f"[ERROR] Calendar fetch failed: {e}")

    db.commit()
    elapsed = time.time() - start

    db.execute(
        """INSERT INTO ingest_log (source, run_at, items_total, items_new, items_skipped, items_error, duration_sec)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        ("gcalendar", datetime.now().isoformat(), total, new_count, skipped, errors, elapsed),
    )
    db.commit()

    print(f"\n[DONE] Google Calendar: {new_count} new, {skipped} skipped, {errors} errors ({elapsed:.1f}s)")


# --- Search ---
def search_kb(query, source=None, after=None, before=None, speaker=None, limit=10):
    """Search knowledge base using FTS5 with BM25 ranking."""
    if not DB_PATH.exists():
        print("[ERROR] KB not found. Run: python kb.py ingest tldv")
        return

    db = get_db()
    safe_query = re.sub(r'[^\w\s"*]', " ", query)

    sql = """
        SELECT
            d.id,
            d.source,
            d.title,
            d.date,
            d.duration,
            d.participants,
            c.speaker,
            c.timestamp_start,
            snippet(chunks_fts, 0, '>>>', '<<<', '...', 40) as snippet,
            rank
        FROM chunks_fts
        JOIN chunks AS c ON c.id = chunks_fts.rowid
        JOIN documents AS d ON d.id = c.doc_id
        WHERE chunks_fts MATCH ?
    """
    params = [safe_query]

    if source:
        sql += " AND d.source = ?"
        params.append(source)
    if after:
        sql += " AND d.date >= ?"
        params.append(after)
    if before:
        sql += " AND d.date <= ?"
        params.append(before)
    if speaker:
        sql += " AND d.participants LIKE ?"
        params.append(f"%{speaker}%")

    sql += " ORDER BY rank LIMIT ?"
    params.append(limit)

    try:
        results = db.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        print(f"[ERROR] Search failed: {e}")
        print("[HINT] Try simpler query or use quotes for exact phrase")
        return

    if not results:
        print(f'No results for "{query}"')
        return

    # Group by document
    docs_seen = {}
    for row in results:
        doc_id = row[0]
        if doc_id not in docs_seen:
            dur = row[4]
            dur_str = f"{dur // 60} min" if dur else ""
            docs_seen[doc_id] = {
                "source": row[1],
                "title": row[2],
                "date": row[3],
                "duration": dur_str,
                "participants": row[5],
                "snippets": [],
            }
        docs_seen[doc_id]["snippets"].append({
            "speaker": row[6],
            "ts": row[7],
            "text": row[8],
        })

    print(f'\n=== Results for "{query}" ({len(docs_seen)} documents) ===\n')

    source_icons = {"tldv": "tldv", "spark": "spark", "telegram": "tg", "email": "mail", "calendar": "cal"}

    for i, (doc_id, doc) in enumerate(docs_seen.items(), 1):
        icon = source_icons.get(doc["source"], doc["source"])
        dur = f" ({doc['duration']})" if doc["duration"] else ""
        print(f"--- [{i}] [{icon}] {doc['title']} — {doc['date']}{dur}")
        if doc["participants"]:
            parts = doc["participants"]
            if len(parts) > 80:
                parts = parts[:80] + "..."
            print(f"    {parts}")
        for snip in doc["snippets"][:3]:
            ts = f"[{snip['ts']}] " if snip.get("ts") else ""
            text = snip["text"].replace("\n", " ")[:200]
            print(f"    {ts}{text}")
        print()


# --- Stats ---
def show_stats():
    """Show index statistics."""
    if not DB_PATH.exists():
        print("[ERROR] KB not found. Run: python kb.py ingest tldv")
        return

    db = get_db()

    total_docs = db.execute("SELECT COUNT(*) FROM documents").fetchone()[0]
    total_chunks = db.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    oldest = db.execute("SELECT MIN(date) FROM documents").fetchone()[0]
    newest = db.execute("SELECT MAX(date) FROM documents").fetchone()[0]
    db_size = DB_PATH.stat().st_size / (1024 * 1024)

    print(f"""
=== Knowledge Base Stats ===

Documents:   {total_docs:,}
Chunks:      {total_chunks:,}
Date range:  {oldest or '?'} — {newest or '?'}
DB size:     {db_size:.1f} MB
DB path:     {DB_PATH}
""")

    # Per-source
    rows = db.execute("""
        SELECT source, COUNT(*) as docs, SUM(chunk_count) as chunks,
               MIN(date) as earliest, MAX(date) as latest
        FROM documents GROUP BY source ORDER BY docs DESC
    """).fetchall()

    if rows:
        print("Sources:")
        for source, docs, chunks, earliest, latest in rows:
            print(f"  {source:12s}  {docs:5d} docs, {chunks or 0:6d} chunks  ({earliest} — {latest})")
        print()

    # Last ingest runs
    runs = db.execute(
        "SELECT source, run_at, items_new, items_skipped, items_error, duration_sec FROM ingest_log ORDER BY run_at DESC LIMIT 5"
    ).fetchall()

    if runs:
        print("Recent ingests:")
        for source, run_at, items_new, items_skipped, items_error, dur in runs:
            print(f"  {run_at[:16]}  {source:12s}  +{items_new} new, {items_skipped} skip, {items_error} err ({dur:.1f}s)")
        print()


def show_sources():
    """Show per-source breakdown."""
    if not DB_PATH.exists():
        print("[ERROR] KB not found.")
        return

    db = get_db()
    rows = db.execute("""
        SELECT source, COUNT(*) as docs, SUM(chunk_count) as chunks,
               MIN(date) as earliest, MAX(date) as latest
        FROM documents GROUP BY source ORDER BY docs DESC
    """).fetchall()

    if not rows:
        print("No documents indexed yet.")
        return

    print(f"\n{'Source':<12} {'Docs':>6} {'Chunks':>8} {'Earliest':<12} {'Latest':<12}")
    print("-" * 56)
    for source, docs, chunks, earliest, latest in rows:
        print(f"{source:<12} {docs:>6} {chunks or 0:>8} {earliest or '?':<12} {latest or '?':<12}")

    total = sum(r[1] for r in rows)
    total_ch = sum(r[2] or 0 for r in rows)
    print("-" * 56)
    print(f"{'TOTAL':<12} {total:>6} {total_ch:>8}")
    print()


def show_doc(doc_id):
    """Show full document by ID."""
    db = get_db()
    doc = db.execute(
        "SELECT id, source, title, date, duration, participants, extra FROM documents WHERE id=?",
        (doc_id,),
    ).fetchone()

    if not doc:
        print(f"[ERROR] Document #{doc_id} not found.")
        return

    dur = f"{doc[4] // 60} min" if doc[4] else "N/A"
    print(f"\n=== Document #{doc[0]} ===")
    print(f"Source:       {doc[1]}")
    print(f"Title:        {doc[2]}")
    print(f"Date:         {doc[3]}")
    print(f"Duration:     {dur}")
    print(f"Participants: {doc[5] or 'N/A'}")
    print()

    chunks = db.execute(
        "SELECT chunk_index, content, speaker, timestamp_start FROM chunks WHERE doc_id=? ORDER BY chunk_index",
        (doc_id,),
    ).fetchall()

    for idx, content, speaker, ts in chunks:
        if len(chunks) > 1:
            header = f"--- Chunk {idx + 1}/{len(chunks)}"
            if ts:
                header += f" [{ts}]"
            print(header)
        print(content)
        print()


# --- CLI ---
if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "ingest":
        if len(sys.argv) < 3:
            print("Usage: python kb.py ingest <source> [options]")
            print("Sources: tldv, spark, telegram <file.json>")
            sys.exit(1)

        source = sys.argv[2]
        force = "--force" in sys.argv

        if source == "tldv":
            ingest_tldv(force=force)
        elif source == "spark":
            ingest_spark(force=force)
        elif source == "telegram":
            if len(sys.argv) < 4:
                print("Usage: python kb.py ingest telegram <file.json>")
                sys.exit(1)
            ingest_telegram(sys.argv[3], force=force)
        elif source == "outlook":
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 90
            ingest_outlook(days=days, force=force)
        elif source == "gmail":
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 90
            ingest_gmail(days=days, force=force)
        elif source == "gcalendar":
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 365
            ingest_gcalendar(days=days, force=force)
        else:
            print(f"[ERROR] Unknown source: {source}")
            print("Available: tldv, spark, telegram, outlook, gmail, gcalendar")

    elif cmd == "search":
        if len(sys.argv) < 3:
            print('Usage: python kb.py search "query" [--source X] [--after DATE] [--before DATE] [--speaker NAME] [--limit N]')
            sys.exit(1)

        query = sys.argv[2]
        source = None
        after = None
        before = None
        speaker = None
        limit = 10

        args = sys.argv[3:]
        for i, arg in enumerate(args):
            if arg == "--source" and i + 1 < len(args):
                source = args[i + 1]
            elif arg == "--after" and i + 1 < len(args):
                after = args[i + 1]
            elif arg == "--before" and i + 1 < len(args):
                before = args[i + 1]
            elif arg == "--speaker" and i + 1 < len(args):
                speaker = args[i + 1]
            elif arg == "--limit" and i + 1 < len(args):
                limit = int(args[i + 1])

        search_kb(query, source=source, after=after, before=before, speaker=speaker, limit=limit)

    elif cmd == "stats":
        show_stats()

    elif cmd == "sources":
        show_sources()

    elif cmd == "doc":
        if len(sys.argv) < 3:
            print("Usage: python kb.py doc <id>")
            sys.exit(1)
        show_doc(int(sys.argv[2]))

    elif cmd == "reindex":
        if len(sys.argv) < 3:
            print("Usage: python kb.py reindex <source>")
            sys.exit(1)
        source = sys.argv[2]
        if source == "tldv":
            ingest_tldv(force=True)
        elif source == "spark":
            ingest_spark(force=True)
        elif source == "outlook":
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 90
            ingest_outlook(days=days, force=True)
        elif source == "gmail":
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 90
            ingest_gmail(days=days, force=True)
        elif source == "gcalendar":
            days = int(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3].isdigit() else 365
            ingest_gcalendar(days=days, force=True)
        else:
            print(f"[ERROR] Unknown source: {source}")
            print("Available: tldv, spark, telegram, outlook, gmail, gcalendar")

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
