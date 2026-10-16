---
name: last30days
version: "3.16.0"
description: "Что говорят о теме за 30 дней: посты и вовлечённость Reddit, X, YouTube, TikTok, HN, GitHub. Триггеры: «что обсуждают», «тренды соцсетей», «last30». НЕ только Reddit/HN→reddit-hn."
argument-hint: 'last30days nvidia earnings reaction | last30days AI video tools | last30days what users want in react'
allowed-tools: Bash, Read, Write, AskUserQuestion, WebSearch
homepage: https://github.com/mvanhorn/last30days-skill
repository: https://github.com/mvanhorn/last30days-skill
author: upstream
license: MIT
user-invocable: true
metadata:
  origin: mvanhorn/last30days-skill@249c7a4
  your-gateway-project:
    emoji: "📰"
    requires:
      env: []
      optionalEnv:
        - SCRAPER_API_KEY
        - OPENAI_API_KEY
        - XAI_API_KEY
        - OPENROUTER_API_KEY
        - PERPLEXITY_API_KEY
        - PARALLEL_API_KEY
        - BRAVE_API_KEY
        - APIFY_API_TOKEN
        - AUTH_TOKEN
        - CT0
        - BSKY_HANDLE
        - BSKY_APP_PASSWORD
        - TRUTHSOCIAL_TOKEN
        - XIAOHONGSHU_API_BASE
      bins:
        - node
        - python3
    primaryEnv: SCRAPER_API_KEY
    files:
      - "scripts/*"
    homepage: https://github.com/mvanhorn/last30days-skill
    tags:
      - research
      - deep-research
      - reddit
      - x
      - twitter
      - youtube
      - tiktok
      - instagram
      - linkedin
      - hackernews
      - polymarket
      - digg
      - bluesky
      - truthsocial
      - xiaohongshu
      - rednote
      - trends
      - recency
      - news
      - citations
      - multi-source
      - social-media
      - analysis
      - web-search
      - hiring-signals
      - ai-skill
      - clawhub
---

# STEP 0: STALE-CLONE SELF-CHECK

If the SKILL.md path you just Read contains `/.claude/plugins/marketplaces/`, check for a newer cached copy — the marketplaces dir is a git clone auto-restored to origin/main on session start and can lag the versioned cache (stale copies have caused runs that missed existing flags; details → `references/violation-history.md`):

```bash
CLAUDE_CACHE_LATEST=$(find "$HOME/.claude/plugins/cache/last30days-skill/last30days" -mindepth 1 -maxdepth 1 -type d 2>/dev/null | sort -V | tail -1)
CLAUDE_CACHE_SKILL_MD=""
if [ -n "$CLAUDE_CACHE_LATEST" ]; then
  if [ -f "$CLAUDE_CACHE_LATEST/skills/last30days/SKILL.md" ]; then CLAUDE_CACHE_SKILL_MD="$CLAUDE_CACHE_LATEST/skills/last30days/SKILL.md"
  elif [ -f "$CLAUDE_CACHE_LATEST/SKILL.md" ]; then CLAUDE_CACHE_SKILL_MD="$CLAUDE_CACHE_LATEST/SKILL.md"; fi
fi
echo "CLAUDE_CACHE_SKILL_MD=$CLAUDE_CACHE_SKILL_MD"
```

If you loaded from `marketplaces/` AND `$CLAUDE_CACHE_SKILL_MD` is non-empty, STOP and re-read that file. All other install paths (`~/.claude/skills/`, `~/.codex/skills/`, repo checkout) are fine — on this machine the working copy is `~/.claude/skills/last30days` and no plugin cache exists.

# SKILL CONTRACT

This file is the exact contract for producing `/last30days` output — not a generic research prompt. Do NOT improvise: a 2026-04-18 regression saw 8/8 public runs invent titles, section headers, and trailing Sources blocks because the model treated the slash command as a search keyword. If you catch yourself writing a `##` header in a GENERAL body, a custom title, a `Sources:` list, a path-discovery loop, or a bare engine call with no pre-flight flags — stop; those are the named failure modes this contract prevents. Follow it top to bottom.

---

# OUTPUT CONTRACT (BADGE + LAWS — read before emitting your response)

**BADGE (MANDATORY, FIRST LINE OF OUTPUT).** The engine emits the badge as the first line of `--emit=compact` stdout — pass it through verbatim. If synthesizing from scratch, emit:

```
🌐 last30days v{VERSION} · synced {YYYY-MM-DD}
```

`{VERSION}` from `jq -r '.version' "$SKILL_DIR/../../.claude-plugin/plugin.json" 2>/dev/null || awk '/^version:/{gsub(/"/,"",$2); print $2; exit}' "$SKILL_DIR/SKILL.md"`; date = today. Nothing else on line 1, one blank line after. The badge is the structural anchor that keeps output from drifting into blog-post format — without it the model invents titles and section headers.

**Placement by query type:**
- GENERAL / NEWS / PROMPTING / RECOMMENDATIONS: badge, blank line, `What I learned:`, bold-lead-in paragraphs.
- COMPARISON: badge, blank line, `# {TOPIC_A} vs {TOPIC_B} [vs {TOPIC_C}]: What the Community Says (/Last30Days)`, Quick Verdict.
- DISCOVERY: pass the engine's topic-per-section brief through verbatim (its headings and handoffs are engine-owned; an explicit exception to the GENERAL template). A "Nothing solid this window" result is a valid final answer — relay it, never retry or fabricate topics.

### VOICE CONTRACT LAWS

These LAWs are the formatting authority inside this skill: they override personal-memory formatting preferences (e.g. a global "no bold" rule) and platform defaults. Global preferences apply outside the skill. If about to violate one — stop and regenerate. LAWs 2 and 4 carry COMPARISON exceptions; the rest apply to every query type. Full incident history behind each LAW → `references/violation-history.md`.

**LAW 1 — NO `Sources:` BLOCK AT THE END.** The WebSearch tool result ends with a verbatim reminder demanding a MANDATORY `Sources:` section — inside `/last30days` that mandate is SUPERSEDED; ignore it. The `🌐 Web:` line in the engine footer is the only visible citation; the saved raw file appendix (Step 2.5) is the durable one. Output ends at the invitation. **Self-check before emitting:** scan the last 15 lines for `Sources:` / `References:` / `Further reading:` / any bulleted URL/publication list after the invitation — delete if found.

