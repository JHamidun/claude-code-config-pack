# Design System

> Build and apply a complete design system in Claude Code — tokens, color scales, type, dark mode, themes, and brand kit.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `design-system-create` | Build a design system from scratch: tokens, typography, components. |
| `design-tokens-w3c` | Export design tokens to the W3C Design Tokens (DTCG) format. |
| `color-system-builder` | One accent → full palette (light + dark, 9-step scale, semantic roles) with contrast checks. |
| `type-scale` | Modular type scale + proven font pairings (7–9 sizes, tiny → hero). |
| `dark-mode-add` | Turn a light-only design into light + dark with a working toggle. |
| `theme-factory` | Style any artifact (slides, docs, landing pages) with a coherent theme. |
| `deck-themes` | Ready-made slide themes — minimal, editorial, dark, data, brutalist. |
| `fonts-bundle` | Drop-in `<link>` blocks for common font pairs (Google Fonts, with fallbacks). |
| `brand-guidelines` | Apply a brand's colors and typography to any artifact. |
| `brand-extractor` | Pull colors, fonts, and base copy from a landing page by URL. |
| `moodboard` | HTML moodboard with an auto-extracted palette from 4–12 references. |

## Install

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin install design-system@hamidun
```

Enable it with `/plugin` — the skills then activate automatically when relevant.

## Usage

Just describe the design task — the right skill triggers itself:

- *"Build a design system from this brand color #2563EB"* → `color-system-builder` + `design-system-create`
- *"Add a dark mode to this landing page"* → `dark-mode-add`
- *"Export these tokens to W3C format for Style Dictionary"* → `design-tokens-w3c`
- *"Make a moodboard from these 6 screenshots"* → `moodboard`

## Related plugins

`design-process` · `prototyping` · `ui-motion` · `design-io` · `web-publish`

---

MIT © [Zhemal Khamidun](https://github.com/JHamidun)
