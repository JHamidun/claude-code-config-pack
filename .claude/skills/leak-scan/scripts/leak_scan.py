"""
Pre-publish depersonalization / PII leak scanner.

Usage: python leak_scan.py <target_dir_or_file> [--allow SUBSTR ...]

Two layers of patterns:
- GENERIC_PATTERNS (in this file): key/token/secret SHAPES that are not tied to any
  person — API keys, bot tokens, JWT, SMTP keys, phone number formats, national ID cues.
- IDENTITY_PATTERNS (loaded from ~/.claude/leak-scan-identity.json, NOT shipped):
  the specific names, documents, domains, server IPs and client names of THIS owner.
  Without that file the scanner still catches generic secret shapes and warns that
  personal tells are not being checked. See scripts/identity.example.json for the shape.

Exit code: 0 if clean, 1 if matches found.
"""

from __future__ import annotations

import json
import re
import sys
import argparse
from pathlib import Path

_ap = argparse.ArgumentParser(description="Pre-publish PII / depersonalization scanner")
_ap.add_argument("target", nargs="?", default=".", help="directory or file to scan")
_ap.add_argument("--allow", action="append", default=[], help="extra allowlist substring (repeatable)")
_args = _ap.parse_args()
ROOT = Path(_args.target)

# Case-insensitive patterns we never want to see in the public archive.
# Общие формы секретов: ключи, токены, подписи. Они не привязаны к человеку —
# их можно и нужно возить вместе с инструментом.
GENERIC_PATTERNS: list[tuple[str, str]] = [
    ('api:sk-ant'              , 'sk-ant-api\\d+-[A-Za-z0-9_-]{40,}'),
    ('api:sk-proj'             , 'sk-proj-[A-Za-z0-9_-]{40,}'),
    ('api:google-AIza'         , 'AIza[0-9A-Za-z_-]{35}'),
    ('api:ghp_'                , '\\bghp_[A-Za-z0-9]{36}\\b'),
    ('api:xoxb'                , 'xoxb-[0-9]+-[0-9]+-[A-Za-z0-9]+'),
    ('api:ntn'                 , '\\bntn_[A-Za-z0-9]{40,}\\b'),
    ('api:pplx'                , '\\bpplx-[A-Za-z0-9]{40,}\\b'),
    ('api:figd'                , '\\bfigd_[A-Za-z0-9_-]{30,}\\b'),
    ('api:r8_'                 , '\\br8_[A-Za-z0-9]{30,}\\b'),
    ('api:lin_api'             , '\\blin_api_[A-Za-z0-9]{30,}\\b'),
    ('api:apify'               , '\\bapify_api_[A-Za-z0-9]{30,}\\b'),
    ('tg:bot-token'            , '\\b\\d{8,10}:AA[A-Za-z0-9_-]{33}\\b'),
    ('kuma:push-token'         , '/api/push/[A-Za-z0-9_-]{10,}'),
    ('jwt'                     , 'eyJ[A-Za-z0-9_-]+\\.eyJ[A-Za-z0-9_-]+\\.[A-Za-z0-9_-]+'),
    ('phone:ru'                , '\\+7\\s?\\(?\\d{3}\\)?[\\s-]?\\d{3}[\\s-]?\\d{2}[\\s-]?\\d{2}'),
    ('net:docker_bridge'       , '172\\.17\\.0\\.1'),
    ('brevo:smtp_key'          , 'xsmtpsib-[a-f0-9]{30,}'),
    ('fingerprint:cpf_lang'    , '\\bCPF\\b'),
    ('stego:zero_width'        , '[\u200b\u200c\u200d\ufeff]'),
]


def _load_identity() -> list[tuple[str, str]]:
    """Личный словарь опознавания — из файла рядом, а не из кода.

    Раньше двести с лишним личных признаков — имена, документы, адреса серверов,
    названия клиентов, ключи сервисов — лежали прямо в этом файле. Инструмент,
    который ищет утечки, сам был крупнейшей из них: опубликовать его означало
    опубликовать каталог всего частного разом.

    Теперь словарь живёт отдельно и не попадает в репозиторий. Без него сканер
    продолжает ловить общие формы секретов, но перестаёт узнавать конкретного
    человека — и честно об этом предупреждает, чтобы молчание не приняли за чистоту.
    """
    import os
    candidates = [
        os.environ.get("LEAK_SCAN_IDENTITY"),
        Path.home() / ".claude" / "leak-scan-identity.json",
        Path(__file__).resolve().parent.parent / "identity.local.json",
    ]
    for c in candidates:
        if not c:
            continue
        p = Path(c)
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"WARNING: словарь {p.name} не читается ({e}) — личные признаки не проверяются",
                  file=sys.stderr)
            return []
        return [(lbl, rx) for lbl, rx in data.get("patterns", [])]
    for _msg in (
        "WARNING: личного словаря нет — проверяются только общие формы секретов.",
        "         Имена, документы, адреса и названия клиентов НЕ ищутся.",
        "         Заведи ~/.claude/leak-scan-identity.json по образцу identity.example.json.",
    ):
        print(_msg, file=sys.stderr)
    return []


IDENTITY_PATTERNS = _load_identity()
LEAK_PATTERNS: list[tuple[str, str]] = GENERIC_PATTERNS + IDENTITY_PATTERNS

