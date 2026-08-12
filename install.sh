#!/usr/bin/env bash
# Claude Code config pack installer (macOS / Linux)
#
# === ГЛАВНЫЙ ИНВАРИАНТ: установщик НИКОГДА не стирает и не переносит ~/.claude ===
# Твоё дерево ~/.claude остаётся на месте. Пак кладётся ПОВЕРХ копированием (merge).
# Никаких mv/rm всего каталога — раньше `--backup` делал `mv ~/.claude ~/.claude.backup.*`,
# то есть ПЕРЕНОСИЛ твой конфиг; если что-то падало посреди установки, ты оставался
# без ключей, памяти и истории сессий. Этот режим удалён целиком.
#
# Два режима merge:
#   add-missing (ПО УМОЛЧАНИЮ) — докладываем ТОЛЬКО отсутствующие файлы; всё, что уже
#                                 есть у тебя (любой версии), не трогаем вообще.
#   repair (--repair)          — перезаписываем НАШИ базовые файлы свежими.
# preserve-list (ключи, память, история чатов, tg-сессия, settings.local.json, ~/CLAUDE.md)
# защищён в ОБОИХ режимах, включая --repair.
#
# Полная копия-бэкап ~/.claude делается ПЕРВОЙ операцией и ПО УМОЛЧАНИЮ. Это сейф-нет,
# а НЕ единственная копия: неполный бэкап (занятый файл) = предупреждение, не остановка,
# потому что оригинал никуда не переносится.
#
# Всё разложенное записывается в ~/.claude/.ccpack-manifest.txt — по нему uninstall.sh
# удаляет РОВНО то, что положил пак, и ничего больше.
set -uo pipefail

MODE="add-missing"
BACKUP=1
SKIP_DEPS=0
DRY=0

usage() {
    cat <<'USAGE'
Usage: ./install.sh [--repair] [--no-backup] [--skip-deps] [--dry-run]

  (без флагов)   добавить только НЕДОСТАЮЩИЕ файлы; существующее не трогать.
                 Резервная копия ~/.claude делается автоматически (копия, не перенос).
  --repair       перезаписать НАШИ базовые файлы свежими. Пользовательское
                 (ключи, память, история, settings.local.json, ~/CLAUDE.md) всё равно не трогается.
  --no-backup    не делать резервную копию ~/.claude (НЕ рекомендуется).
  --skip-deps    не ставить Python-зависимости (pip install --user -r requirements.txt).
  --dry-run      только показать, что будет сделано; ничего не менять.

Удаление: ./uninstall.sh (удаляет только то, что положил этот установщик).
USAGE
}

for arg in "$@"; do
    case "$arg" in
        --repair)      MODE="repair" ;;
        --no-backup)   BACKUP=0 ;;
        --skip-deps)   SKIP_DEPS=1 ;;
        --dry-run)     DRY=1 ;;
        -h|--help)     usage; exit 0 ;;
        --backup)
            echo "ПРИМЕЧАНИЕ: --backup больше не нужен — резервная копия делается по умолчанию"
            echo "            и теперь это КОПИЯ, а не перенос ~/.claude." ;;
        --force)
            echo "ОШИБКА: --force удалён. Раньше он затирал ~/CLAUDE.md без спроса." >&2
            echo "        Если нужно обновить наши базовые файлы — ./install.sh --repair" >&2
            echo "        (~/CLAUDE.md всё равно не перезаписывается: это твой файл)." >&2
            exit 2 ;;
        *)
            echo "ОШИБКА: неизвестный аргумент: $arg" >&2; usage >&2; exit 2 ;;
    esac
done

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SRC_CLAUDE="$HERE/.claude"
SRC_CLAUDE_MD="$HERE/CLAUDE.md"
SRC_ENV_TEMPLATE="$HERE/.credentials.template.env"
DST_CLAUDE="$HOME/.claude"
DST_CLAUDE_MD="$HOME/CLAUDE.md"
DST_ENV="$DST_CLAUDE/.credentials.master.env"
MANIFEST="$DST_CLAUDE/.ccpack-manifest.txt"

[ -d "$SRC_CLAUDE" ] || { echo "ОШИБКА: не найден $SRC_CLAUDE" >&2; exit 1; }

