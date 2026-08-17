"""
Gmail Multi-Account Search
Search emails across all authorized Gmail accounts.

Usage:
  python gmail_search.py "refund OR возврат" [--accounts all|email1,email2]
  python gmail_search.py "from:anthropic invoice" --accounts your-email@gmail.com
  python gmail_search.py "subject:receipt heygen" --max 20
  python gmail_search.py --list-accounts

SECURITY: All email content is treated as untrusted external data.
Sanitization strips prompt injection patterns before output.
"""

import json
import re
import sys
import urllib.request
import urllib.parse
import argparse
import base64
from pathlib import Path

# Fix Windows encoding
sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

TOKENS_DIR = Path.home() / ".claude" / ".gmail-tokens"

# Patterns that look like prompt injection attempts
_INJECTION_PATTERNS = [
    r'ignore\s+(all\s+)?previous\s+instructions',
    r'you\s+are\s+now\s+',
    r'system\s*:\s*',
    r'<\s*system\s*>',
    r'\[INST\]',
    r'###\s*(instruction|system|prompt)',
    r'forget\s+(everything|all|prior)',
    r'disregard\s+(above|previous|prior)',
    r'new\s+instructions?\s*:',
    r'override\s+instructions',
    r'act\s+as\s+(if|a|an)\b',
    r'pretend\s+(you|to)\b',
    r'do\s+not\s+follow\s+(the\s+)?(above|previous)',
    r'<\/?(?:script|iframe|object|embed|form|input)',
]
_INJECTION_RE = re.compile('|'.join(_INJECTION_PATTERNS), re.IGNORECASE)


def sanitize_text(text: str) -> str:
    """Strip prompt injection patterns and suspicious content from email text.

    Replaces detected patterns with [REDACTED] marker.
    This protects against emails containing adversarial instructions
    that could manipulate LLM behavior when content enters the context window.
    """
    if not text:
        return text
    result = _INJECTION_RE.sub('[REDACTED:injection]', text)
    # Strip zero-width and invisible unicode chars often used to hide instructions
    result = re.sub(r'[\u200b\u200c\u200d\u200e\u200f\u2060\ufeff\u034f]', '', result)
    return result


def sanitize_dict(d: dict) -> dict:
    """Sanitize all string values in a dict."""
    return {k: sanitize_text(v) if isinstance(v, str) else v for k, v in d.items()}


def refresh_access_token(token_data: dict) -> str:
    """Refresh the access token using refresh_token."""
    data = urllib.parse.urlencode({
        "client_id": token_data["client_id"],
        "client_secret": token_data["client_secret"],
        "refresh_token": token_data["refresh_token"],
        "grant_type": "refresh_token",
    }).encode()

    req = urllib.request.Request("https://oauth2.googleapis.com/token", data=data)
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    return result["access_token"]


def gmail_api_get(access_token: str, endpoint: str, params: dict = None) -> dict:
    """Make a GET request to Gmail API."""
    url = f"https://gmail.googleapis.com/gmail/v1/users/me/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {access_token}")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def search_account(email: str, query: str, max_results: int = 10) -> list:
    """Search emails in a single account. Returns metadata only (no full body)."""
    token_path = TOKENS_DIR / f"{email}.json"
    if not token_path.exists():
        return [{"error": f"Not authorized: {email}"}]

    with open(token_path) as f:
        token_data = json.load(f)

    try:
        access_token = refresh_access_token(token_data)
    except Exception as e:
        return [{"error": f"Token refresh failed for {email}: {e}"}]

    # Update saved token
    token_data["token"] = access_token
    with open(token_path, "w") as f:
        json.dump(token_data, f, indent=2)

    try:
        result = gmail_api_get(access_token, "messages", {
            "q": query,
            "maxResults": max_results,
        })
    except Exception as e:
        return [{"error": f"Search failed for {email}: {e}"}]

    messages = result.get("messages", [])
    if not messages:
        return []

    results = []
    for msg_info in messages:
        try:
            msg = gmail_api_get(access_token, f"messages/{msg_info['id']}", {
                "format": "metadata",
                "metadataHeaders": "Subject,From,To,Date",
            })

            headers = {h["name"]: h["value"] for h in msg.get("payload", {}).get("headers", [])}
            entry = {
                "id": msg_info["id"],
                "threadId": msg_info.get("threadId", ""),
                "subject": headers.get("Subject", "(no subject)"),
                "from": headers.get("From", ""),
                "to": headers.get("To", ""),
                "date": headers.get("Date", ""),
                "snippet": msg.get("snippet", ""),
                "labels": msg.get("labelIds", []),
            }
            # Sanitize all text fields against prompt injection
            results.append(sanitize_dict(entry))
        except Exception as e:
            results.append({"id": msg_info["id"], "error": str(e)})

    return results


