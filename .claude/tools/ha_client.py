"""
Home Assistant CLI for Claude Code.
Control and inspect a Home Assistant instance via its documented REST API
(+ WebSocket API for live events and registries).

Connect -> do -> print -> exit. No daemon, no gateway.

Credentials: ~/.claude/.credentials.master.env
    HA_URL   - base URL of the instance, e.g. http://homeassistant.local:8123
    HA_TOKEN - Long-Lived Access Token (HA profile -> Security -> Create token)

Endpoints used (official REST API docs):
    GET  /api/                      -> ping
    GET  /api/states                -> all entity states
    GET  /api/states/<entity_id>    -> one entity
    POST /api/services/<dom>/<svc>  -> call a service
    GET  /api/config                -> instance config
    GET  /api/history/period/<ts>   -> state history
WebSocket API (/api/websocket):
    subscribe_events                -> live event stream (documented)
    config/area_registry/list       -> areas   (internal frontend command)
    config/device_registry/list     -> devices (internal frontend command)

Usage:
    python ha_client.py ping
    python ha_client.py states --domain light
    python ha_client.py get light.kitchen
    python ha_client.py on light.kitchen
    python ha_client.py call light turn_on --entity light.kitchen --data '{"brightness": 128}'
    python ha_client.py history sensor.temperature --hours 12
    python ha_client.py events --type state_changed --limit 20
"""

import argparse
import io
import json
import os
import sys
import urllib.parse
from datetime import datetime, timedelta, timezone
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

try:
    import requests
except ImportError:
    print("[!] Missing dependency: requests")
    print("    Install: pip install requests")
    sys.exit(2)

HA_URL = os.environ.get("HA_URL", "").rstrip("/")
HA_TOKEN = os.environ.get("HA_TOKEN", "")
TIMEOUT = 15


def require_credentials():
    """Exit with clear setup instructions if HA is not configured."""
    missing = []
    if not HA_URL:
        missing.append("HA_URL")
    if not HA_TOKEN:
        missing.append("HA_TOKEN")
    if missing:
        print("[!] Home Assistant is not configured. Missing: " + ", ".join(missing))
        print()
        print("    Add to ~/.claude/.credentials.master.env:")
        print("      HA_URL=http://homeassistant.local:8123   # or http://<ip>:8123")
        print("      HA_TOKEN=<long-lived access token>")
        print()
        print("    Token: HA web UI -> your profile (bottom left) -> Security tab ->")
        print("           'Long-lived access tokens' -> Create Token.")
        print()
        print("    No HA instance yet? Install options: Home Assistant OS on a")
        print("    Raspberry Pi / mini-PC, or Docker: docker run -d --name homeassistant \\")
        print("      --network=host ghcr.io/home-assistant/home-assistant:stable")
        sys.exit(2)


def headers():
    return {
        "Authorization": f"Bearer {HA_TOKEN}",
        "Content-Type": "application/json",
    }


def api_get(path):
    url = f"{HA_URL}{path}"
    try:
        resp = requests.get(url, headers=headers(), timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        print(f"[!] Cannot connect to {HA_URL} - is the instance up and the URL correct?")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"[!] Timeout ({TIMEOUT}s) connecting to {HA_URL}")
        sys.exit(1)
    check_http(resp)
    return resp.json()


def api_post(path, payload):
    url = f"{HA_URL}{path}"
    try:
        resp = requests.post(url, headers=headers(), json=payload, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        print(f"[!] Cannot connect to {HA_URL} - is the instance up and the URL correct?")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"[!] Timeout ({TIMEOUT}s) connecting to {HA_URL}")
        sys.exit(1)
    check_http(resp)
    return resp.json() if resp.text else []


def check_http(resp):
    if resp.status_code == 401:
        print("[!] 401 Unauthorized - HA_TOKEN is invalid or revoked.")
        print("    Create a new Long-Lived Access Token in HA profile -> Security.")
        sys.exit(1)
    if resp.status_code == 404:
        print(f"[!] 404 Not Found: {resp.url}")
        print("    Entity/service does not exist, or endpoint unavailable in this HA version.")
        sys.exit(1)
    if resp.status_code >= 400:
        print(f"[!] HTTP {resp.status_code}: {resp.text[:500]}")
        sys.exit(1)