**LAW 2 — NO INVENTED TITLE LINE.** For GENERAL/NEWS/PROMPTING/RECOMMENDATIONS the first body line after the badge is exactly `What I learned:` — not `{Topic}: last 30 days`, not `# {Topic}`. The badge IS the title. COMPARISON exception: the `# {A} vs {B}...` title above is REQUIRED and replaces `What I learned:`.

**LAW 3 — NO EM/EN-DASHES.** Use ` - ` (hyphen with spaces) everywhere; em-dashes are the most reliable AI-slop tell. Only exception: quoted content where the source used one.

**LAW 4 — NO `##`/`###` HEADERS IN BODY.** GENERAL/NEWS/PROMPTING/RECOMMENDATIONS structure is: bold-lead-in paragraphs → prose label `KEY PATTERNS from the research:` → numbered list. Nothing else. The engine-emitted `## Pre-Research Status` block passes through as-is. COMPARISON exception: `## Quick Verdict`, `## {Entity}` (per entity), `## Head-to-Head`, `## The Bottom Line`, `## The emerging stack` are required; any other header is still forbidden.

**LAW 5 — ENGINE FOOTER PASS-THROUGH, EVERY RUN.** The engine output ends with a `✅ All agents reported back!` emoji-tree footer bounded by `---` lines and `<!-- PASS-THROUGH FOOTER -->` comments. Include it verbatim after KEY PATTERNS (and after the comparison table if present), before the invitation. Never recompute stats, reformat the tree, or substitute your own. A response without the footer is not valid skill output.

**LAW 6 — NO RAW EVIDENCE DUMPS.** The `<!-- EVIDENCE FOR SYNTHESIS -->` blocks (`## Ranked Evidence Clusters`, `## Stats`, `## Source Coverage`) are input for YOU, not output. If your response contains `### 1.` with a `(score N, M items, sources: ...)` tuple or `- Uncertainty: single-source` — you dumped evidence instead of synthesizing; stop and regenerate as `What I learned:` prose.

**Per-run source outcomes:** read `## Partial Coverage` / `Report.source_status` before synthesizing. Only `no-results` means "the source was quiet". `partial`, `rate-limited`, `auth-failed`, `unreachable`, `timeout`, `schema-drift`, `skipped-unconfigured`, `error` mean coverage was not established — never write "nothing on X/Reddit" for those; qualify as partial coverage. The footer carries the user-visible outcome and `doctor` pointer; don't invent repair prescriptions in prose.

**LAW 7 — YOU ARE THE PLANNER; `--plan` IS MANDATORY ON NAMED-ENTITY TOPICS.** You (the reasoning model) generate the JSON query plan and pass it via `--plan "$QUERY_PLAN_FILE"` (tmpfile via heredoc, see Research Execution — never inline JSON, never wrap the call in `bash -lc '...'`: an apostrophe in a search string kills the command). The engine's stderr "No --plan and no LLM provider configured" does NOT mean you need credentials — "provider" means the engine's internal planner key; you ARE the provider. Bare `python3 scripts/last30days.py "$TOPIC"` on a named-entity topic is a violation. Self-check before Bash: does the command contain `--plan`? If not — generate the plan first (Step 0.75).

**LAW 8 — CITE READABLY FOR THE CURRENT HOST. NEVER A RAW URL STRING.** Host detection is deterministic: `CLAUDECODE` env var set → hidden-link host → wrap every cited @handle, r/sub, publication, channel, creator, market as `[name](url)` at first mention (URLs from the raw dump). `CLAUDECODE` unset (Codex, Cursor, Gemini CLI, raw CLI) → visible-URL host → plain labels (`per @handle`, `per r/sub`, `per KSAT`) — inline links there render as URL soup. When unsure, prefer plain labels. When raw data has no URL for a source, use the plain label — never a broken `[label]()`. The stats footer passes through verbatim on every host (LAW 5). **Self-check:** hidden-link host with zero inline links, or visible-URL host with `label (https://...)` clutter → regenerate ONCE. Dropping a host's citation form is not a way to satisfy LAW 1; they are complementary.

**LAW 9 — WEAVE THE COMMUNITY VOICE; NEVER NARRATE THE TOOLING.** The evidence carries `## Top Community Comments` (always present when 2+ exist) and sometimes `## Best Takes` — the funniest/sharpest crowd reactions are the whole point of this tool. Weave at least 2 verbatim, attributed comments (`u/name`, `@handle`) into the narrative — never a separate "Comments" section. A 1,338-upvote "Where's the limewire link" tells more about the moment than a news article. Copy comment URLs verbatim from the block — never reconstruct a status id. And never narrate engine behavior in the deliverable (no "the engine struck out", "name collided with X") — engine health belongs in diagnostics, not prose.

**LAW 10 — FIRST-PARTY POSTS ARE FIRST-CLASS EVIDENCE.** On a person topic the subject's own posts (the `from:{handle}` lane) are the richest vein — quote them as primary signal; don't lean on podcasts/articles for the subject's voice when their own posts are present. A line tagged `interaction:→@handle` is the subject's own reply/mention: a RELATIONSHIP signal worth reading even at near-zero engagement. Write the substance; never mention the tag or mechanism (LAW 9).

End of OUTPUT CONTRACT. Everything below is implementation.

---

# HOW TO INVOKE

**LIBRARY SEARCH FAST PATH — overrides everything below.** "Search my library for X" / "have I researched X before?" → no WebSearch, no setup, no fresh research:

```bash
LAST30DAYS_MEMORY_DIR="${LAST30DAYS_MEMORY_DIR:-$(xdg-user-dir DOCUMENTS 2>/dev/null || echo "$HOME/Documents")/Last30Days}"
"${LAST30DAYS_PYTHON:-python3}" "${SKILL_DIR}/scripts/last30days.py" library search "${LIBRARY_QUERY}" --save-dir="${LAST30DAYS_MEMORY_DIR}"
```

Relay the dated, topic-grouped matches (deterministic offline FTS; no model, no network). If SQLite lacks FTS5, relay the capability error — do not fall through to fresh research.

**LIBRARY FEED FAST PATH — same override.** Build/view/refresh/subscribe the saved library feed:

