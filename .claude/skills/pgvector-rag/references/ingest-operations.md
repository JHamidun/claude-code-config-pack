# Bulk ingest и долгие прогоны — операционка

Читать при массовой индексации (тысячи файлов, часы-сутки), переиндексации корпуса
или выносе эмбеддера в инфраструктуру. Для проектирования RAG хватает SKILL.md.

## GPU/CPU планирование (замеры на корпусе издательского масштаба: ~3.5 тыс. книг, ~1.2B токенов)

| Платформа | Speed (512-token чанки) | Полный корпус ~2-3M чанков |
|---|---|---|
| RTX 4090 Laptop (Qwen3-0.6B) | **~9 chunks/s** | ~24h business + ~36h all |
| VPS без GPU (6 vCPU, Qwen3-0.6B) | **0.3-1 chunk/s** | **~26 дней** — НЕ ГОДИТСЯ для bulk |
| OpenAI 3-large (rate-limited) | ~rate limit | ~3h, но ~$122 |

**Правило:** bulk re-embed только на GPU. CPU годится лишь для query-time (1 запрос ~1-2s) — приемлемо для чат-бота, недопустимо для индексации.

**Cold start:** Qwen3 грузится в память ~30s при первом запросе (lazy-load в sentence-transformers). Либо prewarm dummy-запросом на старте, либо подними timeout у вызывающего до 120s + закэшируй.

## Embedder как отдельный микросервис

Когда одну embedding-модель шарят несколько сервисов (коннектор контента, бот, API) — выноси Qwen3 в свой контейнер с HTTP `/embed`, а не тащи torch+sentence-transformers (~3 GB) в каждый образ:

```python
# embedder-сервис: FastAPI + lazy SentenceTransformer
@app.post('/embed')
def embed(req):                      # req.texts: list[str]
    m = get_model()                  # lazy-load, держим в памяти
    v = m.encode(req.texts, batch_size=16, normalize_embeddings=True)
    return {'vectors': v.tolist(), 'dim': v.shape[1]}
```

- Образ: `python:3.11-slim` + torch CPU + sentence-transformers, модель **предзагружена на build** (`RUN python -c "SentenceTransformer(...)"`), чтобы первый запрос не качал 1.2 GB.
- Вызывающий: httpx timeout 120s (cold start) + `@lru_cache` на query-эмбеддинги (регулярный дайджест повторяет одни и те же запросы → ~70% hit).
- Грабля: проверь занятость порта — у нас `:8096` оказался занят другим контейнером, замапили `8097:8096`.

## Реконструкция исходника из существующего vector store

Если нужно переиндексировать (сменилась модель/чанкинг), а оригинальных файлов нет — собери текст обратно из чанков, если point ID последовательны:

```python
# Scroll все точки, группируй по book_title, сортируй по id (= порядок чанков), concat text
by_book[(title, isbn)].append((point_id, text))
...
items.sort(key=lambda x: x[0])           # ascending id = исходный порядок
full_text = "\n\n".join(t for _, t in items)
```

Проверено на живом корпусе: ~3.5 тыс. книг восстановлены из Qdrant-чанков без исходных EPUB, потери только на overlap-границах (новый chunker 512/64 их съедает). **Caveat:** работает только если ingestor писал чанки последовательно (id 0,1,2... в порядке документа). Проверь sample перед массовым прогоном.

## Устойчивость переноса данных

- **Resume-friendly transfer.** Сеть — реальное бутылочное горло (SSH-канал к серверу просел с 22 MB/s до 70 KB/s, 4.8 GB = 19h). Используй `tar … --skip-old-files` или rsync для докачки. Лучше — эмбедь рядом с данными, не гоняй гигабайты.
- **Долгий прогон — truly detached.** `nohup`/Scheduled Task, НЕ дочерний процесс сессии. И БЕЗ `set -e` на сетевых шагах (иначе один dropped-стрим убивает весь pipeline — у нас так и умер orchestrator на середине download).

## Gateway-proxied embeddings (обход мёртвого ключа)

Если прямой OpenAI-ключ исчерпан/протух, а рядом есть AI Gateway с рабочим ключом — направь embeddings через него, не меняя код:

```python
openai_client = OpenAI(api_key='proxy', base_url='http://ai-gateway:8080/openai/v1')
# /openai/v1/embeddings проксируется gateway'ем со своим ключом
```

Спасло коннектор контента, когда оба OpenAI-ключа вернули `insufficient_quota`.

## Multi-day прогоны (замерено на транскрипции 1 255 видео)

### 1. Долгому ingest нужен OS-level супервайзер, не shell background

Перепробовали и подтвердили — каждое решение умерло раньше, чем доехал ран:

| Запуск | Сколько прожил | Почему умер |
|---|---|---|
| `python ... &` в bash | до конца сессии bash | child привязан к session shell |
| `run_in_background: true` в Bash-tool харнеса | несколько часов | харнес чистит «фон» при cleanup |
| PowerShell `Start-Process -WindowStyle Hidden` | минуту | parent PS закрылся → child убит |
| **`schtasks` + `.bat` self-loop** | **2+ суток, 1 255 файлов** | управляется Windows, переживает всё кроме reboot |

Шаблон `.bat`-обёртки:

