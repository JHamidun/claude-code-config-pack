#!/usr/bin/env bash
# Claude Code config pack — удаление (macOS / Linux)
#
# === ГЛАВНЫЙ ИНВАРИАНТ: удаляем ТОЛЬКО то, что положил install.sh ===
# Источник правды — ~/.claude/.ccpack-manifest.txt: install.sh записывает туда РОВНО те
# файлы, которые он реально создал (не те, что у тебя уже были, даже если имена совпали),
# вместе с их размером и датой на момент установки.
#
# Файл удаляется, только если выполнено ВСЁ:
#   1) он перечислен в манифесте;
#   2) он лежит внутри ~/.claude (или это ~/CLAUDE.md от прежних версий пака);
#   3) он не симлинк;
#   4) размер и дата совпадают с записанными — то есть ты его не менял.
# Изменённый тобой файл НЕ удаляется: раз ты его правил, он больше не наш.
#
# Манифеста нет или он нечитаем — не удаляем НИЧЕГО (fail-closed) и честно говорим об этом.
#
# НЕ ТРОГАЕМ НИКОГДА: .credentials.master.env, .credentials.json, MEMORY.md, memory/,
# projects/ (история сессий), todos/, shell-snapshots/, chats.db*, tg_session.session*,
# settings.local.json, резервные копии ~/.claude.backup.*, а также любые твои файлы,
# которых нет в манифесте.
set -uo pipefail

DRY=0
for arg in "$@"; do
    case "$arg" in
        --dry-run) DRY=1 ;;
        -h|--help)
            cat <<'USAGE'
Usage: ./uninstall.sh [--dry-run]

Удаляет файлы конфиг-пака, перечисленные в ~/.claude/.ccpack-manifest.txt и не изменённые
тобой после установки. Ключи, память, история сессий, локальные настройки, навигационный
хаб ~/.claude/CLAUDE.md (если он был твоим) и резервные копии не трогаются.

  --dry-run   показать, что будет удалено, и ничего не удалять.
USAGE
            exit 0 ;;
        *) echo "ОШИБКА: неизвестный аргумент: $arg" >&2; exit 2 ;;
    esac
done

DST_CLAUDE="$HOME/.claude"
MANIFEST="$DST_CLAUDE/.ccpack-manifest.txt"

if [ ! -f "$MANIFEST" ]; then
    echo "Список разложенного не найден: $MANIFEST"
    echo
    echo "Без него невозможно отличить файлы пака от твоих собственных, поэтому НИЧЕГО не удаляю."
    echo "Так и задумано: лучше оставить лишнее, чем снести чужое."
    echo
    echo "Что можно сделать:"
    echo "  • если пак ставился этим install.sh — манифест должен быть на месте; проверь ~/.claude;"
    echo "  • если конфиг раскладывался вручную/старым скриптом — удаляй нужные подкаталоги сам;"
    echo "  • резервные копии (если install.sh их делал) лежат рядом: ls -d ~/.claude.backup.*"
    exit 1
fi
if [ ! -r "$MANIFEST" ]; then
    echo "Список разложенного нечитаем: $MANIFEST — ничего не удаляю (fail-closed)." >&2
    exit 1
fi

TMPD="$(mktemp -d "${TMPDIR:-/tmp}/ccpack-un.XXXXXX" 2>/dev/null)" || TMPD=""
[ -n "$TMPD" ] || { echo "ОШИБКА: не удалось создать временный каталог — ничего не удаляю." >&2; exit 1; }
trap 'rm -rf "$TMPD"' EXIT
ENTRIES="$TMPD/entries.txt"; PATHS="$TMPD/paths.txt"; STATS="$TMPD/stats.txt"
LINKS="$TMPD/links.txt"
: > "$ENTRIES"; : > "$PATHS"; : > "$LINKS"

TAB="$(printf '\t')"
skipped_unsafe=0; skipped_link=0; skipped_preserved=0

