---
description: "Перевод через DeepL Pro: текст, formality, документы docx/pptx/pdf/xlsx. Триггеры: «переведи», «перевод документа». Массовый Google-перевод → /gtranslate."
argument-hint: "<text> [target_lang] [formal] | file <path> <lang> | usage"
---

# Translate

/translate - Professional translation via DeepL Pro API

## Usage
```
/translate <text>                    - Auto-detect -> English (configurable)
/translate <text> EN                 - Translate to English
/translate <text> DE formal          - Translate to formal German
/translate file <path> <target_lang> - Translate document
/translate usage                     - Check API usage/limits
```

## Instructions for Claude

Uses DeepL Pro API. Full reference: `~/.claude/skills/deepl-pro/SKILL.md`

### Quick translate

```python
import deepl
import os
from dotenv import load_dotenv

load_dotenv('${HOME}/.claude/.credentials.master.env')
translator = deepl.Translator(os.getenv('DEEPL_API_KEY'))

# Text translation
result = translator.translate_text("Hello world", target_lang="RU")
print(result.text)  # "Привет мир"

# With formality
result = translator.translate_text("How are you?", target_lang="DE", formality="more")

# Batch
results = translator.translate_text(["Hello", "Goodbye"], target_lang="FR")
for r in results:
    print(r.text)
```

### Translate document

```python
# Supports: .docx, .pptx, .pdf, .txt, .html, .xlsx
with open("report.docx", "rb") as in_file:
    with open("report_de.docx", "wb") as out_file:
        translator.translate_document(in_file, out_file, target_lang="DE")
```

### Check usage

```python
usage = translator.get_usage()
print(f"Characters: {usage.character.count}/{usage.character.limit}")
```

## Language codes

**Common:** RU, EN-US, EN-GB, DE, FR, ES, IT, PT-BR, ZH-HANS, JA, KO, TR, PL, UK

**Formality** (DE, FR, ES, RU, IT, NL, PL, PT, JA): `more`, `less`, `prefer_more`, `prefer_less`

## Important

- Use `api.deepl.com` (NOT `api-free.deepl.com`)
- DEEPL_API_KEY from `~/.claude/.credentials.master.env`
