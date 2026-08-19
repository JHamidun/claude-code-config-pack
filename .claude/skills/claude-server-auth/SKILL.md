---
name: claude-server-auth
description: "Authenticate Claude CLI on a headless server: subscription setup-token via tmux + local Playwright OAuth. Trigger: «authorize claude on server»."
---

# Claude Server Auth

Authenticate Claude CLI on headless servers (no GUI browser) using `setup-token` in tmux + local Playwright for OAuth.

## When to Use

- Need to auth Claude CLI on a remote server via SSH
- Setting up `CLAUDE_CODE_OAUTH_TOKEN` for subscription-based usage
- Adding new accounts to token rotation
- Re-authenticating expired tokens (tokens live ~1 year)

## Prerequisites

- SSH access to server (`ssh your-server`)
- Claude CLI installed on server (`npm i -g @anthropic-ai/claude-code`)
- tmux on server
- Playwright available locally (Claude Code's built-in MCP Playwright)
- Google account credentials for the Claude subscription account

## Architecture

```
Local PC                          Remote Server (headless)
-----------                       -------------------------
Playwright browser  <-- URL ---   tmux: claude setup-token
    |                                    |
    v                                    |
Google OAuth login                       |
    |                                    |
    v                                    |
Claude "Authorize"                       |
    |                                    |
    v                                    v
callback URL ---- code --------> tmux paste-buffer
    (code#state)                         |
                                         v
                                  stdout: sk-ant-oat01-...
```

## Step-by-Step Process

### 1. Create account directory and start setup-token

```bash
ACCOUNT="account-1"
SESSION="auth1"
ssh your-server "mkdir -p /root/.claude-accounts/  # rename to your convention$ACCOUNT"
ssh your-server "tmux kill-session -t $SESSION 2>/dev/null; \
  rm -f /tmp/${SESSION}-output.txt; \
  tmux new-session -d -s $SESSION -x 400 -y 30 \
  'CLAUDE_CONFIG_DIR=/root/.claude-accounts/  # rename to your convention$ACCOUNT claude setup-token'"
```

Key flags:
- `-x 400` wide terminal prevents URL line-wrapping
- `-d` detached so SSH doesn't need to hold TTY
- `CLAUDE_CONFIG_DIR` isolates auth per account
- Always kill previous session first to avoid conflicts

### 2. Set up output capture and get URL

```bash
sleep 4
ssh your-server "tmux pipe-pane -t $SESSION 'cat >> /tmp/${SESSION}-output.txt'"
ssh your-server "tmux capture-pane -t $SESSION -p -S -50"
```

**IMPORTANT:** Set up `pipe-pane` BEFORE pasting the code. This captures output even if the tmux session exits (setup-token exits immediately after printing the token).

Look for URL like:
```
https://claude.ai/oauth/authorize?code=true&client_id=...&state=...
```

If URL is truncated, use `-S -100` for more scrollback.

### 3. Open URL in local Playwright

```
browser_navigate to the captured URL
```

Wait 3-4 seconds for the page to load, then take a snapshot.

### 4. Handle Google Authentication

Three possible scenarios after opening the URL:

**A) "Authorize" button visible with correct account** — Skip to step 5.

**B) "Authorize" button visible with WRONG account** — Click "Switch account" link at the bottom to log out and re-enter with the correct account.

**C) Login page** — Need Google OAuth:

1. Click "Continue with Google"
2. Switch to the new Google accounts tab (tab index 1)
3. If the needed account is in the list — click it
4. If NOT in the list — click "Use another account", enter email, then password
5. **2FA may appear** (e.g., "Check your phone") — either:
   - Wait for the user to approve on their device, OR
   - Click "Another way" to try backup codes
6. Google consent page ("Повторный вход") — click "Continue/Продолжить"
7. Page redirects back to Claude "Authorize" page — proceed to step 5

### 5. Click "Authorize" — handle the double-click issue

**KNOWN BUG:** The first click on "Authorize" often fails silently (returns a 403 on the server-side authorize endpoint). The page stays the same.

**Fix:** Wait 3-5 seconds, check if the page still shows "Authorize". If yes, click again. The second click typically works.

```
# Click Authorize
browser_click "Authorize" ref=...

# Wait and check
browser_wait_for time=3
browser_snapshot

# If still on authorize page — click again
browser_click "Authorize" ref=...
```

### 6. Extract auth code

After successful Authorize click, the page redirects to:
```
https://platform.claude.com/oauth/code/callback?code=XXXX&state=YYYY
```

The page shows "Authentication Code" with the full code displayed as:
```
XXXX#YYYY
```

