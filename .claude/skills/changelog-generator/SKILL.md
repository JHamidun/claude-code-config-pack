---
name: changelog-generator
description: "Changelog из git-коммитов: semver, Keep a Changelog, PR/issues через gh, git tag, GitHub Release. Триггеры: «сгенерируй changelog», «release notes»."
---

# Changelog Generator Skill

## Overview

Автоматическая генерация CHANGELOG из git коммитов. Семантическое версионирование, группировка по типам.

## When to Use

- Релиз новой версии
- Подготовка release notes
- Документирование изменений
- CI/CD pipeline для changelog

## Full Release Flow (5 шагов)

1. **Git Analysis** — коммиты с последнего тега, группировка по типам (Conventional Commits) — см. «Generation Algorithm» ниже.
2. **GitHub Integration** — обогати детали через `gh`: `gh pr list --state merged --search "merged:>YYYY-MM-DD"`, `gh issue list --state closed` — заголовки PR и закрытые issues часто описательнее коммитов.
3. **Format CHANGELOG.md** — по Keep a Changelog (шаблон ниже).
4. **Generate Release Notes** — `gh release create vX.Y.Z --notes-file release_notes.md` (или через CI, см. GitHub Actions ниже).
5. **Distribution** — закоммить CHANGELOG.md, создай git tag, уведоми команду.

## Changelog Format

### Keep a Changelog Standard

```markdown
# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [1.2.0] - 2024-01-15

### Added
- New user authentication system
- Dark mode support

### Changed
- Improved performance of search

### Deprecated
- Old API endpoints (will remove in 2.0)

### Removed
- Legacy database driver

### Fixed
- Memory leak in image processing
- Login redirect bug

### Security
- Updated dependencies with CVE fixes
```

## Semantic Versioning

```
MAJOR.MINOR.PATCH

MAJOR - Breaking changes (feat!:, BREAKING CHANGE)
MINOR - New features (feat:)
PATCH - Bug fixes (fix:)
```

## Commit Types → Changelog Sections

| Commit Type | Changelog Section |
|-------------|------------------|
| `feat:` | Added |
| `fix:` | Fixed |
| `perf:` | Changed (Performance) |
| `refactor:` | Changed |
| `docs:` | Documentation |
| `style:` | (skip) |
| `test:` | (skip) |
| `chore:` | (skip) |
| `ci:` | (skip) |
| `feat!:` / `BREAKING CHANGE` | Breaking Changes |
| `security:` / `deps(security)` | Security |
| `deprecate:` | Deprecated |
| `remove:` | Removed |

## Generation Algorithm

> **Готовый скрипт поставляется с навыком:** `~/.claude/skills/changelog-generator/scripts/changelog.py`
> (разбор `--version` / `--since` / `--repo` / `--hashes` / `--dry-run` уже встроен; работает и в репо без тегов).
> Код ниже — ядро алгоритма для понимания/адаптации; для запуска используй файл из scripts/.
> Для CI скопируй его в свой репозиторий (обычно как `scripts/changelog.py`).

