# VPS SSH Hardening Playbook (any fresh server, not Hermes-specific)

> Goal: SSH key-only, fail2ban against bruteforce, ufw with only SSH open, password login off.
> Applies to ANY new VPS (aeza/Vultr/Hetzner, Ubuntu cloud images). Field-tested on Ubuntu 24.04.
> `claude-server-auth` skill is about Claude CLI tokens — different topic; this is the OS-level playbook.

**ORDER IS CRITICAL — disable the password LAST, only after a confirmed key login. Otherwise: lockout,
recoverable only via the provider's VNC/console.**

---

## 1. Operator key: reuse existing, generate only if none

Runs on the OPERATOR machine (never generate on the server — private key stays with the operator):

```bash
if [ -f ~/.ssh/id_ed25519.pub ]; then
  KEYFILE=~/.ssh/id_ed25519                 # ed25519 exists — use it
elif ls ~/.ssh/*.pub >/dev/null 2>&1; then
  KEYFILE=$(ls ~/.ssh/*.pub | head -1); KEYFILE=${KEYFILE%.pub}   # other key (id_rsa etc.) — use as-is
else
  ssh-keygen -t ed25519 -N "" -f ~/.ssh/id_ed25519               # nothing — generate
  KEYFILE=~/.ssh/id_ed25519
fi
cat "$KEYFILE.pub"        # this is OPERATOR_SSH_PUBKEY
```

**Never overwrite an existing operator key.** Windows: same logic in `%USERPROFILE%\.ssh\`.

Install on the server (over the current password session), idempotent:

```bash
mkdir -p /root/.ssh && chmod 700 /root/.ssh
touch /root/.ssh/authorized_keys && chmod 600 /root/.ssh/authorized_keys
grep -qF "<OPERATOR_SSH_PUBKEY>" /root/.ssh/authorized_keys || echo "<OPERATOR_SSH_PUBKEY>" >> /root/.ssh/authorized_keys
```

## 2. KEY_OK check BEFORE touching sshd (gotcha: skip this = lockout)

Separate session from the operator machine:

```bash
ssh -i "$KEYFILE" -o PreferredAuthentications=publickey -o PasswordAuthentication=no -o IdentitiesOnly=yes root@<VPS_IP> 'echo KEY_OK'
```

If the answer is not `KEY_OK` — **STOP**, debug the key (perms on `authorized_keys`, right pubkey,
right `$KEYFILE`). From here on all SSH goes by key (`-i "$KEYFILE"`), not password.

## 3. Firewall (ufw) — gotcha: allow SSH BEFORE enable, or you cut yourself off

```bash
ufw allow OpenSSH            # BEFORE enable — otherwise you sever your own session
ufw default deny incoming
ufw default allow outgoing
ufw --force enable           # --force skips the interactive prompt
ufw status verbose           # active, only 22/tcp allowed
```

Bots (Telegram polling) and model APIs are outbound — no extra inbound ports needed.

## 4. fail2ban

```bash
apt -y install fail2ban
cat > /etc/fail2ban/jail.local << 'EOF'
[sshd]
enabled = true
backend = systemd
maxretry = 5
findtime = 10m
bantime = 1h
EOF
systemctl enable --now fail2ban
fail2ban-client status sshd
```

`backend = systemd` is required on Ubuntu 24.04 (no auth.log by default — journald only).

## 5. Disable password login — gotcha: 50-cloud-init.conf overrides your sshd_config edit

On Ubuntu cloud images `PasswordAuthentication yes` sits in the drop-in
`/etc/ssh/sshd_config.d/50-cloud-init.conf` and overrides edits to the main `sshd_config`.
sshd takes the FIRST match, and drop-ins are read in LEXICOGRAPHIC order → ship a file with
prefix `00-` so it wins:

```bash
cat > /etc/ssh/sshd_config.d/00-hardening.conf << 'EOF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin prohibit-password
EOF
# defense-in-depth: neutralize the 'yes' in the cloud-init drop-in too
sed -i 's/^PasswordAuthentication yes/#&  # disabled by hardening playbook/' /etc/ssh/sshd_config.d/50-cloud-init.conf
sshd -t && systemctl restart ssh     # validate config FIRST, then restart
sshd -T | grep -Ei 'passwordauthentication|permitrootlogin'   # expect: passwordauthentication no
```

## 6. Re-verify (drive to green)

- Key login still works: `ssh -i "$KEYFILE" root@<VPS_IP> 'echo KEY_OK'` → `KEY_OK`
- Password rejected: `ssh -o PreferredAuthentications=password -o PubkeyAuthentication=no root@<VPS_IP>` → `Permission denied (publickey)`
- `ufw status` → active, SSH only; `fail2ban-client status sshd` → jail active
- Services on the box still respond (ufw does not break outbound)

## Re-entry after hardening

Password is off — connect by the SAME operator key used during setup
(`ssh -i ~/.ssh/id_ed25519 root@<VPS_IP>`). New operator? Append their pubkey to
`authorized_keys` from a working key session (step 1). Never re-enable password.

## Notes

- SSH port stays 22: key + fail2ban + ufw is sufficient; port change is optional obscurity.
- Root login stays `prohibit-password` here for the quick path; our prod canon is a dedicated
  non-root user + `PermitRootLogin no` once services run under that user.

## Lockout gotcha table

| Symptom | Cause / Fix |
|---------|-------------|
| **Locked out after hardening** | Password disabled before KEY_OK check. Never do step 5 before a successful step 2. Recovery: provider VNC/console only |
| Password won't turn off despite editing `sshd_config` | `PasswordAuthentication yes` lives in `50-cloud-init.conf` drop-in and wins → add `00-hardening.conf` (read first) + comment out the cloud-init line. Verify via `sshd -T \| grep passwordauth` |
| Cut own session at `ufw enable` | Enabled firewall without allowing SSH → always `ufw allow OpenSSH` BEFORE `ufw --force enable` |
| fail2ban jail inactive on Ubuntu 24.04 | Missing `backend = systemd` in jail.local |
