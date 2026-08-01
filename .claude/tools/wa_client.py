"""
WhatsApp CLI for Claude Code (personal number, local-only).

Talks to a local Node.js bridge (Baileys) over loopback HTTP:
    bridge dir : ~/.claude/tools/wa-bridge   (override: WA_BRIDGE_DIR)
    bridge url : http://127.0.0.1:3000         (override: WA_BRIDGE_PORT)
    session    : <bridge dir>/.session         (override: WA_SESSION_DIR)  <- NEVER commit
    bridge log : <session>/../bridge.log
    store      : <session>/../store/store.json (chats/contacts/message index)

Credentials: none required. WhatsApp auth is the Baileys multi-file session
created by scanning a QR code once (`wa_client.py login`).
Optional env overrides live in ~/.claude/.credentials.master.env.

Pattern: connect -> do one thing -> print -> exit. The bridge process is the
only long-lived part (start it once with `bridge-start`).

WARNING: this drives a PERSONAL WhatsApp account through an unofficial client.
Bulk sending violates Meta's Terms of Service and gets numbers banned.
`broadcast` is dry-run by default and rate-limited on purpose — keep it that way.
"""

import argparse
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, date
from hashlib import sha1
from pathlib import Path

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_env():
    env_path = Path.home() / ".claude" / ".credentials.master.env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip()
                if key and not os.environ.get(key):
                    os.environ[key] = value


load_env()

# ---------------------------------------------------------------- config ----

# Дефолт берётся от расположения САМОГО скрипта, а не от жёстко вшитого пути:
# мост живёт рядом с клиентом, где бы ни лежала папка tools. Прежний хардкод раскрывал
# раскладку диска владельца и ломался у всех остальных.
DEFAULT_BRIDGE_DIR = Path(os.environ.get("WA_BRIDGE_DIR") or (Path(__file__).resolve().parent / "wa-bridge"))
DEFAULT_PORT = int(os.environ.get("WA_BRIDGE_PORT") or "3000")
DEFAULT_MODE = os.environ.get("WA_MODE") or "bot"  # "bot" = no Hermes reply prefix
IS_WINDOWS = os.name == "nt"


def port_of(args) -> int:
    return int(getattr(args, "port", None) or DEFAULT_PORT)


def bridge_dir(args) -> Path:
    return Path(getattr(args, "bridge_dir", None) or DEFAULT_BRIDGE_DIR).expanduser().resolve()


def session_dir(args) -> Path:
    explicit = getattr(args, "session", None) or os.environ.get("WA_SESSION_DIR")
    if explicit:
        return Path(explicit).expanduser().resolve()
    return bridge_dir(args) / ".session"


def base_url(args) -> str:
    return f"http://127.0.0.1:{port_of(args)}"


def pid_file(args) -> Path:
    return bridge_dir(args) / f".bridge-{port_of(args)}.pid"


def log_file(args) -> Path:
    return session_dir(args).parent / "bridge.log"


# ------------------------------------------------------------ http layer ----


class BridgeError(Exception):
    def __init__(self, message, hint=None, status=None, payload=None):
        super().__init__(message)
        self.message = message
        self.hint = hint
        self.status = status
        self.payload = payload or {}


def api(args, method, path, payload=None, params=None, timeout=60):
    """One HTTP call to the bridge. Raises BridgeError with a usable message."""
    url = base_url(args) + path
    if params:
        clean = {k: v for k, v in params.items() if v not in (None, "", False)}
        if clean:
            url += "?" + urllib.parse.urlencode(clean)

    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"

    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            parsed = json.loads(raw)
        except Exception:
            parsed = {"error": raw.strip()[:500] or exc.reason}
        raise BridgeError(
            parsed.get("error") or f"HTTP {exc.code}",
            hint=parsed.get("hint"),
            status=exc.code,
            payload=parsed,
        )
    except urllib.error.URLError as exc:
        raise BridgeError(
            f"Мост недоступен на {base_url(args)} ({exc.reason})",
            hint="Запусти мост:  python ~/.claude/tools/wa_client.py bridge-start",
        )
    except TimeoutError:
        raise BridgeError(f"Таймаут запроса к мосту ({path})")

    if not body:
        return {}
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        raise BridgeError(f"Мост вернул не-JSON ответ на {path}: {body[:200]}")


def health(args, timeout=3):
    return api(args, "GET", "/health", timeout=timeout)


def bridge_alive(args) -> bool:
    try:
        health(args, timeout=2)
        return True
    except BridgeError:
        return False


def require_connected(args):
    data = health(args)
    if data.get("status") != "connected":
        raise BridgeError(
            f"Мост запущен, но WhatsApp не подключён (status: {data.get('status')})",
            hint="Авторизуйся:  python ~/.claude/tools/wa_client.py login",
        )
    return data


# --------------------------------------------------------------- helpers ----


