"""
Generic Email CLI (IMAP + SMTP) for Claude Code.

For ANY mailbox that speaks IMAP/SMTP: Yandex, corporate Exchange-IMAP,
Gmail with app-password, Mail.ru, custom hosting, etc.
NOT a replacement for the OAuth-based `gmail` (personal) and `outlook` (work)
skills — use this only for mailboxes those skills do not cover.

Credentials: ~/.claude/.credentials.master.env
Profiles via env prefix MAIL_<PROFILE>_*:
    MAIL_<PROFILE>_IMAP_HOST      e.g. imap.yandex.ru
    MAIL_<PROFILE>_IMAP_PORT      default 993 (SSL)
    MAIL_<PROFILE>_USER           login / email address
    MAIL_<PROFILE>_PASSWORD       password or app-password
    MAIL_<PROFILE>_SMTP_HOST      e.g. smtp.yandex.ru
    MAIL_<PROFILE>_SMTP_PORT      default 465 (465=SSL, 587=STARTTLS)
    MAIL_<PROFILE>_FROM           optional From address (default: USER)

Default profile name: DEFAULT (i.e. MAIL_DEFAULT_IMAP_HOST, ...).
Select with --profile <name> (case-insensitive).

Stdlib only: imaplib / smtplib / email. No external dependencies.

Usage examples:
    python email_client.py profiles
    python email_client.py list --limit 10 --unseen
    python email_client.py read 4321
    python email_client.py search "invoice" --since 2026-07-01
    python email_client.py send user@example.com "Subject" "Body" --attach report.pdf
    python email_client.py reply 4321 "Thanks, received."
    python email_client.py download-attachments 4321 --out C:/temp
"""

import argparse
import email as email_lib
import imaplib
import io
import json
import os
import re
import smtplib
import ssl
import sys
import uuid
from datetime import datetime
from email.header import decode_header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, parseaddr
from email import encoders
from pathlib import Path

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_env():
    env_path = Path.home() / ".claude" / ".credentials.master.env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = value


load_env()

DOWNLOAD_DIR = str(Path.home() / ".claude" / "mail_downloads")

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


# ========== PROFILES ==========

class Profile:
    def __init__(self, name):
        self.name = name.upper()
        p = f"MAIL_{self.name}_"
        self.imap_host = os.environ.get(p + "IMAP_HOST", "")
        self.imap_port = int(os.environ.get(p + "IMAP_PORT", "993"))
        self.user = os.environ.get(p + "USER", "")
        self.password = os.environ.get(p + "PASSWORD", "")
        self.smtp_host = os.environ.get(p + "SMTP_HOST", "")
        self.smtp_port = int(os.environ.get(p + "SMTP_PORT", "465"))
        self.from_addr = os.environ.get(p + "FROM", "") or self.user

    def require_imap(self):
        missing = []
        if not self.imap_host:
            missing.append(f"MAIL_{self.name}_IMAP_HOST")
        if not self.user:
            missing.append(f"MAIL_{self.name}_USER")
        if not self.password:
            missing.append(f"MAIL_{self.name}_PASSWORD")
        if missing:
            die_missing(missing, self.name)

    def require_smtp(self):
        missing = []
        if not self.smtp_host:
            missing.append(f"MAIL_{self.name}_SMTP_HOST")
        if not self.user:
            missing.append(f"MAIL_{self.name}_USER")
        if not self.password:
            missing.append(f"MAIL_{self.name}_PASSWORD")
        if missing:
            die_missing(missing, self.name)


def die_missing(missing, profile_name):
    print(f"ERROR: profile '{profile_name}' is not configured.")
    print("Add these lines to ~/.claude/.credentials.master.env:")
    for m in missing:
        print(f"  {m}=...")
    others = discover_profiles()
    if others:
        print(f"Configured profiles: {', '.join(others)}")
    sys.exit(2)