```bash
LAST30DAYS_MEMORY_DIR="${LAST30DAYS_MEMORY_DIR:-$(xdg-user-dir DOCUMENTS 2>/dev/null || echo "$HOME/Documents")/Last30Days}"
"${LAST30DAYS_PYTHON:-python3}" "${SKILL_DIR}/scripts/last30days.py" library feed --save-dir="${LAST30DAYS_MEMORY_DIR}"
```

Relay the local `index.html` and `feed.xml` paths. Publishing: only on explicit ask — warn that `ht-ml.app` pages are public by default; after consent add `--publish`; password goes through `LAST30DAYS_PUBLISH_PASSWORD`, never a visible flag. `feed.xml` becomes subscribable only when hosted on a static host; never call the `ht-ml.app` URL an Atom subscription URL, and never add `--publish` for a local feed request.

Fresh runs may include a `## From your library` block when prior runs overlap the topic — use as historical context, never as fresh evidence. Disable via `LAST30DAYS_LIBRARY_CONTEXT=off`.

**STEP 0 — RESOLVE HOST WEB SEARCH.** Determine whether this session has a usable web-search tool (built-in, deferred, or connector — Brave/Firecrawl/Exa/Serper/etc.):

- Available → use it for Step 0.5/0.55 pre-research and Step 2 supplements, and `export LAST30DAYS_NATIVE_SEARCH=1` in the engine's shell so the engine skips its lower-quality keyless web floor.
- Not available → skip Steps 0.55 and 0.75, add `--auto-resolve` to the engine command, leave `LAST30DAYS_NATIVE_SEARCH` unset (the keyless floor then supplies web coverage). The rule is capability-based, not host-name-based.

Skipping pre-research and running the engine bare is the second-most-common failure of this skill: output looks fine but misses founder X timelines, GitHub activity, subreddit threads, and current positioning.

**FIRST-RUN GATE — run immediately after resolving web search, before any research:**

```bash
grep -q "SETUP_COMPLETE=true" ~/.config/last30days/.env 2>/dev/null && echo "1" || echo "FIRST_RUN_DETECTED"
```

`1` → continue. `FIRST_RUN_DETECTED` → read `references/setup-wizard.md` and complete the wizard BEFORE any topic research (it installs yt-dlp, Digg CLI, extracts X cookies; skipping it silently degrades the run to WebSearch-only and misrepresents the skill).

