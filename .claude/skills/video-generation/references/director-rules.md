# Director rules — anti-cliché tone + audience cue

Эмпирические правила для **scene-prompt director'а** (LLM, который превращает скрипт/пост → список prompts для Veo / Sora / Seedance). Спасают от двух самых частых багов AI-видео:

1. **«Угрюмый человек на рваном диване»** — LLM по дефолту берёт самый литеральный визуал (post про выгорание → измученное лицо в кадре).
2. **«Темнокожий герой для русского контента»** — Veo / Sora / Seedance дефолтят к глобально-нейтральному кастингу. Для RU-аудитории это читается мимо.

## §1 — Anti-cliché tone rules (вшить в system prompt director'а)

```
STYLE RULES (critical):

- Be SUGGESTIVE, not LITERAL. Show mood through lighting, framing,
  weather, small objects — NOT through an actor's pained face or shabby
  surroundings.

- Avoid on-the-nose visuals. FORBIDDEN list:
    * 'ragged sofa', 'cluttered desk with empty coffee cups'
    * 'glazed exhausted eyes', 'pained facial close-up'
    * 'tear running down cheek', 'hand over forehead'
    * 'crumpled paper scattered around'
  These read as parody, not editorial.

- VARY the scenes:
    * one may show a person
    * another a detail (hands, a window, a clock, a steaming cup)
    * another a pure environment without people
  Don't put the same protagonist in every scene looking sad.

- Tasteful modern look: editorial photography, not stock-footage cliché.
  Clean frames, thoughtful composition, warm or muted palette
  — NOT always grim blue.

- Arc loosely follows the post: problem → nuance → resolution.
  The LAST scene usually has a lighter or more hopeful tone than the first.

- No text overlays, no captions in frame, no logos.
```

Вставлять как часть `system` промпта **перед** «Return STRICT JSON: {scenes: [str, ...]}».

## §2 — Audience cue (региональная этника по языку)

Авто-детект языка по доле кириллических символов:

```python
def _looks_russian(text: str) -> bool:
    total = sum(1 for c in text if c.isalpha())
    if total < 20:
        return False
    cyr = sum(1 for c in text if "А" <= c <= "я" or c in "ёЁ")
    return cyr / total > 0.2
```

Затем в director prompt подмешать соответствующий cue:

```python
AUDIENCE_CUE = {
    "ru": (
        "Target audience: Russian-speaking. If people appear, "
        "Eastern European / Slavic features (light/olive skin, varied hair). "
        "Settings look like a modern Russian / Eastern European apartment, "
        "office, or city street — NOT American suburbs, NOT African or "
        "South Asian backdrops."
    ),
    "en": (
        "Target audience: global English-speaking. "
        "Diverse but coherent casting across scenes."
    ),
    "es": "Target audience: Spanish-speaking. Latin/Iberian casting context.",
    # ... добавить по мере необходимости
}
```

Без явного cue Veo по умолчанию даёт «globally neutral» кастинг, который для RU-постов читается чужеродно.

## §3 — Self-test promo (когда применять)

| Бриф | Применить cue + tone rules? |
|------|---|
| RU-пост про выгорание / отношения / финансы | **Обязательно**. Без правил — depressive cliché + не-славянские лица. |
| Cinematic 21:9 trailer (YourFirstName narration) | tone rules — да; audience cue — RU. |
| Книжный буктрейлер по русской книге | tone rules — да; audience cue — RU. |
| Global product launch на EN | tone rules — да; audience cue — `en` (или skip). |
| Личные истории пользователя | tone rules — да; audience cue — RU. |
| Abstract motion design без людей | tone rules — частично (forbidden list не нужен); audience cue — skip. |

## §4 — Self-check после генерации storyboard

После того как director вернул `scenes: [...]`, прогнать каждый prompt через quick regex-check:

```python
FORBIDDEN_TOKENS = [
    "ragged sofa", "exhausted glazed eyes", "cluttered desk",
    "tear running", "pained face", "crumpled paper",
    "hand over forehead", "sobbing", "head in hands",
]

def lint_scene(prompt: str) -> list[str]:
    return [t for t in FORBIDDEN_TOKENS if t.lower() in prompt.lower()]
```

Если что-то нашлось — re-run director с `style_notes="user wants softer, no on-the-nose distress; remove [bad tokens]"`.

## §5 — Stage 2 approval (когда юзер сам ревьюит раскадровку)

Если режим pipeline'а — staged (см. SKILL.md §Phase 5 staged), показывать storyboard юзеру **с номерами**:

```
Раскадровка — 4 сцены:

1. Поздний вечер в современном офисе: мягкий свет мониторов,
   на стеклянной перегородке отражения чатов, камера статична.

2. Крупный план рук над клавиатурой: курсор мигает в пустом
   редакторе, телефон экраном вниз, одинокая лампа.

3. Тихая кухня в современной квартире: человек у окна,
   мокрый асфальт за стеклом, без включённых уведомлений.

4. Утро в минималистичном рабочем уголке: закрытый ноутбук,
   чашка чая, теплое солнце, ощущение восстановленных границ.

Утверждаешь?
```

Не дампи markdown списком без номеров — юзеру невозможно сказать «третью сцену помягче». С номерами правка — `style_notes="третью сделай без человека вообще, только детали"`.