def fmt_state(s):
    """One-line human-readable entity state."""
    entity_id = s.get("entity_id", "?")
    state = s.get("state", "?")
    attrs = s.get("attributes", {})
    name = attrs.get("friendly_name", "")
    unit = attrs.get("unit_of_measurement", "")
    changed = (s.get("last_changed") or "")[:19].replace("T", " ")
    val = f"{state}{unit}" if unit else state
    line = f"{entity_id:<45} {val:<15} {changed}"
    if name and name != entity_id:
        line += f"  ({name})"
    return line


def print_json(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ========== COMMANDS ==========


def cmd_ping(args):
    require_credentials()
    data = api_get("/api/")
    if args.json:
        print_json({"ok": True, "url": HA_URL, "response": data})
    else:
        print(f"OK: {HA_URL} -> {data.get('message', data)}")


def cmd_states(args):
    require_credentials()
    states = api_get("/api/states")
    if args.domain:
        states = [s for s in states if s.get("entity_id", "").startswith(args.domain + ".")]
    states.sort(key=lambda s: s.get("entity_id", ""))
    if args.json:
        print_json(states)
        return
    if not states:
        print(f"No entities" + (f" in domain '{args.domain}'" if args.domain else ""))
        return
    for s in states:
        print(fmt_state(s))
    print(f"\nTotal: {len(states)} entities")


def cmd_get(args):
    require_credentials()
    s = api_get(f"/api/states/{args.entity_id}")
    if args.json:
        print_json(s)
        return
    attrs = s.get("attributes", {})
    print(f"Entity:       {s.get('entity_id')}")
    print(f"State:        {s.get('state')}{attrs.get('unit_of_measurement', '')}")
    print(f"Name:         {attrs.get('friendly_name', '-')}")
    print(f"Last changed: {s.get('last_changed', '-')}")
    print(f"Last updated: {s.get('last_updated', '-')}")
    if attrs:
        print("Attributes:")
        for k, v in attrs.items():
            if k in ("friendly_name", "unit_of_measurement"):
                continue
            print(f"  {k}: {v}")


def _service_call(domain, service, entity_id=None, extra_data=None, as_json=False):
    payload = {}
    if extra_data:
        payload.update(extra_data)
    if entity_id:
        payload["entity_id"] = entity_id
    result = api_post(f"/api/services/{domain}/{service}", payload)
    if as_json:
        print_json({"called": f"{domain}.{service}", "payload": payload, "changed_states": result})
        return
    print(f"Called {domain}.{service}" + (f" on {entity_id}" if entity_id else ""))
    if isinstance(result, list) and result:
        print("Changed states:")
        for s in result:
            print("  " + fmt_state(s))
    else:
        print("(no state changes reported in response)")


def cmd_call(args):
    require_credentials()
    extra = None
    if args.data:
        try:
            extra = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"[!] --data is not valid JSON: {e}")
            sys.exit(2)
    _service_call(args.domain, args.service, args.entity, extra, args.json)


def cmd_on(args):
    require_credentials()
    _service_call("homeassistant", "turn_on", args.entity_id, None, args.json)


def cmd_off(args):
    require_credentials()
    _service_call("homeassistant", "turn_off", args.entity_id, None, args.json)


def cmd_toggle(args):
    require_credentials()
    _service_call("homeassistant", "toggle", args.entity_id, None, args.json)


def cmd_history(args):
    require_credentials()
    start = datetime.now(timezone.utc) - timedelta(hours=args.hours)
    start_str = urllib.parse.quote(start.isoformat())
    path = f"/api/history/period/{start_str}?filter_entity_id={args.entity_id}"
    data = api_get(path)
    if args.json:
        print_json(data)
        return
    if not data or not data[0]:
        print(f"No history for {args.entity_id} in the last {args.hours}h")
        return
    entries = data[0]
    print(f"History for {args.entity_id} (last {args.hours}h, {len(entries)} points):")
    for e in entries:
        ts = (e.get("last_changed") or e.get("last_updated") or "")[:19].replace("T", " ")
        unit = e.get("attributes", {}).get("unit_of_measurement", "")
        print(f"  {ts}  {e.get('state')}{unit}")


