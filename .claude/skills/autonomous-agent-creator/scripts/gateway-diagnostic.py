#!/usr/bin/env python3
"""
gateway-diagnostic.py — AI Gateway diagnostic tool for OpenClaw fleet.

Checks:
1. Which providers are alive (direct API probe)
2. Circuit breaker state (from gateway logs)
3. Cron job status across all bots

Usage:
  python3 gateway-diagnostic.py [--server your-server]

Run on the server or via SSH:
  ssh "$SERVER" "python3 /opt/ai-gateway/gateway-diagnostic.py"
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓, эмодзи) валит процесс UnicodeEncodeError —
# нередко на --help, то есть ДО любой полезной работы. errors="replace" оставляет
# вывод читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


import subprocess
import json
import os
from datetime import datetime

def run(cmd: str) -> str:
    """Run a shell command and return its combined output — never None.

    `text=True` without an explicit encoding decodes with the console codepage.
    On Windows that is cp866/cp1251, and docker's own output contains bytes those
    codecs reject: the reader thread dies with UnicodeDecodeError, `result.stdout`
    comes back as None, and the caller blows up on `None + str` — an error that
    says nothing about the real cause. Decode as UTF-8 with replacement instead,
    and coerce None away so every caller can rely on getting a string.
    """
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True,
                                text=True, encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"[gateway-diagnostic] не удалось запустить команду: {exc}"
    return (result.stdout or "") + (result.stderr or "")

def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def check_gateway_health():
    section("AI Gateway Health")

    # Check container status
    status = run("docker ps --filter name=ai-gateway --format '{{.Status}}'").strip()
    print(f"Container status: {status}")

    # Check recent errors
    errors = run("docker logs ai-gateway --since 5m 2>&1 | grep -c 'ERROR'").strip()
    print(f"Errors (last 5min): {errors}")

    # Check circuit breaker state
    cb_lines = run("docker logs ai-gateway --since 30m 2>&1 | grep -E 'OPEN|CLOSED|HALF' | tail -5")
    print(f"\nCircuit breaker (last 30min):")
    for line in cb_lines.strip().split('\n'):
        if line:
            print(f"  {line.strip()}")

    # Check failover success/failure
    ok = run("docker logs ai-gateway --since 30m 2>&1 | grep -c 'FAILOVER OK'").strip()
    exhaust = run("docker logs ai-gateway --since 30m 2>&1 | grep -c 'ALL MODELS EXHAUSTED'").strip()
    print(f"\nFailover OK: {ok} | Exhausted: {exhaust}")


def check_openclaw_fleet():
    section("OpenClaw Fleet")

    containers = run("docker ps --format '{{.Names}}' | grep openclaw").strip().split('\n')
    containers = [c for c in containers if c]

    print(f"Active containers: {len(containers)}")
    print()

    for c in containers:
        # Get last activity
        last_ok = run(f"docker logs {c} 2>&1 | grep '⇄ res ✓' | tail -1").strip()
        last_err = run(f"docker logs {c} 2>&1 | grep -iE 'error|rate limit' | tail -1").strip()

        status_icon = "✅" if last_ok and not last_err else ("⚠️" if last_err else "❓")
        print(f"  {status_icon} {c}")
        if last_ok:
            print(f"      Last OK: {last_ok[:80]}")
        if last_err:
            print(f"      Last ERR: {last_err[:80]}")
        print()


def check_cron_health():
    section("Cron Jobs Status")

    containers = run("docker ps --format '{{.Names}}' | grep openclaw").strip().split('\n')
    containers = [c for c in containers if c]

    for c in containers:
        config_vol = f"{c}-config"
        cron_path = f"/var/lib/docker/volumes/{config_vol}/_data/cron/jobs.json"

        if not os.path.exists(cron_path):
            continue

        try:
            with open(cron_path) as f:
                data = json.load(f)

            jobs = data.get("jobs", [])
            if not jobs:
                continue

            print(f"  {c}:")
            for j in jobs:
                status = j.get("state", {}).get("lastStatus", "?")
                enabled = j.get("enabled", False)
                icon = "✅" if status == "ok" else ("❌" if status == "error" else "❓")
                en_icon = "" if enabled else " [DISABLED]"
                sched = j.get("schedule", {}).get("expr", "?")
                print(f"    {icon} {j['id'][:30]:30} | {sched:15} | {status}{en_icon}")
            print()
        except (json.JSONDecodeError, FileNotFoundError, PermissionError):
            pass


def main():
    print(f"🔍 AI Gateway Diagnostic — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    check_gateway_health()
    check_openclaw_fleet()
    check_cron_health()

    section("Summary")
    print("  Run fixes if needed:")
    print("    docker restart ai-gateway          # reset circuit breaker")
    print("    docker restart openclaw-<name>      # restart specific bot")
    print("    cat /opt/ai-gateway/config.yaml     # check credentials")
    print()


if __name__ == "__main__":
    main()
