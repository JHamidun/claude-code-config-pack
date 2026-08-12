# Отключённые плагины (Pass-68)

Их содержимое влито в собственные скиллы — см. references/ в перечисленных ниже.
Вернуть любой: добавить строку в `settings.json` → `enabledPlugins`.

| Плагин | Почему выключен |
| ------ | --------------- |
| `figma@claude-plugins-official` | дубль своего figma-api + figma_api.py |
| `sentry@claude-plugins-official` | в routing.md не встречается, не используется |
| `finance@knowledge-work-plugins` | US GAAP/SOX не применимы; методология влита в brazil-accounting/moy-nalog/metrics-tracking |
| `legal@knowledge-work-plugins` | US-практика; матрицы риска и тиры переговоров влиты в company-lawyer |
| `operations@knowledge-work-plugins` | runbook создан свой, под флот your-server и bash-guard |
| `data@knowledge-work-plugins` | 36 скиллов влиты в database-design/csv-analysis/verifier/d3-visualization |
| `explanatory-output-style@claude-plugins-official` | перебивает outputStyle=Proactive через SessionStart-хук |