def cmd_config(args):
    require_credentials()
    cfg = api_get("/api/config")
    if args.json:
        print_json(cfg)
        return
    print(f"Location:   {cfg.get('location_name')}")
    print(f"Version:    {cfg.get('version')}")
    print(f"Time zone:  {cfg.get('time_zone')}")
    print(f"Units:      {cfg.get('unit_system')}")
    print(f"State:      {cfg.get('state')}")
    print(f"Components: {len(cfg.get('components', []))}")
    print(f"URL (int):  {cfg.get('internal_url')}")
    print(f"URL (ext):  {cfg.get('external_url')}")


# ---- WebSocket-based commands ----


def _ws_url():
    ws = HA_URL.replace("https://", "wss://").replace("http://", "ws://")
    return f"{ws}/api/websocket"


def _require_websockets():
    try:
        import websockets  # noqa: F401
        return True
    except ImportError:
        print("[!] Missing dependency for WebSocket commands: websockets")
        print("    Install: pip install websockets")
        sys.exit(2)


async def _ws_auth(ws):
    """Perform HA WebSocket auth handshake. Returns True on success."""
    msg = json.loads(await ws.recv())
    if msg.get("type") != "auth_required":
        print(f"[!] Expected auth_required, got: {msg.get('type')}")
        return False
    await ws.send(json.dumps({"type": "auth", "access_token": HA_TOKEN}))
    msg = json.loads(await ws.recv())
    if msg.get("type") != "auth_ok":
        print(f"[!] WebSocket auth failed: {msg}")
        print("    Check HA_TOKEN (Long-Lived Access Token).")
        return False
    return True


async def _ws_command(command_type):
    """Connect, auth, run one WS command, return its result."""
    import websockets

    async with websockets.connect(_ws_url(), open_timeout=TIMEOUT) as ws:
        if not await _ws_auth(ws):
            sys.exit(1)
        await ws.send(json.dumps({"id": 1, "type": command_type}))
        while True:
            msg = json.loads(await ws.recv())
            if msg.get("id") == 1:
                if not msg.get("success"):
                    err = msg.get("error", {})
                    print(f"[!] WS command '{command_type}' failed: "
                          f"{err.get('code')} {err.get('message')}")
                    print("    This is an internal frontend command - it may be "
                          "unavailable in your HA version.")
                    sys.exit(1)
                return msg.get("result")


def cmd_events(args):
    require_credentials()
    _require_websockets()
    import asyncio
    import websockets

    async def stream():
        async with websockets.connect(_ws_url(), open_timeout=TIMEOUT) as ws:
            if not await _ws_auth(ws):
                sys.exit(1)
            sub = {"id": 1, "type": "subscribe_events"}
            if args.type:
                sub["event_type"] = args.type
            await ws.send(json.dumps(sub))
            ack = json.loads(await ws.recv())
            if not ack.get("success"):
                print(f"[!] Subscription failed: {ack}")
                sys.exit(1)
            label = args.type or "all events"
            print(f"Listening for {label} on {HA_URL} "
                  f"(limit {args.limit}, Ctrl+C to stop)...")
            count = 0
            while count < args.limit:
                msg = json.loads(await ws.recv())
                if msg.get("type") != "event":
                    continue
                event = msg.get("event", {})
                count += 1
                if args.json:
                    print(json.dumps(event, ensure_ascii=False))
                    continue
                etype = event.get("event_type", "?")
                ts = (event.get("time_fired") or "")[:19].replace("T", " ")
                data = event.get("data", {})
                if etype == "state_changed":
                    eid = data.get("entity_id", "?")
                    old = (data.get("old_state") or {}).get("state", "?")
                    new = (data.get("new_state") or {}).get("state", "?")
                    print(f"{ts}  {eid}: {old} -> {new}")
                else:
                    brief = json.dumps(data, ensure_ascii=False)
                    if len(brief) > 120:
                        brief = brief[:120] + "..."
                    print(f"{ts}  [{etype}] {brief}")
            print(f"\nDone: {count} events")

    try:
        asyncio.run(stream())
    except KeyboardInterrupt:
        print("\nStopped")


