#!/usr/bin/env python3
"""<SERVICE> client skeleton: a command-line client for a web service that has no official CLI, SDK or MCP.

Copy to ~/.claude/tools/<service>_client.py, edit block 1 (CONFIG) and replace block 4 (EXAMPLE COMMANDS)
with the service's own commands. Keep the pattern: that is what the template is for.

What the template enforces
  1. --json everywhere (before or after the command). Success: ONE JSON object on stdout,
     {"ok": true, "data": ...}. Failure: stdout stays empty; stderr gets {"ok": false, "error": {...}}
     with --json, or "ERROR:" and "NEXT:" lines without it; the exit code is not 0.
     (doctor prints its report on stdout even when it fails: its exit code says whether it is healthy.)
  2. Every error names the next step (NEXT:). A raw 404, a stack trace or "failed" is not an answer.
  3. Exit codes: 0 ok · 1 failed · 2 wrong arguments · 3 configuration · 4 session (login needed or refused)
     · 5 refused: the action needs --yes.
  4. Reads run. Every change is a DRY RUN unless --apply. What costs money, messages people or cannot
     be undone ("paid") also needs --yes (--yes implies --apply). --dry-run always wins. The price
     is read BEFORE the first changing request, so the dry run can show it. Client.send refuses a
     changing request that did not pass gate(), so a command added later cannot forget the dry run.
  5. doctor = configuration + the current session by ONE safe read. It never logs in and never writes.
  6. api <path> = raw escape hatch. GET runs; any other method counts as paid (unknown cost).
     A full URL is accepted only for the same host: the session never leaves for another one.
  7. 401 (or whatever EXPIRED_* says) -> one silent re-login through login_hook(), one retry, and at most
     MAX_RELOGINS per run. A service that allows ONE session per account (SINGLE_SESSION = True) is never
     re-logged-in automatically: that would throw the other holder (a daemon, a browser tab) out.
     --no-relogin (or <SERVICE>_NO_RELOGIN=1) switches it off for one run. A re-login is the only
     write a dry run can make.
  8. Secrets come only from ~/.claude/.credentials.master.env, by NAME (set in CONFIG). Values are never
     printed and are masked in error text. The token minted at runtime lives in SESSION_FILE, under
     ~/.claude/.sessions/, outside any repository.
  9. Output is cut by items (and, past MAX_STRING characters, by string): still valid JSON, and "truncated" says what was cut.
     --limit 0 cuts nothing.

    python client_skeleton.py doctor
    python client_skeleton.py items --json
    python client_skeleton.py rename 5 "New name"            # dry run
    python client_skeleton.py rename 5 "New name" --apply    # really renames
    python client_skeleton.py buy SKU-1 --yes                # costs money: needs --yes
"""

import argparse
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ============================================================== 1. CONFIG: edit this block
SERVICE = "example"                        # short name; the env variable names below derive from it
ENV_PREFIX = SERVICE.upper()
BASE_URL = os.environ.get(ENV_PREFIX + "_BASE_URL", "https://app.example.com/api")  # no trailing slash
TOKEN_ENV = ENV_PREFIX + "_TOKEN"          # NAME of the variable holding a token you copied by hand, if any
LOGIN_ENVS = (ENV_PREFIX + "_EMAIL", ENV_PREFIX + "_PASSWORD")  # NAMES of the variables login_hook() uses
LOGIN_PATH = "/auth/login"                 # POST {"email", "password"} -> {"token": "..."}; None = no automatic login
LOGIN_TOKEN_KEY = "token"
DOCTOR_PATH = "/me"                        # ONE safe GET that proves the session works; None = configuration check only
SINGLE_SESSION = False                     # True: one session per account, so never re-login by itself
MAX_RELOGINS = 1                           # automatic re-logins per run: a loop of logins can lock the account
EXPIRED_STATUSES = (401,)                  # 403 is not here on purpose: it usually means "your plan has no such feature"
EXPIRED_BODY_MARKERS = ()                  # for services that answer 200 with an error body, e.g. ("token expired",)
LOGIN_URL_HINTS = ("login", "signin")      # a redirect to such a URL, or a login form instead of JSON, means: session gone
TIMEOUT_S = 30
DEFAULT_LIMIT = 100                        # list items kept per list in the output (--limit 0 = no cut at all)
MAX_STRING = 20000                         # characters kept per string in the output (--limit 0 lifts this cap too)
# Some services answer 403 to a bare client: copy the browser's headers from the api map (section 1) into this dict.
DEFAULT_HEADERS = {"Accept": "application/json", "User-Agent": SERVICE + "-client/1"}