```bat
@echo off
cd /d C:\path\to\project
:loop
echo === LOOP RESTART %DATE% %TIME% === >> D:\logs\ingest.log
python -X utf8 script.py >> D:\logs\ingest.log 2>&1
echo === EXITED (code %ERRORLEVEL%) at %DATE% %TIME% === >> D:\logs\ingest.log
timeout /t 30 /nobreak >nul
goto loop
```

Регистрация и немедленный запуск:

```cmd
schtasks /Create /TN MyIngest /TR "C:\path\wrapper.bat" /SC ONCE /ST 23:59 /F
schtasks /Run /TN MyIngest
```

Live `===` маркеры в логе позволяют сразу сказать сколько было рестартов и где провалился прошлый запуск.

### 2. У self-restart loop ОБЯЗАН быть «нечего делать» exit

Когда работа кончилась, скрипт рестартился вхолостую каждые 30 с — через **~1 500 рестартов python.exe начал падать со STATUS_DLL_INIT_FAILED (0xC0000142)** (Windows исчерпал init-pool процессов). Профилактика: signal-флаг + проверка в .bat:

```python
# в ingest-скрипте после успешного цикла:
if not pending_files:
    Path("D:/flags/RUN_COMPLETE.flag").touch()
    sys.exit(0)
```

```bat
:loop
if exist D:\flags\RUN_COMPLETE.flag exit /b 0
python -X utf8 script.py >> log 2>&1
timeout /t 30 /nobreak >nul
goto loop
```

Иначе watchdog буквально load-тестит OS до отказа.

### 3. Resumability через file-sentinel

Дешёвый skip в начале каждого файла:

```python
out_path = out_dir / f"{stem}.md"
if out_path.exists() and out_path.stat().st_size > 200:
    skipped += 1
    continue
```

На 1 255 видео и 1 544 + 1 368 рестартов на двух workers — ни одной потери прогресса. Вместе с idempotent upsert (delete-then-insert) = супервайзер, который можно перезапускать сколько угодно.

### 4. Мониторь БД, а не stdout

`python script.py > log 2>&1` буферизирует stdout ~4 KB — лог пустой час, а в БД строки появляются каждую секунду. В проде смотри `SELECT COUNT(*) FROM "{idx}"` каждые 1-5 минут, а не `tail -f log`. (`python -u` форс-флашит, но лишний syscall на каждый print редко того стоит.)

### 5. Не параллелить GPU-embedding процессы

CUDA сериализует доступ внутри драйвера, VRAM × 2 впустую, ускорение ~0. Правильно: один GPU-worker с большим `batch_size` (sentence-transformers на 4090 — 32-64 ок). Для CPU-workers (sherpa-onnx ASR) — наоборот: на 16-ядерном 185H два потока × 8 threads дали ~1.6× throughput.

### 6. SSH-туннель живёт меньше многосуточного ingest

`ssh -fN -L 5502:127.0.0.1:5502 "$SERVER"` падал каждые 1-2 суток; видно только по тайм-ауту следующего connect. Варианты:
- `autossh -M 0 -o "ServerAliveInterval 30" -o "ServerAliveCountMax 3" -fN -L 5502:127.0.0.1:5502 "$SERVER"`
- Pre-check порта в скрипте + reopen `subprocess.Popen(["ssh", "-fN", "-L", ...])`
- Или не SSH вовсе: Tailscale / Cloudflare Tunnel

### 7. Считай файлы по ВСЕМ media-расширениям перед оценкой ETA

`find -name "*.webm"` показал 172, реально было 415 (172 webm + 241 mkv + 2 mp4) — ETA промахнулась в 2.4×:

```bash
find <root> -type f \( -name "*.webm" -o -name "*.mkv" -o -name "*.mp4" -o -name "*.m4a" \) | wc -l
```

### 8. CI-гейт `pnpm audit` может блокировать pure-Python PR в TS-монорепо

Pre-existing CVE в Next.js/aws-sdk валит security gate, не связанный с диффом. Чистка transitive deps через `pnpm.overrides` в root package.json; порядок PR-ов: первый — security bump, второй — RAG-код.

### 9. Чанк-производительность зависит от плотности контента

| Индекс | Содержимое | Чанков / файл | Throughput на 4090 |
|---|---|---|---|
| `idx_*_book` | плотный текст книги (632 KB md) | 382 / файл | 61 с total |
| `idx_*_courses` | markdown курсов | ~3.3 / файл | 5 463 за 2.6 ч |
| `idx_*_transcripts` | ASR-транскрипт видео | ~4-6 / видео | ~5 000 за ~15 мин |

Транскрипты дают меньше чанков на час видео, чем кажется. Перед новым источником — pilot на 5% корпуса; экстраполяция между типами контента ошибается в разы.

### 10. ASR-to-RAG: чанк ASR на 180 с, не 600 с

sherpa-onnx Parakeet TDT INT8 на 600-секундном чанке падает с `Non-zero status code ... broadcast 748 by 5748` (overflow позиционного энкодера). Безопасный `chunk_seconds=180` + per-chunk try/except (один битый кусок не убивает файл) + `rglob` для discovery (плоский `iterdir` терял ~80% файлов в подпапках per-курс).
