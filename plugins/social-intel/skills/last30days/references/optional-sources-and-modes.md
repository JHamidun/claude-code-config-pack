# Optional sources, remote API mode, doctor details

Read when the relevant trigger fires; not needed on a normal fresh-research run.

## Remote API mode (`LAST30DAYS_API_KEY` + `LAST30DAYS_API_BASE` both set)

The engine runs research through the configured remote API instead of local sources (unless
`--mock` is passed). `LAST30DAYS_API_BASE` is the endpoint and has no built-in default —
leaving either variable unset runs local sources normally. A configured `--corpus` /
`LAST30DAYS_CORPUS_DIRS` is the privacy exception: the engine bypasses the hosted backend and
runs locally so no file-derived input is forwarded.

The invocation is otherwise unchanged: same flags, `--quick`/`--deep` map to search depth, a
non-default `--register` is forwarded for server-side synthesis, progress lines stream on
stderr (`[narrate] step=...` plus elapsed/eta), report prints on stdout and saves to the
memory dir as usual — Steps 1-4 proceed normally. Exception: the remote endpoint does not
return the local `Report` needed for the versioned agent profile; use
`--emit=json --json-profile=raw` for its server-response JSON contract. No per-source keys or
setup-wizard credentials are needed for the search itself in this mode.

Two engine exits need specific handling:
- **exit code 3** — the API asked a clarifying question first; the engine prints the question
  and options on stderr. Present them to the user and re-run with the chosen angle folded
  into the topic.
- **HTTP 402 insufficient credits** — prints balance, amount needed, and a billing link.
  Relay those lines verbatim; do not fall back to WebSearch-only synthesis.

## Local corpus source (`--corpus <dir>`, `LAST30DAYS_CORPUS_DIRS`)

If the user asks to include their own notes/documents, preserve each supplied directory as a
repeatable `--corpus <dir>` flag. `LAST30DAYS_CORPUS_DIRS` activates persistent registered
directories automatically. Do not WebSearch, upload, quote into a hosted request, or
otherwise expose those paths or contents. Corpus retrieval is an offline lane; its candidates
bypass remote reranker/fun-scoring prompts and use deterministic local scoring. Matches
render under the 🔒 **From your files** badge. Recency window uses file modification time;
add `--corpus-all-time` only when the user explicitly asks for older files. Corpus evidence
is excluded from `--publish-html`, `library feed --publish`, and agent JSON by default.
`LAST30DAYS_CORPUS_IN_EXPORT=1` is the explicit agent-JSON privacy opt-in; never enable it on
the user's behalf.

## Perplexity source

Use only when the user asks for Perplexity, Deep Research, or paid grounded synthesis, or
when `perplexity` is already enabled in `INCLUDE_SOURCES` / `--search`. Direct
`PERPLEXITY_API_KEY` supports Sonar synthesis, Search API rows, and async Deep Research.
`OPENROUTER_API_KEY` is only a Sonar fallback. Normal runs default to
`LAST30DAYS_PERPLEXITY_MODE=sonar`; `search` = raw ranked web rows, `both` = synthesis plus
rows, `--deep-research` = `sonar-deep-research` with a 600s default wall timeout. A local
Deep Research timeout is not a failed API key; inspect the raw artifact's async request
id/status and resume by id if needed.

## Reddit backend pin

Reddit defaults to the free public backend with ScraperVendor as backup when
`SCRAPER_API_KEY` is available. If the user says public Reddit is shallow, bot-gated,
or missing nested comments: they can set `LAST30DAYS_REDDIT_BACKEND=scraper-vendor` to make
ScraperVendor primary and keep public Reddit as fallback. Do not set this automatically.

## Doctor (full detail)

`"${LAST30DAYS_PYTHON}" "${SKILL_DIR}/scripts/last30days.py" doctor` (append `--json` for the
machine contract). Four-state audit per source: **WORKING** (verified this/last run or
keyless-always-on), **TURNED ON - UNVERIFIED** (configured but no run evidence),
**NOT WORKING** (configured but failing, or last run errored), **COULD BE ON** (available,
not configured) — plus a CLI-health block for binary-dependent sources and indented
backup/comment sub-lanes.

- `doctor --postmortem` reads the last run's `last-report.json` and reports what actually
  broke per source (Failed/Partial/Succeeded with fix hints) — use right after a run that
  returned less than expected.
- `doctor --probe` runs a bounded live test (free HTTP + keyless CLI sources only;
  credit-gated sources never probed); the same bounded probe auto-fires on plain `doctor`
  when there is no fresh run. Per-source deadline: `LAST30DAYS_DOCTOR_PROBE_TIMEOUT`
  (default 10s).
- `doctor --cached --json` serves the report cached at
  `~/.config/last30days/doctor-cache.json` within its TTL (`LAST30DAYS_DOCTOR_TTL` seconds,
  default 900) for the cost of one file read.

## Developer-only eval capture

`--record-fixtures <dir>` is a hidden direct-engine flag for the deterministic
research-quality suite: records scrubbed HTTP and CLI-adapter responses to `<dir>/http.json`.
Never part of the user-facing slash-command invocation. See `docs/reference/eval.md` for
fixture review, replay, and baseline rules.

## Security & permissions catalog

**What the skill does:** sends search queries to ScraperVendor (`api.your-scraper.example`;
TikTok/Instagram, Reddit backup), legacy OpenAI Responses API for Reddit discovery (fallback
when no ScraperVendor key), X/Twitter via optional user cookies (`AUTH_TOKEN`/`CT0`),
explicit browser-cookie opt-in (`FROM_BROWSER` or setup consent), xAI (`api.x.ai`), Xquik
(`xquik.com`), or official X API v2 via xurl CLI (auto-detected); Algolia HN
(`hn.algolia.com`, free), Polymarket Gamma (`gamma-api.polymarket.com`, free); runs `yt-dlp`
locally for YouTube; optionally Brave / Parallel / Perplexity / OpenRouter for web; fetches
public Reddit thread data; stores watchlist findings in local SQLite; saves briefings as .md
to `LAST30DAYS_MEMORY_DIR`; generates local `index.html` / Atom `feed.xml`; publishes to
`ht-ml.app` only after explicit opt-in (public by default unless password-protected).
`--preflight` prints a permission summary without reading cookies, writing files, or running
research.

**What it does NOT do:** never posts/likes/modifies content; never reads browser cookies
without explicit config or consent; never uses Codex ChatGPT auth as an OpenAI credential;
never shares keys between providers; never logs or writes keys to output files. HN and
Polymarket are always available (no key, no binary). TikTok/Instagram require
SCRAPER_API_KEY (10,000 free calls, then PAYG). If `--agent` appears in the user's
slash-command arguments, treat it as skill-level mode guidance, not a Python CLI flag.

**Bundled scripts:** `scripts/last30days.py` (engine), `scripts/lib/` (search, enrichment,
rendering), `scripts/lib/vendor/bird-search/` (vendored X search client, MIT).
