"""
OpenAI-compatible API server on top of the LOCAL `claude` CLI (Max subscription, no API key).

What it does:
    Exposes an OpenAI-shaped HTTP endpoint on 127.0.0.1 that any OpenAI client
    (n8n "OpenAI Chat Model" node, openai-python/openai-node SDK, curl, IDE
    plugins, Open WebUI, LibreChat, ...) can talk to.  Every request is served
    by spawning the local `claude` CLI in print mode (`claude -p`), so billing
    goes through the Claude Code subscription — no ANTHROPIC_API_KEY involved.

Direction of traffic (do not confuse with the local-gateway skill):
    local-gateway  (127.0.0.1:GATEWAY_PORT) = OUTBOUND  -> proxies to external providers.
    agent_api_server (127.0.0.1:8199) = INBOUND -> serves Claude-by-subscription
                                                   as an OpenAI-compatible API.

Endpoints:
    POST /v1/chat/completions   OpenAI Chat Completions (stream=true -> SSE)
    GET  /v1/models             model list (Claude Code aliases + full ids)
    GET  /health                liveness + backend diagnostics
    GET  /                      short human-readable help

Sessions:
    Optional request header `X-Session-Id: <any-string>` continues a
    conversation server-side: the string is mapped to a stable UUIDv5 and
    passed to the CLI as `--session-id` (first turn) / `--resume` (later
    turns).  Without the header the endpoint is stateless and the whole
    `messages[]` array is flattened into one prompt.
    Session registry: ~/.claude/agent_api_sessions.json

Backend / reuse:
    CLI discovery is reused from ~/.claude/tools/claude_cli.py when importable
    (CLAUDE_CLI_PATH / _find_cli), otherwise falls back to PATH lookup.

Credentials / env (read from ~/.claude/.credentials.master.env if present):
    AGENT_API_TOKEN    optional Bearer token; if set, every /v1/* call must send
                       `Authorization: Bearer <token>`.  REQUIRED when binding
                       to a non-loopback host.
    AGENT_API_MODEL    default model when the request omits one (default: sonnet)
    AGENT_API_HOST     default bind host (default: 127.0.0.1)
    AGENT_API_PORT     default bind port (default: 8199)
    AGENT_API_TIMEOUT  per-request CLI timeout in seconds (default: 600)
    AGENT_API_WORKDIR  cwd for the spawned CLI (default: ~/.claude/agent-api-workdir)
    AGENT_API_MAX_CONCURRENCY  max simultaneous CLI processes (default: 4)

Usage:
    python agent_api_server.py serve [--port 8199] [--host 127.0.0.1]
    python agent_api_server.py test  [--model haiku] [--json]
    python agent_api_server.py models [--json]

Requires: Python 3.9+ (stdlib only) and `claude` on PATH
    (npm install -g @anthropic-ai/claude-code)
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
import hmac
import io
import json
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Fix Windows encoding (mirrors tg_client.py)
if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "buffer"):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_env():
    """Load ~/.claude/.credentials.master.env without overriding real env vars."""
    env_path = Path.home() / ".claude" / ".credentials.master.env"
    if env_path.exists():
        try:
            lines = env_path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and not os.environ.get(key):
                    os.environ[key] = value


load_env()

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_HOST = os.environ.get("AGENT_API_HOST", "127.0.0.1")
DEFAULT_PORT = int(os.environ.get("AGENT_API_PORT", "8199") or 8199)
DEFAULT_MODEL = os.environ.get("AGENT_API_MODEL", "sonnet")
DEFAULT_TIMEOUT = float(os.environ.get("AGENT_API_TIMEOUT", "600") or 600)
MAX_CONCURRENCY = int(os.environ.get("AGENT_API_MAX_CONCURRENCY", "4") or 4)
API_TOKEN = os.environ.get("AGENT_API_TOKEN", "").strip()

WORKDIR = Path(os.environ.get("AGENT_API_WORKDIR", "") or (Path.home() / ".claude" / "agent-api-workdir"))
SESSION_REGISTRY = Path.home() / ".claude" / "agent_api_sessions.json"

MAX_BODY_BYTES = 10_000_000  # 10 MB
LOOPBACK_HOSTS = {"127.0.0.1", "::1", "localhost"}

# Session-id namespace: stable across runs, so the same X-Session-Id always
# maps to the same CLI session UUID.
_SESSION_NS = uuid.UUID("6f1d9c9e-2f4a-5b8c-9d1e-4a7b3c2d1e0f")

# Models advertised by /v1/models. Aliases are what `claude --model` accepts;
# full ids must match ~/.claude/config/models.md — that file is the single canon.
#
# Prefer the ALIAS when you have a choice. A stale full id does not fail: the CLI
# accepts it and quietly serves last year's model, and nothing in the response says
# so. This list already drifted once — it advertised claude-opus-4-8 and
# claude-sonnet-4-5-20250929 after Opus 5 / Sonnet 5 had shipped, so a client that
# asked for "the full id" got the older engine and no warning.
MODELS = [
    ("opus", "Opus 5 — orchestrator-grade reasoning"),
    ("fable", "Fable 5 — default worker engine"),
    ("sonnet", "Sonnet 5"),
    ("haiku", "Haiku 4.5 — cheapest/fastest"),
    ("claude-opus-5", "Opus 5 (full id)"),
    ("claude-fable-5", "Fable 5 (full id)"),
    ("claude-sonnet-5", "Sonnet 5 (full id)"),
    ("claude-haiku-4-5-20251001", "Haiku 4.5 (full id — dated by Anthropic, not stale)"),
]
MODEL_IDS = {m for m, _ in MODELS}

_sem = threading.BoundedSemaphore(max(1, MAX_CONCURRENCY))
_registry_lock = threading.Lock()


# ---------------------------------------------------------------------------
# claude CLI discovery (reuses ~/.claude/tools/claude_cli.py when available)
# ---------------------------------------------------------------------------

def find_claude_cli():
    """Return path to the claude binary, or None.

    Reuses claude_cli.CLAUDE_CLI_PATH / _find_cli() from the owner's existing
    wrapper so there is a single source of truth for CLI discovery.
    """
    try:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        import claude_cli  # noqa: F401  (owner's existing wrapper)

        if getattr(claude_cli, "CLAUDE_CLI_PATH", None):
            return claude_cli.CLAUDE_CLI_PATH
        try:
            return claude_cli._find_cli()
        except Exception:
            pass
    except Exception:
        pass
    return shutil.which("claude")


CLI_MISSING_HINT = (
    "claude CLI not found.\n"
    "  Install:  npm install -g @anthropic-ai/claude-code\n"
    "  Or set:   CLAUDE_CLI_PATH=<full path to claude executable>\n"
    "  Check:    claude --version"
)


def cli_argv(cli_path, args):
    """Wrap .cmd/.bat shims for Windows (CreateProcess cannot exec them directly)."""
    if os.name == "nt" and cli_path.lower().endswith((".cmd", ".bat")):
        comspec = os.environ.get("COMSPEC", "cmd.exe")
        return [comspec, "/c", cli_path] + list(args)
    return [cli_path] + list(args)


# Env vars that would hijack the CLI away from the Max subscription (or corrupt
# the request) if inherited by the child.  load_env() pulls your
# .credentials.master.env into this process, and that file contains
# ANTHROPIC_API_KEY + ANTHROPIC_CUSTOM_HEADERS (JSON), which make `claude -p`
# fail with `API Error: Invalid header name: '{"anthropic-beta"'` and would bill
# the API key instead of the subscription.  Verified live 2026-07-25.
# NB: BEDROCK/VERTEX below are Claude Code's own provider switches (AWS Bedrock,
# Google Cloud Vertex AI) — they are literal env-var names, not host names.
_STRIP_ENV_PREFIXES = ("ANTHROPIC_",)
_STRIP_ENV_EXACT = (
    "CLAUDE_CODE_USE_BEDROCK",
    "CLAUDE_CODE_USE_VERTEX",
    "CLAUDE_CODE_SESSION_ID",
    "CLAUDE_CODE_CHILD_SESSION",
)


# --- recursion guard ------------------------------------------------------
# A CLI child can reach back into this server (it is a plain HTTP endpoint on
# loopback), and that request spawns another CLI, which can call again: the
# nesting only ends when RAM or the rate limit ends it.  The depth marker rides
# into every child; at the limit we answer 508 instead of forking another tree.
# NB: the marker must survive child_env() sanitising — it is deliberately named
# outside _STRIP_ENV_PREFIXES / _STRIP_ENV_EXACT.
DEPTH_ENV = "CLAUDE_CLI_DEPTH"
MAX_DEPTH_ENV = "CLAUDE_CLI_MAX_DEPTH"
DEFAULT_MAX_DEPTH = 1


def _int_env(name, default):
    try:
        return max(0, int(os.environ.get(name, default)))
    except (TypeError, ValueError):
        return default


def current_depth():
    """Nesting depth of THIS process (0 = not spawned by a claude CLI wrapper)."""
    return _int_env(DEPTH_ENV, 0)


def check_recursion(allow_nested=False):
    """Return the child's depth, or raise CLIError(508) at the limit."""
    depth = current_depth()
    limit = _int_env(MAX_DEPTH_ENV, DEFAULT_MAX_DEPTH)
    if not allow_nested and depth >= limit:
        raise CLIError(
            f"recursion guard: refusing to spawn a nested claude CLI — this server "
            f"is already running at depth {depth} (limit {limit}, {DEPTH_ENV}="
            f"{os.environ.get(DEPTH_ENV)!r}). An agent calling its own API server "
            f"recurses without bound. If intended, set {MAX_DEPTH_ENV}={depth + 1}.",
            status=508,
        )
    return depth + 1


