# Фактчекинг через Perplexity Max: рабочий процесс

> Вынесено из тела навыка. Читать, когда на руках FACT-REPORT.md с флагами
> FABRICATION / DRIFT / NOT_FOUND по книге, лонгриду или статье — то есть
> нужно триажить пачку спорных утверждений, а не проверить один факт.

Типовой сценарий работы над non-fiction книгой или лонгридом: после internal fact-check пайплайна получаешь FACT-REPORT.md с флагами FABRICATION / DRIFT / NOT_FOUND. Перед тем как удалять — проверь через Perplexity Max.

### Пять типов ошибок, которые ловит Perplexity Max

| Тип | Пример из практики | Как ловится |
|-----|--------------------|-------------|
| **Фабрикация** | ConsultingFirm1 «3x успешность с change management» — цифра не существует | Запрос «confirm ConsultingFirm1 finding X» → «I could not verify» + список реальных цифр (12% vs 5%, ~2.4×) |
| **Source mix-up** | «ConsultingFirm2 обзор 2026, 5%/60%» — реально это «Widening AI Value Gap» сентябрь 2025 | Запрос с цифрами → правильное название отчёта + URL |
| **Name correction** | В тексте автор исследования назван неверно (перепутаны имя/фамилия или атрибуция) | Запрос про человека → реальное имя в источниках |
| **Factual error** | IBM PC «1985» → реально 1981 (запуск 12 августа 1981) | Запрос «when was IBM PC launched» → точная дата |
| **False fabrication flag** | Cambridge «Feedback of Flattery» — fact-checker пометил как fabrication, но исследование РЕАЛЬНОЕ | Запрос «does X study exist» → URL + полная цитата |

### Pattern: триаж FABRICATION-флагов

```bash
# Для каждой главы с BLOCK вердиктом:
# 1. Прочитать FACT-REPORT.md, выделить FABRICATION items
# 2. Запустить параллельные pplx-max queries:

for claim in "$@"; do
  nohup python ~/.claude/skills/perplexity/pplx-max.py \
    "Verify: $claim. Provide URL if real, or confirm fabrication." \
    > "/tmp/pplx-$$-$RANDOM.log" 2>&1 &
done
wait

# 3. Применить фиксы:
#    - Если REAL → добавить в SOURCES.md, оставить текст
#    - Если FABRICATION → удалить или заменить на верифицированную цифру
#    - Если NAME WRONG → исправить
```

### Промпт-формулы для фактчекинга

| Цель | Формула |
|------|---------|
| Подтверждение существования | `"Does X study/report by Y exist? URL if yes, no if fabrication."` |
| Точные цифры | `"Confirm exact figures from X report: A%, B%. Provide URL."` |
| Имя автора | `"Who is the lead author of X publication? Full name and affiliation."` |
| Дата события | `"When exactly was X launched/published? Exact date with source."` |
| Real quote | `"Did Y publicly say Z? Provide direct quote and source link."` |

### Source-добавление в SOURCES.md после верификации

Если Perplexity подтвердил спорный факт — добавь источник в SOURCES.md по шаблону:

```markdown
- **«Точное название отчёта»** — Org, Date.
  https://exact-url
  **Что важно:** конкретная цитата/цифра из отчёта (по чему его вспоминать).
  **Какой тезис главы поддерживает:** один-два предложения о том, что именно подтверждается.
```

После этого fact-checker при следующем прогоне найдёт источник в SOURCES.md и снимет FABRICATION-флаг.

### Когда НЕ доверять Perplexity Max

1. **Контркстно близкие, но разные исследования** — Perplexity иногда подтверждает «похожий» факт, не указывая что это другой отчёт. Всегда проверяй точное название.
2. **Regional sources** — for non-English content, indexing quality varies; for verification of regional companies/figures, add an explicit "Regional sources OK" hint to the prompt.
3. **Закрытые отчёты** — Gartner / Forrester / IDC paywalled. Perplexity видит только пресс-релизы — детали могут отличаться.
4. **Статистика < 6 месяцев старая** — для совсем свежих данных лучше `--mode "deep research"` или прямой первоисточник.
