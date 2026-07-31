#!/usr/bin/env python3
"""
Claude Code Chat Search — SQLite FTS5 full-text search over session history.

Usage:
    python search_chats.py index              # Build/update index
    python search_chats.py index --include-newsbot  # Also index/keep ai-news-bot noise unflagged

    # --- Поиск чата по ИМЕНИ (как в списке чатов и в /resume) ---
    python search_chats.py titles "юрист"     # Найти чат по его имени (ai-title), выдаёт session_id + resume-команду
    python search_chats.py titles             # Последние чаты с именами

    # --- 3-layer token-aware retrieval (claude-mem pattern) ---
    python search_chats.py search "query"     # Layer 1: compact index (id, date, project, <=2-line snippet) + ИМЯ ЧАТА
    python search_chats.py search "query" --days 30     # Freshness window (default 90 days)
    python search_chats.py search "query" --days 0      # Disable window (search all time)
    python search_chats.py search "query" --after 2026-02-01 --limit 20
    python search_chats.py search "query" --include-newsbot  # Include ai-news-bot noise sessions
    python search_chats.py timeline <msg_id> [--before N] [--after N]  # Layer 2: msgs around an anchor
    python search_chats.py get <id1,id2>      # Layer 3: full text of only those message ids

    python search_chats.py export <session_id>  # Recover full chat as markdown (works for deleted sessions)
    python search_chats.py stats              # Show index stats
    python search_chats.py archive            # Move old sessions to archive/
    python search_chats.py archive-large      # Also archive large files (>20MB, >3 days old)
    python search_chats.py learn "content" "category"  # Save knowledge
    python search_chats.py knowledge "query"  # Search knowledge base
    python search_chats.py knowledge "query" --type code
"""

import json
import sqlite3
import sys
import os
import re
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional

# --- Config ---
PROJECTS_DIR = Path.home() / ".claude" / "projects"
DB_PATH = Path.home() / ".claude" / "chats.db"
ARCHIVE_SUBDIR = "archive"   # e.g. ~/.claude/projects/C--Users-youruser/archive/
ARCHIVE_AGE_DAYS = 90        # Sessions newer than this kept for /resume (owner wants >=90 days visible in the session picker)
ARCHIVE_LARGE_MB = 20        # Size threshold for archive-large command
ARCHIVE_LARGE_DAYS = 3       # Age threshold for archive-large command

SEARCH_DEFAULT_DAYS = 90     # Default freshness window for `search` (0/--after disables)
# Project paths matching these substrings are treated as noise (flagged is_noise=1, hidden from
# search by default). ai-news-bot sessions are ~92.7% pipeline noise. Override with --include-newsbot.
NOISE_PROJECT_PATTERNS = ("ai-news-bot",)


def is_noise_project(project_path: str) -> bool:
    """True if a session's project_path looks like a noise source (e.g. ai-news-bot)."""
    p = (project_path or "").lower()
    return any(pat in p for pat in NOISE_PROJECT_PATTERNS)


