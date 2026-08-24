---
name: trend-engine
description: "Viral detector + выбор темы контента: z-score по платформам, Google Trends, разбор конкурентов. Триггеры: «что снимать», «топ тема для шортса»."
allowed-tools: Bash, Read, Write, WebSearch
---

# Trend Engine

> Multi-source viral detector + auto-pick scoring под контент ТВОЕГО канала.
> Дополняет `last30days` и `tiktok-intel` детекцией аномалий по z-score, Google Trends,
> разбором транскриптов конкурентов и выбором темы моделью.

## Что понадобится

| Что | Платно | Где взять | Без этого |
|---|---|---|---|
| `SCRAPECREATORS_API_KEY` | **да, 1 кредит за запрос** (полный прогон ~15-20) | scrapecreators.com | нет TikTok/Instagram источников — остаются Google Trends и `last30days` |
| `pytrends` | нет | `pip install pytrends` | нет Google Trends, остальное работает |
| `YOUTUBE_API_KEY` | нет (квота бесплатная) | Google Cloud Console → YouTube Data API v3 | нет истории своего канала — темы будут повторяться |
| навык `last30days` | нет | в паке | нет сводки Reddit/X/YT/HN |

Ключи — в переменных окружения или в своём `.credentials.master.env`
(шаблон: `~/.claude/templates/.credentials.master.env.example`).

## Профиль канала — заполнить ДО первого прогона

Скоринг считается **относительно твоего канала**, поэтому в начале работы нужны
четыре вещи. Держи их в `~/.claude/business-context.md` (шаблон в `~/.claude/templates/`)
или прямо в промпте:

| Поле | Пример | Зачем |
|---|---|---|
| Ниша и язык аудитории | «ИИ и технологии, русскоязычная» | отсекает темы, которые «вирусные», но не для твоих |
| S-tier темы (взрывались) | 3-5 тем из своей же аналитики | вес `channel_fit` |
| A-tier темы (стабильно хорошо) | 3-5 тем | вес `channel_fit` |
| Формат и длина | «shorts 15-25 сек, вертикаль» | вес `visual_potential` |

Не знаешь свои S/A-tier — сначала `youtube-analytics` по своему каналу за 90 дней.
Подставлять чужие списки бессмысленно: они описывают чужую аудиторию.

## When to Use

- "найди вирусный тренд" — что сейчас взрывается на всех платформах
- "лучший тренд для видео" / "что снимать сегодня" — auto-pick single best topic
- "проанализируй конкурента" — hook/body/CTA breakdown от viral видео
- "viral detector" — запустить полный 4-шаговый пайплайн
- "топ тема для шортса" — выбор темы с учётом S/A-tier своего канала

---

## How It Works — 4-Step Pipeline

```
Step 1: GATHER    → 5 parallel sources (Reddit/X/YT/TikTok/HN + TikTok API + Google Trends + channel history)
Step 2: SCORE     → Viral Detector (z-score ER anomaly detection per platform)
Step 3: ANALYZE   → Transcript breakdown of HOT/VIRAL videos (hook / body / CTA)
Step 4: PICK      → Claude scoring on 5 dimensions → trend_brief.json
```

Total time: ~3-5 minutes for full pipeline. ~1 minute for quick mode (skip Step 3).

---

## Step 1: Gather Trends (Multi-Source)

### Source A — last30days (Reddit / X / YouTube / TikTok / HN)

```bash
# Quick sweep across platforms. Тема — ПОЗИЦИОННЫЙ аргумент, без неё скрипт не работает.
# --quick режет до топа по каждому источнику; машинный JSON = --emit json --json-profile agent.
# Флага --agent НЕТ: он валит запуск с usage-ошибкой (проверено 2026-08-17).
python ~/.claude/skills/last30days/scripts/last30days.py "<тема>" \
  --emit json --json-profile agent --quick --output /tmp/te_last30.json
```

