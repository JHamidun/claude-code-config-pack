"""
Webhook receiver CLI for Claude Code.
Receives webhook POSTs (GitHub / Stripe / GitLab / JIRA / forms), validates
HMAC signatures, logs every event to JSONL, and optionally pipes the payload
into a command.

Connect -> receive -> log -> exit. No gateway, no agent — plain CLI server.

Routes config: ~/.claude/data/webhooks/routes.json (or --routes FILE)
Event log:     ~/.claude/data/webhooks/YYYY-MM-DD.jsonl
Credentials:   ~/.claude/.credentials.master.env (secrets referenced by
               env-var NAME in routes.json via "secret_env" — values never
               live in the config file and are never logged)

Providers / signature schemes:
  github   X-Hub-Signature-256: sha256=<hex HMAC-SHA256(secret, body)>
  stripe   Stripe-Signature: t=<ts>,v1=<hex HMAC-SHA256(secret, "{t}.{body}")>
           (+/- 300s timestamp tolerance, multiple v1 supported)
  gitlab   X-Gitlab-Token: <plain secret> (constant-time compare)
  generic  X-Webhook-Signature: <hex HMAC-SHA256(secret, body)>
  none     no signature check (forms, JIRA default webhooks — see SKILL.md)

Security: binds 127.0.0.1 by default; refuses to bind non-loopback host for
routes with provider "none" unless --allow-insecure-public is passed;
signature header values are never written to the log (only a valid/invalid
boolean).

Usage:
  python webhook_server.py serve [--port 8787] [--routes FILE]
  python webhook_server.py test github [--payload file.json]
  python webhook_server.py routes [--init]
  python webhook_server.py tail [-n 20]
  python webhook_server.py verify github --secret s3cret
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
import hashlib
import hmac
import io
import json
import os
import shlex
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
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

DATA_DIR = Path.home() / ".claude" / "data" / "webhooks"
DEFAULT_ROUTES_FILE = DATA_DIR / "routes.json"
DEFAULT_PORT = 8787
DEFAULT_HOST = "127.0.0.1"
MAX_BODY_BYTES = 1_048_576  # 1 MB
STRIPE_TOLERANCE_SEC = 300

PROVIDERS = ("github", "stripe", "gitlab", "generic", "none")

# Headers worth keeping in the event log. Signature/auth headers are
# deliberately excluded — we log only the validation verdict.
LOGGED_HEADERS = (
    "Content-Type",
    "User-Agent",
    "X-GitHub-Event",
    "X-GitHub-Delivery",
    "X-Gitlab-Event",
    "X-Request-ID",
)

SAMPLE_ROUTES = {
    "github": {
        "path": "/hooks/github",
        "provider": "github",
        "secret_env": "WEBHOOK_GITHUB_SECRET",
        "action": None,
    },
    "stripe": {
        "path": "/hooks/stripe",
        "provider": "stripe",
        "secret_env": "WEBHOOK_STRIPE_SECRET",
        "action": None,
    },
    "form": {
        "path": "/hooks/form",
        "provider": "none",
        "action": {
            "command": "python ~/.claude/tools/example_handler.py",
            "timeout": 30,
        },
    },
}

SAMPLE_PAYLOADS = {
    "github": {
        "action": "opened",
        "pull_request": {"title": "Test PR", "number": 1},
        "repository": {"full_name": "owner/repo"},
    },
    "stripe": {
        "id": "evt_test_0001",
        "type": "payment_intent.succeeded",
        "data": {"object": {"id": "pi_test", "amount": 1000, "currency": "usd"}},
    },
    "gitlab": {"object_kind": "push", "ref": "refs/heads/main"},
    "generic": {"event": "test", "ok": True},
    "none": {"name": "Test User", "message": "form submission"},
}


# ========== HELPERS ==========

def utc_now_iso():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def load_routes(routes_file):
    path = Path(routes_file)
    if not path.exists():
        print(f"Routes config not found: {path}")
        print(f"Create one with:  python {Path(__file__).name} routes --init")
        sys.exit(1)
    try:
        routes = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        print(f"Routes config is not valid JSON ({path}): {e}")
        sys.exit(1)
    if not isinstance(routes, dict) or not routes:
        print(f"Routes config must be a non-empty JSON object: {path}")
        sys.exit(1)
    # Validate
    for name, route in routes.items():
        provider = route.get("provider", "generic")
        if provider not in PROVIDERS:
            print(f"Route '{name}': unknown provider '{provider}'. Allowed: {', '.join(PROVIDERS)}")
            sys.exit(1)
        if not route.get("path", "").startswith("/"):
            print(f"Route '{name}': 'path' must start with '/'. Got: {route.get('path')!r}")
            sys.exit(1)
        if provider != "none":
            env_name = route.get("secret_env", "")
            if not env_name:
                print(f"Route '{name}': provider '{provider}' requires 'secret_env' "
                      f"(env var NAME holding the secret). Add it to routes.json.")
                sys.exit(1)
            if not os.environ.get(env_name):
                print(f"Route '{name}': env var {env_name} is not set.")
                print(f"Add it to ~/.claude/.credentials.master.env:  {env_name}=<secret>")
                sys.exit(1)
    return routes


def route_secret(route):
    env_name = route.get("secret_env", "")
    return os.environ.get(env_name, "") if env_name else ""


def append_log(record):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    log_file = DATA_DIR / (datetime.now().strftime("%Y-%m-%d") + ".jsonl")
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return log_file


def read_log_events(limit, route_filter=None):
    """Read last `limit` events across daily JSONL files (newest first)."""
    if not DATA_DIR.exists():
        return []
    files = sorted(DATA_DIR.glob("*.jsonl"), reverse=True)
    events = []
    for lf in files:
        lines = lf.read_text(encoding="utf-8").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if route_filter and rec.get("route") != route_filter:
                continue
            events.append(rec)
            if len(events) >= limit:
                return events
    return events


# ========== SIGNATURES ==========

def sign_github(secret, body):
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def sign_stripe(secret, body, ts=None):
    ts = int(ts if ts is not None else time.time())
    mac = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256)
    return f"t={ts},v1={mac.hexdigest()}"


def sign_generic(secret, body):
    return hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def build_signature_headers(provider, secret, body):
    """Headers a provider would send for this body (used by test/verify)."""
    if provider == "github":
        return {"X-Hub-Signature-256": sign_github(secret, body)}
    if provider == "stripe":
        return {"Stripe-Signature": sign_stripe(secret, body)}
    if provider == "gitlab":
        return {"X-Gitlab-Token": secret}
    if provider == "generic":
        return {"X-Webhook-Signature": sign_generic(secret, body)}
    return {}


def validate_signature(provider, headers, body, secret):
    """Return (ok: bool, detail: str). headers: case-insensitive getter expected."""
    get = headers.get

    if provider == "none":
        return True, "no signature check (provider 'none')"

    if not secret:
        return False, "secret not available in env"

    if provider == "github":
        sig = get("X-Hub-Signature-256", "")
        if not sig:
            return False, "missing X-Hub-Signature-256 header"
        expected = sign_github(secret, body)
        ok = hmac.compare_digest(sig, expected)
        return ok, "valid" if ok else "signature mismatch"

    if provider == "stripe":
        sig_header = get("Stripe-Signature", "")
        if not sig_header:
            return False, "missing Stripe-Signature header"
        ts = None
        v1s = []
        for item in sig_header.split(","):
            k, _, v = item.strip().partition("=")
            if k == "t":
                ts = v
            elif k == "v1":
                v1s.append(v)
        if not ts or not v1s:
            return False, "malformed Stripe-Signature (need t= and v1=)"
        try:
            ts_int = int(ts)
        except ValueError:
            return False, "malformed timestamp in Stripe-Signature"
        expected = hmac.new(
            secret.encode(), f"{ts_int}.".encode() + body, hashlib.sha256
        ).hexdigest()
        if not any(hmac.compare_digest(expected, v) for v in v1s):
            return False, "signature mismatch"
        if abs(time.time() - ts_int) > STRIPE_TOLERANCE_SEC:
            return False, f"timestamp outside tolerance ({STRIPE_TOLERANCE_SEC}s)"
        return True, "valid"

    if provider == "gitlab":
        token = get("X-Gitlab-Token", "")
        if not token:
            return False, "missing X-Gitlab-Token header"
        ok = hmac.compare_digest(token, secret)
        return ok, "valid" if ok else "token mismatch"

    if provider == "generic":
        sig = get("X-Webhook-Signature", "")
        if not sig:
            return False, "missing X-Webhook-Signature header"
        expected = sign_generic(secret, body)
        ok = hmac.compare_digest(sig, expected)
        return ok, "valid" if ok else "signature mismatch"

    return False, f"unknown provider: {provider}"


# ========== ACTION RUNNER ==========

def run_action(route_name, action, body_bytes, event_type):
    """Run route action command with payload on stdin (background thread)."""
    command = action.get("command", "")
    timeout = int(action.get("timeout", 30))
    if not command:
        return
    if isinstance(command, str):
        cmd = shlex.split(command, posix=False)
    else:
        cmd = list(command)
    env = dict(os.environ)
    env["WEBHOOK_ROUTE"] = route_name
    env["WEBHOOK_EVENT"] = event_type or ""
    started = time.time()
    record = {
        "ts": utc_now_iso(),
        "kind": "action_result",
        "route": route_name,
        "command": command if isinstance(command, str) else " ".join(cmd),
    }
    try:
        proc = subprocess.run(
            cmd, input=body_bytes, capture_output=True, timeout=timeout, env=env
        )
        record["rc"] = proc.returncode
        record["stdout"] = proc.stdout.decode("utf-8", errors="replace")[:500]
        record["stderr"] = proc.stderr.decode("utf-8", errors="replace")[:500]
    except subprocess.TimeoutExpired:
        record["rc"] = -1
        record["error"] = f"timeout after {timeout}s"
    except FileNotFoundError:
        record["rc"] = -1
        record["error"] = f"command not found: {cmd[0]}"
    except Exception as e:
        record["rc"] = -1
        record["error"] = str(e)
    record["duration_ms"] = int((time.time() - started) * 1000)
    append_log(record)


# ========== HTTP SERVER ==========

class WebhookHandler(BaseHTTPRequestHandler):
    routes = {}       # set by cmd_serve: name -> route dict
    path_index = {}   # path -> name
    quiet = False

    server_version = "webhook-cli/1.0"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt, *args):
        if not self.quiet:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {self.address_string()} {fmt % args}")

    def _respond(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {"status": "ok", "routes": sorted(self.routes.keys())})
        else:
            self._respond(404, {"error": "not found (webhooks accept POST only)"})

    def do_POST(self):
        path = self.path.split("?")[0]
        route_name = self.path_index.get(path)
        if not route_name:
            self._respond(404, {"error": f"no route for path {path}"})
            return
        route = self.routes[route_name]
        provider = route.get("provider", "generic")

        # Body size limit before reading
        try:
            content_length = int(self.headers.get("Content-Length", 0))
        except ValueError:
            content_length = 0
        if content_length > MAX_BODY_BYTES:
            self._respond(413, {"error": "payload too large"})
            return
        body = self.rfile.read(content_length)

        # Signature first
        secret = route_secret(route)
        ok, detail = validate_signature(provider, self.headers, body, secret)
        event_type = (
            self.headers.get("X-GitHub-Event", "")
            or self.headers.get("X-Gitlab-Event", "")
            or ""
        )

        try:
            payload = json.loads(body) if body else {}
        except json.JSONDecodeError:
            try:
                import urllib.parse
                payload = dict(urllib.parse.parse_qsl(body.decode("utf-8")))
            except Exception:
                payload = {"_raw": body.decode("utf-8", errors="replace")[:2000]}

        if not event_type and isinstance(payload, dict):
            event_type = str(payload.get("type", "") or payload.get("event", "") or "")

        record = {
            "ts": utc_now_iso(),
            "kind": "event",
            "route": route_name,
            "provider": provider,
            "path": path,
            "event": event_type or "unknown",
            "signature_valid": ok,
            "signature_detail": detail,
            "remote": self.client_address[0],
            "headers": {h: self.headers[h] for h in LOGGED_HEADERS if self.headers.get(h)},
            "payload": payload,
        }

        if not ok:
            record["payload"] = None  # don't store unauthenticated payloads
            append_log(record)
            self._respond(401, {"error": "invalid signature", "detail": detail})
            return

        action = route.get("action")
        if action and action.get("command"):
            record["action"] = "spawned"
            threading.Thread(
                target=run_action,
                args=(route_name, action, body, event_type),
                daemon=True,
            ).start()

        append_log(record)
        self._respond(200, {"status": "ok", "route": route_name, "event": record["event"]})


# ========== COMMANDS ==========

def cmd_serve(args):
    routes = load_routes(args.routes)
    if args.host not in ("127.0.0.1", "localhost", "::1") and not args.allow_insecure_public:
        insecure = [n for n, r in routes.items() if r.get("provider", "generic") == "none"]
        if insecure:
            print(f"Refusing to bind {args.host}: routes without signature check: {', '.join(insecure)}")
            print("Use --allow-insecure-public to override (NOT recommended), or bind 127.0.0.1 "
                  "and expose via cloudflared/ngrok.")
            sys.exit(1)

    WebhookHandler.routes = routes
    WebhookHandler.path_index = {r["path"]: name for name, r in routes.items()}
    WebhookHandler.quiet = args.quiet

    try:
        httpd = ThreadingHTTPServer((args.host, args.port), WebhookHandler)
    except OSError as e:
        print(f"Cannot bind {args.host}:{args.port} — {e}")
        print("Port busy? Try another: serve --port 8788")
        sys.exit(1)

    print(f"Webhook server listening on http://{args.host}:{args.port}")
    print(f"Log dir: {DATA_DIR}")
    for name, r in routes.items():
        sec = f"secret_env={r['secret_env']}" if r.get("secret_env") else "no signature"
        act = " -> action" if r.get("action") else ""
        print(f"  POST {r['path']:<24} [{name}] provider={r.get('provider', 'generic')} ({sec}){act}")
    print("Ctrl+C to stop.")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


def cmd_test(args):
    routes = load_routes(args.routes)
    route = routes.get(args.route)
    if not route:
        print(f"Unknown route '{args.route}'. Available: {', '.join(routes.keys())}")
        sys.exit(1)
    provider = route.get("provider", "generic")

    if args.payload:
        body = Path(args.payload).read_bytes()
    else:
        body = json.dumps(SAMPLE_PAYLOADS.get(provider, {"event": "test"})).encode()

    secret = route_secret(route)
    headers = {"Content-Type": "application/json"}
    headers.update(build_signature_headers(provider, secret, body))
    if provider == "github":
        headers["X-GitHub-Event"] = "ping"
        headers["X-GitHub-Delivery"] = f"test-{int(time.time())}"

    url = f"http://{args.host}:{args.port}{route['path']}"
    import urllib.request
    import urllib.error
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_body = resp.read().decode("utf-8", errors="replace")
            status = resp.status
    except urllib.error.HTTPError as e:
        status = e.code
        resp_body = e.read().decode("utf-8", errors="replace")
    except urllib.error.URLError as e:
        print(f"Cannot reach {url} — is the server running?")
        print(f"Start it with:  python {Path(__file__).name} serve --port {args.port}")
        print(f"({e.reason})")
        sys.exit(1)

    if args.json:
        print(json.dumps({"url": url, "status": status, "response": resp_body}, ensure_ascii=False))
    else:
        print(f"POST {url}")
        print(f"Provider: {provider}  |  Signed: {'yes' if provider != 'none' else 'no (provider none)'}")
        print(f"HTTP {status}: {resp_body}")
    sys.exit(0 if status == 200 else 1)


def cmd_routes(args):
    path = Path(args.routes)
    if args.init:
        if path.exists() and not args.force:
            print(f"Config already exists: {path} (use --force to overwrite)")
            sys.exit(1)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(SAMPLE_ROUTES, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"Sample routes config written: {path}")
        print("Edit it, then set secret env vars in ~/.claude/.credentials.master.env")
        return
    if not path.exists():
        print(f"No routes config at {path}")
        print(f"Create a sample:  python {Path(__file__).name} routes --init")
        sys.exit(1)
    routes = json.loads(path.read_text(encoding="utf-8"))
    if args.json:
        print(json.dumps(routes, indent=2, ensure_ascii=False))
        return
    print(f"Routes config: {path}\n")
    for name, r in routes.items():
        env_name = r.get("secret_env", "")
        env_ok = "set" if env_name and os.environ.get(env_name) else ("MISSING" if env_name else "-")
        action = r.get("action") or {}
        print(f"  {name}")
        print(f"    path:     {r.get('path')}")
        print(f"    provider: {r.get('provider', 'generic')}")
        print(f"    secret:   {env_name or '(none)'} [{env_ok}]")
        print(f"    action:   {action.get('command') or '(log only)'}")


def cmd_tail(args):
    events = read_log_events(args.n, args.route)
    if args.json:
        print(json.dumps(events, indent=2, ensure_ascii=False))
        return
    if not events:
        print(f"No events logged yet (log dir: {DATA_DIR})")
        return
    for rec in reversed(events):  # oldest first
        if rec.get("kind") == "action_result":
            status = f"rc={rec.get('rc')}" + (f" {rec.get('error')}" if rec.get("error") else "")
            print(f"{rec.get('ts', '?')}  [action] {rec.get('route')}: {rec.get('command')} -> {status}")
            continue
        sig = "OK " if rec.get("signature_valid") else "BAD"
        payload_str = json.dumps(rec.get("payload"), ensure_ascii=False)
        if len(payload_str) > 120:
            payload_str = payload_str[:120] + "…"
        print(f"{rec.get('ts', '?')}  [{sig}] {rec.get('route')}/{rec.get('event')}  {payload_str}")


def cmd_verify(args):
    provider = args.provider
    if provider not in PROVIDERS or provider == "none":
        print(f"Provider must be one of: {', '.join(p for p in PROVIDERS if p != 'none')}")
        sys.exit(1)

    secret = args.secret or (os.environ.get(args.secret_env, "") if args.secret_env else "")
    if not secret:
        print("No secret. Pass --secret <value> or --secret-env <ENV_NAME> "
              "(env var from ~/.claude/.credentials.master.env)")
        sys.exit(1)

    if args.payload:
        body = Path(args.payload).read_bytes()
    else:
        body = json.dumps(SAMPLE_PAYLOADS.get(provider, {})).encode()

    headers = build_signature_headers(provider, secret, body)

    if args.signature:
        # Verify a given signature value against the payload
        header_name = list(headers.keys())[0]
        check_headers = {header_name: args.signature}
        ok, detail = validate_signature(provider, check_headers, body, secret)
        result = {"provider": provider, "verified": ok, "detail": detail}
        if args.json:
            print(json.dumps(result))
        else:
            print(f"Verification: {'VALID' if ok else 'INVALID'} ({detail})")
        sys.exit(0 if ok else 1)

    # Round-trip demo: compute headers, then validate them with our own checker
    ok, detail = validate_signature(provider, headers, body, secret)
    if args.json:
        print(json.dumps({"provider": provider, "headers": headers,
                          "self_check": ok, "detail": detail}, ensure_ascii=False))
    else:
        print(f"Provider: {provider}")
        print(f"Payload: {len(body)} bytes" + ("" if args.payload else " (built-in sample)"))
        for k, v in headers.items():
            print(f"  {k}: {v}")
        print(f"Self-check (compute -> validate): {'OK' if ok else 'FAIL'} ({detail})")
    sys.exit(0 if ok else 1)


# ========== MAIN ==========

def main():
    parser = argparse.ArgumentParser(
        prog="webhook_server.py",
        description="Webhook receiver: GitHub/Stripe/GitLab/forms -> JSONL log / command",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("serve", help="Run the webhook HTTP server (foreground)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--host", default=DEFAULT_HOST, help="Bind host (default 127.0.0.1)")
    p.add_argument("--routes", default=str(DEFAULT_ROUTES_FILE), help="Routes JSON config")
    p.add_argument("--quiet", action="store_true", help="Suppress per-request console lines")
    p.add_argument("--allow-insecure-public", action="store_true",
                   help="Allow provider 'none' routes on a non-loopback bind (dangerous)")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("test", help="Send a correctly-signed test payload to a running server")
    p.add_argument("route", help="Route name from routes.json")
    p.add_argument("--payload", help="JSON file to send (default: built-in sample)")
    p.add_argument("--port", type=int, default=DEFAULT_PORT)
    p.add_argument("--host", default=DEFAULT_HOST)
    p.add_argument("--routes", default=str(DEFAULT_ROUTES_FILE))
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_test)

    p = sub.add_parser("routes", help="Show (or --init create) routes config")
    p.add_argument("--routes", default=str(DEFAULT_ROUTES_FILE))
    p.add_argument("--init", action="store_true", help="Write a sample routes.json")
    p.add_argument("--force", action="store_true", help="Overwrite existing config with --init")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_routes)

    p = sub.add_parser("tail", help="Show last received events from JSONL log")
    p.add_argument("-n", type=int, default=20, help="Number of events (default 20)")
    p.add_argument("--route", help="Filter by route name")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_tail)

    p = sub.add_parser("verify", help="Compute/verify a provider signature on a sample payload")
    p.add_argument("provider", choices=[pr for pr in PROVIDERS if pr != "none"])
    p.add_argument("--payload", help="Payload file (default: built-in sample)")
    p.add_argument("--secret", help="Secret value (prefer --secret-env)")
    p.add_argument("--secret-env", help="Env var NAME holding the secret")
    p.add_argument("--signature", help="Signature/header value to verify against the payload")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_verify)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