CREDENTIALS_FILE = Path.home() / ".claude" / ".credentials.master.env"
SESSION_FILE = Path.home() / ".claude" / ".sessions" / (SERVICE + ".json")  # runtime token cache

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_CONFIG, EXIT_SESSION, EXIT_NEEDS_YES = 0, 1, 2, 3, 4, 5
READ, WRITE, PAID = "read", "write", "paid"
READ_METHODS = ("GET", "HEAD")
OPTION_DEFAULTS = {"json": False, "limit": DEFAULT_LIMIT, "no_relogin": False, "dry_run": False, "apply": False, "yes": False}
KINDS ={EXIT_FAIL: "failed", EXIT_USAGE: "usage", EXIT_CONFIG: "config", EXIT_SESSION: "session", EXIT_NEEDS_YES: "needs_yes"}

EPILOG = """exit codes:
  0  ok (a dry run is ok too)
  1  failed (HTTP error, network, unexpected response)
  2  wrong arguments
  3  configuration: a variable or the credentials file is missing (run doctor)
  4  session: login needed or refused (run doctor, then login)
  5  refused: this action costs money, messages people or cannot be undone: add --yes

changes: dry run by default; --apply runs reversible changes; --yes also confirms paid or irreversible ones
(and implies --apply); --dry-run always wins.
"""


def auth_headers(token):
    """EDIT: how the session is presented. Bearer token by default; for a cookie session use {"Cookie": "name=" + token}."""
    return {"Authorization": "Bearer " + token} if token else {}


# ============================================================== 2. PLUMBING: rarely needs edits
SECRET_VALUES = set()  # live secret values of this process; scrub() masks them in anything that gets printed


class CliError(Exception):
    def __init__(self, code, message, hint="", kind=None, **extra):
        super().__init__(message)
        self.code, self.message, self.hint = code, message, hint
        self.kind = kind or KINDS.get(code, "failed")
        self.extra = extra


def load_env():
    """Copy ~/.claude/.credentials.master.env into os.environ without overriding what is already set."""
    try:
        text = CREDENTIALS_FILE.read_text(encoding="utf-8-sig", errors="replace")  # -sig: a BOM from Notepad must not eat the first name
    except OSError:
        return False
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        value = value.strip().strip('"').strip("'")
        if key and not os.environ.get(key):
            os.environ[key] = value
    return True


def remember_secrets():
    """Register the secret values this client knows, so scrub() can mask them wherever they would be printed."""
    for name in (TOKEN_ENV,) + tuple(LOGIN_ENVS):
        remember(os.environ.get(name))


def remember(value):
    if isinstance(value, str) and len(value) >= 6:
        SECRET_VALUES.add(value)


def scrub(text, limit=200):
    for secret in sorted(SECRET_VALUES, key=len, reverse=True):
        text = text.replace(secret, "<secret>")
    return re.sub(r"[A-Za-z0-9_\-]{40,}", "<redacted>", text)[:limit]


def fingerprint(secret):
    """Short non-reversible tag of a secret ('' for none). The cache stores the tag of the TOKEN_ENV value that was current
    when it was written, so a token the owner pastes into TOKEN_ENV LATER is recognised as newer than the cache."""
    return hashlib.sha256(secret.encode("utf-8")).hexdigest()[:12] if secret else ""


