# check-skill-solo

A Claude Code skill that fact-checks claims, numbers, citations, and AI output against
**independent model families** (Claude + Gemini + GPT) and verifies every source URL
mechanically (alive + exact quote present). Built to catch hallucinations — including the
"all the models agreed, so it must be true" kind.

## Install (the easy way)

1. Unzip this folder anywhere.
2. Run the installer:
   ```bash
   bash check-skill-solo/install.sh
   ```
3. Restart Claude Code.

## Install (manual)

Copy `SKILL.md` to:
```
~/.claude/skills/check-skill-solo/SKILL.md
```
(The folder name must be `check-skill-solo` and the file must be named `SKILL.md`.)

## Use

```
/check-skill-solo <fact or claim>
```
or just say "проверь / verify / fact-check this …".

## What you need (all optional)

The skill works with **zero setup** in Claude-only mode. For full strength, install one or both
cross-checkers and log in once — the skill auto-detects them:

```bash
npm install -g @openai/codex      && codex    # OpenAI / GPT
npm install -g @google/gemini-cli && gemini   # Google / Gemini
```

- No API keys are required if you log in to each CLI interactively.
- If you prefer headless keys, create `~/.claude/skills/check-skill-solo/.env.local` with
  `OPENAI_API_KEY="…"` and/or `GEMINI_API_KEY="…"` (`chmod 600`). This file stays on your machine
  and is **never** part of the shared skill.

## Honesty guarantee

If Gemini/GPT aren't available, the skill says so loudly ("SINGLE-FAMILY mode") instead of
pretending multiple models agreed. Only sources that pass the mechanical URL+quote check are
marked confirmed.
