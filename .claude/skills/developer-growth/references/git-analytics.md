# Git-аналитика — скрипты для Workflow B

Python-скрипты для анализа вклада разработчика. Запускай из корня репо или передавай `repo_path`. Интерпретация результатов — в SKILL.md (Workflow B, шаг 3): выводы про паттерны и рост, не про объём строк.

## 1. Паттерны коммитов (типы, время, помесячно)

```python
import subprocess
from collections import defaultdict
from datetime import datetime

def analyze_git_contributions(repo_path: str, author: str | None = None,
                              since: str | None = None) -> dict:
    """Analyze git contribution patterns.

    author: substring for git --author (name or email)
    since:  e.g. '3 months ago' or '2026-01-01'
    """
    cmd = ["git", "log", "--pretty=format:%H|%an|%ae|%ad|%s", "--date=short"]
    if author:
        cmd.append(f"--author={author}")
    if since:
        cmd.append(f"--since={since}")

    result = subprocess.run(cmd, capture_output=True, text=True, cwd=repo_path)

    commits = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        parts = line.split("|", 4)
        if len(parts) < 5:
            continue
        commits.append({
            "hash": parts[0], "author": parts[1], "email": parts[2],
            "date": parts[3], "message": parts[4],
        })

    by_weekday = defaultdict(int)
    by_month = defaultdict(int)
    by_type = defaultdict(int)

    for commit in commits:
        date = datetime.strptime(commit["date"], "%Y-%m-%d")
        by_weekday[date.strftime("%A")] += 1
        by_month[date.strftime("%Y-%m")] += 1

        msg = commit["message"].lower()
        for prefix, bucket in (("feat", "features"), ("fix", "fixes"),
                               ("refactor", "refactors"), ("test", "tests"),
                               ("docs", "docs")):
            if msg.startswith(prefix):
                by_type[bucket] += 1
                break
        else:
            by_type["other"] += 1

    return {
        "total_commits": len(commits),
        "by_weekday": dict(by_weekday),
        "by_month": dict(by_month),
        "by_type": dict(by_type),
        "commits": commits[:50],  # последние 50 для выборочного просмотра
    }
```

Что смотреть в результате:
- `by_type`: fix > 50% при tests ~ 0% → «пожарный режим», нет профилактики.
- `by_month`: провалы/пики — сверить с контекстом (релизы, отпуск), не делать выводов вслепую.
- `by_weekday`: систематические выходные-коммиты → вопрос про нагрузку/выгорание (аккуратно, это сигнал, не диагноз).
- Каталоги коммитов (`git log --name-only`) — узкая зона владения, если всё в одном модуле.

## 2. Тренд сложности кода (Python-репо, radon)

Требует `pip install radon`. Для не-Python стеков — аналоги: `eslint --max-complexity` / `gocyclo` / `lizard` (мультиязычный).

```python
import subprocess
import json

def analyze_complexity(repo_path: str) -> dict:
    """Snapshot of cyclomatic complexity distribution (radon ranks A-F)."""
    result = subprocess.run(
        ["radon", "cc", ".", "-a", "-j"],
        capture_output=True, text=True, cwd=repo_path,
    )
    complexity = json.loads(result.stdout)

    summary = {r: 0 for r in "ABCDEF"}  # A = low ... F = extreme
    for file_data in complexity.values():
        if not isinstance(file_data, list):
            continue  # radon puts error dicts for unparsable files
        for func in file_data:
            summary[func.get("rank", "A")] += 1
    return summary
```

Тренд: прогони на 2-3 исторических точках (`git stash` не нужен — `git worktree add /tmp/snap <sha>` и прогнать там). Рост доли C-F при активных коммитах автора в эти файлы → сигнал «фичи без рефакторинга».

## 3. Паттерны код-ревью (если есть PR-данные)

PR-данные бери из `gh api` (GitHub) или экспорта своей платформы. Формат входа: список PR-объектов с `reviews_given`, `reviews_received`, `comments[{body}]`.

```python
from collections import defaultdict

def analyze_code_reviews(pr_data: list) -> dict:
    """Analyze code review patterns from PR export."""
    stats = {
        "reviews_given": 0,
        "reviews_received": 0,
        "comments_total": 0,
        "common_feedback": [],
    }
    feedback_categories = defaultdict(int)

    for pr in pr_data:
        stats["reviews_given"] += len(pr.get("reviews_given", []))
        stats["reviews_received"] += len(pr.get("reviews_received", []))
        for comment in pr.get("comments", []):
            stats["comments_total"] += 1
            text = comment.get("body", "").lower()
            if "style" in text or "format" in text:
                feedback_categories["style"] += 1
            elif "test" in text:
                feedback_categories["testing"] += 1
            elif "performance" in text:
                feedback_categories["performance"] += 1
            elif "security" in text:
                feedback_categories["security"] += 1
            else:
                feedback_categories["logic"] += 1

    stats["common_feedback"] = sorted(
        feedback_categories.items(), key=lambda x: x[1], reverse=True
    )[:5]
    return stats
```

Интерпретация:
- reviews_given ≈ 0 при mid+ → зона роста «влияние на команду» (типичный gap до senior).
- В received-фидбеке доминирует одна категория (например, testing) → системный пробел, кандидат в PDP-цель.
- В given-фидбеке только style → ревью поверхностные, растить глубину (логика, дизайн, edge cases).

## Быстрые one-liner'ы (без Python)

```bash
# Типы коммитов автора за период
git log --author="user@example.com" --since="3 months ago" --pretty=%s \
  | grep -oE '^(feat|fix|refactor|test|docs|chore)' | sort | uniq -c | sort -rn

# Зона владения: в какие каталоги коммитит
git log --author="user@example.com" --since="3 months ago" --name-only --pretty=format: \
  | grep -v '^$' | cut -d/ -f1-2 | sort | uniq -c | sort -rn | head -15

# Кто ещё трогает те же файлы (bus factor / сотрудничество)
git shortlog -sn --since="3 months ago" -- path/to/module
```

## Ограничения и этика

- LOC и число коммитов ≠ продуктивность. Никогда не ранжируй людей по этим цифрам.
- Анализ чужого вклада — только с ведома человека (менторинг/self-review), не для скрытого надзора.
- Один репозиторий — неполная картина: учитывай ревью, дизайн-доки, менторинг вне git.