def get_db() -> sqlite3.Connection:
    """Get or create SQLite database with FTS5."""
    db = sqlite3.connect(str(DB_PATH), timeout=30)
    db.execute("PRAGMA busy_timeout=30000")  # wait out transient write locks (index/other session)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")

    db.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            project_path TEXT,
            first_prompt TEXT,
            created TEXT,
            modified TEXT,
            message_count INTEGER DEFAULT 0,
            file_size INTEGER DEFAULT 0,
            file_mtime REAL DEFAULT 0,
            indexed_at TEXT
        );

        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            timestamp TEXT,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
            content,
            session_id UNINDEXED,
            role UNINDEXED,
            timestamp UNINDEXED,
            content='messages',
            content_rowid='id',
            tokenize='unicode61'
        );

        -- Triggers to keep FTS in sync
        CREATE TRIGGER IF NOT EXISTS messages_ai AFTER INSERT ON messages BEGIN
            INSERT INTO messages_fts(rowid, content, session_id, role, timestamp)
            VALUES (new.id, new.content, new.session_id, new.role, new.timestamp);
        END;

        CREATE TRIGGER IF NOT EXISTS messages_ad AFTER DELETE ON messages BEGIN
            INSERT INTO messages_fts(messages_fts, rowid, content, session_id, role, timestamp)
            VALUES ('delete', old.id, old.content, old.session_id, old.role, old.timestamp);
        END;
    """)

    # Additive migration: is_noise flag on sessions (default 0). Idempotent — only added if missing.
    # Non-destructive: existing rows keep all data; flag just hides noise from search by default.
    # Fail-open: if the DB is momentarily locked, don't crash read-only commands — the column will
    # be added on a later call, and callers guard with _has_is_noise() before using it.
    cols = [r[1] for r in db.execute("PRAGMA table_info(sessions)").fetchall()]
    if "is_noise" not in cols:
        try:
            db.execute("ALTER TABLE sessions ADD COLUMN is_noise INTEGER DEFAULT 0")
            db.commit()
        except sqlite3.OperationalError as e:
            print(f"[WARN] is_noise migration deferred (DB busy): {e}", file=sys.stderr)

    # Additive migration: ai_title — короткое человекочитаемое имя чата, которое Claude Code
    # генерирует и пишет в JSONL записями {"type":"ai-title","title":"..."}. Именно оно видно
    # в списке чатов и в /resume, поэтому по нему пользователь и ищет сессию.
    if "ai_title" not in cols:
        try:
            db.execute("ALTER TABLE sessions ADD COLUMN ai_title TEXT")
            db.commit()
        except sqlite3.OperationalError as e:
            print(f"[WARN] ai_title migration deferred (DB busy): {e}", file=sys.stderr)

    return db


def _has_is_noise(db: sqlite3.Connection) -> bool:
    """True if the sessions.is_noise column exists (migration may be deferred if DB was locked)."""
    return any(r[1] == "is_noise" for r in db.execute("PRAGMA table_info(sessions)").fetchall())


def _has_ai_title(db: sqlite3.Connection) -> bool:
    """True if the sessions.ai_title column exists (migration may be deferred if DB was locked)."""
    return any(r[1] == "ai_title" for r in db.execute("PRAGMA table_info(sessions)").fetchall())


def parse_jsonl_session(filepath: Path) -> dict:
    """Parse a JSONL session file, extracting messages."""
    session = {
        "session_id": filepath.stem,
        "messages": [],
        "first_prompt": None,
        "ai_title": None,
        "created": None,
        "modified": None,
        "message_count": 0,
    }

    try:
        with open(filepath, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                entry_type = entry.get("type", "")
                timestamp = entry.get("timestamp", "")

                # Короткое имя чата, сгенерированное Claude Code (видно в списке чатов и /resume).
                # Пишется многократно по мере уточнения — последнее выигрывает.
                if entry_type == "ai-title":
                    t = entry.get("title") or entry.get("aiTitle")
                    if t:
                        session["ai_title"] = t.strip()[:200]
                    continue

                # Track timestamps
                if timestamp:
                    if not session["created"]:
                        session["created"] = timestamp
                    session["modified"] = timestamp

                # User messages
                if entry_type == "user":
                    msg = entry.get("message", {})
                    contents = msg.get("content", [])
                    text_parts = []
                    for c in contents:
                        if isinstance(c, dict):
                            if c.get("type") == "text":
                                text_parts.append(c.get("text", ""))
                            elif c.get("type") == "tool_result":
                                # Skip large tool results (file contents etc)
                                result_text = c.get("content", "")
                                if isinstance(result_text, str) and len(result_text) < 500:
                                    text_parts.append(result_text)
                        elif isinstance(c, str):
                            text_parts.append(c)

                    text = "\n".join(text_parts).strip()
                    if text and len(text) > 10:
                        session["messages"].append({
                            "role": "user",
                            "content": text[:5000],  # Cap at 5K chars
                            "timestamp": timestamp,
                        })
                        if not session["first_prompt"]:
                            session["first_prompt"] = text[:200]
                        session["message_count"] += 1

                # Assistant messages (text only, skip tool_use)
                elif entry_type == "assistant":
                    msg = entry.get("message", {})
                    contents = msg.get("content", [])
                    text_parts = []
                    for c in contents:
                        if isinstance(c, dict) and c.get("type") == "text":
                            t = c.get("text", "").strip()
                            if t and len(t) > 20:
                                text_parts.append(t)

                    text = "\n".join(text_parts).strip()
                    if text and len(text) > 20:
                        session["messages"].append({
                            "role": "assistant",
                            "content": text[:10000],  # Cap at 10K chars
                            "timestamp": timestamp,
                        })
                        session["message_count"] += 1

    except Exception as e:
        print(f"  [ERROR] Failed to parse {filepath.name}: {e}")

    return session


def index_sessions(force: bool = False, include_newsbot: bool = False):
    """Index all sessions into SQLite FTS5. Incremental by default.

    Noise filter: sessions whose project_path matches NOISE_PROJECT_PATTERNS (ai-news-bot)
    are flagged is_noise=1 and hidden from `search` by default. Content is still indexed
    (nothing destroyed) so `search --include-newsbot` / `export` keep working.
    Pass include_newsbot=True to keep such sessions unflagged (visible in normal search).
    """
    db = get_db()
    start = time.time()

    # Find all project dirs
    if not PROJECTS_DIR.exists():
        print(f"[ERROR] Projects dir not found: {PROJECTS_DIR}")
        return

    jsonl_files = list(PROJECTS_DIR.rglob("*.jsonl"))
    # Only index main session files (not subagent files in subdirectories)
    main_files = []
    for f in jsonl_files:
        # Main session files are directly in the project dir: projects/PROJECT_NAME/UUID.jsonl
        # Subagent files are in: projects/PROJECT_NAME/UUID/subagents/agent-*.jsonl
        parent_name = f.parent.name
        if "subagent" not in str(f) and "compact" not in f.name:
            main_files.append(f)

    print(f"[INDEX] Found {len(main_files)} session files")

    indexed = 0
    skipped = 0

    for filepath in main_files:
        session_id = filepath.stem
        file_mtime = filepath.stat().st_mtime
        file_size = filepath.stat().st_size

        # Check if already indexed and up to date
        if not force:
            row = db.execute(
                "SELECT file_mtime FROM sessions WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            if row and abs(row[0] - file_mtime) < 1:
                skipped += 1
                continue

        # Parse and index
        session = parse_jsonl_session(filepath)

        if not session["messages"]:
            skipped += 1
            continue

        # Get project path from parent directory structure
        project_path = filepath.parent.name

        # Noise flag: ai-news-bot sessions hidden from search by default (unless override)
        sess_is_noise = 0 if include_newsbot else (1 if is_noise_project(project_path) else 0)

        # Delete old data for this session
        db.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        db.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))

        # Insert session metadata
        db.execute("""
            INSERT INTO sessions (session_id, project_path, first_prompt, ai_title, created, modified,
                                  message_count, file_size, file_mtime, indexed_at, is_noise)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id,
            project_path,
            session["first_prompt"],
            session.get("ai_title"),
            session["created"],
            session["modified"],
            session["message_count"],
            file_size,
            file_mtime,
            datetime.now().isoformat(),
            sess_is_noise,
        ))

        # Insert messages
        for msg in session["messages"]:
            db.execute("""
                INSERT INTO messages (session_id, role, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (session_id, msg["role"], msg["content"], msg["timestamp"]))

        indexed += 1
        if indexed % 20 == 0:
            db.commit()
            print(f"  ... indexed {indexed} sessions")

    db.commit()

    # Non-destructive backfill: flag already-indexed noise sessions that were indexed before this
    # filter existed (or were skipped as up-to-date this run). Only touches the flag, never content.
    flagged = 0
    if not include_newsbot and _has_is_noise(db):
        like_clauses = " OR ".join(["lower(project_path) LIKE ?"] * len(NOISE_PROJECT_PATTERNS))
        like_params = [f"%{p.lower()}%" for p in NOISE_PROJECT_PATTERNS]
        cur = db.execute(
            f"UPDATE sessions SET is_noise = 1 "
            f"WHERE COALESCE(is_noise, 0) = 0 AND ({like_clauses})",
            like_params,
        )
        flagged = cur.rowcount if cur.rowcount and cur.rowcount > 0 else 0
        db.commit()

    elapsed = time.time() - start
    db_size_mb = DB_PATH.stat().st_size / (1024 * 1024) if DB_PATH.exists() else 0
    noise_total = (
        db.execute("SELECT COUNT(*) FROM sessions WHERE is_noise = 1").fetchone()[0]
        if _has_is_noise(db) else 0
    )

    print(f"\n[DONE] Indexed: {indexed}, Skipped (up-to-date): {skipped}")
    print(f"[DONE] Time: {elapsed:.1f}s, DB size: {db_size_mb:.1f} MB")
    if include_newsbot:
        print(f"[NOISE] --include-newsbot: ai-news-bot sessions left unflagged this run.")
    else:
        print(f"[NOISE] Flagged {flagged} new noise session(s); {noise_total} total hidden from search (--include-newsbot to show).")


def _short_project(project_path: str) -> str:
    """Compact a project_path for one-line display."""
    p = project_path or "?"
    if len(p) > 28:
        p = "…" + p[-27:]
    return p


def search(query: str, after: Optional[str] = None, limit: int = 10,
           role: Optional[str] = None, days: int = SEARCH_DEFAULT_DAYS,
           include_newsbot: bool = False):
    """Layer 1 — compact, token-aware index (claude-mem pattern).

    Returns one line per hit: [msg_id] date, project, <=2-line snippet, plus a footer with
    the result count and a rough token estimate (chars/4). Freshness window --days (default 90;
    0 or an explicit --after disables it). Noise sessions (ai-news-bot) hidden unless
    include_newsbot=True. Drill into hits with `timeline <id>` (Layer 2) and `get <ids>` (Layer 3).
    """
    if not DB_PATH.exists():
        print("[ERROR] Index not found. Run: python search_chats.py index")
        return

    db = get_db()

    # Build FTS5 query — escape special characters
    safe_query = re.sub(r'[^\w\s"*]', ' ', query)

    # Freshness window: explicit --after wins; else now-days; days<=0 disables the window.
    if after:
        window_note = f"since {after}"
    elif days and days > 0:
        after = (datetime.now() - timedelta(days=days)).isoformat()
        window_note = f"last {days}d"
    else:
        window_note = "all time"

    title_col = "s.ai_title" if _has_ai_title(db) else "NULL"
    sql = f"""
        SELECT
            m.id,
            m.session_id,
            s.project_path,
            m.role,
            m.timestamp,
            snippet(messages_fts, 0, '>>>', '<<<', '…', 18) as snippet,
            rank,
            {title_col} as ai_title
        FROM messages_fts AS mf
        JOIN messages AS m ON m.id = mf.rowid
        JOIN sessions AS s ON s.session_id = m.session_id
        WHERE messages_fts MATCH ?
    """
    params = [safe_query]

    if not include_newsbot and _has_is_noise(db):
        sql += " AND COALESCE(s.is_noise, 0) = 0"

    if after:
        sql += " AND m.timestamp >= ?"
        params.append(after)

    if role:
        sql += " AND m.role = ?"
        params.append(role)

    sql += """
        ORDER BY rank
        LIMIT ?
    """
    params.append(limit)

    try:
        results = db.execute(sql, params).fetchall()
    except sqlite3.OperationalError as e:
        print(f"[ERROR] Search failed: {e}")
        print(f"[HINT] Try simpler query or use quotes for exact phrase")
        return

    if not results:
        extra = "" if include_newsbot else " (newsbot noise hidden — add --include-newsbot)"
        print(f'No results for "{query}" [{window_note}]{extra}')
        if days and days > 0 and not (after and window_note.startswith("since")):
            print(f'[HINT] Window is last {days}d — widen with --days N (e.g. --days 365) or --days 0 for all time.')
        return

    print(f'\n=== "{query}" — {len(results)} hits [{window_note}] ===\n')

    est_chars = 0
    for mid, sid, proj, role_v, ts, snip, _rank, ai_title in results:
        snip = snip or ""
        est_chars += len(snip)
        role_icon = "[U]" if role_v == "user" else "[A]"
        date_str = (ts or "?")[:10]
        line = snip.replace("\n", " ").strip()
        print(f"[{mid}] {date_str} {role_icon} {_short_project(proj)}  sess:{(sid or '')[:8]}")
        if ai_title:
            # Имя чата как в списке чатов / /resume — по нему проще всего найти сессию глазами
            print(f"    ЧАТ: «{ai_title}»")
        print(f"    {line[:100]}")
        if len(line) > 100:
            print(f"    {line[100:200]}")
        print()

    est_tokens = est_chars // 4
    hidden = "" if include_newsbot else " · newsbot noise hidden"
    print(f"— {len(results)} results · ~{est_tokens} tok (chars/4) · window: {window_note}{hidden}")
    print(f"  drill in: timeline <id> [--before N --after N] · get <id1,id2>   (widen: --days N / --after DATE)")


def _last_ai_title_from_file(filepath: Path, tail_bytes: int = 512 * 1024) -> Optional[str]:
    """Последнее имя чата (ai-title) из JSONL, читая ХВОСТ файла.

    Claude Code переписывает имя по мере разговора, поэтому актуальное — последнее.
    Читаем хвост (файлы сессий бывают по сотне МБ), при неудаче расширяем окно.
    """
    try:
        size = filepath.stat().st_size
    except OSError:
        return None

    for window in (tail_bytes, tail_bytes * 4, size):
        start = max(0, size - window)
        try:
            with open(filepath, "rb") as f:
                f.seek(start)
                chunk = f.read()
        except OSError:
            return None
        text = chunk.decode("utf-8", errors="replace")
        if start:  # первая строка вероятно обрезана
            text = text.split("\n", 1)[-1]
        found = None
        for line in text.split("\n"):
            if '"ai-title"' not in line:
                continue
            try:
                entry = json.loads(line)
            except json.JSONDecodeError:
                continue
            if entry.get("type") == "ai-title":
                t = entry.get("title") or entry.get("aiTitle")
                if t:
                    found = t.strip()[:200]
        if found:
            return found
        if start == 0:
            return None
    return None


def backfill_titles(limit: int = 0, days: int = 0):
    """Проставить sessions.ai_title для уже проиндексированных сессий (без полного реиндекса).

    Полный `index` перечитывает только изменившиеся файлы, поэтому после добавления колонки
    старые сессии остаются без имени. Здесь читаем только хвост каждого JSONL — быстро.
    """
    db = get_db()
    if not _has_ai_title(db):
        print("[ERROR] Нет колонки ai_title.")
        return

    sql = "SELECT session_id, project_path FROM sessions WHERE ai_title IS NULL"
    params: list = []
    if days and days > 0:
        sql += " AND modified >= ?"
        params.append((datetime.now() - timedelta(days=days)).isoformat())
    sql += " ORDER BY modified DESC"
    if limit:
        sql += f" LIMIT {int(limit)}"

    rows = db.execute(sql, params).fetchall()
    print(f"сессий без имени: {len(rows)}")
    done = miss = 0
    for i, (sid, proj) in enumerate(rows, 1):
        fp = PROJECTS_DIR / (proj or "") / f"{sid}.jsonl"
        if not fp.exists():
            alt = list(PROJECTS_DIR.glob(f"**/{sid}.jsonl"))
            if not alt:
                miss += 1
                continue
            fp = alt[0]
        title = _last_ai_title_from_file(fp)
        if title:
            db.execute("UPDATE sessions SET ai_title = ? WHERE session_id = ?", (title, sid))
            done += 1
        else:
            miss += 1
        if i % 500 == 0:
            db.commit()
            print(f"  {i}/{len(rows)} · с именем: {done} · без: {miss}", flush=True)
    db.commit()
    print(f"ГОТОВО: проставлено {done}, без имени {miss}")


def titles(query: str = "", limit: int = 20, days: int = 0, include_newsbot: bool = False):
    """Найти сессию по ИМЕНИ ЧАТА (ai_title) — тому, что видно в списке чатов и в /resume.

    Claude Code пишет короткое имя чата в JSONL записями {"type":"ai-title","title":"..."}
    (многократно, последнее выигрывает). Это самый быстрый способ найти нужный чат глазами:
    поиск по содержимому даёт message-id, а здесь сразу человеческое название + session_id.
    Пустой query = просто последние чаты с именами.
    """
    if not DB_PATH.exists():
        print("[ERROR] Index not found. Run: python search_chats.py index")
        return

    db = get_db()
    if not _has_ai_title(db):
        print("[ERROR] Колонки ai_title нет — выполните: python search_chats.py index --force")
        return

    sql = "SELECT session_id, ai_title, first_prompt, project_path, created, modified, message_count FROM sessions WHERE ai_title IS NOT NULL"
    params = []
    if query:
        sql += " AND (LOWER(ai_title) LIKE ? OR LOWER(COALESCE(first_prompt,'')) LIKE ?)"
        q = f"%{query.lower()}%"
        params += [q, q]
    if not include_newsbot and _has_is_noise(db):
        sql += " AND COALESCE(is_noise, 0) = 0"
    if days and days > 0:
        sql += " AND modified >= ?"
        params.append((datetime.now() - timedelta(days=days)).isoformat())
    sql += " ORDER BY modified DESC LIMIT ?"
    params.append(limit)

    rows = db.execute(sql, params).fetchall()
    if not rows:
        print(f'Чатов с именем по запросу "{query}" не найдено.')
        print('[HINT] Если БД индексировалась до появления ai_title — прогоните: index --force')
        return

    print(f'\n=== Чаты по имени: "{query or "(последние)"}" — {len(rows)} ===\n')
    for sid, title, fp, proj, created, modified, mc in rows:
        span = f"{(created or '')[:10]} → {(modified or '')[:10]}"
        print(f"«{title}»")
        print(f"    {span} · {mc} msg · {_short_project(proj)}")
        print(f"    resume: claude --resume {sid}")
        if fp:
            print(f"    1-й промпт: {fp[:90].replace(chr(10), ' ')}")
        print()


def timeline(anchor_id: int, before: int = 3, after: int = 3):
    """Layer 2 — messages around an anchor message id (same session, chronological order)."""
    if not DB_PATH.exists():
        print("[ERROR] Index not found. Run: python search_chats.py index")
        return

    db = get_db()
    arow = db.execute("SELECT session_id FROM messages WHERE id = ?", (anchor_id,)).fetchone()
    if not arow:
        print(f"[ERROR] No message with id {anchor_id}")
        return
    sid = arow[0]

    rows = db.execute(
        "SELECT id, role, timestamp, content FROM messages WHERE session_id = ? ORDER BY timestamp, id",
        (sid,)
    ).fetchall()

    idx = next((i for i, r in enumerate(rows) if r[0] == anchor_id), None)
    if idx is None:
        print(f"[ERROR] Anchor {anchor_id} not found in session {sid}")
        return

    lo = max(0, idx - before)
    hi = min(len(rows), idx + after + 1)

    meta = db.execute(
        "SELECT project_path, first_prompt FROM sessions WHERE session_id = ?", (sid,)
    ).fetchone()
    proj = meta[0] if meta else "?"

    print(f'\n=== timeline around [{anchor_id}] · sess:{sid[:8]} · {_short_project(proj)} ===')
    print(f'    showing msgs {lo + 1}-{hi} of {len(rows)} (window -{before}/+{after})\n')

    for mid, role_v, ts, content in rows[lo:hi]:
        marker = ">>>" if mid == anchor_id else "   "
        label = "USER" if role_v == "user" else "CLAUDE"
        body = (content or "").replace("\n", " ").strip()
        print(f"{marker} [{mid}] {label} [{(ts or '')[:16]}]")
        print(f"    {body[:400]}{'…' if len(body) > 400 else ''}")
        print()

    print(f"  full text: get <id[,id2]>  ·  whole session: export {sid[:8]}")


def get_messages(id_arg: str):
    """Layer 3 — full text of specific message ids only (comma/space separated)."""
    if not DB_PATH.exists():
        print("[ERROR] Index not found. Run: python search_chats.py index")
        return

    db = get_db()
    tokens = [x for x in re.split(r"[,\s]+", id_arg.strip()) if x]
    parsed = []
    for x in tokens:
        try:
            parsed.append(int(x))
        except ValueError:
            print(f"[WARN] skipping non-numeric id '{x}'")
    if not parsed:
        print("[ERROR] No valid message ids (expected e.g. get 123,456)")
        return

    placeholders = ",".join("?" for _ in parsed)
    rows = db.execute(
        f"SELECT id, session_id, role, timestamp, content FROM messages WHERE id IN ({placeholders})",
        parsed
    ).fetchall()
    by_id = {r[0]: r for r in rows}

    for mid in parsed:
        r = by_id.get(mid)
        if not r:
            print(f"--- [{mid}] NOT FOUND ---\n")
            continue
        _, sid, role_v, ts, content = r
        label = "USER" if role_v == "user" else "CLAUDE"
        print(f"--- [{mid}] {label} · sess:{(sid or '')[:8]} · [{ts}] ---")
        print(content or "")
        print()


def show_stats():
    """Show index statistics."""
    if not DB_PATH.exists():
        print("[ERROR] Index not found. Run: python search_chats.py index")
        return

    db = get_db()

    sessions_count = db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
    messages_count = db.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
    user_msgs = db.execute("SELECT COUNT(*) FROM messages WHERE role='user'").fetchone()[0]
    asst_msgs = db.execute("SELECT COUNT(*) FROM messages WHERE role='assistant'").fetchone()[0]

    oldest = db.execute("SELECT MIN(created) FROM sessions").fetchone()[0]
    newest = db.execute("SELECT MAX(modified) FROM sessions").fetchone()[0]

    db_size = DB_PATH.stat().st_size / (1024 * 1024)

    print(f"""
=== Chat Search Index Stats ===

Sessions:    {sessions_count}
Messages:    {messages_count:,} (user: {user_msgs:,}, assistant: {asst_msgs:,})
Date range:  {(oldest or '?')[:10]} - {(newest or '?')[:10]}
DB size:     {db_size:.1f} MB
DB path:     {DB_PATH}
""")

    # Knowledge stats
    try:
        kcount = db.execute("SELECT COUNT(*) FROM knowledge").fetchone()[0]
        if kcount > 0:
            by_type = db.execute("SELECT type, COUNT(*) FROM knowledge GROUP BY type ORDER BY COUNT(*) DESC").fetchall()
            by_source = db.execute("SELECT source, COUNT(*) FROM knowledge GROUP BY source ORDER BY COUNT(*) DESC").fetchall()
            print(f"Knowledge: {kcount:,} entries")
            print(f"  Types:   {', '.join(f'{t}: {c}' for t, c in by_type)}")
            print(f"  Sources: {', '.join(f'{s}: {c}' for s, c in by_source)}")
            print()
    except Exception:
        pass


def archive_old_sessions():
    """Move old session files to archive/ subdirectory."""
    if not PROJECTS_DIR.exists():
        print("[ERROR] Projects dir not found")
        return

    cutoff = datetime.now() - timedelta(days=ARCHIVE_AGE_DAYS)

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        archive_dir = project_dir / ARCHIVE_SUBDIR
        moved = 0

        for f in project_dir.glob("*.jsonl"):
            mtime = datetime.fromtimestamp(f.stat().st_mtime)
            if mtime < cutoff:
                archive_dir.mkdir(exist_ok=True)
                dest = archive_dir / f.name
                f.rename(dest)
                moved += 1

                # Also move session subdirectory if exists
                session_dir = project_dir / f.stem
                if session_dir.is_dir():
                    dest_dir = archive_dir / f.stem
                    session_dir.rename(dest_dir)

        if moved:
            print(f"[ARCHIVE] {project_dir.name}: moved {moved} sessions to archive/")

    print("[DONE] Old sessions archived. Extension should work now.")
    print(f"[INFO] Sessions newer than {ARCHIVE_AGE_DAYS} days kept in place for /resume.")


def archive_large_sessions(max_size_mb: float = ARCHIVE_LARGE_MB, min_age_days: int = ARCHIVE_LARGE_DAYS):
    """Archive large session files to reduce Extension Host memory pressure."""
    if not PROJECTS_DIR.exists():
        print("[ERROR] Projects dir not found")
        return

    cutoff = datetime.now() - timedelta(days=min_age_days)
    max_bytes = max_size_mb * 1024 * 1024

    for project_dir in PROJECTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        archive_dir = project_dir / ARCHIVE_SUBDIR
        moved = 0
        freed_mb = 0

        for f in project_dir.glob("*.jsonl"):
            stat = f.stat()
            mtime = datetime.fromtimestamp(stat.st_mtime)
            if stat.st_size > max_bytes and mtime < cutoff:
                archive_dir.mkdir(exist_ok=True)
                dest = archive_dir / f.name
                f.rename(dest)
                freed_mb += stat.st_size / (1024 * 1024)
                moved += 1

                session_dir = project_dir / f.stem
                if session_dir.is_dir():
                    dest_dir = archive_dir / f.stem
                    session_dir.rename(dest_dir)

        if moved:
            print(f"[ARCHIVE] {project_dir.name}: moved {moved} large sessions ({freed_mb:.0f} MB freed)")

    print(f"[DONE] Large sessions (>{max_size_mb}MB, >{min_age_days} days old) archived.")
    print("[INFO] Search still works via SQLite index. Use /resume only for recent sessions.")


def save_knowledge(content: str, category: str = "", doc_type: str = "learning"):
    """Save a knowledge entry to the database."""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            type TEXT,
            category TEXT,
            content TEXT NOT NULL,
            created TEXT,
            session_id TEXT,
            extra TEXT
        )
    """)
    db.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
            content, type, category,
            content=knowledge, content_rowid=id
        )
    """)
    now = datetime.now().isoformat()[:19]
    db.execute(
        "INSERT INTO knowledge (source, type, category, content, created) VALUES (?, ?, ?, ?, ?)",
        ("manual", doc_type, category, content, now)
    )
    db.commit()
    print(f"[SAVED] type={doc_type}, category={category}")
    print(f"  {content[:100]}...")


def search_knowledge(query: str, doc_type: str = None, limit: int = 10):
    """Search the knowledge base using FTS5."""
    db = get_db()

    try:
        db.execute("SELECT 1 FROM knowledge LIMIT 1")
    except Exception:
        print("[ERROR] Knowledge table not found. Run migration first.")
        return

    fts_query = query
    where_extra = ""
    params = []

    if doc_type:
        where_extra = "AND k.type = ?"
        params.append(doc_type)

    rows = db.execute(f"""
        SELECT k.id, k.source, k.type, k.category, k.content, k.created,
               snippet(knowledge_fts, 0, '>>>', '<<<', '...', 40) as snip
        FROM knowledge_fts
        JOIN knowledge k ON k.id = knowledge_fts.rowid
        WHERE knowledge_fts MATCH ?
        {where_extra}
        ORDER BY rank
        LIMIT ?
    """, [fts_query] + params + [limit]).fetchall()

    if not rows:
        print(f'No results for "{query}"' + (f" (type={doc_type})" if doc_type else ""))
        return

    print(f'=== Knowledge: "{query}" ({len(rows)} results) ===')
    if doc_type:
        print(f"    Filter: type={doc_type}")
    print()

    for kid, source, ktype, category, content, created, snip in rows:
        date_str = (created or "?")[:10]
        cat_str = f" [{category}]" if category else ""
        print(f"--- [{ktype}]{cat_str} ({source}, {date_str}) ---")
        print(f"  {snip}")
        print()


def export_session(sid_prefix: str, out_path: str = None):
    """Reconstruct a full chat as markdown from the index (works for deleted sessions)."""
    db = get_db()
    rows = db.execute(
        "SELECT session_id, project_path, first_prompt, created, modified, message_count "
        "FROM sessions WHERE session_id LIKE ?", (sid_prefix + "%",)
    ).fetchall()
    if not rows:
        print(f"[ERROR] No session matching '{sid_prefix}'")
        return
    if len(rows) > 1:
        print(f"[ERROR] Ambiguous prefix, {len(rows)} matches:")
        for r in rows[:10]:
            print(f"  {r[0]}  ({r[4][:10]})  {(r[2] or '')[:60]}")
        return

    sid, proj, first_prompt, created, modified, mcount = rows[0]
    msgs = db.execute(
        "SELECT role, timestamp, content FROM messages WHERE session_id = ? ORDER BY timestamp, id",
        (sid,)
    ).fetchall()

    if out_path is None:
        exp_dir = Path.home() / ".claude" / "recovered-chats"
        exp_dir.mkdir(exist_ok=True)
        out_path = exp_dir / f"{(modified or 'unknown')[:10]}_{sid[:8]}.md"
    out_path = Path(out_path)

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Recovered chat {sid}\n\n")
        f.write(f"- **Project:** {proj}\n- **Created:** {created}\n- **Modified:** {modified}\n")
        f.write(f"- **Messages:** {len(msgs)} (indexed of {mcount})\n\n---\n\n")
        for role, ts, content in msgs:
            label = {"user": "USER", "assistant": "CLAUDE"}.get(role, role.upper())
            f.write(f"### {label} [{ts}]\n\n{content}\n\n")

    size_kb = out_path.stat().st_size / 1024
    print(f"[OK] {len(msgs)} messages -> {out_path} ({size_kb:.0f} KB)")


# --- CLI ---
if __name__ == "__main__":
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "index":
        force = "--force" in sys.argv
        include_newsbot = "--include-newsbot" in sys.argv
        index_sessions(force=force, include_newsbot=include_newsbot)

    elif cmd == "search":
        if len(sys.argv) < 3:
            print("Usage: python search_chats.py search \"query\" [--days N] [--after DATE] [--limit N] [--include-newsbot]")
            sys.exit(1)

        query = sys.argv[2]
        after = None
        limit = 10
        days = SEARCH_DEFAULT_DAYS
        include_newsbot = "--include-newsbot" in sys.argv

        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--after" and i + 1 < len(sys.argv):
                after = sys.argv[i + 1]
            if arg == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])

        search(query, after=after, limit=limit, days=days, include_newsbot=include_newsbot)

    elif cmd == "backfill-titles":
        limit, days = 0, 0
        for i, arg in enumerate(sys.argv):
            if arg == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
        backfill_titles(limit=limit, days=days)

    elif cmd == "titles":
        query = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else ""
        limit, days = 20, 0
        include_newsbot = "--include-newsbot" in sys.argv
        for i, arg in enumerate(sys.argv):
            if arg == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
            if arg == "--days" and i + 1 < len(sys.argv):
                days = int(sys.argv[i + 1])
        titles(query, limit=limit, days=days, include_newsbot=include_newsbot)

    elif cmd == "timeline":
        if len(sys.argv) < 3:
            print("Usage: python search_chats.py timeline <msg_id> [--before N] [--after N]")
            sys.exit(1)
        try:
            anchor_id = int(sys.argv[2])
        except ValueError:
            print(f"[ERROR] timeline expects a numeric message id, got '{sys.argv[2]}'")
            sys.exit(1)
        before = 3
        after_n = 3
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--before" and i + 1 < len(sys.argv):
                before = int(sys.argv[i + 1])
            if arg == "--after" and i + 1 < len(sys.argv):
                after_n = int(sys.argv[i + 1])
        timeline(anchor_id, before=before, after=after_n)

    elif cmd == "get":
        if len(sys.argv) < 3:
            print("Usage: python search_chats.py get <id1,id2,...>")
            sys.exit(1)
        get_messages(" ".join(sys.argv[2:]))

    elif cmd == "export":
        if len(sys.argv) < 3:
            print('Usage: python search_chats.py export <session_id_or_prefix> [--out FILE]')
            sys.exit(1)
        out = None
        if "--out" in sys.argv:
            i = sys.argv.index("--out")
            if i + 1 < len(sys.argv):
                out = sys.argv[i + 1]
        export_session(sys.argv[2], out_path=out)

    elif cmd == "stats":
        show_stats()

    elif cmd == "archive":
        archive_old_sessions()

    elif cmd == "archive-large":
        archive_large_sessions()

    elif cmd == "learn":
        if len(sys.argv) < 3:
            print('Usage: python search_chats.py learn "content" ["category"]')
            sys.exit(1)
        content = sys.argv[2]
        category = sys.argv[3] if len(sys.argv) > 3 else ""
        save_knowledge(content, category=category)

    elif cmd == "knowledge":
        if len(sys.argv) < 3:
            print('Usage: python search_chats.py knowledge "query" [--type TYPE] [--limit N]')
            sys.exit(1)
        query = sys.argv[2]
        doc_type = None
        limit = 10
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg == "--type" and i + 1 < len(sys.argv):
                doc_type = sys.argv[i + 1]
            if arg == "--limit" and i + 1 < len(sys.argv):
                limit = int(sys.argv[i + 1])
        search_knowledge(query, doc_type=doc_type, limit=limit)

    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
