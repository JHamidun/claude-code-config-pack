# doc-coauthoring — откуда это и что с лицензией

Источник: <https://github.com/anthropics/skills>, каталог `skills/doc-coauthoring`.
Отметка в `SKILL.md`: `metadata.origin: anthropics/skills@fa0fa64`.
Изменён относительно первоисточника: `SKILL.md` (описание и триггеры переписаны
под маршрутизацию этого пака). Остальных файлов у навыка нет.

## Что проверено 23.08.2026 и почему здесь нет LICENSE.txt

В репозитории `anthropics/skills` **19 навыков**. У **18** из них рядом с кодом
лежит собственный `LICENSE.txt` — Apache License 2.0, `Copyright 2026 Anthropic,
PBC.`. У `doc-coauthoring` такого файла нет, и в корне репозитория общего
`LICENSE` тоже нет (GitHub API отдаёт `license: null`).

`README.md` первоисточника говорит: «Many skills in this repo are open source
(Apache 2.0)», и отдельно оговаривает как **не** open source ровно четыре
навыка — `docx`, `pdf`, `pptx`, `xlsx` («source-available, not open source»).
`doc-coauthoring` в это исключение не входит.

Положить сюда текст Apache-2.0 «по аналогии с соседями» — значит заявить о
предоставленном праве, которого первоисточник для ЭТОГО навыка не выразил.
Поэтому файл лицензии здесь не создан намеренно, а факт записан как есть.

**Решение владельца:** либо запросить у Anthropic подтверждение (issue в
репозитории первоисточника), либо не включать навык в раздачу до подтверждения.