def discover_profiles():
    """Find all MAIL_<PROFILE>_IMAP_HOST env vars."""
    names = []
    for key in os.environ:
        m = re.match(r"^MAIL_([A-Z0-9]+)_IMAP_HOST$", key)
        if m:
            names.append(m.group(1))
    return sorted(names)


# ========== CONNECTIONS ==========

def imap_connect(prof, folder="INBOX", readonly=False):
    prof.require_imap()
    try:
        imap = imaplib.IMAP4_SSL(prof.imap_host, prof.imap_port, timeout=30)
    except Exception as e:
        print(f"ERROR: cannot connect to IMAP {prof.imap_host}:{prof.imap_port} — {e}")
        print("Check MAIL_%s_IMAP_HOST / _IMAP_PORT (993 = SSL standard)." % prof.name)
        sys.exit(1)
    try:
        imap.login(prof.user, prof.password)
    except imaplib.IMAP4.error as e:
        print(f"ERROR: IMAP login failed for {prof.user}: {e}")
        print("Hints: Yandex/Gmail need an APP PASSWORD (not the account password);")
        print("Yandex also requires enabling IMAP in mailbox settings (Все настройки -> Почтовые программы).")
        sys.exit(1)
    if folder:
        status, _ = imap.select(_quote_folder(folder), readonly=readonly)
        if status != "OK":
            print(f"ERROR: cannot open folder '{folder}'. Run: email_client.py folders")
            try:
                imap.logout()
            except Exception:
                pass
            sys.exit(1)
    return imap


def smtp_connect(prof):
    prof.require_smtp()
    ctx = ssl.create_default_context()
    try:
        if prof.smtp_port == 465:
            smtp = smtplib.SMTP_SSL(prof.smtp_host, prof.smtp_port, timeout=30, context=ctx)
        else:
            smtp = smtplib.SMTP(prof.smtp_host, prof.smtp_port, timeout=30)
            smtp.starttls(context=ctx)
        smtp.login(prof.user, prof.password)
        return smtp
    except smtplib.SMTPAuthenticationError as e:
        print(f"ERROR: SMTP auth failed for {prof.user}: {e}")
        print("Use an app password; check MAIL_%s_SMTP_HOST/_SMTP_PORT (465=SSL, 587=STARTTLS)." % prof.name)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: SMTP connection failed {prof.smtp_host}:{prof.smtp_port} — {e}")
        sys.exit(1)


def _quote_folder(folder):
    """Quote folder name for IMAP; encode non-ASCII as modified UTF-7."""
    try:
        folder.encode("ascii")
    except UnicodeEncodeError:
        folder = _imap_utf7_encode(folder)
    if " " in folder or "(" in folder:
        return f'"{folder}"'
    return folder


def _imap_utf7_encode(s):
    """Encode folder name to IMAP modified UTF-7 (RFC 3501)."""
    out = []
    buf = []

    def flush():
        if buf:
            b64 = "".join(buf).encode("utf-16-be")
            import base64
            enc = base64.b64encode(b64).decode("ascii").rstrip("=").replace("/", ",")
            out.append("&" + enc + "-")
            buf.clear()

    for ch in s:
        if 0x20 <= ord(ch) <= 0x7E:
            flush()
            out.append("&-" if ch == "&" else ch)
        else:
            buf.append(ch)
    flush()
    return "".join(out)


def _imap_utf7_decode(s):
    """Decode IMAP modified UTF-7 folder name to unicode."""
    import base64
    res = []
    i = 0
    while i < len(s):
        ch = s[i]
        if ch == "&":
            j = s.find("-", i)
            if j == -1:
                res.append(s[i:])
                break
            chunk = s[i + 1:j]
            if chunk == "":
                res.append("&")
            else:
                b64 = chunk.replace(",", "/")
                b64 += "=" * (-len(b64) % 4)
                try:
                    res.append(base64.b64decode(b64).decode("utf-16-be"))
                except Exception:
                    res.append(s[i:j + 1])
            i = j + 1
        else:
            res.append(ch)
            i += 1
    return "".join(res)


