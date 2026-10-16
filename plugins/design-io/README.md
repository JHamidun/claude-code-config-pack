# Design I/O & QA

> Figma import/export, PDF/PNG/PPTX export, dev handoff, verify, perf & a11y audits.

Part of the **[hamidun marketplace](../../README.md)**.

## What's inside

| Skill | What it does |
|-------|--------------|
| `a11y-audit` | Прогон axe-core в headless: отчёт по WCAG-нарушениям готовой страницы. |
| `claude-design` | Claude Design (claude.ai/design): от AI-мокапа до production-кода, handoff-bundle. |
| `design-guardrails` | QA-гейт дизайн-артефакта: Visual Diff PASS/FAIL против референса, редизайн без поломки логики. |
| `dev-handoff` | Handoff-пакет разработчику из готового HTML: токены, компоненты, README. |
| `document-import` | Извлечь текст и картинки из PDF/DOCX/PPTX/скетча для прототипа или дека. |
| `export-pdf` | Печать HTML-макета или дека в PDF через headless Chrome (Playwright), слайд = страница. |
| `export-png` | PNG-скриншоты слайдов/экранов через Playwright: кадр на слайд или по селектору. |
| `export-pptx` | HTML-дек в PPTX: режим картинок (надёжный) или редактируемый (нативный текст, pptxgenjs). |
| `github-import` | Импорт файлов GitHub-репо как контекст: токены, компоненты, стили. |
| `i18n-stress-test` | Стресс-тест локализации перед сдачей макета: немецкий, арабский RTL, японский, emoji-переполнение. |
| `miro` | Доски Miro: MCP (чтение/саммари, layout-DSL, диаграммы, комменты) + REST v2 (коннекторы, теги — чего MCP не умеет). |
| `onboarding-ux` | Паттерны первого запуска: welcome, tour, empty-states. |
| `perf-audit` | Lighthouse в headless перед публикацией страницы: LCP, CLS, TBT, размер бандла, конкретные советы. |
| `proto-smoketest` | Smoke-тесты прототипа: 5-10 критичных путей не отвалились, не unit. |
| `screenshot-test` | Pixel-diff скриншота с эталоном в репо — падает при визуальной поломке; CI/pre-commit. |
| `verifier` | Готовый файл в headless перед сдачей: console-ошибки, скриншот, матрица проверок. |
| `version-snapshots` | Копии одного файла в .snapshots/ + MANIFEST.md — откат правки без git. |

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