def cmd_areas(args):
    require_credentials()
    _require_websockets()
    import asyncio

    result = asyncio.run(_ws_command("config/area_registry/list"))
    if args.json:
        print_json(result)
        return
    if not result:
        print("No areas configured")
        return
    for a in result:
        print(f"{a.get('area_id', '?'):<30} {a.get('name', '?')}")
    print(f"\nTotal: {len(result)} areas")


def cmd_devices(args):
    require_credentials()
    _require_websockets()
    import asyncio

    result = asyncio.run(_ws_command("config/device_registry/list"))
    if args.json:
        print_json(result)
        return
    if not result:
        print("No devices registered")
        return
    for d in result:
        name = d.get("name_by_user") or d.get("name") or "?"
        manuf = d.get("manufacturer") or ""
        model = d.get("model") or ""
        area = d.get("area_id") or "-"
        print(f"{name:<40} {manuf} {model}  [area: {area}]")
    print(f"\nTotal: {len(result)} devices")


# ========== MAIN ==========


def main():
    parser = argparse.ArgumentParser(
        prog="ha_client.py",
        description="Home Assistant CLI (REST + WebSocket). "
                    "Needs HA_URL and HA_TOKEN in ~/.claude/.credentials.master.env",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_json(p):
        p.add_argument("--json", action="store_true", help="machine-readable JSON output")

    p = sub.add_parser("ping", help="check API is alive (GET /api/)")
    add_json(p)
    p.set_defaults(func=cmd_ping)

    p = sub.add_parser("states", help="list entity states (GET /api/states)")
    p.add_argument("--domain", help="filter by domain, e.g. light, switch, sensor")
    add_json(p)
    p.set_defaults(func=cmd_states)

    p = sub.add_parser("get", help="get one entity state (GET /api/states/<id>)")
    p.add_argument("entity_id", help="e.g. light.kitchen")
    add_json(p)
    p.set_defaults(func=cmd_get)

    p = sub.add_parser("call", help="call a service (POST /api/services/<domain>/<service>)")
    p.add_argument("domain", help="e.g. light, climate, media_player")
    p.add_argument("service", help="e.g. turn_on, set_temperature")
    p.add_argument("--entity", help="target entity_id")
    p.add_argument("--data", help='extra service data as JSON, e.g. \'{"brightness": 128}\'')
    add_json(p)
    p.set_defaults(func=cmd_call)

    p = sub.add_parser("on", help="turn entity on (homeassistant.turn_on)")
    p.add_argument("entity_id")
    add_json(p)
    p.set_defaults(func=cmd_on)

    p = sub.add_parser("off", help="turn entity off (homeassistant.turn_off)")
    p.add_argument("entity_id")
    add_json(p)
    p.set_defaults(func=cmd_off)

    p = sub.add_parser("toggle", help="toggle entity (homeassistant.toggle)")
    p.add_argument("entity_id")
    add_json(p)
    p.set_defaults(func=cmd_toggle)

    p = sub.add_parser("history", help="entity state history (GET /api/history/period)")
    p.add_argument("entity_id")
    p.add_argument("--hours", type=int, default=24, help="lookback window, default 24")
    add_json(p)
    p.set_defaults(func=cmd_history)

    p = sub.add_parser("events", help="live event stream via WebSocket subscribe_events")
    p.add_argument("--type", help="event type filter, e.g. state_changed (default: all)")
    p.add_argument("--limit", type=int, default=50, help="stop after N events, default 50")
    add_json(p)
    p.set_defaults(func=cmd_events)

    p = sub.add_parser("config", help="instance config (GET /api/config)")
    add_json(p)
    p.set_defaults(func=cmd_config)

    p = sub.add_parser("areas", help="list areas (WS config/area_registry/list - internal API)")
    add_json(p)
    p.set_defaults(func=cmd_areas)

    p = sub.add_parser("devices", help="list devices (WS config/device_registry/list - internal API)")
    add_json(p)
    p.set_defaults(func=cmd_devices)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