# ========== PARSING HELPERS ==========

def decode_hdr(raw):
    """Decode an RFC 2047 encoded header into a plain string."""
    if raw is None:
        return ""
    try:
        parts = decode_header(raw)
    except Exception:
        return str(raw)
    decoded = []
    for part, charset in parts:
        if isinstance(part, bytes):
            decoded.append(part.decode(charset or "utf-8", errors="replace"))
        else:
            decoded.append(part)
    return "".join(decoded).strip()


def strip_html(html):
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<p[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    text = text.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", '"').replace("&#39;", "'")
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_bodies(msg):
    """Return (text, html) from a potentially multipart message."""
    text_body, html_body = "", ""
    parts = msg.walk() if msg.is_multipart() else [msg]
    for part in parts:
        ctype = part.get_content_type()
        disposition = str(part.get("Content-Disposition", ""))
        if "attachment" in disposition:
            continue
        if ctype not in ("text/plain", "text/html"):
            continue
        payload = part.get_payload(decode=True)
        if not payload:
            continue
        charset = part.get_content_charset() or "utf-8"
        decoded = payload.decode(charset, errors="replace")
        if ctype == "text/plain" and not text_body:
            text_body = decoded
        elif ctype == "text/html" and not html_body:
            html_body = decoded
    return text_body, html_body


def list_attachments(msg):
    """Return [{index, filename, content_type, size}] for attachment parts."""
    result = []
    if not msg.is_multipart():
        return result
    idx = 0
    for part in msg.walk():
        disposition = str(part.get("Content-Disposition", ""))
        filename = part.get_filename()
        if "attachment" not in disposition and not (filename and "inline" in disposition):
            continue
        idx += 1
        payload = part.get_payload(decode=True) or b""
        result.append({
            "index": idx,
            "filename": decode_hdr(filename) if filename else f"attachment-{idx}.bin",
            "content_type": part.get_content_type(),
            "size": len(payload),
            "_part": part,
        })
    return result


def fetch_message(imap, uid):
    """Fetch full RFC822 message by UID. Returns email.message.Message or exits."""
    status, data = imap.uid("fetch", str(uid), "(RFC822)")
    if status != "OK" or not data or data[0] is None:
        print(f"ERROR: message UID {uid} not found in this folder.")
        sys.exit(1)
    raw = None
    for item in data:
        if isinstance(item, tuple) and len(item) >= 2:
            raw = item[1]
            break
    if raw is None:
        print(f"ERROR: empty FETCH response for UID {uid}.")
        sys.exit(1)
    return email_lib.message_from_bytes(raw)


def fmt_size(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024


def to_imap_date(s):
    """YYYY-MM-DD -> DD-Mon-YYYY (IMAP format)."""
    try:
        dt = datetime.strptime(s, "%Y-%m-%d")
    except ValueError:
        print(f"ERROR: bad date '{s}', expected YYYY-MM-DD.")
        sys.exit(2)
    return f"{dt.day:02d}-{MONTHS[dt.month - 1]}-{dt.year}"


def uid_search(imap, criteria_parts, utf8_text=None):
    """UID SEARCH with optional UTF-8 literal for non-ASCII text criteria.

    criteria_parts: list of ASCII-safe tokens, e.g. ['UNSEEN', 'SINCE', '01-Jul-2026'].
    utf8_text: (key, value) e.g. ('TEXT', 'счёт') — sent as UTF-8 literal.
    """
    if utf8_text:
        key, value = utf8_text
        try:
            value.encode("ascii")
            criteria_parts = criteria_parts + [key, f'"{value}"']
            utf8_text = None
        except UnicodeEncodeError:
            pass
    if utf8_text:
        key, value = utf8_text
        imap.literal = value.encode("utf-8")
        args = ["CHARSET", "UTF-8"] + criteria_parts + [key]
        status, data = imap.uid("SEARCH", *args)
    else:
        args = criteria_parts or ["ALL"]
        status, data = imap.uid("SEARCH", *args)
    if status != "OK":
        print(f"ERROR: server rejected SEARCH {' '.join(args)}: {data}")
        print("Some servers do not support CHARSET UTF-8 search — try ASCII-only criteria (--from/--since).")
        sys.exit(1)
    if not data or not data[0]:
        return []
    return data[0].split()


def summarize(imap, uids, flags_map=None):
    """Fetch light headers for a list of uids. Returns list of dicts."""
    rows = []
    for uid in uids:
        uid_s = uid.decode() if isinstance(uid, bytes) else str(uid)
        status, data = imap.uid(
            "fetch", uid_s,
            "(FLAGS BODY.PEEK[HEADER.FIELDS (FROM SUBJECT DATE)])")
        if status != "OK" or not data:
            continue
        flags = ""
        header_bytes = b""
        for item in data:
            if isinstance(item, tuple) and len(item) >= 2:
                meta = item[0].decode("utf-8", "replace") if isinstance(item[0], bytes) else str(item[0])
                fm = re.search(r"FLAGS \(([^)]*)\)", meta)
                if fm:
                    flags = fm.group(1)
                header_bytes = item[1] or b""
            elif isinstance(item, bytes):
                m = re.search(rb"FLAGS \(([^)]*)\)", item)
                if m:
                    flags = m.group(1).decode("utf-8", "replace")
        hdr = email_lib.message_from_bytes(header_bytes)
        rows.append({
            "uid": uid_s,
            "from": decode_hdr(hdr.get("From", "")),
            "subject": decode_hdr(hdr.get("Subject", "(no subject)")),
            "date": decode_hdr(hdr.get("Date", "")),
            "unseen": "\\Seen" not in flags,
        })
    return rows


def print_rows(rows, as_json):
    if as_json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
        return
    if not rows:
        print("(no messages)")
        return
    for r in rows:
        mark = "* " if r["unseen"] else "  "
        print(f"{mark}[{r['uid']}] {r['date']}")
        print(f"   From: {r['from']}")
        print(f"   Subj: {r['subject']}")


# ========== COMMANDS ==========

def cmd_profiles(args, prof):
    names = discover_profiles()
    if args.json:
        print(json.dumps({"profiles": names}, ensure_ascii=False))
        return
    if not names:
        print("No mail profiles configured.")
        print("Add to ~/.claude/.credentials.master.env (example, profile YANDEX):")
        print("  MAIL_YANDEX_IMAP_HOST=imap.yandex.ru")
        print("  MAIL_YANDEX_SMTP_HOST=smtp.yandex.ru")
        print("  MAIL_YANDEX_USER=you@yandex.ru")
        print("  MAIL_YANDEX_PASSWORD=<app-password>")
        return
    for n in names:
        p = Profile(n)
        print(f"{n}: {p.user} (imap={p.imap_host}:{p.imap_port}, smtp={p.smtp_host}:{p.smtp_port})")


def cmd_folders(args, prof):
    imap = imap_connect(prof, folder=None)
    try:
        status, data = imap.list()
        if status != "OK":
            print("ERROR: LIST command failed.")
            sys.exit(1)
        folders = []
        for line in data or []:
            if line is None:
                continue
            s = line.decode("utf-8", "replace") if isinstance(line, bytes) else str(line)
            # '(\HasNoChildren) "/" "INBOX"' or '... "|" INBOX'
            m = re.match(r'^\(([^)]*)\)\s+"?([^"\s]*)"?\s+(.*)$', s)
            if not m:
                continue
            raw_name = m.group(3).strip().strip('"')
            folders.append({
                "name": _imap_utf7_decode(raw_name),
                "raw": raw_name,
                "flags": m.group(1),
            })
        if args.json:
            print(json.dumps(folders, ensure_ascii=False, indent=2))
        else:
            for f in folders:
                extra = f" (raw: {f['raw']})" if f["raw"] != f["name"] else ""
                print(f"{f['name']}{extra}")
    finally:
        imap.logout()


def cmd_list(args, prof):
    imap = imap_connect(prof, folder=args.folder, readonly=True)
    try:
        criteria = ["UNSEEN"] if args.unseen else ["ALL"]
        uids = uid_search(imap, criteria)
        uids = uids[-args.limit:]
        uids.reverse()  # newest first
        rows = summarize(imap, uids)
        print_rows(rows, args.json)
    finally:
        imap.logout()


def cmd_search(args, prof):
    imap = imap_connect(prof, folder=args.folder, readonly=True)
    try:
        criteria = []
        utf8_text = None
        if args.since:
            criteria += ["SINCE", to_imap_date(args.since)]
        if args.from_addr:
            criteria += ["FROM", f'"{args.from_addr}"']
        if args.subject:
            try:
                args.subject.encode("ascii")
                criteria += ["SUBJECT", f'"{args.subject}"']
            except UnicodeEncodeError:
                utf8_text = ("SUBJECT", args.subject)
        if args.query:
            if utf8_text:
                print("ERROR: cannot combine non-ASCII --subject with a text query in one search.")
                sys.exit(2)
            utf8_text = ("TEXT", args.query)
        if not criteria and not utf8_text:
            print("ERROR: give a query and/or --since/--from/--subject.")
            sys.exit(2)
        uids = uid_search(imap, criteria, utf8_text=utf8_text)
        uids = uids[-args.limit:]
        uids.reverse()
        rows = summarize(imap, uids)
        print_rows(rows, args.json)
    finally:
        imap.logout()


def cmd_read(args, prof):
    imap = imap_connect(prof, folder=args.folder, readonly=not args.mark_read)
    try:
        msg = fetch_message(imap, args.uid)
    finally:
        imap.logout()
    text, html = extract_bodies(msg)
    body = text or (strip_html(html) if html else "")
    atts = list_attachments(msg)
    out = {
        "uid": str(args.uid),
        "from": decode_hdr(msg.get("From", "")),
        "to": decode_hdr(msg.get("To", "")),
        "cc": decode_hdr(msg.get("Cc", "")),
        "date": decode_hdr(msg.get("Date", "")),
        "subject": decode_hdr(msg.get("Subject", "(no subject)")),
        "message_id": msg.get("Message-ID", ""),
        "body": body.strip(),
        "attachments": [{k: a[k] for k in ("index", "filename", "content_type", "size")} for a in atts],
    }
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return
    print(f"UID:     {out['uid']}")
    print(f"From:    {out['from']}")
    print(f"To:      {out['to']}")
    if out["cc"]:
        print(f"Cc:      {out['cc']}")
    print(f"Date:    {out['date']}")
    print(f"Subject: {out['subject']}")
    if out["attachments"]:
        print("Attachments:")
        for a in out["attachments"]:
            print(f"  [{a['index']}] {a['filename']} ({a['content_type']}, {fmt_size(a['size'])})")
    print("-" * 60)
    print(out["body"] or "(empty body)")


def _build_message(prof, to_addr, subject, body, attach=None, html=False,
                   in_reply_to=None, references=None, cc=None):
    msg = MIMEMultipart()
    msg["From"] = prof.from_addr
    msg["To"] = to_addr
    if cc:
        msg["Cc"] = cc
    msg["Subject"] = subject
    msg["Date"] = formatdate(localtime=True)
    domain = prof.from_addr.split("@")[1] if "@" in prof.from_addr else "local"
    msg["Message-ID"] = f"<cli-{uuid.uuid4().hex[:16]}@{domain}>"
    if in_reply_to:
        msg["In-Reply-To"] = in_reply_to
        msg["References"] = references or in_reply_to
    msg.attach(MIMEText(body, "html" if html else "plain", "utf-8"))
    for path in attach or []:
        p = Path(path)
        if not p.exists():
            print(f"ERROR: attachment not found: {path}")
            sys.exit(2)
        part = MIMEBase("application", "octet-stream")
        part.set_payload(p.read_bytes())
        encoders.encode_base64(part)
        # RFC2231 for non-ASCII filenames is handled by add_header when tuple given
        try:
            p.name.encode("ascii")
            part.add_header("Content-Disposition", "attachment", filename=p.name)
        except UnicodeEncodeError:
            part.add_header("Content-Disposition", "attachment",
                            filename=("utf-8", "", p.name))
        msg.attach(part)
    return msg


def _smtp_send(prof, msg):
    smtp = smtp_connect(prof)
    try:
        smtp.send_message(msg)
    finally:
        try:
            smtp.quit()
        except Exception:
            smtp.close()


def cmd_send(args, prof):
    msg = _build_message(prof, args.to, args.subject, args.body,
                         attach=args.attach, html=args.html, cc=args.cc)
    _smtp_send(prof, msg)
    result = {
        "sent": True,
        "to": args.to,
        "subject": args.subject,
        "message_id": msg["Message-ID"],
        "attachments": args.attach or [],
    }
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Sent to {args.to} (Message-ID {msg['Message-ID']})")


def cmd_reply(args, prof):
    imap = imap_connect(prof, folder=args.folder, readonly=True)
    try:
        orig = fetch_message(imap, args.uid)
    finally:
        imap.logout()
    # Prefer Reply-To, then From
    reply_to_hdr = orig.get("Reply-To") or orig.get("From", "")
    _, to_addr = parseaddr(decode_hdr(reply_to_hdr))
    if not to_addr:
        print("ERROR: cannot determine reply address from the original message.")
        sys.exit(1)
    subject = decode_hdr(orig.get("Subject", ""))
    if not subject.lower().startswith("re:"):
        subject = f"Re: {subject}" if subject else "Re:"
    orig_id = orig.get("Message-ID", "")
    refs = (orig.get("References", "") + " " + orig_id).strip()
    msg = _build_message(prof, to_addr, subject, args.body,
                         attach=args.attach, html=args.html,
                         in_reply_to=orig_id or None, references=refs or None)
    _smtp_send(prof, msg)
    result = {"sent": True, "to": to_addr, "subject": subject,
              "in_reply_to": orig_id, "message_id": msg["Message-ID"]}
    if args.json:
        print(json.dumps(result, ensure_ascii=False))
    else:
        print(f"Replied to {to_addr} (subject: {subject})")


def cmd_mark_read(args, prof):
    imap = imap_connect(prof, folder=args.folder)
    try:
        status, _ = imap.uid("STORE", str(args.uid), "+FLAGS", "(\\Seen)")
        if status != "OK":
            print(f"ERROR: could not mark UID {args.uid} as read.")
            sys.exit(1)
    finally:
        imap.logout()
    if args.json:
        print(json.dumps({"uid": str(args.uid), "marked_read": True}))
    else:
        print(f"UID {args.uid} marked as read.")


def cmd_delete(args, prof):
    imap = imap_connect(prof, folder=args.folder)
    try:
        status, _ = imap.uid("STORE", str(args.uid), "+FLAGS", "(\\Deleted)")
        if status != "OK":
            print(f"ERROR: could not flag UID {args.uid} as deleted.")
            sys.exit(1)
        imap.expunge()
    finally:
        imap.logout()
    if args.json:
        print(json.dumps({"uid": str(args.uid), "deleted": True}))
    else:
        print(f"UID {args.uid} deleted (expunged) from {args.folder}.")


def cmd_download_attachments(args, prof):
    imap = imap_connect(prof, folder=args.folder, readonly=True)
    try:
        msg = fetch_message(imap, args.uid)
    finally:
        imap.logout()
    atts = list_attachments(msg)
    if not atts:
        print("(no attachments)" if not args.json else json.dumps({"saved": []}))
        return
    out_dir = Path(args.out or DOWNLOAD_DIR)
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = []
    for a in atts:
        payload = a["_part"].get_payload(decode=True)
        if not payload:
            continue
        # sanitize filename for Windows
        safe = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", a["filename"]) or f"attachment-{a['index']}.bin"
        target = out_dir / safe
        n = 1
        while target.exists():
            target = out_dir / f"{Path(safe).stem}_{n}{Path(safe).suffix}"
            n += 1
        target.write_bytes(payload)
        saved.append({"filename": a["filename"], "path": str(target), "size": len(payload)})
    if args.json:
        print(json.dumps({"saved": saved}, ensure_ascii=False, indent=2))
    else:
        for s in saved:
            print(f"Saved: {s['path']} ({fmt_size(s['size'])})")


# ========== MAIN ==========

def main():
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument("--profile", default="DEFAULT",
                        help="mail profile name (env prefix MAIL_<PROFILE>_*), default: DEFAULT")
    parent.add_argument("--json", action="store_true", help="machine-readable JSON output")

    parser = argparse.ArgumentParser(
        prog="email_client.py",
        description="Generic IMAP/SMTP email CLI (any mailbox: Yandex, corporate, gmail app-password).",
        epilog="Profiles live in ~/.claude/.credentials.master.env as MAIL_<PROFILE>_IMAP_HOST etc.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("profiles", parents=[parent], help="list configured mail profiles")
    p.set_defaults(func=cmd_profiles)

    p = sub.add_parser("folders", parents=[parent], help="list IMAP folders")
    p.set_defaults(func=cmd_folders)

    p = sub.add_parser("list", parents=[parent], help="list recent messages")
    p.add_argument("--folder", default="INBOX")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--unseen", action="store_true", help="only unread messages")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("search", parents=[parent], help="search messages (full-text and/or header filters)")
    p.add_argument("query", nargs="?", help="full-text query (server-side TEXT search)")
    p.add_argument("--folder", default="INBOX")
    p.add_argument("--since", help="date YYYY-MM-DD")
    p.add_argument("--from", dest="from_addr", help="sender address filter")
    p.add_argument("--subject", help="subject substring filter")
    p.add_argument("--limit", type=int, default=20)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("read", parents=[parent], help="read a message by UID")
    p.add_argument("uid")
    p.add_argument("--folder", default="INBOX")
    p.add_argument("--mark-read", action="store_true",
                   help="also mark as read (default: reading does NOT set \\Seen)")
    p.set_defaults(func=cmd_read)

    p = sub.add_parser("send", parents=[parent], help="send a new email")
    p.add_argument("to")
    p.add_argument("subject")
    p.add_argument("body")
    p.add_argument("--attach", action="append", help="file to attach (repeatable)")
    p.add_argument("--html", action="store_true", help="body is HTML")
    p.add_argument("--cc", help="Cc addresses (comma-separated)")
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("reply", parents=[parent], help="reply to a message by UID (keeps threading)")
    p.add_argument("uid")
    p.add_argument("body")
    p.add_argument("--folder", default="INBOX")
    p.add_argument("--attach", action="append", help="file to attach (repeatable)")
    p.add_argument("--html", action="store_true", help="body is HTML")
    p.set_defaults(func=cmd_reply)

    p = sub.add_parser("mark-read", parents=[parent], help="mark a message as read")
    p.add_argument("uid")
    p.add_argument("--folder", default="INBOX")
    p.set_defaults(func=cmd_mark_read)

    p = sub.add_parser("delete", parents=[parent], help="delete a message (flag \\Deleted + expunge)")
    p.add_argument("uid")
    p.add_argument("--folder", default="INBOX")
    p.set_defaults(func=cmd_delete)

    p = sub.add_parser("download-attachments", parents=[parent], help="save attachments of a message")
    p.add_argument("uid")
    p.add_argument("--folder", default="INBOX")
    p.add_argument("--out", help=f"output dir (default: {DOWNLOAD_DIR})")
    p.set_defaults(func=cmd_download_attachments)

    args = parser.parse_args()
    prof = Profile(args.profile)
    args.func(args, prof)


if __name__ == "__main__":
    main()
