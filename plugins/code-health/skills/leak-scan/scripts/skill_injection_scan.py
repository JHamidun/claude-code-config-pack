#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Входящий скан чужого скилла / плагина / агента перед установкой.

Ищет prompt-injection и тихий захват полномочий в коде, который попадёт
в авто-загружаемый каталог (~/.claude/skills, ~/.claude/plugins, ~/.claude/agents).

Дополняет leak_scan.py: тот проверяет ИСХОДЯЩЕЕ (мои данные наружу),
этот — ВХОДЯЩЕЕ (чужие инструкции и чужой код внутрь).

Только stdlib. Ничего не меняет на диске. Коды выхода: 0 чисто / 1 находки / 2 скан не завершён.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

# --------------------------------------------------------------------------- #
# Лимиты
# --------------------------------------------------------------------------- #

MAX_FILES = 4000
MAX_FILE_BYTES = 2 * 1024 * 1024
MAX_TOTAL_BYTES = 40 * 1024 * 1024

SKIP_DIRS = {".git", "__pycache__", ".venv", "venv", ".mypy_cache", ".pytest_cache", ".idea"}
VENDOR_DIRS = {"node_modules", "dist", "build", ".next", "site-packages"}

TEXT_EXT = {
    ".md", ".markdown", ".txt", ".json", ".yaml", ".yml", ".toml", ".cfg", ".ini",
    ".py", ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".js", ".mjs", ".cjs", ".ts",
    ".tsx", ".jsx", ".bat", ".cmd", ".rb", ".pl", ".php", ".env", ".xml", ".html",
}
CODE_EXT = {
    ".py", ".sh", ".bash", ".zsh", ".ps1", ".psm1", ".js", ".mjs", ".cjs",
    ".ts", ".tsx", ".jsx", ".bat", ".cmd", ".rb", ".pl", ".php",
}
BINARY_ARTIFACT_EXT = {".exe", ".dll", ".so", ".dylib", ".node", ".msi", ".scr", ".jar", ".pyd"}

SEVERITIES = ("CRITICAL", "WARN", "INFO")
SEV_RANK = {"CRITICAL": 0, "WARN": 1, "INFO": 2}

# --------------------------------------------------------------------------- #
# Невидимый Unicode
# --------------------------------------------------------------------------- #

_INVISIBLE_CODEPOINTS = {
    0x00AD,  # soft hyphen
    0x180E,  # mongolian vowel separator
    0x200B,  # zero width space
    0x200C,  # zero width non-joiner
    0x200D,  # zero width joiner
    0x200E,  # left-to-right mark
    0x200F,  # right-to-left mark
    0x2060,  # word joiner
    0x2061, 0x2062, 0x2063, 0x2064,  # invisible math operators
    0xFEFF,  # BOM внутри файла (ведущий снимается utf-8-sig)
}
# bidi-переопределения — «trojan source»: текст на экране не равен тексту для модели
_BIDI_CODEPOINTS = set(range(0x202A, 0x202F)) | set(range(0x2066, 0x206A))


def _is_invisible(cp: int) -> bool:
    return cp in _INVISIBLE_CODEPOINTS or cp in _BIDI_CODEPOINTS or 0xE0000 <= cp <= 0xE007F


def _is_emoji(cp: int) -> bool:
    """Пиктографические кодпойнты — чтобы не считать легитимный emoji-ZWJ инъекцией."""
    return (
        0x1F000 <= cp <= 0x1FAFF          # эмодзи-блоки (symbols & pictographs, supplemental, extended-A)
        or 0x2600 <= cp <= 0x27BF          # misc symbols + dingbats
        or 0x1F1E6 <= cp <= 0x1F1FF        # regional indicators (флаги)
        or 0x1F3FB <= cp <= 0x1F3FF        # skin-tone modifiers
        or cp in (0xFE0F, 0x203C, 0x2049, 0x2122, 0x2139)
        or 0x2190 <= cp <= 0x21FF          # arrows (стрелки-эмодзи)
        or 0x2300 <= cp <= 0x23FF          # misc technical (⌚⏰ и пр.)
    )


# --------------------------------------------------------------------------- #
# Текстовые правила (md, doc, любой текст)
# --------------------------------------------------------------------------- #

