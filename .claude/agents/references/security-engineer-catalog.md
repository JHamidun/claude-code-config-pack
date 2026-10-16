# security-engineer — detection catalog

Reference for the `security-engineer` agent. Read a section when you are actually
auditing that surface; do not load the whole file by default.

- OWASP Top 10 → detection hints per category, when classifying a finding
- STRIDE → during Phase 1 threat modeling
- Compliance → only for the frameworks that apply to the audited system
- Security headers → when reviewing HTTP responses / edge config
- Secrets patterns → when grepping a repo for leaked credentials

---

## OWASP Top 10 (2025) — detection hints

Concrete patterns worth grepping for. The classification itself is standard; what
follows is the part that is easy to miss in a hurry.

### A01: Broken Access Control
- Route handlers without an auth middleware/decorator (`@app.route` with no
  `@login_required`); object fetched by `params[:id]` with no ownership check;
  `../` reaching the filesystem; CORS reflecting arbitrary origins.
- Fix: server-side authorization, deny by default, indirect object references.

### A02: Cryptographic Failures
- `hashlib.md5`/`sha1` on passwords, DES/RC4, hardcoded keys/IVs, IV reuse,
  plaintext-looking password columns in the schema, no encryption at rest.
- Fix: argon2/bcrypt for passwords, AES-256-GCM, TLS 1.2+.

### A03: Injection
- `f"SELECT ... {user_id}"`, template strings in `db.query`, `.raw(`,
  `os.system(f"cmd {input}")`, `exec`/`compile` on request data, `innerHTML =`.
- Fix: parameterized queries/ORM, output encoding + CSP, no dynamic code exec.

### A04: Insecure Design
- Login with no lockout or rate limit, upload with no size/type cap, unbounded
  resource allocation per request, no CAPTCHA on public write endpoints.

### A05: Security Misconfiguration
- `DEBUG = True` reachable in prod, default credentials, directory listing,
  stack traces in 5xx bodies, missing security headers.

### A06: Vulnerable and Outdated Components
- Lockfile packages 2+ majors behind, GHSA/CVE advisories, unmaintained or
  typosquatted names, `postinstall` scripts in dependencies.

### A07: Identification and Authentication Failures
- Session id in URL, no session rotation after login, unlimited login attempts,
  no MFA path, password reset tokens without expiry or single use.

### A08: Software and Data Integrity Failures
- Python `pickle` / Java `ObjectInputStream` on untrusted data, `yaml.load()`
  without `SafeLoader`, unsigned artifacts, webhooks accepted without signature
  verification, CDN scripts without SRI.

### A09: Security Logging and Monitoring Failures
- No log line on auth success/failure, PII or tokens written to logs, no
  alerting path, no retention policy.

### A10: SSRF
- `requests.get(user_url)`, `fetch(params.webhook_url)`, link unfurling/preview
  features, PDF/image fetchers.
- Fix: allowlist, block 127.0.0.0/8, 10/8, 172.16/12, 192.168/16, 169.254/16
  (cloud metadata), disable redirect following.

---

## STRIDE

| Threat | Example | Mitigation |
|---|---|---|
| Spoofing | Stolen JWT, forged API key | MFA, token rotation, mTLS |
| Tampering | SQLi, MITM | Input validation, HMAC, TLS |
| Repudiation | "I never deleted it" | Audit logs, signatures |
| Info disclosure | Stack traces, verbose API | Data classification, minimal exposure |
| Denial of service | Resource exhaustion, algorithmic complexity | Rate limits, quotas, circuit breakers |
| Elevation of privilege | IDOR, broken RBAC, JWT `alg=none` | Least privilege, server-side authz |

**Attack trees** (for systems with many vectors): root goal → AND/OR sub-goals →
leaf steps rated by cost/skill/detectability; prune infeasible branches, then map
the cheapest viable path against existing controls.

---

## Compliance frameworks

### GDPR (EU users)
Lawful basis required; consent freely given, specific, informed, withdrawable;
erasure within 30 days; data minimization; DPO for large-scale sensitive
processing; **breach notification to the authority within 72 hours**;
cross-border only under adequacy or SCCs.

### 152-FZ (Russian users/data)
**Data localization: personal data of Russian citizens must be stored on servers
in Russia.** Operator registers with Roskomnadzor, appoints a responsible person,
collects consent naming purpose, scope and retention. Cross-border transfer only
to countries on the Roskomnadzor adequacy list.

### LGPD (Brazilian users/data)
10 legal bases; **DPO (Encarregado) mandatory for every controller**; ANPD fines
up to 2% of revenue, capped at 50M BRL; rights include anonymization and
portability.

### SOC 2
Trust Service Criteria — Security required, plus Availability, Processing
Integrity, Confidentiality, Privacy as scoped. Evidence must be *continuous*
control monitoring over a 6-12 month window, not a point-in-time snapshot.

---

## Security headers

| Header | Recommended value | Purpose |
|---|---|---|
| Content-Security-Policy | `default-src 'self'; script-src 'self'` | XSS / injection |
| Strict-Transport-Security | `max-age=31536000; includeSubDomains; preload` | Force HTTPS |
| X-Frame-Options | `DENY` or `SAMEORIGIN` | Clickjacking |
| X-Content-Type-Options | `nosniff` | MIME sniffing |
| Referrer-Policy | `strict-origin-when-cross-origin` | Referrer leakage |
| Permissions-Policy | `camera=(), microphone=(), geolocation=()` | Browser features |
| X-XSS-Protection | `0` | Deprecated; CSP replaces it |
| Cache-Control | `no-store` on sensitive pages | Secrets in cache |

---

## Secrets detection patterns

```
# AWS
AKIA[0-9A-Z]{16}
aws_secret_access_key\s*=\s*[A-Za-z0-9/+=]{40}

# Google
AIza[0-9A-Za-z_-]{35}
[0-9]+-[0-9A-Za-z_]{32}\.apps\.googleusercontent\.com

# GitHub
gh[pousr]_[A-Za-z0-9_]{36,255}

# Generic tokens/passwords
(password|passwd|secret|token|api_key|apikey)\s*[:=]\s*['"][^\s'"]{8,}['"]

# Private keys
-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----

# JWT (never hardcode)
eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}

# Telegram bot token
[0-9]{8,10}:[A-Za-z0-9_-]{35}

# Anthropic
sk-ant-[A-Za-z0-9_-]{40,}

# OpenAI
sk-[A-Za-z0-9]{48,}
```

A hit in git history counts as leaked even if the current file is clean — the
finding is "rotate this credential", not "delete this line".
