---
name: threat-hunting
description: "Threat hunting: правила Sigma, detection engineering. Триггеры: «охота на угрозы», «sigma rules». НЕ свой код → security-audit."
---

# Threat Hunting Skill

## Overview

Threat hunting с использованием Sigma rules, detection engineering, анализ безопасности.

## When to Use

- Проактивный поиск угроз
- Написание detection rules
- Анализ логов безопасности
- Incident response
- Security monitoring

## Sigma Rules

### Basic Structure

```yaml
title: Suspicious PowerShell Execution
id: 12345678-1234-1234-1234-123456789abc
status: experimental
description: Detects suspicious PowerShell command execution
author: Your Name
date: 2024/01/15
references:
    - https://attack.mitre.org/techniques/T1059/001/
logsource:
    category: process_creation
    product: windows
detection:
    selection:
        Image|endswith: '\powershell.exe'
        CommandLine|contains:
            - '-enc'
            - '-EncodedCommand'
            - 'bypass'
            - 'hidden'
    condition: selection
falsepositives:
    - Legitimate admin scripts
level: medium
tags:
    - attack.execution
    - attack.t1059.001
```

### Common Detection Patterns

```yaml
# String matching
detection:
    selection:
        CommandLine|contains: 'mimikatz'

# Multiple conditions
detection:
    selection1:
        Image|endswith: '\cmd.exe'
    selection2:
        CommandLine|contains:
            - 'whoami'
            - 'net user'
    condition: selection1 and selection2

# Exclusions
detection:
    selection:
        EventType: 'ProcessCreate'
    filter:
        User: 'SYSTEM'
    condition: selection and not filter

# Regex
detection:
    selection:
        CommandLine|re: '.*\.(ps1|bat|cmd).*-[eE].*'
```

### Sigma Modifiers

| Modifier | Description |
|----------|-------------|
| `contains` | String contains |
| `startswith` | String starts with |
| `endswith` | String ends with |
| `re` | Regular expression |
| `base64` | Base64 encoded |
| `all` | All items must match |
| `cidr` | IP CIDR range |

## Threat Categories

### Execution (T1059)

```yaml
title: Suspicious Script Execution
logsource:
    category: process_creation
detection:
    selection:
        Image|endswith:
            - '\powershell.exe'
            - '\pwsh.exe'
            - '\cmd.exe'
            - '\wscript.exe'
            - '\cscript.exe'
        CommandLine|contains:
            - 'downloadstring'
            - 'invoke-expression'
            - 'iex'
            - 'bypass'
    condition: selection
```

### Persistence (T1053)

```yaml
title: Scheduled Task Creation
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 4698
    filter:
        TaskName|contains:
            - 'Microsoft'
            - 'Windows'
    condition: selection and not filter
```

### Defense Evasion (T1562)

```yaml
title: Windows Defender Disabled
logsource:
    product: windows
    service: security
detection:
    selection:
        EventID: 5001
    condition: selection
level: high
```

### Credential Access (T1003)

```yaml
title: LSASS Memory Access
logsource:
    category: process_access
    product: windows
detection:
    selection:
        TargetImage|endswith: '\lsass.exe'
        GrantedAccess|contains:
            - '0x1010'
            - '0x1410'
    filter:
        SourceImage|endswith:
            - '\wmiprvse.exe'
            - '\taskmgr.exe'
    condition: selection and not filter
level: critical
```

## Log Sources

### Windows Event Logs

| Log | Event IDs | Use Case |
|-----|-----------|----------|
| Security | 4624, 4625 | Logon events |
| Security | 4688 | Process creation |
| Security | 4698-4702 | Scheduled tasks |
| Sysmon | 1 | Process create |
| Sysmon | 3 | Network connection |
| Sysmon | 7 | Image load (DLL) |
| Sysmon | 10 | Process access |
| PowerShell | 4103, 4104 | Script block logging |

### Linux Logs

```yaml
logsource:
    product: linux
    service: auditd
detection:
    selection:
        type: 'EXECVE'
        a0|contains: '/bin/bash'
        a1|contains: '-c'
```

## Hunting Queries

### Splunk