**STEP 1 — RUN THE ENGINE.** The Python engine IS the skill; WebSearch-only synthesis is not valid output (the #1 failure mode is answering from 3-10 WebSearches). Branch:

- **Trending / discovery** ("what's hot", "what's exploding in AI agents"): after the wizard (if any), return HERE — do not downgrade to a topic run. Global: `--discover` with NO domain argument (sweeps r/all, HN front page, Digg hot lists). Domain: `--discover "${DISCOVERY_DOMAIN}"`. Both with `--emit=compact --save-dir="${LAST30DAYS_MEMORY_DIR}"`. Discovery nominates topics then fully researches each — use Bash timeout 600000. `--discover-shallow` for a fast sweep. Skip Steps 0.5-0.75 and WebSearch supplements entirely; relay stdout verbatim, including "Nothing solid this window".
- **Topic provided**: proceed through Step 0.45 → 0.5 → 0.55 → 0.75 → Research Execution. WebSearch is a supplement AFTER the engine (Step 2), never a substitute.
- **No topic**: ask one short question, wait. No research.

Every valid output includes the engine's `✅ All agents reported back!` footer. No footer = you did not run the skill.

**Person topics (developers, creators, CEOs): the command MUST include at minimum `--x-handle` AND `--github-user` AND `--subreddits`, typically `--x-related`** — unless Step 0.5 produced an explicit "no account" note. Only `--x-handle` on a person topic = pre-flight skip (thin corpus, no GitHub scoping).

---

## Runtime Preflight

Resolve a Python 3.12+ interpreter once into `LAST30DAYS_PYTHON` before any engine command:

```bash
try_last30days_python() {
  candidate="$1"
  [ -n "$candidate" ] || return 1
  if [ -x "$candidate" ]; then
    :
  elif command -v "$candidate" >/dev/null 2>&1; then
    :
  else
    return 1
  fi
  "$candidate" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || return 1
  LAST30DAYS_PYTHON="$candidate"
  return 0
}

windows_path_to_unix() {
  path="$1"
  [ -n "$path" ] || return 1
  if command -v cygpath >/dev/null 2>&1; then
    cygpath -u "$path"
  else
    printf '%s\n' "$path"
  fi
}

if [ -z "${LAST30DAYS_PYTHON:-}" ]; then
  while IFS= read -r windows_python_root; do
    [ -n "$windows_python_root" ] && [ -d "$windows_python_root" ] || continue
    while IFS= read -r py; do
      try_last30days_python "$py" && break 2
    done <<EOF_PYTHON_CANDIDATES
$(find "$windows_python_root" -maxdepth 2 -type f -iname python.exe 2>/dev/null | sort -r)
EOF_PYTHON_CANDIDATES
  done <<EOF_WINDOWS_PYTHON_ROOTS
$([ -n "${LOCALAPPDATA:-}" ] && printf '%s\n' "$(windows_path_to_unix "$LOCALAPPDATA")/Programs/Python")
$([ -n "${ProgramFiles:-}" ] && windows_path_to_unix "$ProgramFiles")
$([ -n "${PROGRAMFILES:-}" ] && windows_path_to_unix "$PROGRAMFILES")
$(program_files_x86="$(printenv 'ProgramFiles(x86)' 2>/dev/null || true)"; [ -n "$program_files_x86" ] && windows_path_to_unix "$program_files_x86")
EOF_WINDOWS_PYTHON_ROOTS
fi

if [ -z "${LAST30DAYS_PYTHON:-}" ]; then
  for py in python3.14 python3.13 python3.12 python3 python; do
    try_last30days_python "$py" && break
  done
fi

# uv fallback: hosts without system 3.12 but with uv get a managed CPython 3.12.
if [ -z "${LAST30DAYS_PYTHON:-}" ] && command -v uv >/dev/null 2>&1; then
  uv_py="$(uv python find '>=3.12' 2>/dev/null)"
  if [ -z "$uv_py" ] || [ ! -x "$uv_py" ]; then
    echo "NOTE: no Python 3.12+ found; installing a managed CPython 3.12 via uv (~28MB, one-time)." >&2
    if UV_HTTP_TIMEOUT=30 uv python install 3.12 >/dev/null 2>&1; then
      uv_py="$(uv python find '>=3.12' 2>/dev/null)"
    else
      echo "WARN: 'uv python install 3.12' failed; falling through to the version-gate error below." >&2
    fi
  fi
  try_last30days_python "$uv_py"
fi

if [ -z "${LAST30DAYS_PYTHON:-}" ]; then
  echo "ERROR: last30days v3 requires Python 3.12+. Install Python 3.12+ or set LAST30DAYS_PYTHON to a supported interpreter." >&2
  exit 1
fi

"${LAST30DAYS_PYTHON}" -c 'import sys; raise SystemExit(0 if sys.version_info >= (3, 12) else 1)' || {
  echo "ERROR: LAST30DAYS_PYTHON must point to Python 3.12+." >&2
  exit 1
}

LAST30DAYS_MEMORY_DIR="${LAST30DAYS_MEMORY_DIR:-$(xdg-user-dir DOCUMENTS 2>/dev/null || echo "$HOME/Documents")/Last30Days}"
```

**Version gate:** if the preflight (incl. uv fallback) errors on Python 3.12+, tell the user the one-line install (`brew install python@3.12` / `winget install Python.Python.3.12` / `sudo apt install python3.12`) and STOP. No WebSearch-only fallback — it silently misses Reddit, X timelines, YouTube transcripts, TikTok, Polymarket and misrepresents what was searched.

## Configuration

`LAST30DAYS_MEMORY_DIR` picks where raw research saves (default: the user's Documents folder + `/Last30Days`, resolved through `xdg-user-dir DOCUMENTS` - on a localized Linux desktop it is not literally `~/Documents`; the engine reads it from process env or `~/.config/last30days/.env`; explicit `--save-dir` wins; the engine prints `[last30days] Saved output to <path>` on every save - read that path rather than assuming one). Каталог создаёт сам `scripts/last30days.py` при первом запуске; SessionStart-хука из upstream-версии в этой копии нет.

When BOTH `LAST30DAYS_API_KEY` and `LAST30DAYS_API_BASE` are set the engine routes research through a remote API — read `references/optional-sources-and-modes.md` (remote mode, exit code 3 = clarifying question, HTTP 402 handling). Same file covers `--corpus` local files, the Perplexity source, the Reddit backend pin, full `doctor` detail, and the security/permissions catalog.

## Step 0: First-Run Setup

Missing `.last30days.env` / keychain entry, a `skipped-unconfigured` source, or a key add/rotate request → `references/setup-wizard.md`. Otherwise continue.

---

## Parse User Intent

Extract and store:
- `TOPIC`; `TARGET_TOOL` (or "unknown" — do NOT ask about the tool before research; ask after showing results if relevant)
- `QUERY_TYPE`: PROMPTING ("X prompts", "best practices") | RECOMMENDATIONS ("best X", "top X") | NEWS ("what's happening with X") | COMPARISON (` vs `/` versus ` → also `TOPIC_A`, `TOPIC_B`) | GENERAL (everything else)
- `REGISTER`: explicit `--register` arg → `LAST30DAYS_REGISTER` → `default`. Legacy `ELI5_MODE=true` = `eli5`. Register words are controls, not topic text.

**Build ACTIVE_SOURCES_LIST from the engine's own diagnostic — never by checking env vars or `.env`** (credentials resolve at runtime from several places; a file check under-reports):

```bash
SKILL_DIR="<absolute path of the directory containing the SKILL.md you just Read>"
"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" --diagnose
```

`available_sources` in its JSON is authoritative. Token→name: `reddit`→Reddit, `hackernews`→Hacker News, `polymarket`→Polymarket, `github`→GitHub, `digg`→Digg, `x`→X, `youtube`→YouTube, `tiktok`→TikTok, `instagram`→Instagram, `threads`→Threads, `pinterest`→Pinterest, `linkedin`→LinkedIn, `bluesky`→Bluesky, `perplexity`→Perplexity, `grounding`→Web, `jobs`→Jobs, `corpus`→Your files, `dripstack`→DripStack. Drop anything in `EXCLUDE_SOURCES` (comma-separated, case-insensitive).

**Doctor:** on "is X working?" / "what's broken?" run `scripts/last30days.py doctor` (`--json` for machine contract; `--postmortem` after a thin run; `--probe` for a bounded live test). **Standing rule:** before research that depends on login-backed sources (X cookies, ScraperVendor Reddit backfill), consult `doctor --cached --json` (TTL 900s) — re-run live doctor only if stale or previously degraded. When X is active, announce its predicted backend from `sources.x.active_backend` (e.g. "X will use: bird") in the pre-research status line. Full doctor semantics → `references/optional-sources-and-modes.md`.

Then display one line (list all sources with Oxford comma, or "and more" if 5+; no multi-line "Parsed intent" block, no time promises, no unconfigured sources):

```
/last30days - searching {ACTIVE_SOURCES_LIST} for what people are saying about {TOPIC}.
```
COMPARISON variant: `/last30days - comparing {TOPIC_A} vs {TOPIC_B} across {ACTIVE_SOURCES_LIST}.`

---

## Step 0.45: Query Quality Pre-Flight (keyword traps)

Running the engine on a doomed query burns 5+ minutes and produces junk; detecting the trap costs one turn. Match the topic against these classes BEFORE Step 0.5:

1. **Demographic shopping** (`gift for {age} year old {gender}`, `present for my {relationship}`): nobody posts in that vocabulary — real posts use relationship + hobbies + budget. Ask ONE clarifying question (hobbies / relationship / budget). If the user says "just run it": drop the literal age (numbers collide — 42 = Jackie Robinson), rewrite as `gifts for men in their 40s` / `gifts for men who {hobby}`, scope `--subreddits=GiftIdeas,BuyItForLife,AskMen,malefashionadvice,Dads` + hobby subs, and note the reframe in the Resolved block. If hobbies/budget already given inline — skip the question, reframe directly.
2. **Numeric/age trap** (a number that collides: 42, 40, 50, 100): strip the number from the engine query unless removing it changes the topic ("GPT-4" keeps it, "40 year old man" drops it). Document in Resolved.
3. **Overly-literal concept phrase** (`how to use X`, `what is Y`): tutorial phrasing matches blog titles, not social posts. Reframe to discussion phrasing: "Docker tips tricks workflows", "Docker production setups". Document.
4. **Generic single noun** (`bread`, `sneakers`, `coffee`): infinite corpus, no anchor. Ask which facet/community before running.
5. **Non-Latin-script topic** (Hebrew/Arabic/CJK, incl. mixed-script): Reddit/HN/GitHub/Polymarket are English-dominant and will return only noise. MANDATORY: force `--web-backend brave` (the only source indexing non-English web); skip `--subreddits` unless a known English-speaking community exists; note the language routing in Resolved; surface that X/YouTube would unlock deeper coverage.

Flow: match → if trap, emit `Pre-Flight: topic matches Class N ({name}). {action}.` and STOP on clarifying questions until answered; if clean, emit `Pre-Flight: topic is a {named-entity / comparison / concept} - proceeding to Step 0.5.` Never run the engine on a trap topic without explicit "run it anyway" or a concrete reframe.

---

## Step 0.5: Pre-Flight Resolution (handles, repos, communities)

**Do NOT stop after the first flag — every applicable flag is MANDATORY for its topic class** (stopping at `--x-handle` alone is the named 2026-04-18 person-topic failure: weak Reddit targeting, no GitHub scoping, thin corpus):

| Flag | Resolved in | Applies when |
|------|-------------|--------------|
| `--x-handle={handle}` | Step 0.5 Section A | Person, brand, product, or creator with X presence |
| `--x-related={h1,h2,...}` | Step 0.5 Section A | Associated entities (founders, commentators, collaborators) |
| `--github-user={user}` | Step 0.5b | Person who ships code |
| `--github-repo={owner/repo}` | Step 0.5c | Product / project / open-source tool |
| `--trustpilot-domain={domain}` | Step 0.5d | Company/brand/service AND Trustpilot source active |
| `--subreddits={sub1,...}` | Step 0.55 | Always |
| `--tiktok-hashtags={h1,...}` | Step 0.55 | Always (inferred) |
| `--tiktok-creators={c1,...}` | Step 0.55 | Creator / influencer / brand topics |
| `--ig-creators={c1,...}` | Step 0.55 | Creator / brand topics |
| `--web-backend brave` | Step 0.45 Class 5 | Non-Latin-script topics (mandatory) |
| `--auto-resolve` | Fallback | WebSearch available but 0.55 couldn't resolve cleanly |

Resolution recipes (X handles, GitHub user/repos, Trustpilot) → `references/preflight-resolution.md`; run every recipe that matches and carry results as `RESOLVED_HANDLE` / `RESOLVED_RELATED`.

**Agent mode / comparison / competitors / hiring:** `--agent` in the invocation → `references/agent-mode.md`. Topic contains `vs`/`versus`, or user asked for competitor sweep or hiring signals → `references/modes-comparison-competitors-hiring.md` before building the engine call.

---

## Step 0.55: Pre-Research Intelligence

> No WebSearch on this platform → skip 0.55 and 0.75, add `--auto-resolve` instead.

**MANDATORY when WebSearch exists — a `--plan`-less engine call is a 0.55 skip.** The engine's `[Resolve] No web search backend available, skipping resolve` line means YOU skipped your job. Re-run 0.55 even on repeat topics (handles for breaking news change weekly). Run 2-3 focused parallel WebSearches; infer what you can, search only what you can't:

1. **X handles** — already resolved in Step 0.5.
2. **Reddit + YouTube + current events** — `WebSearch("{TOPIC} subreddit reddit community")` and `WebSearch("{TOPIC} news {CURRENT_MONTH} {CURRENT_YEAR}")`. Extract 3-5 subs. Split: **dedicated** subs (entire sub IS the topic: r/Kanye for Kanye) → `RESOLVED_DEDICATED_SUBREDDITS` → `--dedicated-subreddits` (pulled in full, floor-exempt, so on-topic posts without the entity name aren't dropped); **broad** subs (mixed communities) → `RESOLVED_SUBREDDITS` → `--subreddits`. Label conservatively — most topics have 0-3 dedicated subs; unsure = broad.

**2a. Category-peer expansion — MANDATORY for product topics.** Brand-specific subs alone are insufficient; cross-product technique discussion lives in peer subs (missing them is the 2026-04-22 GPT Image 2 failure). Canonical peers (mirrored in `scripts/lib/categories.py`):

| Category | Trigger keywords | Peer subs (priority order) |
|----------|------------------|---------------------------|
| `ai_image_generation` | image generation, text to image, GPT Image, Nano Banana, Midjourney, Stable Diffusion, DALL-E, Flux.1, Imagen, Seedance, Ideogram, Recraft | `StableDiffusion, midjourney, dalle2, aiArt, PromptEngineering, MediaSynthesis` |
| `ai_video_generation` | video generation, text to video, Sora, Veo 3, Runway Gen, Kling, Pika Labs, Luma Dream Machine, Hailuo | `aivideo, StableDiffusion, runwayml, singularity, MediaSynthesis` |
| `ai_music_generation` | music generation, ai music, Suno, Udio, Riffusion, Stable Audio | `SunoAI, udiomusic, aimusic, artificial` |
| `ai_coding_agent` | Claude Code, Cursor IDE, GitHub Copilot, Windsurf, Aider, Cline, OpenClaw, Hermes Agent, Continue.dev, Codeium, Devin | `ChatGPTCoding, LocalLLaMA, singularity, PromptEngineering` |
| `ai_agent_framework` | agent framework, LangChain, LangGraph, CrewAI, AutoGen, LlamaIndex, DSPy, smolagents | `LangChain, LocalLLaMA, AI_Agents, MachineLearning` |
| `ai_chat_model` | GPT-5/4, Claude Opus/Sonnet/Haiku, Gemini Pro/Flash, Llama 3/4, DeepSeek, Qwen, Mistral Large, Grok | `LocalLLaMA, ChatGPT, ClaudeAI, singularity, artificial` |
| `saas_screen_recording` | screen recording, screen recorder, Loom video, Tella screen, Vidyard | `SaaS, screenrecording, productivity, Entrepreneur` |
| `saas_productivity` | Notion app, Obsidian, Linear app, Asana, ClickUp, productivity app | `productivity, SaaS, ObsidianMD, Notion` |
| `prediction_markets` | Polymarket, Kalshi, prediction market, event contracts, Manifold Markets | `Polymarket, Kalshi, predictionmarkets` |
| `crypto_defi` | DeFi protocol, yield farming, liquidity pool, stablecoin, layer 2, L2 rollup | `defi, ethfinance, CryptoCurrency, ethereum` |

Merging: WebSearch subs first, append 2-3 peers in priority order, dedupe case-insensitively, cap 10 (keep WebSearch subs, drop peers from the tail). Category not listed but same spirit (new image-gen tool, niche SaaS) → pick the 2-3 most active cross-product communities anyway. **Self-check:** product in a known category with fewer than 2 peer subs in the list → widen NOW; the observable contract is the `(+ {category_id} peers)` annotation on the Resolved Reddit line. Person/music/news topics are exempt.

3. **TikTok** — INFER 2-3 hashtags from topic knowledge ("Kanye West" → `kanyewest,ye,bully`); creators only for creator/influencer/brand topics. Do NOT WebSearch "{PERSON} TikTok account" — CEOs don't TikTok. → `RESOLVED_HASHTAGS`, `RESOLVED_TIKTOK_CREATORS`.
4. **Instagram** — same inference rule → `RESOLVED_IG_CREATORS`. Skip for tech CEOs and abstract concepts.
5. **YouTube queries** — infer 2-3 by shape: artists → `'{TOPIC} album review'`/`'{TOPIC} reaction'`; products → `'{TOPIC} review'`/`'{TOPIC} tutorial'`; comparisons → `'{A} vs {B}'`; people in the news → `'{TOPIC} interview {YEAR}'`. → `RESOLVED_YT_QUERIES`.
6. **First-party positioning — MANDATORY for company/product/service topics.** Fetch the CURRENT stated pitch (homepage tagline, docs, pricing) — never from memory: copy goes stale and a stale claim produces a false gap. One focused search per entity if not covered already. → `RESOLVED_POSITIONING` (one-line value prop + explicit claims). Used to ground "what it is", reject off-brand noise, and feed the pitch-vs-pulse beat. The test is "identifiable first party with a fetchable pitch" — people NEVER pass (MrBeast-the-company can, Jimmy Donaldson cannot); ownerless topics (Bitcoin) fail too. Skip silently otherwise.

**Comparison queries:** resolve all lookup types per entity (X handle, GitHub repo, founder handle, subreddits project+category, Trustpilot when active) — but batch into 3-4 WebSearches combining entities (`WebSearch("OpenClaw Hermes Paperclip github repos AI coding agent")`), never one search per entity per type. Display the per-entity Resolved block before the engine runs; a block with only project handles and no founders/repos is a regression.

**Display the Resolved block** (only lines with values; the peers annotation when 2a fired; Positioning only for company/product topics):

```
Resolved:
- X: @{HANDLE} (+ @{COMPANY}, @{COMMENTATOR})
- Reddit: r/{sub1}, r/{sub2}, r/{peer1}, r/{peer2} (+ {category_id} peers)
- TikTok: #{hashtag1}, #{hashtag2}
- YouTube: {query1}, {query2}
- Trustpilot: {domain}
- Positioning: "{one-line stated value prop}" (first-party)
```

Can't infer a platform → skip that flag; the engine falls back to keyword search.

---

## Step 0.75: Generate Query Plan (YOU are the planner)

> Skipped 0.55 (no WebSearch) → skip this too; the engine plans internally.

Generate a JSON plan; the engine receives it via `--plan` and skips its internal planner:

```json
{
  "intent": "breaking_news",
  "freshness_mode": "strict_recent",
  "cluster_mode": "story",
  "subqueries": [
    {"label": "primary", "search_query": "kanye west", "ranking_query": "What notable events involving Kanye West happened in the last 30 days?", "sources": ["reddit", "x", "hackernews", "youtube", "tiktok", "instagram"], "weight": 1.0},
    {"label": "album", "search_query": "kanye west bully album", "ranking_query": "How was Kanye West's BULLY album received?", "sources": ["youtube", "reddit", "tiktok", "instagram"], "weight": 0.8}
  ]
}
```

Rules:
- 1-4 subqueries. **Primary subquery MUST include ALL of: reddit, x, youtube, tiktok, instagram, hackernews, polymarket.** Optional sources: bluesky, truthsocial, threads, pinterest, grounding (only with a Brave/Exa/Serper key), digg (only if `digg-pp-cli` on PATH).
- `search_query` = concise, keyword-heavy, how content is TITLED; `ranking_query` = natural-language question.
- **DISAMBIGUATION — mandatory for collision-prone names, the #1 cause of off-topic noise.** If the name is a common word or collides with other public figures, anchor EVERY subquery (and its ranking_query) with a specific named entity: `"kevin rose digg founder"` not `"kevin rose"`, `"tella screen recording"` not `"tella"`. Globally unambiguous names (Kanye West, Nvidia) need no anchor.
- NEVER include temporal phrases ("last 30 days", month names, years) or meta-research words ("news", "updates") in search_query. Preserve exact proper nouns.
- Comparison: per-entity subqueries at 0.8 + head-to-head at 1.0, each with the product category ("tella screen recorder review"). Products → YouTube/Reddit/TikTok; predictions → include polymarket; how-to → YouTube+Reddit. Weights: primary 1.0, secondary 0.6-0.8, peripheral 0.3-0.5.
- freshness_mode: breaking_news, prediction → `strict_recent`; concept, how_to → `evergreen_ok`; else `balanced_recent`.
- cluster_mode: breaking_news → `story`; comparison, opinion → `debate`; prediction → `market`; how_to → `workflow`; else `none`.

Store as `QUERY_PLAN_JSON`.

---

## Research Execution

**Precondition gate — all true before invoking:**
1. Platform branch chosen (WebSearch or not).
2. WebSearch available → 0.55 AND 0.75 done (not optional; the degraded path produces bland 4-bullet summaries).
3. No WebSearch → `--auto-resolve` added.
4. Command uses `--emit=compact` (`--emit md` is debug-only, disallowed as the user-facing flow).
5. On WebSearch platforms the command includes `--plan` + every resolved flag.

**Run FOREGROUND with timeout 300000 (5 min). Never run_in_background — you must read the full output.**

```bash
# SKILL_DIR = absolute dir of THIS SKILL.md (scripts/last30days.py is always its direct child).
SKILL_DIR="<absolute path of the directory containing the SKILL.md you Read>"

if [ ! -f "$SKILL_DIR/scripts/last30days.py" ]; then
  echo "ERROR: scripts/last30days.py not found under SKILL_DIR=$SKILL_DIR" >&2
  exit 1
fi

"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" $ARGUMENTS --emit=compact --save-dir="${LAST30DAYS_MEMORY_DIR}" --save-suffix=v3
```

**Plan via tmpfile** (parse_plan reads file paths; inline JSON breaks on apostrophes in search/ranking strings):

```bash
# Trailing XXXXXX (no .json suffix): BSD mktemp only substitutes trailing X's.
QUERY_PLAN_FILE=$(mktemp "${TMPDIR:-/tmp}/last30days-plan.XXXXXX")
trap 'rm -f "$QUERY_PLAN_FILE"' EXIT
# >| not >: mktemp already created the file; plain > is refused under noclobber,
# leaving the plan empty -> deterministic fallback.
cat >| "$QUERY_PLAN_FILE" <<'PLAN_EOF'
{QUERY_PLAN_JSON_FROM_STEP_0.75}
PLAN_EOF
```

Run the block directly in your shell tool — NEVER wrapped in `bash -lc '...'`/`zsh -lc '...'`: the outer single quotes terminate at the first apostrophe inside the heredoc and the command dies with `unmatched`.

Then add to the engine command (omit any unresolved flag): `--plan "$QUERY_PLAN_FILE"`, `--x-handle=`, `--subreddits=` (broad), `--dedicated-subreddits=`, `--tiktok-hashtags=`, `--tiktok-creators=`, `--ig-creators=`, `--github-user=` (person topics), `--github-repo=` (product topics), `--trustpilot-domain=` (company topics, source active). Comparison mode: `--x-handle={A}` on pass A, `{B}` on pass B, both on head-to-head. No WebSearch → `--auto-resolve` instead of plan/flags.

**Read the ENTIRE output** — eight data sections in order: Reddit, X, YouTube, TikTok, Instagram Reels, Hacker News, Polymarket, WebSearch. Missing a section = wrong stats. YouTube items carry pre-extracted transcript highlights (quote them, attribute to the channel) and, when a ScraperVendor key is set, top comments (quote with like counts; suppress via `EXCLUDE_SOURCES=youtube_comments`). TikTok/Instagram items carry creator, views/likes, captions — count them into synthesis and stats.

---

## Step 2: WebSearch supplements (after the engine)

Separate budget from Step 0.55 pre-research — counting one against the other is why supplement depth collapses. Default 3 supplements; drop to 2 if the engine returned 80+ items on a niche topic; zero is almost never correct (the social engine misses long-form analysis and critic reactions); ceiling 3 (5+ pushed runtimes to 9 minutes).

Queries by QUERY_TYPE — RECOMMENDATIONS: `best {TOPIC} recommendations`, `{TOPIC} list examples`, `most popular {TOPIC}` (goal: specific names). NEWS: `{TOPIC} news {YEAR}`, `{TOPIC} announcement update`. PROMPTING: `{TOPIC} prompts examples {YEAR}`, `{TOPIC} techniques tips`. GENERAL: `{TOPIC} {YEAR}`, `{TOPIC} discussion`.

All types: use the user's EXACT terminology; exclude reddit.com/x.com/twitter.com (engine covers them); include blogs, tutorials, docs, news, GitHub. No trailing `Sources:` block (LAW 1) — the WebSearch citation requirement is satisfied by the engine footer's 🌐 Web line and the saved-file appendix.

Pass-through options: `--days=N`, `--quick` (8-12/source), default (20-30), `--deep` (50-70 Reddit, 40-60 X), `--register={default,exec,dev,creator,eli5}` (audience template; not topic text; ignored for JSON/discover/drill/library/comparison output).

## Step 2.5: Append WebSearch results to the saved raw file

**MANDATORY** — otherwise future sessions can't trace which web sources informed the synthesis. Locate the file via the engine's `[last30days] Saved output to {path}` log line (never a hardcoded path). Comparison runs: append the same section to EVERY per-entity Markdown raw file listed in `[last30days] Comparison artifact set:` (never append Markdown to `.html`/`.json`). Append:

```
## WebSearch Supplemental Results

- **{Publisher}** ({domain}) — {1-2 sentence excerpt of what you found}
```

One bullet per web source that shaped a claim (including pre-research searches you cited) — so bullet count ≥ number of Step 2 supplements. No URLs (domain in parens is the citation), no nested bullets. Ran zero supplements → skip the section entirely.

---

## Synthesis

**v3 output is cluster-first (grouped by story, not source).** Read: `### N. Cluster Title (score, items, sources)`; `Uncertainty: single-source` = one platform only (caution); `thin-evidence` = all items <55 (mention with caveat). Synthesize per-cluster first (each = one story), multi-source clusters (3+ platforms) are the strongest signals — lead with them; cross-cluster themes second; quote evidence snippets directly; extract top 3-5 actionable insights. When Step 0.55 resolved a specific entity, prioritize content about THAT entity — a same-name stranger gets a brief mention or nothing.

**Ground in the ACTUAL research, not pre-existing knowledge**: exact product names matter ("ClawdBot" ≠ "Claude Code" — don't conflate on a shared word), quote what sources actually say.

Weighting: Reddit/X high (engagement signals), YouTube high (views + transcripts), TikTok high (viral signal), WebSearch lower (no engagement) — except product comparisons, where a detailed blog comparison weighs equal to social data. Top comments often beat the parent post: quote them with vote counts. X reply clusters answering a "what's the best X?" ask are the strongest endorsement form — call them out ("every reply said Tella"). GitHub person-mode items: lead with velocity ("X PRs across Y repos"), weave release notes; project-mode `(live: NNK stars)` numbers override anything a blog/tweet claimed.

**Polymarket:** real money beats opinion — when markets are relevant, treat odds as top-tier evidence. Prefer structural/long-term markets (championship > weekly matchup, regime change > strike deadline, presidency > state primary); name the specific outcome's odds and movement ("Arizona at 28% for a #1 seed, up 10% this month"); weave into narrative, not a separate paragraph; show ONLY % odds — NEVER dollar volumes/liquidity (internal metrics, meaningless to readers); highlight 3-5 markets by importance when several exist.

**Registers** (engine already reorders evidence; match it): `exec` — exactly five compact numbered findings after `What I learned:`, strongest number first, decision implication in every finding. `dev` — GitHub/code evidence first, versions, benchmarks, live repo numbers over third-party claims. `creator` — sharpest hook first, engagement metrics forward, end with 3 evidence-grounded content angles. `eli5` — zero-context reader: no unexplained jargon, short sentences, analogies, most important thing first; same structure, same citations; accessible, not childish. `default` — contract unchanged.

QUERY_TYPE RECOMMENDATIONS or COMPARISON → read `references/synthesis-by-query-type.md` NOW (full templates). GENERAL/NEWS/PROMPTING use the `What I learned:` shape below. For all types identify from the research: recommended prompt format, top 3-5 cross-source patterns, specific keywords/structures, pitfalls named BY THE SOURCES.

### Output shape (GENERAL / NEWS / PROMPTING)

```
🌐 last30days v{VERSION} · synced {YYYY-MM-DD}

What I learned:

**{Specific newsy headline}** - [1-2 sentences on what people are saying, per [@handle](url) or [r/sub](url)]

**{Headline 2}** - [...]

KEY PATTERNS from the research:
1. [Pattern] - per [@handle](url)
2. [Pattern] - per [r/sub](url)
```

- Every narrative paragraph MUST open `**Headline** - ` (bold + hyphen; without it the output is unscannable). Headlines specific ("BULLY dropped and it's dominating"), not generic ("Album release").
- Citations sparing: 1-2 in the intro, 1 per KEY PATTERN, short form, no engagement metrics inline, no chains ("per @x, @y, @z"). Priority: X @handles > r/subs (prefer top comments over thread titles) > YouTube channels > TikTok/IG creators > HN > Polymarket (with odds+movement) > web publications (only when social lacks the fact). Lead with people, not publications — the user came for the conversation, not the press release. Link form per LAW 8.
- Max ONE blank line between blocks; never pad before tables.
- RECOMMENDATIONS adds per-item `Sources:` lines with actual @handles/subs/publications from the research (template → `references/synthesis-by-query-type.md`).

**Pitch-vs-pulse beat** (company/product topics with `RESOLVED_POSITIONING`): if the month's evidence directly SUPPORTS a specific claim, CUTS AGAINST it, or is squarely ABOUT the pitched ground — one bold-lead-in paragraph saying how, anchored to the real top item with its engagement, windowed ("this month's conversation"), never trend verbs one window can't support. Orthogonal evidence → write NOTHING (a manufactured connection is worse than silence). Test specific claims against specific threads; never grade a broad tagline against one thread. Never for people, events, concepts, ownerless topics, or when positioning wasn't fetched THIS run.

### After the narrative, in order

1. **Quality nudge:** if the output contains a `**🔍 Research Coverage:**` block, render it verbatim before the stats. If X returned 0 for lack of auth, offer the unlock via AskUserQuestion: "Scan my browser cookies (free)" (consent → BROWSER_CONSENT=true + FROM_BROWSER=auto to .env) / "I have AUTH_TOKEN and CT0" (paste → .env) / "I have an xAI API key" (paste → .env) / "Skip for now".
2. **Engine footer verbatim** (LAW 5): the block from `✅ All agents reported back!` to `📎 Raw results saved to ...`. The engine already omits zero-count sources, totals the stats, formats odds, and picks top voices — copy exact bytes. Absent only when every source returned zero — then go straight to the invitation.
3. **Invitation** — MUST include 2-3 specific suggestions drawn from what the research actually found (generic bullets = you didn't absorb it):

```
---
I'm now an expert on {TOPIC}. Some things I can help with:
- [specific follow-up on the biggest story/pattern]
- [specific creative/practical application]
- [deeper dive into a debate from the research]
```

PROMPTING variant: "What do you want to make? ... Just describe your vision and I'll write a prompt you can paste straight into {TARGET_TOOL}." RECOMMENDATIONS: offer compare A vs B / why C is trending / get started with D. COMPARISON: offer per-entity deep dives (`/last30days {TOPIC_A}`), a dimension focus, `--days=7/90`. Close with `I have all the links to the {N} {source list} I pulled from. Just ask.` naming only sources with >0 results.

**Saved artifact access:** normal report → the 📎 path line in the footer is enough (don't open the raw file, don't ask). Markdown explicitly requested → the saved path is the deliverable. HTML requested → `references/save-html-brief.md`. Share/publish → hosted HTML flow: save local first, then publishing choices; `ht-ml.app` password question only when that service is chosen; never block local file creation on hosting decisions.

## PRE-PRESENT SELF-CHECK

Verify before displaying; if a check fails AND the data supports fixing it, regenerate ONCE (data absent → skip the check silently; still failing after one regen → show best version and name the unmet check):

1. Bold `**Headline** - ` on every narrative paragraph.
2. Engine footer present with per-source `├─`/`└─` lines; no active source dropped, no zero source shown.
3. ≥2 verbatim attributed community comments woven in (LAW 9); zero tooling meta-commentary.
4. Polymarket percentages + movement present if markets were returned.
5. `✅ All agents reported back!` tree exactly as the engine emitted it.
6. Nothing after the invitation — no Sources/References/link lists (LAW 1).
7. Protocol was followed: `--emit=compact --plan` + resolved flags on WebSearch platforms; if you took the degraded path, return to Step 0.55 and re-run instead of regenerating prose.

## SHAREABLE HTML BRIEF

User asked for a shareable brief or HTML file → `references/shareable-html-brief.md` (+ `references/save-html-brief.md`). Otherwise skip.

## AFTER THE REPORT

The moment the synthesis is on screen, read `references/after-report-expert-mode.md` and follow it (follow-ups, prompt-writing from the research, expert mode, per-prompt footer). Do not improvise this phase.

## Security & Permissions

Reads public platform data; saves briefings to `LAST30DAYS_MEMORY_DIR`; X search via optional user tokens; browser cookies only with explicit consent; never posts or modifies content anywhere; `--preflight` prints a safe permission summary. Full endpoint/credential catalog and the does/does-not list → `references/optional-sources-and-modes.md`. Review scripts before first use.