**The code is shown directly on the page** — no need to parse the URL. Copy the full value from the page element (ref `e19` in snapshot typically).

**IMPORTANT:** The `#` between code and state is literal, not a URL fragment.

### 7. Paste code into tmux

**DO NOT use `tmux send-keys`** — the `#` character breaks it even with `-l` flag.

Use load-buffer + paste-buffer:

```bash
ssh your-server "tmux load-buffer - <<'EOF'
THE_CODE#THE_STATE
EOF"
ssh your-server "tmux paste-buffer -t $SESSION && sleep 1 && tmux send-keys -t $SESSION Enter"
```

**NOTE:** Use `<<'EOF'` (quoted) to prevent shell interpretation of special characters in the code.

### 8. Capture the token

Wait 5-6 seconds for token generation:

```bash
sleep 5
ssh your-server "tmux capture-pane -t $SESSION -p -S -100 2>/dev/null || cat /tmp/${SESSION}-output.txt"
```

Token appears in the output as: `sk-ant-oat01-` followed by ~80+ characters.

The output contains ANSI escape codes — extract the token by looking for `sk-ant-oat01-` pattern.

If tmux session already exited, the `pipe-pane` fallback (`/tmp/${SESSION}-output.txt`) will have the output.

### 9. Handle OAuth 500 errors

**KNOWN ISSUE:** `setup-token` frequently returns "OAuth error: Request failed with status code 500" — this is an intermittent server-side error from Anthropic.

**Fix:** The CLI shows "Press Enter to retry". Two approaches:

**A) Retry in-place** (if the session is still alive):
```bash
ssh your-server "tmux send-keys -t $SESSION Enter"
# Wait for new URL
sleep 5
ssh your-server "tmux capture-pane -t $SESSION -p -S -50"
# Get new URL, repeat from step 3
```

**B) Full restart** (cleaner, recommended after 2+ failures):
```bash
ssh your-server "tmux kill-session -t $SESSION 2>/dev/null; \
  rm -f /tmp/${SESSION}-output.txt; \
  tmux new-session -d -s $SESSION -x 400 -y 30 \
  'CLAUDE_CONFIG_DIR=/root/.claude-accounts/  # rename to your convention$ACCOUNT claude setup-token'"
# Re-setup pipe-pane and repeat from step 2
```

**The 500 error is random and may happen 1-3 times before succeeding.** Account-1 took 2 attempts, account-2 took 2 attempts, account-3 took 4 attempts. Don't give up.

**NOTE:** Each retry generates a new `code_challenge` and `state`. The browser must re-authorize with the new URL — old codes won't work with a new challenge.

### 10. Save and verify token

```bash
ssh your-server "echo 'sk-ant-oat01-...' > /root/.claude-accounts/  # rename to your convention$ACCOUNT/token.txt"
ssh your-server "chmod 600 /root/.claude-accounts/  # rename to your convention$ACCOUNT/token.txt"

# Verify — use single quotes for SSH to avoid local shell expansion
ssh your-server 'CLAUDE_CODE_OAUTH_TOKEN=$(cat /root/.claude-accounts/  # rename to your conventionACCOUNT/token.txt) claude -p --model claude-haiku-4-5-20251001 --output-format text "respond with just OK"'
# Expected: OK
```

**IMPORTANT:** Use single quotes around the SSH command to prevent local `$()` expansion. With double quotes, the subshell runs locally and fails.

### 11. Cleanup

```bash
ssh your-server "tmux kill-session -t $SESSION 2>/dev/null; rm -f /tmp/${SESSION}-output.txt"
```

## Switching Accounts in Playwright

When authenticating multiple accounts sequentially, the browser stays logged into the previous Claude account.

**To switch accounts:**
1. On the "Authorize" page, click "Switch account" link
2. This logs out and shows the Claude login page
3. Click "Continue with Google"
4. Switch to Google accounts tab (tab index 1)
5. Select the correct Google account from the list
6. If account has 2FA — handle it (approve on device or use another method)
7. Google consent → "Continue/Продолжить"
8. Back to Claude "Authorize" page with the correct account

**TIP:** After switching, always verify "Logged in as X@gmail.com" at the bottom of the Authorize page before clicking.

## Token Rotation Setup

Rotation script at `/root/.claude-accounts/  # rename to your conventiontoken-rotator.sh`:

```bash
token-rotator.sh status     # show all accounts and which is active
token-rotator.sh get        # get current token (no rotation)
token-rotator.sh rotate     # switch to next account
token-rotator.sh validate   # test current token with haiku
token-rotator.sh get-valid  # get token with auto-failover (tries up to 3)
token-rotator.sh init       # re-scan account directories
```

