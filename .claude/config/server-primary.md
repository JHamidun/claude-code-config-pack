# Primary Server

> Add your primary server details here.

## Specs
- IP: YOUR_SERVER_IP
- Hostname: your-server
- Specs: X vCPU, X GB RAM, X GB SSD
- User: deploy (sudo)

## Installed
- Docker, Node.js, Nginx, PostgreSQL, Redis, Python

## SSH
```bash
ssh your-server
```

## SSH Config
```
Host your-server
    HostName YOUR_SERVER_IP
    User deploy
    IdentityFile ~/.ssh/your_key
```