# Allowed false positives — strings that might match but are intentional
# (placeholders/templates, public software references, etc.)
ALLOWLIST_SUBSTRINGS = [
    "your-username",
    "your-domain",
    "your-server",
    "YOUR_BOT_TOKEN",
    "YOUR_TOKEN",
    "YOUR_KEY",
    "YOUR_API",
    "YOUR_TG",
    "YOUR_TELEGRAM",
    "YOUR_GITHUB",
    "YOUR_GOOGLE",
    "YOUR_SLACK",
    "YOUR_FIGMA",
    "YOUR_NOTION",
    "YOUR_LINEAR",
    "YOUR_HEYGEN",
    "YOUR_ELEVEN",
    "YOUR_PERPLEX",
    "YOUR_CLOUDFLARE",
    "YOUR_AWS",
    "YOUR_PINECONE",
    "YOUR_REPLICATE",
    "YOUR_SERPAPI",
    "YOUR_APIFY",
    "YOUR_GREPTILE",
    "YOUR_BRAVE",
    "YOUR_CAPMONSTER",
    "YOUR_JWT",
    "YOUR_OAUTH",
    "YOUR_GCP",
    "YOUR_TUNNEL",
    "YOUR_DEEPL",
    "YOUR_DEEPGRAM",
    "YOUR_DEEPSEEK",
    "YOUR_MANUS",
    "YOUR_KIMI",
    "YOUR_TLDV",
    "YOUR_ZOOM",
    "YOUR_PLAUD",
    "YOUR_TILDA",
    "YOUR_BREVO",
    "YOUR_ANTHROPIC_ORG",
    "YOUR_LINKEDIN",
    "YOUR_MAX_USER",
    "YOUR_AFFINE",
    "YOUR_GAMMA",
    "YOUR_SUBMAGIC",
    "YOUR_DID",
    "YOUR_SENTRY",
    "YOUR_AIRTABLE",
    "YOUR_MONGO",
    "YOUR_REDIS",
    "YOUR_DB_PASSWORD",
    "YOUR_PROXY",
    "YOUR_TILDA",
    "YOUR_N8N",
    "YOUR_UPTIME",
    "YOUR_EXCHANGE",
    "YOUR_GMAIL",
    "YOUR_YANDEX",
    "YOUR_2FA",
    "YOUR_SERVER_PASSWORD",
    "YOUR_PROJECT",
    "YOUR_USER",
    "YourFirstName",
    "YourLastName",
    "YourName",
    "YourUsername",
    "YourCompany",
    "YourCompanyGPT",
    "YourChannel",
    "YourProject",
    "YourBot",
    "[REDACTED",
    "+1234567890",
    "+55 XX XXXXX-XXXX",
    "${HOME}",
    "${WORKSPACE}",
    # Upstream public authors / projects credited in README
    "Garry Tan",
    "garrytan",      # gstack upstream
    "Y Combinator",
    "Jake Ward",     # public LinkedIn formula author
    "Lara Acosta",
    "Cam Trew",
    "Noam Nisand",
    # Public OSS authors credited in skills/docs (not our user)
    "Anthropic",
    "Typhren",
    "vanzan01",
    "zhsama",
    "steveyegge",
    "Steve Yegge",
    "mvanhorn",       # last30days-skill author (frontmatter)
    "wowyuarm",
    "michalparkola",
    "aerkalov",
    "Jesse Vincent",
    "Matt VanHorn",
]

TEXT_EXTENSIONS = {
    ".md", ".txt", ".json", ".jsonc", ".yaml", ".yml",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".mjs", ".cjs",
    ".sh", ".ps1", ".bat", ".env",
    ".html", ".htm", ".css",
    ".toml", ".cfg", ".ini", ".conf",
    ".sql",
}


def is_allowlisted(line: str) -> bool:
    return any(s in line for s in ALLOWLIST_SUBSTRINGS) or any(s in line for s in _args.allow)


def main() -> int:
    if not ROOT.exists():
        print(f"NOT FOUND: {ROOT}")
        return 2

    matches: dict[str, list[tuple[Path, int, str]]] = {}
    total_files = 0
    total_lines = 0

    _paths = [ROOT] if ROOT.is_file() else ROOT.rglob("*")
    for path in _paths:
        if not path.is_file():
            continue
        if ".git" in path.parts or "__pycache__" in path.parts or path.name.startswith("_"):
            continue  # __pycache__/*.pyc — байткод таскает абсолютные пути окружения (деанон-фингерпринт)
        if path.suffix.lower() not in TEXT_EXTENSIONS and path.suffix != "":
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        total_files += 1

        for lineno, line in enumerate(text.splitlines(), start=1):
            total_lines += 1
            stripped = line.strip()
            if not stripped:
                continue
            if is_allowlisted(line):
                continue
            for label, pattern in LEAK_PATTERNS:
                if re.search(pattern, line, re.IGNORECASE):
                    if is_allowlisted(line):
                        continue
                    matches.setdefault(label, []).append((path, lineno, stripped[:200]))

    # Report
    print(f"Scanned {total_files} text files, {total_lines} lines.")
    print()

    # Force UTF-8 stdout to avoid Windows cp1251 crash on Cyrillic
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    if not matches:
        print("CLEAN: no leak patterns matched.")
        return 0

    total = sum(len(v) for v in matches.values())
    print(f"FOUND {total} match(es) across {len(matches)} pattern type(s):\n")
    for label, hits in sorted(matches.items(), key=lambda x: -len(x[1])):
        print(f"\n=== [{label}] {len(hits)} hits ===")
        for path, lineno, text in hits[:25]:
            rel = path if ROOT.is_file() else path.relative_to(ROOT)
            safe = text[:150].encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            print(f"  {rel}:{lineno}  {safe}")
        if len(hits) > 25:
            print(f"  ... +{len(hits) - 25} more")

    return 1


if __name__ == "__main__":
    sys.exit(main())