Usage in projects:
```bash
export CLAUDE_CODE_OAUTH_TOKEN=$(bash /root/.claude-accounts/  # rename to your conventiontoken-rotator.sh get-valid)
claude -p "your prompt"
```

Auto-failover logic: `get-valid` tries current token → if error → rotates → tries next → up to 3 attempts.

## OpenClaw Integration

Update `auth-profiles.json` with all subscription tokens:

```json
{
  "version": 1,
  "profiles": {
    "anthropic:subscription-1": {
      "type": "token",
      "provider": "anthropic",
      "token": "sk-ant-oat01-..."
    },
    "anthropic:subscription-2": {
      "type": "token",
      "provider": "anthropic",
      "token": "sk-ant-oat01-..."
    },
    "anthropic:subscription-3": {
      "type": "token",
      "provider": "anthropic",
      "token": "sk-ant-oat01-..."
    }
  },
  "order": {
    "anthropic": [
      "anthropic:subscription-1",
      "anthropic:subscription-2",
      "anthropic:subscription-3"
    ]
  },
  "lastGood": {
    "anthropic": "anthropic:subscription-1"
  }
}
```

Path: `/var/lib/docker/volumes/your-config-volume/_data/agents/main/agent/auth-profiles.json`

**IMPORTANT:** Set ownership `chown 1000:1000` (node user inside container).

After updating, restart gateway:
```bash
cd ~/your-gateway && docker compose -f docker-compose.hardened.yml restart your-gateway
```

OpenClaw failover: tries tokens in `order` sequence. If first token hits rate limit, automatically tries the next.

## Common Mistakes

| Mistake | Why it fails | Fix |
|---------|-------------|-----|
| `tmux send-keys -l "code#state"` | `#` interpreted as window ref | Use `load-buffer` + `paste-buffer` |
| `claude setup-token \| tee log` | Pipe breaks Ink TUI raw mode | Use `tmux pipe-pane` for capture |
| `claude auth login` for paste flow | `auth login` uses polling, no paste prompt | Use `setup-token` instead |
| Running Playwright on server | Cloudflare blocks headless browsers on claude.ai | Run Playwright locally |
| Expecting `.credentials.json` | `setup-token` outputs to stdout only | Capture from tmux output |
| Narrow tmux window | URL gets line-wrapped and truncated | Use `-x 400` |
| `ssh your-server "claude setup-token"` | No TTY for Ink TUI | Must use tmux |
| `ssh your-server "OAUTH=\$(cat ...)"` | `$()` expands locally, not on server | Use single-quoted SSH: `ssh your-server '...'` |
| Clicking Authorize only once | First click often fails silently (403) | Wait 3s, check page, click again if needed |
| Reusing code after 500 error | Each retry generates new code_challenge | Must re-authorize in browser with new URL |
| Not setting up pipe-pane early | Token output lost if tmux exits | Set pipe-pane right after session creation |
| Forgetting `chown 1000:1000` | OpenClaw container can't read profiles | Always chown after writing auth-profiles.json |

## Red Flags

- Using `auth login` instead of `setup-token` (different flow, no paste prompt)
- Trying to pipe or redirect setup-token stdin/stdout (breaks Ink)
- Attempting headless auth directly on server (Cloudflare blocks it)
- Hardcoding tokens in scripts instead of reading from token.txt
- Not setting `CLAUDE_CONFIG_DIR` when managing multiple accounts (overwrites single config)
- Giving up after first 500 error (it's intermittent, keep retrying)
- Using old auth code after setup-token retry (new challenge = need new code)

## Checklist

- [ ] Created account directory on server
- [ ] Started `setup-token` in tmux with `-x 400` wide terminal
- [ ] Set up `tmux pipe-pane` for output capture
- [ ] Captured OAuth URL from tmux output
- [ ] Opened URL in local Playwright
- [ ] Verified correct account at bottom of Authorize page
- [ ] Clicked Authorize (twice if first click fails silently)
- [ ] Got `code#state` from callback page
- [ ] Pasted code via `load-buffer` + `paste-buffer` (NOT send-keys)
- [ ] Handled 500 errors by retrying with fresh URL
- [ ] Captured `sk-ant-oat01-...` token from output
- [ ] Saved to token.txt with `chmod 600`
- [ ] Verified token works with `'...'` single-quoted SSH command
- [ ] Cleaned up tmux session and temp files
- [ ] Updated rotation script (`token-rotator.sh init`)
- [ ] Updated OpenClaw auth-profiles.json with `chown 1000:1000`
- [ ] Restarted OpenClaw gateway
