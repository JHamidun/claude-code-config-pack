#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_digests_from_db.py — дайджесты сессий ИЗ chats.db (а не локальных .jsonl).

Зачем: кейсбук (_casebook/build_digests.py) читал только локальные .jsonl → пропустил
стёртые баг'ом транскрипты (5фев–8июн) + облачные сессии. В chats.db `messages` контент ЦЕЛ.
Этот билдер закрывает дыру: строит дайджесты для РЕАЛЬНЫХ (is_noise=0) сессий >= порога,
которых НЕТ в _casebook/all_cards_v2.json. Выход: _casebook/digests_db/<sid>.md + manifest.

Использование:
  python build_digests_from_db.py [MIN_MSGS=15]      # построить недостающие
"""
import sqlite3, json, re, sys, os
from pathlib import Path

H = Path.home()
DB = H / ".claude" / "chats.db"
CB = H / "_casebook"
OUT = CB / "digests_db"
OUT.mkdir(parents=True, exist_ok=True)

MIN_MSGS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
USER_CAP, ASST_CAP, DIGEST_CAP = 6000, 3000, 280_000

# системный/служебный шум — пропускать целиком
SKIP_PAT = re.compile(r"^\s*<(local-command|command-name|command-message|command-args|"
                      r"local-command-stdout|local-command-caveat|system-reminder|"
                      r"bash-(input|stdout|stderr))", re.I)


def demangle(s):
    # чинит редкий "символ-на-строку" (строки из 1 символа подряд)
    if s.count("\n") > len(s) * 0.4:
        lines = s.split("\n")
        if sum(1 for l in lines if len(l) <= 1) > len(lines) * 0.6:
            return "".join(lines)
    return s


def clean(s):
    s = demangle(s or "")
    s = re.sub(r"\n{3,}", "\n\n", s).strip()
    return s


def build():
    con = sqlite3.connect(str(DB))
    cur = con.cursor()
    # непокрытые кейсбуком
    cb = json.load(open(CB / "all_cards_v2.json", encoding="utf-8"))
    covered = set(str(x.get("session_id", "")).replace("cloud-", "") for x in cb if x.get("session_id"))
    # top-level интерактивные сессии: без субагент-транскриптов (agent-*), как в кейсбуке
    sessions = cur.execute(
        "SELECT session_id, created, message_count, first_prompt FROM sessions "
        "WHERE is_noise=0 AND message_count>=? AND session_id NOT LIKE 'agent-%' "
        "ORDER BY created", (MIN_MSGS,)).fetchall()
    todo = [s for s in sessions if s[0].replace("cloud-", "") not in covered]
    manifest = []
    written = 0
    for sid, created, mc, fp in todo:
        rows = cur.execute(
            "SELECT role, content, timestamp FROM messages WHERE session_id=? ORDER BY id", (sid,)).fetchall()
        parts, real_msgs = [], 0
        for role, content, ts in rows:
            c = clean(content)
            if not c or SKIP_PAT.match(c):
                continue
            if role == "user":
                if len(c) > USER_CAP:
                    c = c[:USER_CAP] + " …[trunc]"
                parts.append(f"### 👤 USER\n{c}\n")
                real_msgs += 1
            elif role == "assistant":
                if len(c) > ASST_CAP:
                    c = c[:ASST_CAP] + " …[trunc]"
                parts.append(f"### 🤖 ASSISTANT\n{c}\n")
                real_msgs += 1
        if real_msgs < 6:  # после чистки пусто/мелко
            continue
        date = (created or "")[:10]
        body = f"# Session {sid}  ({date})\n\n> source: chats.db (транскрипт стёрт/облако; msg_count={mc})\n\n" + "\n".join(parts)
        if len(body.encode("utf-8", "replace")) > DIGEST_CAP:
            body = body[:DIGEST_CAP // 2] + "\n\n…[MIDDLE TRUNCATED]…\n\n" + body[-DIGEST_CAP // 2:]
        (OUT / f"{sid}.md").write_text(body, encoding="utf-8", errors="replace")
        manifest.append({"session_id": sid, "date": date, "message_count": mc,
                         "digest_msgs": real_msgs, "first_prompt": (fp or "")[:200]})
        written += 1
    (OUT / "manifest.jsonl").write_text(
        "\n".join(json.dumps(m, ensure_ascii=False) for m in manifest), encoding="utf-8")
    con.close()
    print(f"[digests-from-db] порог>={MIN_MSGS}msg  непокрытых={len(todo)}  дайджестов записано={written}  -> {OUT}")
    print(f"manifest: {OUT / 'manifest.jsonl'}")


if __name__ == "__main__":
    build()
