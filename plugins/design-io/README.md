# Design I/O & QA

> Figma import/export, PDF/PNG/PPTX export, dev handoff, verify, perf & a11y audits.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `a11y-audit` | Run axe-core headless; report WCAG violations with links to the offending elements. |
| `claude-design` | Work with Claude Design (claude.ai/design) — mockup-to-production workflow, reading prototypes and porting them pixel-perfect. |
| `dev-handoff` | Build a developer handoff package — extract tokens from finished HTML, generate a component/spec README with sizes and states. |
| `document-import` | PDF / DOCX / PPTX / sketch → structured content for slides or landing pages (headings, text, quotes, images). |
| `export-pdf` | HTML → PDF via Playwright Chromium, keeping vector text — for slides and landers you send as one file. |
| `export-png` | HTML → PNG (single or series) — social covers (Twitter/Instagram/LinkedIn), previews, individual slides. |
| `export-pptx` | HTML slides → PPTX where each slide is a screenshot image (no text editability). |
| `figma-import` | Figma → design tokens (colors/type/spacing) plus key nodes exported as PNG references. |
| `figma-write-back` | Post HTML changes back into Figma as comments or suggestions via the Figma REST API. |
| `github-import` | GitHub repo → design system, components, and CSS tokens as context so a new prototype matches the codebase. |
| `i18n-stress-test` | Stress-test UI for i18n — long words (German), RTL (Arabic/Hebrew), CJK, and emoji in text. |
| `onboarding-ux` | First-run patterns — welcome screens, permission requests, teaching empty states, progressive disclosure, time-to-value. |
| `perf-audit` | Lighthouse performance audit — measures LCP / CLS / TBT / FCP / TTI on an artifact with actionable advice. |
| `proto-smoketest` | E2E click-through smoke test via Playwright over the critical user paths of an interactive prototype. |
| `screenshot-test` | Pixel-diff between the current and a baseline screenshot; fails if the artifact visually broke. |
| `verifier` | Headless HTML check — open in Chromium, read console errors/warnings, screenshot for review. |
| `version-snapshots` | Lightweight version history for an artifact — snapshot on each save, roll back, compare two moments. |

### Agents

- `accessibility-tester`
- `mobile-fixes-implementer`
- `mobile-responsiveness-tester`

### Commands

- `/userflow`

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install design-io@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Related plugins

`design-system` · `design-process` · `prototyping` · `ui-motion` · `web-publish`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