```python
import subprocess
import re
from datetime import datetime

def get_commits_since_tag(tag: str = None) -> list:
    """Get commits since last tag"""
    if tag:
        cmd = f"git log {tag}..HEAD --pretty=format:'%H|%s|%b' --no-merges"
    else:
        cmd = "git log --pretty=format:'%H|%s|%b' --no-merges"

    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    commits = []

    for line in result.stdout.strip().split('\n'):
        if '|' in line:
            parts = line.split('|', 2)
            commits.append({
                'hash': parts[0][:7],
                'subject': parts[1],
                'body': parts[2] if len(parts) > 2 else ''
            })
    return commits

def parse_conventional_commit(subject: str) -> dict:
    """Parse conventional commit format"""
    pattern = r'^(\w+)(\([\w-]+\))?(!)?:\s*(.+)$'
    match = re.match(pattern, subject)

    if match:
        return {
            'type': match.group(1),
            'scope': match.group(2)[1:-1] if match.group(2) else None,
            'breaking': bool(match.group(3)),
            'description': match.group(4)
        }
    return {'type': 'other', 'description': subject}

def categorize_commits(commits: list) -> dict:
    """Group commits by type"""
    categories = {
        'breaking': [],
        'added': [],
        'changed': [],
        'deprecated': [],
        'removed': [],
        'fixed': [],
        'security': []
    }

    type_mapping = {
        'feat': 'added',
        'fix': 'fixed',
        'perf': 'changed',
        'refactor': 'changed',
        'security': 'security',
        'deprecate': 'deprecated',
        'remove': 'removed'
    }

    for commit in commits:
        parsed = parse_conventional_commit(commit['subject'])

        # Check for breaking changes
        if parsed.get('breaking') or 'BREAKING CHANGE' in commit.get('body', ''):
            categories['breaking'].append(commit)
            continue

        category = type_mapping.get(parsed['type'])
        if category:
            categories[category].append(commit)

    return categories

def generate_changelog(version: str, categories: dict) -> str:
    """Generate changelog markdown"""
    date = datetime.now().strftime('%Y-%m-%d')
    lines = [f"## [{version}] - {date}\n"]

    section_names = {
        'breaking': '### ⚠️ Breaking Changes',
        'added': '### Added',
        'changed': '### Changed',
        'deprecated': '### Deprecated',
        'removed': '### Removed',
        'fixed': '### Fixed',
        'security': '### Security'
    }

    for key, title in section_names.items():
        if categories.get(key):
            lines.append(f"\n{title}\n")
            for commit in categories[key]:
                parsed = parse_conventional_commit(commit['subject'])
                scope = f"**{parsed['scope']}**: " if parsed.get('scope') else ""
                lines.append(f"- {scope}{parsed['description']}")

    return '\n'.join(lines)
```

## CLI Usage

Скрипт лежит в навыке: `~/.claude/skills/changelog-generator/scripts/changelog.py`.

```bash
CL=~/.claude/skills/changelog-generator/scripts/changelog.py

# Generate changelog for next version (since last tag; no tags -> entire history)
python $CL --version 1.2.0

# Generate since specific tag
python $CL --since v1.1.0 --version 1.2.0

# Another repo + short hashes in entries
python $CL --version 1.2.0 --repo path/to/repo --hashes

# Output to file
python $CL --version 1.2.0 >> CHANGELOG.md

# Preview only (changelog -> stdout, stats -> stderr)
python $CL --version 1.2.0 --dry-run
```

## Git Commands

```bash
# Get last tag
git describe --tags --abbrev=0

# Commits since last tag
git log $(git describe --tags --abbrev=0)..HEAD --oneline

# All tags sorted by date
git tag --sort=-creatordate

# Create new tag
git tag -a v1.2.0 -m "Release 1.2.0"
git push origin v1.2.0
```

## Integration with CI/CD

### GitHub Actions

```yaml
name: Generate Changelog

on:
  push:
    tags:
      - 'v*'

jobs:
  changelog:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      # scripts/changelog.py — копия из навыка (~/.claude/skills/changelog-generator/scripts/changelog.py),
      # закоммиченная в ТВОЙ репозиторий; без неё шаг упадёт с «No such file».
      - name: Generate Changelog
        id: changelog
        run: |
          VERSION=${GITHUB_REF#refs/tags/v}
          python scripts/changelog.py --version $VERSION > release_notes.md

      - name: Create Release
        uses: softprops/action-gh-release@v1
        with:
          body_path: release_notes.md
```

## Best Practices

1. **Conventional Commits** - используй стандартный формат
2. **Scope** - указывай область изменения: `feat(auth):`
3. **Breaking Changes** - всегда помечай `!` или `BREAKING CHANGE`
4. **Атомарные коммиты** - один коммит = одно изменение
5. **User-facing** - пиши для пользователей, не для разработчиков

## Example Output

```markdown
## [2.1.0] - 2024-01-15

### ⚠️ Breaking Changes
- **api**: Changed response format for /users endpoint

### Added
- **auth**: OAuth2 login with Google and GitHub
- **ui**: Dark mode toggle in settings
- **search**: Full-text search across all documents

### Changed
- **performance**: Reduced API response time by 40%
- **database**: Migrated to connection pooling

### Fixed
- **auth**: Fixed session expiration handling
- **ui**: Corrected button alignment on mobile
- **api**: Resolved null pointer in user endpoint

### Security
- Updated axios to fix CVE-2024-xxxx
```

## Tips

1. **Squash before merge** - чистая история = чистый changelog
2. **PR title = commit message** - при squash merge
3. **Автоматизируй** - добавь в CI/CD
4. **Версионируй правильно** - breaking = major, feat = minor, fix = patch
