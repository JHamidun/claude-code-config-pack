#!/usr/bin/env python3
"""
manus_helper.py — thin, working client for the Manus API v2.

Verified against https://open.manus.im/docs (API v2, July 2026). v1 is deprecated.

Base URL : https://api.manus.ai
Auth     : header  x-manus-api-key: <MANUS_API_KEY>
Key from : env MANUS_API_KEY  (stored in ~/.claude/.credentials.master.env)

Endpoints used:
  POST /v2/task.create        -> create an async agent task
  GET  /v2/task.listMessages  -> poll events / agent_status
  POST /v2/task.sendMessage   -> follow-up / answer a waiting task
  GET  /v2/task.detail        -> task metadata
  POST /v2/task.stop          -> stop a running task

agent_status lifecycle: running -> stopped (success) | error (failed) | waiting (needs input)

CLI:
  python manus_helper.py create   "<prompt>" [--profile manus-1.6-lite] [--locale en]
  python manus_helper.py run      "<prompt>" [--profile ...] [--timeout 1800] [--poll 8]
  python manus_helper.py status   <task_id>
  python manus_helper.py messages <task_id> [--limit 20] [--order desc]
  python manus_helper.py reply    <task_id> "<message>"
  python manus_helper.py stop     <task_id>

Exit codes: 0 ok, 1 usage/error, 2 task failed, 3 timeout.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE_URL = "https://api.manus.ai"
DEFAULT_PROFILE = "manus-1.6"          # also: manus-1.6-lite (fast/cheap), manus-1.6-max (best)
POLL_SECONDS = 8
TIMEOUT_SECONDS = 1800                 # 30 min hard cap for `run`


def _key() -> str:
    k = os.getenv("MANUS_API_KEY")
    if not k:
        sys.exit("MANUS_API_KEY not set. Add it to ~/.claude/.credentials.master.env "
                 "and export it, or set the env var.")
    return k


def _request(method: str, path: str, *, body=None, params=None):
    url = BASE_URL + path
    if params:
        url += "?" + urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("x-manus-api-key", _key())
    req.add_header("accept", "application/json")
    if data is not None:
        req.add_header("content-type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        sys.exit(f"HTTP {e.code} on {method} {path}: {detail}")
    except urllib.error.URLError as e:
        sys.exit(f"Network error on {method} {path}: {e.reason}")


# --- API wrappers ---------------------------------------------------------

def create_task(prompt: str, *, profile=DEFAULT_PROFILE, locale=None,
                interactive=False, title=None, hide=False, structured_schema=None):
    body = {
        "message": {"content": prompt},
        "agent_profile": profile,
        "interactive_mode": interactive,
        "hide_in_task_list": hide,
    }
    if locale:
        body["locale"] = locale
    if title:
        body["title"] = title
    if structured_schema:
        body["structured_output_schema"] = structured_schema
    return _request("POST", "/v2/task.create", body=body)


def list_messages(task_id: str, *, limit=20, order="desc", cursor=None):
    return _request("GET", "/v2/task.listMessages",
                    params={"task_id": task_id, "limit": limit, "order": order, "cursor": cursor})


def task_detail(task_id: str):
    return _request("GET", "/v2/task.detail", params={"task_id": task_id})


def send_message(task_id: str, text: str):
    return _request("POST", "/v2/task.sendMessage",
                    body={"task_id": task_id, "message": {"content": text}})


def stop_task(task_id: str):
    return _request("POST", "/v2/task.stop", body={"task_id": task_id})


def _agent_status(task_id: str):
    """Return (agent_status, messages_dump) from newest status_update event."""
    msgs = list_messages(task_id, limit=10, order="desc")
    for ev in msgs.get("messages", []) or []:
        st = (ev.get("status_update") or {}).get("agent_status")
        if st:
            return st, msgs
    return None, msgs


def latest_answer(msgs: dict):
    """Extract the newest assistant_message text from a listMessages dump."""
    for ev in msgs.get("messages", []) or []:
        am = ev.get("assistant_message")
        if am and am.get("content"):
            return am["content"]
    return None


def run_task(prompt: str, *, profile=DEFAULT_PROFILE, locale=None,
             poll=POLL_SECONDS, timeout=TIMEOUT_SECONDS):
    """Create a task and poll until stopped/error/timeout. Returns final message dump."""
    created = create_task(prompt, profile=profile, locale=locale)
    task_id = created.get("task_id")
    if not task_id:
        sys.exit(f"create failed: {json.dumps(created)}")
    sys.stderr.write(f"task_id={task_id}  url={created.get('task_url')}\n")
    deadline = time.time() + timeout
    while time.time() < deadline:
        status, msgs = _agent_status(task_id)
        sys.stderr.write(f"agent_status={status}\n")
        if status in ("stopped", "error"):
            return {"task_id": task_id, "task_url": created.get("task_url"),
                    "agent_status": status, "answer": latest_answer(msgs),
                    "messages": msgs}
        if status == "waiting":
            return {"task_id": task_id, "task_url": created.get("task_url"),
                    "agent_status": "waiting",
                    "note": "Task paused for input. Use `reply <task_id> \"...\"` to continue.",
                    "messages": msgs}
        time.sleep(poll)
    return {"task_id": task_id, "task_url": created.get("task_url"),
            "agent_status": "timeout", "timeout_seconds": timeout}


# --- CLI ------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(description="Manus API v2 client")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create"); c.add_argument("prompt")
    c.add_argument("--profile", default=DEFAULT_PROFILE)
    c.add_argument("--locale"); c.add_argument("--title")
    c.add_argument("--interactive", action="store_true")

    r = sub.add_parser("run"); r.add_argument("prompt")
    r.add_argument("--profile", default=DEFAULT_PROFILE)
    r.add_argument("--locale")
    r.add_argument("--poll", type=int, default=POLL_SECONDS)
    r.add_argument("--timeout", type=int, default=TIMEOUT_SECONDS)

    s = sub.add_parser("status"); s.add_argument("task_id")
    m = sub.add_parser("messages"); m.add_argument("task_id")
    m.add_argument("--limit", type=int, default=20); m.add_argument("--order", default="desc")
    rp = sub.add_parser("reply"); rp.add_argument("task_id"); rp.add_argument("message")
    st = sub.add_parser("stop"); st.add_argument("task_id")

    a = p.parse_args()
    if a.cmd == "create":
        out = create_task(a.prompt, profile=a.profile, locale=a.locale,
                          title=a.title, interactive=a.interactive)
    elif a.cmd == "run":
        out = run_task(a.prompt, profile=a.profile, locale=a.locale,
                       poll=a.poll, timeout=a.timeout)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        sys.exit(0 if out.get("agent_status") in ("stopped", "waiting")
                 else 3 if out.get("agent_status") == "timeout" else 2)
    elif a.cmd == "status":
        status, _ = _agent_status(a.task_id); out = {"task_id": a.task_id, "agent_status": status}
    elif a.cmd == "messages":
        out = list_messages(a.task_id, limit=a.limit, order=a.order)
    elif a.cmd == "reply":
        out = send_message(a.task_id, a.message)
    elif a.cmd == "stop":
        out = stop_task(a.task_id)
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