def norm_jid(value: str) -> str:
    """'+55 XX XXXXX-XXXX' -> '5581900000000@s.whatsapp.net'. Full JIDs pass through."""
    raw = str(value or "").strip()
    if not raw:
        raise BridgeError("Пустой JID/номер")
    if "@" in raw:
        return raw
    if re.fullmatch(r"\d+-\d+", raw):  # bare group id
        return raw + "@g.us"
    digits = re.sub(r"\D", "", raw)
    if not digits:
        raise BridgeError(
            f"Не понял получателя: {raw!r}",
            hint="Формат: +55 XX XXXXX-XXXX, 5581900000000 или полный JID 5581...@s.whatsapp.net / ...@g.us",
        )
    return digits + "@s.whatsapp.net"


def fmt_ts(epoch) -> str:
    try:
        epoch = int(epoch or 0)
    except (TypeError, ValueError):
        return ""
    if not epoch:
        return ""
    if epoch > 10_000_000_000:  # milliseconds
        epoch //= 1000
    return datetime.fromtimestamp(epoch).strftime("%Y-%m-%d %H:%M")


def short(text, width=70):
    text = (text or "").replace("\n", " ⏎ ").strip()
    return text if len(text) <= width else text[: width - 1] + "…"


def emit(args, data, human):
    if getattr(args, "json", False):
        print(json.dumps(data, ensure_ascii=False, indent=2))
    else:
        human(data)


def read_text_arg(value: str) -> str:
    """'@path/to/file.txt' loads text from a file; anything else is literal."""
    if isinstance(value, str) and value.startswith("@"):
        path = Path(value[1:]).expanduser()
        if path.exists():
            return path.read_text(encoding="utf-8")
    return value


# -------------------------------------------------------------- commands ----


def cmd_bridge_start(args):
    bdir = bridge_dir(args)
    script = bdir / "bridge.js"
    if not script.exists():
        raise BridgeError(
            f"Не найден bridge.js: {script}",
            hint="Укажи каталог моста: --bridge-dir <путь> или env WA_BRIDGE_DIR",
        )

    node = shutil.which("node")
    if not node:
        raise BridgeError(
            "Node.js не найден в PATH",
            hint="Поставь Node.js 18+ (проверено на 22.x): https://nodejs.org — затем перезапусти терминал",
        )

    if bridge_alive(args):
        data = health(args)
        return emit(
            args,
            {"already_running": True, **data},
            lambda d: print(
                f"✅ Мост уже запущен на {base_url(args)} (status: {d.get('status')}, pid: {d.get('pid')})"
            ),
        )

    if not (bdir / "node_modules" / "@whiskeysockets" / "baileys" / "package.json").exists():
        npm = shutil.which("npm")
        if not npm:
            raise BridgeError(
                "npm не найден, а зависимости моста не установлены",
                hint=f"Установи вручную:  cd {bdir} && npm install",
            )
        print(f"📦 Устанавливаю зависимости моста в {bdir} (может занять пару минут)...")
        proc = subprocess.run([npm, "install"], cwd=str(bdir), capture_output=True, text=True, timeout=600)
        if proc.returncode != 0:
            raise BridgeError(
                "npm install завершился с ошибкой",
                hint=(proc.stderr or proc.stdout or "").strip()[-800:]
                or f"Запусти вручную:  cd {bdir} && npm install",
            )
        print("📦 Зависимости установлены")

    sess = session_dir(args)
    sess.mkdir(parents=True, exist_ok=True)
    logp = log_file(args)
    logp.parent.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env.setdefault("WHATSAPP_REPLY_PREFIX", "")  # CLI must not prepend the Hermes banner
    if args.allowed_users:
        env["WHATSAPP_ALLOWED_USERS"] = args.allowed_users

    cmd = [
        node,
        str(script),
        "--port", str(port_of(args)),
        "--session", str(sess),
        "--mode", getattr(args, "mode", None) or DEFAULT_MODE,
    ]

    kwargs = {}
    if IS_WINDOWS:
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP — survives this CLI exiting
        kwargs["creationflags"] = 0x00000008 | 0x00000200
    else:
        kwargs["start_new_session"] = True

    log_fh = open(logp, "a", encoding="utf-8", errors="replace")
    log_fh.write(f"\n===== bridge start {datetime.now().isoformat(timespec='seconds')} =====\n")
    log_fh.flush()
    proc = subprocess.Popen(cmd, cwd=str(bdir), stdout=log_fh, stderr=log_fh, env=env, **kwargs)
    pid_file(args).write_text(str(proc.pid), encoding="utf-8")

    status = "starting"
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        time.sleep(1)
        if proc.poll() is not None:
            tail = "\n".join(logp.read_text(encoding="utf-8", errors="replace").splitlines()[-25:])
            raise BridgeError(
                f"Процесс моста упал (exit {proc.returncode})",
                hint=f"Лог: {logp}\n--- хвост лога ---\n{tail}",
            )
        try:
            data = health(args, timeout=2)
        except BridgeError:
            continue
        status = data.get("status", "unknown")
        if status == "connected":
            break

    result = {
        "started": True,
        "pid": proc.pid,
        "port": port_of(args),
        "status": status,
        "session": str(sess),
        "log": str(logp),
        "mode": getattr(args, "mode", None) or DEFAULT_MODE,
    }

    def human(d):
        print(f"🌉 Мост запущен: pid {d['pid']}, {base_url(args)} (mode: {d['mode']})")
        print(f"📁 Сессия: {d['session']}")
        print(f"📝 Лог:    {d['log']}")
        if d["status"] == "connected":
            print("✅ WhatsApp подключён")
        else:
            print(f"⏳ Статус: {d['status']} — нужна авторизация по QR:")
            print("   python ~/.claude/tools/wa_client.py login")

    emit(args, result, human)


