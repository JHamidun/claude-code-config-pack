# seo-machine-ru

Community-built [Claude Code](https://docs.anthropic.com/claude/docs/claude-code) skill —
**SEO / GEO / AEO контент-машина под русский поиск (Яндекс)**. Семантическое ядро →
написание → оптимизация → подготовка к публикации лонгридов и лендингов, плюс
оптимизация под AI-выдачу (Яндекс Нейро, Alice, GigaChat, ChatGPT, Perplexity) и
**рабочий рецепт реального Wordstat**.

> Скилл самодостаточен: движок внутри (Python, чистый stdlib + опц. `requests`/`python-docx`).
> Данные (Wordstat/Вебмастер/Метрика) и публикацию (CMS) подключаете своими — через `.env`.
> Никаких чужих кредов внутри нет.

## Что умеет

- **research** — семантическое ядро + топ-10 выдачи + гэпы → бриф.
- **cluster** — пиллар + 8–12 спутников + карта перелинковки (анти-каннибализация).
- **write** — статья 1500–3000 слов, AEO-структура (прямой ответ сверху + H2/H3 + FAQ).
- **optimize/audit** — on-page SEO 0–100, читаемость (Флеш-Оборнева), плотность с лемматизацией.
- **aeo** — попасть в цитирование AI-ответов (schema, извлекаемые блоки, атрибутируемые факты).
- **Wordstat (реальные частоты)** — через internal API с залогиненного браузера (Direct API обычно закрыт).
- **Word-отчёт** — упаковка ядра+статьи в `.docx` для маркетолога/стейкхолдера.

## Требования

- Claude Code (или совместимый агент со Skill-поддержкой).
- Python 3.10+ (`pip install requests python-docx` — для Wordstat-headless и Word-отчёта; ядро скриптов — stdlib).
- Свой аккаунт Яндекса (для Wordstat) — в `.env`.

## Установка

### Вариант A — скрипт
```powershell
# Windows
./install.ps1
```
```bash
# macOS / Linux
bash install.sh
```
Скрипт копирует папку скилла в `~/.claude/skills/seo-machine-ru/`.

### Вариант B — вручную
Скопируйте содержимое репозитория в `~/.claude/skills/seo-machine-ru/`.

### Вариант C — отдай это своему Claude Code
Открой Claude Code в любой папке и вставь промпт из [`DEPLOY.md`](DEPLOY.md) —
агент сам склонирует, разложит скилл, поставит зависимости и проверит установку.

## Настройка под себя (обязательно)

1. `cp .env.example .env` и впиши свой `YANDEX_LOGIN` / `YANDEX_PASSWORD`.
2. Заполни `context/product.md` — бренд, ICP, оффер, голос, уникальные данные.
3. (Опц.) `context/target-keywords.md`, `internal-links-map.md`, `ai-citation-targets.md`.

## Использование

В Claude Code: «собери семантическое ядро по теме X», «напиши SEO-статью под главный кластер»,
«почему страница не в топе». Скилл подхватится по описанию. Пошагово — `references/workflow.md`.

```bash
# примеры запуска скриптов напрямую
python scripts/opportunity_scorer.py keywords.json
python scripts/seo_quality_rater_ru.py drafts/article.md --kw "ключ"
python scripts/build_report_docx.py --title "Бренд — SEO" --out report.docx --draft drafts/article.md
```

## Структура

```
SKILL.md                  — точка входа для агента
context/                  — шаблоны под проект (product, ключи, перелинковка, AEO-цели)
references/               — workflow, чеклисты-роли, AEO/GEO, гайдлайны, Wordstat-рецепт
scripts/                  — Python-движок + Wordstat + Word-упаковщик
examples/                 — демо-прогон (фиктивный SaaS) — форма артефактов
.env.example              — какие переменные нужны (свои креды)
```

## Лицензия

MIT — см. [LICENSE](LICENSE). Локализованный порт идеи `seomachine` под RU/Яндекс.