If `last30days` CLI is unavailable, trigger the skill directly:
> "Run last30days skill with quick mode, output top 10 trending topics per platform to /tmp/te_last30.json"

### Source B — TikTok API (4 parallel calls, 4 credits)

```bash
# Ключ из окружения; если держишь свой .credentials.master.env — подхвати его:
[ -f ~/.claude/.credentials.master.env ] && source ~/.claude/.credentials.master.env
API="https://api.scrapecreators.com"
H="x-api-key: $SCRAPECREATORS_API_KEY"

curl -s "$API/v1/tiktok/get-trending-feed"    -H "$H" > /tmp/te_tt_trending.json &
curl -s "$API/v1/tiktok/songs/popular"         -H "$H" > /tmp/te_tt_songs.json &
curl -s "$API/v1/tiktok/hashtags/popular"      -H "$H" > /tmp/te_tt_hashtags.json &
curl -s "$API/v1/tiktok/creators/popular"      -H "$H" > /tmp/te_tt_creators.json &
wait
```

Extract topic signals from trending feed titles + hashtag names.

### Source C — Google Trends (pytrends)

```python
# Install: pip install pytrends
# Degrades gracefully if not installed — skip this source and continue

from pytrends.request import TrendReq

# hl / tz / pn — под язык и страну ТВОЕЙ аудитории (tz в минутах от UTC)
pt = TrendReq(hl="ru", tz=180)

# Daily trending searches
trending_ru = pt.trending_searches(pn="russia")

# Real-time trending (last 24h) — more volatile, higher signal
realtime_ru = pt.realtime_trending_searches(pn="RU")

# Score: linear decay 1.0 → 0.05 over ranks 0-19
topics = []
for i, title in enumerate(trending_ru[0].head(20)):
    score = max(0.05, 1.0 - (i * 0.05))   # rank 0 = 1.0, rank 19 = 0.05
    topics.append({"title": title, "source": "google_trends", "score": score})
```

> If pytrends raises `429 Too Many Requests`: add `requests_args={"timeout": 20}` and retry once after 30s.

### Source D — Channel History (youtube-analytics skill)

```bash
# Что уже сработало на СВОЁМ канале — чтобы не повторять недавние темы.
# Через навык youtube-analytics:
# "Покажи топ-10 видео моего канала по просмотрам за последние 90 дней"
```

Collect: top performing topics (S/A-tier confirmation), recently posted topics (exclude from candidates).

### TopicCandidate Schema

Each source produces candidates in this normalized shape — общая форма для всех источников,
чтобы дедупликация и скоринг работали независимо от того, откуда тема пришла:

```python
@dataclass
class TopicCandidate:
    title: str
    source: str          # "reddit/r/technology", "google_trends", "tiktok_trending", etc.
    trending_score: float  # normalized 0.0–1.0
    summary: str = ""
    url: str = ""
    metadata: dict = {}  # platform-specific raw data
```

Deduplication: fuzzy match on `title.lower().strip()[:50]` — keep highest score when collision.

---

## Step 2: Viral Detector Algorithm

The core signal: **z-score of engagement rate vs channel baseline**.

### Formula

```
For each video/post in competitor's feed:

  ER(video)  = (likes + comments + shares) / views
  ER_avg     = mean(ER) across channel's last 20 posts
  ER_std     = std(ER)  across channel's last 20 posts
  viral_score = (ER - ER_avg) / ER_std   # z-score

Classification:
  viral_score > 3.0  →  VIRAL    (statistical anomaly — 1 in 741 chance by random)
  viral_score > 2.0  →  HOT      (top 2.3% of content)
  viral_score > 1.0  →  ABOVE_AVG
  else               →  NORMAL
```

### Per-Platform Implementation

