# Step 0: First-Run Setup Wizard

The full first-run configuration flow: modal flow for Claude Code, non-modal prose flow for other hosts, and the manual setup guide with every key and its scope.
**Read this only when `.last30days.env` (or the keychain entry) is missing, when a source reports `skipped-unconfigured`, or when the user asks to add/rotate a key.** On a configured machine skip it entirely.

## Contents

- Step 0: First-Run Setup Wizard
- Claude Code Modal Flow
- Non-Modal Prose Flow
- Manual Setup Guide

---

## Step 0: First-Run Setup Wizard

**CRITICAL: ALWAYS execute Step 0 BEFORE Step 1, even when the user provided a topic.** If the user typed `/last30days Mercer Island`, you MUST run the wizard BEFORE any research. The topic is preserved - research runs immediately after the wizard completes. Do NOT skip the wizard because a topic was provided. It takes about 30 seconds and only runs once, ever.

**You are the conversational driver.** The Python setup script does only mechanical work (cookie reads, tool installs, the GitHub device-auth flow) - it CANNOT prompt the user, because it runs as a non-interactive subprocess. So consent happens HERE, in chat: you ask, the user answers, and you gate each subprocess call on the answer. Do NOT just run `setup` and report the result - that is the silent-onboarding regression this section exists to prevent.

**First-run detection (silent, no commands, no output to user):**
- If `SETUP_COMPLETE=true` is available from process env, project config (`.claude/last30days.env`), global config (`~/.config/last30days/.env`), or the setup check reports configured credentials, skip Step 0 entirely and go to Step 1 (CRITICAL: Parse User Intent below). Do NOT announce that setup is complete. The user does not need a status message on every run.
- Do NOT treat the absence of `~/.config/last30days/.env` alone as a first run. Credentials may live in process env, project config, macOS Keychain (`last30days-<KEY>`), pass(1), or host-provided auth.
- If no setup marker or credential source is present, this is a first run.

**Named onboarding contracts:**
- *(2026-06-22, silent-wizard regression - Fredy Montero run):* a prior version said "Run `setup` ... follow the wizard's prompts end-to-end." But `run_auto_setup()` has NO prompts - it extracts cookies, installs yt-dlp + Digg, and writes `SETUP_COMPLETE` with zero interaction. The model ran the silent path, never asked cookie consent, never surfaced the macOS Full Disk Access fix, and never offered the ScraperVendor signup. Consent must be conversational.
- *(2026-06-22, NUX restoration):* the original v3.0.0 Claude Code wizard was a guided, modal-driven flow (welcome → Auto/Manual/Skip → cookie consent → ScraperVendor offer → source opt-in → first-topic picker) that eroded over time. It is restored below as the **Claude Code Modal Flow**. Do NOT collapse it back into a bare prose call - the guided modals are the feature. Reference capture: `docs/reference/old-nux-wizard-v3.0.0.md`.

**Platform split - run exactly ONE branch:**
- **If you HAVE WebSearch and AskUserQuestion (Claude Code):** run the **Claude Code Modal Flow** immediately below.
- **If you do NOT (OpenClaw, Codex, Cursor, Gemini CLI, raw CLI):** run the **Non-Modal Prose Flow** further down. It does the same work conversationally, without modals.

---

### Claude Code Modal Flow

**Follow these steps IN ORDER. Do NOT skip ahead to research. The sequence is: (1) welcome (built into the setup modal) → (2) setup modal → (3) run setup if chosen → (4) ScraperVendor offer modal → (5) source opt-in modal → (6) first-topic picker. Start at step 1.**

**Step 1 - Welcome.** The welcome pitch is delivered INSIDE the Step 2 setup modal, NOT as a separate message. Claude Code folds Bash/tool output behind "ctrl+o to expand", so a separate welcome message - or a `--welcome` command run - gets buried and the user never sees it. The AskUserQuestion modal is the only always-fully-visible surface, so the pitch lives in its question text. Do NOT run a separate `--welcome` command in this modal flow, and do NOT try to print the welcome as a chat message before the modal; go straight to Step 2. (The `--welcome` command still exists for the Non-Modal Prose Flow below, where there is no modal.)

**Step 2 - Welcome + setup choice (one modal).** Call AskUserQuestion with EXACTLY this question and these options. Reproduce the question verbatim, including the welcome pitch on the first lines:

