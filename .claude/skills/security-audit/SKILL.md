---
name: security-audit
description: Security auditing - vulnerability scanning, code review, OWASP checks, penetration testing guidance
---

# Security Audit Skill

## Overview

Навык для аудита безопасности: поиск уязвимостей, анализ кода, проверка OWASP Top 10.

## When to Use

- Аудит безопасности кода
- Поиск уязвимостей (XSS, SQLi, CSRF, etc.)
- Проверка конфигурации
- Анализ зависимостей
- Penetration testing guidance

## OWASP Top 10 (2021)

| # | Уязвимость | Проверка |
|---|------------|----------|
| A01 | **Broken Access Control** | Проверка авторизации, IDOR, privilege escalation |
| A02 | **Cryptographic Failures** | Слабое шифрование, hardcoded secrets |
| A03 | **Injection** | SQL, NoSQL, OS, LDAP injection |
| A04 | **Insecure Design** | Архитектурные проблемы |
| A05 | **Security Misconfiguration** | Дефолтные настройки, открытые порты |
| A06 | **Vulnerable Components** | Устаревшие зависимости |
| A07 | **Auth Failures** | Слабые пароли, session management |
| A08 | **Software/Data Integrity** | CI/CD security, unsigned updates |
| A09 | **Logging Failures** | Недостаточное логирование |
| A10 | **SSRF** | Server-Side Request Forgery |

## Security Checklist

### Authentication

```python
# ❌ Плохо
def login(username, password):
    user = db.query(f"SELECT * FROM users WHERE name='{username}'")  # SQLi!
    if user.password == password:  # Plain text!
        return True

# ✅ Хорошо
def login(username, password):
    user = db.query("SELECT * FROM users WHERE name = %s", (username,))
    if user and bcrypt.checkpw(password.encode(), user.password_hash):
        return create_session(user)
```

### Input Validation

```python
# ❌ Плохо
@app.route('/search')
def search():
    query = request.args.get('q')
    return f"<h1>Results for: {query}</h1>"  # XSS!

# ✅ Хорошо
from markupsafe import escape

@app.route('/search')
def search():
    query = escape(request.args.get('q', ''))
    return f"<h1>Results for: {query}</h1>"
```

### File Upload

```python
# ❌ Плохо
def upload(file):
    file.save(f'/uploads/{file.filename}')  # Path traversal!

# ✅ Хорошо
import os
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'pdf'}

def upload(file):
    if '.' in file.filename and \
       file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS:
        filename = secure_filename(file.filename)
        file.save(os.path.join('/uploads', filename))
```

## Scanning Tools

### Static Analysis (SAST)

```bash
# Python - Bandit
pip install bandit
bandit -r ./src -f json -o report.json

# JavaScript - ESLint Security
npm install eslint-plugin-security
eslint --ext .js,.ts ./src

# Multi-language - Semgrep
pip install semgrep
semgrep scan --config=auto ./
```

### Dependency Scanning

```bash
# Python
pip install safety
safety check

# Node.js
npm audit
npm audit fix

# Go
go list -m all | nancy sleuth
```

### Secrets Detection

```bash
# Gitleaks
gitleaks detect --source . --verbose

# TruffleHog
trufflehog filesystem ./

# Pattern matching
grep -rn "password\s*=\s*['\"]" ./
grep -rn "api_key\s*=\s*['\"]" ./
```

## Vulnerability Patterns

### SQL Injection

```python
# Detect patterns:
# - String concatenation in queries
# - f-strings with user input in SQL
# - .format() with user input in SQL

# Safe alternatives:
cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
User.query.filter_by(id=user_id).first()
```

### XSS (Cross-Site Scripting)

```javascript
// Detect patterns:
// - innerHTML with user input
// - document.write() with user input
// - eval() with any input

// Safe alternatives:
element.textContent = userInput;
element.innerText = userInput;
```

### Command Injection

```python
# ❌ Dangerous
os.system(f"ping {user_input}")
subprocess.call(f"ls {path}", shell=True)

# ✅ Safe
subprocess.run(["ping", "-c", "4", validated_ip], check=True)
subprocess.run(["ls", validated_path], shell=False)
```

### Path Traversal

```python
# ❌ Dangerous
open(f"/data/{filename}")

# ✅ Safe
import os
base_path = "/data"
full_path = os.path.realpath(os.path.join(base_path, filename))
if not full_path.startswith(base_path):
    raise ValueError("Invalid path")
```

## Security Headers

```python
# Flask example
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

## Audit Report Template

```markdown
# Security Audit Report

## Executive Summary
- **Scope**: [описание]
- **Date**: [дата]
- **Risk Level**: Critical/High/Medium/Low

## Findings

### [CRITICAL] Finding 1: SQL Injection in login.py
- **Location**: src/auth/login.py:42
- **Description**: User input directly concatenated into SQL query
- **Impact**: Full database compromise
- **Remediation**: Use parameterized queries
- **CVSS Score**: 9.8

### [HIGH] Finding 2: Hardcoded API Key
- **Location**: src/config.py:15
- **Description**: API key stored in source code
- **Impact**: Unauthorized access to external service
- **Remediation**: Move to environment variables

## Recommendations
1. Implement input validation
2. Update dependencies
3. Enable security headers
4. Add logging and monitoring
```

## Automated Audit Script

```bash
#!/bin/bash
# security-audit.sh

echo "=== Security Audit ==="

echo "\n[1] Checking for secrets..."
gitleaks detect --source . --no-git

echo "\n[2] Scanning Python code..."
bandit -r ./src -ll

echo "\n[3] Checking dependencies..."
safety check || pip-audit

echo "\n[4] Running Semgrep..."
semgrep scan --config=p/security-audit ./src

echo "\n[5] Checking for outdated packages..."
pip list --outdated

echo "\n=== Audit Complete ==="
```

## Tips

1. **Defense in depth** - несколько уровней защиты
2. **Principle of least privilege** - минимальные права
3. **Fail securely** - при ошибке - блокировка, не пропуск
4. **Don't trust user input** - всегда валидировать
5. **Keep dependencies updated** - регулярные обновления
6. **Log security events** - аудит и мониторинг