def read_session():
    """(token, tag of the TOKEN_ENV value current at write time) from the session cache; (None, None) when unusable."""
    try:
        data = json.loads(SESSION_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None, None
    token = data.get("token") if isinstance(data, dict) else None
    if not (isinstance(token, str) and token):
        return None, None
    tag = data.get("env_fp")
    return token, tag if isinstance(tag, str) else None


def read_session_token():
    return read_session()[0]


def write_session_token(token):
    SESSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    tmp = SESSION_FILE.with_name(SESSION_FILE.name + ".tmp")
    tmp.write_text(json.dumps({"token": token, "saved_at": int(time.time()), "env_fp": fingerprint(os.environ.get(TOKEN_ENV))}),
                   encoding="utf-8")
    try:
        os.chmod(tmp, 0o600)
    except OSError:
        pass
    os.replace(tmp, SESSION_FILE)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        return None  # a redirect is an answer: "to /login" means the session is gone; urllib would also forward Authorization


class Reply:
    def __init__(self, status, headers, body):
        self.status, self.body = status, body
        self.headers = {str(k).lower(): v for k, v in (headers or {}).items()}

    @property
    def content_type(self):
        return self.headers.get("content-type", "")

    def text(self):
        return self.body.decode("utf-8", errors="replace")

    def json(self):
        try:
            return json.loads(self.text())
        except ValueError:
            return None


def default_transport(method, url, headers, body, timeout):
    request = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.build_opener(_NoRedirect).open(request, timeout=timeout) as resp:
            return resp.status, dict(resp.headers.items()), resp.read()
    except urllib.error.HTTPError as err:  # 3xx, 4xx, 5xx are answers, not exceptions
        return err.code, dict(err.headers.items()) if err.headers else {}, err.read()
    except (urllib.error.URLError, OSError) as err:
        raise CliError(EXIT_FAIL, "network error: %s" % getattr(err, "reason", err),
                       "check the connection and BASE_URL (%s)" % BASE_URL, kind="network")


URL_SAFE = "/:@!$&'()*+,;=-._~%"  # kept as typed; '%' too, so an address that is already encoded is not encoded twice


def check_path(path):
    """A path typed by a human: a line break, a tab or any other control character is a wrong argument, not a bug in the client."""
    for ch in path:
        if ord(ch) < 32 or ord(ch) == 127:
            raise CliError(EXIT_USAGE, "the path contains a control character (%r)" % ch,
                           "remove line breaks, tabs and other control characters from the path argument")


def encode_target(text):
    """'/my path', '/файл?q=a b' -> '/my%20path', '/%D1%84...?q=a%20b': the path and an inline query are percent-encoded (UTF-8),
    an existing %XX stays, the fragment is dropped (a client never sends it)."""
    path, q_sep, query = text.partition("#")[0].partition("?")
    return urllib.parse.quote(path, safe=URL_SAFE) + (q_sep + urllib.parse.quote(query, safe=URL_SAFE + "?") if q_sep else "")


def build_url(path, query=None):
    check_path(path)
    base = urllib.parse.urlsplit(BASE_URL)
    if path.startswith(("http://", "https://")):
        target = urllib.parse.urlsplit(path)
        if (target.scheme, target.netloc.lower()) != (base.scheme, base.netloc.lower()):
            raise CliError(EXIT_USAGE, "refusing to send the session to another host: %s" % target.netloc,
                           "pass a path relative to BASE_URL (%s)" % BASE_URL)
        url = "%s://%s%s" % (target.scheme, target.netloc, encode_target(target.path + ("?" + target.query if target.query else "")))
    else:
        url = BASE_URL.rstrip("/") + "/" + encode_target(path.lstrip("/"))
    if query:
        url += ("&" if "?" in url else "?") + urllib.parse.urlencode(query)
    return url


def looks_like_login_page(text):
    low = text[:6000].lower()
    return "<form" in low and any(m in low for m in ('type="password"', "type='password'", 'name="password"'))


def looks_expired(reply):
    """EDIT when the service signals a dead session some other way."""
    if reply.status in EXPIRED_STATUSES:
        return True
    if reply.status in (301, 302, 303, 307, 308):
        return any(h in reply.headers.get("location", "").lower() for h in LOGIN_URL_HINTS)
    if EXPIRED_BODY_MARKERS:
        head = reply.text()[:4096].lower()
        if any(m.lower() in head for m in EXPIRED_BODY_MARKERS):
            return True
    return reply.status == 200 and "html" in reply.content_type.lower() and looks_like_login_page(reply.text())


def ensure_ok(reply, method, path):
    """Return the reply for 2xx; otherwise raise an error that says what to do next."""
    if 200 <= reply.status < 300:
        return reply
    where = "%s %s" % (method.upper(), path)
    ctype, text = reply.content_type.lower(), reply.text()
    if reply.status == 404 and "html" in ctype:
        hint = ("HTML 404 from the web app instead of JSON: a required query parameter is probably missing "
                "(compare with the api map; see references/troubleshooting.md)")
    elif reply.status == 404 and "xml" in ctype:
        hint = "XML error: the request reached cloud storage, not the API. Check the host and the path prefix (references/troubleshooting.md)"
    elif reply.status == 403:
        hint = "forbidden: the plan or role has no such feature. This is not a session problem, re-login will not help"
    elif reply.status == 429:
        hint = "rate limited: wait and retry later; do not run requests in parallel"
    elif reply.status >= 500:
        hint = "server error: retry later; if it repeats for one request, a field is probably wrong: compare with the api map"
    elif 300 <= reply.status < 400:
        hint = "unexpected redirect to %s: the path is probably not an API route" % scrub(reply.headers.get("location", "?"))
    else:
        hint = "compare the request with the api map (path, required parameters, body fields)"
    raise CliError(EXIT_FAIL, "HTTP %d from %s" % (reply.status, where), hint, kind="http",
                   status=reply.status, detail=scrub(text))


def login_hook(client):
    """EDIT: how to get a fresh session. The default posts the e-mail and password named in LOGIN_ENVS.

    Services with 2FA, a captcha or a browser-only login cannot do this unattended: raise
    CliError(EXIT_SESSION, ..., hint=<the human step>) instead of guessing."""
    if not LOGIN_PATH:
        raise CliError(EXIT_SESSION, "session expired and no login hook is configured",
                       "log in by hand, put the new token into %s in ~/.claude/.credentials.master.env, then run: doctor" % TOKEN_ENV)
    user, password = (os.environ.get(name) for name in LOGIN_ENVS)
    if not user or not password:
        raise CliError(EXIT_CONFIG, "login needs %s and %s" % LOGIN_ENVS,
                       "add both names to ~/.claude/.credentials.master.env (values stay there, never in this file)")
    headers = dict(DEFAULT_HEADERS, **{"Content-Type": "application/json"})
    payload = json.dumps({"email": user, "password": password}).encode("utf-8")
    reply = Reply(*client.transport("POST", build_url(LOGIN_PATH), headers, payload, TIMEOUT_S))
    data = reply.json()
    token = data.get(LOGIN_TOKEN_KEY) if isinstance(data, dict) else None
    if reply.status >= 400 or not token:
        raise CliError(EXIT_SESSION, "login was refused (HTTP %d)" % reply.status,
                       "check the credentials; if the service asks for 2FA or a captcha, log in by hand and put the token into %s" % TOKEN_ENV)
    return token


class Client:
    def __init__(self, transport=None, allow_relogin=None):
        self.transport = transport or default_transport
        self.allow_relogin = (not SINGLE_SESSION) if allow_relogin is None else allow_relogin
        self.armed = False   # set only by gate(): a changing request is refused until then
        self.relogins = 0
        cached, cached_tag = read_session()
        env_token = os.environ.get(TOKEN_ENV)
        if cached and not (env_token and fingerprint(env_token) != cached_tag):
            self.token, self.token_source = cached, "session file"
        elif env_token:  # no cache, or the owner changed TOKEN_ENV after the cache was written: the hand-copied token is newer
            self.token, self.token_source = env_token, "env " + TOKEN_ENV
        else:
            self.token, self.token_source = None, "none"
        remember(self.token)

    def send(self, method, path, query=None, body=None):
        """One request, no retry, no re-login. A changing request must have passed gate() first."""
        method = method.upper()
        if method not in READ_METHODS and not self.armed:
            raise CliError(EXIT_FAIL, "bug: %s %s was attempted without passing gate()" % (method, path),
                           "call gate(c, args, risk, plan) before any changing request; reads need no gate", kind="bug")
        headers = dict(DEFAULT_HEADERS, **auth_headers(self.token))
        data = None
        if body is not None:
            data = body.encode("utf-8") if isinstance(body, str) else json.dumps(body).encode("utf-8")
            headers["Content-Type"] = "application/json"
        return Reply(*self.transport(method, build_url(path, query), headers, data, TIMEOUT_S))

    def relogin(self):
        if not self.allow_relogin:
            raise CliError(EXIT_SESSION, "session expired and automatic re-login is off (SINGLE_SESSION or --no-relogin)",
                           "if the service allows ONE session per account, make sure no other consumer holds it "
                           "(a daemon, a browser tab), then run: login (add --yes when SINGLE_SESSION)")
        if self.relogins >= MAX_RELOGINS:
            raise CliError(EXIT_SESSION, "session expired again in this run: not logging in a second time",
                           "run: doctor; if the account needs 2FA or was changed, log in by hand and update the credentials")
        self.relogins += 1
        self.token = login_hook(self)
        self.token_source = "session file"
        remember(self.token)
        write_session_token(self.token)

    def call(self, method, path, query=None, body=None, _retry=True):
        reply = self.send(method, path, query, body)
        if not looks_expired(reply):
            return reply
        if not _retry:
            raise CliError(EXIT_SESSION, "still unauthorized after re-login",
                           "the account may need 2FA or was changed: log in by hand, update the credentials, then run: doctor")
        self.relogin()
        return self.call(method, path, query, body, _retry=False)

    def get(self, path, query=None):
        return ensure_ok(self.call("GET", path, query), "GET", path)


# --------------------------------------------------------------- output
def cut(value, max_items, max_chars, path, notes):
    """Cut by items and characters but keep the JSON valid; every cut is written into notes."""
    if isinstance(value, dict):
        return {k: cut(v, max_items, max_chars, "%s.%s" % (path, k), notes) for k, v in value.items()}
    if isinstance(value, list):
        kept = [cut(v, max_items, max_chars, path + "[]", notes) for v in (value[:max_items] if max_items else value)]
        if max_items and len(value) > max_items:
            notes.append({"path": path, "kind": "items", "shown": max_items, "total": len(value)})
        return kept
    if isinstance(value, str) and max_chars and len(value) > max_chars:
        notes.append({"path": path, "kind": "chars", "shown": max_chars, "total": len(value)})
        return value[:max_chars]
    return value


def emit(args, payload, ok=True):
    """Success output on stdout: one JSON object with --json, readable JSON otherwise."""
    notes = []
    body = cut(payload, args.limit, MAX_STRING if args.limit else 0, "$", notes)  # --limit 0 lifts BOTH caps: the hint below promises everything
    out = dict({"ok": ok}, **body)
    if notes:
        out["truncated"] = notes
    if args.json:
        print(json.dumps(out, ensure_ascii=False, separators=(",", ":")))
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))
        if notes:
            print("(output cut: %s; use --limit 0 for everything)" % ", ".join("%s %s %d of %d" % (n["path"], n["kind"], n["shown"], n["total"]) for n in notes),
                  file=sys.stderr)


