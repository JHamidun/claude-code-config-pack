---
name: domain-dns-ops
description: Manage DNS records via Cloudflare API - list, add, update, delete records, check SSL, manage proxy. Use with /domain-dns-ops or "DNS", "домен".
---

# Domain & DNS Operations via Cloudflare

Manage DNS records and domain settings through Cloudflare API.

## Setup

API credentials from `~/.claude/.credentials.master.env`:
- `CLOUDFLARE_API_TOKEN` or `CLOUDFLARE_API_KEY` + `CLOUDFLARE_EMAIL`

See `~/.claude/config/cloudflare.md` for zone IDs and config.

## Operations

### List DNS Records
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" | python -m json.tool
```

### Add DNS Record
```bash
curl -s -X POST "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{
    "type": "A",
    "name": "subdomain.example.com",
    "content": "YOUR_PUBLIC_IP",
    "ttl": 1,
    "proxied": true
  }'
```

### Update DNS Record
```bash
curl -s -X PATCH "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" \
  --data '{"content": "YOUR_PUBLIC_IP"}'
```

### Delete DNS Record
```bash
curl -s -X DELETE "https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

### Check SSL Status
```bash
curl -s -X GET "https://api.cloudflare.com/client/v4/zones/{zone_id}/ssl/verification" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN"
```

## Common Record Types

| Type | Use Case | Example |
|------|----------|---------|
| A | IPv4 address | `YOUR_PUBLIC_IP` |
| AAAA | IPv6 address | `2001:db8::1` |
| CNAME | Alias | `other.example.com` |
| MX | Mail server | `mail.example.com` (priority 10) |
| TXT | Verification, SPF, DKIM | `v=spf1 include:...` |
| SRV | Service location | `_sip._tcp` |

## Process

1. User specifies domain operation
2. Load Cloudflare credentials from env
3. Identify zone ID for the domain
4. Execute API call
5. Verify the change
6. Report result

## Safety
- Always confirm before DELETE operations
- Show current state before UPDATE
- Verify DNS propagation after changes: `dig +short subdomain.example.com`