Question:
"Welcome to /last30days! I research any topic across Reddit, X, YouTube, TikTok, Digg, arXiv, Techmeme, HN, Polymarket & more - pulling what people actually said in the last 30 days.

How would you like to set up?"

Options:
- "Auto setup (~30s)" - description: "Scan browser cookies for X + install yt-dlp (YouTube), Digg, arXiv, Techmeme. Reddit/HN/Polymarket/GitHub/Web work out of the box. Add TikTok + Instagram after via ScraperVendor (10k free calls)."
- "Manual setup" - description: "Show me each source and credential to configure by hand."
- "Skip for now" - description: "Just the free no-setup sources: Reddit (with comments), HN, Polymarket, GitHub, Web."

**Step 3 - Run setup based on the choice.**

**If the user picks Skip for now:** write `SETUP_COMPLETE=true` to `~/.config/last30days/.env` (append-only; run `mkdir -p ~/.config/last30days && touch ~/.config/last30days/.env` first if the file does not exist) so the wizard does NOT re-fire on every subsequent run, then skip straight to Step 6 (the topic picker). Do not run any `setup` command - the always-on sources (Reddit, HN, Polymarket, GitHub, Web) need no setup.

**If the user picks Auto setup:**

Get cookie consent first. Check if `BROWSER_CONSENT=true` already exists in `~/.config/last30days/.env`; if so, skip the consent prompt and run `setup --allow-browser-cookies` directly. Otherwise **call AskUserQuestion:**
Question: "Auto setup installs the free CLIs either way - yt-dlp (YouTube), Digg, arXiv, and Techmeme. The only thing that needs your OK is reading your browser's x.com cookies to authenticate X/Twitter search: I check Chrome first (a one-time macOS Keychain prompt may appear; click Always Allow), then Firefox and Safari. Cookies are read live, never saved to disk. Include X?"
Options (give each option the description shown):
- "Yes - X cookies + all CLIs" - description: "Read x.com cookies for X/Twitter search AND install yt-dlp (YouTube), Digg, arXiv, and Techmeme." Run `"${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup --allow-browser-cookies` (relative to the skill root). Append `BROWSER_CONSENT=true` to `.env` after setup completes.
- "Skip X - just the CLIs" - description: "No cookie reads. Still installs yt-dlp (YouTube), Digg, arXiv, and Techmeme." Run `FROM_BROWSER=off "${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup`.
- "xAI API key for X instead" - description: "Use an api.x.ai key for X search (no cookie read), plus install yt-dlp (YouTube), Digg, arXiv, and Techmeme." Ask them to paste it, write `XAI_API_KEY` to `.env`, then run `FROM_BROWSER=off "${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup`.

The consented `setup --allow-browser-cookies` run extracts cookies (Chrome/Chromium family first via the Keychain with no Full Disk Access, then Firefox and Safari as fallbacks; the winning browser is pinned for future runs only when it is Firefox or Safari, so Chrome never re-triggers the Keychain prompt on later runs) and best-effort installs yt-dlp (YouTube), the free keyless Digg CLI (`digg-pp-cli` via `@mvanhorn/printing-press-library install digg --cli-only`; Digg activates only when the binary is on the **agent subprocess PATH**, typically `$HOME/.local/bin`; setup reports honestly if installed off-PATH; recommend-only if `npx` is unavailable), plus the free keyless arXiv and Techmeme CLIs. Show the user what was found and installed - including whether Digg landed on PATH (active) or off-PATH (installed but not yet active).

**macOS Full Disk Access remediation (Safari fallback only).** Chrome and Firefox need no Full Disk Access; only the Safari fallback does. After the `setup` run, inspect its stderr. If it contains `Permission denied reading Cookies.binarycookies` and the platform is macOS, the OS blocked the Safari read - surface the fix instead of swallowing it: `macOS blocked the Safari cookie read. If your x.com login is in Chrome, you don't need this. To use Safari: System Settings > Privacy & Security > Full Disk Access > enable your terminal (or the Claude app), then I can retry.` Offer ONE retry of the `setup` command. If the user skips, continue.

**Step 4: ScraperVendor offer (every first run).** Show this as plain text, then a modal:

