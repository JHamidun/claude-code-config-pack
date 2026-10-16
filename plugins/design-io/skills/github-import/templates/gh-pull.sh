#!/usr/bin/env bash
# gh-pull.sh — скачать файл или папку из GitHub-репы.
# Usage: ./gh-pull.sh <github-url> [out-dir]
#
# Требует curl и jq. jq не входит ни в macOS, ни в Windows, ни в базовый Debian —
# поэтому проверяем его ДО первого запроса: без jq обход дерева репозитория молча
# скачивал пустоту и заканчивался словом «Готово».

set -euo pipefail

die() {
  printf '%s\n' "$@" >&2
  exit 1
}

# ── 1. Инструменты ───────────────────────────────────────────────────────────
missing=()
command -v curl >/dev/null 2>&1 || missing+=("curl")
command -v jq   >/dev/null 2>&1 || missing+=("jq")
if [[ ${#missing[@]} -gt 0 ]]; then
  die "gh-pull: на этой машине нет: ${missing[*]}" \
      "  macOS:          brew install ${missing[*]}" \
      "  Debian/Ubuntu:  sudo apt install -y ${missing[*]}" \
      "  Fedora:         sudo dnf install -y ${missing[*]}" \
      "  Windows:        winget install jqlang.jq   (curl входит в Windows 10+)" \
      "Останавливаюсь здесь: без jq скрипт создал бы пустые папки и отчитался об успехе."
fi

# ── 2. Разбор URL ────────────────────────────────────────────────────────────
URL="${1:?передай GitHub URL, например https://github.com/owner/repo/tree/main/path}"
OUT_BASE="${2:-gh-import}"

[[ "$URL" == https://github.com/* ]] || \
  die "не похоже на GitHub URL: $URL" \
      "Ожидаю https://github.com/<owner>/<repo>[/tree|blob/<ref>/<path>]"

proto="${URL#https://github.com/}"
IFS='/' read -ra parts <<< "$proto"
OWNER="${parts[0]:-}"
REPO="${parts[1]:-}"
TYPE="${parts[2]:-tree}"
REF="${parts[3]:-HEAD}"
PATH_IN_REPO=$(IFS=/; echo "${parts[*]:4}")

[[ -n "$OWNER" && -n "$REPO" ]] || die "в URL не читаются owner/repo: $URL"

# Каталог назначения создаём НИЖЕ, в своей ветке. Общий `mkdir -p "$OUT"` здесь
# для blob-URL создавал каталог С ИМЕНЕМ ФАЙЛА, curl потом не мог в него писать,
# а `-s` глушил ошибку — и рядом печаталась галочка «✓».
OUT="${OUT_BASE}/${OWNER}-${REPO}${PATH_IN_REPO:+/${PATH_IN_REPO}}"

AUTH=()
if [[ -n "${GITHUB_TOKEN:-}" ]]; then
  AUTH=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
fi

DOWNLOADED=0

# ── 3. Запросы с проверкой HTTP-кода ─────────────────────────────────────────
# curl -s без --fail отдаёт 0 и на 404: тело ошибки уезжало в файл, а рядом
# печаталась галочка. Поэтому код ответа читаем явно.

hint_for_code() {   # http_code api_message
  case "$1" in
    404) echo "  Проверь owner/repo/ref/путь. Приватная репа? нужен GITHUB_TOKEN." ;;
    401|403)
      if [[ "$2" == *"rate limit"* ]]; then
        echo "  Это лимит запросов. Задай GITHUB_TOKEN=<токен> — лимит вырастет с 60 до 5000/час."
      else
        echo "  Нет доступа. Для приватной репы задай GITHUB_TOKEN с правом contents:read."
      fi ;;
    429) echo "  Слишком часто. Подожди или задай GITHUB_TOKEN." ;;
    *)   echo "  Ответ GitHub целиком см. выше." ;;
  esac
}

api_get() {         # url -> тело ответа в stdout
  local url="$1" raw http body msg
  raw=$(curl -sS -L -w $'\n%{http_code}' "${AUTH[@]}" "$url") \
    || die "запрос к GitHub не удался (сеть/прокси/DNS): $url"
  http="${raw##*$'\n'}"
  body="${raw%$'\n'*}"
  if [[ "$http" != "200" ]]; then
    msg=$(printf '%s' "$body" | jq -r '.message? // empty' 2>/dev/null || true)
    die "GitHub API: HTTP $http на $url" \
        "  сообщение: ${msg:-<пусто>}" \
        "$(hint_for_code "$http" "$msg")"
  fi
  printf '%s' "$body"
}

fetch_file() {      # url dest
  local url="$1" dest="$2" http rc
  if [[ -d "$dest" ]]; then
    die "по пути $dest уже лежит КАТАЛОГ — файл туда не записать."
  fi
  http=$(curl -sS -L -w '%{http_code}' "${AUTH[@]}" "$url" -o "$dest") || {
    rc=$?
    die "curl вышел с кодом $rc на $url" \
        "  22/6/7 — сеть, DNS или прокси; 23 — не смог записать в $dest."
  }
  if [[ "$http" != "200" ]]; then
    rm -f "$dest"
    die "HTTP $http при скачивании $url" \
        "  файл не сохранён — иначе на диске лежало бы тело ошибки под видом данных." \
        "$(hint_for_code "$http" "")"
  fi
  DOWNLOADED=$((DOWNLOADED + 1))
}

# ── 4. Один файл ─────────────────────────────────────────────────────────────
if [[ "$TYPE" == "blob" ]]; then
  [[ -n "$PATH_IN_REPO" ]] || die "в blob-URL нет пути к файлу: $URL"
  echo "→ Один файл: $PATH_IN_REPO"
  raw_url="https://raw.githubusercontent.com/${OWNER}/${REPO}/${REF}/${PATH_IN_REPO}"
  dest="${OUT_BASE}/${OWNER}-${REPO}/$(basename "$PATH_IN_REPO")"
  mkdir -p "$(dirname "$dest")"
  fetch_file "$raw_url" "$dest"
  echo "✓ $dest"
  exit 0
fi

# ── 5. Папка рекурсивно ──────────────────────────────────────────────────────
echo "→ Папка: ${PATH_IN_REPO:-<корень репозитория>} (рекурсивно)"
mkdir -p "$OUT"
api="https://api.github.com/repos/${OWNER}/${REPO}/contents/${PATH_IN_REPO}?ref=${REF}"

walk() {
  local api_url="$1" local_dir="$2" json kind name type download sub_url
  mkdir -p "$local_dir"
  json=$(api_get "$api_url")

  kind=$(printf '%s' "$json" | jq -r 'type')
  if [[ "$kind" != "array" ]]; then
    # На путь к файлу API отдаёт объект, а не список — тоже валидный случай.
    name=$(printf '%s' "$json" | jq -r '.name // empty')
    download=$(printf '%s' "$json" | jq -r '.download_url // empty')
    [[ -n "$name" && -n "$download" ]] || \
      die "неожиданный ответ GitHub на $api_url (тип: $kind)" \
          "  ждал список файлов; проверь, что путь указывает на папку."
    fetch_file "$download" "${local_dir}/${name}"
    echo "  ✓ ${local_dir}/${name}"
    return 0
  fi

  # Цикл читаем из process substitution, а не из пайпа: тело остаётся в текущей
  # оболочке, поэтому рекурсия и die работают, а не глохнут в подпроцессе.
  #
  # Порядок полей не случаен. Табуляция для `read` — это IFS-ПРОБЕЛ, и два тире
  # подряд схлопываются в один разделитель: у папки download_url пустой, и при
  # порядке [name,type,download,url] адрес папки уезжал в переменную download,
  # а sub_url оставался пустым — рекурсия уходила запрашивать пустой URL.
  # Поэтому возможно-пустое поле идёт ПОСЛЕДНИМ и с заглушкой "-".
  while IFS=$'\t' read -r name type sub_url download; do
    download="${download%$'\r'}"; sub_url="${sub_url%$'\r'}"
    [[ -n "$name" ]] || continue
    if [[ "$type" == "file" ]]; then
      [[ -n "$download" && "$download" != "-" ]] || \
        die "у файла ${local_dir}/${name} нет download_url" \
            "  так бывает для файлов >100 МБ и подмодулей — скачай его вручную."
      fetch_file "$download" "${local_dir}/${name}"
      echo "  ✓ ${local_dir}/${name}"
    elif [[ "$type" == "dir" ]]; then
      [[ -n "$sub_url" ]] || die "у папки ${local_dir}/${name} пустой url в ответе GitHub"
      walk "$sub_url" "${local_dir}/${name}"
    fi
  done < <(printf '%s' "$json" | jq -r '.[] | [.name, .type, .url, (.download_url // "-")] | @tsv')
}

walk "$api" "$OUT"

# ── 6. Пустой результат — это отказ, а не успех ──────────────────────────────
if [[ "$DOWNLOADED" -eq 0 ]]; then
  die "скачано 0 файлов — папка «${PATH_IN_REPO:-<корень>}» пуста или путь неверен." \
      "  Каталог $OUT оставлен пустым намеренно, чтобы это было видно."
fi

echo "Готово: файлов $DOWNLOADED. См. $OUT"
