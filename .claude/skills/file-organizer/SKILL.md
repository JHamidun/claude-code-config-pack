---
name: file-organizer
description: "Раскладка файлов по контексту, типу и дате с автоматизацией. Триггеры: «организуй файлы», «разбери папку», «наведи порядок в загрузках», «sort files»."
---

# File Organizer Skill

## Overview

Интеллектуальная организация файлов по контексту, типу, дате. Автоматизация сортировки.

## When to Use

- Наведение порядка в папках
- Организация Downloads
- Архивирование проектов
- Автоматическая сортировка
- Подготовка к бэкапу

## Organization Strategies

### By Type

```
Documents/
├── PDFs/
├── Word/
├── Excel/
├── Presentations/
└── Text/

Media/
├── Images/
│   ├── Photos/
│   ├── Screenshots/
│   └── Graphics/
├── Video/
├── Audio/
└── GIFs/

Code/
├── Projects/
├── Scripts/
├── Snippets/
└── Archives/
```

### By Date

```
Archive/
├── 2024/
│   ├── Q1/
│   │   ├── January/
│   │   ├── February/
│   │   └── March/
│   └── Q2/
└── 2023/
```

### By Project

```
Projects/
├── Active/
│   ├── ProjectA/
│   │   ├── docs/
│   │   ├── assets/
│   │   └── exports/
│   └── ProjectB/
├── On-Hold/
└── Completed/
    └── 2024/
```

### By Status (GTD)

```
Work/
├── Inbox/           # Unsorted new files
├── Action/          # Need to work on
├── Waiting/         # Waiting for response
├── Reference/       # Keep for reference
└── Archive/         # Done, but keep
```

## Python Automation

### Basic File Sorter

```python
import os
import shutil
from pathlib import Path
from datetime import datetime

# File type mapping
FILE_TYPES = {
    'Images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.bmp'],
    'Documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt'],
    'Spreadsheets': ['.xls', '.xlsx', '.csv'],
    'Presentations': ['.ppt', '.pptx'],
    'Videos': ['.mp4', '.mov', '.avi', '.mkv', '.webm'],
    'Audio': ['.mp3', '.wav', '.flac', '.m4a', '.ogg'],
    'Archives': ['.zip', '.rar', '.7z', '.tar', '.gz'],
    'Code': ['.py', '.js', '.ts', '.html', '.css', '.json', '.md'],
    'Data': ['.sql', '.db', '.sqlite', '.json', '.xml', '.yaml'],
}

def organize_by_type(source_dir: str, dest_dir: str):
    """Organize files by type"""
    source = Path(source_dir)
    dest = Path(dest_dir)

    for file in source.iterdir():
        if file.is_file():
            ext = file.suffix.lower()

            # Find category
            category = 'Other'
            for cat, extensions in FILE_TYPES.items():
                if ext in extensions:
                    category = cat
                    break

            # Create dest folder and move
            dest_folder = dest / category
            dest_folder.mkdir(parents=True, exist_ok=True)
            shutil.move(str(file), str(dest_folder / file.name))
            print(f"Moved: {file.name} → {category}/")

# Usage
organize_by_type("~/Downloads", "~/Organized")
```

### Date-Based Organization

```python
from datetime import datetime

def organize_by_date(source_dir: str, dest_dir: str):
    """Organize files by creation/modification date"""
    source = Path(source_dir)
    dest = Path(dest_dir)

    for file in source.iterdir():
        if file.is_file():
            # Get file date
            timestamp = file.stat().st_mtime
            date = datetime.fromtimestamp(timestamp)

            # Create folder structure: Year/Month
            year_month = date.strftime("%Y/%m-%B")
            dest_folder = dest / year_month
            dest_folder.mkdir(parents=True, exist_ok=True)

            shutil.move(str(file), str(dest_folder / file.name))
            print(f"Moved: {file.name} → {year_month}/")

# Usage
organize_by_date("~/Downloads", "~/Archive")
```

### Smart File Renaming

