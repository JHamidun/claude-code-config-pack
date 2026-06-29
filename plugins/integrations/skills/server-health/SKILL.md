---
name: server-health
description: "Server health checks via SSH - docker, systemctl, disk, memory, logs. Use when asked to check server status or diagnose issues."
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

## Tips

1. Use `--no-pager` for journalctl/systemctl
2. Set `timeout=15` on subprocess calls
3. Alert if disk >80% or memory <500MB free