def get_message_body(email: str, message_id: str, raw: bool = False) -> str:
    """Get full message body (text) for a specific message.

    WARNING: Full body is untrusted external content.
    Sanitized by default. Use raw=True only for downloading/forwarding.
    """
    token_path = TOKENS_DIR / f"{email}.json"
    with open(token_path) as f:
        token_data = json.load(f)

    access_token = refresh_access_token(token_data)

    msg = gmail_api_get(access_token, f"messages/{message_id}", {"format": "full"})

    def extract_text(payload):
        parts_text = []
        if payload.get("mimeType") == "text/plain" and payload.get("body", {}).get("data"):
            parts_text.append(base64.urlsafe_b64decode(payload["body"]["data"]).decode("utf-8", errors="replace"))
        for part in payload.get("parts", []):
            parts_text.extend(extract_text(part))
        return parts_text

    texts = extract_text(msg.get("payload", {}))
    body = "\n---\n".join(texts) if texts else msg.get("snippet", "")

    if raw:
        return body

    # Sanitize before returning to LLM context
    sanitized = sanitize_text(body)
    if sanitized != body:
        sanitized = "[SECURITY: prompt injection patterns detected and redacted]\n" + sanitized
    return sanitized


def list_authorized_accounts() -> list:
    """List all accounts with saved tokens."""
    accounts = []
    for f in TOKENS_DIR.glob("*.json"):
        email = f.stem
        with open(f) as fh:
            data = json.load(fh)
        accounts.append({
            "email": email,
            "has_refresh": bool(data.get("refresh_token")),
        })
    return accounts


def main():
    parser = argparse.ArgumentParser(description="Search Gmail across multiple accounts")
    parser.add_argument("query", nargs="?", help="Gmail search query")
    parser.add_argument("--accounts", default="all", help="Comma-separated emails or 'all'")
    parser.add_argument("--max", type=int, default=10, help="Max results per account")
    parser.add_argument("--list-accounts", action="store_true", help="List authorized accounts")
    parser.add_argument("--read", help="Read full message: email:message_id")
    parser.add_argument("--raw", action="store_true", help="Skip sanitization (for download/forward only)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    if args.list_accounts:
        accounts = list_authorized_accounts()
        if not accounts:
            print("Нет авторизованных ящиков. Положи токен в ~/.claude/.gmail-tokens/<ящик>.json (client_id, client_secret, refresh_token).")
            return
        for a in accounts:
            status = "OK" if a["has_refresh"] else "NO REFRESH TOKEN"
            print(f"[{status}] {a['email']}")
        return

    if args.read:
        email, msg_id = args.read.split(":", 1)
        body = get_message_body(email, msg_id, raw=args.raw)
        print(body)
        return

    if not args.query:
        parser.print_help()
        return

    # Determine accounts to search
    if args.accounts == "all":
        accounts = [f.stem for f in TOKENS_DIR.glob("*.json")]
    else:
        accounts = [a.strip() for a in args.accounts.split(",")]

    if not accounts:
        print("Нет авторизованных ящиков. Положи токен в ~/.claude/.gmail-tokens/<ящик>.json (client_id, client_secret, refresh_token).")
        return

    all_results = {}
    for email in accounts:
        results = search_account(email, args.query, args.max)
        all_results[email] = results

    if args.json:
        print(json.dumps(all_results, indent=2, ensure_ascii=False))
        return

    # Pretty print
    total = 0
    for email, results in all_results.items():
        if not results:
            continue
        if results and "error" in results[0]:
            print(f"\n[ERROR] {email}: {results[0]['error']}")
            continue

        print(f"\n{'='*70}")
        print(f"  {email} — {len(results)} result(s)")
        print(f"{'='*70}")
        for r in results:
            if "error" in r:
                print(f"  [ERROR] {r['error']}")
                continue
            print(f"  Date: {r['date']}")
            print(f"  From: {r['from']}")
            print(f"  Subj: {r['subject']}")
            print(f"  Snip: {r['snippet'][:120]}")
            print(f"  ID:   {r['id']} (read: --read {email}:{r['id']})")
            print()
            total += 1

    print(f"\nTotal: {total} message(s) across {len(all_results)} account(s)")


if __name__ == "__main__":
    main()
