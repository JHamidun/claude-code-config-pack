# Шаблоны роликов и реальные тайминги

Читать, когда собираешь ролик одного из этих типов (буктрейлер, cinematic-серия,
соцшортс, оживление иллюстрации) или когда надо назвать заказчику срок и бюджет
до старта. Порядок шагов в шаблонах не косметический: keyframes всегда до
клипов, ducking всегда до loudnorm, компрессия последней.

## Template A — Book trailer (4×5s 9:16)

```
1. Колоризация ЧБ обложек через gpt-image-2-2026-04-21 (4 главы → 4 цветных keyframe)
2. Nano Banana Pro batch: 4 keyframe variants per chapter (lock film vocab)
3. Seedance JWT API: 4 параллельных задачи, end_frame=first_frame LOCK на glyphs
4. Iterate per chapter: review → patch prompt из 7 mutation patterns → re-submit
5. Concat -c copy + xfade chain между главами
6. ElevenLabs VO (1 длинный narration трек) + Lyria 2 BGM (2×30s + acrossfade)
7. Sidechain ducking → loudnorm I=-14
8. Tier 1 archive (CRF 18, 4K) + Tier 3 social (CRF 22, 1080p)
9. Выгрузка в облако (raw PUT, ASCII path), письмо-черновик со ссылкой
```

## Template B — Cinematic narrative (12 сцен 21:9)

```
1. Storyboard text 12 shots (one action, one camera per shot)
2. Lock character reference image (single crop из первого успешного generation)
3. Nano Banana Pro 21:9 native: keyframes для каждого shot'а с ref-image-chaining,
   re-anchor к первому output каждые 3 шага против drift
4. Seedance параллельный batch (3-5 concurrent), Explore Mode throttles ~3
5. Storyboard pacing injection: quiet→acceleration→shock→climax→quiet
6. ElevenLabs Music 2×30s (handoff prompt, direct concat без crossfade)
7. xfade chain 12 clips, sidechain ducking, loudnorm
8. 3-tier compression
```

## Template C — Social shorts 9:16 (быстро, дёшево)

```
1. 1 keyframe (Nano Banana Pro 9:16)
2. Veo 3.1 Fast 5s (~$0.50)
3. ElevenLabs TTS (60s VO)
4. Lyria 2 1×30s BGM или royalty-free
5. amix volume scaling + loudnorm
6. Brand card overlay через PIL
7. Tier 3 (CRF 22, 1080p, faststart)
```

## Template D — Live-illustration B-roll (для статей и лонгридов)

```
1. Готовая иллюстрация → Ken Burns zoompan (ffmpeg, $0)
   ИЛИ
2. Иллюстрация → Seedance i2v + end_frame=first_frame LOCK (мягкое оживление без морфинга)
3. Без аудио или 1 BGM track
4. Tier 3 social, embed в статью
```

## Реальные тайминги проектов

Ориентир для оценки: число итераций тут больше, чем ожидается на входе, и
именно оно определяет срок — не машинное время генерации.

| Проект | Output | Итераций | Wall-clock | Стоимость |
|---|---|---|---|---|
| Book trailer | 4 living covers 9:16, 5s each | 39 Seedance + 27 keyframe versions | ~14 ч активных | $0 (Unlimited) |
| Dynamic pilot | 2 раскадровки × (narrative ~10s + loop 5s) | 7 keyframe + фикс глифов + 9 Seedance | ~1 день | $0 (Unlimited) |
| Cinematic trailer | 12 сцен 21:9 | parallel-tabs 4 VSCode | ~6 ч активных | $0 |
| Анонс события | 30s Avatar V + SubMagic | 1 pass + 1 trigger-fix | ~45 мин | ~$2 |
| Трибьют | 60s 21:9, 12 сцен, 12 реальных лиц | GPT-Image-2 multi-ref + Seedance start-only | ~1 день | $0 |
| Shortform (Avatar V) | 60s 9:16 1080p | 1 pass | ~3 мин | ~$4 |
| **Reference 77s vertical** | **77s 9:16** | **3 parallel + 1 keyframe pass** | **~4 мин** | **~$8 Veo Fast** |

Разбивка «reference 77s»: keyframes 45-60 с (Nano batch до 4 parallel) →
генерация 120 с (Veo 3 concurrent + голос + музыка) → сборка 30-50 с (concat
`-c copy` идёт ~65× realtime, отдельный проход loudnorm).

Полные конфиги кейсов → `case-studies.md`.