def fail(args, err):
    if getattr(args, "json", False):
        error = {"kind": err.kind, "exit": err.code, "message": err.message, "hint": err.hint}
        error.update(err.extra)
        print(json.dumps({"ok": False, "error": error}, ensure_ascii=False), file=sys.stderr)
    else:
        print("ERROR: %s" % err.message, file=sys.stderr)
        if err.hint:
            print("NEXT: %s" % err.hint, file=sys.stderr)
    return err.code


def reply_data(reply):
    parsed = reply.json()
    if parsed is not None:
        return parsed
    return {"content_type": reply.content_type, "text": reply.text()}


def gate(c, args, risk, plan):
    """The ONE place where a change is allowed to run. True = go on; False = a dry run was printed instead."""
    if risk == READ:
        return True
    if args.dry_run or not (args.apply or args.yes):
        step = "--yes (it costs money, messages people or cannot be undone)" if risk == PAID else "--apply"
        emit(args, {"dry_run": True, "risk": risk, "plan": plan, "hint": "dry run: nothing was changed. Add %s to run it" % step})
        return False
    if risk == PAID and not args.yes:
        raise CliError(EXIT_NEEDS_YES, "this action costs money, messages people or cannot be undone: %s" % plan.get("summary", "?"),
                       "run it without --apply first to read the plan, then add --yes", kind="needs_yes", plan=plan)
    c.armed = True
    return True