| Platform | Endpoint | Fields | Notes |
|----------|----------|--------|-------|
| TikTok | `/v3/tiktok/profile/videos?username=COMPETITOR` | `diggCount`, `commentCount`, `shareCount`, `playCount` | `ER = (digg+comment+share)/play` |
| Instagram | `/v2/instagram/user/posts?username=COMPETITOR` | `like_count`, `comment_count`, `view_count` | Reels: use `/v1/instagram/user/reels` |
| YouTube | `youtube-analytics` skill | views, likes, comments from channel data | Use channel's own stats for baseline |

```bash
# Ключ из окружения; если держишь свой .credentials.master.env — подхвати его:
[ -f ~/.claude/.credentials.master.env ] && source ~/.claude/.credentials.master.env
API="https://api.scrapecreators.com"
H="x-api-key: $SCRAPECREATORS_API_KEY"

# Fetch competitor videos for viral scoring
curl -s "$API/v3/tiktok/profile/videos?username=COMPETITOR_HANDLE" -H "$H" > /tmp/te_comp_tt.json
curl -s "$API/v2/instagram/user/posts?username=COMPETITOR_HANDLE"  -H "$H" > /tmp/te_comp_ig.json
```

```python
import json, statistics

with open("/tmp/te_comp_tt.json") as f:
    data = json.load(f)

videos = data.get("videos", [])

# Build baseline from last 20 posts
er_list = []
for v in videos[:20]:
    views = v.get("playCount", 1)
    eng   = v.get("diggCount", 0) + v.get("commentCount", 0) + v.get("shareCount", 0)
    er_list.append(eng / views if views > 0 else 0)

er_avg = statistics.mean(er_list) if er_list else 0
er_std = statistics.stdev(er_list) if len(er_list) > 1 else 1e-9

results = []
for v in videos:
    views = v.get("playCount", 1)
    eng   = v.get("diggCount", 0) + v.get("commentCount", 0) + v.get("shareCount", 0)
    er    = eng / views if views > 0 else 0
    z     = (er - er_avg) / er_std if er_std > 0 else 0

    label = "VIRAL" if z > 3 else "HOT" if z > 2 else "ABOVE_AVG" if z > 1 else "NORMAL"
    results.append({**v, "viral_score": round(z, 2), "label": label, "er": round(er, 4)})

viral_hits = [r for r in results if r["label"] in ("VIRAL", "HOT")]
```

Prioritize `VIRAL` and `HOT` candidates for Step 3 transcript analysis.

---

## Step 3: Competitor Transcript Analysis

For each `VIRAL` or `HOT` video: fetch transcript → Claude breakdown.

### Fetch Transcript

```bash
# TikTok
curl -s "$API/v1/tiktok/video/transcript?url=TIKTOK_VIDEO_URL" -H "$H" > /tmp/te_transcript_tt.json

# Instagram Reel
curl -s "$API/v2/instagram/media/transcript?url=REEL_URL" -H "$H" > /tmp/te_transcript_ig.json

# YouTube — use youtube-transcript skill:
# "Get transcript for youtube.com/watch?v=VIDEO_ID"
```

### Claude Analysis Prompt

```
Analyze this viral video transcript. Break it down into:
1. HOOK (first 1-3 seconds): What technique?
   Options: shocking_fact | question | contradiction | name_drop | threat | pattern_interrupt
2. BODY (middle): Key message, pacing, facts used, density
3. CTA/ENDING: How does it end?
   Options: abrupt | loop | call_to_action | cliffhanger | resolution
4. WHY VIRAL: What made this resonate?
   Options: emotion, timing, controversy, trend_riding, unique_info, personality

Transcript:
---
{transcript}
---

Output ONLY valid JSON:
{
  "hook_type": "...",
  "hook_text": "first 1-2 sentences",
  "body_summary": "...",
  "ending_type": "...",
  "virality_factors": ["emotion", "timing"],
  "replicable_elements": ["specific element 1", "specific element 2"],
  "suggested_adaptation": "Как адаптировать эту формулу под мой канал и нишу"
}
```

