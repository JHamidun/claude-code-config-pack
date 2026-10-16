#!/usr/bin/env python3
"""Record the internal API of a web service from YOUR OWN logged-in browser session.

One file, stdlib only (the browser engine is imported lazily, only by `capture`).

    capture    open a browser with a persistent profile, wait until you are logged in, walk
               the routes and write what the page calls into out/:
               api_map.json (every XHR/fetch), endpoints.md (table for the api-map),
               auth_hints.json (HOW auth works: cookie TTLs, JWT lifetimes, header names),
               routes.json
    summarize  offline: turn a saved api_map.json into the endpoint table; no browser, no network
    bundles    offline: list API-looking paths in saved JS bundles; no browser, no network

    python harvest.py capture --url https://app.example.com/ --route '#/billing' --discover
    python harvest.py summarize out/api_map.json > endpoints.md
    python harvest.py bundles out/bundles --grep refund

Rules baked in
  * Your own account only. YOU log in, in the window that opens (2FA and captcha are human
    steps); the profile keeps the session, so it happens once. This script never types or
    stores credentials.
  * Headed by default: bot protection often answers a headless browser with a ~100 byte stub
    instead of the JS bundles. --headless is for a profile that is already warm.
  * Redacted by default: cookies, tokens, passwords and JWTs are masked in everything written
    to out/ (names, shapes and lifetimes stay). Masking goes by field name (English, Portuguese,
    Spanish, French, German and Russian password words, compound names like user_pwd or oldPass)
    and by value shape, and EVERY value in the request body of a login-like endpoint is masked (and every token-shaped
    string in its response, whatever the field is called; /graphql counts as login-like when the query names a login).
    It is a safety net, not a proof: read out/ before you hand it to anyone. --keep-secrets
    switches masking off; then out/ must stay out of git.
  * Walking routes only navigates (GET). Nothing is clicked. Routes that look like logout or
    delete are skipped with a [skip] line (--discover never visits them; only --allow-route does).
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qsl, unquote_plus, urljoin, urlsplit

EXIT_OK, EXIT_FAIL, EXIT_USAGE, EXIT_LOGIN = 0, 1, 2, 4

EPILOG = """exit codes:
  0  done
  1  failed (unreadable input, browser engine missing, capture error)
  2  wrong arguments
  4  capture: login was not completed in time (log in once in the window, or raise --login-wait)
