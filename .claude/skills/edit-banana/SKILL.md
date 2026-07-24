---
name: edit-banana
description: "Edit Banana — convert diagram images (PNG/JPG) into editable DrawIO XML. Edit text on screenshots of flowcharts, architecture diagrams, tables, formulas. Uses SAM 3 + PaddleOCR + Gemini VLM. Local install at ~/Edit-Banana with CUDA support."
---

# Edit Banana — Редактирование текста на картинках

> **Аналог:** editbanana.anxin6.cn/app (web demo)
> **GitHub:** BIT-DataLab/Edit-Banana (Apache 2.0)
> **Локальная установка:** `~/Edit-Banana/`
> **venv:** `~/Edit-Banana/.venv/` (Python 3.11, uv)

## Что делает

Превращает статичные изображения диаграмм/таблиц/формул в редактируемые
DrawIO XML-файлы с сохранением:
- Оригинального layout (позиции элементов)
- Цветов и оформления
- Логических связей (стрелки, линии)
- Текста (в редактируемых блоках)

Экспорт: **DrawIO XML** (основной) → SVG/PNG/PowerPoint через конверсию в draw.io.

## Когда использовать

- Редактирование текста на скриншоте диаграммы (flowchart, архитектурная схема)
- Перевод диаграммы на другой язык без перерисовки
- Извлечение таблиц в редактируемый формат
- Реконструкция формул в LaTeX
- "Оживление" старых PDF/PNG презентаций

## Быстрый старт

### Single image (CLI)

```bash
cd ~/Edit-Banana
.venv/Scripts/python.exe main.py -i input/diagram.png
# → output/diagram.xml (открыть в app.diagrams.net)
```

### Batch processing

```bash
cd ~/Edit-Banana
cp ~/Downloads/*.png input/
.venv/Scripts/python.exe main.py
# → output/*.xml для всех картинок из input/
```

### Web API (FastAPI)

```bash
cd ~/Edit-Banana
.venv/Scripts/python.exe server_pa.py
# → http://localhost:8000/docs (Swagger UI)
```

## Архитектура pipeline

```
Input PNG/JPG
    ↓
[1] SAM 3 segmentation (CUDA on your GPU)
    ↓ boxes for shapes, arrows, backgrounds, images
[2] PaddleOCR text recognition (per-element)
    ↓ text content + positions
[3] Gemini 2.5 Flash VLM (structure guidance)
    ↓ logical hierarchy, element classification
[4] DrawIO XML generation
    ↓ merge spatial + text + semantic
Output XML
```

## Конфигурация

`~/Edit-Banana/config/config.yaml`:

| Параметр | Значение | Что делает |
|----------|----------|-----------|
| `sam3.checkpoint_path` | `models/sam3_ms/sam3.pt` | SAM3 веса (~4 GB) |
| `sam3.bpe_path` | `models/bpe_simple_vocab_16e6.txt.gz` | BPE токенизатор |
| `ocr.engine` | `paddleocr` | Text recognition (можно переключить на tesseract) |
| `multimodal.model` | `gemini-2.5-flash` | VLM для структуры |
| `multimodal.api_key` | `${GOOGLE_API_KEY}` | Ключ из `.credentials.master.env` |
| `multimodal.base_url` | `https://generativelanguage.googleapis.com/v1beta/openai/` | Gemini OpenAI-compatible endpoint |

### Смена VLM

- **Gemini 2.5 Flash** (по умолчанию, быстро, дёшево): `model: "gemini-2.5-flash"`
- **Gemini 2.5 Pro** (точнее, медленнее): `model: "gemini-2.5-pro"`
- **Claude Opus via AI Gateway:** указать OpenAI-compat endpoint на your-server gateway
- **Локальная VLM (Ollama):** установить `qwen2.5vl` в Ollama, `mode: "local"`

## Применённые патчи (Windows + torch 2.5.1)

Без патча pipeline падал на `[2] Segmentation (SAM3)` с dtype mismatch
(BFloat16 vs Float) в `perflib/fused.addmm_act`: fused kernel кастует mat1/mat2
в bf16, но смежные Linear слои работают в float32 → конфликт.

**Единственный нужный патч:** `sam3_src/sam3/perflib/fused.py`:`addmm_act()` —
заменён fused bf16 путь на обычный `torch.nn.functional.linear` + activation.
Скорость снижается незначительно, pipeline стабилен на GPU.

## Что получаем на выходе

