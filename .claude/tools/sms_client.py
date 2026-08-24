"""
SMS CLI for Claude Code — Twilio REST API connector.
Send single/bulk SMS, check delivery status, list messages, check balance and account numbers.

Credentials: ~/.claude/.credentials.master.env
  TWILIO_ACCOUNT_SID   — Account SID (starts with "AC...", Twilio Console dashboard)
  TWILIO_AUTH_TOKEN    — Auth Token (same dashboard)
  TWILIO_PHONE_NUMBER  — default From-number in E.164 (+15551234567)

API: https://api.twilio.com/2010-04-01 (HTTP Basic auth: SID:TOKEN).
Uses `requests` if installed, otherwise falls back to stdlib urllib — no twilio SDK needed.

Usage:
  python sms_client.py send +55 XX XXXXX-XXXX "Hello" [--from +1555...]
  python sms_client.py bulk numbers.txt "Hello" [--rate 2.0] [--confirm]
  python sms_client.py status SMxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
  python sms_client.py list [--limit 20] [--to +55...] [--from +1555...]
  python sms_client.py balance
  python sms_client.py numbers
  python sms_client.py receive-webhook
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import argparse
import base64
import io
import json
import os
import random
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

TWILIO_API_BASE = "https://api.twilio.com/2010-04-01/Accounts"
MAX_SMS_LENGTH = 1600  # Twilio hard limit (~10 segments)
CRED_FILE = Path.home() / ".claude" / ".credentials.master.env"

try:
    import requests  # noqa: F401
    HAVE_REQUESTS = True
except ImportError:
    HAVE_REQUESTS = False


def load_env():
    if CRED_FILE.exists():
        for line in CRED_FILE.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key, value = key.strip(), value.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = value


load_env()

ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
FROM_NUMBER = os.environ.get("TWILIO_PHONE_NUMBER", "")


def require_creds():
    """Exit with a clear instruction if Twilio credentials are missing."""
    missing = []
    if not ACCOUNT_SID:
        missing.append("TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    if not AUTH_TOKEN:
        missing.append("TWILIO_AUTH_TOKEN=your_auth_token")
    if missing:
        print("Twilio credentials are not configured.")
        print(f"Add these lines to {CRED_FILE}:")
        print()
        for m in missing:
            print(f"  {m}")
        print("  TWILIO_PHONE_NUMBER=+15551234567   # your Twilio number (E.164)")
        print()
        print("Where to get them: https://console.twilio.com -> Account Info")
        print("(Account SID starts with 'AC', Auth Token is next to it.)")
        sys.exit(2)


def api_request(method, path, params=None, data=None):
    """Call Twilio REST API. Returns (status_code, parsed_json).

    path: relative to /2010-04-01/Accounts/{SID}, e.g. "/Messages.json"
    params: dict for query string (GET)
    data: dict for form body (POST)
    """
    url = f"{TWILIO_API_BASE}/{ACCOUNT_SID}{path}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    if HAVE_REQUESTS:
        import requests
        try:
            resp = requests.request(
                method, url,
                auth=(ACCOUNT_SID, AUTH_TOKEN),
                data=data,
                timeout=30,
            )
        except requests.RequestException as e:
            print(f"Network error talking to Twilio: {e}")
            sys.exit(1)
        try:
            body = resp.json()
        except ValueError:
            body = {"raw": resp.text}
        return resp.status_code, body

    # stdlib fallback
    creds = base64.b64encode(f"{ACCOUNT_SID}:{AUTH_TOKEN}".encode("ascii")).decode("ascii")
    body_bytes = urllib.parse.urlencode(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body_bytes, method=method)
    req.add_header("Authorization", f"Basic {creds}")
    if body_bytes:
        req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode("utf-8"))
        except Exception:
            return e.code, {"message": str(e)}
    except urllib.error.URLError as e:
        print(f"Network error talking to Twilio: {e.reason}")
        sys.exit(1)


def api_error_text(status, body):
    """Human-readable Twilio error."""
    msg = body.get("message") or body.get("raw") or str(body)
    code = body.get("code")
    hint = ""
    if status == 401:
        hint = "  (check TWILIO_ACCOUNT_SID / TWILIO_AUTH_TOKEN)"
    elif code == 21608:
        hint = "  (trial account: recipient number must be verified in Twilio Console)"
    elif code == 21211:
        hint = "  (invalid 'To' number — use E.164 format, e.g. +55 XX XXXXX-XXXX)"
    elif code == 21606:
        hint = "  (the From number is not a valid SMS-capable Twilio number on this account)"
    return f"Twilio API error {status}" + (f" (code {code})" if code else "") + f": {msg}{hint}"


def fmt_msg_line(m):
    date = (m.get("date_sent") or m.get("date_created") or "")[:22]
    price = m.get("price")
    price_s = f" {price} {m.get('price_unit', '')}" if price else ""
    return (f"{m.get('sid', '?')}  {date:22}  {m.get('direction', ''):14}  "
            f"{m.get('from', '')} -> {m.get('to', '')}  [{m.get('status', '')}]"
            f"{price_s}  {(m.get('body') or '')[:60]}")


def resolve_from(args_from):
    frm = args_from or FROM_NUMBER
    if not frm:
        print("No From-number: pass --from +1555... or add TWILIO_PHONE_NUMBER "
              f"to {CRED_FILE}")
        sys.exit(2)
    return frm


# ========== COMMANDS ==========

def cmd_send(args):
    require_creds()
    frm = resolve_from(args.from_)
    text = args.text
    if len(text) > MAX_SMS_LENGTH:
        print(f"Message too long: {len(text)} chars (Twilio limit {MAX_SMS_LENGTH}). Not sent.")
        sys.exit(1)

    status, body = api_request("POST", "/Messages.json",
                               data={"From": frm, "To": args.to, "Body": text})
    if status >= 400:
        print(api_error_text(status, body))
        sys.exit(1)

    if args.json:
        print(json.dumps(body, ensure_ascii=False, indent=2))
    else:
        segs = body.get("num_segments", "?")
        print(f"Sent: {body.get('sid')}")
        print(f"  {frm} -> {args.to}  status={body.get('status')}  segments={segs}")
        print(f"  Check delivery: python sms_client.py status {body.get('sid')}")


def cmd_bulk(args):
    require_creds()
    frm = resolve_from(args.from_)
    path = Path(args.file)
    if not path.exists():
        print(f"File not found: {path}")
        sys.exit(1)

    numbers = []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        n = line.strip()
        if n and not n.startswith("#"):
            numbers.append(n)
    # dedupe, keep order
    seen = set()
    numbers = [n for n in numbers if not (n in seen or seen.add(n))]

    if not numbers:
        print(f"No phone numbers found in {path} (one E.164 number per line, # = comment).")
        sys.exit(1)

    bad = [n for n in numbers if not n.startswith("+")]
    if bad:
        print(f"WARNING: {len(bad)} number(s) not in E.164 format (must start with '+'): "
              + ", ".join(bad[:5]) + ("..." if len(bad) > 5 else ""))

    if len(numbers) > args.limit:
        print(f"Refusing: {len(numbers)} numbers exceeds --limit {args.limit}. "
              f"Raise --limit explicitly if intended.")
        sys.exit(1)

    dry = not args.confirm
    mode = "DRY-RUN (no SMS sent; add --confirm to send)" if dry else "LIVE SEND"
    print(f"Bulk SMS — {mode}")
    print(f"  From: {frm}   Recipients: {len(numbers)}   Rate: ~{args.rate}s + jitter")
    print(f"  Text ({len(args.text)} chars): {args.text[:100]}")
    print()

    results = []
    for i, to in enumerate(numbers, 1):
        if dry:
            print(f"  [{i}/{len(numbers)}] would send -> {to}")
            results.append({"to": to, "status": "dry-run"})
            continue

        status, body = api_request("POST", "/Messages.json",
                                   data={"From": frm, "To": to, "Body": args.text})
        if status >= 400:
            err = api_error_text(status, body)
            print(f"  [{i}/{len(numbers)}] FAIL -> {to}: {err}")
            results.append({"to": to, "status": "error", "error": err})
        else:
            print(f"  [{i}/{len(numbers)}] sent -> {to}  sid={body.get('sid')}")
            results.append({"to": to, "status": body.get("status"), "sid": body.get("sid")})

        if i < len(numbers):
            # anti-spam: base rate + jitter 0..50%
            time.sleep(args.rate + random.uniform(0, args.rate * 0.5))

    ok = sum(1 for r in results if r["status"] not in ("error",))
    if args.json:
        print(json.dumps({"mode": "dry-run" if dry else "live",
                          "total": len(numbers), "ok": ok, "results": results},
                         ensure_ascii=False, indent=2))
    else:
        print()
        print(f"Done: {ok}/{len(numbers)} " + ("planned (dry-run)" if dry else "accepted by Twilio"))
        if dry:
            print("Re-run with --confirm to actually send.")


def cmd_status(args):
    require_creds()
    status, body = api_request("GET", f"/Messages/{args.sid}.json")
    if status >= 400:
        print(api_error_text(status, body))
        sys.exit(1)
    if args.json:
        print(json.dumps(body, ensure_ascii=False, indent=2))
    else:
        print(fmt_msg_line(body))
        if body.get("error_code"):
            print(f"  error_code={body['error_code']}  error_message={body.get('error_message')}")


def cmd_list(args):
    require_creds()
    params = {"PageSize": args.limit}
    if args.to:
        params["To"] = args.to
    if args.from_:
        params["From"] = args.from_
    status, body = api_request("GET", "/Messages.json", params=params)
    if status >= 400:
        print(api_error_text(status, body))
        sys.exit(1)
    msgs = body.get("messages", [])
    if args.json:
        print(json.dumps(msgs, ensure_ascii=False, indent=2))
        return
    if not msgs:
        print("No messages.")
        return
    for m in msgs:
        print(fmt_msg_line(m))
    print(f"\n{len(msgs)} message(s).")


def cmd_balance(args):
    require_creds()
    status, body = api_request("GET", "/Balance.json")
    if status >= 400:
        print(api_error_text(status, body))
        sys.exit(1)
    if args.json:
        print(json.dumps(body, ensure_ascii=False, indent=2))
    else:
        print(f"Balance: {body.get('balance')} {body.get('currency')}")


def cmd_numbers(args):
    require_creds()
    status, body = api_request("GET", "/IncomingPhoneNumbers.json", params={"PageSize": 50})
    if status >= 400:
        print(api_error_text(status, body))
        sys.exit(1)
    nums = body.get("incoming_phone_numbers", [])
    if args.json:
        print(json.dumps(nums, ensure_ascii=False, indent=2))
        return
    if not nums:
        print("No phone numbers on this account. Buy one: https://console.twilio.com "
              "-> Phone Numbers -> Buy a number (SMS-capable).")
        return
    for n in nums:
        caps = n.get("capabilities", {})
        cap_s = ",".join(k for k, v in caps.items() if v)
        print(f"{n.get('phone_number')}  {n.get('friendly_name', '')}  [{cap_s}]  sid={n.get('sid')}")
    print(f"\n{len(nums)} number(s).")


def cmd_receive_webhook(args):
    print("""Receiving inbound SMS (webhook) — this CLI only SENDS; to RECEIVE you need
