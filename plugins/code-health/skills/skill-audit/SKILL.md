---
name: skill-audit
description: "Заглушка: проверка чужого скилла/плагина до установки переехала в skill-manager, режим «Аудит». Сам не вызывается, держит старые ссылки живыми."
disable-model-invocation: true
metadata:
  version: 2.0.0
  updated: 2026-09-23
---

# skill-audit → skill-manager

Перенесено в навык `skill-manager`, режим **«Аудит»**
(`~/.claude/skills/skill-manager/references/audit.md`): там паспорт репозитория и
таблица лицензий, таблица правил, флаги `--allow` / `--min-severity`, «сканер ловит
сам себя», плюс вторая линия NVIDIA SkillSpector (необязательная, установка —
`references/skillspector-setup.md`) и смысловой разбор.

Полный аудит (локальный сканер leak-scan + NVIDIA, отчёт в scratchpad сессии, не в
`~/.claude/skills`):

```bash
python -I -B ~/.claude/skills/skill-manager/scripts/audit_skill.py <цель> --output <scratchpad>/skill-audit/<имя>/report.json
```

Без SkillSpector аудит всё равно прогоняет локальную линию, а NVIDIA помечает как
`unavailable` (код выхода 2): это неполный аудит, а не чистый.

Быстрый скан одним локальным сканером leak-scan (36 правил):

```bash
python ~/.claude/skills/leak-scan/scripts/skill_injection_scan.py <цель>
```
