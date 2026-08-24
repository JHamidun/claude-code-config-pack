---
description: Релиз вручную по шагам — bump версии, два чейнджлога, тег и пуш. Скрипта-автомата нет.
argument-hint: "[patch|minor|major] [-m message]"
---

# /push — релиз

**Автоматизации нет.** Команда раньше вызывала `bash .claude/scripts/release.sh` в
корне проекта. Такого файла в паке нет — ни в `~/.claude/scripts/`, ни где-либо ещё
(проверяется: `ls ~/.claude/scripts/release.sh`). Всё, что перечислено ниже, делается
руками по шагам — либо навыком `changelog-generator`, который закрывает пункты 2-3 и
умеет `gh release`.

Обещание без файла хуже прямого «не автоматизировано»: по нему идут и упираются в
`bash: .claude/scripts/release.sh: No such file or directory`. На Windows без Git Bash
до этой строки дело даже не дойдёт — оболочка сначала не найдёт `bash`, и человек
решит, что дело в нём.

## Шаги

1. **Синхронизировать версию с последним тегом** — иначе `package.json` и
   `git tag` разъезжаются, и следующий bump считается от неверной базы.
   ```bash
   git describe --tags --abbrev=0
   ```
2. **Собрать коммиты с прошлого релиза** и определить тип bump'а по conventional
   commits: `feat:` → minor, `fix:` → patch, `BREAKING CHANGE`/`!` → major.
   Аргумент `patch|minor|major` перебивает автоопределение.
   ```bash
   git log $(git describe --tags --abbrev=0)..HEAD --oneline
   ```
3. **Два чейнджлога** — у них разные читатели, поэтому и файлов два:
   - `CHANGELOG.md` — формат Keep a Changelog, для разработчиков, все коммиты.
   - `RELEASE_NOTES.md` — для людей: человеческие имена скоупов
     (auth → Authentication, db → Database), эмодзи по разделам
     (✨ Features, 🐛 Fixes, 🔒 Security), без `chore`/`ci`/`docs`.
4. **Проставить версию** во всех `package.json` монорепо (не только в корневом).
5. **Тег и пуш**:
   ```bash
   git tag -a vX.Y.Z -m "release: vX.Y.Z" && git push --follow-tags
   ```

## Откат

Автоматического rollback тоже нет. Если релиз испорчен до пуша — `git tag -d vX.Y.Z`
и `git reset` на релизный коммит. После пуша тег не переписывать: выпускать
следующий патч, иначе у тех, кто уже подтянул тег, останется другое содержимое.

## Что стоит сделать перед релизом

Незакоммиченное — отдельным коммитом с осмысленным префиксом, чтобы оно попало в
`RELEASE_NOTES.md`: `feat(worker): add worker readiness pre-flight system`.
Коммит без `feat:`/`fix:` в пользовательский чейнджлог не попадёт.