ScraperVendor adds TikTok and Instagram - posts AND top comments - plus YouTube comments, all on by default. 10,000 free calls, no credit card. Your key also auto-enriches Reddit (runs public + ScraperVendor merged for wider coverage) and backstops YouTube search if yt-dlp gets throttled. (We don't get a cut.) You can widen coverage even further in the next step.

Before the modal, run `which gh` via Bash silently; store as gh_available.

**Call AskUserQuestion:**
Question: "Want to add TikTok and Instagram? Your key also keeps Reddit and YouTube working when they hit rate limits. (We don't get a cut.)"
Options:
- "ScraperVendor via GitHub (recommended - most free calls)" - description: "Opens GitHub - we copy your code to your clipboard automatically, so you just paste it (Cmd+V), ~20-30s. Grants the full 10,000 free calls - more than the web signup." (Recommend this over the web option because the GitHub path grants more free calls.) This is a **two-command flow** - `--github-start` returns the code fast (foreground), then `--github-poll` waits for you to authorize. The code comes back in the command output, so it can't be missed:
   1. **Run `--github-start` in the FOREGROUND** (it returns in ~1-2s, it does NOT block-poll): `"${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup --github-start`. It submits the device flow, copies the code to the clipboard, opens the browser, and returns a JSON blob plus a plain `Your GitHub code: XXXX-XXXX` line on stdout.
      - If the returned `status == "already_registered"` (a key was already saved): tell the user "You're already set up - your existing ScraperVendor key is active" and STOP (do not run poll).
      - If `status == "error"`: show the message and offer the web option below.
   2. **SHOW THE CODE.** Read the `user_code` from the output and output ONE chat message: "Enter this code on the GitHub page: **XXXX-XXXX** - it's already on your clipboard, so just paste (Cmd+V) and click Continue." (If the output said the clipboard copy failed, tell them to type it instead.) The code is right there in step 1's output - surfacing it is the whole point.
   3. **Run `--github-poll`** (background with a 5-minute timeout, or foreground): `"${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup --github-poll`. Parse the **LAST** JSON line of its stdout for the final status:
      - `status == "success"`: the engine persisted the key (`"persisted": true`, MASKED `api_key` - never ask for or echo the raw key); confirm "You're in! 10,000 free calls. TikTok, Instagram, and the Reddit/YouTube backups are now active."
      - `status == "success"` but `"persisted": false` (key write failed): do NOT claim sources are active - tell the user signup worked but saving the key failed, and have them add `SCRAPER_API_KEY=<key>` to `~/.config/last30days/.env` manually.
      - `status == "error"` **with `message == "Authorized but failed to fetch API key"`**: GitHub authorized fine - do NOT say auth failed. This usually means your GitHub is **already linked** to a ScraperVendor account. Tell the user: "GitHub authorized, but I couldn't auto-grab your ScraperVendor key - your GitHub is probably already linked to an account. Get your key at your-scraper.example and paste it here, or Skip." Then accept a pasted key (write `SCRAPER_API_KEY` to `.env`) or offer the web/skip options.
      - `status == "timeout"`, or any other `status == "error"` message: show "GitHub auth didn't complete - no worries, sign up at your-scraper.example or try again later," then offer the web option below.
   - **One-shot fallback:** hosts that prefer a single call can still run `setup --github` (foreground), which chains start+poll; tell the user first that a code will appear on their clipboard to paste.
- "Open your-scraper.example (Google sign-in)" - run `open https://your-scraper.example` via Bash, then ask them to paste the API key. Write `SCRAPER_API_KEY={key}` to `~/.config/last30days/.env`.
- "I have a key" - accept the key, write to `.env`.
- "Skip for now" - proceed without ScraperVendor. No TikTok/Instagram, and no ScraperVendor backup if Reddit or YouTube get rate-limited (your free sources still work).

**Step 5: Source opt-in (only if a ScraperVendor key was saved, not if skipped).** Comments are the DEFAULT, never an opt-in - there is no posts-only tier. Plain text then modal:

Your key is set. On by default: TikTok + Instagram (posts AND top comments), YouTube comments, and Reddit auto-enrichment (public + ScraperVendor). Want the widest net?

**Call AskUserQuestion:**
Question: "Which ScraperVendor sources?"
Options:
- "TikTok + Instagram + all comments (recommended)" - the default: posts AND top comments (ranked by votes) for TikTok + Instagram, plus YouTube comments. Reddit is auto-enriched too. Append `INCLUDE_SOURCES=tiktok,instagram,youtube_comments,tiktok_comments,instagram_comments` to `~/.config/last30days/.env` (the list must include `tiktok,instagram` so they are not treated as excluded). Confirm: "TikTok, Instagram, and top YouTube/TikTok/Instagram comments are on, plus Reddit auto-enrichment."
- "Everything (also Threads + Pinterest)" - everything above plus Threads and Pinterest searches. Most coverage, most credits. Append `INCLUDE_SOURCES=tiktok,instagram,youtube_comments,tiktok_comments,instagram_comments,threads,pinterest`. Confirm: "Everything's on: posts + comments for TikTok/Instagram/YouTube, plus Threads and Pinterest."

**Step 6: First-topic picker.** Once `SETUP_COMPLETE=true` is written, **call AskUserQuestion:**
Question: "What do you want to research first?"
Options:
- "Claude Code vs Codex" - tech comparison
- "Sam Altman" - person in the news
- "Warriors Basketball" - sports
- "AI Legal Prompting Techniques" - niche/professional
- "Type my own topic"

If the user picks an example, run research with it. If "Type my own", ask what they want. **If the user already supplied a topic with the command (e.g. `/last30days Mercer Island`), SKIP this picker and use their topic directly.**

**END OF FIRST-RUN WIZARD.** Everything in the Modal Flow ONLY runs on first run. If `SETUP_COMPLETE=true` exists, skip ALL of it - no welcome, no modals, no topic picker - and go straight to research (Parse User Intent).

**If the user picked Manual setup** at Step 2, follow the **Manual Setup Guide** below instead of the Auto branch (the guide writes `SETUP_COMPLETE=true` itself), then continue to Step 6.

---

### Non-Modal Prose Flow

For hosts without interactive modal prompts (OpenClaw, Codex, Cursor, Gemini CLI, raw CLI). Same work, done conversationally. Run in order; wait where it says to wait.

**1. Welcome.** Run `"${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py --welcome` and show its stdout to the user VERBATIM (do not summarize or reformat). The welcome is engine-owned so it renders the same everywhere.

**2. Permission preflight.** Run `"${LAST30DAYS_PYTHON:-python3}" "${SKILL_DIR}/scripts/last30days.py" --preflight` using the directory of the `SKILL.md` you loaded, then summarize the human-readable result before setup: config source, project config trust/ignore state, planned browser-cookie mode, planned writes, optional commands, and active/ignored endpoint overrides. This is safe: it does not read browser-cookie values, does not write setup/config/report files, and does not run research. For Codex desktop and other folder-mode hosts, if hidden `.claude/last30days.env` project config is shown as ignored, tell the user it remains ignored unless `LAST30DAYS_TRUST_PROJECT_CONFIG=1` is set from the process environment or global config. Do not block normal research on missing optional commands; describe them as optional coverage.

**3. Cookie consent (ask BEFORE reading anything).** First check if `BROWSER_CONSENT=true` already exists in `~/.config/last30days/.env` (e.g. granted in a prior Claude Code session); if so, skip this prompt and run `setup --allow-browser-cookies` directly. Otherwise ask. Example: `I can read your browser cookies to unlock X/Twitter and other logged-in sources - I check Chrome first (a one-time macOS Keychain prompt may appear; click Always Allow), then Firefox and Safari. Want me to? (yes / no)` **Wait for the answer.**
   - On **yes** → run `"${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup --allow-browser-cookies` (and append `BROWSER_CONSENT=true` to `.env` after it completes). Extracts cookies (Chrome/Chromium family first via the Keychain with no Full Disk Access, then Firefox and Safari; only a Firefox/Safari winner is pinned for later runs, so Chrome never re-prompts) and best-effort installs yt-dlp (YouTube), the free keyless Digg CLI (`digg-pp-cli` via `@mvanhorn/printing-press-library install digg --cli-only`; activates only when on the agent subprocess PATH, typically `$HOME/.local/bin`; reports honestly if off-PATH; recommend-only if `npx` is unavailable), plus the free keyless arXiv and Techmeme CLIs.
   - On **no** → run `FROM_BROWSER=off "${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup`. Skips all cookie reads; still installs yt-dlp (YouTube), Digg, arXiv, and Techmeme, still writes `SETUP_COMPLETE`.

**4. Full Disk Access remediation (macOS only).** After `setup`, inspect stderr. If it contains `Permission denied reading Cookies.binarycookies` on macOS, surface: `macOS blocked the cookie read. To enable X/Twitter: System Settings > Privacy & Security > Full Disk Access > enable your terminal (or the Claude app), then I can retry.` Offer ONE retry. If skipped, continue.

**5. ScraperVendor signup offer (every first run, consent BEFORE launching the browser).** Explain it grants 10,000 free calls that add TikTok and Instagram, plus a backup that keeps Reddit and YouTube working when they hit rate limits (a Reddit backup and a YouTube transcript fallback), that GitHub signup grants the full 10,000 free calls (more than the web form), and that it opens a GitHub authorization page where you enter a short code. Ask, e.g.: `Want to unlock TikTok, Instagram, and more? I can sign you up for ScraperVendor with GitHub (10,000 free calls, ~20-30s) - it opens a browser and you enter a short code. (yes / no)` **Wait for the answer.**
   - On **yes** → two commands. FIRST run `"${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup --github-start` in the FOREGROUND - it returns in ~1-2s with a `Your GitHub code: XXXX-XXXX` line plus a JSON blob, copies the code to the clipboard, and opens the browser. Read the `user_code` from that output and immediately tell the user: the code, that it's on their clipboard so they can just paste it (Cmd+V) on the GitHub page - do not make them hunt for it. (If `status == "already_registered"`, stop here - their existing key is active. If the output said the clipboard copy failed, tell them to type the code.) THEN run `"${LAST30DAYS_PYTHON:-python3}" skills/last30days/scripts/last30days.py setup --github-poll` (background with a 5-min timeout, or foreground) and parse the **LAST** JSON line of its stdout for the final status. On success the engine persists the key automatically and returns `"persisted": true` with a MASKED `api_key` (never ask for or echo the raw key). Confirm the paid sources are active.
   - On **success but `"persisted": false`** (auth completed yet the key write failed) → do NOT claim sources are active. Tell the user signup worked but saving failed, and have them add `SCRAPER_API_KEY=<key>` to `~/.config/last30days/.env` manually (the raw key is masked in output, so re-run `setup --github` or retrieve it from your-scraper.example to get the value).
   - On **`status == "error"` with `message == "Authorized but failed to fetch API key"`** → GitHub authorized fine, so do NOT say auth failed. This usually means the GitHub account is already linked to a ScraperVendor account. Tell the user: "GitHub authorized, but I couldn't auto-grab your ScraperVendor key - your GitHub is probably already linked to an account. Get your key at your-scraper.example and paste it, or Skip." Accept a pasted key or offer web/skip.
   - On **timeout, or any other error** → tell the user it didn't complete and offer to retry or the web signup at your-scraper.example.
   - On **no** → note they can run it later by asking to set up ScraperVendor, then continue.

**5b. Source tier (only if a key was saved).** Comments are the default, never opt-in. Your key runs TikTok + Instagram posts AND top comments, YouTube comments, and Reddit auto-enrichment. Ask whether they want the widest net, e.g.: `Recommended is TikTok + Instagram + all comments (posts and top comments for TikTok/Instagram plus YouTube comments). Or Everything - also Threads + Pinterest (more credits). (recommended / everything)` **Wait for the answer.**
   - On **recommended** → append `INCLUDE_SOURCES=tiktok,instagram,youtube_comments,tiktok_comments,instagram_comments` to `~/.config/last30days/.env` (include `tiktok,instagram` so they are not treated as excluded). Confirm posts + top comments for TikTok/Instagram/YouTube are on, plus Reddit auto-enrichment.
   - On **everything** → append `INCLUDE_SOURCES=tiktok,instagram,youtube_comments,tiktok_comments,instagram_comments,threads,pinterest`. Confirm Threads and Pinterest are on too.

**6. Complete.** Once `SETUP_COMPLETE=true` is written, briefly confirm which sources are now active (read the `setup --github` JSON `persisted` field, re-run `--preflight` for a human permission summary, or re-run safe `--diagnose` for JSON) and proceed to research. For Codex desktop, Cursor, Gemini CLI, and raw folder-mode hosts, hidden `.claude/last30days.env` project config is ignored unless `LAST30DAYS_TRUST_PROJECT_CONFIG=1` is set from the process environment or global config; only report a project file as active when diagnose reports it as the config source.

---

### Manual Setup Guide

Shown when a Claude Code user picks "Manual setup", or for anyone who wants to configure by hand. Present as plain text (not blockquoted).

The magic of /last30days is Reddit comments + X posts together - and both are free. Add these to `~/.config/last30days/.env`:

**X/Twitter (pick one - the most important source):**
- `FROM_BROWSER=auto` - free. Reads your x.com login cookies live at search time (Firefox/Safari, never saved to disk).
- `XAI_API_KEY=xxx` - no browser access needed. Get a key at api.x.ai. Best for servers.
- `XQUIK_API_KEY=xxx` - keyless-style X via Xquik.
- `AUTH_TOKEN=xxx` + `CT0=xxx` - paste your X cookies manually (x.com → F12 → Application → Cookies).

**Reddit (free, works out of the box):**
- Public JSON gives threads + top comments with upvote counts. No setup required.
- `SCRAPER_API_KEY=xxx` - optional backup if public Reddit gets rate-limited.

**YouTube (free, open source):**
- Run `brew install yt-dlp` (or `pip install yt-dlp`) - enables YouTube search + transcripts.
- `SCRAPER_API_KEY=xxx` - optional server-side transcript fallback, used only when yt-dlp is rate-limited/bot-gated.

**Digg (free, keyless):**
- Run `npx @mvanhorn/printing-press-library install digg --cli-only` - installs the Digg CLI for trending news, GitHub stars, and pipeline feeds. Activates when `digg-pp-cli` is on your PATH (typically `$HOME/.local/bin`).

**GitHub Issues/PRs (free, no key needed):**
- If the `gh` CLI is installed and authed (`brew install gh && gh auth login`), GitHub search is automatic. No API key required.

**Bonus: TikTok, Instagram, YouTube comments (ScraperVendor):**
- `SCRAPER_API_KEY=xxx` - 10,000 free calls at your-scraper.example.
- After adding your key, set `INCLUDE_SOURCES=tiktok,instagram` to turn on the popular ones. (Threads, Pinterest, and LinkedIn are also available via `INCLUDE_SOURCES=threads,pinterest,linkedin` for power users.)

**Other optional sources (add anytime):**
- `PERPLEXITY_API_KEY=xxx` (or `OPENROUTER_API_KEY=xxx`) - AI-synthesized research with citations; set `INCLUDE_SOURCES=perplexity`.
- `XIAOHONGSHU_API_BASE=http://localhost:18060` - Xiaohongshu/RED via a logged-in x-mcp browser plugin or `xiaohongshu-mcp` service; optional unless the local service runs on a custom URL. Opt in per run with `--search xhs`, or persistently via `INCLUDE_SOURCES=xiaohongshu`.
- DripStack (premium financial newsletter search) is opt-in only: per run with `--search dripstack`, or persistently via `INCLUDE_SOURCES=dripstack`. Free public search API, no key; never active without the opt-in.
- `BSKY_HANDLE=you.bsky.social` + `BSKY_APP_PASSWORD=xxx` - Bluesky (free app password).
- `BRAVE_API_KEY=xxx` or `EXA_API_KEY=xxx` - web search backends.

**CRITICAL: NEVER overwrite an existing `.env`.** Before writing ANY key:
1. Check if the file exists: `test -f ~/.config/last30days/.env`
2. If it exists, READ it, then APPEND only missing keys with `>>` (double redirect).
3. NEVER use `>` (single redirect) - it destroys existing content.
4. If it doesn't exist: `mkdir -p ~/.config/last30days && touch ~/.config/last30days/.env`

Always add this last line: `SETUP_COMPLETE=true`. Then proceed to research.

The setup wizard's mechanical work lives in a Python module so it runs across all hosts (Claude Code, Codex, Cursor, etc.) while you drive the consent conversation above. The common-case (already set up) path through this file stays short.

---