def parse_data(text):
    if text is None:
        return None
    try:
        return json.loads(text)
    except ValueError as exc:
        raise CliError(EXIT_USAGE, "--data is not valid JSON: %s" % exc, 'pass a JSON string, e.g. --data \'{"name": "x"}\'')


def limit_arg(text):
    """argparse type for --limit: 0 means everything; a negative number would silently cut items off the END of a list."""
    try:
        value = int(text)
    except ValueError:
        raise argparse.ArgumentTypeError("not a number: %r" % text)
    if value < 0:
        raise argparse.ArgumentTypeError("must be 0 (everything) or a positive number, got %s" % text)
    return value


def parse_pairs(pairs):
    out = {}
    for item in pairs or []:
        key, sep, value = item.partition("=")
        if not sep or not key:
            raise CliError(EXIT_USAGE, "--query expects key=value, got %r" % item, "example: --query page=2 --query per_page=50")
        out[key] = value
    return out


# ============================================================== 3. BUILT-IN COMMANDS: doctor, login, api
def cmd_doctor(c, args):
    checks = []

    def add(name, ok, detail, fix=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail, **({"fix": fix} if fix and not ok else {})})

    have_login = bool(LOGIN_PATH) and all(os.environ.get(n) for n in LOGIN_ENVS)
    have_file = CREDENTIALS_FILE.exists()
    add("credentials file", have_file, "~/.claude/.credentials.master.env " + ("present" if have_file else "not found"),
        "create ~/.claude/.credentials.master.env and add %s (or the login pair %s)" % (TOKEN_ENV, "/".join(LOGIN_ENVS)))
    if c.token:
        auth_detail = "token from " + c.token_source
    elif have_login:
        auth_detail = "no token yet; %s set, so login can mint one" % "/".join(LOGIN_ENVS)
    else:
        auth_detail = "no token (%s) and no login pair (%s)" % (TOKEN_ENV, "/".join(LOGIN_ENVS))
    add("authentication", c.token or have_login, auth_detail,
        "add %s (or %s) to ~/.claude/.credentials.master.env" % (TOKEN_ENV, " and ".join(LOGIN_ENVS)))
    parts = urllib.parse.urlsplit(BASE_URL)
    local = parts.hostname in ("localhost", "127.0.0.1", "::1")
    add("base url", parts.scheme in ("http", "https") and bool(parts.netloc) and (parts.scheme == "https" or local),
        "%s://%s" % (parts.scheme, parts.netloc), "BASE_URL must be an https URL")
    add("session file", True, ("present, saved %ds ago" % (time.time() - SESSION_FILE.stat().st_mtime)) if SESSION_FILE.exists() else "absent (nothing cached yet)")
    code, nxt = EXIT_OK, ""
    if not all(ch["ok"] for ch in checks):
        code = EXIT_CONFIG
        nxt = next(ch["fix"] for ch in checks if not ch["ok"])
    elif args.offline or not DOCTOR_PATH:
        add("live read", True, "skipped (%s)" % ("--offline" if args.offline else "DOCTOR_PATH is not set"))
    elif not c.token:
        add("live read", False, "no session yet: nothing to test", "run: login")
        code, nxt = EXIT_SESSION, "run: login"
    else:
        try:
            reply = c.send("GET", DOCTOR_PATH)
        except CliError as err:
            add("live read", False, "unreachable: %s" % err.message, err.hint)
            code, nxt = EXIT_FAIL, err.hint
        else:
            if looks_expired(reply):
                fix = ("make sure nobody else holds the session, then run: login --yes" if SINGLE_SESSION else "run: login")
                add("live read", False, "GET %s -> session expired (HTTP %d)" % (DOCTOR_PATH, reply.status), fix)
                code, nxt = EXIT_SESSION, fix
            elif 200 <= reply.status < 300:
                add("live read", True, "GET %s -> %d, session valid" % (DOCTOR_PATH, reply.status))
            else:
                add("live read", False, "GET %s -> HTTP %d" % (DOCTOR_PATH, reply.status), "compare DOCTOR_PATH with the api map")
                code, nxt = EXIT_FAIL, "compare DOCTOR_PATH with the api map"
    report = {"ok": code == EXIT_OK, "checks": checks, "next": nxt}
    print(json.dumps(report, ensure_ascii=False, indent=None if args.json else 2,
                     separators=(",", ":") if args.json else None))
    return code