# Ссылкой может оказаться не сам файл, а ЛЮБОЙ его предок. Бытовой случай без экзотики:
# человек перенёс ~/.claude/skills в свой репозиторий и слинковал обратно. Move в пределах
# тома сохраняет размер и mtime, поэтому сверка манифеста совпадает — и удаление уносит
# файлы ИЗ ЕГО РЕПОЗИТОРИЯ, а отчёт при этом честно пишет «пропущено симлинков: 0».
# Поэтому проверяем КАЖДОЕ ЗВЕНО пути, а не только последний элемент.
LINK_HIT=""
has_link_in_path() {   # $1 = путь относительно $HOME; 0 = какое-то звено — симлинк
    local rel="$1" acc="" comp oldifs
    LINK_HIT=""
    oldifs="$IFS"; IFS='/'; set -- $rel; IFS="$oldifs"
    for comp in "$@"; do
        [ -n "$comp" ] || continue
        acc="${acc:+$acc/}$comp"
        if [ -L "$HOME/$acc" ]; then LINK_HIT="$acc"; return 0; fi
    done
    return 1
}

# То же, что в install.sh: второй рубеж на случай правленого/старого манифеста.
is_preserved() {
    case "/$1" in
        */.credentials.master.env|*/.credentials.json|*/settings.local.json|*/MEMORY.md) return 0 ;;
        */chats.db*|*/tg_session.session*) return 0 ;;
        */.ccpack-manifest.txt) return 0 ;;
    esac
    # Якорь к первому уровню внутри .claude — зеркало install.sh. Здесь путь идёт от $HOME
    # (".claude/rules/..."). Голое имя каталога совпадало на любой глубине, из-за чего
    # .claude/templates/memory/* (файлы пака) считались пользовательской памятью.
    case "$1" in
        .claude/memory/*|.claude/projects/*|.claude/todos/*|.claude/shell-snapshots/*) return 0 ;;
    esac
    return 1
}

while IFS="$TAB" read -r sz mt p; do
    case "$sz" in ''|'#'*) continue ;; esac
    [ -n "$p" ] || continue
    # Путь обязан быть внутри ~/.claude. Никаких "..", никаких абсолютных путей —
    # манифест мог быть подправлен руками. Голый CLAUDE.md разрешён отдельной строкой:
    # так навигационный хаб записывали прежние версии установщика (~/CLAUDE.md), и такие
    # манифесты ещё лежат у тех, кто ставил пак раньше. Сейчас хаб пишется как
    # .claude/CLAUDE.md и проходит по общему правилу выше.
    case "$p" in
        /*|*..*) skipped_unsafe=$((skipped_unsafe+1)); continue ;;
        .claude/*) ;;
        CLAUDE.md) ;;
        *) skipped_unsafe=$((skipped_unsafe+1)); continue ;;
    esac
    if is_preserved "$p"; then skipped_preserved=$((skipped_preserved+1)); continue; fi
    # Размер/дата должны быть числами, иначе проверить «не менялся ли файл» нечем.
    case "$sz$mt" in *[!0-9]*) skipped_unsafe=$((skipped_unsafe+1)); continue ;; esac
    [ "$mt" = "0" ] && { skipped_unsafe=$((skipped_unsafe+1)); continue; }
    if has_link_in_path "$p"; then
        skipped_link=$((skipped_link+1))
        printf '%s\n' "$LINK_HIT" >> "$LINKS"
        continue
    fi
    printf '%s\t%s\t%s\n' "$sz" "$mt" "$p" >> "$ENTRIES"
    printf '%s\n' "$p" >> "$PATHS"
done < "$MANIFEST"

# Молчать про пропущенные ссылки нельзя: человек должен видеть, что часть пака осталась
# лежать в его внешнем каталоге и убрать её при желании руками.
report_links() {   # $1 = префикс строки
    local d
    [ -s "$LINKS" ] || return 0
    sort -u "$LINKS" | while IFS= read -r d; do
        [ -n "$d" ] && echo "$1  ~/$d — ссылка: внутрь внешней цели не заходим, файлы под ней НЕ удалены"
    done
    return 0
}

STAT_FLAVOR=""
if stat -f '%z %m %N' "$MANIFEST" >/dev/null 2>&1; then STAT_FLAVOR=bsd
elif stat -c '%s %Y %n' "$MANIFEST" >/dev/null 2>&1; then STAT_FLAVOR=gnu; fi
if [ -z "$STAT_FLAVOR" ]; then
    echo "ОШИБКА: команда stat недоступна — проверить, что файлы не изменены, нечем. Ничего не удаляю." >&2
    exit 1
fi
# Первая строка-страж: без неё awk-приём FNR==NR ломается на пустом файле статистики.
printf '0 0 .ccpack-sentinel\n' > "$STATS"
if [ -s "$PATHS" ]; then
    if [ "$STAT_FLAVOR" = bsd ]; then
        ( cd "$HOME" && tr '\n' '\0' < "$PATHS" | xargs -0 stat -f '%z %m %N' ) >> "$STATS" 2>/dev/null || :
    else
        ( cd "$HOME" && tr '\n' '\0' < "$PATHS" | xargs -0 stat -c '%s %Y %n' ) >> "$STATS" 2>/dev/null || :
    fi
fi

# Сверка: DEL — совпало (наш нетронутый файл), MOD — файл изменён (оставляем),
# GONE — файла уже нет.
awk -v OFS='\t' '
    FNR==NR { s=$1; m=$2; p=$0; sub(/^[^ ]+ +[^ ]+ +/,"",p); if(p!=""){sz[p]=s; mt[p]=m}; next }
    !/^#/ {
        n=split($0, F, "\t"); if (n<3) next
        p=F[3]
        if (!(p in sz))            { print "GONE", p; next }
        if (sz[p]==F[1] && mt[p]==F[2]) { print "DEL", p } else { print "MOD", p }
    }
' "$STATS" "$ENTRIES" > "$TMPD/plan.txt" 2>/dev/null

n_del=$(awk -F'\t' '$1=="DEL"' "$TMPD/plan.txt" | wc -l | tr -d ' ')
n_mod=$(awk -F'\t' '$1=="MOD"' "$TMPD/plan.txt" | wc -l | tr -d ' ')
n_gone=$(awk -F'\t' '$1=="GONE"' "$TMPD/plan.txt" | wc -l | tr -d ' ')

if [ "$DRY" -eq 1 ]; then
    echo "[dry-run] Будет удалено файлов: $n_del"
    awk -F'\t' '$1=="DEL"{print "  rm ~/" $2}' "$TMPD/plan.txt" | head -20
    [ "${n_del:-0}" -gt 20 ] && echo "  ... и ещё $((n_del-20))"
    echo "[dry-run] Оставлю (ты их менял после установки): $n_mod"
    awk -F'\t' '$1=="MOD"{print "  keep ~/" $2}' "$TMPD/plan.txt" | head -20
    echo "[dry-run] Уже отсутствуют: $n_gone"
    echo "[dry-run] Пропущено записей из-за ссылок: $skipped_link, защищённых: $skipped_preserved, некорректных: $skipped_unsafe"
    report_links "[dry-run] "
    echo "[dry-run] Ничего не изменено."
    exit 0
fi

removed=0; failed=0
DIRS="$TMPD/dirs.txt"; : > "$DIRS"
while IFS="$TAB" read -r kind p; do
    [ "$kind" = "DEL" ] || continue
    if rm -f "$HOME/$p" 2>/dev/null; then
        removed=$((removed+1))
        # Копим каталоги-предки, чтобы потом снять опустевшие (только rmdir — непустой не тронет).
        d="$(dirname "$p")"
        while [ "$d" != "." ] && [ "$d" != "/" ] && [ "$d" != ".claude" ]; do
            printf '%s\n' "$d" >> "$DIRS"
            d="$(dirname "$d")"
        done
    else
        failed=$((failed+1))
    fi
done < "$TMPD/plan.txt"

# Опустевшие каталоги — снизу вверх, ТОЛЬКО rmdir: непустой каталог он не удалит,
# а на симлинк-каталоге просто провалится. rm -rf здесь не используем принципиально.
# Проверка на ссылку — по ВСЕМ звеньям пути, а не только по самому каталогу: rmdir
# ~/.claude/skills/alpha при ссылке на skills снёс бы каталог во внешнем репозитории.
if [ -s "$DIRS" ]; then
    sort -u "$DIRS" | awk '{n=gsub(/\//,"/"); print n "\t" $0}' | sort -rn -k1,1 | cut -f2- | while IFS= read -r d; do
        has_link_in_path "$d" && continue
        rmdir "$HOME/$d" 2>/dev/null || :
    done
fi

# Манифест: оставляем записи, которые пережили удаление (изменённые тобой файлы),
# чтобы повторный запуск снова про них честно сказал. Не осталось ничего — файл убираем.
KEEP="$TMPD/keep.txt"
awk -F'\t' 'FNR==NR { if($1=="MOD") keep[$2]=1; next } !/^#/ { n=split($0,F,"\t"); if(n>=3 && (F[3] in keep)) print }' \
    "$TMPD/plan.txt" "$ENTRIES" > "$KEEP" 2>/dev/null
if [ -s "$KEEP" ]; then
    {
        echo "# ccpack manifest v1 — остаток после uninstall.sh"
        echo "# Здесь только файлы, которые ты менял после установки, — они НЕ удалены."
        echo "# поля: размер<TAB>mtime_unix<TAB>путь (относительно \$HOME)"
        cat "$KEEP"
    } > "$TMPD/manifest.new" && mv "$TMPD/manifest.new" "$MANIFEST" 2>/dev/null
elif [ "$removed" -gt 0 ]; then
    rm -f "$MANIFEST" 2>/dev/null
else
    # Не удалили ничего — манифест не трогаем, иначе потеряли бы единственный
    # признак «что тут наше» и повторный запуск стал бы бесполезен.
    echo "Удалять нечего — список разложенного оставлен на месте."
fi

echo
echo "Удалено файлов пака: $removed"
[ "${n_mod:-0}" -gt 0 ] && echo "Оставлено (ты их правил после установки, значит они уже не наши): $n_mod — см. $MANIFEST"
[ "${n_gone:-0}" -gt 0 ] && echo "Уже отсутствовали: $n_gone"
if [ "${skipped_link:-0}" -gt 0 ]; then
    echo "Пропущено записей из-за ссылок (внутрь внешних целей не заходим): $skipped_link"
    report_links ""
fi
[ "${skipped_preserved:-0}" -gt 0 ] && echo "Пропущено защищённых записей: $skipped_preserved"
[ "${skipped_unsafe:-0}" -gt 0 ] && echo "Пропущено некорректных записей манифеста: $skipped_unsafe"
[ "${failed:-0}" -gt 0 ] && echo "Не удалось удалить (нет прав / файл занят): $failed"
echo
echo "НЕ тронуты: ключи (.credentials.*), MEMORY.md, memory/, projects/ (история сессий), todos/,"
echo "  shell-snapshots/, chats.db*, tg_session.session*, settings.local.json и всё, чего нет в манифесте."
if [ -f "$DST_CLAUDE/.credentials.master.env" ]; then
    echo "  $DST_CLAUDE/.credentials.master.env оставлен намеренно (там могут быть твои ключи)."
    echo "  Если он так и остался пустым шаблоном — удали его сам."
fi
ls -d "$DST_CLAUDE".backup.* >/dev/null 2>&1 && echo "Резервные копии на месте: $(ls -d "$DST_CLAUDE".backup.* | tr '\n' ' ')"
[ "${failed:-0}" -gt 0 ] && exit 1
exit 0