```python
import re
from datetime import datetime

def clean_filename(filename: str) -> str:
    """Clean and standardize filename"""
    name, ext = os.path.splitext(filename)

    # Remove special characters
    name = re.sub(r'[^\w\s-]', '', name)

    # Replace spaces with underscores
    name = re.sub(r'\s+', '_', name)

    # Lowercase
    name = name.lower()

    # Add date prefix if not present
    if not re.match(r'^\d{4}', name):
        date_prefix = datetime.now().strftime("%Y%m%d_")
        name = date_prefix + name

    return name + ext.lower()

def batch_rename(directory: str, pattern: str = None):
    """Batch rename files"""
    path = Path(directory)

    for i, file in enumerate(sorted(path.iterdir()), 1):
        if file.is_file():
            new_name = clean_filename(file.name)
            file.rename(file.parent / new_name)
            print(f"Renamed: {file.name} → {new_name}")
```

### Duplicate Finder

```python
import hashlib
from collections import defaultdict

def get_file_hash(filepath: Path) -> str:
    """Calculate file hash"""
    hasher = hashlib.md5()
    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def find_duplicates(directory: str) -> dict:
    """Find duplicate files"""
    hashes = defaultdict(list)

    for file in Path(directory).rglob('*'):
        if file.is_file():
            file_hash = get_file_hash(file)
            hashes[file_hash].append(file)

    # Return only duplicates
    return {h: files for h, files in hashes.items() if len(files) > 1}

def remove_duplicates(directory: str, keep: str = 'first'):
    """Remove duplicate files, keeping first or newest"""
    duplicates = find_duplicates(directory)

    for hash_val, files in duplicates.items():
        if keep == 'newest':
            files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        # Keep first, remove rest
        for file in files[1:]:
            print(f"Removing duplicate: {file}")
            file.unlink()
```

### Watch Folder Automation

```python
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import time

class FileOrganizer(FileSystemEventHandler):
    def __init__(self, dest_dir):
        self.dest_dir = Path(dest_dir)

    def on_created(self, event):
        if not event.is_directory:
            file = Path(event.src_path)
            # Wait for file to finish downloading
            time.sleep(1)
            self.organize_file(file)

    def organize_file(self, file: Path):
        ext = file.suffix.lower()

        for category, extensions in FILE_TYPES.items():
            if ext in extensions:
                dest = self.dest_dir / category
                dest.mkdir(exist_ok=True)
                shutil.move(str(file), str(dest / file.name))
                print(f"Auto-organized: {file.name} → {category}/")
                return

def watch_folder(watch_dir: str, dest_dir: str):
    """Watch folder and auto-organize new files"""
    observer = Observer()
    handler = FileOrganizer(dest_dir)
    observer.schedule(handler, watch_dir, recursive=False)
    observer.start()

    print(f"Watching {watch_dir}...")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

# Run in background
# watch_folder("~/Downloads", "~/Organized")
```

## Naming Conventions

### Files

```markdown
## Good Naming:
✅ 2024-01-15_project-report_v2.pdf
✅ invoice_acme-corp_2024-01.pdf
✅ screenshot_2024-01-15_143052.png

## Bad Naming:
❌ final_FINAL_v3_REAL(1).docx
❌ Document1.pdf
❌ asdfgh.txt
❌ New folder (3)/file.doc

## Pattern:
[date]_[description]_[version].[ext]
[type]_[subject]_[date].[ext]
```

### Folders

```markdown
## Conventions:
- lowercase-with-dashes
- or_underscores_like_this
- Clear, descriptive names
- No spaces (use - or _)

## Examples:
✅ project-alpha
✅ 2024-q1-reports
✅ client_acme
❌ New Folder
❌ Stuff
❌ IMPORTANT!!!
```

## Folder Templates

### Project Template

```bash
#!/bin/bash
# create-project.sh

PROJECT_NAME=$1
mkdir -p "$PROJECT_NAME"/{
    docs,
    assets/{images,videos,fonts},
    src,
    tests,
    exports,
    .archive
}

touch "$PROJECT_NAME/README.md"
touch "$PROJECT_NAME/.gitignore"

echo "Created project structure: $PROJECT_NAME"
```

### Client Folder Template

```
client-name/
├── 01-briefs/
├── 02-contracts/
├── 03-invoices/
├── 04-deliverables/
├── 05-correspondence/
└── 06-archive/
```

## Tips

1. **Inbox zero** - регулярно разбирай Downloads
2. **One system** - придерживайся одной схемы
3. **Automate** - используй скрипты
4. **Date prefix** - облегчает сортировку
5. **Archive, don't delete** - сначала архивируй
6. **Backups** - перед большой реорганизацией
7. **README** - документируй структуру