def cmd_login(c, args):
    plan = {"method": "POST", "path": LOGIN_PATH, "summary": "log in again and cache the session"}
    if SINGLE_SESSION:
        plan["note"] = "this service allows one session per account: it ends the session of any other holder"
        if not gate(c, args, PAID, plan):
            return None
    elif args.dry_run:  # --dry-run always wins; without it a login on a many-sessions service runs at once
        emit(args, {"dry_run": True, "risk": WRITE, "plan": plan, "hint": "dry run: nothing was changed. Run it without --dry-run to log in"})
        return None
    c.token = login_hook(c)
    remember(c.token)
    write_session_token(c.token)
    emit(args, {"data": {"logged_in": True, "session_file": SESSION_FILE.name}})


def cmd_api(c, args):
    check_path(args.path)  # also on a dry run: a changing call must not look fine in the plan and fail on --apply
    method = args.method.upper()
    query, body = parse_pairs(args.query), parse_data(args.data)
    plan = {"method": method, "path": args.path, "query": query, "body": body, "summary": "%s %s" % (method, args.path)}
    if not gate(c, args, READ if method in READ_METHODS else PAID, plan):
        return None
    reply = ensure_ok(c.call(method, args.path, query, body), method, args.path)
    emit(args, {"status": reply.status, "data": reply_data(reply)})