# --- preserve-list: ПОЛЬЗОВАТЕЛЬСКОЕ, не перезаписываем ни в одном режиме ---------------
# .credentials.master.env / .credentials.json — все твои API-ключи и OAuth Claude Code.
# settings.local.json — твои локальные настройки (settings.json — наш базовый, его обновляем).
# MEMORY.md + memory/ — авто-память. projects/ — история сессий (самое невосстановимое).
# todos/, shell-snapshots/ — рантайм сессий. chats.db* — база чатов (+ -wal/-shm/-journal).
# tg_session.session* — авторизация Telegram-клиента.
hm_is_preserved() {
    case "/$1" in
        */.credentials.master.env|*/.credentials.json|*/settings.local.json|*/MEMORY.md) return 0 ;;
        */chats.db*|*/tg_session.session*) return 0 ;;
        */.ccpack-manifest.txt) return 0 ;;
    esac
    # user-profile.md — файл-анкета: пак везёт ПУСТОЙ шаблон («Your Name»), а установщик
    # прямым текстом просит вписать туда имя, почту, телефон. Это пользовательские данные,
    # поэтому обращаемся как с ~/CLAUDE.md: кладём только если нет, не перезаписываем
    # никогда — иначе --repair менял живую анкету обратно на «Your Name».
    # Якорим к ТОЧНОМУ месту — rules/user-profile.md от корня .claude. Шаблон
    # `*/rules/user-profile.md` совпал бы на любой глубине, и одноимённый файл пака
    # (например .claude/get-shit-done/templates/user-profile.md) не разложился бы, хотя
    # rsync-исключение --exclude=/rules/user-profile.md его пропускает: две ветки
    # копирования разошлись бы в поведении. На Windows этот же промах уже съедал файл.
    case "$1" in
        rules/user-profile.md) return 0 ;;
    esac
    # Каталоги пользовательских данных сверяем ТОЛЬКО на первом уровне ~/.claude ($1 идёт
    # от корня .claude). Без якоря имя совпадало на любой глубине, и собственный каталог
    # пака templates/memory/ молча не раскладывался: файлы, которые пак ОБЯЗАН положить,
    # попадали под правило «не трогать память». Данные человека лежат ровно в
    # ~/.claude/memory, projects, todos, shell-snapshots — этого якоря достаточно.
    case "$1" in
        memory/*|projects/*|todos/*|shell-snapshots/*) return 0 ;;
    esac
    return 1
}
PRESERVE_RSYNC=(
    --exclude=.credentials.master.env --exclude=.credentials.json
    --exclude=settings.local.json --exclude=MEMORY.md
    --exclude='chats.db*' --exclude='tg_session.session*'
    --exclude=.ccpack-manifest.txt
    --exclude=/rules/user-profile.md
    # Ведущий слэш якорит правило к корню передачи (~/.claude). Без него rsync режет
    # каталог с таким именем на ЛЮБОЙ глубине — и templates/memory/ из пака не доезжал.
    --exclude=/memory/ --exclude=/projects/ --exclude=/todos/ --exclude=/shell-snapshots/
)
# В резервную копию секреты НЕ кладём: копий храним 3 ротируемые, ключи и tg-сессия
# размножались бы в трёх экземплярах рядом с ~/.claude. Оригиналы при этом целы —
# merge их не перезаписывает (они в preserve-list).
BACKUP_EXCLUDES=(--exclude=.credentials.master.env --exclude=.credentials.json --exclude='tg_session.session*')

# --- временный каталог (нужен уже для скана ссылок) --------------------------------------
TMPD="$(mktemp -d "${TMPDIR:-/tmp}/ccpack.XXXXXX" 2>/dev/null)" || TMPD=""
[ -n "$TMPD" ] || { echo "ОШИБКА: не удалось создать временный каталог." >&2; exit 1; }
# HM_TMPFILE — файл, в который прямо сейчас идёт запись (см. hm_copy: пишем во временный
# файл рядом с целью и переименовываем). Если нас прервали ровно между cp и mv, мусор
# остался бы в ~/.claude — убираем его на любом выходе, включая Ctrl+C.
HM_TMPFILE=""
hm_cleanup() {
    rm -rf "$TMPD" 2>/dev/null
    [ -n "$HM_TMPFILE" ] && rm -f "$HM_TMPFILE" 2>/dev/null
    return 0
}
trap 'hm_cleanup' EXIT
trap 'hm_cleanup; exit 130' INT
trap 'hm_cleanup; exit 143' TERM

# --- symlink-защита: РЕКУРСИВНЫЙ скан всего дерева ~/.claude -----------------------------
# Любой каталог ИЛИ файл внутри ~/.claude мог быть слинкован тобой на свой git-репо или
# облако — и вовсе не обязательно на первом уровне: ~/.claude/agents/health,
# ~/.claude/config/rules-ref/hooks.md — такие же обычные случаи.
# Писать СКВОЗЬ ссылку нельзя: rsync/cp уходят по ней и затирают ВНЕШНЮЮ цель, а
# восстановить её будет НЕОТКУДА — резервная копия сохраняет ссылки КАК ССЫЛКИ, содержимого
# внешней цели в ней нет (и не должно быть: иначе копия растёт бесконечно). Защита ДО
# записи — единственная, поэтому скан рекурсивный: собираем КАЖДУЮ ссылку на ЛЮБОЙ глубине,
# и запись запрещаем, если ссылкой оказалось хотя бы ОДНО ЗВЕНО пути назначения.
# Раньше проверялись только непосредственные дети ~/.claude и дети skills/ — ссылка на
# глубине 2 вне skills/ не обнаруживалась, и --repair молча затирал внешний файл.
LINK_RELS=()
LINK_N=0
LINK_HIT=""
scan_links() {
    local p rel
    # Функцию вызываем ДВАЖДЫ: один раз в начале (для dry-run и для решения, можно ли
    # вообще пользоваться rsync) и второй раз вплотную к записи — см. «ЛОСС 5» ниже.
    # Поэтому список каждый раз собираем заново, а не дописываем к прежнему.
    LINK_RELS=()
    LINK_N=0
    [ -e "$DST_CLAUDE" ] || return 0
    # find -P (режим по умолчанию) НЕ разыменовывает ссылки: сама ссылка попадает в вывод
    # как -type l, но ВНУТРЬ её цели обход не заходит — уйти по ссылке в чужое дерево или
    # зациклиться невозможно. Стартовая точка с завершающим слэшем: если ссылкой оказался
    # сам ~/.claude, без слэша find напечатал бы только его и не заглянул внутрь.
    # projects/, todos/, shell-snapshots/, memory/ пропускаем: пак туда не пишет ни в одном
    # режиме (preserve-list), а на живой машине это десятки тысяч файлов.
    find -P "$DST_CLAUDE/" -mindepth 1 \
        -path "$DST_CLAUDE/projects" -prune -o \
        -path "$DST_CLAUDE/todos" -prune -o \
        -path "$DST_CLAUDE/shell-snapshots" -prune -o \
        -path "$DST_CLAUDE/memory" -prune -o \
        -type l -print0 > "$TMPD/links.raw" 2>/dev/null || return 1
    while IFS= read -r -d '' p; do
        rel="${p#"$DST_CLAUDE"}"; rel="${rel#/}"; rel="${rel#/}"
        [ -n "$rel" ] || continue
        LINK_RELS+=("$rel")
        LINK_N=$((LINK_N+1))
    done < "$TMPD/links.raw"
    return 0
}
if ! scan_links; then
    # Сбой скана = fail-closed. Не зная, где ссылки, писать нельзя вообще.
    echo "ОШИБКА: не удалось просмотреть $DST_CLAUDE на симлинки — установка прервана," >&2
    echo "        чтобы не записать сквозь ссылку в твой внешний каталог. Ничего не изменено." >&2
    echo "        Обычная причина — нет прав на чтение какого-то подкаталога ~/.claude." >&2
    exit 1
fi

is_link_excluded() {   # $1 = relpath внутри .claude; 0 = сам путь ИЛИ любой его предок — ссылка
    local rel="$1" k
    for k in ${LINK_RELS[@]+"${LINK_RELS[@]}"}; do
        case "$rel" in "$k"|"$k"/*) LINK_HIT="$k"; return 0 ;; esac
    done
    return 1
}

# Проверка ПЕРЕД КАЖДЫМ cp (ветка hm_copy) и перед точечными копированиями ниже:
# сканом мы знаем ссылки на момент старта, а этот тест смотрит на диск прямо сейчас —
# ловит и ссылку, созданную уже после скана.
hm_dst_link_in_path() {   # $1 = relpath внутри .claude; 0 = какое-то ЗВЕНО пути — ссылка
    local rel="$1" acc="" comp oldifs
    oldifs="$IFS"; IFS='/'; set -- $rel; IFS="$oldifs"
    for comp in "$@"; do
        [ -n "$comp" ] || continue
        acc="${acc:+$acc/}$comp"
        if [ -L "$DST_CLAUDE/$acc" ]; then LINK_HIT="$acc"; return 0; fi
    done
    return 1
}

LINK_RSYNC=()
RSYNC_SAFE=1
build_rsync_link_excludes() {
    local k
    LINK_RSYNC=()
    RSYNC_SAFE=1
    for k in ${LINK_RELS[@]+"${LINK_RELS[@]}"}; do
        LINK_RSYNC+=("--exclude=/$k")
        # В шаблонах rsync символы * ? [ — подстановка, а не буквальный текст: путь с таким
        # символом исключился бы не тот или не исключился вовсе. Для такого дерева rsync не
        # используем вообще — копируем пофайлово, с проверкой перед каждым cp (fail-closed).
        case "$k" in *'*'*|*'?'*|*'['*) RSYNC_SAFE=0 ;; esac
    done
    return 0
}
build_rsync_link_excludes

# --- ЖЁСТКИЕ ССЫЛКИ (hardlink): только для отчёта, защита встроена в саму запись ---------
# Жёсткая ссылка — это ВТОРОЕ ИМЯ того же файла (того же inode), а не отдельная копия.
# Признака «это ссылка» у неё нет: [ -L ] про неё ничего не знает, рекурсивный скан выше
# её не видит — оба имени равноправны. Поэтому обычная перезапись «на месте»
# (cp поверх существующего файла) меняет содержимое ПО ОБОИМ именам сразу: человек правит
# наш файл в ~/.claude, а меняется и его собственный файл где-нибудь в ~/work/config.json.
# Восстановить его неоткуда — резервная копия хранит ~/.claude, а не внешнее имя.
#
# Чинится это не детектированием, а способом записи: пишем во ВРЕМЕННЫЙ файл рядом с целью
# и переименовываем поверх (см. hm_copy). rename заменяет запись в каталоге, а не содержимое
# inode, — второе имя остаётся при своём старом содержимом. Ровно так же (temp+rename)
# работает rsync, поэтому его ветка была безопасна изначально.
# Ниже — только СПИСОК таких файлов, чтобы честно сказать человеку: «у этого файла было
# два имени, наша версия легла в ~/.claude, второе имя осталось прежним».
# find -links +1 есть и в GNU findutils, и в BSD/macOS find — одинаково.
HARDLINKS="$TMPD/hardlinks.txt"
: > "$HARDLINKS"
scan_hardlinks() {
    local p rel
    [ -e "$DST_CLAUDE" ] || return 0
    find -P "$DST_CLAUDE/" -mindepth 1 \
        -path "$DST_CLAUDE/projects" -prune -o \
        -path "$DST_CLAUDE/todos" -prune -o \
        -path "$DST_CLAUDE/shell-snapshots" -prune -o \
        -path "$DST_CLAUDE/memory" -prune -o \
        -type f -links +1 -print0 > "$TMPD/hardlinks.raw" 2>/dev/null || return 1
    while IFS= read -r -d '' p; do
        rel="${p#"$DST_CLAUDE"}"; rel="${rel#/}"; rel="${rel#/}"
        [ -n "$rel" ] || continue
        printf '%s\n' "$rel" >> "$HARDLINKS"
    done < "$TMPD/hardlinks.raw"
    return 0
}

report_links() {   # $1 = префикс строки
    local k
    for k in ${LINK_RELS[@]+"${LINK_RELS[@]}"}; do
        echo "$1~/.claude/$k — ссылка: пропускаю ВЕСЬ этот путь (внешнюю цель не трогаю)"
    done
    [ "$LINK_N" -gt 0 ] && echo "$1ссылок найдено: $LINK_N — ни один файл под ними не записывается"
    return 0
}

# --- dry-run ветвится ДО любой мутации --------------------------------------------------
if [ "$DRY" -eq 1 ]; then
    echo "[dry-run] Режим: $MODE"
    if [ "$BACKUP" -eq 1 ] && [ -d "$DST_CLAUDE" ]; then
        echo "[dry-run] WOULD: копия-бэкап $DST_CLAUDE -> $DST_CLAUDE.backup.<stamp> (КОПИЯ, не перенос; без ключей и tg-сессии; храню 3 последние)"
    fi
    if [ "$MODE" = "add-missing" ]; then
        echo "[dry-run] WOULD: скопировать в $DST_CLAUDE ТОЛЬКО недостающие файлы; существующее не трогать"
    else
        echo "[dry-run] WOULD: перезаписать в $DST_CLAUDE наши базовые файлы; пользовательское (preserve-list) не трогать"
    fi
    [ -f "$DST_CLAUDE_MD" ] && echo "[dry-run] ~/CLAUDE.md уже есть — НЕ трогаю (твой файл)" || echo "[dry-run] WOULD: создать ~/CLAUDE.md (сейчас его нет)"
    [ -f "$DST_ENV" ] && echo "[dry-run] ~/.claude/.credentials.master.env уже есть — НЕ трогаю" || echo "[dry-run] WOULD: создать .credentials.master.env из шаблона"
    report_links "[dry-run] "
    # Про жёсткие ссылки честно предупреждаем ЗАРАНЕЕ: в --repair такой файл будет
    # переписан как новый, и связь между двумя именами разорвётся. Данные не пропадут
    # (второе имя останется со старым содержимым), но человек должен знать до запуска.
    if [ "$MODE" = "repair" ] && scan_hardlinks && [ -s "$HARDLINKS" ]; then
        DRY_HL=0
        while IFS= read -r rel; do
            [ -n "$rel" ] || continue
            hm_is_preserved "$rel" && continue
            is_link_excluded "$rel" && continue
            [ -f "$SRC_CLAUDE/$rel" ] || continue
            DRY_HL=$((DRY_HL+1))
            [ "$DRY_HL" -le 10 ] && echo "[dry-run] ~/.claude/$rel — у файла есть второе имя (жёсткая ссылка): запишем новый файл, второе имя останется прежним"
        done < "$HARDLINKS"
        [ "$DRY_HL" -gt 10 ] && echo "[dry-run] ... и ещё $((DRY_HL - 10)) таких файлов"
        [ "$DRY_HL" -gt 0 ] && echo "[dry-run] файлов с несколькими жёсткими ссылками: $DRY_HL"
    fi
    echo "[dry-run] WOULD: записать список разложенного в $MANIFEST"
    [ "$SKIP_DEPS" -eq 1 ] || echo "[dry-run] WOULD: pip install --user -r requirements.txt"
    echo "[dry-run] Изменений не внесено."
    exit 0
fi

# --- 1. Резервная копия — ПЕРВАЯ мутирующая операция ------------------------------------
# Это КОПИЯ. Оригинал остаётся на месте, поэтому неполный бэкап не фатален.
if [ "$BACKUP" -eq 1 ] && [ -d "$DST_CLAUDE" ]; then
    STAMP=$(date +%Y%m%d-%H%M%S)
    BACKUP_DIR="$DST_CLAUDE.backup.$STAMP"
    echo "Резервная копия ~/.claude -> $BACKUP_DIR (без ключей и tg-сессии; храню 3 последние)..."
    BACKUP_OK=0
    if command -v rsync >/dev/null 2>&1; then
        rsync -a "${BACKUP_EXCLUDES[@]}" "$DST_CLAUDE/" "$BACKUP_DIR/" 2>/dev/null && BACKUP_OK=1
    else
        # -P: симлинки копируем как симлинки, а не тянем содержимое внешней цели в копию.
        if cp -RP "$DST_CLAUDE" "$BACKUP_DIR" 2>/dev/null; then
            if find "$BACKUP_DIR" \( -name '.credentials.master.env' -o -name '.credentials.json' -o -name 'tg_session.session*' \) -exec rm -f {} + 2>/dev/null; then
                BACKUP_OK=1
            else
                # Копию с ключами держать нельзя — fail-closed.
                rm -rf "$BACKUP_DIR" 2>/dev/null
                echo "ВНИМАНИЕ: не удалось исключить секреты из копии — копия удалена (оригинал ~/.claude цел)."
            fi
        fi
    fi
    if [ "$BACKUP_OK" -eq 1 ]; then
        # Маркер «эту копию сделали мы» — по нему и только по нему ретенция ниже имеет
        # право её удалить. Чужой каталог с похожим именем (в том числе перенесённый
        # ~/.claude от прежних версий пака) маркера не имеет и переживёт любое число
        # прогонов. Пишем СРАЗУ после успешного копирования, до любой ретенции.
        # self: — ПОЛНЫЙ путь самой копии. По нему ретенция отличает свой ротируемый слот
        # от копии этого же каталога, сделанной человеком: при cp -r маркер переезжает,
        # а путь в нём остаётся прежним и перестаёт совпадать с фактическим.
        printf 'claude-config-pack backup\ncreated: %s\nsource: %s\nself: %s\n' \
            "$STAMP" "$DST_CLAUDE" "$BACKUP_DIR" > "$BACKUP_DIR/.ccpack-backup" 2>/dev/null || \
            echo "  (маркер копии записать не удалось — эта копия не будет удаляться ретенцией)"
        SRC_N=$(find "$DST_CLAUDE" ! -name '.credentials.master.env' ! -name '.credentials.json' ! -name 'tg_session.session*' 2>/dev/null | wc -l | tr -d ' ')
        DST_N=$(find "$BACKUP_DIR" 2>/dev/null | wc -l | tr -d ' ')
        if [ "${DST_N:-0}" -lt "${SRC_N:-0}" ]; then
            if [ "$MODE" = "repair" ]; then
                # В repair мы ПЕРЕЗАПИСЫВАЕМ свои базовые файлы. Неполная копия означает,
                # что часть из них не сохранена нигде: у человека может быть свой
                # settings.json, свои hooks/, свои rules/*.md с теми же именами.
                echo "ОШИБКА: копия неполная, а --repair перезаписывает файлы. Прерываю ДО изменений." >&2
                echo "  Неполная копия: скопировано $DST_N из $SRC_N. Освободи место / закрой Cursor и Claude, потом повтори." >&2
                echo "  Без --repair (обычный запуск) установка безопасна и в этом случае: она только докладывает недостающее." >&2
                exit 1
            fi
            echo "ВНИМАНИЕ: копия неполная (часть файлов занята/недоступна). НЕ критично: обычный режим только докладывает недостающее, существующее не трогает. Продолжаю."
        fi
    else
        # ГЛАВНОЕ РАЗЛИЧИЕ РЕЖИМОВ. Фраза «оригинал на месте» верна ТОЛЬКО для add-missing:
        # там мы ничего не перезаписываем, поэтому отсутствие копии ничем не грозит.
        # В repair оригинал именно перезаписывается — и без копии файл человека,
        # совпавший по имени с файлом пака, не остаётся НИГДЕ. Раньше здесь оба режима
        # шли дальше с одинаково успокаивающим текстом, а в финале печаталось
        # «Прежняя версия — в резервной копии выше», хотя копии не было вовсе.
        if [ "$MODE" = "repair" ]; then
            echo "ОШИБКА: резервную копию снять не удалось, а --repair перезаписывает файлы. Прерываю ДО изменений." >&2
            echo "  Причина обычно одна из: нет места на диске, квота, HOME только для чтения, сетевой профиль." >&2
            echo "  Устрани причину и повтори. Либо запусти БЕЗ --repair: обычный режим только докладывает" >&2
            echo "  недостающее и существующие файлы не трогает, поэтому копия там не критична." >&2
            exit 1
        fi
        echo "ВНИМАНИЕ: снять копию не удалось. НЕ критично: обычный режим только докладывает недостающее, существующее не трогает. Продолжаю."
        # Копию БЕЗ ЕДИНОГО ФАЙЛА убираем: она ничего не хранит, но занимает один из трёх
        # слотов ретенции и на следующих прогонах вытесняет РАБОЧУЮ копию. Частичную копию
        # (хоть один файл) оставляем — неполный сейф-нет лучше, чем никакого.
        if [ -d "$BACKUP_DIR" ] && [ -z "$(find "$BACKUP_DIR" -type f -print -quit 2>/dev/null)" ]; then
            case "$BACKUP_DIR" in
                "$DST_CLAUDE".backup.*) rm -rf "$BACKUP_DIR" 2>/dev/null || : ;;
            esac
        fi
        BACKUP_DIR=""
    fi
    # Ретенция: 3 последние копии. Имя .backup.<YYYYMMDD-HHMMSS> => лексикографический
    # порядок = хронологический. Без ретенции каждый повторный прогон оставлял бы
    # полную копию ~/.claude навсегда.
    #
    # УДАЛЯЕМ ТОЛЬКО СВОИ КОПИИ — по маркеру .ccpack-backup внутри.
    # Раньше здесь сносилось ВСЁ, что подошло под маску имени, без вопроса «мы ли это
    # создали». Цена ошибки максимальная: ПРЕДЫДУЩИЕ версии этого же пака делали
    # `mv ~/.claude ~/.claude.backup.<stamp>`, то есть у человека, который ставит пак
    # поверх старой установки, такой каталог — ЕДИНСТВЕННАЯ копия прежнего конфига:
    # история сессий (projects/), память (memory/), chats.db, ключи. Три обычных прогона
    # установки уничтожали её молча, ни строкой не предупредив.
    # Каталог без маркера считаем ЧУЖИМ и не трогаем никогда — лучше оставить лишнее,
    # чем стереть единственное.
    ls -d "$DST_CLAUDE".backup.* 2>/dev/null | sort -r | tail -n +4 | while IFS= read -r old; do
        case "$old" in
            "$DST_CLAUDE".backup.*)
                [ -d "$old" ] || continue
                # Маркера НЕДОСТАТОЧНО: он отвечает «этот каталог сделал наш код», а не
                # «это наш ротируемый слот». Человек мог скопировать нашу копию себе
                # (cp -r ~/.claude.backup.X ~/.claude.backup.мой-архив) и дописать туда
                # своё — маркер переехал вместе с файлами, и ретенция снесла бы чужое молча.
                # Поэтому сверяем ПУТЬ, записанный в маркере при создании, с фактическим:
                # у копии он не совпадёт. Не смогли прочитать — считаем чужим.
                if [ ! -f "$old/.ccpack-backup" ]; then
                    echo "  Оставляю $old — копия создана не нами (нет маркера .ccpack-backup)."
                    echo "  Если она не нужна, удали вручную: rm -rf \"$old\""
                    continue
                fi
                marked_self=$(sed -n 's/^self: //p' "$old/.ccpack-backup" 2>/dev/null | head -1)
                if [ "$marked_self" = "$old" ]; then
                    rm -rf "$old"
                else
                    echo "  Оставляю $old — маркер указывает на другой путь (это копия нашей копии, а не наш слот)."
                    echo "  Если она не нужна, удали вручную: rm -rf \"$old\""
                fi
                ;;
        esac
    done
elif [ "$BACKUP" -eq 0 ] && [ -d "$DST_CLAUDE" ]; then
    echo "ВНИМАНИЕ: --no-backup — резервная копия ~/.claude НЕ делается."
fi

mkdir -p "$DST_CLAUDE" || { echo "ОШИБКА: не удалось создать $DST_CLAUDE" >&2; exit 1; }

report_links "  "

# --- 2. Список файлов источника + снимок «что уже было» ДО копирования -------------------
SRC_LIST="$TMPD/src.txt"; PRE_LIST="$TMPD/pre.txt"; PREV_LIST="$TMPD/prev.txt"
OURS_LIST="$TMPD/ours.txt"; STATS="$TMPD/stats.txt"
: > "$SRC_LIST"; printf '#\n' > "$PRE_LIST"; printf '#\n' > "$PREV_LIST"

MANIFEST_OK=1
if ! ( cd "$SRC_CLAUDE" && find . -type f ) > "$TMPD/raw.txt" 2>/dev/null; then
    MANIFEST_OK=0
    echo "ВНИМАНИЕ: не удалось перечислить файлы источника — список разложенного не будет обновлён (uninstall.sh не тронет эти файлы)."
fi
if [ "$MANIFEST_OK" -eq 1 ]; then
    while IFS= read -r rel; do
        rel="${rel#./}"
        [ -n "$rel" ] || continue
        hm_is_preserved "$rel" && continue
        is_link_excluded "$rel" && continue
        printf '%s\n' ".claude/$rel" >> "$SRC_LIST"
        [ -e "$DST_CLAUDE/$rel" ] && printf '%s\n' ".claude/$rel" >> "$PRE_LIST"
    done < "$TMPD/raw.txt"
    # Что мы клали в прошлые прогоны (из старого манифеста).
    if [ -f "$MANIFEST" ]; then
        awk -F'\t' '!/^#/ && NF>=3 {print $3}' "$MANIFEST" >> "$PREV_LIST" 2>/dev/null || :
    fi
fi

# --- 3. Merge-копия ПОВЕРХ ~/.claude (без переноса и стирания) ---------------------------
COPY_FAILED=0
# Про ссылки из скана уже сказал report_links выше — здесь докладываем только про те,
# что появились ПОСЛЕ скана; повторять один и тот же список дважды незачем.
LINK_SEEN=""
for k in ${LINK_RELS[@]+"${LINK_RELS[@]}"}; do LINK_SEEN="$LINK_SEEN|$k|"; done
hm_note_link() {   # печатаем про каждую ссылку ОДИН раз, а не про каждый файл под ней
    case "$LINK_SEEN" in
        *"|$LINK_HIT|"*) : ;;
        *) LINK_SEEN="$LINK_SEEN|$LINK_HIT|"
           echo "  ~/.claude/$LINK_HIT — ссылка (появилась после проверки): пропускаю весь путь." ;;
    esac
}
hm_copy() {   # $1=src $2=dst $3=missing|overwrite — фолбэк без rsync
    local src="$1" dst="$2" mode="$3" rc=0 rel d tmp
    while IFS= read -r rel; do
        rel="${rel#./}"
        [ -n "$rel" ] || continue
        hm_is_preserved "$rel" && continue
        # Две проверки подряд: по списку из скана и по живому состоянию диска. Вторая
        # обязана быть ПЕРЕД mkdir/cp для КАЖДОГО файла: mkdir -p сквозь ссылку создаёт
        # каталог во внешней цели, а cp — перезаписывает там файл.
        if is_link_excluded "$rel"; then hm_note_link; continue; fi
        if hm_dst_link_in_path "$rel"; then hm_note_link; continue; fi
        [ "$mode" = "missing" ] && [ -e "$dst/$rel" ] && continue
        d="$(dirname "$dst/$rel")"
        mkdir -p "$d" || { rc=1; continue; }
        # ЗАПИСЬ ЧЕРЕЗ ВРЕМЕННЫЙ ФАЙЛ + ПЕРЕИМЕНОВАНИЕ, а не прямой cp поверх цели.
        # Прямой `cp -p src dst` открывает СУЩЕСТВУЮЩИЙ файл и пишет в его inode. Если у
        # этого inode есть второе имя (жёсткая ссылка на твой файл вне ~/.claude), меняется
        # и оно — молча, без единого предупреждения, и восстановить его неоткуда.
        # mv в пределах одного каталога — это rename(2): он подменяет ЗАПИСЬ В КАТАЛОГЕ,
        # а старый inode остаётся жить под вторым именем со своим прежним содержимым.
        # Поэтому ссылка «расщепляется», а не затирается. Побочных эффектов для обычных
        # файлов нет: cp -p переносит на временный файл права и время источника — ровно то
        # же, что делал cp -p прямо на цель, — а rename их сохраняет. Идемпотентность тоже
        # не страдает: повторный прогон снова кладёт тот же байт-в-байт файл.
        # НЕ cp -Rn: GNU coreutils >= 9.2 считает пропуск существующего файла ошибкой.
        if [ -e "$dst/$rel" ]; then
            # Цель уже есть — только здесь и возможна жёсткая ссылка, поэтому платим
            # за лишний процесс (cp + mv вместо одного cp) ровно на этих файлах.
            tmp="$dst/$rel.ccpk-tmp.$$"
            HM_TMPFILE="$tmp"
            if cp -p "$src/$rel" "$tmp"; then
                # mv -f: цель может быть с правами «только чтение» — rename смотрит на
                # права КАТАЛОГА, а не файла, поэтому такой файл теперь обновляется.
                if ! mv -f "$tmp" "$dst/$rel"; then
                    rm -f "$tmp" 2>/dev/null
                    rc=1
                fi
            else
                rm -f "$tmp" 2>/dev/null
                rc=1
            fi
            HM_TMPFILE=""
        else
            # Файла нет — второму имени взяться неоткуда, пишем напрямую. Между этой
            # проверкой и cp есть те же микросекунды TOCTOU, что и у любой проверки на
            # диске; чтобы файл успел появиться ИМЕННО там и ИМЕННО жёсткой ссылкой,
            # кто-то должен делать это ровно в этот момент от твоего имени.
            cp -p "$src/$rel" "$dst/$rel" || rc=1
        fi
    done < "$TMPD/raw.txt"
    return $rc
}

# --- ЛОСС 5: ПЕРЕПРОВЕРКА ССЫЛОК ВПЛОТНУЮ К ЗАПИСИ --------------------------------------
# Первый скан отработал в самом начале, ДО резервного копирования. Копирование бэкапа —
# это секунды, а на большом конфиге и десятки секунд. Всё это время список ссылок уже
# устарел: появившаяся за это окно ссылка (её мог сделать твой же скрипт синхронизации,
# облачный клиент или ты сам в соседнем терминале) не попала бы в исключения rsync, и он
# записал бы сквозь неё во внешний каталог. У пофайловой ветки такой дыры не было:
# hm_copy проверяет диск перед КАЖДЫМ файлом. Здесь выравниваем ветку rsync — сканируем
# заново прямо перед запуском копирования.
#
# ЧЕСТНО ПРО ОСТАТОК. Полностью окно не закрывается: между этим сканом и моментом, когда
# rsync запишет последний файл, проходит время самого прогона (обычно секунды). Ссылка,
# созданная ровно в эти секунды, замечена не будет. Убрать остаток можно было бы, только
# отказавшись от rsync в пользу пофайлового копирования с проверкой перед каждым файлом,
# но и там окно не ноль (микросекунды между проверкой и записью — то же самое TOCTOU),
# зато скорость падает на порядок: пак — это тысячи файлов. Поэтому: было «время
# копирования резервной копии» (десятки секунд), стало «время одного прохода rsync».
# Создать ссылку в этот момент может только процесс, работающий от твоего имени.
# Второй скан — ещё и последний барьер: не смогли просмотреть дерево — не пишем вовсе.
if ! scan_links; then
    echo "ОШИБКА: повторная проверка $DST_CLAUDE на симлинки не удалась — установка прервана" >&2
    echo "        ПЕРЕД записью. Файлы конфига не изменены; резервная копия (если делалась) на месте." >&2
    exit 1
fi
build_rsync_link_excludes
# Появившиеся после первого скана ссылки: сказать про них и выкинуть эти пути из списка
# разложенного — иначе манифест записал бы как «наши» файлы, которых мы не клали.
NEW_LINKS="$TMPD/newlinks.txt"; : > "$NEW_LINKS"
for k in ${LINK_RELS[@]+"${LINK_RELS[@]}"}; do
    case "$LINK_SEEN" in
        *"|$k|"*) : ;;
        *) printf '%s\n' "$k" >> "$NEW_LINKS"
           LINK_SEEN="$LINK_SEEN|$k|"
           echo "  ~/.claude/$k — ссылка (появилась после первой проверки): пропускаю весь этот путь." ;;
    esac
done
if [ -s "$NEW_LINKS" ] && [ -s "$SRC_LIST" ]; then
    if awk 'FNR==NR { k[".claude/" $0]=1; next }
            { for (p in k) if ($0 == p || index($0, p "/") == 1) next; print }' \
            "$NEW_LINKS" "$SRC_LIST" > "$SRC_LIST.f" 2>/dev/null; then
        mv "$SRC_LIST.f" "$SRC_LIST" 2>/dev/null || rm -f "$SRC_LIST.f" 2>/dev/null
    fi
fi
# Список файлов с несколькими жёсткими ссылками снимаем ДО записи: после расщепления
# ссылки уже не будет и сказать о ней станет нечего. Нужен только в --repair — в
# add-missing существующие файлы не перезаписываются вообще.
if [ "$MODE" = "repair" ]; then
    scan_hardlinks || : > "$HARDLINKS"
fi

if [ "$MODE" = "add-missing" ]; then
    echo "Добавляю только НЕДОСТАЮЩИЕ файлы конфига (существующее сохраняю)..."
    if command -v rsync >/dev/null 2>&1 && [ "$RSYNC_SAFE" -eq 1 ]; then
        rsync -a --ignore-existing "${PRESERVE_RSYNC[@]}" ${LINK_RSYNC[@]+"${LINK_RSYNC[@]}"} "$SRC_CLAUDE/" "$DST_CLAUDE/" || COPY_FAILED=1
    else
        hm_copy "$SRC_CLAUDE" "$DST_CLAUDE" missing || COPY_FAILED=1
    fi
else
    echo "Режим --repair: перезаписываю НАШИ базовые файлы свежими (ключи, память, история, settings.local.json, ~/CLAUDE.md не трогаю)..."
    echo "  ВНИМАНИЕ: если ты правил файл, имя которого совпадает с файлом пака (например,"
    echo "  skills/<имя>/SKILL.md), в этом режиме он будет заменён нашей версией. Прежняя"
    echo "  версия — в резервной копии выше. Нужно сохранить свои правки — жми Ctrl+C и"
    echo "  ставь без --repair."
    if command -v rsync >/dev/null 2>&1 && [ "$RSYNC_SAFE" -eq 1 ]; then
        rsync -a "${PRESERVE_RSYNC[@]}" ${LINK_RSYNC[@]+"${LINK_RSYNC[@]}"} "$SRC_CLAUDE/" "$DST_CLAUDE/" || COPY_FAILED=1
    else
        hm_copy "$SRC_CLAUDE" "$DST_CLAUDE" overwrite || COPY_FAILED=1
    fi
fi
[ "$COPY_FAILED" -eq 1 ] && echo "ВНИМАНИЕ: часть файлов скопировать не удалось (см. вывод выше)."

# --- отчёт про расщеплённые жёсткие ссылки ----------------------------------------------
# Говорим только про те файлы, которые реально перезаписывали: у файла было два имени,
# теперь имя внутри ~/.claude — наша свежая версия, а второе имя осталось со старым
# содержимым. Данные не потеряны, но связь между двумя именами разорвана — это заметно
# для того, кто её создавал намеренно, и молчать об этом нельзя.
if [ "$MODE" = "repair" ] && [ -s "$HARDLINKS" ] && [ -s "$SRC_LIST" ]; then
    HL_HIT="$TMPD/hl_hit.txt"; HL_REAL="$TMPD/hl_real.txt"
    if awk 'FNR==NR { h[".claude/" $0]=1; next } ($0 in h) { print }' \
        "$HARDLINKS" "$SRC_LIST" > "$HL_HIT" 2>/dev/null && [ -s "$HL_HIT" ]; then
        # Проверяем ПО ФАКТУ, а не по намерению: у файла действительно стало одно имя?
        # rsync пропускает файлы, у которых совпали размер и время, — такой файл он не
        # переписывал, ссылка цела, и говорить, что мы её расщепили, было бы неправдой.
        : > "$HL_REAL"
        while IFS= read -r p; do
            [ -e "$HOME/$p" ] || continue
            [ -n "$(find "$HOME/$p" -links +1 -print 2>/dev/null)" ] && continue
            printf '%s\n' "$p" >> "$HL_REAL"
        done < "$HL_HIT"
        mv -f "$HL_REAL" "$HL_HIT" 2>/dev/null || : > "$HL_HIT"
    fi
    if [ -s "$HL_HIT" ]; then
        HL_N=$(wc -l < "$HL_HIT" | tr -d ' ')
        echo "ПРИМЕЧАНИЕ: у $HL_N файл(ов) в ~/.claude было по нескольку жёстких ссылок"
        echo "  (второе имя того же файла — обычно твоя копия вне ~/.claude)."
        echo "  Свежую версию записали как НОВЫЙ файл, второе имя оставили нетронутым:"
        sed -n '1,10p' "$HL_HIT" | while IFS= read -r p; do echo "    ~/$p"; done
        [ "$HL_N" -gt 10 ] && echo "    ... и ещё $((HL_N - 10))"
        echo "  Если связь между двумя именами была нужна — пересоздай ссылку вручную (ln)."
    fi
fi

# --- 4. ~/CLAUDE.md — только если его нет (это ТВОЙ файл) --------------------------------
CLAUDE_MD_ADDED=0
if [ -f "$SRC_CLAUDE_MD" ]; then
    if [ -e "$DST_CLAUDE_MD" ] || [ -L "$DST_CLAUDE_MD" ]; then
        echo "~/CLAUDE.md уже есть — НЕ трогаю (твои личные инструкции). Наш вариант: $SRC_CLAUDE_MD"
    else
        if cp "$SRC_CLAUDE_MD" "$DST_CLAUDE_MD"; then CLAUDE_MD_ADDED=1; echo "Создан ~/CLAUDE.md"
        else COPY_FAILED=1; echo "ВНИМАНИЕ: не удалось скопировать ~/CLAUDE.md."; fi
    fi
fi

# --- 4b. rules/user-profile.md — только если его нет (это ТВОЯ анкета) -------------------
# Из merge он исключён в ОБОИХ режимах (см. preserve-list выше), поэтому кладём вручную.
USER_PROFILE_ADDED=0
if [ -f "$SRC_CLAUDE/rules/user-profile.md" ]; then
    if [ -e "$DST_CLAUDE/rules/user-profile.md" ] || [ -L "$DST_CLAUDE/rules/user-profile.md" ]; then
        echo "rules/user-profile.md уже есть — НЕ трогаю (там твои личные данные)."
    elif hm_dst_link_in_path "rules/user-profile.md"; then
        # Сам файл ещё не создан, но каталог rules/ (или он сам) — ссылка наружу.
        # mkdir -p + cp создали бы файл в ТВОЁМ внешнем каталоге. Не делаем.
        echo "rules/user-profile.md пропущен: ~/.claude/$LINK_HIT — ссылка, во внешнюю цель не пишу."
    else
        mkdir -p "$DST_CLAUDE/rules" 2>/dev/null || :
        if cp "$SRC_CLAUDE/rules/user-profile.md" "$DST_CLAUDE/rules/user-profile.md"; then
            USER_PROFILE_ADDED=1
        else
            COPY_FAILED=1; echo "ВНИМАНИЕ: не удалось скопировать rules/user-profile.md."
        fi
    fi
fi

# --- 5. credentials — только если ключей ещё нет ----------------------------------------
if [ -f "$SRC_ENV_TEMPLATE" ] && [ ! -e "$DST_ENV" ]; then
    if cp "$SRC_ENV_TEMPLATE" "$DST_ENV"; then echo "Создан $DST_ENV — ключи НЕ нужны: всё работает по подписке Claude. Трогай только если включаешь опциональную платную фичу."
    else COPY_FAILED=1; echo "ВНИМАНИЕ: не удалось создать $DST_ENV."; fi
elif [ -e "$DST_ENV" ]; then
    echo "$DST_ENV уже есть — НЕ трогаю."
fi

# --- 6. Манифест: РОВНО то, что положили мы ---------------------------------------------
# Наше = (файл источника, которого в ~/.claude не было ДО копирования)
#        ∪ (файл, записанный нами в манифест прошлым прогоном).
# Файл, который у тебя УЖЕ был и в манифесте не значится, нашим НЕ считается, даже если
# --repair его перезаписал: uninstall.sh его не тронет (а прежняя версия — в резервной копии).
if [ "$MANIFEST_OK" -eq 1 ]; then
    awk 'FNR==1{f++} f==1{if($0!="#")pre[$0]=1;next} f==2{if($0!="#")prev[$0]=1;next}
         { if (!($0 in pre) || ($0 in prev)) print }' \
        "$PRE_LIST" "$PREV_LIST" "$SRC_LIST" > "$OURS_LIST" 2>/dev/null || MANIFEST_OK=0
fi
if [ "$MANIFEST_OK" -eq 1 ]; then
    [ "$CLAUDE_MD_ADDED" -eq 1 ] && printf 'CLAUDE.md\n' >> "$OURS_LIST"
    # Анкету пишем в список разложенного, только если её создали МЫ (её не было). Тогда
    # uninstall уберёт нетронутый шаблон, а заполненную анкету оставит: размер/дата разойдутся.
    [ "$USER_PROFILE_ADDED" -eq 1 ] && printf '.claude/rules/user-profile.md\n' >> "$OURS_LIST"
    # На всякий случай: ключи в манифест не попадают никогда.
    grep -v '^\.claude/\.credentials\.' "$OURS_LIST" > "$OURS_LIST.f" 2>/dev/null && mv "$OURS_LIST.f" "$OURS_LIST"
    # Файл, который УЖЕ лежал в ~/.claude до этого прогона, в add-missing мы НЕ писали.
    # Значит его запись в манифесте должна остаться ПРЕЖНЕЙ — с размером и датой на момент,
    # когда файл клали МЫ. Иначе выходит «отмывание правки»: ты поправил наш файл, потом
    # повторно запустил установку, она записала бы твои размер/дату, и uninstall.sh счёл бы
    # файл нетронутым и УДАЛИЛ его вместе с правкой. В --repair мы файл реально перезаписали
    # своей версией, поэтому там актуальные размер/дата — правильные.
    CARRY="$TMPD/carry.txt"; FRESH="$TMPD/fresh.txt"; : > "$CARRY"; : > "$FRESH"
    # COPY_FAILED в --repair означает «часть файлов переписать не удалось» (файл занят,
    # нет прав). Какие именно — неизвестно, поэтому для всех уже существовавших файлов
    # действует то же консервативное правило: держим прежнюю запись. Худшее следствие —
    # uninstall.sh оставит лишний файл; это лучше, чем удалить чужой.
    if { [ "$MODE" = "add-missing" ] || [ "$COPY_FAILED" -eq 1 ]; } && [ -f "$MANIFEST" ]; then
        awk -v CARRYF="$CARRY" -v FRESHF="$FRESH" \
            'FNR==NR { if($0!="#" && $0!="") pre[$0]=1; next }
             { if ($0 in pre) print > CARRYF; else print > FRESHF }' "$PRE_LIST" "$OURS_LIST"
    else
        cp "$OURS_LIST" "$FRESH" 2>/dev/null || cat "$OURS_LIST" > "$FRESH"
    fi
    STAT_FLAVOR=""
    if stat -f '%z %m %N' "$SRC_CLAUDE" >/dev/null 2>&1; then STAT_FLAVOR=bsd
    elif stat -c '%s %Y %n' "$SRC_CLAUDE" >/dev/null 2>&1; then STAT_FLAVOR=gnu; fi
    if [ -z "$STAT_FLAVOR" ]; then
        echo "ВНИМАНИЕ: команда stat недоступна — размер/дату файлов записать не могу."
        echo "          uninstall.sh в этом случае ничего удалять не будет (fail-closed)."
        : > "$STATS"
    elif [ ! -s "$FRESH" ]; then
        # Нечего заново измерять: все записи переносятся из прошлого манифеста как есть.
        : > "$STATS"
    elif [ "$STAT_FLAVOR" = "bsd" ]; then
        ( cd "$HOME" && tr '\n' '\0' < "$FRESH" | xargs -0 stat -f '%z %m %N' ) > "$STATS" 2>/dev/null || :
    else
        ( cd "$HOME" && tr '\n' '\0' < "$FRESH" | xargs -0 stat -c '%s %Y %n' ) > "$STATS" 2>/dev/null || :
    fi
    # Сверка: сколько файлов мы собирались измерить и сколько реально нашлось на диске.
    # Расхождение = файл не доехал (антивирус/права/диск), а copy об этом не сказал.
    # Молчать нельзя: такой файл не разложен И не попадёт в список разложенного.
    FRESH_N=$(wc -l < "$FRESH" 2>/dev/null | tr -d ' '); STAT_N=$(wc -l < "$STATS" 2>/dev/null | tr -d ' ')
    if [ "${STAT_N:-0}" -lt "${FRESH_N:-0}" ]; then
        echo "ВНИМАНИЕ: $(( FRESH_N - STAT_N )) файл(ов) пака не оказалось на месте после копирования"
        echo "  (чаще всего не хватило прав или файл придержал антивирус). Они НЕ разложены и не"
        echo "  попали в список разложенного. Запусти установку ещё раз — она их доложит."
    fi
    CUR_LIST="$TMPD/cur.txt"
    { printf '#\n'; cat "$OURS_LIST"; } > "$CUR_LIST"
    TAB="$(printf '\t')"
    {
        echo "# ccpack manifest v1 — файлы, разложенные your-config-repo"
        echo "# Не редактируй руками. uninstall.sh удаляет ТОЛЬКО перечисленное здесь"
        echo "# и только если файл не изменился (сверка по размеру и дате)."
        echo "# поля: размер<TAB>mtime_unix<TAB>путь (относительно \$HOME)"
        awk '{s=$1; m=$2; p=$0; sub(/^[^ ]+ +[^ ]+ +/,"",p); if (p!="") print s "\t" m "\t" p}' "$STATS"
        # Файлы, которые в этот раз мы не писали (они уже были): переносим прежнюю запись
        # ЦЕЛИКОМ, с исходными размером и датой — чтобы правка пользователя не «отмывалась».
        if [ -s "$CARRY" ] && [ -f "$MANIFEST" ]; then
            awk -F'\t' 'FNR==NR { if($0!="") c[$0]=1; next }
                        !/^#/ && NF>=3 { if ($3 in c) print }' "$CARRY" "$MANIFEST"
        fi
        # Переносим записи прошлых прогонов, которые в этот раз не обновлялись,
        # но файлы всё ещё на месте: иначе снятие пака работало бы ровно один раз.
        if [ -f "$MANIFEST" ]; then
            awk -F'\t' 'FNR==1{f++} f==1{if($0!="#" && $0!="")cur[$0]=1;next}
                        !/^#/ && NF>=3 { if (!($3 in cur)) print }' "$CUR_LIST" "$MANIFEST" \
            | while IFS="$TAB" read -r sz mt p; do
                [ -n "$p" ] && [ -e "$HOME/$p" ] && printf '%s\t%s\t%s\n' "$sz" "$mt" "$p"
              done
        fi
    } > "$TMPD/manifest.new" 2>/dev/null
    if mv "$TMPD/manifest.new" "$MANIFEST" 2>/dev/null; then
        N=$(awk -F'\t' '!/^#/ && NF>=3' "$MANIFEST" | wc -l | tr -d ' ')
        echo "Список разложенного записан: $MANIFEST (файлов: $N)"
    else
        echo "ВНИМАНИЕ: не удалось записать $MANIFEST — uninstall.sh не сможет ничего удалить (fail-closed)."
    fi
fi

# --- 7. Python-зависимости (по желанию) --------------------------------------------------
if [ "$SKIP_DEPS" -ne 1 ] && [ -f "$HERE/requirements.txt" ]; then
    if command -v python3 >/dev/null 2>&1; then
        echo "Ставлю Python-зависимости (--user)... (пропустить: --skip-deps)"
        python3 -m pip install --user --upgrade pip >/dev/null 2>&1 || :
        python3 -m pip install --user -r "$HERE/requirements.txt" || echo "Python-зависимости не поставились — пропускаю (на работу конфига не влияет)."
    else
        echo "python3 не найден — Python-зависимости пропущены."
    fi
fi

# --- 7b. Рантайм: то, что живёт НЕ в файлах ------------------------------------------------
# Копирование файлов — ещё не рабочий конфиг. Три вещи живут в состоянии машины, и без них
# пак выглядит установленным, а половина скиллов падает на первом запуске:
#   • браузер Playwright (пакет ставится из requirements, сам браузер — нет; на него
#     завязаны 42 скилла: карточки, экспорт в PNG/PDF/PPTX, деки, скриншот-тесты);
#   • маркетплейсы плагинов (объявлено 29 плагинов, но машина не знает, откуда их брать);
#   • node_modules для dev-browser (его server.sh иначе делает npm install в бою).
# Именно это и было «полчаса докручивали после установки»: скрипт-лекарство существовал,
# но его никто не вызывал, и на экране о нём не было ни слова.
# Идемпотентно: повторный прогон занимает секунды и ничего не делает.
if [ "$SKIP_DEPS" -ne 1 ] && [ -f "$DST_CLAUDE/scripts/setup_runtime.py" ]; then
    if command -v python3 >/dev/null 2>&1; then
        echo
        echo "Довожу рантайм (браузер Playwright, маркетплейсы плагинов, node_modules)..."
        python3 "$DST_CLAUDE/scripts/setup_runtime.py" || {
            echo "Рантайм доехал НЕ полностью. Это не ломает установку — доделать можно в любой момент:"
            echo "  python3 ~/.claude/scripts/setup_runtime.py"
            echo "Что именно не хватает, покажет: python3 ~/.claude/scripts/setup_runtime.py --check"
        }
    else
        echo "python3 не найден — рантайм не доведён. После установки Python запусти:"
        echo "  python3 ~/.claude/scripts/setup_runtime.py"
    fi
fi

# --- 8. Честный итог ---------------------------------------------------------------------
echo
if [ "$COPY_FAILED" -eq 1 ]; then
    echo "ГОТОВО НЕ ПОЛНОСТЬЮ: часть файлов скопировать не удалось (см. вывод выше)."
    echo "  Твои ключи, память и история сессий НЕ тронуты — мы ничего не переносили и не стирали."
    echo "  Можно запустить установку повторно после устранения причины."
else
    if [ "$MODE" = "add-missing" ]; then echo "ГОТОВО: добавлено недостающее, всё существующее сохранено."
    else echo "ГОТОВО: наши базовые файлы обновлены, пользовательские данные на месте."; fi
fi
echo "Сохранено без изменений: ключи (.credentials.*), MEMORY.md, memory/, projects/ (история сессий),"
echo "  todos/, shell-snapshots/, chats.db*, tg_session.session*, settings.local.json, ~/CLAUDE.md."
[ "$BACKUP" -eq 1 ] && [ -n "${BACKUP_DIR:-}" ] && [ -d "${BACKUP_DIR:-/nonexistent}" ] && echo "Резервная копия: $BACKUP_DIR (храним 3 последние)."
echo "Откат: ./uninstall.sh — удалит только то, что положил этот установщик."
echo "Дальше: заполни $DST_CLAUDE/rules/user-profile.md -> запусти 'claude'. API-ключи не требуются."
# Проверка рантайма — не «на всякий случай», а по факту: если браузера Playwright или
# маркетплейсов нет, скиллы падают на первой же задаче, и человек об этом узнаёт в бою.
# Показываем строку ТОЛЬКО когда чего-то реально не хватает, чтобы не приучать
# пролистывать хвост установки.
if [ -f "$DST_CLAUDE/scripts/setup_runtime.py" ] && command -v python3 >/dev/null 2>&1; then
    if ! python3 "$DST_CLAUDE/scripts/setup_runtime.py" --check >/dev/null 2>&1; then
        echo ""
        echo "ВНИМАНИЕ: рантайм доведён не полностью — часть скиллов упадёт при первом запуске."
        echo "  Что именно: python3 ~/.claude/scripts/setup_runtime.py --check"
        echo "  Доделать:   python3 ~/.claude/scripts/setup_runtime.py"
    fi
fi
[ "$COPY_FAILED" -eq 1 ] && exit 1
exit 0
