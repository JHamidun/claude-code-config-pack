---
name: file-converter
description: "Локальный MCP-сервер конвертации файлов (file-converter в mcp.json, uvx, без API-ключа): Word↔PDF, изображения и др. форматы. Триггеры: «конвертируй файл», «convert file», «file format», «word в pdf», «pdf в word»."
---

# File Converter MCP Server Skill

## Overview

Локальный MCP сервер для конвертации файлов. **Без API ключа!**

## Installation

Уже добавлен в `mcp.json`:

```json
{
  "file-converter": {
    "type": "stdio",
    "command": "uvx",
    "args": [
      "--from",
      "git+https://github.com/<author>/file-converter-mcp",
      "file-converter-mcp"
    ]
  }
}
```

### Зависимости (устанавливаются автоматически):

```bash
pip install mcp docx2pdf pdf2docx pillow pandas pdfkit markdown
```

## Features

### Конвертация документов:

| Из | В | Tool |
|----|---|------|
| **Word (.docx)** | PDF | `docx_to_pdf` |
| **PDF** | Word (.docx) | `pdf_to_docx` |
| **Excel (.xlsx)** | CSV | `excel_to_csv` |
| **HTML** | PDF | `html_to_pdf` |
| **Markdown** | PDF | `markdown_to_pdf` |

### Конвертация изображений:

| Из | В | Tool |
|----|---|------|
| **PNG** | JPG, WebP, etc. | `convert_image` |
| **JPG** | PNG, WebP, etc. | `convert_image` |
| **WebP** | PNG, JPG, etc. | `convert_image` |
| **Любой формат** | Любой формат | `convert_image` |

## MCP Tools

После установки доступны:

| Tool | Описание |
|------|----------|
| `docx_to_pdf` | Word → PDF |
| `pdf_to_docx` | PDF → Word |
| `excel_to_csv` | Excel → CSV |
| `html_to_pdf` | HTML → PDF |
| `markdown_to_pdf` | Markdown → PDF |
| `convert_image` | Конвертация изображений |

## Usage

### Через Claude Code (MCP):

```
# Конвертировать Word в PDF
Конвертируй document.docx в PDF

# Конвертировать PDF в Word
Преобразуй report.pdf в редактируемый Word документ

# Конвертировать изображение
Конвертируй image.png в WebP формат

# Excel в CSV
Преобразуй data.xlsx в CSV
```

### Input modes:

1. **File path** - путь к файлу на диске
2. **Base64** - закодированный контент файла

## Advantages

| Feature | file-converter-mcp | PDF.co |
|---------|-------------------|--------|
| API Key | **Не нужен** | Нужен |
| Стоимость | **Бесплатно** | Платно |
| Offline | **Да** | Нет |
| Приватность | **Локально** | Cloud |
| Скорость | **Быстро** | Зависит от сети |

## When to Use

| Задача | Используй |
|--------|-----------|
| Word ↔ PDF | `file-converter` |
| Image conversion | `file-converter` |
| Excel → CSV | `file-converter` |
| HTML/MD → PDF | `file-converter` |
| PDF → JSON/Text (OCR) | `markitdown` MCP |

## Tips

1. **Локальная обработка** - файлы не уходят в облако
2. **Без лимитов** - конвертируй сколько нужно
3. **Быстро** - нет сетевых задержек
4. **Комбинируй** с `markitdown` для извлечения текста из PDF

## Source

GitHub: [<author>/file-converter-mcp](https://github.com/<author>/file-converter-mcp)