# ============================================================== 4. EXAMPLE COMMANDS: replace with the service's own
def cmd_items(c, args):
    """READ: runs at once."""
    reply = c.get("/items", {"page": args.page})
    emit(args, {"data": reply_data(reply)})


def cmd_rename(c, args):
    """WRITE (reversible): a dry run unless --apply."""
    plan = {"method": "PUT", "path": "/items/%s" % args.id, "body": {"name": args.name}, "summary": "rename item %s" % args.id}
    if not gate(c, args, WRITE, plan):
        return None
    reply = ensure_ok(c.call("PUT", plan["path"], body=plan["body"]), "PUT", plan["path"])
    emit(args, {"data": reply_data(reply)})


def cmd_buy(c, args):
    """PAID: the price is READ first (a plain GET) and shown in the plan; the changing request needs --yes."""
    quote = reply_data(c.get("/quote", {"sku": args.sku}))
    plan = {"method": "POST", "path": "/buy", "body": {"sku": args.sku, "qty": args.qty}, "cost": quote, "summary": "buy %s x%d" % (args.sku, args.qty)}
    if not gate(c, args, PAID, plan):
        return None
    reply = ensure_ok(c.call("POST", "/buy", body=plan["body"]), "POST", "/buy")
    emit(args, {"data": reply_data(reply)})


# ============================================================== 5. PARSER AND ENTRY POINT
WANT_JSON = False  # set by main() from argv: argparse raises usage errors before there are any args to ask


class ArgumentParser(argparse.ArgumentParser):
    """Usage errors follow the contract of every other error: ERROR and NEXT lines, or one JSON object with --json; exit 2.
    The class keeps the stdlib name on purpose: gen_commands.py recognises a parser by that name, so the command table still works."""

    def error(self, message):
        raise SystemExit(fail(argparse.Namespace(json=WANT_JSON), CliError(EXIT_USAGE, message, "run: %s --help" % self.prog)))


