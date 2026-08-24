#!/usr/bin/env python3
"""
Prompt Router — UserPromptSubmit hook script.
Reads prompt from stdin JSON, matches keywords from routing table,
outputs routing hint to stdout for Claude to see.
"""

import sys
import json
import re

# Routing table: keyword patterns → hint
ROUTES = [
    # Media
    (r"картинк|нарисуй|\bimage\b|изображени", "Skill `image-generation` (см. config/models.md для выбора модели)"),
    (r"видео с аватаром|аватар", "Skill `heygen`"),
    (r"озвуч|голос|\btts\b", "Skill `elevenlabs`"),
    (r"субтитр", "Skill `submagic`"),
    (r"транскриб|распознай речь", "Skill `deepgram`"),
    (r"переведи", "DeepL API"),

    # Code quality
    (r"проверь код|ревью|review", "Agent `code-reviewer`"),
    (r"найди баг|ошибк|bug", "Agent `bug-hunter` → `bug-fixer`"),
    (r"security|уязвимост|безопасност", "Agent `security-scanner`"),
    (r"напиши тест|write test", "Agent `test-writer`"),
    (r"dead code|unused|мёртвый код", "Agent `dead-code-hunter`"),
    (r"дублирован|duplicate", "Agent `reuse-hunter`"),
    (r"dependenc|outdated|зависимост", "Agent `dependency-auditor`"),

    # Dev
    (r"задеплой|deploy", "Command `deploy`"),
    (r"research|найди информаци", "Command `deep-research`"),
    (r"документ|gdoc", "Command `gdocs`"),
    (r"таблиц|gsheet", "Command `gsheets`"),
    (r"письмо|email|gmail", "Command `gmail`"),
    (r"бот|telegram", "Skill `telegram-bot-toolkit`"),
    (r"автоматизац|workflow|n8n", "Skill `n8n`"),
    (r"архитектур|дизайн систем", "Agent `software-architect`"),
    (r"\breact\b|\bui\b|компонент|фронтенд", "Agent `frontend-dev`"),
    (r"\bapi\b|endpoint|бэкенд", "Agent `backend-dev`"),
    (r"миграци|schema|\bsql\b", "Command `setup-db`"),
    (r"pipeline|docker|ci.?cd", "Agent `devops-engineer`"),
    (r"слайд|презентаци", "Agent `slide-designer`"),
    (r"проверь текст|корректур|proofread", "Command `proofread`"),
    (r"рефакторинг|legacy", "Agent `legacy-modernizer`"),
    (r"оптимизируй|медленно|performance", "Agent `performance-optimizer`"),

    # New skills (v8.0)
    (r"убери ии стиль|де-аифай|humanize text|ai.?жаргон", "Skill `de-ai-ify`"),
    (r"итоги недели|weekly.?synthesis", "Command `weekly-synthesis`"),
    (r"статистик.+сесси|prompt.?log", "Command `prompt-log`"),
    (r"диаграмм|flowchart|excalidraw", "Skill `excalidraw-flowchart`"),
    (r"мониторинг|uptime", "Свой Uptime Kuma + Skill `webhook-receiver` (навыка-обёртки в паке нет)"),
    (r"\bdns\b|домен", "Command `domain-dns-ops`"),
    (r"проанализируй себя|self.?reflect", "Skill `self-reflect`"),
    (r"фреймворк|think deeper|first principles", "Skill `thinking-frameworks`"),
]


def main():
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return

        data = json.loads(raw)
        prompt = data.get("prompt", "").lower()

        if not prompt:
            return

        matches = []
        for pattern, hint in ROUTES:
            if re.search(pattern, prompt, re.IGNORECASE):
                matches.append(hint)

        if matches:
            hints = "; ".join(matches[:3])  # max 3 hints
            print(f"ROUTING_HINT: {hints}")

    except (json.JSONDecodeError, KeyError, TypeError):
        pass  # silently ignore malformed input
    except Exception:
        pass  # never block user prompt


if __name__ == "__main__":
    main()