def cmd_bridge_stop(args):
    pidp = pid_file(args)
    pid = None
    if pidp.exists():
        try:
            pid = int(pidp.read_text(encoding="utf-8").strip())
        except ValueError:
            pid = None
    if pid is None:
        try:
            pid = health(args, timeout=2).get("pid")
        except BridgeError:
            pid = None

    if not pid:
        return emit(
            args,
            {"stopped": False, "reason": "pid not found"},
            lambda d: print("ℹ️  Мост не запущен (pid-файл отсутствует и /health не отвечает)"),
        )

    killed = False
    if IS_WINDOWS:
        proc = subprocess.run(["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, text=True)
        killed = proc.returncode == 0
        detail = (proc.stdout or proc.stderr).strip()
    else:
        try:
            os.kill(pid, 15)
            killed = True
            detail = "SIGTERM sent"
        except ProcessLookupError:
            detail = "process already gone"
        except PermissionError as exc:
            detail = f"permission denied: {exc}"

    for _ in range(10):
        if not bridge_alive(args):
            break
        time.sleep(0.5)

    if pidp.exists():
        try:
            pidp.unlink()
        except OSError:
            pass

    emit(
        args,
        {"stopped": killed and not bridge_alive(args), "pid": pid, "detail": detail},
        lambda d: print(f"🛑 Мост остановлен (pid {d['pid']})" if d["stopped"] else f"⚠️  Не удалось остановить pid {d['pid']}: {d['detail']}"),
    )


def cmd_status(args):
    data = health(args)

    def human(d):
        icon = "✅" if d.get("status") == "connected" else "⏳"
        print(f"{icon} WhatsApp: {d.get('status')}   ({base_url(args)}, mode: {d.get('mode', '?')})")
        user = d.get("user") or {}
        if user:
            print(f"👤 Аккаунт: {user.get('name') or '—'}  id={user.get('id')}  lid={user.get('lid')}")
        print(f"⏱  Uptime: {int(d.get('uptime') or 0)}s   pid: {d.get('pid', '?')}   очередь: {d.get('queueLength')}")
        st = d.get("store") or {}
        if st:
            if st.get("enabled"):
                print(
                    f"💾 Store: {st.get('chats')} чатов, {st.get('contacts')} контактов, "
                    f"{st.get('messages')} сообщений "
                    f"({fmt_ts(st.get('oldestTimestamp'))} → {fmt_ts(st.get('newestTimestamp'))})"
                )
            else:
                print("💾 Store: выключен (WA_STORE=off) — chats/search/contacts недоступны")
        if d.get("hasQR"):
            print("📱 Есть неотсканированный QR — выполни: wa_client.py login")

    emit(args, data, human)


def cmd_login(args):
    deadline = time.time() + args.timeout
    shown = None
    last = {}
    while True:
        last = api(args, "GET", "/qr", timeout=10)
        if last.get("connection") == "connected":
            break
        qr = last.get("qr")
        if qr and qr != shown:
            shown = qr
            print("\n📱 Отсканируй QR: WhatsApp → Настройки → Связанные устройства → Привязка устройства\n")
            ascii_qr = last.get("ascii")
            if ascii_qr:
                print(ascii_qr)
            else:
                rendered = _render_qr_locally(qr)
                if rendered:
                    print(rendered)
                else:
                    print("(ASCII-QR недоступен из моста)")
                    print(f"Смотри QR в логе моста: {log_file(args)}")
                    print("Или поставь рендерер:  pip install qrcode")
                    print(f"\nСырая строка QR:\n{qr}\n")
        if time.time() >= deadline:
            break
        time.sleep(3)

    connected = last.get("connection") == "connected"
    result = {"connected": connected, "user": last.get("user"), "qr_pending": bool(last.get("qr"))}

    def human(d):
        if d["connected"]:
            user = d.get("user") or {}
            print(f"✅ Авторизован: {user.get('name') or ''} {user.get('id') or ''}".rstrip())
        else:
            print("⏳ Пока не авторизован. Запусти login ещё раз или увеличь --timeout.")

    emit(args, result, human)


def _render_qr_locally(payload):
    try:
        import qrcode  # optional dependency
    except ImportError:
        return None
    try:
        qr = qrcode.QRCode(border=1)
        qr.add_data(payload)
        qr.make(fit=True)
        buf = io.StringIO()
        qr.print_ascii(out=buf, invert=True)
        return buf.getvalue()
    except Exception:
        return None


def cmd_chats(args):
    data = api(args, "GET", "/chats", params={"limit": args.limit, "unread": "1" if args.unread else None,
                                              "groups": "1" if args.groups else None})

    def human(d):
        chats = d.get("chats", [])
        if not chats:
            print("Пусто. Store наполняется тем, что мост видел вживую + history-sync.")
            print("Подожди входящих/отправь сообщение, или запусти мост с syncFullHistory (см. SKILL.md).")
            return
        print(f"{'ЧАТ':<34} {'НЕПРОЧ':>6}  {'КОГДА':<16} ПОСЛЕДНЕЕ")
        print("-" * 110)
        for c in chats:
            last = c.get("lastMessage") or {}
            prefix = "→ " if last.get("fromMe") else ""
            print(
                f"{short(c.get('name'), 33):<34} {c.get('unreadCount') or 0:>6}  "
                f"{fmt_ts(c.get('timestamp')):<16} {prefix}{short(last.get('text'), 45)}"
            )
            print(f"{'':<34} {'':>6}  {c.get('id')}")
        cov = d.get("coverage") or {}
        print(f"\nВсего чатов в store: {d.get('total')} · сообщений: {cov.get('messages')}")

    emit(args, data, human)


def cmd_unread(args):
    args.unread = True
    args.groups = False
    cmd_chats(args)


def cmd_read_chat(args):
    jid = norm_jid(args.jid)
    data = api(args, "GET", f"/chat/{urllib.parse.quote(jid, safe='')}/messages", params={"limit": args.limit})

    def human(d):
        msgs = d.get("messages", [])
        if not msgs:
            print(f"Нет сообщений в store для {jid}.")
            print("Store покрывает только то, что мост видел вживую (+ history-sync).")
            return
        print(f"=== {jid} · показано {len(msgs)} из {d.get('total')} ===\n")
        for m in msgs:
            who = "Я" if m.get("fromMe") else (m.get("senderName") or m.get("senderId"))
            media = f" [{m['mediaType']}]" if m.get("mediaType") else ""
            print(f"[{fmt_ts(m.get('timestamp'))}] {who}{media}: {m.get('text') or ''}")
            if args.ids:
                print(f"            id={m.get('id')}")

    emit(args, data, human)


def cmd_send(args):
    require_connected(args)
    jid = norm_jid(args.jid)
    text = read_text_arg(args.text)
    data = api(args, "POST", "/send", payload={"chatId": jid, "message": text})
    emit(args, {"chatId": jid, **data}, lambda d: print(f"✅ Отправлено в {jid} (messageId: {d.get('messageId')})"))


def cmd_send_media(args):
    require_connected(args)
    jid = norm_jid(args.jid)
    path = Path(args.file).expanduser().resolve()
    if not path.exists():
        raise BridgeError(f"Файл не найден: {path}")
    payload = {"chatId": jid, "filePath": str(path)}
    if args.caption:
        payload["caption"] = args.caption
    if args.type:
        payload["mediaType"] = args.type
    if args.filename:
        payload["fileName"] = args.filename
    data = api(args, "POST", "/send-media", payload=payload, timeout=180)
    emit(args, {"chatId": jid, "file": str(path), **data},
         lambda d: print(f"✅ Медиа отправлено в {jid}: {path.name} (messageId: {d.get('messageId')})"))


def cmd_edit(args):
    require_connected(args)
    jid = norm_jid(args.jid)
    data = api(args, "POST", "/edit", payload={"chatId": jid, "messageId": args.message_id,
                                               "message": read_text_arg(args.text)})
    emit(args, {"chatId": jid, **data}, lambda d: print(f"✅ Сообщение {args.message_id} отредактировано"))


def cmd_typing(args):
    require_connected(args)
    jid = norm_jid(args.jid)
    data = api(args, "POST", "/typing", payload={"chatId": jid})
    emit(args, {"chatId": jid, **data}, lambda d: print(f"⌨️  Индикатор набора отправлен в {jid}"))


def cmd_contacts(args):
    data = api(args, "GET", "/contacts", params={"q": args.q, "limit": args.limit})

    def human(d):
        contacts = d.get("contacts", [])
        if not contacts:
            print("Контактов в store нет (WhatsApp отдаёт их при history-sync / при входящих).")
            return
        print(f"{'ИМЯ':<32} {'НОМЕР':<18} JID")
        print("-" * 90)
        for c in contacts:
            print(f"{short(c.get('displayName'), 31):<32} {c.get('number', ''):<18} {c.get('id')}")
        print(f"\nВсего: {d.get('total')}")

    emit(args, data, human)


def cmd_groups(args):
    require_connected(args)
    data = api(args, "GET", "/groups", timeout=90)

    def human(d):
        groups = d.get("groups", [])
        if not groups:
            print("Групп не найдено.")
            return
        print(f"{'ГРУППА':<40} {'УЧАСТНИКОВ':>10}  JID")
        print("-" * 100)
        for g in groups:
            print(f"{short(g.get('subject'), 39):<40} {g.get('size') or 0:>10}  {g.get('id')}")
        print(f"\nВсего групп: {d.get('count')}")

    emit(args, data, human)


def cmd_search(args):
    data = api(args, "GET", "/search", params={"q": args.query, "limit": args.limit,
                                               "chat": norm_jid(args.chat) if args.chat else None})

    def human(d):
        results = d.get("results", [])
        if not results:
            print(f"Ничего не найдено по «{args.query}».")
        else:
            for m in results:
                who = "Я" if m.get("fromMe") else (m.get("senderName") or "")
                print(f"[{fmt_ts(m.get('timestamp'))}] {short(m.get('chatName'), 22)} · {who}: {short(m.get('text'), 80)}")
                print(f"            {m.get('chatId')}  id={m.get('id')}")
        cov = d.get("coverage") or {}
        print(f"\nИсточник: {d.get('source')} · охват: {cov.get('messages')} сообщений "
              f"({fmt_ts(cov.get('oldestTimestamp'))} → {fmt_ts(cov.get('newestTimestamp'))})")

    emit(args, data, human)


def cmd_mark_read(args):
    require_connected(args)
    jid = norm_jid(args.jid)
    data = api(args, "POST", "/mark-read", payload={"chatId": jid, "limit": args.limit})
    emit(args, data, lambda d: print(f"✅ Прочитано: {d.get('marked')} сообщений в {d.get('chatId')}"))


def cmd_download_media(args):
    require_connected(args)
    params = {"dir": str(Path(args.dir).expanduser().resolve())} if args.dir else None
    data = api(args, "GET", f"/media/{urllib.parse.quote(args.message_id, safe='')}", params=params, timeout=300)
    emit(args, data, lambda d: print(f"✅ Сохранено: {d.get('path')} ({d.get('size')} байт, {d.get('mimetype')})"))


def cmd_profile(args):
    require_connected(args)
    jid = norm_jid(args.jid)
    data = api(args, "GET", f"/profile/{urllib.parse.quote(jid, safe='')}", timeout=60)

    def human(d):
        print(f"JID:     {d.get('jid')}")
        print(f"Тип:     {'группа' if d.get('isGroup') else 'контакт'}")
        if d.get("isGroup"):
            print(f"Название: {d.get('subject') or d.get('name') or '—'}")
            print(f"Описание: {short(d.get('desc'), 100) or '—'}")
            print(f"Участников: {d.get('size')}")
        else:
            print(f"Имя:     {d.get('name') or '—'}")
            print(f"Статус:  {d.get('status') or d.get('statusError') or '—'}")
            if d.get("businessProfile"):
                print(f"Бизнес:  {json.dumps(d['businessProfile'], ensure_ascii=False)[:300]}")
        print(f"Аватар:  {d.get('pictureUrl') or d.get('pictureError') or '—'}")

    emit(args, data, human)


def cmd_export_chat(args):
    jid = norm_jid(args.jid)
    data = api(args, "GET", f"/chat/{urllib.parse.quote(jid, safe='')}/messages", params={"limit": args.limit})
    msgs = data.get("messages", [])

    if args.format == "json":
        content = json.dumps(data, ensure_ascii=False, indent=2)
    else:
        lines = [f"# WhatsApp export — {jid}",
                 f"# exported: {datetime.now().isoformat(timespec='seconds')}",
                 f"# messages: {len(msgs)} (bridge-local store, не полная история телефона)", ""]
        for m in msgs:
            who = "Я" if m.get("fromMe") else (m.get("senderName") or m.get("senderId"))
            media = f" [{m['mediaType']}]" if m.get("mediaType") else ""
            lines.append(f"[{fmt_ts(m.get('timestamp'))}] {who}{media}: {m.get('text') or ''}")
        content = "\n".join(lines)

    if args.out:
        out = Path(args.out).expanduser().resolve()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(content, encoding="utf-8")
        emit(args, {"chatId": jid, "messages": len(msgs), "file": str(out)},
             lambda d: print(f"✅ Экспортировано {d['messages']} сообщений → {d['file']}"))
    else:
        if getattr(args, "json", False):
            print(json.dumps({"chatId": jid, "messages": msgs}, ensure_ascii=False, indent=2))
        else:
            print(content)


# ------------------------------------------------------------- broadcast ----


def broadcast_state_path(args, recipients_file: Path) -> Path:
    if args.state:
        return Path(args.state).expanduser().resolve()
    digest = sha1(str(recipients_file).encode("utf-8")).hexdigest()[:10]
    return bridge_dir(args) / ".broadcast" / f"{recipients_file.stem}-{digest}.json"


def load_state(path: Path) -> dict:
    if path.exists():
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"sent": {}, "failed": {}, "daily": {}}


def save_state(path: Path, state: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def parse_recipients(path: Path):
    """One recipient per line: `<phone|jid>[,Name]`. `#` starts a comment."""
    out = []
    for lineno, raw in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        parts = [p.strip() for p in line.split(",", 1)]
        try:
            jid = norm_jid(parts[0])
        except BridgeError as exc:
            raise BridgeError(f"{path}:{lineno}: {exc.message}", hint=exc.hint)
        name = parts[1] if len(parts) > 1 and parts[1] else jid.split("@")[0]
        out.append({"jid": jid, "name": name})
    return out


def cmd_broadcast(args):
    recipients_file = Path(args.file).expanduser().resolve()
    if not recipients_file.exists():
        raise BridgeError(
            f"Файл со списком получателей не найден: {recipients_file}",
            hint="Формат: одна строка = `+55 XX XXXXX-XXXX,Имя`; строки с # — комментарии",
        )

    if args.min_delay < 20 or args.max_delay < args.min_delay:
        raise BridgeError(
            f"Некорректные задержки: --min-delay {args.min_delay}, --max-delay {args.max_delay}",
            hint="Минимум 20 с между отправками; --max-delay должен быть >= --min-delay (дефолт 45-120 с)",
        )

    text_template = read_text_arg(args.text)
    recipients = parse_recipients(recipients_file)
    state_path = broadcast_state_path(args, recipients_file)
    state = load_state(state_path)
    stop_path = Path(args.stop_file).expanduser().resolve() if args.stop_file else (bridge_dir(args) / ".broadcast" / "STOP")

    today = date.today().isoformat()
    sent_today = int(state.get("daily", {}).get(today, 0))
    pending = [r for r in recipients if r["jid"] not in state.get("sent", {})]
    quota_left = max(0, args.max - sent_today)
    batch = pending[:quota_left]

    live = bool(args.confirm) and not args.dry_run
    if live:
        require_connected(args)

    header = {
        "recipients_file": str(recipients_file),
        "total": len(recipients),
        "already_sent": len(recipients) - len(pending),
        "pending": len(pending),
        "daily_limit": args.max,
        "sent_today": sent_today,
        "will_send_now": len(batch),
        "delay_range_sec": [args.min_delay, args.max_delay],
        "dry_run": not live,
        "state_file": str(state_path),
        "stop_file": str(stop_path),
    }

    if not getattr(args, "json", False):
        print("=" * 72)
        print("WhatsApp broadcast" + ("  [DRY-RUN — ничего не отправляется]" if not live else "  [LIVE]"))
        print("=" * 72)
        print(f"Получателей в файле : {header['total']} (уже отправлено ранее: {header['already_sent']})")
        print(f"Лимит на сутки      : {args.max} (сегодня отправлено: {sent_today})")
        print(f"Будет отправлено    : {len(batch)}")
        print(f"Задержка            : {args.min_delay}-{args.max_delay} с со случайным джиттером")
        print(f"Состояние           : {state_path}")
        print(f"Стоп-файл           : {stop_path}  (создай его, чтобы прервать)")
        if not live:
            print("\n⚠️  DRY-RUN по умолчанию. Реальная отправка — только с флагом --confirm.")
            print("⚠️  Массовые рассылки нарушают ToS Meta и приводят к бану номера. На свой риск.")
        print("-" * 72)

    results = []
    for idx, rec in enumerate(batch, 1):
        if stop_path.exists():
            results.append({"jid": rec["jid"], "status": "stopped"})
            if not getattr(args, "json", False):
                print(f"🛑 Обнаружен стоп-файл {stop_path} — остановка на {idx}/{len(batch)}")
            break

        message = (text_template
                   .replace("{name}", rec["name"])
                   .replace("{jid}", rec["jid"])
                   .replace("{number}", rec["jid"].split("@")[0]))

        if not live:
            results.append({"jid": rec["jid"], "name": rec["name"], "status": "dry-run", "preview": message})
            if not getattr(args, "json", False):
                print(f"[{idx}/{len(batch)}] DRY-RUN → {rec['name']} ({rec['jid']}): {short(message, 60)}")
            continue

        try:
            if not args.no_typing:
                try:
                    api(args, "POST", "/typing", payload={"chatId": rec["jid"]}, timeout=15)
                    time.sleep(random.uniform(2, 6))
                except BridgeError:
                    pass
            resp = api(args, "POST", "/send", payload={"chatId": rec["jid"], "message": message}, timeout=90)
            state.setdefault("sent", {})[rec["jid"]] = {
                "at": datetime.now().isoformat(timespec="seconds"),
                "messageId": resp.get("messageId"),
                "name": rec["name"],
            }
            sent_today += 1
            state.setdefault("daily", {})[today] = sent_today
            save_state(state_path, state)
            results.append({"jid": rec["jid"], "name": rec["name"], "status": "sent", "messageId": resp.get("messageId")})
            if not getattr(args, "json", False):
                print(f"[{idx}/{len(batch)}] ✅ {rec['name']} ({rec['jid']}) — messageId {resp.get('messageId')}")
        except BridgeError as exc:
            state.setdefault("failed", {})[rec["jid"]] = {
                "at": datetime.now().isoformat(timespec="seconds"),
                "error": exc.message,
            }
            save_state(state_path, state)
            results.append({"jid": rec["jid"], "name": rec["name"], "status": "failed", "error": exc.message})
            if not getattr(args, "json", False):
                print(f"[{idx}/{len(batch)}] ❌ {rec['name']} ({rec['jid']}): {exc.message}")
            if args.stop_on_error:
                break

        if idx < len(batch):
            delay = random.uniform(args.min_delay, args.max_delay)
            if not getattr(args, "json", False):
                print(f"      ⏳ пауза {delay:.0f} с (анти-бан)")
            time.sleep(delay)

    summary = {
        **header,
        "results": results,
        "sent_ok": sum(1 for r in results if r["status"] == "sent"),
        "failed": sum(1 for r in results if r["status"] == "failed"),
    }

    if getattr(args, "json", False):
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        print("-" * 72)
        if live:
            print(f"Итог: отправлено {summary['sent_ok']}, ошибок {summary['failed']}, "
                  f"осталось в очереди {max(0, len(pending) - len(batch))}")
        else:
            print(f"DRY-RUN завершён. Для реальной отправки добавь --confirm")


# ------------------------------------------------------------------ main ----


def build_parser():
    # default=SUPPRESS everywhere: these flags may appear BEFORE or AFTER the
    # subcommand, and argparse would otherwise let the subparser's defaults
    # clobber a value already parsed by the main parser.
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="Машинный вывод (JSON)")
    common.add_argument("--port", type=int, default=argparse.SUPPRESS,
                        help=f"Порт моста (env WA_BRIDGE_PORT, деф {DEFAULT_PORT})")
    common.add_argument("--bridge-dir", default=argparse.SUPPRESS,
                        help=f"Каталог моста (env WA_BRIDGE_DIR, деф {DEFAULT_BRIDGE_DIR})")
    common.add_argument("--session", default=argparse.SUPPRESS,
                        help="Каталог сессии Baileys (env WA_SESSION_DIR, деф <bridge-dir>/.session)")

    parser = argparse.ArgumentParser(
        prog="wa_client.py",
        parents=[common],
        description="WhatsApp CLI поверх локального Baileys-моста (личный номер, всё локально).",
        epilog="Старт: bridge-start → login (QR с телефона) → chats / send / search. "
               "Массовая рассылка (broadcast) нарушает ToS Meta — используй на свой риск.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", metavar="COMMAND")

    p = sub.add_parser("bridge-start", parents=[common], help="Поднять Node-мост в фоне (и поставить зависимости)")
    p.add_argument("--mode", default=DEFAULT_MODE, choices=["bot", "self-chat"],
                   help="Режим моста: bot (без Hermes-префикса, деф для CLI) | self-chat")
    p.add_argument("--allowed-users", help="WHATSAPP_ALLOWED_USERS для очереди /messages (CLI это не нужно)")
    p.add_argument("--timeout", type=int, default=40, help="Сколько секунд ждать подключения (деф 40)")
    p.set_defaults(func=cmd_bridge_start)

    p = sub.add_parser("bridge-stop", parents=[common], help="Остановить мост")
    p.set_defaults(func=cmd_bridge_stop)

    p = sub.add_parser("status", parents=[common], help="Состояние моста и WhatsApp (/health)")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("login", parents=[common], help="Показать QR для привязки устройства и дождаться сканирования")
    p.add_argument("--timeout", type=int, default=180, help="Сколько секунд ждать сканирования (деф 180)")
    p.set_defaults(func=cmd_login)

    p = sub.add_parser("chats", parents=[common], help="Список чатов с последним сообщением и непрочитанными")
    p.add_argument("--limit", type=int, default=30)
    p.add_argument("--unread", action="store_true", help="Только с непрочитанными")
    p.add_argument("--groups", action="store_true", help="Только группы")
    p.set_defaults(func=cmd_chats)

    p = sub.add_parser("unread", parents=[common], help="Только чаты с непрочитанными сообщениями")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_unread)

    p = sub.add_parser("read-chat", parents=[common], help="История одного чата из store моста")
    p.add_argument("jid", help="Номер (+5581...) или полный JID")
    p.add_argument("--limit", type=int, default=50)
    p.add_argument("--ids", action="store_true", help="Показывать messageId (нужен для edit/download-media)")
    p.set_defaults(func=cmd_read_chat)

    p = sub.add_parser("send", parents=[common], help="Отправить текстовое сообщение")
    p.add_argument("jid")
    p.add_argument("text", help="Текст или @path/to/file.txt")
    p.set_defaults(func=cmd_send)

    p = sub.add_parser("send-media", parents=[common], help="Отправить файл (image/video/audio/document)")
    p.add_argument("jid")
    p.add_argument("file")
    p.add_argument("--caption")
    p.add_argument("--type", choices=["image", "video", "audio", "document"], help="Иначе определяется по расширению")
    p.add_argument("--filename", help="Имя файла у получателя (для document)")
    p.set_defaults(func=cmd_send_media)

    p = sub.add_parser("edit", parents=[common], help="Отредактировать своё отправленное сообщение")
    p.add_argument("jid")
    p.add_argument("message_id")
    p.add_argument("text")
    p.set_defaults(func=cmd_edit)

    p = sub.add_parser("typing", parents=[common], help="Отправить индикатор набора")
    p.add_argument("jid")
    p.set_defaults(func=cmd_typing)

    p = sub.add_parser("contacts", parents=[common], help="Контакты, известные мосту")
    p.add_argument("--q", help="Фильтр по имени/номеру")
    p.add_argument("--limit", type=int, default=200)
    p.set_defaults(func=cmd_contacts)

    p = sub.add_parser("groups", parents=[common], help="Группы аккаунта (живой запрос к WhatsApp)")
    p.set_defaults(func=cmd_groups)

    p = sub.add_parser("search", parents=[common], help="Поиск по сообщениям в store моста")
    p.add_argument("query")
    p.add_argument("--chat", help="Ограничить одним чатом")
    p.add_argument("--limit", type=int, default=30)
    p.set_defaults(func=cmd_search)

    p = sub.add_parser("mark-read", parents=[common], help="Отметить чат прочитанным")
    p.add_argument("jid")
    p.add_argument("--limit", type=int, default=30, help="Сколько последних входящих подтвердить (деф 30)")
    p.set_defaults(func=cmd_mark_read)

    p = sub.add_parser("download-media", parents=[common], help="Скачать медиа сообщения по messageId")
    p.add_argument("message_id")
    p.add_argument("--dir", help="Каталог назначения (деф <store>/media)")
    p.set_defaults(func=cmd_download_media)

    p = sub.add_parser("profile", parents=[common], help="Профиль контакта/группы (аватар, статус, участники)")
    p.add_argument("jid")
    p.set_defaults(func=cmd_profile)

    p = sub.add_parser("export-chat", parents=[common], help="Выгрузить чат в файл (txt/json)")
    p.add_argument("jid")
    p.add_argument("--out", help="Файл назначения (иначе печать в stdout)")
    p.add_argument("--limit", type=int, default=5000)
    p.add_argument("--format", choices=["txt", "json"], default="txt")
    p.set_defaults(func=cmd_export_chat)

    p = sub.add_parser(
        "broadcast", parents=[common],
        help="Рассылка по списку с анти-бан гардами (DRY-RUN по умолчанию)",
        description="ВНИМАНИЕ: массовые рассылки нарушают ToS Meta и приводят к блокировке номера. "
                    "Дефолт — dry-run; реальная отправка только с --confirm.",
    )
    p.add_argument("file", help="Файл со списком: строка `+55 XX XXXXX-XXXX,Имя`, # — комментарий")
    p.add_argument("text", help="Текст или @path/to/file.txt; плейсхолдеры {name} {jid} {number}")
    p.add_argument("--confirm", action="store_true", help="РЕАЛЬНАЯ отправка (без него — dry-run)")
    p.add_argument("--dry-run", action="store_true", default=False, help="Явный dry-run (и так дефолт)")
    p.add_argument("--max", type=int, default=50, help="Лимит отправок в сутки (деф 50)")
    p.add_argument("--min-delay", type=float, default=45, help="Мин. пауза между адресатами, с (деф 45, минимум 20)")
    p.add_argument("--max-delay", type=float, default=120, help="Макс. пауза между адресатами, с (деф 120)")
    p.add_argument("--state", help="Файл состояния для резюмируемости (деф <bridge>/.broadcast/<файл>.json)")
    p.add_argument("--stop-file", help="Стоп-файл (деф <bridge>/.broadcast/STOP)")
    p.add_argument("--no-typing", action="store_true", help="Не слать индикатор набора перед сообщением")
    p.add_argument("--stop-on-error", action="store_true", help="Прервать рассылку на первой ошибке")
    p.set_defaults(func=cmd_broadcast)

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 0
    try:
        args.func(args)
    except BridgeError as exc:
        print(f"❌ {exc.message}", file=sys.stderr)
        if exc.hint:
            print(f"💡 {exc.hint}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\n⏹  Прервано пользователем", file=sys.stderr)
        return 130
    return 0


if __name__ == "__main__":
    sys.exit(main())