a public HTTPS endpoint that Twilio can POST to:

1) Endpoint: any web server accepting POST form-data (From, To, Body, MessageSid)
   and replying with empty TwiML:
     <?xml version="1.0" encoding="UTF-8"?><Response></Response>

2) Expose it publicly:
   - quick test:   ngrok http 8080   (or cloudflared tunnel)
   - production:   nginx on your server + HTTPS

3) Twilio Console -> Phone Numbers -> your number -> Messaging Configuration ->
   "A message comes in" = Webhook, URL = https://your-host/webhooks/twilio, HTTP POST.

4) SECURITY: validate the X-Twilio-Signature header (HMAC-SHA1 over URL+sorted
   params with AUTH_TOKEN, base64). Without validation anyone who knows the URL
   can inject fake inbound messages.

For the server part, reuse ~/.claude/tools/webhook_server.py (skill: webhook-receiver)
instead of writing one from scratch. Note it does NOT know Twilio's scheme: run it with
--provider none and validate X-Twilio-Signature yourself (twilio.request_validator.
RequestValidator, or ~15 lines of hmac-sha1 following step 4).""")


# ========== MAIN ==========

def main():
    parser = argparse.ArgumentParser(
        prog="sms_client.py",
        description="Twilio SMS CLI: send, bulk-send, status, list, balance, numbers.",
    )
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("send", help="Send one SMS")
    p.add_argument("to", help="Recipient in E.164, e.g. +55 XX XXXXX-XXXX")
    p.add_argument("text", help="Message text (<=1600 chars; >160 chars = multiple segments, billed per segment)")
    p.add_argument("--from", dest="from_", default=None, help="From-number (default: TWILIO_PHONE_NUMBER)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("bulk", help="Send SMS to a list of numbers from a file (DRY-RUN by default)")
    p.add_argument("file", help="Text file: one E.164 number per line, # = comment")
    p.add_argument("text", help="Message text sent to every number")
    p.add_argument("--from", dest="from_", default=None, help="From-number (default: TWILIO_PHONE_NUMBER)")
    p.add_argument("--rate", type=float, default=2.0, help="Base delay between sends, seconds (+0..50%% jitter; default 2.0)")
    p.add_argument("--limit", type=int, default=50, help="Safety cap on recipient count (default 50)")
    p.add_argument("--dry-run", action="store_true", help="Preview only (this is already the DEFAULT)")
    p.add_argument("--confirm", action="store_true", help="Actually send (without it — dry-run)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.set_defaults(func=cmd_bulk)

    p = sub.add_parser("status", help="Delivery status of a message by SID")
    p.add_argument("sid", help="Message SID (SM... / MM...)")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("list", help="Recent messages (sent and received)")
    p.add_argument("--limit", type=int, default=20, help="Max messages (default 20)")
    p.add_argument("--to", default=None, help="Filter by recipient")
    p.add_argument("--from", dest="from_", default=None, help="Filter by sender")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.set_defaults(func=cmd_list)

    p = sub.add_parser("balance", help="Account balance")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.set_defaults(func=cmd_balance)

    p = sub.add_parser("numbers", help="Phone numbers on the account")
    p.add_argument("--json", action="store_true", help="JSON output")
    p.set_defaults(func=cmd_numbers)

    p = sub.add_parser("receive-webhook", help="How to receive inbound SMS (instructions, no server started)")
    p.set_defaults(func=cmd_receive_webhook)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(0)
    args.func(args)


if __name__ == "__main__":
    main()