Collect `replicable_elements` and `hook_type` distributions across all analyzed videos.
If 3+ viral videos share the same `hook_type` → it's a pattern, not a fluke.

---

## Step 4: Auto-Pick Best Topic

Combine all candidates from Steps 1-2 with transcript insights from Step 3.

### Scoring Prompt

Подставь профиль своего канала из блока «Профиль канала» выше — три поля в квадратных скобках.

```
You are selecting the single best topic for a viral YouTube Short on the channel
[ниша, язык аудитории, формат и длина — из профиля канала].

Channel's proven S-tier topics: [3-5 тем, которые на этом канале взрывались]
Channel's proven A-tier topics: [3-5 тем, которые стабильно дают хороший результат]

Score each topic 1-10 on these dimensions:
- visual_potential:  Can this be shown visually in 15-25 seconds?
- broad_appeal:      Will this interest a wide Russian-speaking audience (not just niche)?
- timeliness:        Is this breaking/trending RIGHT NOW (not last week)?
- controversy:       Does this provoke strong opinions, debate, or surprise?
- channel_fit:       Does this match S/A-tier topics above?

Topics with viral signals:
{topics_with_viral_scores}

Competitor hook patterns detected (use these to inspire the hook):
{hook_pattern_summary}

Output ONLY valid JSON:
{
  "best_topic": "exact topic title",
  "composite_score": 8.4,
  "dimension_scores": {
    "visual_potential": 9,
    "broad_appeal": 8,
    "timeliness": 9,
    "controversy": 7,
    "channel_fit": 9
  },
  "reasoning": "2-3 sentence explanation",
  "hook_suggestion": "First 1-2 sentences for the Short",
  "hook_type": "shocking_fact",
  "reference_videos": ["url1", "url2"],
  "avoid_topics": ["topic that was just posted", "topic that underperforms on channel"]
}
```

---

## Output: trend_brief.json

Full pipeline produces a single structured brief:

```json
{
  "generated_at": "2026-03-28T10:00:00Z",
  "topic": "DeepSeek V4 launched — beats GPT-5 at 1/100th the cost",
  "virality_score": 4.2,
  "google_trend_score": 0.85,
  "sources": ["reddit/r/technology", "tiktok_trending", "google_trends", "x_trending"],
  "hook_examples": [
    {
      "type": "shocking_fact",
      "text": "DeepSeek V4 обошёл GPT-5 и стоил в 100 раз дешевле"
    },
    {
      "type": "question",
      "text": "Почему весь мир говорит о DeepSeek V4?"
    }
  ],
  "competitor_hooks": [
    {
      "creator": "@ai_news_ru",
      "platform": "tiktok",
      "hook_type": "shocking_fact",
      "hook_text": "...",
      "views": 500000,
      "viral_label": "VIRAL",
      "viral_score": 3.8
    }
  ],
  "hook_pattern": "shocking_fact (seen in 4/5 viral videos this week)",
  "reference_videos": [
    "https://www.tiktok.com/@ai_news_ru/video/...",
    "https://youtube.com/shorts/..."
  ],
  "script_template": "hook-value-abrupt",
  "recommended_duration": "18-22s",
  "recommended_format": "short",
  "channel_fit_tier": "S",
  "post_timing": "Friday 06:00-08:00 (время основной аудитории)"
}
```

Save to `/tmp/trend_brief.json` and print a human-readable summary.

---

## Integration with video-factory

trend_brief.json feeds directly into the video production pipeline:

| Phase | Skill | What it uses from trend_brief.json |
|-------|-------|-------------------------------------|
| Phase 1: Topic | trend-engine (this skill) | Produces `trend_brief.json` |
| Phase 2: Script | shorts-pipeline | `topic`, `hook_examples`, `hook_type`, `script_template` |
| Phase 3: Visuals | video-generation + nano-banana-pro | `topic`, `recommended_duration` |
| Phase 4: Audio | elevenlabs | `hook_examples[0].text` → voiceover |
| Phase 5: Publish | свой загрузчик на YouTube Data API v3 (`videos.insert`) | `post_timing`, `channel_fit_tier` for title formula |

