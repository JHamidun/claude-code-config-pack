# Отключённые плагины (Pass-68)

Их содержимое влито в собственные скиллы — см. references/ в перечисленных ниже.
Вернуть любой: добавить строку в `settings.json` → `enabledPlugins`.

| Плагин | Почему выключен |
| ------ | --------------- |
| `figma@claude-plugins-official` | дубль своего figma-api + figma_api.py |
| `sentry@claude-plugins-official` | в routing.md не встречается, не используется |
| `finance@knowledge-work-plugins` | US GAAP/SOX не применимы вне США; из финансового в паке остаётся `metrics-tracking`. Нужен учёт своей юрисдикции — включай плагин или заводи свой навык |
| `legal@knowledge-work-plugins` | US-практика. Юридического навыка в паке нет вовсе (тот был построен на корп-подписках и договорах одной компании) — если тема нужна, включи плагин |
| `operations@knowledge-work-plugins` | ⚠️ был отключён ради своего `runbook`, а тот в пак не входит (писался под конкретный хост). Если нужны операционные процедуры — этот плагин имеет смысл включить |
| `data@knowledge-work-plugins` | 36 скиллов влиты в database-design/csv-analysis/verifier/d3-visualization |
| `explanatory-output-style@claude-plugins-official` | перебивает outputStyle=Proactive через SessionStart-хук |