_TEXT_RULES: tuple[tuple[str, str, re.Pattern[str], str], ...] = (
    (
        "prompt.ignore_previous", "CRITICAL",
        re.compile(
            r"\b(?:ignore|forget|override|bypass)\s+(?:all\s+|any\s+|the\s+|your\s+)*"
            r"(?:previous|prior|above|earlier|preceding|system)\s+"
            r"(?:instructions?|prompts?|rules?|messages?|guidelines?)\b"
            r"|(?:игнорируй|забудь|отмени|отбрось)\s+"
            r"(?:все\s+|всё\s+|свои\s+|предыдущие\s+|прошлые\s+|эти\s+|системные\s+|данные\s+тебе\s+|выше\s+)+"
            r"(?:инструкц|правил|указан|промпт|сообщени)",
            re.IGNORECASE,
        ),
        "фраза-перехват: приказ проигнорировать предыдущие инструкции",
    ),
    (
        "prompt.disregard_system", "CRITICAL",
        re.compile(
            r"\bdisregard\s+(?:the\s+|your\s+)?(?:system|developer|operator)\b"
            r"|\bsystem\s+prompt\s+(?:is\s+)?(?:void|cancell?ed|no longer|overridden)\b"
            r"|(?:не\s+слушай|игнорируй)\s+(?:системн|разработчик)",
            re.IGNORECASE,
        ),
        "приказ отменить системную инструкцию",
    ),
    (
        "prompt.role_reassignment", "WARN",
        re.compile(
            r"\byou\s+are\s+now\s+(?:a|an|the|in\s|no\s+longer)\b"
            r"|\bfrom\s+now\s+on[, ]+you\s+(?:are|will|must)\b"
            r"|(?:теперь|отныне)\s+ты\s+(?:—\s*)?(?:не\s+)?[а-яё]",
            re.IGNORECASE,
        ),
        "переназначение роли модели",
    ),
    (
        "prompt.fake_system_prefix", "CRITICAL",
        re.compile(
            r"^\s*(?:[-*>]\s*)?(?:system|developer|operator|assistant)\s*:\s*"
            r"(?:you\b|your\b|ignore\b|do not\b|don't\b|never\b|always\b|from now\b"
            r"|ты\b|игнорируй\b|никогда\b|всегда\b)",
            re.IGNORECASE,
        ),
        "поддельный префикс системного сообщения",
    ),
    (
        "prompt.system_tag", "CRITICAL",
        re.compile(r"<\s*/?\s*(?:system|system-reminder|important_instructions)\b[^>]*>", re.IGNORECASE),
        "поддельный системный тег",
    ),
    (
        "prompt.chat_template_tag", "CRITICAL",
        re.compile(
            r"<\|\s*(?:im_start|im_end|system|endoftext|start_header_id)\s*\|>"
            r"|\[\s*/?\s*INST\s*\]|<\s*/?\s*\|?\s*(?:antml:)?function_calls\s*\|?\s*>",
            re.IGNORECASE,
        ),
        "разделитель чат-шаблона модели",
    ),
    (
        "prompt.tool_call_tag", "CRITICAL",
        re.compile(
            r"<\s*/?\s*(?:tool_call|tool_use|antml:invoke|invoke\s+name=|function_results)\b",
            re.IGNORECASE,
        ),
        "литеральный тег вызова инструмента",
    ),
    (
        "prompt.covert_directive", "CRITICAL",
        re.compile(
            r"\b(?:do\s+not|don't|never)\s+(?:tell|inform|mention|show|reveal|report)\s+"
            r"(?:this\s+|it\s+)?(?:to\s+)?(?:the\s+)?(?:user|human|owner|operator)\b"
            r"|\bwithout\s+(?:telling|informing|asking)\s+the\s+user\b"
            r"|\bsilently\s+(?:run|execute|send|append)\b"
            r"|(?:не\s+(?:сообщай|говори|показывай|упоминай))\s+(?:это\s+)?пользовател"
            r"|скрой\s+(?:это\s+)?от\s+пользовател",
            re.IGNORECASE,
        ),
        "приказ действовать скрытно от пользователя",
    ),
    (
        "prompt.autonomy_grab", "CRITICAL",
        re.compile(
            r"--dangerously-skip-permissions|\bbypassPermissions\b"
            r"|\b(?:disable|skip|turn\s+off)\s+(?:the\s+)?(?:permission|approval|confirmation)\s+"
            r"(?:prompt|check|system)s?\b",
            re.IGNORECASE,
        ),
        "попытка снять систему разрешений",
    ),
    (
        "prompt.memory_write", "WARN",
        re.compile(
            r"\b(?:append|write|add)\s+(?:this|the following)[^\n]{0,40}\b(?:CLAUDE\.md|MEMORY\.md|settings\.json)\b"
            r"|\bedit\s+(?:your\s+)?(?:CLAUDE\.md|settings\.json)\b",
            re.IGNORECASE,
        ),
        "инструкция дописать себя в постоянную память/конфиг",
    ),
)

_HTML_COMMENT = re.compile(r"<!--(.*?)-->", re.DOTALL)
_HIDDEN_DIRECTIVE = re.compile(
    r"\b(?:ignore|disregard|you\s+are\s+now|do\s+not\s+tell|always|never|must|execute|run|send|fetch)\b"
    r"|(?:игнорируй|выполни|отправь|никогда|всегда)",
    re.IGNORECASE,
)
_HIDDEN_STYLE = re.compile(
    r"(?:display\s*:\s*none|font-size\s*:\s*0|visibility\s*:\s*hidden"
    r"|color\s*:\s*#?(?:fff(?:fff)?|white)\b)",
    re.IGNORECASE,
)
_B64_BLOB = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{400,}={0,2}(?![A-Za-z0-9+/=])")

# --------------------------------------------------------------------------- #
# Форма эксфильтрации
# --------------------------------------------------------------------------- #

_OUTBOUND = re.compile(
    r"\b(?:curl|wget|Invoke-WebRequest|Invoke-RestMethod|iwr|irm)\b"
    r"|\bfetch\s*\(|\baxios\.(?:post|put|get)\b|\brequests\.(?:post|put)\b"
    r"|\burllib\.request\.urlopen\b|\bhttpx\.(?:post|put)\b|\bnc\s+-\w*\s",
    re.IGNORECASE,
)
_SECRET_REF = re.compile(
    r"\.credentials\.master\.env|\.env\b|\.ssh[/\\]|id_rsa|id_ed25519"
    r"|\.aws[/\\]credentials|\.claude[/\\]settings|chats\.db|Login\s+Data|Cookies\b"
    r"|\b[A-Z][A-Z0-9_]*(?:API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL)S?\b"
    r"|process\.env\.[A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)"
    r"|os\.environ(?:\.get)?[\[(]\s*[\"'][A-Za-z0-9_]*(?:KEY|TOKEN|SECRET|PASSWORD)",
    re.IGNORECASE,
)
_URL = re.compile(r"https?://([A-Za-z0-9._~%-]+)", re.IGNORECASE)

