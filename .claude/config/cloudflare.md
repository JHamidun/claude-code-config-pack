# Cloudflare

> Add your Cloudflare account details here.

## Account
- Account ID: YOUR_CLOUDFLARE_ACCOUNT_ID
- Email: YOUR_CLOUDFLARE_EMAIL

## Zones
| Domain | Zone ID | Registrar |
|--------|---------|-----------|
| your-domain.com | YOUR_CLOUDFLARE_ZONE_ID | Cloudflare |

## Tunnels (optional)
- Tunnel ID: YOUR_CLOUDFLARE_TUNNEL_ID
- Tunnel Name: your-tunnel-name

### Routes
| Hostname | Target |
|----------|--------|
| app.your-domain.com | your-service:3000 |

## API
Keys in `~/.claude/.credentials.master.env`:
- `CLOUDFLARE_GLOBAL_API_KEY`
- `CLOUDFLARE_EMAIL`
