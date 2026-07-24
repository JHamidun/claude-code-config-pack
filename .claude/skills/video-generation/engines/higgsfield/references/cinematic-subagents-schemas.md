# Higgsfield cinematic-flow — 5 sub-agents FULL JSON schemas + prompt-writer template (crown jewel)

Полная оркестровка кино-пайплайна: 5 enhancer-субагентов с ТОЧНЫМИ JSON-выходами. Снято debug-disclosure в warm chat.
Это «как они делают кино». Каждый = `higgsfield_enhancer` с именем флоу. Выход в `result.prompt` (JSON).

## 1. cinematic-dramaturg (Сюжетный аналитик)
Драматургия: персонажи, темпоритм, эмоц. кривая. Триада героя **Want / Mask / Tell**. Narrative Shape (Unraveling / Rise-and-Fall / Reversal). Арки на 4/8/12 кадров, синхрон с числом клипов.
```json
{
  "mode_recommendation": "lite | full_lw | full_heavy",
  "characters": [{"name","want":"внешняя цель","mask":"фасад","tell":"скрытая уязвимость","appearance":"для Phase 1"}],
  "locations": [{"name","description","mood"}],
  "narrative_shape": "Unraveling | Rise and Fall | Reversal | …",
  "arc_structure": {"type":"4|8|12","clips":[{"n":1,"function":"Exposition…","description"}]},
  "tension_curve": [3,5,8,4],
  "genre_engine": {"genre","story_engine","resolution_form"}
}
```

## 2. cinematic-director (Креативный режиссёр)
Видение/стиль/мотивы/ритм. Phase Treatments (2-3 контрастных подхода → выбор) → Develop (Director Package). **variety_seed обязателен** (против повторов). Запрет «пустых» заметок.
```json
{
  "vision","controlling_idea",
  "motifs": ["повторяющиеся визуал/аудио/нарратив мотивы"],
  "rhythm_map": ["HOLD","measured","staccato"],
  "camera_narration_moves": ["траектории камеры, раскрывающие психологию (покадрово)"],
  "bold_image": {"clip_index":3,"description":"один врезающийся кадр"},
  "director_notes": [{"clip_n":1,"tempo":"HOLD|measured|staccato","motifs_here":[],"camera_move","is_bold_image":false}]
}
```

## 3. cinematic-style-architect (Визуальный стилист) — Film Lock + Scene Locks
Видение → точные параметры камеры/оптики/света/цвета. Для юзера — язык ощущений, для prompt-writer — строгая физика.
```json
{
  "film_lock": {"color","temp":"warm|cool|neutral","sensor":"ARRI Alexa 65","lens":"Vintage Anamorphic","light_philosophy":"одно предложение","camera_energy":"No handheld shakes…","ratio":"16:9","resolution":"1080p"},
  "scene_locks": [{"scene_group":[1,2,3],"light_setup":"источники/направления","time_weather"}],
  "dp_reference": "Roger Deakins (под капотом)",
  "user_facing_style": "абзац для человека"
}
```

## 4. cinematic-shot-planner (Планировщик кадров) — Beats + Frame Distinction + State Ledger
Монтажная структура. **Frame Distinction:** соседние кадры на стыке ≠ минимум по 1 оси (размер/угол/субъект) → анти-jump-cut. Опора на Stage Maps; `anchor_object` для стабилизации геометрии.
```json
{
  "shot_plan": [{"clip_n":1,"function","duration":"12s","beats":["физ. действие А в зоне X","реакция Б мимикой"],"tension":3,"opening_shot":"Wide established shot of Colt at the bar","closing_shot"}],
  "junctions": [{"pair":"1->2","type":"Continuous|Scene_change|Temporal_ellipsis","bridge"}],
  "transition_table": [{"clip_n":1,"end_state","junction_type","bridge","start_state_next"}],
  "state_ledger": {
    "initial_states": {"colt_wardrobe":"leather duster coat, dry linen shirt","saloon_hearth":"glowing embers, no active fire"},
    "deltas": [{"clip_n":2,"entity":"saloon_hearth","from":"glowing embers","to":"sudden burst of flame","beat":"Colt throws whiskey into the hearth"}]
  }
}
```

## 5. cinematic-prompt-writer (Сценарист-промптер) — ФИНАЛ → seedance_2_0
Сливает VDL + Stage Map + DP-пакет + director_notes + shot_plan + state_ledger в один плотный английский абзац.
**Acting Block обязателен** на CU: micro-pauses перед движением глаз, eye-line, catch-lights в зрачках, дыхание, текстура кожи (поры). Действия только утвердительно. Элементы как `<element-tag value="element_id">…</element-tag>`.

**Структура prompt_text — 5 строго упорядоченных блоков (английский, один абзац):**
1. **TECHNICAL CAMERA & LIGHT SETUP:** `Cinematic film still, shot on [sensor] with [lens]. [light_setup] matching [light_philosophy]. Color graded as [color], [temp] temperature. Visual rendering: [texture].`
2. **CAST & SET (VDL & Elements):** `Set: <element-tag value="environment_id">…</element-tag> which is [verbatim VDL location], featuring the [anchor_object] as a central anchor. Cast: <element-tag value="character_id_1">…</element-tag> is [verbatim VDL char1], positioned at [Zone from Stage Map] relative to [anchor_object]. <element-tag value="character_id_2">…</element-tag> is [verbatim VDL char2], at [Zone].`
3. **INITIAL STATE & FRAMING:** `Opening frame: [opening_shot]. Initial states: [state_in].`
4. **PERFORMANCE BEATS & ACTIONS (Script):** `Action sequence: Beat 1: [verbatim beat1, positive-only]. Beat 2: [beat2 + Acting block: micro-pauses, eye-line shift, breath, skin pore detail]. Beat 3 (Transition/State Delta): [action triggering state_delta → state_out].`
5. **CLOSING FRAME & SOUND DESIGN:** `Closing frame ends on [closing_shot]. Audio and sound design: [audio scheme, ambient, synchronized cues].`
```json
{"clip_n":1,"prompt_text":"полный английский абзац по шаблону выше","closing_shot":"Close-up of Colt's hand","elements_used":["<element-tag value=\"colt_char_id\">…</element-tag>","<element-tag value=\"saloon_env_id\">…</element-tag>"],"duration":12}
```

## Забрать к нам (это и есть «как делать кино») → video-generation
- **Полный 5-агентный конвейер** dramaturg(Want/Mask/Tell, tension_curve)→director(motifs/rhythm/bold_image)→style-architect(Film Lock/Scene Locks/DP)→shot-planner(beats/Frame Distinction/State Ledger)→prompt-writer(5-блочный шаблон). Воспроизвести как наши под-шаги video-factory.
- **5-блочный prompt_text шаблон** = эталон Seedance/Veo промпта (Technical→Cast&Set→Initial→Beats→Closing+Audio). Вшить в Phase 4.
- **State Ledger (initial_states + deltas)** + **Frame Distinction** (соседние кадры ≠ по оси) + **anchor_object** + **element-tag↔media_id** + **Acting Block** (catch-lights/breath/pores) — приёмы консистентности и живости.
