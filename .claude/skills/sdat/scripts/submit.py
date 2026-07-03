#!/usr/bin/env python3
"""submit.py — сдача заданий Академии Hamidun из Claude Code (скилл «сдать»).

Zero-dependency (только stdlib): читает персональный токен ученика, ходит в
LMS-эндпоинт /api/submit. Токен — в ~/.claude/hamidun.env строкой
`HAMIDUN_SUBMIT_TOKEN=hs_...` (или в переменной окружения). Токен ученик берёт
в кабинете: academy.hamidun.com → «Эфиры» → блок «Сдача заданий через Claude Code».

Команды:
  list                              — какие задания есть и их статусы (что сдавать)
  submit --assignment N --type text  --content "..."        [--resubmit]
  submit --assignment N --type text  --content-file path.md [--resubmit]
  submit --assignment N --type link  --url https://...      [--resubmit]
  submit --assignment N --type file  --file path            [--resubmit]

Вердикт (passed | needs_work) выносит проверяющий-агент асинхронно — придёт в
Telegram/на почту и появится в кабинете. Здесь мы только отправляем сдачу.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_BASE = os.environ.get("HAMIDUN_ACADEMY_URL", "https://academy.hamidun.com").rstrip("/")
ENV_FILE = Path(os.environ.get("HAMIDUN_ENV_FILE", str(Path.home() / ".claude" / "hamidun.env")))
MAX_CONTENT_BYTES = 2 * 1024 * 1024  # 2 МБ текста — совпадает с лимитом сервера


def load_token() -> str:
    """Токен из окружения или из ~/.claude/hamidun.env (HAMIDUN_SUBMIT_TOKEN=...)."""
    tok = os.environ.get("HAMIDUN_SUBMIT_TOKEN", "").strip()
    if tok:
        return tok
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            if key.strip() == "HAMIDUN_SUBMIT_TOKEN":
                return val.strip().strip('"').strip("'")
    return ""


def die(msg: str, code: int = 1) -> None:
    print(f"[сдать] {msg}", file=sys.stderr)
    sys.exit(code)


def api(method: str, token: str, payload: dict | None = None) -> tuple[int, dict]:
    url = f"{DEFAULT_BASE}/api/submit"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/json")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, json.loads(body or "{}")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        try:
            return e.code, json.loads(body or "{}")
        except json.JSONDecodeError:
            return e.code, {"ok": False, "error": "http_error", "message": body[:300]}
    except urllib.error.URLError as e:
        die(f"Не удалось связаться с academy.hamidun.com: {e.reason}")
    except TimeoutError:
        die("Таймаут запроса к academy.hamidun.com — попробуй ещё раз.")
    return 0, {}  # unreachable


STATUS_LABEL = {
    "passed": "✓ зачтено",
    "pending": "⏳ на проверке",
    "needs_work": "✗ нужна доработка",
    "none": "— не сдано",
}


def cmd_list(token: str) -> None:
    status, data = api("GET", token)
    if not data.get("ok"):
        die(_explain(status, data))
    student = data.get("student") or {}
    prog = data.get("progress") or {}
    who = student.get("name") or "ученик"
    cohort = student.get("cohort") or "поток"
    print(f"Ученик: {who} · Поток: {cohort} · Прогресс: {prog.get('passed', 0)}/{prog.get('total', 0)}\n")
    items = data.get("assignments") or []
    if not items:
        print("Заданий пока нет — появятся по ходу потока.")
        return
    for a in items:
        label = STATUS_LABEL.get(a.get("status", "none"), a.get("status", ""))
        kind = {"on_call": "на звонке", "homework": "домашнее"}.get(a.get("kind", ""), a.get("kind", ""))
        head = f"  №{a.get('number')}  {label:<18}  {a.get('title', '')}"
        meta = " · ".join(x for x in [a.get("module"), kind] if x)
        print(head + (f"   [{meta}]" if meta else ""))
        if a.get("status") == "needs_work" and a.get("last_feedback_md"):
            print(f"       ↳ фидбек: {a['last_feedback_md']}")
    print("\nСдать: submit.py submit --assignment <номер> --type text --content-file <файл>")


def cmd_submit(token: str, args: argparse.Namespace) -> None:
    payload: dict = {"artifact_type": args.type}
    # assignment: число (номер) или uuid
    payload["assignment"] = int(args.assignment) if str(args.assignment).isdigit() else args.assignment

    if args.type == "link":
        if not args.url:
            die("--type link требует --url")
        payload["url"] = args.url
    else:  # text | file
        content = None
        if args.content is not None:
            content = args.content
        elif args.content_file:
            p = Path(args.content_file)
            if not p.is_file():
                die(f"Файл не найден: {p}")
            content = p.read_text(encoding="utf-8", errors="replace")
            payload.setdefault("filename", p.name)
        elif args.file:
            p = Path(args.file)
            if not p.is_file():
                die(f"Файл не найден: {p}")
            content = p.read_text(encoding="utf-8", errors="replace")
            payload["filename"] = p.name
        if not content:
            die(f"--type {args.type} требует --content / --content-file / --file")
        if len(content.encode("utf-8")) > MAX_CONTENT_BYTES:
            die("Артефакт больше 2 МБ. Залей на gist/github и сдай ссылкой: --type link --url ...")
        payload["content"] = content

    if args.filename:
        payload["filename"] = args.filename
    if args.resubmit:
        payload["resubmit"] = True

    status, data = api("POST", token, payload)
    if not data.get("ok"):
        die(_explain(status, data))

    a = data.get("assignment") or {}
    head = f"Задание №{a.get('number', args.assignment)} «{a.get('title', '')}»".rstrip()
    st = data.get("status")
    if data.get("already_passed"):
        print(f"{head}\n✓ Уже зачтено. Чтобы пересдать — добавь --resubmit.")
    elif data.get("duplicate"):
        print(f"{head}\n⏳ Уже на проверке — вердикт придёт в Telegram/на почту.")
    elif st == "pending":
        print(f"{head}\n✅ Сдача принята (попытка №{data.get('attempt_no', 1)}).")
        print(data.get("message", "Автопроверка запустится в течение пары минут."))
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


def _explain(status: int, data: dict) -> str:
    err = data.get("error", "")
    msg = data.get("message", "")
    hints = {
        "missing_token": "Токен не передан. Проверь HAMIDUN_SUBMIT_TOKEN в ~/.claude/hamidun.env.",
        "invalid_token": "Токен недействителен. Возьми свежий в кабинете (Эфиры → Сдача заданий).",
        "assignment_not_found": "Такого задания нет. Запусти `list` — увидишь доступные номера.",
        "rate_limited": "Слишком часто. " + (msg or "Подожди и повтори."),
        "too_large": "Артефакт больше 2 МБ — сдай ссылкой (--type link --url ...).",
    }
    base = hints.get(err) or msg or err or f"HTTP {status}"
    return f"{base}" + (f"  ({err})" if err and err not in base else "")


def main() -> None:
    p = argparse.ArgumentParser(prog="submit.py", description="Сдача заданий Академии Hamidun")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="показать задания и статусы")
    s = sub.add_parser("submit", help="сдать задание")
    s.add_argument("--assignment", "-a", required=True, help="номер задания (или uuid)")
    s.add_argument("--type", "-t", choices=["text", "link", "file"], default="text")
    s.add_argument("--content", "-c", help="текст артефакта прямо в аргументе")
    s.add_argument("--content-file", help="файл, чьё содержимое отправить как текст")
    s.add_argument("--file", "-f", help="то же, но filename проставится автоматически")
    s.add_argument("--url", "-u", help="ссылка (для --type link)")
    s.add_argument("--filename", help="имя файла (метка)")
    s.add_argument("--resubmit", action="store_true", help="пересдать уже зачтённое")
    args = p.parse_args()

    token = load_token()
    if not token:
        die(
            "Нет токена сдачи. Возьми его в кабинете (academy.hamidun.com → Эфиры → "
            "«Сдача заданий через Claude Code») и положи строкой\n"
            "  HAMIDUN_SUBMIT_TOKEN=hs_...\n"
            f"в файл {ENV_FILE}"
        )

    if args.cmd == "list":
        cmd_list(token)
    elif args.cmd == "submit":
        cmd_submit(token, args)


if __name__ == "__main__":
    main()