```spl
# Suspicious PowerShell
index=windows sourcetype=WinEventLog:Security EventCode=4688
| where match(CommandLine, "(?i)(invoke-expression|iex|downloadstring)")
| stats count by User, CommandLine, Computer

# Failed logins
index=windows sourcetype=WinEventLog:Security EventCode=4625
| stats count by src_ip, user
| where count > 10

# Rare processes
index=windows sourcetype=WinEventLog:Security EventCode=4688
| rare NewProcessName limit=20
```

### Elastic/KQL

```kql
// Suspicious command lines
process.command_line: (*mimikatz* OR *sekurlsa* OR *kerberos*)

// Encoded PowerShell
process.name: "powershell.exe" AND
process.command_line: (*-enc* OR *-EncodedCommand*)

// Network connections to rare ports
event.category: "network" AND
destination.port: (4444 OR 5555 OR 8888)
```

## Detection Engineering

### Rule Development Process

```
1. HYPOTHESIS
   - What attack are we detecting?
   - MITRE ATT&CK technique?

2. DATA REQUIREMENTS
   - What logs needed?
   - Are they being collected?

3. LOGIC DEVELOPMENT
   - Write Sigma rule
   - Test against known-bad

4. TESTING
   - Atomic Red Team simulation
   - Check false positives

5. TUNING
   - Add exclusions
   - Adjust thresholds

6. DEPLOYMENT
   - Convert to SIEM format
   - Set alerting
```

### Sigma to SIEM Conversion

```bash
# Install sigmac
pip install sigma-cli

# Convert to Splunk
sigma convert -t splunk rule.yml

# Convert to Elastic
sigma convert -t elasticsearch rule.yml

# Convert to QRadar
sigma convert -t qradar rule.yml
```

## Python Sigma Parser

```python
from sigma.parser.rule import SigmaRule
from sigma.backends.splunk import SplunkBackend

def convert_sigma_to_splunk(rule_path: str) -> str:
    """Convert Sigma rule to Splunk query"""
    with open(rule_path, 'r') as f:
        rule = SigmaRule.from_yaml(f.read())

    backend = SplunkBackend()
    return backend.generate(rule)

def validate_sigma_rule(rule_path: str) -> dict:
    """Validate Sigma rule syntax"""
    try:
        with open(rule_path, 'r') as f:
            rule = SigmaRule.from_yaml(f.read())
        return {
            "valid": True,
            "title": rule.title,
            "level": rule.level,
            "tags": rule.tags
        }
    except Exception as e:
        return {
            "valid": False,
            "error": str(e)
        }
```

## Atomic Red Team Testing

```bash
# Install Atomic Red Team
IEX (IWR 'https://raw.githubusercontent.com/redcanaryco/invoke-atomicredteam/master/install-atomicredteam.ps1' -UseBasicParsing)

# Run specific test
Invoke-AtomicTest T1059.001 -TestNumbers 1

# Run and generate logs
Invoke-AtomicTest T1003.001 -GetPrereqs
Invoke-AtomicTest T1003.001 -TestNumbers 1,2,3

# Cleanup
Invoke-AtomicTest T1059.001 -Cleanup
```

## Hunting Playbook Template

```markdown
# Threat Hunt: [Name]

## Hypothesis
Based on [intelligence/observation], we believe [threat actor/technique]
may be present in our environment.

## MITRE ATT&CK
- Technique: [T1xxx]
- Tactic: [Tactic name]

## Data Sources Required
- [ ] Windows Security Events
- [ ] Sysmon
- [ ] Network logs
- [ ] EDR telemetry

## Detection Logic

### Query 1: [Description]
```query
[SIEM query here]
```

### Query 2: [Description]
```query
[Query here]
```

## Investigation Steps
1. Run queries
2. Analyze results
3. Pivot on IOCs
4. Document findings

## Findings
| Timestamp | Host | User | Finding | Severity |
|-----------|------|------|---------|----------|
| [Time] | [Host] | [User] | [Finding] | [H/M/L] |

## Recommendations
1. [Recommendation 1]
2. [Recommendation 2]

## IOCs Discovered
- IP: [x.x.x.x]
- Hash: [SHA256]
- Domain: [domain.com]
```

## Tips

1. **Start with hypothesis** - что ищем?
2. **Know your baseline** - что "нормально"
3. **Use MITRE ATT&CK** - структурируй охоту
4. **Document everything** - для повторяемости
5. **Tune rules** - уменьшай false positives
6. **Automate testing** - Atomic Red Team
7. **Share intelligence** - community rules
