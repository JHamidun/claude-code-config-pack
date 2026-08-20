---
name: server-health
description: "Проверка сервера по SSH: docker, systemctl, диск, память, логи. Триггеры: «проверь сервер», «почему упало на сервере». НЕ процедуры и откаты→runbook."
---

# Server Health Check Skill

## Servers

| Alias | IP | SSH |
|-------|----|----|
| your-server | YOUR_SERVER_IP | `ssh your-server` |
| secondary-server | see ~/.ssh/config | `ssh your-server-2` |

## Quick Health Check

```bash
ssh your-server "echo '=== DOCKER ===' && docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}' && echo && echo '=== DISK ===' && df -h / && echo && echo '=== MEMORY ===' && free -h && echo && echo '=== LOAD ===' && uptime"
```

## Individual Checks

```bash
# Docker containers
ssh your-server "docker ps --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"

# Container logs
ssh your-server "docker logs --tail 50 container_name"

# Disk space
ssh your-server "df -h"

# Memory
ssh your-server "free -h"

# System load
ssh your-server "uptime"

# Service status
ssh your-server "systemctl status nginx"

# Recent errors
ssh your-server "journalctl --since '1 hour ago' --priority=err --no-pager | tail -20"

# Listening ports
ssh your-server "ss -tlnp"
```

## Health via Python

```python
import subprocess

def ssh_cmd(host, cmd):
    result = subprocess.run(
        ["ssh", host, cmd],
        capture_output=True, text=True, timeout=15
    )
    return result.stdout.strip()

def health_check(host="your-server"):
    return {
        "docker": ssh_cmd(host, "docker ps --format '{{.Names}}\\t{{.Status}}'"),
        "disk": ssh_cmd(host, "df -h / | tail -1"),
        "memory": ssh_cmd(host, "free -h | grep Mem"),
        "load": ssh_cmd(host, "uptime"),
    }
```

## Before Changing Anything (checks are read-only, fixes are not)

A health check often turns into a fix. Four lines before the first mutating command:

- [ ] **Return point** — `cp <file> <file>.bak-$(date +%Y%m%dT%H%M%SZ)` for any config you touch; for a container, note its current `Status`/uptime so you can tell a regression from a cure
- [ ] **Blast radius** — `docker ps` first: which other stacks share this network, volume or port? your-server runs 150+ containers
- [ ] **Revert trigger** — decide in advance what makes you roll back ("service does not answer within 2 min")
- [ ] **Verify the effect, not the command** — `Up 5 seconds` is not "it works"; hit the real endpoint / send a real message

Full procedures with rollback and escalation (bot silent, Hermes restart, cron did not fire, disk full, fleet liveness) → skill `runbook`.

## Tips

1. Use `--no-pager` for journalctl/systemctl
2. Set `timeout=15` on subprocess calls
3. Alert if disk >80% or memory <500MB free
