---
name: deepl-pro
description: "Перевод текста и документов (docx/pptx/pdf/xlsx) через DeepL, глоссарии, formality. Триггеры: «переведи», «перевод документа», «google translate»."
---

# DeepL Pro API Skill

## Overview

Expert skill for professional translation using DeepL API - the most accurate machine translation service.

## API Key

```bash
# ~/.claude/.credentials.master.env — впиши САМ КЛЮЧ, не код на Python
DEEPL_API_KEY=ВСТАВЬ_СЮДА_СВОЙ_КЛЮЧ   # https://www.deepl.com/your-account/keys
DEEPL_API_URL=https://api.deepl.com/v2
```

> Строка `DEEPL_API_KEY=os.getenv('DEEPL_API_KEY')` ключ НЕ настраивает: это непустое
> значение, любая проверка `if not key` сочтёт ключ заданным, запрос уйдёт с этим
> текстом и вернётся `403` без объяснения. В коде читай ключ через
> `os.getenv('DEEPL_API_KEY')`, а в файле должен лежать сам ключ. Файл не подгружается
> сам: `load_dotenv(Path.home()/'.claude'/'.credentials.master.env')`.

<!-- no-key-block -->
## Ключа нет — что тогда

**Сначала бесплатный тариф.** У DeepL есть план DeepL API Free: 500 000 знаков в
месяц, ключ выдаётся там же (`https://www.deepl.com/your-account/keys`) и
оканчивается на `:fx`. Он ходит на **другой** хост:

```bash
DEEPL_API_KEY=ВАШ_КЛЮЧ:fx
DEEPL_API_URL=https://api-free.deepl.com/v2      # НЕ api.deepl.com
```

Ключ Free, отправленный на `api.deepl.com`, отвечает `403 Forbidden` — ошибка про
доступ, хотя ключ верный, и человек идёт проверять оплату вместо адреса.

**Совсем без ключа:** перевод делает сама модель — просто попроси перевести текст.
Глоссарии, `formality`, сохранение разметки в `.docx`/`.pptx` при этом теряются;
если нужен именно перевод документа с сохранением вёрстки — навык `file-converter`
(вынуть текст) плюс ручная сборка обратно.

## ВАЖНО: Правильный endpoint

- **Использовать:** `api.deepl.com` (платный)
- **НЕ использовать:** `api-free.deepl.com` (вернёт ошибку)

## When to Use DeepL

**Best for:**
- High-quality text translation
- Document translation (PDF, DOCX, PPTX)
- Batch translation
- Formality control
- Custom terminology (glossaries)
- Text improvement/rephrasing

**Advantages:**
- Most accurate translations
- 33+ languages
- Document format preservation
- Formality options
- Custom glossaries
- Context-aware

## Dependencies

```bash
pip install deepl
```

## Supported Languages

**Source (auto-detect or specify):**
BG, CS, DA, DE, EL, EN, ES, ET, FI, FR, HU, ID, IT, JA, KO, LT, LV, NB, NL, PL, PT, RO, RU, SK, SL, SV, TR, UK, ZH

**Target:**
BG, CS, DA, DE, EL, EN-GB, EN-US, ES, ET, FI, FR, HU, ID, IT, JA, KO, LT, LV, NB, NL, PL, PT-BR, PT-PT, RO, RU, SK, SL, SV, TR, UK, ZH-HANS, ZH-HANT

## Basic Usage

### Setup Client

```python
import deepl
import os

translator = deepl.Translator(os.getenv('DEEPL_API_KEY'))
```

### Text Translation

```python
def translate_text(text: str, target_lang: str, source_lang: str = None,
                   formality: str = None):
    """
    Translate text.

    Args:
        text: Text to translate
        target_lang: Target language code (EN-US, DE, FR, RU, etc.)
        source_lang: Source language (auto-detect if None)
        formality: "more" (formal), "less" (informal), "prefer_more", "prefer_less"
    """
    result = translator.translate_text(
        text,
        target_lang=target_lang,
        source_lang=source_lang,
        formality=formality
    )

    return {
        "text": result.text,
        "detected_source_lang": result.detected_source_lang
    }

# Examples
translate_text("Hello, world!", "DE")  # → "Hallo, Welt!"
translate_text("Hello", "DE", formality="more")  # More formal German
translate_text("Hello", "RU")  # → "Привет!"
```

### Batch Translation