def child_env(sanitize=True, allow_nested=False):
    """Environment for the spawned CLI: subscription auth, nothing hijacking it."""
    env = dict(os.environ)
    if sanitize:
        for key in list(env):
            if key.startswith(_STRIP_ENV_PREFIXES) or key in _STRIP_ENV_EXACT:
                env.pop(key, None)
    env[DEPTH_ENV] = str(check_recursion(allow_nested))
    return env


def cli_version(cli_path):
    try:
        proc = subprocess.run(
            cli_argv(cli_path, ["--version"]),
            capture_output=True, text=True, timeout=30,
            # `--version` is not an agent spawn — exempt from the recursion guard.
            encoding="utf-8", errors="replace", env=child_env(allow_nested=True),
        )
        return (proc.stdout or proc.stderr or "").strip().splitlines()[0] if (proc.stdout or proc.stderr) else ""
    except Exception as e:
        return f"error: {e}"


# ---------------------------------------------------------------------------
# Session registry
# ---------------------------------------------------------------------------

def _load_registry():
    if not SESSION_REGISTRY.exists():
        return {}
    try:
        return json.loads(SESSION_REGISTRY.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _save_registry(data):
    try:
        SESSION_REGISTRY.parent.mkdir(parents=True, exist_ok=True)
        SESSION_REGISTRY.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass


def session_uuid_for(session_key):
    """Map an arbitrary X-Session-Id string to a stable UUID + known-flag."""
    sid = str(uuid.uuid5(_SESSION_NS, session_key))
    with _registry_lock:
        reg = _load_registry()
        known = session_key in reg and reg[session_key].get("uuid") == sid
    return sid, known


def session_mark_used(session_key, sid, actual_sid=None):
    with _registry_lock:
        reg = _load_registry()
        entry = reg.get(session_key) or {"uuid": sid, "created": time.time(), "turns": 0}
        entry["uuid"] = sid
        entry["turns"] = int(entry.get("turns", 0)) + 1
        entry["updated"] = time.time()
        if actual_sid:
            entry["cli_session_id"] = actual_sid
        reg[session_key] = entry
        _save_registry(reg)


def session_forget(session_key):
    with _registry_lock:
        reg = _load_registry()
        reg.pop(session_key, None)
        _save_registry(reg)


# ---------------------------------------------------------------------------
# OpenAI <-> claude CLI translation
# ---------------------------------------------------------------------------

def normalize_content(content):
    """Flatten OpenAI content (string or typed parts array) into plain text.

    Image / file parts are NOT supported by this backend and are reported as
    markers so the caller sees them dropped rather than silently vanishing.
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                t = str(item.get("type") or "").lower()
                if t in ("text", "input_text", "output_text"):
                    parts.append(str(item.get("text") or ""))
                elif t in ("image_url", "input_image"):
                    parts.append("[image input not supported by claude-cli backend]")
                elif t in ("file", "input_file"):
                    parts.append("[file input not supported by claude-cli backend]")
        return "\n".join(p for p in parts if p)
    return str(content)


def split_messages(messages):
    """Return (system_prompt, turns) where turns is [(role, text), ...]."""
    system_parts = []
    turns = []
    for msg in messages:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role") or "").lower()
        text = normalize_content(msg.get("content"))
        if role in ("system", "developer"):
            if text:
                system_parts.append(text)
        elif role in ("user", "assistant"):
            turns.append((role, text))
        elif role == "tool":
            turns.append(("user", f"[tool result]\n{text}"))
    return ("\n\n".join(system_parts).strip(), turns)


def build_prompt(turns, stateful):
    """Build the stdin prompt for the CLI.

    Stateless mode: flatten the whole transcript (the CLI keeps no state).
    Stateful mode (X-Session-Id): send only the last user turn — prior turns
    already live in the resumed CLI session.
    """
    if not turns:
        return ""
    if stateful:
        for role, text in reversed(turns):
            if role == "user" and text.strip():
                return text
        return turns[-1][1]

    if len(turns) == 1:
        return turns[0][1]

    lines = []
    for role, text in turns[:-1]:
        label = "User" if role == "user" else "Assistant"
        lines.append(f"{label}: {text}")
    last_role, last_text = turns[-1]
    header = "Conversation so far:\n" + "\n\n".join(lines)
    if last_role == "user":
        return f"{header}\n\nUser: {last_text}\n\n(Reply to the last user message only.)"
    return f"{header}\n\nAssistant: {last_text}\n\n(Continue.)"


def build_cli_args(*, model, system, stream, sid, resume, allow_tools):
    args = ["-p", "--model", model]
    if stream:
        # --include-partial-messages requires --verbose with stream-json.
        args += ["--output-format", "stream-json", "--include-partial-messages", "--verbose"]
    else:
        args += ["--output-format", "json"]
    if system:
        args += ["--system-prompt", system]
    if sid:
        args += (["--resume", sid] if resume else ["--session-id", sid])
    if not allow_tools:
        # Pure text generation: no Bash/Edit/Read, so nothing can block on a
        # permission prompt in non-interactive mode.
        args += ["--tools", ""]
    return args


def openai_error(message, err_type="invalid_request_error", code=None, param=None):
    return {"error": {"message": message, "type": err_type, "code": code, "param": param}}


def map_stop_reason(stop_reason):
    if stop_reason in ("max_tokens", "output_truncated"):
        return "length"
    if stop_reason == "refusal":
        return "content_filter"
    return "stop"


def usage_block(usage):
    usage = usage or {}
    prompt_tokens = int(usage.get("input_tokens", 0) or 0) + int(usage.get("cache_read_input_tokens", 0) or 0) \
        + int(usage.get("cache_creation_input_tokens", 0) or 0)
    completion_tokens = int(usage.get("output_tokens", 0) or 0)
    return {
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "total_tokens": prompt_tokens + completion_tokens,
    }


# ---------------------------------------------------------------------------
# CLI invocation
# ---------------------------------------------------------------------------

class CLIError(Exception):
    def __init__(self, message, status=502):
        super().__init__(message)
        self.status = status


def _popen_kwargs(sanitize_env=True):
    kw = dict(
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=str(WORKDIR),
        env=child_env(sanitize_env),
    )
    if os.name == "nt":
        kw["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    return kw


def run_cli_once(cli_path, args, prompt, timeout, sanitize_env=True):
    """Non-streaming call -> parsed `result` JSON object from the CLI."""
    try:
        proc = subprocess.run(
            cli_argv(cli_path, args),
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            cwd=str(WORKDIR),
            env=child_env(sanitize_env),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0) if os.name == "nt" else 0,
        )
    except subprocess.TimeoutExpired:
        raise CLIError(f"claude CLI timed out after {timeout:.0f}s", status=504)
    except FileNotFoundError:
        raise CLIError(CLI_MISSING_HINT, status=503)

    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "").strip()[:1500] or f"exit code {proc.returncode}"
        raise CLIError(f"claude CLI failed: {err}")

    out = (proc.stdout or "").strip()
    if not out:
        raise CLIError("claude CLI returned empty output")
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        # Defensive: tolerate a stray banner line before the JSON object.
        for line in out.splitlines()[::-1]:
            line = line.strip()
            if line.startswith("{"):
                try:
                    return json.loads(line)
                except json.JSONDecodeError:
                    continue
        raise CLIError(f"claude CLI returned non-JSON output: {out[:500]}")


def stream_cli(cli_path, args, prompt, timeout, sanitize_env=True):
    """Streaming call. Yields ('delta', text) / ('result', obj) tuples."""
    try:
        proc = subprocess.Popen(cli_argv(cli_path, args), **_popen_kwargs(sanitize_env))
    except FileNotFoundError:
        raise CLIError(CLI_MISSING_HINT, status=503)

    deadline = time.monotonic() + timeout
    stderr_buf = []

    def _drain_stderr():
        try:
            for line in proc.stderr:
                stderr_buf.append(line)
        except Exception:
            pass

    threading.Thread(target=_drain_stderr, daemon=True).start()

    try:
        proc.stdin.write(prompt)
        proc.stdin.close()
    except Exception:
        pass

    got_result = False
    try:
        for line in proc.stdout:
            if time.monotonic() > deadline:
                proc.kill()
                raise CLIError(f"claude CLI timed out after {timeout:.0f}s", status=504)
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                continue
            etype = event.get("type")
            if etype == "stream_event":
                ev = event.get("event") or {}
                if ev.get("type") == "content_block_delta":
                    delta = ev.get("delta") or {}
                    # thinking_delta / signature_delta are internal — skip.
                    if delta.get("type") == "text_delta" and delta.get("text"):
                        yield ("delta", delta["text"])
            elif etype == "result":
                got_result = True
                yield ("result", event)
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        try:
            proc.wait(timeout=15)
        except Exception:
            proc.kill()

    if not got_result and proc.returncode not in (0, None):
        err = "".join(stderr_buf).strip()[:1500] or f"exit code {proc.returncode}"
        raise CLIError(f"claude CLI failed: {err}")


# ---------------------------------------------------------------------------
# HTTP handler
# ---------------------------------------------------------------------------

class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "agent-api-server/1.0"
    quiet = False

    # -- plumbing ---------------------------------------------------------

    def log_message(self, fmt, *args):
        if not self.quiet:
            sys.stderr.write("[%s] %s\n" % (time.strftime("%H:%M:%S"), fmt % args))
            sys.stderr.flush()

    def _send_json(self, obj, status=200, extra_headers=None):
        payload = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _send_text(self, text, status=200):
        payload = text.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        try:
            self.wfile.write(payload)
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass

    def _sse_start(self, extra_headers=None):
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("Transfer-Encoding", "chunked")
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()

    def _sse_write(self, text):
        data = text.encode("utf-8")
        self.wfile.write(b"%X\r\n" % len(data))
        self.wfile.write(data)
        self.wfile.write(b"\r\n")
        self.wfile.flush()

    def _sse_end(self):
        self.wfile.write(b"0\r\n\r\n")
        self.wfile.flush()

    def _auth_ok(self):
        if not API_TOKEN:
            return True
        header = self.headers.get("Authorization", "")
        if header.startswith("Bearer "):
            return hmac.compare_digest(header[7:].strip(), API_TOKEN)
        return False

    def _read_body(self):
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            raise CLIError("Invalid Content-Length header", status=400)
        if length > MAX_BODY_BYTES:
            raise CLIError("Request body too large", status=413)
        raw = self.rfile.read(length) if length else b""
        if not raw:
            raise CLIError("Empty request body", status=400)
        try:
            body = json.loads(raw.decode("utf-8", errors="replace"))
        except json.JSONDecodeError:
            raise CLIError("Invalid JSON in request body", status=400)
        if not isinstance(body, dict):
            raise CLIError("Request body must be a JSON object", status=400)
        return body

    def _session_key(self):
        raw = (self.headers.get("X-Session-Id") or "").strip()
        if not raw:
            return None
        if re.search(r"[\r\n\x00]", raw):
            raise CLIError("Invalid X-Session-Id (control characters)", status=400)
        if len(raw) > 128:
            raise CLIError("X-Session-Id too long (max 128 chars)", status=400)
        return raw

    # -- routes -----------------------------------------------------------

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Allow", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Origin", "http://localhost")
        self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type, X-Session-Id")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/health":
            return self._send_json(self._health_payload())
        if path == "/v1/models":
            if not self._auth_ok():
                return self._send_json(openai_error("Invalid API key", "authentication_error", "invalid_api_key"), 401)
            now = int(time.time())
            return self._send_json({
                "object": "list",
                "data": [
                    {"id": mid, "object": "model", "created": now, "owned_by": "claude-cli",
                     "root": mid, "parent": None, "description": desc}
                    for mid, desc in MODELS
                ],
            })
        if path == "/":
            return self._send_text(
                "agent_api_server — OpenAI-compatible API over the local claude CLI\n"
                "  POST /v1/chat/completions   (stream=true -> SSE)\n"
                "  GET  /v1/models\n"
                "  GET  /health\n"
                "Optional header: X-Session-Id: <string>  (continues a conversation)\n"
            )
        return self._send_json(openai_error(f"Unknown path {path}", code="not_found"), 404)

    def do_POST(self):
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path != "/v1/chat/completions":
            return self._send_json(openai_error(f"Unknown path {path}", code="not_found"), 404)
        if not self._auth_ok():
            return self._send_json(openai_error("Invalid API key", "authentication_error", "invalid_api_key"), 401)
        try:
            self._handle_chat()
        except CLIError as e:
            try:
                self._send_json(openai_error(str(e), "server_error" if e.status >= 500 else "invalid_request_error"),
                                e.status)
            except Exception:
                pass
        except Exception as e:  # last-resort guard: never leak a traceback to the wire
            try:
                self._send_json(openai_error(f"Internal error: {e}", "server_error"), 500)
            except Exception:
                pass

    def _health_payload(self):
        cli = self.server.cli_path
        return {
            "status": "ok" if cli else "degraded",
            "backend": "claude-cli",
            "cli_found": bool(cli),
            "cli_path": cli or None,
            "cli_version": self.server.cli_version or None,
            "hint": None if cli else CLI_MISSING_HINT,
            "default_model": self.server.default_model,
            "workdir": str(WORKDIR),
            "auth_required": bool(API_TOKEN),
            "tools_enabled": self.server.allow_tools,
            "anthropic_env_sanitized": self.server.sanitize_env,
            "max_concurrency": MAX_CONCURRENCY,
            "host": self.server.server_address[0],
            "port": self.server.server_address[1],
            "pid": os.getpid(),
            "uptime_s": round(time.time() - self.server.started_at, 1),
        }

    def _handle_chat(self):
        body = self._read_body()
        messages = body.get("messages")
        if not isinstance(messages, list) or not messages:
            raise CLIError("Missing or invalid 'messages' field", status=400)

        system, turns = split_messages(messages)
        if not any(t.strip() for _, t in turns):
            raise CLIError("No user/assistant message content found in 'messages'", status=400)

        model = str(body.get("model") or self.server.default_model).strip() or self.server.default_model
        stream = bool(body.get("stream", False))
        cli = self.server.cli_path
        if not cli:
            raise CLIError(CLI_MISSING_HINT, status=503)

        session_key = self._session_key()
        sid, resume = (None, False)
        if session_key:
            sid, known = session_uuid_for(session_key)
            resume = known

        prompt = build_prompt(turns, stateful=bool(session_key))
        if not prompt.strip():
            raise CLIError("Empty prompt after normalizing 'messages'", status=400)

        args = build_cli_args(model=model, system=system, stream=stream, sid=sid,
                              resume=resume, allow_tools=self.server.allow_tools)

        completion_id = "chatcmpl-" + uuid.uuid4().hex[:24]
        created = int(time.time())
        headers = {}
        if session_key:
            headers["X-Session-Id"] = session_key

        if not _sem.acquire(timeout=10):
            raise CLIError(f"Server busy: {MAX_CONCURRENCY} concurrent CLI runs in flight", status=429)
        try:
            if stream:
                self._chat_stream(cli, args, prompt, completion_id, model, created, headers,
                                  session_key, sid)
            else:
                self._chat_once(cli, args, prompt, completion_id, model, created, headers,
                                session_key, sid)
        finally:
            _sem.release()

    def _chat_once(self, cli, args, prompt, completion_id, model, created, headers, session_key, sid):
        result = run_cli_once(cli, args, prompt, self.server.cli_timeout,
                              sanitize_env=self.server.sanitize_env)
        if result.get("is_error"):
            msg = result.get("result") or result.get("error") or "claude CLI reported an error"
            raise CLIError(str(msg))
        text = result.get("result") or ""
        actual_sid = result.get("session_id")
        if session_key:
            session_mark_used(session_key, sid, actual_sid)
            if actual_sid:
                headers["X-Claude-Session-Id"] = actual_sid
        self._send_json({
            "id": completion_id,
            "object": "chat.completion",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": text},
                "finish_reason": map_stop_reason(result.get("stop_reason")),
            }],
            "usage": usage_block(result.get("usage")),
        }, extra_headers=headers)

    def _chat_stream(self, cli, args, prompt, completion_id, model, created, headers, session_key, sid):
        self._sse_start(headers)

        def chunk(delta, finish=None, usage=None):
            obj = {
                "id": completion_id, "object": "chat.completion.chunk",
                "created": created, "model": model,
                "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
            }
            if usage is not None:
                obj["usage"] = usage
            return "data: " + json.dumps(obj, ensure_ascii=False) + "\n\n"

        finish = "stop"
        usage = usage_block({})
        actual_sid = None
        try:
            self._sse_write(chunk({"role": "assistant"}))
            for kind, payload in stream_cli(cli, args, prompt, self.server.cli_timeout,
                                            sanitize_env=self.server.sanitize_env):
                if kind == "delta":
                    self._sse_write(chunk({"content": payload}))
                elif kind == "result":
                    finish = map_stop_reason(payload.get("stop_reason"))
                    usage = usage_block(payload.get("usage"))
                    actual_sid = payload.get("session_id")
                    if payload.get("is_error"):
                        finish = "error"
            self._sse_write(chunk({}, finish=finish, usage=usage))
            self._sse_write("data: [DONE]\n\n")
            self._sse_end()
        except (BrokenPipeError, ConnectionResetError, OSError):
            return  # client hung up mid-stream
        except CLIError as e:
            try:
                self._sse_write("data: " + json.dumps(openai_error(str(e), "server_error")) + "\n\n")
                self._sse_write(chunk({}, finish="error"))
                self._sse_write("data: [DONE]\n\n")
                self._sse_end()
            except Exception:
                pass
            return
        if session_key:
            session_mark_used(session_key, sid, actual_sid)


# ---------------------------------------------------------------------------
# Server bootstrap
# ---------------------------------------------------------------------------

def make_server(host, port, *, model, timeout, allow_tools, quiet=False, sanitize_env=True):
    WORKDIR.mkdir(parents=True, exist_ok=True)
    handler = type("BoundHandler", (Handler,), {"quiet": quiet})
    httpd = ThreadingHTTPServer((host, port), handler)
    httpd.daemon_threads = True
    httpd.cli_path = find_claude_cli()
    httpd.cli_version = cli_version(httpd.cli_path) if httpd.cli_path else ""
    httpd.default_model = model
    # NB: BaseServer.timeout has its own meaning (handle_request poll), so the
    # per-request CLI budget lives on a separate attribute.
    httpd.cli_timeout = timeout
    httpd.allow_tools = allow_tools
    httpd.sanitize_env = sanitize_env
    httpd.started_at = time.time()
    return httpd


def cmd_serve(args):
    host = args.host
    if host not in LOOPBACK_HOSTS and not API_TOKEN:
        print("REFUSING TO START: binding to a non-loopback host without a token.")
        print("  Set AGENT_API_TOKEN=<secret> in ~/.claude/.credentials.master.env (or the env)")
        print("  or bind to 127.0.0.1 instead.")
        return 2

    cli = find_claude_cli()
    if not cli:
        print(CLI_MISSING_HINT)
        return 2

    if current_depth() >= _int_env(MAX_DEPTH_ENV, DEFAULT_MAX_DEPTH):
        # Serving still starts (models/health stay useful), but every completion
        # would recurse — say so now instead of at the first 508.
        # flush=True: stdout is block-buffered when redirected to a log, and an
        # unflushed warning sits in the buffer until exit — i.e. is never seen.
        print(f"WARNING: started inside a claude CLI child ({DEPTH_ENV}="
              f"{os.environ.get(DEPTH_ENV)!r}). Completion requests will be refused "
              f"with 508 by the recursion guard. Set {MAX_DEPTH_ENV} higher if intended.",
              flush=True)

    try:
        httpd = make_server(host, args.port, model=args.model, timeout=args.timeout,
                            allow_tools=args.allow_tools, quiet=args.quiet,
                            sanitize_env=not args.inherit_anthropic_env)
    except OSError as e:
        print(f"Cannot bind {host}:{args.port} — {e}")
        print("  Pick another port:  --port 8299")
        return 2

    port = httpd.server_address[1]
    if args.json:
        print(json.dumps({"status": "listening", "host": host, "port": port,
                          "base_url": f"http://{host}:{port}/v1",
                          "cli_path": cli, "model": args.model,
                          "auth_required": bool(API_TOKEN)}, ensure_ascii=False))
    else:
        print(f"agent_api_server listening on http://{host}:{port}")
        print(f"  base_url для OpenAI-клиентов : http://{host}:{port}/v1")
        print(f"  api_key                      : {'<AGENT_API_TOKEN>' if API_TOKEN else 'любой непустой (не проверяется)'}")
        print(f"  claude CLI                   : {cli} ({httpd.cli_version})")
        print(f"  default model                : {args.model}   tools: {'on' if args.allow_tools else 'off'}")
        print(f"  workdir                      : {WORKDIR}")
        print("  Ctrl+C to stop")
    try:
        httpd.serve_forever(poll_interval=0.3)
    except KeyboardInterrupt:
        print("\nstopping...")
    finally:
        httpd.shutdown()
        httpd.server_close()
    return 0


def cmd_models(args):
    cli = find_claude_cli()
    if args.json:
        print(json.dumps({
            "models": [{"id": m, "description": d} for m, d in MODELS],
            "default": DEFAULT_MODEL,
            "cli_path": cli,
            "cli_found": bool(cli),
        }, ensure_ascii=False, indent=2))
        return 0
    print(f"claude CLI: {cli or 'NOT FOUND'}")
    if not cli:
        print(CLI_MISSING_HINT)
    print(f"default model: {DEFAULT_MODEL}\n")
    width = max(len(m) for m, _ in MODELS)
    for mid, desc in MODELS:
        mark = " *" if mid == DEFAULT_MODEL else "  "
        print(f"{mark} {mid.ljust(width)}  {desc}")
    return 0


def _http_get(url, token=None, timeout=30):
    import urllib.request
    req = urllib.request.Request(url)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.status, json.loads(resp.read().decode("utf-8"))


def _http_post(url, payload, token=None, timeout=300, session_id=None, raw=False):
    import urllib.request
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if session_id:
        req.add_header("X-Session-Id", session_id)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return resp.status, (body if raw else json.loads(body))


def cmd_test(args):
    """Self-check: start server on an ephemeral port, hit it, shut it down."""
    results = []

    def record(name, ok, detail=""):
        results.append({"check": name, "ok": bool(ok), "detail": str(detail)[:400]})

    cli = find_claude_cli()
    record("claude CLI found", bool(cli), cli or CLI_MISSING_HINT)

    try:
        httpd = make_server("127.0.0.1", args.port, model=args.model, timeout=args.timeout,
                            allow_tools=False, quiet=True)
    except OSError as e:
        record("server bind", False, e)
        return _finish_test(results, args)

    port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, kwargs={"poll_interval": 0.2}, daemon=True)
    thread.start()
    record("server bind", True, f"127.0.0.1:{port}")
    base = f"http://127.0.0.1:{port}"

    try:
        try:
            status, payload = _http_get(f"{base}/health")
            record("GET /health", status == 200 and payload.get("backend") == "claude-cli",
                   f"status={status} cli_found={payload.get('cli_found')}")
        except Exception as e:
            record("GET /health", False, e)

        try:
            status, payload = _http_get(f"{base}/v1/models", token=API_TOKEN or None)
            ids = [m["id"] for m in payload.get("data", [])]
            record("GET /v1/models", status == 200 and "haiku" in ids, f"{len(ids)} models")
        except Exception as e:
            record("GET /v1/models", False, e)

        try:
            status, payload = _http_post(f"{base}/v1/chat/completions",
                                         {"messages": [], "model": args.model},
                                         token=API_TOKEN or None, timeout=30)
            record("POST /v1/chat/completions rejects empty messages", False, f"status={status}")
        except Exception as e:
            code = getattr(e, "code", None)
            record("POST /v1/chat/completions rejects empty messages", code == 400, f"HTTP {code}")

        if cli and not args.skip_chat:
            try:
                t0 = time.time()
                status, payload = _http_post(
                    f"{base}/v1/chat/completions",
                    {"model": args.model,
                     "messages": [{"role": "system", "content": "You are a terse echo bot."},
                                  {"role": "user", "content": "Reply with exactly: PONG"}]},
                    token=API_TOKEN or None, timeout=args.timeout)
                text = (payload.get("choices") or [{}])[0].get("message", {}).get("content", "")
                record("POST /v1/chat/completions (non-stream)",
                       status == 200 and "PONG" in text.upper(),
                       f"{time.time()-t0:.1f}s -> {text[:80]!r}")
            except Exception as e:
                record("POST /v1/chat/completions (non-stream)", False, e)

            try:
                t0 = time.time()
                status, raw = _http_post(
                    f"{base}/v1/chat/completions",
                    {"model": args.model, "stream": True,
                     "messages": [{"role": "user", "content": "Reply with exactly: STREAMOK"}]},
                    token=API_TOKEN or None, timeout=args.timeout, raw=True)
                joined = ""
                for line in raw.splitlines():
                    if line.startswith("data: ") and line != "data: [DONE]":
                        try:
                            obj = json.loads(line[6:])
                        except json.JSONDecodeError:
                            continue
                        joined += (obj.get("choices") or [{}])[0].get("delta", {}).get("content", "") or ""
                record("POST /v1/chat/completions (SSE stream)",
                       status == 200 and "[DONE]" in raw and "STREAMOK" in joined.upper(),
                       f"{time.time()-t0:.1f}s -> {joined[:80]!r}")
            except Exception as e:
                record("POST /v1/chat/completions (SSE stream)", False, e)
        else:
            record("chat completion", False, "skipped (claude CLI missing or --skip-chat)")
    finally:
        httpd.shutdown()
        httpd.server_close()
        record("server shutdown", True, "closed")

    return _finish_test(results, args)


def _finish_test(results, args):
    ok = all(r["ok"] for r in results)
    if args.json:
        print(json.dumps({"ok": ok, "checks": results}, ensure_ascii=False, indent=2))
    else:
        width = max(len(r["check"]) for r in results)
        for r in results:
            print(f"[{'PASS' if r['ok'] else 'FAIL'}] {r['check'].ljust(width)}  {r['detail']}")
        print(f"\n{'ALL CHECKS PASSED' if ok else 'SOME CHECKS FAILED'}")
    return 0 if ok else 1


def build_parser():
    p = argparse.ArgumentParser(
        prog="agent_api_server.py",
        description="OpenAI-compatible API server backed by the local claude CLI (subscription, no API key).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Examples:\n"
               "  python agent_api_server.py serve --port 8199\n"
               "  python agent_api_server.py test --model haiku\n"
               "  python agent_api_server.py models --json\n",
    )
    sub = p.add_subparsers(dest="command", required=True)

    s = sub.add_parser("serve", help="Run the HTTP server (blocking)")
    s.add_argument("--host", default=DEFAULT_HOST, help=f"bind host (default {DEFAULT_HOST}; non-loopback needs AGENT_API_TOKEN)")
    s.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"bind port (default {DEFAULT_PORT}; 0 = ephemeral)")
    s.add_argument("--model", default=DEFAULT_MODEL, help=f"default model when the request omits one (default {DEFAULT_MODEL})")
    s.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT, help=f"per-request CLI timeout, seconds (default {DEFAULT_TIMEOUT:.0f})")
    s.add_argument("--allow-tools", action="store_true", help="let the agent use Claude Code tools (Bash/Read/Edit...). OFF by default — text only")
    s.add_argument("--inherit-anthropic-env", action="store_true",
                   help="do NOT strip ANTHROPIC_* from the child env (default: stripped, so the CLI uses the Max subscription)")
    s.add_argument("--quiet", action="store_true", help="suppress per-request access log")
    s.add_argument("--json", action="store_true", help="print startup banner as JSON")
    s.set_defaults(func=cmd_serve)

    t = sub.add_parser("test", help="Self-check: start, call /health + /v1/models + a short completion, stop")
    t.add_argument("--port", type=int, default=0, help="port to test on (default 0 = ephemeral free port)")
    t.add_argument("--model", default="haiku", help="model for the smoke completion (default haiku)")
    t.add_argument("--timeout", type=float, default=180.0, help="timeout for the smoke completion (default 180s)")
    t.add_argument("--skip-chat", action="store_true", help="only test HTTP plumbing, do not spend a model call")
    t.add_argument("--json", action="store_true", help="machine-readable output")
    t.set_defaults(func=cmd_test)

    m = sub.add_parser("models", help="List models advertised by /v1/models")
    m.add_argument("--json", action="store_true", help="machine-readable output")
    m.set_defaults(func=cmd_models)
    return p


def main():
    args = build_parser().parse_args()
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    sys.exit(main())