Handoff command:
```
"Use trend_brief.json at /tmp/trend_brief.json to create a YouTube Short with the shorts-pipeline skill"
```

---

## Watchlist Mode — Daily Competitor Monitoring

Configure a list of competitors to watch. Run daily to catch viral content early.

### Setup watchlist

Create `/tmp/te_watchlist.json`:
```json
{
  "tiktok": ["ai_explained", "futuretools", "developersdigest"],
  "instagram": ["ai_news_daily", "techinsider"],
  "check_interval": "daily",
  "alert_threshold": 2.0
}
```

### Daily digest command

```bash
# Run Viral Detector across all watchlist accounts
# Outputs only VIRAL and HOT content from last 24h

# Ключ из окружения; если держишь свой .credentials.master.env — подхвати его:
[ -f ~/.claude/.credentials.master.env ] && source ~/.claude/.credentials.master.env
API="https://api.scrapecreators.com"
H="x-api-key: $SCRAPECREATORS_API_KEY"

WATCHLIST=("ai_explained" "futuretools" "developersdigest")
for creator in "${WATCHLIST[@]}"; do
  curl -s "$API/v3/tiktok/profile/videos?username=$creator" -H "$H" > "/tmp/te_watch_${creator}.json" &
done
wait

# Then: apply Viral Detector formula to each, collect VIRAL+HOT, generate digest
```

Output format: markdown table of viral hits with topic, platform, creator, views, hook type.

Integrate with `last30days` watchlist feature for a unified daily brief.

---

## Quick Mode (Skip Transcript Analysis)

When speed matters more than depth — omit Step 3:

```
Steps: Gather → Score → Pick  (no transcript analysis)
Time: ~60 seconds
Use when: you need a topic fast, not a full formula breakdown
```

Trigger: "быстро найди тренд" / "quick trend" / "что снимать, быстро"

---

## Credit Budget

| Operation | ScrapeCreators Credits |
|-----------|----------------------|
| TikTok trend snapshot (4 endpoints) | 4 |
| 1 competitor videos fetch | 1 |
| 1 video transcript | 1 |
| Instagram competitor (posts + reels) | 2 |
| Full pipeline (3 competitors, 5 transcripts) | ~15-20 |
| Watchlist mode (5 creators daily) | ~5-10 |

---

## Dependencies

| Dependency | Required | Install | Fallback |
|------------|----------|---------|----------|
| `pytrends` | Optional | `pip install pytrends` | Skip Google Trends source, continue with others |
| `SCRAPECREATORS_API_KEY` | Required for TikTok/Instagram (платный, 1 кредит/запрос) | scrapecreators.com → env-переменная | Skip TikTok sources |
| `YOUTUBE_API_KEY` | Optional | Google Cloud Console → YouTube Data API v3 → env-переменная | Use youtube-analytics skill manually |
| `python 3.10+` | Required | — | — |
| `last30days` skill | Required | `~/.claude/skills/last30days/` | Run manually, skip social sweep |

Skill degrades gracefully: if a source fails, log it and continue with remaining sources.
At minimum, Google Trends + TikTok trending feed produce a usable result.

---

## Related Skills

| Skill | Role in Workflow |
|-------|-----------------|
| `last30days` | Multi-platform social sweep (Step 1 Source A) |
| `tiktok-intel` | TikTok/Instagram trending data + transcripts (Steps 1-3) |
| `youtube-analytics` | Channel history + YouTube competitor data (Steps 1-2) |
| `youtube-transcript` | YouTube video transcripts for Step 3 |
| `shorts-pipeline` | Consumes trend_brief.json for script generation |
| `video-generation` | Full video production after topic is selected |