```python
def translate_batch(texts: list, target_lang: str):
    """Translate multiple texts at once."""

    results = translator.translate_text(
        texts,
        target_lang=target_lang
    )

    return [r.text for r in results]

# Usage
texts = ["Hello", "Goodbye", "Thank you"]
translated = translate_batch(texts, "FR")
# → ["Bonjour", "Au revoir", "Merci"]
```

### Document Translation

```python
def translate_document(input_path: str, output_path: str,
                       target_lang: str, source_lang: str = None):
    """
    Translate document file.

    Supported formats: .docx, .pptx, .pdf, .txt, .html, .xlsx
    """
    with open(input_path, "rb") as in_file:
        with open(output_path, "wb") as out_file:
            translator.translate_document(
                in_file,
                out_file,
                target_lang=target_lang,
                source_lang=source_lang
            )

    return output_path

# Usage
translate_document("report.docx", "report_de.docx", "DE")
translate_document("presentation.pptx", "presentation_fr.pptx", "FR")
```

### Using REST API Directly

```python
import requests

API_KEY = os.getenv('DEEPL_API_KEY')
BASE_URL = "https://api.deepl.com/v2"

def translate_api(text: str, target_lang: str, source_lang: str = None):
    """Direct API call for translation."""

    response = requests.post(
        f"{BASE_URL}/translate",
        headers={
            "Authorization": f"DeepL-Auth-Key {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "text": [text],
            "target_lang": target_lang,
            "source_lang": source_lang
        }
    )

    data = response.json()
    return data["translations"][0]["text"]
```

### Glossary (Custom Terminology)

```python
def create_glossary(name: str, source_lang: str, target_lang: str,
                    entries: dict):
    """
    Create glossary for consistent terminology.

    entries: {"source term": "target term", ...}
    """
    glossary = translator.create_glossary(
        name=name,
        source_lang=source_lang,
        target_lang=target_lang,
        entries=entries
    )

    return glossary.glossary_id

def translate_with_glossary(text: str, target_lang: str, glossary_id: str):
    """Translate using glossary."""

    result = translator.translate_text(
        text,
        target_lang=target_lang,
        glossary=glossary_id
    )

    return result.text

# Usage
glossary_id = create_glossary(
    "Tech Terms",
    "EN", "DE",
    {"machine learning": "maschinelles Lernen", "API": "API"}
)
translate_with_glossary("Using machine learning API", "DE", glossary_id)
```

### Check Usage

```python
def get_usage():
    """Get API usage statistics."""

    usage = translator.get_usage()

    return {
        "character_count": usage.character.count,
        "character_limit": usage.character.limit,
        "document_count": usage.document.count if usage.document else None
    }
```

### Text Improvement (Write API)

```python
def rephrase_text(text: str, target_lang: str = "EN-US"):
    """Improve/rephrase text quality."""

    response = requests.post(
        f"{BASE_URL}/write/rephrase",
        headers={
            "Authorization": f"DeepL-Auth-Key {API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "text": text,
            "target_lang": target_lang
        }
    )

    return response.json()["text"]
```

## Formality Options

| Value | Description |
|-------|-------------|
| `default` | Default formality |
| `more` | More formal language |
| `less` | Less formal, casual |
| `prefer_more` | More formal if available |
| `prefer_less` | Less formal if available |

**Supported languages for formality:**
DE, FR, IT, ES, NL, PL, PT, RU, JA

## API Pricing (DeepL Pro)

| Feature | Price |
|---------|-------|
| Text translation | $20/1M characters |
| Document translation | Same as text |
| Glossaries | Included |

## Quick Reference

| Task | Code |
|------|------|
| Translate text | `translator.translate_text(text, target_lang)` |
| Batch translate | `translator.translate_text([texts], target_lang)` |
| Translate document | `translator.translate_document(in_file, out_file, target_lang)` |
| Create glossary | `translator.create_glossary(name, source_lang, target_lang, entries)` |
| Check usage | `translator.get_usage()` |

## Tips

1. **Auto-detect** - не указывай source_lang для автоопределения
2. **Formality** - используй для DE, FR, ES, RU и др.
3. **Glossaries** - для консистентной терминологии
4. **Documents** - сохраняет форматирование
5. **EN-US vs EN-GB** - указывай точный вариант
6. **PT-BR vs PT-PT** - бразильский или португальский
7. **ZH-HANS vs ZH-HANT** - упрощенный или традиционный китайский
