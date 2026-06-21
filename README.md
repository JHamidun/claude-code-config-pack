# hamidun — Claude Code plugin marketplace

A curated set of **29 focused Claude Code plugins** by [Zhemal Khamidun](https://github.com/JHamidun) — design, content, AI media, engineering workflow, and knowledge work. Install only what you need.

## Quick start

```text
/plugin marketplace add JHamidun/claude-code-config-pack
/plugin                       # browse & enable plugins
/plugin install design-system@hamidun
```

Each plugin is self-contained (`skills/`, `agents/`, `commands/`, `hooks/`). Enable a plugin and its skills activate automatically when relevant — so a small, focused plugin keeps your context light.

> Looking for the old "drop everything into `~/.claude/`" pack? It still lives under [`.claude/`](.claude/) with `install.ps1` / `install.sh`. The marketplace below is the recommended, modular way to consume it.

## Catalog

### 🎨 Design & frontend
| Plugin | Description |
|--------|-------------|
| [design-system](plugins/design-system) | Tokens, color scales, type, dark mode, themes, brand kit. |
| [design-process](plugins/design-process) | Design taste, orchestration, critique, frontend presets, open-design. |
| [prototyping](plugins/prototyping) | Wireframes, interactive prototypes, component playground, sketch→HTML. |
| [ui-motion](plugins/ui-motion) | Microinteractions, animations, mobile overlays, live tweaks, a11y forms. |
| [design-io](plugins/design-io) | Figma import/export, PDF/PNG/PPTX export, dev handoff, perf & a11y audits. |
| [web-publish](plugins/web-publish) | Websites, HTML email, PWA shell, web assets, slides, dataviz, diagrams. |

### 🖼️ Content & media
| Plugin | Description |
|--------|-------------|
| [presentations](plugins/presentations) | Gamma, Manus slides, Marp, native PPTX. |
| [office-docs](plugins/office-docs) | DOCX, XLSX, PDF, EPUB, CSV analysis, file ops. |
| [video-media](plugins/video-media) | Video generation, avatars, edit/export, subtitles, transcripts. |
| [audio-voice](plugins/audio-voice) | Music (ACE-Step), TTS & cloning (ElevenLabs), transcription (Deepgram). |
| [image-gen](plugins/image-gen) | Nano Banana, DALL-E, Replicate, enhancement, OCR, stickers, generative art. |

### 📣 Social & marketing
| Plugin | Description |
|--------|-------------|
| [linkedin-suite](plugins/linkedin-suite) | Write, humanize, audit, plan LinkedIn posts; profile & comment tooling. |
| [social-intel](plugins/social-intel) | Trends, ad spy, TikTok intel, SimilarWeb, mentions monitoring, scraping. |
| [social-posting](plugins/social-posting) | Publish to X, Threads, Bluesky, Instagram, TikTok. |
| [content-writing](plugins/content-writing) | Content engine, de-AI, doc interlinking, RU proofreading. |
| [marketing-tools](plugins/marketing-tools) | Campaign planning, competitive analysis, SEO, performance analytics. |

### 🛠️ Engineering
| Plugin | Description |
|--------|-------------|
| [dev-core](plugins/dev-core) | Python/JS/TS dev, DB design, API docs, git workflow, architecture agents. |
| [dev-process](plugins/dev-process) | TDD, systematic debugging, planning, review, worktrees, parallel agents. |
| [code-health](plugins/code-health) | Bug/cleanup/deps/reuse/security audits, threat hunting. |
| [browser-testing](plugins/browser-testing) | Browser automation, webapp testing, test & perf agents. |
| [gsd](plugins/gsd) | Get Shit Done — phase-based dev framework (roadmaps, plans, execution, verify). |

### 🤖 AI & meta
| Plugin | Description |
|--------|-------------|
| [skill-dev](plugins/skill-dev) | Author skills/agents/plugins/MCP, prompt engineering, Claude API & CLI. |
| [ai-gateways](plugins/ai-gateways) | Route to GPT, Gemini, Kimi, DeepSeek, Perplexity. |

### 💼 Business & ops
| Plugin | Description |
|--------|-------------|
| [product-mgmt](plugins/product-mgmt) | Specs, roadmaps, metrics/OKR, research synthesis, stakeholder comms. |
| [sales-tools](plugins/sales-tools) | Account research, call prep, outreach, leads, battlecards. |
| [research-tools](plugins/research-tools) | Document Q&A, stock analysis, thinking frameworks, meeting analysis. |
| [google-workspace](plugins/google-workspace) | Gmail, Docs, Sheets, Drive, Calendar, Contacts, Tasks, Meet, Ads. |
| [integrations](plugins/integrations) | n8n, AWS, Telegram bots, Zoom, Pinecone, DeepL, server health, Outlook. |
| [session-tools](plugins/session-tools) | Memory, chat history, daily planning, reviews, model switching. |

## Credits & attribution

Most plugins are original work. A few are **adaptations of excellent open-source upstreams**, credited here and in each plugin's `UPSTREAM.md`:

- **gsd** — adapted from the **Get Shit Done** framework by TÂCHES, now community-maintained under [open-gsd](https://github.com/open-gsd/get-shit-done-redux).
- **dev-process** & parts of **skill-dev** — adapted from **[Superpowers](https://github.com/obra/superpowers)** by Jesse Vincent / Prime Radiant.
- **product-mgmt**, **sales-tools**, **marketing-tools** — adapted from Anthropic's **[knowledge-work-plugins](https://github.com/anthropics/knowledge-work-plugins)**.

These adaptations add house conventions, integration with the other plugins here, and documentation. Original authorship and upstream licenses are retained.

## License

MIT © [Zhemal Khamidun](https://github.com/JHamidun). Adapted components remain under their upstream licenses.