def build_parser():
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="machine-readable output: one JSON object")
    common.add_argument("--limit", type=limit_arg, default=argparse.SUPPRESS, help="list items kept per list (default %d); strings are cut at %d characters; 0 = no cut at all" % (DEFAULT_LIMIT, MAX_STRING))
    common.add_argument("--no-relogin", action="store_true", default=argparse.SUPPRESS,
                        help="never log in by itself on a 401 (use when another process may hold the only session)")
    changing = argparse.ArgumentParser(add_help=False)
    changing.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS, help="print the plan, change nothing (always wins)")
    changing.add_argument("--apply", action="store_true", default=argparse.SUPPRESS, help="run a reversible change (default is a dry run)")
    changing.add_argument("--yes", action="store_true", default=argparse.SUPPRESS, help="confirm a paid or irreversible action; implies --apply")

    ap = ArgumentParser(prog=Path(__file__).name, description="Client for %s (copy of client_skeleton.py)." % SERVICE,
                                 epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter, parents=[common])
    # No ap.set_defaults(json=False, ...) here: it would overwrite the SUPPRESS default of the option objects that the
    # top-level parser shares with every subparser, and a flag written BEFORE the command would be lost. main() fills
    # OPTION_DEFAULTS in after parsing instead.
    sub = ap.add_subparsers(dest="command", required=True, metavar="COMMAND")

    p = sub.add_parser("doctor", parents=[common], help="check configuration and the current session (one safe read, no login, no writes)")
    p.add_argument("--offline", action="store_true", help="skip the live read")
    p.set_defaults(func=cmd_doctor)

    p = sub.add_parser("login", parents=[common, changing], help="log in again and cache the session (ends other sessions if SINGLE_SESSION)")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("api", parents=[common, changing], help="raw call; GET runs, any other method is treated as paid")
    p.add_argument("path", help="path relative to BASE_URL (a full URL only for the same host)")
    p.add_argument("--method", default="GET", help="HTTP method (default GET)")
    p.add_argument("--data", help="JSON request body")
    p.add_argument("--query", action="append", help="key=value, repeatable")
    p.set_defaults(func=cmd_api)

    p = sub.add_parser("items", parents=[common], help="EXAMPLE read: list items")
    p.add_argument("--page", type=int, default=1)
    p.set_defaults(func=cmd_items)

    p = sub.add_parser("rename", parents=[common, changing], help="EXAMPLE reversible change: rename an item (dry run unless --apply)")
    p.add_argument("id")
    p.add_argument("name")
    p.set_defaults(func=cmd_rename)

    p = sub.add_parser("buy", parents=[common, changing], help="EXAMPLE paid action: price is read first; needs --yes")
    p.add_argument("sku")
    p.add_argument("--qty", type=int, default=1)
    p.set_defaults(func=cmd_buy)
    return ap


def main(argv=None, transport=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    global WANT_JSON
    WANT_JSON = "--json" in (sys.argv[1:] if argv is None else list(argv))
    args = build_parser().parse_args(argv)
    for name, value in OPTION_DEFAULTS.items():
        if not hasattr(args, name):
            setattr(args, name, value)
    try:
        load_env()
        remember_secrets()
        no_relogin = args.no_relogin or bool(os.environ.get(ENV_PREFIX + "_NO_RELOGIN"))
        result = args.func(Client(transport=transport, allow_relogin=False if no_relogin else None), args)
        return result if isinstance(result, int) else EXIT_OK
    except CliError as err:
        return fail(args, err)
    except Exception as exc:  # a bug must still end as a readable error with an exit code
        if os.environ.get(ENV_PREFIX + "_DEBUG"):
            raise
        return fail(args, CliError(EXIT_FAIL, "unexpected error: %s: %s" % (type(exc).__name__, scrub(str(exc))),
                                   "this is a bug in the client; re-run with %s_DEBUG=1 to see the traceback" % ENV_PREFIX))


if __name__ == "__main__":
    sys.exit(main())