# известные каналы, куда секрет уходит легитимно (или это заведомо пример из доков)
_VENDOR_HOSTS = re.compile(
    r"(?:^|\.)(?:"
    r"localhost|127\.0\.0\.1|0\.0\.0\.0|host\.docker\.internal"
    r"|anthropic\.com|openai\.com|azure\.com|googleapis\.com|google\.com|gstatic\.com"
    r"|telegram\.org|deepseek\.com|perplexity\.ai|elevenlabs\.io|deepgram\.com"
    r"|github\.com|githubusercontent\.com|gitlab\.com|npmjs\.(?:com|org)|pypi\.org"
    r"|yandex\.(?:ru|net|com)|vk\.com|bitrix24\.(?:ru|com)|tildacdn\.com|tilda\.cc"
    r"|replicate\.com|runwayml\.com|heygen\.com|deepl\.com|serpapi\.com"
    r"|example\.(?:com|org|net)|localhost\.localdomain"
    r")$",
    re.IGNORECASE,
)
# классические приёмники эксфильтрации
_BAD_SINK = re.compile(
    r"\b(?:webhook\.site|requestbin\.\w+|pipedream\.net|\w+\.ngrok(?:-free)?\.(?:io|app|dev)"
    r"|burpcollaborator\.net|oast(?:ify|\.\w+)|interact\.sh|\w+\.oastify\.com"
    r"|discord(?:app)?\.com/api/webhooks|termbin\.com|transfer\.sh|0x0\.st"
    r"|paste\.ee|ix\.io|dpaste\.\w+|file\.io)\b",
    re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Правила для кода
# --------------------------------------------------------------------------- #

_CODE_RULES: tuple[tuple[str, str, re.Pattern[str], str], ...] = (
    (
        "code.remote_exec", "CRITICAL",
        re.compile(
            r"(?:curl|wget)[^\n|]{0,200}\|\s*(?:sudo\s+)?(?:ba|z|d)?sh\b"
            r"|(?:iwr|Invoke-WebRequest|irm|Invoke-RestMethod)[^\n|]{0,200}\|\s*(?:iex|Invoke-Expression)"
            r"|powershell(?:\.exe)?\s+[^\n]{0,80}-e(?:nc|ncodedcommand)?\s+[A-Za-z0-9+/=]{20,}",
            re.IGNORECASE,
        ),
        "скачивание и немедленное исполнение кода из сети",
    ),
    (
        "code.dynamic_eval", "CRITICAL",
        re.compile(
            r"\beval\s*\(\s*(?:atob|Buffer\.from|base64|require\s*\(\s*['\"]child_process)"
            r"|\bexec\s*\(\s*(?:base64\.b64decode|__import__)"
            r"|\bnew\s+Function\s*\(\s*atob"
            # исполнение декодированного base64: b64decode внутри eval/exec/compile/system/Popen.
            # Голый base64.b64decode(...) (запись картинки в файл) НЕ флагуем — это FP.
            r"|(?:eval|exec|compile|os\.system|subprocess\.(?:run|Popen|call)|check_output)\s*\("
            r"[^)\n]{0,40}base64\.b64decode"
            r"|\b(?:eval|exec)\s*\(\s*(?:requests|urllib|fetch)",
            re.IGNORECASE,
        ),
        "исполнение динамически декодированного кода",
    ),
    (
        "code.detached_spawn", "WARN",
        re.compile(
            r"detached\s*:\s*true|\.unref\s*\(\s*\)|nohup\s|Start-Process[^\n]{0,80}-WindowStyle\s+Hidden"
            r"|subprocess\.(?:Popen|run)\([^\n]{0,120}(?:DETACHED_PROCESS|start_new_session\s*=\s*True)",
            re.IGNORECASE,
        ),
        "запуск фонового процесса, отвязанного от сессии",
    ),
    (
        "code.destructive", "WARN",
        re.compile(
            r"\brm\s+-[rRf]{1,2}[a-z]*\s+(?:~|/|\$HOME|\"?\$\{?HOME)"
            r"|Remove-Item[^\n]{0,60}-Recurse[^\n]{0,60}-Force[^\n]{0,40}(?:\$HOME|~|C:\\\\?Users)"
            r"|\bgit\s+push\s+--force\b|\bDROP\s+(?:DATABASE|TABLE)\b",
            re.IGNORECASE,
        ),
        "деструктивная команда по домашнему каталогу / БД",
    ),
    (
        "code.claude_config_write", "CRITICAL",
        re.compile(
            r"(?:open|write_text|writeFileSync|appendFileSync|Set-Content|Add-Content|>>?)\s*\(?[^\n]{0,80}"
            r"[\\/]\.claude[\\/](?:settings(?:\.local)?\.json|CLAUDE\.md|rules[\\/]|hooks[\\/])",
            re.IGNORECASE,
        ),
        "запись в мой конфиг Claude Code (settings/CLAUDE.md/rules/hooks)",
    ),
)

_CRED_READ = re.compile(
    r"\.credentials\.master\.env|\.ssh[/\\]id_|\.aws[/\\]credentials"
    r"|\.claude[/\\]settings(?:\.local)?\.json|chats\.db|Login\s+Data|cookies\.sqlite",
    re.IGNORECASE,
)

# --------------------------------------------------------------------------- #
# Структурные (JSON) правила
# --------------------------------------------------------------------------- #

_HOOK_DANGER = re.compile(
    r"(?:curl|wget)[^\n|]{0,160}\|\s*(?:ba)?sh|-e(?:nc|ncodedcommand)\s+[A-Za-z0-9+/=]{20,}"
    r"|\beval\b|base64\s+-d|--dangerously-skip-permissions|\brm\s+-rf\b"
    r"|(?:python|node)\s+-c\s|Invoke-Expression|\biex\b",
    re.IGNORECASE,
)
_LIFECYCLE_KEYS = ("preinstall", "install", "postinstall", "prepare", "prepublish", "prepublishOnly")
_LIFECYCLE_DANGER = re.compile(
    r"child_process|spawn|execSync|exec\(|fork\(|\beval\b|atob|Buffer\.from\([^)]*base64"
    r"|base64\s+-d|curl|wget|iwr|powershell|-e(?:nc)?\s+[A-Za-z0-9+/=]{20,}"
    r"|detached|unref|nohup|chmod\s+\+x|\bnc\s+-",
    re.IGNORECASE,
)
_MCP_INLINE_CODE = re.compile(r"^-(?:c|e|-eval|-command)$|^-[A-Za-z]*[ce]$")
_MCP_SHELLS = {"bash", "sh", "zsh", "cmd", "cmd.exe", "powershell", "powershell.exe", "pwsh", "node", "python", "python3", "deno", "ruby", "perl"}


# --------------------------------------------------------------------------- #
# Модель находки
# --------------------------------------------------------------------------- #

class ScanError(RuntimeError):
    """Скан не может быть завершён достоверно."""


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    rule_id: str
    message: str
    excerpt: str = ""

    def sort_key(self) -> tuple:
        return (SEV_RANK.get(self.severity, 9), self.path.lower(), self.line, self.rule_id)


@dataclass
class ScanStats:
    files_scanned: int = 0
    files_skipped: int = 0
    bytes_scanned: int = 0
    vendor_dirs_skipped: list[str] = field(default_factory=list)


def _safe(value: str, limit: int = 160) -> str:
    """Экранирует управляющие/невидимые символы перед печатью недоверенной строки."""
    out = []
    for ch in value[:limit]:
        cp = ord(ch)
        if cp < 0x20 or cp == 0x7F or _is_invisible(cp):
            out.append(f"\\u{cp:04X}")
        else:
            out.append(ch)
    tail = "…" if len(value) > limit else ""
    return "".join(out) + tail


# --------------------------------------------------------------------------- #
# Обход дерева
# --------------------------------------------------------------------------- #

def _classify_target(root: Path) -> str:
    if root.is_file():
        return "файл"
    if (root / "plugin.json").is_file() or (root / ".claude-plugin").is_dir():
        return "плагин"
    if (root / "SKILL.md").is_file():
        return "скилл"
    md = list(root.glob("*.md"))
    if md and not any(p.is_dir() for p in root.iterdir() if p.name not in SKIP_DIRS):
        return "каталог агентов/команд"
    if any((root / sub).is_dir() for sub in ("skills", "agents", "commands", "hooks")):
        return "плагин/сборник"
    return "каталог"


def _collect(root: Path, include_vendor: bool, stats: ScanStats) -> tuple[list[Path], list[Finding]]:
    """Собирает файлы; симлинки не разыменовывает, а помечает как находку."""
    findings: list[Finding] = []
    files: list[Path] = []

    if root.is_file():
        return [root], findings

    for dirpath, dirnames, filenames in os.walk(root):
        here = Path(dirpath)
        kept = []
        for d in dirnames:
            sub = here / d
            if d in SKIP_DIRS:
                continue
            if sub.is_symlink():
                findings.append(Finding(
                    _rel(sub, root), 0, "CRITICAL", "fs.symlink",
                    "каталог — символическая ссылка, содержимое не проверено (может указывать наружу)",
                ))
                continue
            if d in VENDOR_DIRS and not include_vendor:
                stats.vendor_dirs_skipped.append(_rel(sub, root))
                continue
            kept.append(d)
        dirnames[:] = kept

        for name in filenames:
            p = here / name
            if p.is_symlink():
                findings.append(Finding(
                    _rel(p, root), 0, "CRITICAL", "fs.symlink",
                    "файл — символическая ссылка, содержимое не проверено",
                ))
                continue
            ext = p.suffix.lower()
            if ext in BINARY_ARTIFACT_EXT:
                findings.append(Finding(
                    _rel(p, root), 0, "WARN", "fs.binary_artifact",
                    f"в пакете лежит исполняемый бинарник ({ext}) — исходников нет, проверить нечем",
                ))
                continue
            if ext in TEXT_EXT or name.lower() in {"dockerfile", "makefile", ".mcp.json"} or not ext:
                files.append(p)
            else:
                stats.files_skipped += 1

    files.sort(key=lambda p: _rel(p, root).lower())
    if len(files) > MAX_FILES:
        raise ScanError(f"в цели {len(files):,} текстовых файлов, лимит {MAX_FILES:,}")
    return files, findings


def _rel(p: Path, root: Path) -> str:
    try:
        if root.is_file():
            return p.name
        return p.relative_to(root).as_posix()
    except ValueError:
        return p.as_posix()


def _read(p: Path, stats: ScanStats) -> str | None:
    size = p.stat().st_size
    if size > MAX_FILE_BYTES:
        stats.files_skipped += 1
        return None
    stats.bytes_scanned += size
    if stats.bytes_scanned > MAX_TOTAL_BYTES:
        raise ScanError(f"суммарный объём превысил лимит {MAX_TOTAL_BYTES:,} байт")
    raw = p.read_bytes()
    for enc in ("utf-8-sig", "cp1251"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return None


# --------------------------------------------------------------------------- #
# Проверки текста
# --------------------------------------------------------------------------- #

def _frontmatter_range(lines: Sequence[str]) -> tuple[int, int]:
    if not lines or lines[0].strip() not in {"---", "\ufeff---"}:
        return (0, 0)
    for i, line in enumerate(lines[1:], start=2):
        if line.strip() == "---":
            return (2, i - 1)
    return (0, 0)


def _scan_text(rel: str, text: str, is_markdown: bool, is_code: bool) -> list[Finding]:
    out: list[Finding] = []
    lines = text.splitlines()
    fm_start, fm_end = _frontmatter_range(lines) if is_markdown else (0, 0)

    for n, line in enumerate(lines, start=1):
        invis_set = set()
        for idx, c in enumerate(line):
            cp = ord(c)
            if not _is_invisible(cp):
                continue
            if cp == 0x200D:  # ZWJ между двумя эмодзи — легитимный джойнер (👨‍💻), не инъекция
                prev = ord(line[idx - 1]) if idx > 0 else 0
                nxt = ord(line[idx + 1]) if idx + 1 < len(line) else 0
                if _is_emoji(prev) or _is_emoji(nxt):
                    continue
            invis_set.add(cp)
        invisible = sorted(invis_set)
        if invisible:
            cps = ", ".join(f"U+{v:04X}" for v in invisible)
            out.append(Finding(rel, n, "CRITICAL", "unicode.invisible",
                               f"невидимые символы Unicode ({cps}) — текст на экране не равен тексту для модели",
                               _safe(line.strip())))

        for rule_id, sev, pattern, msg in _TEXT_RULES:
            if pattern.search(line):
                out.append(Finding(rel, n, sev, rule_id, msg, _safe(line.strip())))

        if is_code:
            for rule_id, sev, pattern, msg in _CODE_RULES:
                if pattern.search(line):
                    out.append(Finding(rel, n, sev, rule_id, msg, _safe(line.strip())))

        if _BAD_SINK.search(line):
            out.append(Finding(rel, n, "CRITICAL", "net.suspicious_sink",
                               "обращение к типичному приёмнику утечки (webhook/paste/туннель)",
                               _safe(line.strip())))

        if _OUTBOUND.search(line) and _SECRET_REF.search(line):
            # Только ЛИТЕРАЛЬНЫЙ посторонний хост = сигнал. URL-переменная ($API_URL) —
            # почти всегда легитимный вызов собственного API скилла, это шумит на реальных
            # скиллах; такой случай ловит cross-line credential_exfil_chain по факту чтения кред.
            foreign = [h for h in _URL.findall(line) if not _VENDOR_HOSTS.search(h)]
            if foreign:
                out.append(Finding(rel, n, "CRITICAL", "tool.exfiltration_shape",
                                   f"секрет уходит по сети на посторонний адрес ({_safe(foreign[0], 60)})",
                                   _safe(line.strip())))

        if _B64_BLOB.search(line) and "data:image" not in line and "data:font" not in line:
            out.append(Finding(rel, n, "WARN", "content.base64_blob",
                               "длинный base64-блок — возможен спрятанный payload"))

        if fm_start and fm_start <= n <= fm_end:
            out.extend(_scan_frontmatter_line(rel, n, line))

    if is_markdown:
        out.extend(_scan_hidden_markdown(rel, text, lines))

    # цепочка «прочитал секрет → отправил наружу» в пределах одного файла
    if is_code and _CRED_READ.search(text) and (_OUTBOUND.search(text) or _BAD_SINK.search(text)):
        already = any(f.rule_id in {"tool.exfiltration_shape", "net.suspicious_sink"} for f in out)
        if not already:
            hosts = _URL.findall(text)
            foreign = [h for h in hosts if not _VENDOR_HOSTS.search(h)]
            if foreign or not hosts:
                cred_line = next((i for i, l in enumerate(lines, 1) if _CRED_READ.search(l)), 0)
                out.append(Finding(rel, cred_line, "CRITICAL", "code.credential_exfil_chain",
                                   "в одном файле есть и чтение чужих учётных данных, и отправка по сети"))
    return out


def _scan_frontmatter_line(rel: str, n: int, line: str) -> list[Finding]:
    out: list[Finding] = []
    if re.match(r"^\s*allowed-tools\s*:", line, re.IGNORECASE):
        # CRITICAL только на НЕОГРАНИЧЕННЫЙ грант: Bash(*)/Bash без скоупа/одиночный `*`/bypass.
        # Скоуп (Bash(python:*)) и Read/Write/Edit — норма для многих скиллов → WARN, не блок.
        broad = re.search(
            r"\bBash\s*\(\s*\*?\s*\)"          # Bash() / Bash(*)
            r"|\bBash\b(?!\s*\()"               # bare Bash без скобок скоупа
            r"|(?:^|[\s,'\"\[])\*(?:[\s,'\"\]]|$)"  # одиночный wildcard-токен
            r"|bypass|dangerous",
            line, re.IGNORECASE)
        sev = "CRITICAL" if broad else "WARN"
        msg = ("фронтматтер выдаёт НЕОГРАНИЧЕННЫЙ доступ к инструментам (Bash без скоупа / *)"
               if broad else "фронтматтер объявляет полномочия инструментов — сверь, что ожидаемо")
        out.append(Finding(rel, n, sev, "frontmatter.allowed_tools", msg, _safe(line.strip())))
    if re.match(r"^\s*disable-model-invocation\s*:\s*[\"']?(?:false|no|0)[\"']?\s*(?:#.*)?$", line, re.IGNORECASE):
        out.append(Finding(rel, n, "WARN", "frontmatter.model_invocation_enabled",
                           "фронтматтер явно разрешает автовызов модели", _safe(line.strip())))
    if re.match(r"^\s*(?:permissions?|permission-mode|defaultMode)\s*:", line, re.IGNORECASE) and \
            re.search(r"bypass|accept[- ]?edits|dangerous", line, re.IGNORECASE):
        out.append(Finding(rel, n, "CRITICAL", "frontmatter.permission_mode",
                           "фронтматтер понижает режим разрешений", _safe(line.strip())))
    return out


def _scan_hidden_markdown(rel: str, text: str, lines: Sequence[str]) -> list[Finding]:
    out: list[Finding] = []
    for m in _HTML_COMMENT.finditer(text):
        body = m.group(1)
        if _HIDDEN_DIRECTIVE.search(body):
            n = text.count("\n", 0, m.start()) + 1
            out.append(Finding(rel, n, "CRITICAL", "md.hidden_directive",
                               "инструкция спрятана в HTML-комментарии (не видна при чтении, видна модели)",
                               _safe(body.strip())))
    for n, line in enumerate(lines, start=1):
        if _HIDDEN_STYLE.search(line) and _HIDDEN_DIRECTIVE.search(line):
            out.append(Finding(rel, n, "CRITICAL", "md.hidden_style",
                               "текст с инструкцией скрыт стилями (display:none / белый шрифт)",
                               _safe(line.strip())))
    return out


# --------------------------------------------------------------------------- #
# Структурные проверки JSON
# --------------------------------------------------------------------------- #

def _line_of(text: str, needle: str) -> int:
    idx = text.find(needle)
    return text.count("\n", 0, idx) + 1 if idx >= 0 else 0


def _flatten_cmd(entry: object) -> str:
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        parts = [str(entry.get("command", ""))]
        args = entry.get("args")
        if isinstance(args, list):
            parts.extend(str(a) for a in args)
        return " ".join(p for p in parts if p)
    return str(entry)


def _scan_hooks(rel: str, raw: str, hooks_obj: object, out: list[Finding]) -> None:
    if not isinstance(hooks_obj, dict):
        return
    for event, entries in hooks_obj.items():
        if not isinstance(entries, list):
            continue
        for group in entries:
            matcher = group.get("matcher", "*") if isinstance(group, dict) else "*"
            inner = group.get("hooks", [group]) if isinstance(group, dict) else [group]
            if not isinstance(inner, list):
                inner = [inner]
            for h in inner:
                cmd = _flatten_cmd(h)
                if not cmd:
                    continue
                n = _line_of(raw, cmd[:60]) or _line_of(raw, str(event))
                broad = str(matcher) in {"*", "", ".*"} or "|" in str(matcher)
                sev = "CRITICAL" if _HOOK_DANGER.search(cmd) else "WARN"
                rule = "hooks.dangerous_command" if sev == "CRITICAL" else "hooks.registered"
                note = "выполнится автоматически" + (
                    f" на КАЖДОМ событии {event} (matcher {matcher})" if broad else f" на {event}")
                out.append(Finding(rel, n, sev, rule,
                                   f"регистрируется хук: {note} → {_safe(cmd, 120)}"))


def _scan_mcp(rel: str, raw: str, servers: object, out: list[Finding]) -> None:
    if not isinstance(servers, dict):
        return
    for name, cfg in servers.items():
        if not isinstance(cfg, dict):
            continue
        n = _line_of(raw, f'"{name}"')
        if cfg.get("url") or str(cfg.get("type", "")).lower() in {"http", "sse", "websocket"}:
            host = _URL.search(str(cfg.get("url", "")))
            out.append(Finding(rel, n, "WARN", "mcp.remote_server",
                               f"MCP-сервер «{_safe(str(name), 40)}» удалённый "
                               f"({_safe(host.group(1) if host else str(cfg.get('url')), 60)}) — "
                               f"содержимое сессии уходит на чужой хост"))
            continue
        cmd = str(cfg.get("command", ""))
        args = [str(a) for a in cfg.get("args", []) if isinstance(cfg.get("args"), list)]
        full = " ".join([cmd] + args)
        base = Path(cmd).name.lower()
        inline = any(_MCP_INLINE_CODE.match(a) for a in args)
        remote_pkg = any(re.search(r"https?://|git\+|\.tgz|github:", a, re.IGNORECASE) for a in args)
        if inline or (base in _MCP_SHELLS and inline) or remote_pkg or _HOOK_DANGER.search(full):
            out.append(Finding(rel, n, "CRITICAL", "mcp.arbitrary_command",
                               f"MCP-сервер «{_safe(str(name), 40)}» запускает произвольный код: "
                               f"{_safe(full, 120)}"))
        else:
            out.append(Finding(rel, n, "WARN", "mcp.server_declared",
                               f"объявлен MCP-сервер «{_safe(str(name), 40)}» → {_safe(full, 100)} "
                               f"(процесс с моими правами, без песочницы)"))


def _scan_package_json(rel: str, raw: str, data: dict, base_dir: Path, out: list[Finding]) -> None:
    scripts = data.get("scripts")
    if not isinstance(scripts, dict):
        return
    for key in _LIFECYCLE_KEYS:
        if key not in scripts:
            continue
        value = str(scripts[key])
        n = _line_of(raw, f'"{key}"')
        danger = bool(_LIFECYCLE_DANGER.search(value))
        # значение может указывать на локальный скрипт — вскрываем его
        hidden_reason = ""
        for m in re.finditer(r"[\w./\\-]+\.(?:js|cjs|mjs|ts|py|sh|ps1)", value):
            cand = (base_dir / m.group(0)).resolve()
            try:
                if cand.is_file() and not cand.is_symlink() and cand.stat().st_size < MAX_FILE_BYTES:
                    body = cand.read_bytes().decode("utf-8", errors="replace")
                    if _LIFECYCLE_DANGER.search(body) or _CODE_RULES[2][2].search(body):
                        danger = True
                        hidden_reason = f"; вызываемый {m.group(0)} порождает процесс/сеть"
            except OSError:
                pass
        if danger:
            out.append(Finding(rel, n, "CRITICAL", "npm.obfuscated_lifecycle",
                               f"{key} исполняет код при установке (spawn/сеть/base64){hidden_reason}: "
                               f"{_safe(value, 120)}"))
        else:
            out.append(Finding(rel, n, "WARN", "npm.lifecycle_script",
                               f"{key} выполнится при npm install: {_safe(value, 120)}"))


def _scan_json_file(rel: str, path: Path, raw: str, root: Path) -> list[Finding]:
    out: list[Finding] = []
    name = path.name.lower()
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        return out
    if not isinstance(data, dict):
        return out

    if name == "package.json":
        _scan_package_json(rel, raw, data, path.parent, out)

    if name in {"hooks.json", "plugin.json", "settings.json", "settings.local.json"} or "hooks" in data:
        _scan_hooks(rel, raw, data.get("hooks"), out)

    if name in {".mcp.json", "mcp.json"}:
        servers = data.get("mcpServers") if isinstance(data.get("mcpServers"), dict) else data
        _scan_mcp(rel, raw, servers, out)
    elif isinstance(data.get("mcpServers"), dict):
        _scan_mcp(rel, raw, data["mcpServers"], out)

    perms = data.get("permissions")
    if isinstance(perms, dict):
        n = _line_of(raw, '"permissions"')
        mode = str(perms.get("defaultMode", ""))
        if re.search(r"bypass|dangerous", mode, re.IGNORECASE):
            out.append(Finding(rel, n, "CRITICAL", "config.permission_widening",
                               f"конфиг ставит режим разрешений «{_safe(mode, 40)}»"))
        allow = perms.get("allow")
        if isinstance(allow, list):
            for item in allow:
                s = str(item)
                if re.search(r"Bash\s*\(\s*\*?\s*\)|^Bash$|\*\s*\)|rm\s|--force|curl", s, re.IGNORECASE):
                    out.append(Finding(rel, _line_of(raw, s) or n, "CRITICAL", "config.permission_widening",
                                       f"в allow добавляется широкое/опасное правило: {_safe(s, 80)}"))
    return out


# --------------------------------------------------------------------------- #
# Оркестрация
# --------------------------------------------------------------------------- #

def scan(target: Path, include_vendor: bool = False) -> tuple[list[Finding], ScanStats, str]:
    root = target.expanduser()
    if root.is_symlink():
        raise ScanError("цель — символическая ссылка; проверять чужой код по ссылке нельзя")
    if not root.exists():
        raise ScanError(f"цель не найдена: {_safe(str(root), 200)}")
    root = root.resolve()

    kind = _classify_target(root)
    stats = ScanStats()
    files, findings = _collect(root, include_vendor, stats)

    for p in files:
        rel = _rel(p, root)
        try:
            text = _read(p, stats)
        except OSError:
            stats.files_skipped += 1
            continue
        if text is None:
            stats.files_skipped += 1
            continue
        stats.files_scanned += 1
        ext = p.suffix.lower()
        findings.extend(_scan_text(rel, text, is_markdown=ext in {".md", ".markdown"},
                                   is_code=ext in CODE_EXT))
        if ext == ".json" or p.name.lower() in {".mcp.json"}:
            findings.extend(_scan_json_file(rel, p, text, root))

    findings.sort(key=lambda f: f.sort_key())
    return findings, stats, kind


ALL_RULES = [
    "unicode.invisible", "prompt.ignore_previous", "prompt.disregard_system",
    "prompt.role_reassignment", "prompt.fake_system_prefix", "prompt.system_tag",
    "prompt.chat_template_tag", "prompt.tool_call_tag", "prompt.covert_directive",
    "prompt.autonomy_grab", "prompt.memory_write", "md.hidden_directive", "md.hidden_style",
    "frontmatter.allowed_tools", "frontmatter.model_invocation_enabled", "frontmatter.permission_mode",
    "tool.exfiltration_shape", "net.suspicious_sink", "content.base64_blob",
    "code.remote_exec", "code.dynamic_eval", "code.detached_spawn", "code.destructive",
    "code.claude_config_write", "code.credential_exfil_chain",
    "hooks.registered", "hooks.dangerous_command",
    "mcp.server_declared", "mcp.arbitrary_command", "mcp.remote_server",
    "npm.lifecycle_script", "npm.obfuscated_lifecycle",
    "config.permission_widening", "fs.symlink", "fs.binary_artifact",
]


def main(argv: Sequence[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")

    ap = argparse.ArgumentParser(
        description="Входящий скан чужого скилла/плагина/агента: prompt-injection и захват полномочий.")
    ap.add_argument("target", nargs="?", help="каталог скилла/плагина/агентов или один .md")
    ap.add_argument("--allow", action="append", default=[], metavar="RULE_ID",
                    help="заглушить правило (повторяемо), напр. --allow hooks.registered")
    ap.add_argument("--min-severity", choices=SEVERITIES, default="INFO",
                    help="печатать находки не ниже уровня (по умолчанию INFO)")
    ap.add_argument("--include-vendor", action="store_true",
                    help="сканировать также node_modules/dist (по умолчанию пропускаются)")
    ap.add_argument("--json", dest="as_json", action="store_true", help="машинный вывод")
    ap.add_argument("--list-rules", action="store_true", help="показать список правил и выйти")
    args = ap.parse_args(argv)

    if args.list_rules:
        for r in ALL_RULES:
            print(r)
        return 0
    if not args.target:
        ap.error("нужен путь к цели (или --list-rules)")

    try:
        findings, stats, kind = scan(Path(args.target), include_vendor=args.include_vendor)
    except ScanError as exc:
        msg = f"ОШИБКА скан не завершён: {exc}"
        print(json.dumps({"error": str(exc)}, ensure_ascii=False) if args.as_json else msg,
              file=sys.stderr)
        return 2

    allowed = set(args.allow)
    findings = [f for f in findings if f.rule_id not in allowed]
    floor = SEV_RANK[args.min_severity]
    shown = [f for f in findings if SEV_RANK[f.severity] <= floor]

    counts = {s: sum(1 for f in shown if f.severity == s) for s in SEVERITIES}
    blocking = counts["CRITICAL"] + counts["WARN"]

    if args.as_json:
        print(json.dumps({
            "target": str(Path(args.target).expanduser()),
            "kind": kind,
            "files_scanned": stats.files_scanned,
            "files_skipped": stats.files_skipped,
            "vendor_dirs_skipped": stats.vendor_dirs_skipped,
            "counts": counts,
            "findings": [f.__dict__ for f in shown],
            "exit": 1 if blocking else 0,
        }, ensure_ascii=False, indent=2))
        return 1 if blocking else 0

    print(f"Входящий скан ({kind}): {Path(args.target).expanduser()}")
    print(f"Файлов проверено: {stats.files_scanned}, пропущено: {stats.files_skipped}")
    for d in stats.vendor_dirs_skipped:
        print(f"  ! пропущен вендорный каталог (не проверен): {d} — при сомнениях --include-vendor")
    if stats.files_scanned and stats.files_skipped:
        # Частичный пропуск тоже стоит проговорить: вердикт ниже относится
        # только к прочитанному, а не ко всему пакету.
        print(f"  ! {stats.files_skipped} файл(ов) не прочитано — вердикт ниже только"
              " про проверенные; нечитаемое смотри глазами")

    if not shown:
        if stats.files_scanned == 0:
            # Ноль проверенных файлов — это не чистый пакет, это непроверенный.
            # Раньше здесь печаталось «ЧИСТО», и .skill-архивы (обычные zip)
            # проходили гейт, не будучи прочитанными ни разу.
            print("НЕ ПРОВЕРЕНО: ни один файл не прочитан — выносить вердикт не на чем.")
            print(f"  пропущено файлов: {stats.files_skipped}")
            print("  причины бывают такие: расширение вне списка текстовых, файл больше"
                  f" {MAX_FILE_BYTES:,} байт, или это не текст вообще.")
            print("  если у цели расширение вроде .skill/.plugin — проверь, не архив ли это:")
            print("    python -c \"import zipfile,sys; print(zipfile.is_zipfile(sys.argv[1]))\" <файл>")
            print("  распакуй и просканируй распакованное.")
            return 1
        print("ЧИСТО: известных признаков инъекции и захвата полномочий не найдено.")
        print("Это не гарантия: правила ловят форму, а не смысл. Прочитай SKILL.md и скрипты глазами.")
        return 0

    print(f"\nНайдено {len(shown)}: CRITICAL {counts['CRITICAL']}, "
          f"WARN {counts['WARN']}, INFO {counts['INFO']}\n")
    for f in shown:
        loc = f"{f.path}:{f.line}" if f.line else f.path
        print(f"  {f.severity:<8} {loc} [{f.rule_id}]")
        print(f"           {f.message}")
        if f.excerpt:
            print(f"           > {f.excerpt}")
    print("\nНичего не изменено на диске. Разбирай находки руками:")
    print("  CRITICAL — не устанавливать, пока не понятно, зачем это в пакете;")
    print("  WARN     — легитимно бывает (хук, MCP, allowed-tools), но должно быть заявлено в README;")
    print("  правила широкие — текст про безопасность/LLM может совпасть, смотри контекст строки.")
    return 1 if blocking else 0


if __name__ == "__main__":
    sys.exit(main())