`output/<basename>/`:
- `<basename>_merged.drawio.xml` — **главный результат**, редактируемая диаграмма для draw.io
- `text_only.drawio` — только текстовый слой (из OCR)
- `sam3_extraction.png` — визуализация найденных shape-элементов
- `sam3_metadata.json` — метаданные всех сегментов (bbox, mask, score)

## Пример результата (smoke test)

Демо `static/demo/original_1.jpg` (flowchart):
- 62 текстовых блока (PaddleOCR, 83 сек)
- 60 icons + 34 SAM3 shapes + 4 CV shapes = 98 фрагментов
- 160 элементов в итоговом DrawIO XML (287 KB)
- Время: ~3 мин на your GPU

## Установка (что уже сделано)

- [x] Git clone `BIT-DataLab/Edit-Banana` → `~/Edit-Banana`
- [x] Python 3.11 venv через uv → `.venv/`
- [x] PyTorch + CUDA (GPU stack) (your GPU)
- [x] Base requirements (fastapi, opencv, scikit-image, pytesseract)
- [x] SAM3 библиотека (facebook/sam3 clone + pip install -e)
- [x] BPE vocab → `models/bpe_simple_vocab_16e6.txt.gz`
- [x] PaddleOCR (paddlepaddle 3.2.2 + paddleocr)
- [x] `config/config.yaml` с Gemini 2.5 Flash + PaddleOCR
- [ ] **SAM3 веса** (`models/sam3_ms/sam3.pt`, ~4 GB) — качается с ModelScope, см. ниже
- [ ] Tesseract (опционально, сейчас используется PaddleOCR)

### Если SAM3 веса не докачались

```bash
~/Edit-Banana/.venv/Scripts/python.exe -c "
from modelscope import snapshot_download
snapshot_download('facebook/sam3', cache_dir='${HOME}/Edit-Banana/models_ms_cache', allow_patterns=['sam3.pt'])
"
# → переместить файл в models/sam3_ms/sam3.pt
mv ~/Edit-Banana/models_ms_cache/facebook/sam3/sam3.pt ~/Edit-Banana/models/sam3_ms/
```

### Установка Tesseract (опционально)

```bash
# Вариант A (choco — на момент установки сервер был 503):
choco install tesseract --yes

# Вариант B (winget):
winget install UB-Mannheim.TesseractOCR

# Вариант C (вручную): скачать с https://github.com/UB-Mannheim/tesseract/wiki
```

После установки изменить `ocr.engine: "tesseract"` в config.yaml.

## Опциональные модули

**Pix2Text** (распознавание формул → LaTeX):
```bash
~/AppData/Local/Programs/Python/Python313/Scripts/uv.exe pip install --python ~/Edit-Banana/.venv/Scripts/python.exe pix2text onnxruntime-gpu
```

**RMBG** (удаление фона у иконок):
```bash
~/AppData/Local/Programs/Python/Python313/Scripts/uv.exe pip install --python ~/Edit-Banana/.venv/Scripts/python.exe onnxruntime modelscope
cd ~/Edit-Banana && .venv/Scripts/python.exe scripts/setup_rmbg.py
```

## Troubleshooting

| Ошибка | Причина | Решение |
|--------|---------|---------|
| `no kernel image is available` | GPU arch mismatch | Upgrade PyTorch или `device: "cpu"` в config |
| `Model file not found at sam3.pt` | Веса не скачались | См. "Если SAM3 веса не докачались" |
| `PaddleOCR inference failed` | Баг в paddlepaddle 3.3.0+ | Использовать 3.2.2 (уже установлено) |
| `Gemini API error 403` | Неправильный ключ | Проверить `GOOGLE_API_KEY` в `.credentials.master.env` |
| `GatedRepoError` на HF | SAM3 закрыт на HuggingFace | Использовать ModelScope (уже в настройках) |

## CLI wrapper (для вызова из любой директории)

Скрипт `~/.claude/skills/edit-banana/scripts/edit-banana.sh` — обёртка,
принимает путь к картинке и вызывает pipeline из корректной директории.

```bash
bash ~/.claude/skills/edit-banana/scripts/edit-banana.sh path/to/diagram.png
# → результат в ~/Edit-Banana/output/
```

## Триггеры (routing)

Вызывать при запросах:
- "редактировать текст на картинке"
- "перевести диаграмму"
- "извлечь таблицу в редактируемый формат"
- "конвертировать PNG в drawio"
- "edit banana"

## Ссылки

- **GitHub:** https://github.com/BIT-DataLab/Edit-Banana
- **Web demo:** https://editbanana.anxin6.cn/
- **SAM 3 (facebook):** https://github.com/facebookresearch/sam3
- **PaddleOCR:** https://github.com/PaddlePaddle/PaddleOCR