"""

DEFAULT_INCLUDE = ("/api/", "/rest/", "graphql", "/trpc/", "/v1/", "/v2/", "/v3/")
DEFAULT_EXCLUDE = (
    "mixpanel", "posthog", "sentry", "google-analytics", "googletagmanager", "segment.io",
    "segment.com", "hotjar", "amplitude", "datadoghq", "doubleclick", "clarity.ms",
    "/track/", "/engage/", "/collect?", "/beacon",
)
# '/sso' and 'sso.' instead of a bare 'sso': the bare word sits inside '/lessons/1' and would hold a logged-in page for the whole --login-wait
DEFAULT_LOGIN_HINTS = ("login", "signin", "sign-in", "/sso", "sso.")
# Navigating to these with GET can end the session or change data: never visited by --discover.
UNSAFE_ROUTE_WORDS = (
    "logout", "log-out", "signout", "sign-out", "sair", "exit", "delete", "remove", "destroy",
    "unsubscribe", "cancel", "deactivate", "disconnect", "revoke",
)
RISK_WORDS = (
    "pay", "pagar", "checkout", "charge", "purchase", "buy", "order", "subscribe", "subscription",
    "invoice", "billing", "refund", "recalc", "upgrade", "withdraw", "transfer", "send", "publish",
    "delete", "remove", "destroy", "cancel", "unsubscribe", "revoke", "confirm",
)
# "/sso", not "sso": the bare word sits inside "/lessons/1" and would flag it as an auth endpoint
AUTH_PATH_WORDS = ("auth", "session", "token", "login", "oauth", "/sso", "refresh")
# Request bodies sent to a URL whose path holds one of these are masked WHOLE (every value, keys stay): whatever a login form
# calls its password field, it cannot slip through. Broad on purpose: a masked example is a small loss, a leaked password is not.
SECRET_BODY_PATH_WORDS = AUTH_PATH_WORDS + ("signin", "sign-in", "password", "senha", "otp", "2fa", "mfa", "signup", "sign-up",
                                            "register", "verify", "credential",
                                            # Devise (/users/sign_in), Portuguese (/entrar, /acesso), ASP.NET (/Account/Logon), German (/anmelden)
                                            "sign_in", "sign_up", "log-in", "log_in", "entrar", "acesso", "logon", "anmelden")
# /graphql is one URL for everything, so it counts as a login endpoint only when the operation name or the query text names one
# ('auth' but not 'author': a book query with an author field is not a login)
GRAPHQL_SECRET_RE = re.compile(r"(?i)login|sign[_-]?in|token|password|auth(?!or)")
READ_METHODS = ("GET", "HEAD", "OPTIONS")

# A field is secret when its name, with case and separators removed, contains one of these.
SENSITIVE_PARTS = (
    "token", "secret", "password", "passwd", "passw", "passcode", "passphrase", "pwd", "authorization", "cookie", "session",
    "sessid", "apikey", "csrf", "xsrf", "signature", "credential", "privatekey", "accesskey", "bearer", "jwt",
    "cardnumber", "cvv", "cvc", "securitycode",
    # other languages: pt senha, es contraseña, fr mot de passe, pt-PT palavra-passe, de Kennwort, ru пароль / parol / секрет / токен
    "senha", "contrase", "motdepasse", "palavrapasse", "kennwort", "парол", "parol", "секрет", "токен",
)
SENSITIVE_EXACT = {"key", "pwd", "pass", "sig", "auth", "jwt", "otp", "pin"}
# Short roots are matched as WHOLE words of the name split on case and separators ('oldPass', 'login_pass', 'X-Otp-Code'):
# a substring test would hit 'footprint', 'spinner' or 'enclave'. Suffixes catch the glued forms: userpass, loginpw.
SENSITIVE_WORDS = {"pw", "psw", "pass", "otp", "totp", "hotp", "mdp", "clave", "pin", "jwt"}
SENSITIVE_SUFFIXES = ("pass", "psw", "pw", "otp")
SENSITIVE_PREFIXES = ("otp",)
# Names that also mean something harmless ('country_code', 'status_code', 'ticket' as a helpdesk object): masked only when
# the VALUE looks like a credential (a one-time code, a CAS ticket, a session id).
WEAK_WORDS = {"code", "codigo", "ticket", "sid"}
# name/value pair objects: {"name": "access_token", "value": "..."} (cookie lists, HAR headers, form-field arrays)
PAIR_NAME_KEYS = ("name", "key", "field", "header", "param")
PAIR_VALUE_KEYS = ("value", "val", "content")

JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*")
BEARER_RE = re.compile(r"(?i)\b(bearer|basic)\s+[A-Za-z0-9._~+/=-]{8,}")
LONG_TOKEN_RE = re.compile(r"\b[A-Za-z0-9_-]{40,}\b")
# "token": "value" inside JSON that is cut off or not valid JSON
KV_RE = re.compile(r'("[^"\\]{0,60}"\s*:\s*)"([^"\\]{1,2000})"')
# name=value&name=value: a urlencoded body, a query string, a hash fragment that carries a token
FORM_RE = re.compile(r"[^\s=&]+=[^\s&]*(&[^\s=&]+=[^\s&]*)*")
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")

SHAPE_DEPTH = 4
SHAPE_KEYS = 40


# --------------------------------------------------------------------------- redaction
def _norm(name):
    """Lower-case letters and digits only (unicode-aware, so Cyrillic names survive)."""
    return re.sub(r"[\W_]+", "", str(name).lower())


def _words(name):
    """'oldPass', 'login_pass', 'X-Otp-Code', 'OTPCode' -> ['old', 'pass'], ['login', 'pass'], ['x', 'otp', 'code'], ['otp', 'code']."""
    spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", str(name))
    spaced = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", spaced)
    return [w for w in re.split(r"[\W_]+", spaced.lower()) if w]


def is_sensitive_key(name):
    """True when a field of this name is a secret whatever it holds (password, token, cookie, secret, in several languages)."""
    norm = _norm(name)
    return (norm in SENSITIVE_EXACT or any(p in norm for p in SENSITIVE_PARTS)
            or any(w in SENSITIVE_WORDS or w.startswith(SENSITIVE_PREFIXES) or w.endswith(SENSITIVE_SUFFIXES)
                   for w in _words(name) + [norm]))


def looks_like_credential(value):
    """A one-time code, a ticket, a session id: 4+ token characters with at least one digit. Prose, plain words and booleans are not."""
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return False
    text = str(value).strip()
    return bool(re.fullmatch(r"[A-Za-z0-9._~/+=:-]{4,}", text)) and any(ch.isdigit() for ch in text)


def is_sensitive_field(name, value=None):
    """True when the VALUE under this name must be masked: a secret name, or a code/ticket/sid name carrying a credential-looking value."""
    return is_sensitive_key(name) or (any(w in WEAK_WORDS for w in _words(name)) and looks_like_credential(value))


def _is_scalar(value):
    return isinstance(value, (str, int, float)) and not isinstance(value, bool)


def _pair_value_keys(obj):
    """Keys holding the value of a {'name': 'access_token', 'value': '...'} pair whose NAME is secret."""
    lower = {str(k).lower(): k for k in obj}
    hidden = set()
    for vk in PAIR_VALUE_KEYS:
        if vk in lower and _is_scalar(obj[lower[vk]]):
            for nk in PAIR_NAME_KEYS:
                if nk in lower and isinstance(obj[lower[nk]], str) and is_sensitive_field(obj[lower[nk]], obj[lower[vk]]):
                    hidden.add(lower[vk])
    return hidden


def redact_text(text):
    """Mask JWTs, Bearer/Basic credentials and long opaque tokens inside free text."""
    text = JWT_RE.sub("<jwt>", text)
    text = BEARER_RE.sub(lambda m: m.group(1) + " <redacted>", text)
    return LONG_TOKEN_RE.sub(lambda m: "<redacted:len=%d>" % len(m.group(0)), text)


def redact_kv_text(text):
    def repl(m):
        key = m.group(1).split(":")[0].strip().strip('"')
        return m.group(1) + '"<redacted>"' if is_sensitive_field(key, m.group(2)) else m.group(0)

    return KV_RE.sub(repl, text)


def _redact_embedded(text):
    """A string value that is itself JSON, a form or a URL (payload wrappers, redirect links) is redacted by its own rules."""
    stripped = text.strip()
    if stripped[:1] in ("{", "[") and len(stripped) > 1:
        try:
            return json.dumps(redact_json(json.loads(stripped)), ensure_ascii=False)
        except ValueError:
            return text
    if re.match(r"https?://\S+$", stripped):
        return redact_url(stripped)
    if "=" in stripped and FORM_RE.fullmatch(stripped):
        return redact_form(stripped)
    return text


def redact_json(obj):
    if isinstance(obj, dict):
        hidden = _pair_value_keys(obj)
        return {
            k: ("<redacted>" if (k in hidden or is_sensitive_field(k, v)) and v is not None and not isinstance(v, bool)
                else redact_json(v))
            for k, v in obj.items()
        }
    if isinstance(obj, list):
        return [redact_json(v) for v in obj]
    if isinstance(obj, str):
        return redact_text(_redact_embedded(obj))
    return obj


def mask_scalars(obj):
    """Strict mode: keep the keys (the shape of the request), hide every value."""
    if isinstance(obj, dict):
        return {k: mask_scalars(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask_scalars(v) for v in obj]
    return "<redacted>" if _is_scalar(obj) else obj


def redact_form(body, strict=False):
    """name=value&name=value: sensitive names lose their value (strict: every field does), the rest is scanned for tokens."""
    parts = []
    for piece in body.split("&"):
        name, sep, value = piece.partition("=")
        secret = sep and (strict or is_sensitive_field(unquote_plus(name), unquote_plus(value)))
        parts.append(name + sep + ("<redacted>" if secret else redact_text(value)))
    return "&".join(parts)


def is_secret_body_url(url, body=None):
    """True for the endpoints whose bodies carry credentials: login, session, token, password, sign-up ...
    Case does not matter. A /graphql call counts only when its operation name or query text (body, or the query string of a GET) names a login."""
    parts = urlsplit(url)
    path = parts.path.lower()
    if any(w in path for w in SECRET_BODY_PATH_WORDS):
        return True
    return "graphql" in path and bool(GRAPHQL_SECRET_RE.search("%s %s" % (body or "", unquote_plus(parts.query))))


TOKEN_SHAPE_RE = re.compile(r"[A-Za-z0-9_\-.=/+]{16,}")


def mask_token_values(obj):
    """Response of a login-like endpoint: keys stay, and so does every short or ordinary value, but any string that has the shape
    of a token (16+ letters, digits and _-.=/+) goes, whatever its field is called ('access', 'refresh', 't')."""
    if isinstance(obj, dict):
        return {k: mask_token_values(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [mask_token_values(v) for v in obj]
    if isinstance(obj, str) and TOKEN_SHAPE_RE.fullmatch(obj.strip()):
        return "<redacted>"
    return obj


def redact_body(body, content_type="", strict=False, tokens=False):
    """Redact a request/response body: JSON by key, forms by field name, everything else by pattern.
    strict (the request body of a login-like endpoint): every value goes, only the keys stay; a body that is neither JSON nor a form goes whole.
    tokens (the response of a login-like endpoint): on top of the normal rules, every token-shaped string value goes."""
    stripped = body.strip()
    if stripped[:1] in ("{", "["):
        try:
            data = json.loads(stripped)
        except ValueError:
            if strict:
                return "<redacted:len=%d>" % len(body)
            if tokens:  # cut-off JSON: the same rule, on the "key": "value" pairs
                body = KV_RE.sub(lambda m: m.group(1) + '"<redacted>"' if TOKEN_SHAPE_RE.fullmatch(m.group(2)) else m.group(0), body)
            return redact_text(redact_kv_text(body))
        if strict:
            data = mask_scalars(data)
        else:
            data = redact_json(data)
            if tokens:
                data = mask_token_values(data)
        return json.dumps(data, ensure_ascii=False)
    if "x-www-form-urlencoded" in content_type.lower() or FORM_RE.fullmatch(stripped or " "):
        return redact_form(body, strict)
    return "<redacted:len=%d>" % len(body) if strict else redact_text(body)


def redact_url(url):
    """Mask secrets in the query and in what hash-routed apps keep after the '#': a '?query' or a bare 'access_token=...'."""
    main, hash_sep, frag = url.partition("#")
    base, q_sep, query = main.partition("?")
    out = redact_text(base) + (q_sep + redact_form(query) if q_sep else "")
    if hash_sep:
        fpath, fq_sep, fquery = frag.partition("?")
        out += "#" + (redact_form(fpath) if "=" in fpath and FORM_RE.fullmatch(fpath) else redact_text(fpath)) \
            + (fq_sep + redact_form(fquery) if fq_sep else "")
    return out


URL_IN_TEXT_RE = re.compile(r"https?://[^\s\"'<>]+")


def redact_urls_in_text(text):
    """Free text that embeds URLs (a browser error such as 'navigating to "https://...?token=..."'): each URL is masked like a stored one."""
    return URL_IN_TEXT_RE.sub(lambda m: redact_url(m.group(0)), str(text))


def shown_url(args, url):
    """A URL going into a log line, a file name or a file in out/: masked unless --keep-secrets."""
    return url if getattr(args, "keep_secrets", False) else redact_url(url)


def shown_text(args, text):
    """Same for free text that may contain URLs."""
    return str(text) if getattr(args, "keep_secrets", False) else redact_urls_in_text(text)


def cookie_names_from_cookie_header(value):
    value = str(value or "")
    if value.startswith("<cookie names:"):
        inner = value[len("<cookie names:"):]
        inner = inner[:-1] if inner.endswith(">") else inner  # ONE closing bracket: a masked name such as '<email>' ends with one too
        return [n.strip() for n in inner.split(",") if n.strip()]
    return [p.split("=", 1)[0].strip() for p in value.split(";") if "=" in p]


def cookie_names_from_set_cookie(value):
    """Names from a (possibly merged, newline-separated) Set-Cookie header value."""
    names = []
    for line in str(value or "").splitlines():
        first = line.split(";", 1)[0]
        if "=" in first:
            names.append(first.split("=", 1)[0].strip())
    return names


def redact_headers(headers):
    out = {}
    for name, value in (headers or {}).items():
        low = name.lower()
        value = str(value)
        if low == "cookie":
            out[name] = "<cookie names: %s>" % ", ".join(mask_name(n) for n in cookie_names_from_cookie_header(value))
        elif low == "set-cookie":
            out[name] = "<set-cookie names: %s>" % ", ".join(mask_name(n) for n in cookie_names_from_set_cookie(value))
        elif low in ("authorization", "proxy-authorization"):
            scheme = value.split(" ", 1)[0] if " " in value else "(no scheme)"
            out[name] = scheme + " <redacted>"
        elif is_sensitive_field(name, value):  # the original spelling: 'X-OtpCode' still splits into words
            out[name] = "<redacted>"
        else:
            out[name] = redact_text(value)
    return out


# --------------------------------------------------------------------------- jwt and auth hints
def _b64json(segment):
    segment += "=" * (-len(segment) % 4)
    return json.loads(base64.urlsafe_b64decode(segment.encode("ascii")).decode("utf-8"))


def jwt_claims(token):
    """Lifetime metadata of a JWT (alg, typ, exp, iat, lifetime). Never returns subject, e-mail or any payload value beyond these."""
    token = str(token or "").strip()
    parts = token.split(".")
    if len(parts) < 2 or not token.startswith("eyJ"):
        return None
    try:
        header, payload = _b64json(parts[0]), _b64json(parts[1])
    except Exception:
        return None
    out = {}
    if isinstance(header, dict):
        for k in ("alg", "typ"):
            if isinstance(header.get(k), str):
                out["header_" + k] = header[k]
    if isinstance(payload, dict):
        for k in ("exp", "iat", "nbf"):
            if isinstance(payload.get(k), (int, float)) and not isinstance(payload.get(k), bool):
                out[k] = int(payload[k])
        if isinstance(payload.get("typ"), str):
            out["typ"] = payload["typ"]
    if "exp" in out and "iat" in out:
        out["lifetime_s"] = out["exp"] - out["iat"]
    return out or None


def humanize_seconds(seconds):
    sign = "-" if seconds < 0 else ""
    s = abs(int(seconds))
    if s < 120:
        return "%s%ds" % (sign, s)
    if s < 2 * 3600:
        return "%s%dm" % (sign, s // 60)
    if s < 48 * 3600:
        return "%s%dh" % (sign, s // 3600)
    return "%s%dd" % (sign, s // 86400)


def scan_jwts(obj, path="$", depth=0, found=None):
    """Find JWTs inside parsed JSON (e.g. localStorage.workspaceList[].workspaceToken): [(json path, claims)]."""
    found = [] if found is None else found
    if depth > 6 or len(found) >= 20:
        return found
    if isinstance(obj, dict):
        for k, v in obj.items():
            scan_jwts(v, "%s.%s" % (path, mask_name(k)), depth + 1, found)  # a key can be an e-mail or an id: the path lands in auth_hints.json
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:20]):
            scan_jwts(v, "%s[%d]" % (path, i), depth + 1, found)
    elif isinstance(obj, str):
        claims = jwt_claims(obj.replace("Bearer ", "").replace("bearer ", ""))
        if claims:
            found.append((path, claims))
    return found


def _mask_ids(key):
    key = UUID_RE.sub("<id>", key)
    return re.sub(r"\d{6,}", "<id>", key)


def mask_name(name):
    """Cookie and storage-key names go into auth_hints.json, which is meant to be pasted into the api map: an e-mail or an id inside a name is masked."""
    return None if name is None else _shape_key(name)


def _lifetime_note(claims, now):
    if not claims:
        return {}
    note = {}
    if "lifetime_s" in claims:
        note["lifetime"] = humanize_seconds(claims["lifetime_s"])
    if "exp" in claims:
        note["expires_in"] = humanize_seconds(claims["exp"] - now)
    return note


def describe_cookies(cookies, now):
    out = []
    for c in cookies or []:
        value = str(c.get("value", ""))
        item = {
            "name": mask_name(c.get("name")),
            "domain": c.get("domain"),
            "path": c.get("path"),
            "http_only": bool(c.get("httpOnly")),
            "secure": bool(c.get("secure")),
            "same_site": c.get("sameSite"),
            "length": len(value),
        }
        exp = c.get("expires")
        if isinstance(exp, (int, float)) and exp > 0:
            item["expires_in"] = humanize_seconds(exp - now)
        else:
            item["session_cookie"] = True
        claims = jwt_claims(value)
        if claims:
            item["jwt"] = {**claims, **_lifetime_note(claims, now)}
        out.append(item)
    out.sort(key=lambda i: (str(i["domain"]), str(i["name"])))
    return out


def describe_storage(kv, now):
    out = []
    for key, value in sorted((kv or {}).items()):
        value = value if isinstance(value, str) else json.dumps(value)
        item = {"key": mask_name(str(key)), "length": len(value)}
        bare = value.strip().strip('"')
        claims = jwt_claims(bare.replace("Bearer ", "").replace("bearer ", ""))
        if claims:
            item["kind"] = "jwt"
            item["jwt"] = {**claims, **_lifetime_note(claims, now)}
        else:
            parsed = None
            if value.strip()[:1] in ("{", "["):
                try:
                    parsed = json.loads(value)
                except ValueError:
                    parsed = None
            if parsed is not None:
                item["kind"] = "json"
                jwts = scan_jwts(parsed)
                if jwts:
                    item["jwt_paths"] = [
                        {"path": p, **{k: v for k, v in c.items() if k in ("typ", "header_typ")}, **_lifetime_note(c, now)}
                        for p, c in jwts
                    ]
            else:
                item["kind"] = "string"
        out.append(item)
    return out


def clock():
    return time.time()


def build_auth_hints(cookies, storages, entries, now=None):
    """What the captured session says about HOW auth works. Metadata only: never a cookie or token value."""
    now = clock() if now is None else now
    schemes, custom, cookie_names = Counter(), Counter(), set()
    auth_endpoints = []
    for e in entries:
        headers = {str(k).lower(): str(v) for k, v in (e.get("req_headers") or {}).items()}
        auth = headers.get("authorization")
        if auth:
            schemes[auth.split(" ", 1)[0] if " " in auth else "(no scheme)"] += 1
        for name in headers:
            if name.startswith("x-") and name != "x-requested-with":
                custom[name] += 1
        if headers.get("cookie"):
            cookie_names.update(cookie_names_from_cookie_header(headers["cookie"]))
        cookie_names.update(e.get("set_cookie_names") or [])
        _, path, _ = split_url(e.get("url", ""))
        if any(w in path.lower() for w in AUTH_PATH_WORDS):
            parsed = parse_json_loose(e.get("resp_body"))
            keys = sorted(parsed) if isinstance(parsed, dict) else []
            auth_endpoints.append({"method": e.get("method"), "path": templatize_path(path),
                                   "status": e.get("status"), "response_keys": keys[:15]})
    seen, unique = set(), []
    for a in auth_endpoints:
        k = (a["method"], a["path"], a["status"])
        if k not in seen:
            seen.add(k)
            unique.append(a)
    cookie_info = describe_cookies(cookies, now)
    notes = []
    if schemes:
        notes.append("Authorization header seen with scheme: " + ", ".join("%s x%d" % kv for kv in schemes.items()))
    elif cookie_info or cookie_names:
        notes.append("No Authorization header in the captured calls: the session looks cookie-based")
    if custom:
        notes.append("Custom x-* request headers seen: " + ", ".join("%s x%d" % kv for kv in custom.items()))
    for c in cookie_info:
        if c.get("session_cookie"):
            continue
        if "expires_in" in c:
            notes.append("Cookie %s on %s lives %s from now" % (c["name"], c["domain"], c["expires_in"]))
    if unique:
        notes.append("Auth-looking endpoints were called: check them for a bearer token in the response")
    if not (schemes or cookie_info or cookie_names or custom):
        notes.append("Nothing auth-like was captured: run capture again after a fresh login, or widen --host/--include")
    return {
        "generated_at": datetime.fromtimestamp(now, timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "cookies": cookie_info,
        "storage": {name: describe_storage(kv, now) for name, kv in (storages or {}).items()},
        "request_headers": {
            "authorization_schemes": dict(schemes),
            "custom_headers": dict(custom),
            "cookie_names_sent": sorted({mask_name(n) for n in cookie_names}),
        },
        "auth_endpoints": unique,
        "notes": notes,
    }


# --------------------------------------------------------------------------- url filters and routes
def host_matches(host, hosts):
    if not hosts:
        return True
    host = (host or "").lower().rstrip(".")
    for h in hosts:
        h = h.lower().strip().lstrip(".")
        if host == h or host.endswith("." + h):
            return True
    return False


def url_allowed(url, hosts, include=DEFAULT_INCLUDE, exclude=DEFAULT_EXCLUDE, all_xhr=False):
    low = url.lower()
    if not host_matches(urlsplit(url).hostname, hosts):
        return False
    if any(x.lower() in low for x in exclude):
        return False
    return True if all_xhr else any(i.lower() in low for i in include)


def resolve_route(start_url, route):
    """Absolute URL for a --route value: full URL, '#/hash/route', '/path' or a relative path."""
    route = route.strip()
    if re.match(r"^https?://", route, re.I):
        return route
    base = start_url.split("#", 1)[0]
    if route.startswith("#"):
        return base + route
    sp = urlsplit(start_url)
    if route.startswith("/"):
        return "%s://%s%s" % (sp.scheme, sp.netloc, route)
    return urljoin(base, route)


def slugify(text, limit=40):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:limit] or "r"


def is_unsafe_route(url):
    low = url.lower()
    return any(w in low for w in UNSAFE_ROUTE_WORDS)


def pick_routes(hrefs, start_url, limit=40):
    """Same-origin links worth visiting, in page order, without duplicates, fragments-only anchors,
    downloads or anything that looks like logout/delete."""
    origin = urlsplit(start_url)
    seen = {start_url.rstrip("/")}
    picked = []
    for href in hrefs or []:
        href = (href or "").strip()
        if not href or href.startswith(("mailto:", "tel:", "javascript:", "data:", "blob:")):
            continue
        sp = urlsplit(href)
        if (sp.scheme, sp.netloc) != (origin.scheme, origin.netloc):
            continue
        if re.search(r"\.(pdf|zip|png|jpe?g|gif|svg|csv|xlsx?|docx?|mp4|mp3)$", sp.path, re.I):
            continue
        if not sp.path.strip("/") and not sp.fragment.strip("/"):
            continue
        if is_unsafe_route(href):
            continue
        key = href.rstrip("/")
        if key in seen:
            continue
        seen.add(key)
        picked.append(href)
        if len(picked) >= limit:
            break
    return picked


def ensure_gitignore(workdir, entries):
    """Drop a .gitignore next to out/ and the profile when there is none; never edits an existing one.
    Returns 'created', 'ok' (existing file already lists everything) or the list of missing entries."""
    gi = Path(workdir) / ".gitignore"
    entries = [e for e in entries if e]
    if not gi.exists():
        gi.write_text("# live session and captured traffic: never commit\n" + "\n".join(entries) + "\n", encoding="utf-8")
        return "created"
    have = {line.strip() for line in gi.read_text(encoding="utf-8", errors="replace").splitlines()}
    missing = [e for e in entries if e not in have and e.rstrip("/") not in have]
    return missing or "ok"


# --------------------------------------------------------------------------- recording
class Recorder:
    """Collects XHR/fetch responses from pages. Duck-typed on the Playwright response object."""

    def __init__(self, hosts, include=DEFAULT_INCLUDE, exclude=DEFAULT_EXCLUDE, all_xhr=False,
                 keep_secrets=False, max_req=3000, max_resp=60000, log=None):
        self.hosts, self.include, self.exclude, self.all_xhr = list(hosts), tuple(include), tuple(exclude), all_xhr
        self.keep_secrets, self.max_req, self.max_resp = keep_secrets, max_req, max_resp
        self.log = log or (lambda *a: None)
        self.entries, self.scripts, self.route = [], [], ""

    def attach(self, page):
        page.on("response", self.on_response)

    @staticmethod
    def _request_headers(req):
        try:
            return dict(req.all_headers())  # includes Cookie and the other headers the page API hides
        except Exception:
            return dict(req.headers or {})

    def on_response(self, resp):
        try:
            req = resp.request
            url, rtype = resp.url, req.resource_type
            if rtype == "script":
                if urlsplit(url).path.endswith(".js") and host_matches(urlsplit(url).hostname, self.hosts) \
                        and url not in self.scripts:
                    self.scripts.append(url)
                return
            if rtype not in ("xhr", "fetch"):
                return
            if not url_allowed(url, self.hosts, self.include, self.exclude, self.all_xhr):
                return
            entry = self.build_entry(resp, req)
            self.entries.append(entry)
            self.log("  XHR %s %s %s" % (entry["status"], entry["method"], entry["url"].split("?")[0][-95:]))  # the stored (masked) URL
        except Exception:
            return  # recording must never break the page being driven

    def build_entry(self, resp, req):
        keep = self.keep_secrets
        headers = self._request_headers(req)
        ctype = str((resp.headers or {}).get("content-type", ""))
        try:
            post = req.post_data
        except Exception:
            post = None
        login_like = is_secret_body_url(resp.url, post)  # request AND response of such a call get the strict masks
        entry = {
            "seq": len(self.entries) + 1,
            "route": self.route,
            "method": req.method,
            "url": resp.url if keep else redact_url(resp.url),
            "status": resp.status,
            "resource_type": req.resource_type,
            "req_headers": headers if keep else redact_headers(headers),
            "resp_content_type": ctype,
        }
        if post:
            body = post[: self.max_req]
            entry["req_body"] = body if keep else redact_body(body, str(headers.get("content-type", "")), strict=login_like)
        set_cookie = (resp.headers or {}).get("set-cookie")
        if set_cookie:
            names = cookie_names_from_set_cookie(set_cookie)
            entry["set_cookie_names"] = names if keep else [mask_name(n) for n in names]
        if "json" in ctype.lower():
            try:
                body = resp.text()
                entry["resp_len"] = len(body)
                if len(body) > self.max_resp:
                    entry["resp_truncated"] = True
                cut = body[: self.max_resp]
                entry["resp_body"] = cut if keep else redact_body(cut, "application/json", tokens=login_like)
            except Exception as exc:
                entry["resp_err"] = str(exc)[:200]
        return entry


# --------------------------------------------------------------------------- summarizing saved captures
def parse_json_loose(text):
    if isinstance(text, (dict, list)):
        return text
    if not isinstance(text, str) or text.strip()[:1] not in ("{", "["):
        return None
    try:
        return json.loads(text)
    except ValueError:
        return None


def normalize_entry(raw):
    """Accept the capture shapes seen in the wild: current (req_headers/req_body/resp_body) and
    older probes (m, headers, body, resp). Returns None for rows without a URL."""
    if not isinstance(raw, dict) or not isinstance(raw.get("url"), str) or not raw["url"]:
        return None

    def first(*names):
        for n in names:
            if raw.get(n) is not None:
                return raw[n]
        return None

    try:
        status = int(first("status", "status_code") or 0)
    except (TypeError, ValueError):
        status = 0
    headers = first("req_headers", "headers")
    return {
        "method": str(first("method", "m") or "GET").upper(),
        "url": raw["url"],
        "status": status,
        "req_headers": headers if isinstance(headers, dict) else {},
        "req_body": first("req_body", "post_data", "body"),
        "resp_body": first("resp_body", "resp", "response", "response_body"),
        "resp_content_type": str(first("resp_content_type") or ""),
        "resp_truncated": bool(raw.get("resp_truncated")),
        "route": str(raw.get("route") or ""),
        "set_cookie_names": raw.get("set_cookie_names") or [],
    }


def split_url(url):
    sp = urlsplit(url)
    origin = "%s://%s" % (sp.scheme, sp.netloc) if sp.scheme and sp.netloc else ""
    return origin, sp.path or "/", [k for k, _ in parse_qsl(sp.query, keep_blank_values=True)]


def templatize_path(path):
    segs = []
    for seg in path.split("/"):
        if re.fullmatch(r"\d+", seg):
            segs.append("{n}")
        elif UUID_RE.match(seg):
            segs.append("{uuid}")
        elif re.fullmatch(r"[0-9a-fA-F]{16,}", seg):
            segs.append("{hex}")
        elif len(seg) >= 24 and re.fullmatch(r"[A-Za-z0-9_-]+", seg) and re.search(r"\d", seg):
            segs.append("{token}")
        else:
            segs.append(seg)
    return "/".join(segs)


def _shape_key(key):
    """Keys of dynamic maps can be ids or e-mails: mask them so a shape never carries personal data."""
    key = str(key)
    key = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "<email>", key)
    return _mask_ids(key)


def json_shape(obj, depth=0):
    """Keys and types only: values never leave the capture."""
    if isinstance(obj, dict):
        if depth >= SHAPE_DEPTH:
            return "obj"
        shape = {_shape_key(k): json_shape(v, depth + 1) for k, v in list(obj.items())[:SHAPE_KEYS]}
        if len(obj) > SHAPE_KEYS:
            shape["..."] = "+%d keys" % (len(obj) - SHAPE_KEYS)
        return shape
    if isinstance(obj, list):
        if not obj:
            return []
        return ["list"] if depth >= SHAPE_DEPTH else [json_shape(obj[0], depth + 1)]
    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, int):
        return "int"
    if isinstance(obj, float):
        return "num"
    return "null" if obj is None else "str"


def _label(shape):
    return "obj" if isinstance(shape, dict) else "list" if isinstance(shape, list) else shape


def merge_shape(a, b):
    if a == b:
        return a
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = merge_shape(out[k], v) if k in out else v
        return out
    if isinstance(a, list) and isinstance(b, list):
        if not a:
            return b
        return a if not b else [merge_shape(a[0], b[0])]
    if a == "null" and isinstance(b, (dict, list)):
        return b  # nullable object: keep its structure, it is what the map needs
    if b == "null" and isinstance(a, (dict, list)):
        return a
    return "|".join(sorted(set(_label(a).split("|")) | set(_label(b).split("|"))))


def shape_keys(shape, prefix="", out=None, limit=12):
    """Dotted key paths of a shape: items[].id, user.name ..."""
    out = [] if out is None else out
    if isinstance(shape, list):
        if shape and isinstance(shape[0], dict):
            shape_keys(shape[0], prefix + "[]", out, limit)
        return out
    if isinstance(shape, dict):
        for k, v in shape.items():
            if len(out) >= limit:
                return out
            name = "%s.%s" % (prefix, k) if prefix else k
            if isinstance(v, (dict, list)):
                if isinstance(v, dict) and v or (isinstance(v, list) and v and isinstance(v[0], dict)):
                    shape_keys(v, name, out, limit)
                else:
                    out.append(name)
            else:
                out.append(name)
    return out


def body_shape(body, content_type=""):
    parsed = parse_json_loose(body)
    if parsed is not None:
        return json_shape(parsed)
    if isinstance(body, str) and body.strip() and ("x-www-form-urlencoded" in content_type.lower()
                                                    or re.fullmatch(r"[^\s=&]+=[^\s&]*(&[^\s=&]+=[^\s&]*)*", body.strip())):
        return {k: "str" for k, _ in parse_qsl(body.strip(), keep_blank_values=True)}
    return None


def summarize(entries):
    groups = {}
    hosts, total = Counter(), 0
    for raw in entries:
        e = normalize_entry(raw)
        if e is None or e["method"] == "OPTIONS":
            continue
        total += 1
        origin, path, qnames = split_url(e["url"])
        hosts[origin or "(relative)"] += 1
        key = (e["method"], origin, templatize_path(path))
        g = groups.setdefault(key, {
            "method": e["method"], "origin": origin, "path": templatize_path(path), "calls": 0,
            "statuses": Counter(), "query": Counter(), "resp_shape": None, "error_shape": None,
            "req_shape": None, "flags": set(), "routes": [],
        })
        g["calls"] += 1
        g["statuses"][e["status"]] += 1
        for name in set(qnames):
            g["query"][name] += 1
        if e["route"] and e["route"] not in g["routes"] and len(g["routes"]) < 5:
            g["routes"].append(e["route"])
        text = e["resp_body"] if isinstance(e["resp_body"], str) else None
        parsed = parse_json_loose(e["resp_body"])
        if parsed is not None:
            slot = "resp_shape" if 200 <= e["status"] < 300 else "error_shape"
            shape = json_shape(parsed)
            g[slot] = shape if g[slot] is None else merge_shape(g[slot], shape)
        elif text and text.lstrip()[:1] == "<":
            g["flags"].add("html-body")
            if e["status"] == 404:
                g["flags"].add("html-404")
        if e["resp_truncated"]:
            g["flags"].add("resp-truncated")
        if e["req_body"]:
            content_type = next((str(v) for k, v in e["req_headers"].items() if str(k).lower() == "content-type"), "")
            shape = body_shape(e["req_body"] if isinstance(e["req_body"], str) else json.dumps(e["req_body"]), content_type)
            if shape is not None:
                g["req_shape"] = shape if g["req_shape"] is None else merge_shape(g["req_shape"], shape)
        if e["method"] not in READ_METHODS:
            g["flags"].add("mutating")
            if any(w in path.lower() for w in RISK_WORDS):
                g["flags"].add("risky")
        if any(w in path.lower() for w in AUTH_PATH_WORDS):
            g["flags"].add("auth")
    endpoints = sorted(groups.values(), key=lambda g: (g["origin"], g["path"], g["method"]))
    return {"calls": total, "hosts": dict(hosts), "endpoints": endpoints}


def _fmt_statuses(counter):
    return ", ".join("%s\u00d7%d" % (s or "?", n) for s, n in sorted(counter.items()))


def _fmt_params(g):
    if not g["query"]:
        return "\u2014"
    always = g["calls"] >= 2
    return ", ".join(("**`%s`**" if always and n == g["calls"] else "`%s`") % name for name, n in sorted(g["query"].items()))


def _fmt_notes(g):
    parts = [_fmt_statuses(g["statuses"])]
    keys = shape_keys(g["resp_shape"]) if g["resp_shape"] is not None else []
    if keys:
        parts.append(", ".join("`%s`" % k for k in keys))
    elif g["error_shape"] is not None and not g["resp_shape"]:
        parts.append("error body: " + ", ".join("`%s`" % k for k in shape_keys(g["error_shape"])))
    if "html-404" in g["flags"]:
        parts.append("HTML 404 instead of JSON: a required parameter is probably missing")
    if "resp-truncated" in g["flags"]:
        parts.append("response was cut by the size cap: shape is partial")
    return " \u00b7 ".join(p for p in parts if p)


def render_markdown(summary, title="Endpoints from captured traffic"):
    lines = ["# %s" % title, "",
             "%d calls, %d hosts, %d distinct endpoints. Values are never shown: only names and shapes. "
             "\U0001F4E6 = seen in traffic, not called by us yet. **Bold** parameter = present in every captured call "
             "(confirm by leaving it out)." % (summary["calls"], len(summary["hosts"]), len(summary["endpoints"])), "",
             "## Hosts", "", "| Host | Calls |", "|---|---|"]
    for host, n in sorted(summary["hosts"].items(), key=lambda kv: -kv[1]):
        lines.append("| `%s` | %d |" % (host, n))
    by_origin = {}
    for g in summary["endpoints"]:
        by_origin.setdefault(g["origin"], []).append(g)
    lines += ["", "## Endpoints"]
    for origin, items in by_origin.items():
        # Column titles are the Russian ones from references/api-map-template.md so the table pastes into the map as is.
        lines += ["", "### %s" % (origin or "(relative URLs)"), "",
                  "| \u2713 | \u041c\u0435\u0442\u043e\u0434 | \u041f\u0443\u0442\u044c | \u041f\u0430\u0440\u0430\u043c\u0435\u0442\u0440\u044b (\u043e\u0431\u044f\u0437\u0430\u0442\u0435\u043b\u044c\u043d\u044b\u0435 **\u0436\u0438\u0440\u043d\u044b\u043c**) | \u041e\u0442\u0432\u0435\u0442: \u043a\u043b\u044e\u0447\u0435\u0432\u044b\u0435 \u043f\u043e\u043b\u044f / \u0437\u0430\u043c\u0435\u0442\u043a\u0438 |",
                  "|---|---|---|---|---|"]
        for g in items:
            lines.append("| \U0001F4E6 | %s | `%s` | %s | %s |" % (g["method"], g["path"], _fmt_params(g), _fmt_notes(g)))
    mutating = [g for g in summary["endpoints"] if "mutating" in g["flags"]]
    lines += ["", "## Changing calls: review each before writing a client", ""]
    if not mutating:
        lines += ["none captured", ""]
    for g in mutating:
        mark = " \u26a0 name suggests money, messages or deletion: goes under 'paid / irreversible' in the map" if "risky" in g["flags"] else ""
        lines += ["```", "%s %s" % (g["method"], g["path"]),
                  "     %s" % (json.dumps(g["req_shape"], ensure_ascii=False) if g["req_shape"] is not None else "(no body captured)"),
                  "```", "%s%s" % (_fmt_statuses(g["statuses"]), mark), ""]
    auth = [g for g in summary["endpoints"] if "auth" in g["flags"]]
    lines += ["## Auth-looking endpoints (for section 1 of the map)", ""]
    if not auth:
        lines.append("none captured")
    for g in auth:
        keys = ", ".join("`%s`" % k for k in shape_keys(g["resp_shape"])) if g["resp_shape"] is not None else "(no JSON body)"
        lines.append("- %s `%s` \u2192 %s" % (g["method"], g["path"], keys))
    return "\n".join(lines).rstrip() + "\n"


def jsonable_summary(summary):
    out = dict(summary)
    out["endpoints"] = [
        {**g, "statuses": {str(k): v for k, v in g["statuses"].items()}, "query": dict(g["query"]), "flags": sorted(g["flags"])}
        for g in summary["endpoints"]
    ]
    return out


# --------------------------------------------------------------------------- JS bundles
STATIC_EXT = (".js", ".mjs", ".css", ".map", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".webp", ".avif",
              ".woff", ".woff2", ".ttf", ".eot", ".otf", ".mp4", ".webm", ".mp3", ".wav", ".pdf", ".zip", ".wasm")
STATIC_DIRS = ("/static/", "/assets/", "/img/", "/images/", "/fonts/", "/css/", "/js/", "/node_modules/", "/_next/static/", "/favicon")
PATH_RE = re.compile(r"""["'`]((?:/[A-Za-z0-9_\-.~{}$:@%]+){1,12}/?)["'`]""")
URL_RE = re.compile(r"""["'`](https?://[^"'`\s<>\\]{6,300})["'`]""")
STRONG_RE = re.compile(r"/(?:api|rest|graphql|trpc|rpc|gateway)(?:/|$)|/v\d+(?:/|$)", re.I)
CALL_HINT_RE = re.compile(r"\.(?:post|put|patch|get|delete|request)\s*\(|axios|\$http|httpClient|fetch\(|XMLHttpRequest", re.I)


def is_stub(text, min_bytes=500):
    """Bot protection answers headless browsers with a tiny body (about 100 bytes) instead of the bundle."""
    return len(text.encode("utf-8", errors="replace")) < min_bytes


def extract_paths_from_js(text, hosts=None):
    """API-looking string literals: [{'path': ..., 'strong': bool}] sorted strong first."""
    found = {}
    for m in PATH_RE.finditer(text):
        path = m.group(1)
        low = path.lower()
        if len(path) < 4 or low.endswith(STATIC_EXT) or any(d in low for d in STATIC_DIRS):
            continue
        if all(re.fullmatch(r"\d+", s) for s in path.strip("/").split("/")):
            continue
        found[path] = bool(STRONG_RE.search(path))
    for m in URL_RE.finditer(text):
        url = m.group(1)
        low = url.lower()
        if low.split("?")[0].endswith(STATIC_EXT) or any(x in low for x in DEFAULT_EXCLUDE):
            continue
        if hosts and not host_matches(urlsplit(url).hostname, hosts):
            continue
        found[url] = bool(STRONG_RE.search(url))
    return [{"path": p, "strong": s} for p, s in sorted(found.items(), key=lambda kv: (not kv[1], kv[0]))]


def context_snippets(text, word, radius=320, limit=3):
    """Code around WORD that also looks like an HTTP call: shows the request a button would send."""
    out = []
    for m in re.finditer(re.escape(word), text, re.I):
        seg = text[max(0, m.start() - radius): m.start() + radius]
        if CALL_HINT_RE.search(seg):
            out.append(redact_text(re.sub(r"\s+", " ", seg)))
            if len(out) >= limit:
                break
    return out


# --------------------------------------------------------------------------- commands
def _csv(values):
    out = []
    for v in values or []:
        out += [p.strip() for p in str(v).split(",") if p.strip()]
    return out


def _log(*args):
    print(*args, file=sys.stderr)


def cmd_summarize(args):
    path = Path(args.file)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        _log("ERROR: cannot read %s as JSON: %s" % (path, exc))
        _log("NEXT: pass the api_map.json written by `capture` (a JSON list of calls)")
        return EXIT_FAIL
    if isinstance(data, dict):
        data = data.get("entries") or data.get("calls") or []
    if not isinstance(data, list):
        _log("ERROR: %s is not a list of captured calls" % path)
        return EXIT_FAIL
    summary = summarize(data)
    text = (json.dumps(jsonable_summary(summary), ensure_ascii=False, indent=2) if args.json
            else render_markdown(summary, args.title))
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        _log("wrote %s (%d endpoints from %d calls)" % (args.out, len(summary["endpoints"]), summary["calls"]))
    else:
        sys.stdout.write(text if text.endswith("\n") else text + "\n")
    return EXIT_OK


def cmd_bundles(args):
    files = []
    for p in args.paths:
        pp = Path(p)
        if not pp.exists():
            _log("ERROR: no such file or folder: %s" % p)
            _log("NEXT: pass saved bundle files or the folder written by `capture --bundles` (out/bundles)")
            return EXIT_FAIL
        files += sorted(pp.rglob("*.js")) if pp.is_dir() else [pp]
    if not files:
        _log("ERROR: no .js files under %s" % ", ".join(args.paths))
        _log("NEXT: run `capture --bundles` first, or pass the folder with saved bundles")
        return EXIT_FAIL
    hosts = _csv(args.host)
    report, stubs = [], 0
    for f in files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            report.append({"file": str(f), "error": str(exc)})
            continue
        if is_stub(text, args.min_bytes):
            stubs += 1
            report.append({"file": f.name, "bytes": len(text.encode("utf-8", errors="replace")), "stub": True})
            continue
        paths = extract_paths_from_js(text, hosts)
        if args.strong_only:
            paths = [p for p in paths if p["strong"]]
        words = [w.lower() for w in _csv(args.interest)]
        if words:
            paths = [p for p in paths if any(w in p["path"].lower() for w in words)]
        item = {"file": f.name, "bytes": len(text.encode("utf-8", errors="replace")), "paths": paths}
        if args.grep:
            item["context"] = {w: context_snippets(text, w) for w in _csv(args.grep)}
        report.append(item)
    if args.json:
        sys.stdout.write(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        return EXIT_OK
    total = sum(len(r.get("paths", [])) for r in report)
    print("# JS bundles: %d files, %d stubs, %d paths" % (len(files), stubs, total))
    for r in report:
        if r.get("stub"):
            print("\n## %s: STUB (%d bytes): bot protection? capture again headed" % (r["file"], r["bytes"]))
            continue
        if r.get("error"):
            print("\n## %s: unreadable (%s)" % (r["file"], r["error"]))
            continue
        print("\n## %s (%d bytes, %d paths)" % (r["file"], r["bytes"], len(r["paths"])))
        for p in r["paths"]:
            print("- %s%s" % (p["path"], "  [strong]" if p["strong"] else ""))
        for word, snippets in (r.get("context") or {}).items():
            print("\n### call context for '%s': %d" % (word, len(snippets)))
            for s in snippets:
                print("  " + s[:600])
    return EXIT_OK


def load_engine(name):
    """Browser engine factory, imported lazily so the offline commands (and the tests) need no browser."""
    if name == "patchright":
        from patchright.sync_api import sync_playwright
    else:
        from playwright.sync_api import sync_playwright
    return sync_playwright


def read_storage(page, store):
    try:
        return page.evaluate(
            "() => { const o={}; for (let i=0;i<%s.length;i++) {const k=%s.key(i); o[k]=%s.getItem(k);} return o; }"
            % (store, store, store))
    except Exception:
        return {}


def logged_in(page, args):
    if args.ready_selector:
        try:
            return page.locator(args.ready_selector).count() > 0
        except Exception:
            return False
    url = (page.url or "").lower()
    return not any(h.lower() in url for h in args.login_hint)


POLL_MS = 2000


class CaptureFailed(Exception):
    """The run cannot go on (for example the start page does not open); the message was already logged."""


def wait_for_login(page, args, log):
    try:
        page.goto(args.url, wait_until="domcontentloaded", timeout=60000)
    except Exception as exc:
        log("ERROR: cannot open %s: %s" % (redact_url(args.url), shown_text(args, exc)[:160]))
        log("NEXT: check the URL and the connection (VPN, proxy), then run again")
        raise CaptureFailed(str(exc))
    page.wait_for_timeout(args.wait_ms)
    if logged_in(page, args):
        log("[login] session already valid: %s" % shown_url(args, page.url))
        return True
    if args.headless:
        log("ERROR: not logged in and --headless cannot show a login window")
        log("NEXT: run once without --headless, log in by hand, then re-run headless")
        return False
    log("[login] log in by hand in the opened window (2FA and captcha are yours); waiting up to %ds" % args.login_wait)
    for _ in range(max(1, args.login_wait * 1000 // POLL_MS)):
        page.wait_for_timeout(POLL_MS)
        if logged_in(page, args):
            page.wait_for_timeout(1500)
            log("[login] ok: %s" % shown_url(args, page.url))
            return True
    log("ERROR: login was not completed in %ds" % args.login_wait)
    log("NEXT: re-run and log in faster, raise --login-wait, or pass --ready-selector if the login form has no /login URL")
    return False


def collect_routes(page, args, log=None):
    log = log or _log
    routes = [resolve_route(args.url, r) for r in _csv(args.route)]
    if args.routes_file:
        for line in Path(args.routes_file).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            # '# text' is a comment; '#/billing' is a hash route and must survive
            if line and line != "#" and not line.startswith(("# ", "#" + chr(9))):
                routes.append(resolve_route(args.url, line))
    allowed = [resolve_route(args.url, r) for r in _csv(getattr(args, "allow_route", None))]
    discovered = []
    if args.discover:
        try:
            hrefs = page.eval_on_selector_all("a[href]", "els => els.map(e => e.href)")
        except Exception:
            hrefs = []
        discovered = pick_routes(hrefs, args.url, args.max_routes)
    shown = (lambda u: u) if getattr(args, "keep_secrets", False) else redact_url
    seen, ordered = set(), []
    for r in routes + allowed + discovered:
        if r in seen:
            continue
        if is_unsafe_route(r) and r not in allowed:
            # a named route is never dropped in silence: say why, and how to visit it on purpose
            log("[skip] %s looks like logout/delete/cancel and was not visited; name it with --allow-route to visit it anyway" % shown(r))
            continue
        seen.add(r)
        ordered.append(r)
    return ordered, discovered


def fetch_bundles(page, urls, out_dir, min_bytes, hosts, log):
    cache = out_dir / "bundles"
    cache.mkdir(parents=True, exist_ok=True)
    result = {"files": {}, "stubs": []}
    for u in urls[:80]:
        stem = slugify(u.split("/")[-1].split("?")[0].replace(".js", ""), 60)
        name = "%s-%s.js" % (stem, hashlib.md5(u.encode("utf-8")).hexdigest()[:6])  # the hash keeps chunk names unique
        try:
            r = page.request.get(u)
            if r.status != 200:
                log("  %s: HTTP %s" % (name, r.status))
                continue
            body = r.text()
        except Exception as exc:
            log("  %s: error %s" % (name, str(exc)[:70]))
            continue
        if is_stub(body, min_bytes):
            log("  %s: stub (%d chars): bot protection? use headed" % (name, len(body)))
            result["stubs"].append(name)
            continue
        (cache / name).write_text(body, encoding="utf-8")
        paths = extract_paths_from_js(body, hosts)
        if paths:
            result["files"][name] = paths
    return result


def find_skill_dir(start=None):
    """Nearest folder above this script that holds a SKILL.md; None when the script was copied out of a skill."""
    for parent in Path(start or __file__).resolve().parents:
        if (parent / "SKILL.md").is_file():
            return parent
    return None


SKILL_DIR = find_skill_dir()


def inside(path, folder):
    if folder is None:
        return False
    try:
        Path(path).resolve().relative_to(folder)
        return True
    except ValueError:
        return False


def cmd_capture(args):
    log = _log
    for flag, path in (("--out", args.out), ("--profile", args.profile)):
        if inside(path, SKILL_DIR):
            log("ERROR: %s %s is inside the skill folder %s" % (flag, path, SKILL_DIR))
            log("NEXT: run from the service's own folder (for example ~/.claude/tools/<service>-re/): the profile and the traffic must never end up in the skill or its pack")
            return EXIT_USAGE
    if args.routes_file and not Path(args.routes_file).is_file():
        log("ERROR: --routes-file %s does not exist" % args.routes_file)
        log("NEXT: create it with one route per line, or pass --route instead")
        return EXIT_USAGE
    hosts = _csv(args.host) or [urlsplit(args.url).hostname or ""]
    include = _csv(args.include) or list(DEFAULT_INCLUDE)
    exclude = list(DEFAULT_EXCLUDE) + _csv(args.exclude)
    args.login_hint = _csv(args.login_hint) or list(DEFAULT_LOGIN_HINTS)
    try:
        sync_playwright = load_engine(args.engine)
    except ImportError as exc:
        log("ERROR: browser engine '%s' is not installed (%s)" % (args.engine, exc))
        log("NEXT: pip install %s && %s install chromium" % (args.engine, args.engine))
        return EXIT_FAIL
    out, profile = Path(args.out), Path(args.profile)
    out.mkdir(parents=True, exist_ok=True)
    profile.mkdir(parents=True, exist_ok=True)
    guarded = {}  # one .gitignore per parent folder: out/ and the profile may live in different places
    for folder in (out, profile):
        guarded.setdefault(folder.resolve().parent, []).append(folder.resolve().name + "/")
    for parent, entries in guarded.items():
        status = ensure_gitignore(parent, entries)
        if status == "created":
            log("[git] wrote %s: %s hold a live session" % (parent / ".gitignore", " and ".join(entries)))
        elif status != "ok":
            log("[git] WARNING: %s does not list %s: add it before any commit" % (parent / ".gitignore", ", ".join(status)))
    if args.keep_secrets:
        log("[warn] --keep-secrets: tokens and cookies WILL be written to %s. Keep it out of git." % out)
    rec = Recorder(hosts, include, exclude, args.all_xhr, args.keep_secrets, max_resp=args.max_resp_chars, log=log)

    def shown(url):
        return shown_url(args, url)

    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            user_data_dir=str(profile),
            headless=args.headless,
            viewport={"width": 1520, "height": 960},
            locale=args.locale,
            accept_downloads=True,
            args=["--disable-blink-features=AutomationControlled"],
        )
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            rec.attach(page)
            ctx.on("page", rec.attach)
            try:
                if not wait_for_login(page, args, log):
                    return EXIT_LOGIN
            except CaptureFailed:
                return EXIT_FAIL
            visited, discovered = [], []
            if not args.login_only:
                routes, discovered = collect_routes(page, args, log)
                if args.shots:
                    (out / "shots").mkdir(exist_ok=True)
                for url in routes:
                    rec.route = shown(url.replace(args.url.split("#", 1)[0], "") or "/")
                    log("\n[crawl] %s" % shown(url))
                    try:
                        page.goto(url, wait_until="domcontentloaded", timeout=45000)
                        page.wait_for_timeout(args.wait_ms)
                        visited.append(shown(url))
                        if args.shots:
                            page.screenshot(path=str(out / "shots" / (slugify(shown(url)) + ".png")), full_page=True)
                        if args.save_text:
                            (out / ("text_" + slugify(shown(url)) + ".txt")).write_text(page.inner_text("body"), encoding="utf-8")
                    except Exception as exc:
                        log("    ERR: %s" % shown_text(args, exc)[:160])
                rec.route = ""
            bundle_info = None
            if args.bundles and not args.login_only:
                log("\n[bundles] %d script URLs seen" % len(rec.scripts))
                bundle_info = fetch_bundles(page, rec.scripts, out, args.min_bytes, hosts, log)
            cookies = ctx.cookies()
            storages = {s: read_storage(page, s) for s in ("localStorage", "sessionStorage")}
            hints = build_auth_hints(cookies, storages, rec.entries)
            (out / "auth_hints.json").write_text(json.dumps(hints, ensure_ascii=False, indent=2), encoding="utf-8")
            if args.save_session:
                log("[warn] --save-session: raw cookies and storage go to %s" % (out / "session.raw.json"))
                (out / "session.raw.json").write_text(
                    json.dumps({"cookies": cookies, **storages}, ensure_ascii=False, indent=2), encoding="utf-8")
            (out / "api_map.json").write_text(json.dumps(rec.entries, ensure_ascii=False, indent=2), encoding="utf-8")
            (out / "routes.json").write_text(
                json.dumps({"visited": visited, "discovered": [shown(u) for u in discovered]}, ensure_ascii=False, indent=2),
                encoding="utf-8")
            summary = summarize(rec.entries)
            (out / "endpoints.md").write_text(render_markdown(summary, "Endpoints from %s" % shown(args.url)), encoding="utf-8")
            if bundle_info is not None:
                if not args.keep_secrets:  # a full URL written into a bundle (a signed link, ?key=...) is masked like any other
                    for paths in bundle_info["files"].values():
                        for item in paths:
                            if item["path"].startswith(("http://", "https://")):
                                item["path"] = redact_url(item["path"])
                (out / "bundle_endpoints.json").write_text(json.dumps(bundle_info, ensure_ascii=False, indent=2), encoding="utf-8")
            log("\n[done] %d calls, %d endpoints -> %s" % (len(rec.entries), len(summary["endpoints"]), out))
            for note in hints["notes"]:
                log("[auth] " + note)
        finally:
            ctx.close()
    return EXIT_OK


def build_parser():
    ap = argparse.ArgumentParser(prog="harvest.py", description=__doc__.split("\n\n")[0],
                                 epilog=EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="{capture,summarize,bundles}")

    p = sub.add_parser("capture", help="drive a browser, record the API calls (needs playwright or patchright)",
                       description="Open a persistent-profile browser, wait for your login, walk routes, record XHR/fetch.")
    p.add_argument("--url", required=True, help="start URL of the service (the page you land on after login)")
    p.add_argument("--profile", default="./.profile", help="persistent browser profile folder (holds a live session; never commit)")
    p.add_argument("--out", default="./out", help="output folder (default ./out)")
    p.add_argument("--host", action="append", help="record only these hosts (suffix match; repeat or comma-separate); default: host of --url")
    p.add_argument("--include", action="append", help="URL substrings that mark API calls (default: /api/ /rest/ graphql /trpc/ /v1/ /v2/ /v3/)")
    p.add_argument("--exclude", action="append", help="extra URL substrings to ignore, added to the built-in analytics list")
    p.add_argument("--all-xhr", action="store_true", help="record every XHR/fetch on the allowed hosts, ignoring --include")
    p.add_argument("--route", action="append", help="route to visit: full URL, '#/hash/route', '/path' (repeatable)")
    p.add_argument("--routes-file", help="file with one route per line; a line starting with '# ' (hash and space) is a comment, '#/billing' is a route")
    p.add_argument("--allow-route", action="append", help="visit this route although its address looks like logout/delete/cancel (named on purpose; --discover never does; repeatable)")
    p.add_argument("--discover", action="store_true", help="also visit same-origin links found on the landing page (never logout/delete-like ones)")
    p.add_argument("--max-routes", type=int, default=40, help="cap for --discover (default 40)")
    p.add_argument("--wait-ms", type=int, default=6000, help="settle time per page in ms (default 6000)")
    p.add_argument("--login-hint", action="append", help="URL substring that means 'not logged in' (default: login, signin, sign-in, /sso, sso.)")
    p.add_argument("--ready-selector", help="CSS selector that exists only when logged in (use when the login form has no /login URL)")
    p.add_argument("--login-wait", type=int, default=300, help="seconds to wait for you to log in (default 300)")
    p.add_argument("--login-only", action="store_true", help="log in and stop: warms the profile, no route walk; still writes what the login itself called and auth_hints.json")
    p.add_argument("--headless", action="store_true", help="no window: only for a profile that is already logged in")
    p.add_argument("--engine", choices=("playwright", "patchright"), default="playwright", help="browser driver (patchright = stealth fork)")
    p.add_argument("--locale", default="en-US", help="browser locale (default en-US)")
    p.add_argument("--bundles", action="store_true", help="also download the JS bundles seen and list the API paths inside")
    p.add_argument("--min-bytes", type=int, default=500, help="bundles smaller than this count as bot-protection stubs (default 500)")
    p.add_argument("--max-resp-chars", type=int, default=60000, help="cap for stored response bodies (default 60000)")
    p.add_argument("--shots", action="store_true", help="save a screenshot per route (may contain account data)")
    p.add_argument("--save-text", action="store_true", help="save the visible text of each page (may contain account data)")
    p.add_argument("--keep-secrets", action="store_true", help="do NOT redact tokens, cookies and passwords in out/")
    p.add_argument("--save-session", action="store_true", help="also write raw cookies and storage to out/session.raw.json (secrets!)")
    p.set_defaults(func=cmd_capture)

    p = sub.add_parser("summarize", help="offline: api_map.json -> endpoint table (markdown or --json)")
    p.add_argument("file", help="api_map.json from `capture` (older probe shapes are understood too)")
    p.add_argument("--out", help="write here instead of stdout")
    p.add_argument("--json", action="store_true", help="machine-readable summary")
    p.add_argument("--title", default="Endpoints from captured traffic")
    p.set_defaults(func=cmd_summarize)

    p = sub.add_parser("bundles", help="offline: API-looking paths in saved JS bundles")
    p.add_argument("paths", nargs="+", help="bundle files or folders")
    p.add_argument("--host", action="append", help="keep full URLs only for these hosts")
    p.add_argument("--interest", action="append", help="keep only paths containing one of these words (comma-separate or repeat)")
    p.add_argument("--grep", action="append", help="also print code around WORD when it sits next to an HTTP call (the request shape of a button)")
    p.add_argument("--strong-only", action="store_true", help="only /api/ /rest/ /graphql /vN/ style paths")
    p.add_argument("--min-bytes", type=int, default=500, help="smaller files count as stubs (default 500)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_bundles)
    return ap


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:
                pass
    args = build_parser().parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
