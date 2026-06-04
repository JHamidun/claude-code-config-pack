---
name: video-generation
description: "Full-cycle AI video production: Veo 3.1 Fast/Sora generation → ElevenLabs voiceover → music → subtitles → FFmpeg assembly"
type: actionable
---

# Video Generation Skill

Full-cycle AI video production: 6-phase workflow from brief to finished video with narration, music, and subtitles.

## Workflow Overview

0. **Phase 0: Intake** -- Interactive questionnaire, user confirms full spec → Production Plan
1. **Phase 1: Initial** -- Gather creative requirements, choose video model, STOP for user confirmation
2. **Phase 2: Global Definitions** -- Define style, characters, voices, BGM (text only, no images)
3. **Phase 3: Clip Planning** -- Segment into clips, plan each clip, determine reference image needs
4. **Phase 4: Reference Images** -- Generate reference images (MANDATORY before Phase 5)
5. **Phase 5: Execution** -- Generate keyframes, videos, audio per clip
6. **Phase 6: Assembly** -- Concat clips → mix narration → overlay music → burn subtitles

## When to Use

- User asks to create/generate a video
- User needs help with video prompts
- User wants cinematic AI video content
- User mentions Veo, Sora, Runway, Pika, Kling

## Critical Rules (MUST Follow)

1. **[PHASE 1 STOP]** MUST ask questions to gather information. DO NOT assume or guess missing details. Never proceed without explicit user confirmation.
2. **[DETAILED VIDEO PROMPT]** Video prompts must include detailed transition_description (2-4 sentences). One-line prompts are insufficient.
3. **[KEYFRAME DIFFERENCE]** Last keyframe must show interpolatable change from first keyframe: subject position/pose, state change, or composition change. Subtle-only changes (lighting, background) while subject stays static cause unnatural video motion.
4. **[PHASE 4 MANDATORY]** MUST generate reference images before keyframes. Never skip Phase 4.
5. **[ASPECT RATIO]** ALL keyframes must use 16:9 or 9:16, upright (not rotated). Never 1:1.
6. **[NO TTS FOR ON-SCREEN]** Never use TTS for on-screen dialogue or singing. Video model generates audio with lip sync.
7. **[NARRATION CLIP BY CLIP]** Generate off-screen narration separately for each clip, not all at once.
8. **[AUDIO MIXING]** When combining audio tracks, preserve ALL tracks -- overlay, never replace. Narration must be clearly audible.

## Tools & Models Reference

### Video Generation Models

| Model | ID | Speed | Quality | When to Use |
|-------|-----|-------|---------|-------------|
| **Veo 3.1 Fast** ← DEFAULT | `veo-3.0-fast-generate-001` | ~60s | High | Default — best speed/quality ratio |
| Veo 3.1 (full) | `veo-3.0-generate-001` | ~140s | Highest | When max quality needed, paid |
| Sora (OpenAI) | `sora-1.0-turbo` | ~90s | High | Alternative when Veo unavailable |

**Default:** always use Veo 3.1 Fast unless user explicitly requests higher quality.

### Other Tools

| Tool | Use When |
|------|----------|
| Skill `nano-banana-pro` | Create keyframe images (Gemini Flash Image / Pro) |
| Skill `elevenlabs` | Text-to-speech for off-screen narration |
| `video_editor.py concat` | Assemble clips in Phase 6 |
| FFmpeg subtitles filter | Burn subtitles in Phase 6 |

---

## Production Manifest (fill in as phases complete)

> Maintain this manifest throughout the session. Update after each phase. Show current status when resuming.

```text
PRODUCTION MANIFEST
===================
Title: [project name]
Phase: [1-6] / Status: [IN PROGRESS / DONE]

-- PHASE 1 (Brief) --
Video model: [ ] Veo 3.1 Fast  [ ] Veo 3.1  [ ] Sora
Aspect ratio: [ ] 16:9  [ ] 9:16
Duration: ___s  |  Clips planned: ___
Platform: ___  |  Language: ___
Subtitles: [ ] None  [ ] FFmpeg SRT  [ ] SubtitleService (style: ___)
BGM: [ ] Embedded  [ ] Separate royalty-free  [ ] None

-- PHASE 2 (Global Definitions) --
Visual style: ___
Characters/elements: ___
Narrator voice (ElevenLabs ID): ___

-- PHASE 3 (Clip Plan) --
Total clips: ___
[ ] Clip plan table complete
[ ] Reference image list complete

-- PHASE 4 (Reference Images) --
Generated: [list file names]

-- PHASE 5 (Execution) --
Clips done: ___ / ___  (list: clip_01.mp4, clip_02.mp4, ...)
Narration done: ___ / ___ clips
BGM track: ___

-- PHASE 6 (Assembly) --
[ ] Clips concatenated → assembled_raw.mp4
[ ] Audio mixed → assembled_audio.mp4
[ ] Subtitles added → final.mp4
FINAL OUTPUT: ___
```

---

## Phase 0: Intake (ALWAYS START HERE)

> **On every skill invocation, begin with this phase.** Do not skip to Phase 1.

### How to Run Intake

Present the questionnaire below as a **numbered list**. User can answer inline ("1. Рекламный ролик, 2. Да, 3. ...") or selectively. After receiving answers, summarize as a **Production Plan** and ask for confirmation before proceeding.

---

### Intake Questionnaire

Ask ALL questions in one message. Group them by section for readability.

### РАЗДЕЛ 1 — О ролике

1. Что это за ролик? *(реклама, explainer, соцсети, арт, клип, корпоративное видео...)*
2. Для какой платформы? *(YouTube, Instagram Reels, TikTok, презентация, сайт...)*
3. Целевая длина? *(10 сек / 30 сек / 60 сек / дольше)*
4. Ориентация? *(горизонтальная 16:9 / вертикальная 9:16)*
5. Основная идея или сообщение? *(1-2 предложения)*

### РАЗДЕЛ 2 — Аудио

1. Нужен ли закадровый голос / нарратор? *(да / нет / есть готовый файл)*
2. Если да — голос выделить поверх музыки и приглушить остальное? *(да / нет)*
3. Нужна ли фоновая музыка (BGM)? *(да / нет / есть готовый трек)*
4. Если BGM — приглушать музыку в момент речи? *(да — ducking / нет — одинаково)*
5. Звук из сгенерированных клипов (ambient, эффекты) — сохранить или убрать? *(сохранить / убрать / оставить тихим фоном)*

### РАЗДЕЛ 3 — Брендинг

1. Нужен ли логотип / watermark в ролике? *(да / нет)*
2. Если да — где и когда? *(угол экрана постоянно / в начале / в конце / fade-in-out)*
3. Фирменные цвета или палитра, которую обязательно соблюдать? *(да — укажи / нет)*
4. Нужна ли брендированная концовка (outro)? *(да / нет)*

### РАЗДЕЛ 4 — Субтитры и текст

1. Нужны субтитры? *(нет / FFmpeg простые / SubtitleService стилизованные)*
2. Если субтитры — стиль? *(minimal / hormozi / mrbeast / karaoke / gradient / neon)*
3. Нужны заголовки / lower thirds / текстовые оверлеи прямо в видео? *(да / нет)*

### РАЗДЕЛ 5 — Технические предпочтения

1. Модель генерации? *(Veo 3.1 Fast — default / Veo 3.1 — max quality / Sora — альтернатива)*
2. Язык нарратора / субтитров? *(русский / английский / другой)*
3. Есть ли референсы — видео, изображения, стиль, который нравится? *(да — покажи / нет)*

---

### After Receiving Answers

**Step 1 — Summarize as Production Plan** in this format:

```text
PRODUCTION PLAN (Phase 0 Output)
=================================
Ролик: [тип и платформа]
Длина: [сек] | Ориентация: [16:9/9:16] | Модель: [Veo/Sora]
Язык: [язык]

АУДИО:
  Нарратор: [да/нет] | Выделить голос: [да/нет]
  BGM: [да/нет/трек] | Ducking: [да/нет]
  Ambient из клипов: [сохранить/убрать/фон]

БРЕНДИНГ:
  Логотип: [нет / угол / начало / конец]
  Фирменные цвета: [нет / да: ___]
  Outro: [да/нет]

СУБТИТРЫ: [нет / FFmpeg / SubtitleService style: ___]
Текстовые оверлеи: [да/нет]

ИДЕЯ: [1-2 предложения из ответа на вопрос 5]
РЕФЕРЕНСЫ: [есть/нет]
```

**Step 2 — Ask:** "Всё верно? Подтверди или скорректируй — и я сразу перейду к разработке плана."

**Step 3 — After user confirms:** proceed to Phase 1 without further questions. All answers from Phase 0 are final and carried into Production Manifest.

> **Phase 0 → Phase 1 handoff:** Transfer confirmed Production Plan into the Production Manifest. Audio settings, branding, subtitle style are LOCKED — do not re-ask in later phases.

---

## Phase 1: Initial

### Gather Information

Ask the user about ALL of these dimensions before proceeding:

| Dimension | Question | Default if Not Specified |
|-----------|----------|--------------------------|
| Purpose | What is this video for? (social media, ad, explainer, art, music video) | General creative |
| Narrative arc | What story or message? Beginning/middle/end? | Linear progression |
| Duration | Total target length? | 30-60 seconds |
| Aspect ratio | 16:9 (landscape) or 9:16 (vertical/mobile)? | 16:9 |
| Video model | Veo 3.1 Fast (default) / Veo 3.1 / Sora? | Veo 3.1 Fast |
| Visual style | Realistic, cinematic, animated, stylized? References? | Cinematic realistic |
| Reference materials | Any mood boards, existing videos, images to match? | None |
| Language | Primary language for dialogue/narration? | English |
| Recurring elements | Characters, objects, or settings that appear multiple times? | None |
| Dialogue/singing | Any on-screen speaking or singing? | None |
| Narration needs | Off-screen narrator? Tone and style? | None |
| Subtitles | None / FFmpeg burn-in / SubtitleService styled (for social)? | None |

### Five-Dimension Expert Framework

Analyze the user's request through five specialist lenses:

| Dimension | Expert Role | Focuses On |
|-----------|-------------|------------|
| Strategy & Audience | Strategist | Target audience, platform requirements, call-to-action, pacing for attention retention |
| Narrative & Structure | Screenwriter | Story beats, emotional arc, scene transitions, hook-development-payoff structure |
| Visual Style | Director + Art Director | Color palette, lighting approach, sub-genre aesthetics, visual coherence across clips |
| Shot Execution | Cinematographer | Camera angles, lens choices, movement types, depth of field, framing per clip |
| Sound Design | Sound Designer | Ambient layers, sound effects, music cues, dialogue treatment, audio transitions |

Synthesize all five dimensions into a coherent creative brief.

> **[MANDATORY STOP -- DO NOT PROCEED WITHOUT USER CONFIRMATION]**
> Present the creative brief to the user and wait for approval before moving to Phase 2.

**Phase 1 → Phase 2 handoff:** Update Production Manifest with confirmed: video model, aspect ratio, duration, platform, language, subtitle method, BGM approach. Then proceed directly to Phase 2 without asking.

---

## Phase 2: Global Definitions (Text Only)

This phase is text-only. No image generation yet.

### Visual Style Specification

Define four dimensions of the visual style:

| Dimension | Description | Example |
|-----------|-------------|---------|
| Sub-genre | Specific visual genre | Neo-noir cyberpunk |
| Rendering + Line | How surfaces and edges look | Photorealistic with sharp edges, subtle film grain |
| Color + Lighting | Palette and light treatment | Desaturated teal-orange, neon accents, high contrast rim lighting |
| Detail density | Level of environmental detail | High density -- visible textures on every surface, atmospheric particles |

**Example combined spec:**
> Neo-noir cyberpunk. Photorealistic rendering with sharp edges and subtle film grain. Desaturated teal-orange palette with neon accent colors, high-contrast rim lighting. High detail density with visible textures, rain particles, and atmospheric haze.

### Recurring Elements

For each character, object, or setting that appears in more than one clip:

| Field | Description | Example |
|-------|-------------|---------|
| unique_identifier | Short name used across all phases | "demo_video_1" |
| appearance | Physical description, age, build, skin, hair | Woman, mid-30s, athletic build, dark skin, short silver hair |
| outfit_description | Clothing, accessories, distinguishing marks | Black leather jacket, white t-shirt, silver chain necklace, small scar above left eyebrow |
| language | Language the character speaks (if dialogue) | English |
| mechanical_properties | For objects: material, size, how it moves | N/A for characters |

### Voice Profiles

**On-screen voices:** Derived from character definitions above. Video model handles lip sync.

**Off-screen narrator (if needed):**

| Field | Value |
|-------|-------|
| Name | (e.g., "Narrator_A") |
| Gender | Male / Female |
| Tone | (e.g., warm and authoritative) |
| Pace | (e.g., measured, ~140 words per minute) |
| Language | (e.g., English) |
| ElevenLabs voice | (specify voice name or ID from Skill `elevenlabs`) |

### BGM Source Decision

| Scenario | BGM Source | How |
|----------|-----------|-----|
| Music video / music is central | Embedded in video | Include music description in video prompt |
| Background mood music | Separate track | Search royalty-free library in Phase 5 |
| No music needed | None | Skip BGM |

**Phase 2 → Phase 3 handoff:** Update Manifest with visual style string, all recurring element IDs, narrator ElevenLabs voice ID, BGM decision. Immediately proceed to Phase 3 — no need to pause.

---

## Phase 3: Clip Planning

### Segmentation Rules

- Each clip: **4, 6, or 8 seconds** only
- Each clip: **one primary action, one scene**
- Total clips should sum to target duration from Phase 1
- Prefer 6-second clips as default; use 4s for quick cuts, 8s for slow/dramatic moments

### Per-Clip Specification

Fill out this table for EVERY clip:

| Field | Description | Required |
|-------|-------------|----------|
| clip_number | Sequential number (1, 2, 3...) | Yes |
| narrative_purpose | What this clip accomplishes in the story | Yes |
| pacing | slow / medium / fast | Yes |
| scene | Location and environment description | Yes |
| content_action | What happens -- the primary action | Yes |
| transition_description | **2-4 sentences** describing what the camera sees from start to end | **REQUIRED** |
| duration | 4, 6, or 8 seconds | Yes |
| camera_movement | Pan, track, dolly, crane, static, FPV, etc. | Yes |
| first_keyframe_framing | Shot type and composition for opening frame | Yes |
| first_keyframe_visible_content | Exactly what is visible in the opening frame | Yes |
| last_keyframe_framing | Shot type and composition for closing frame | Yes |
| last_keyframe_visible_content | Exactly what is visible in the closing frame | Yes |
| last_keyframe_edit_from_first | yes / no (see decision table below) | Yes |
| inter_clip_boundary | continuous / cut | Yes |
| first_keyframe_reuse | yes (from previous clip's last keyframe) / no | Yes |
| last_keyframe_required | yes / no | Yes |
| on_screen_dialogue | Dialogue text or "none" | Yes |
| sound_effects | Specific sounds for this clip | Yes |
| bgm_source | embedded / separate / none | Yes |
| bgm_cue | Music description for this clip's segment | If bgm_source != none |
| narration_cue | Narration text for this clip or "none" | Yes |

### Field Dependencies

- If `inter_clip_boundary = continuous` then the **next** clip's `first_keyframe_reuse = yes`
- If `first_keyframe_reuse = yes` then the **previous** clip must have `last_keyframe_required = yes`

### Keyframe Difference Requirement

The last keyframe MUST show an **interpolatable change** from the first keyframe. Valid change types:

1. **Position/Pose change** -- Subject has moved, turned, changed posture
2. **State change** -- Door opened, object picked up, expression changed
3. **Composition change** -- Camera has moved to reveal new framing

**Invalid changes** (cause unnatural motion): Only changing lighting, only changing background blur, only changing color grading while subject remains completely static.

### Decision: last_keyframe_edit_from_first

| Camera Movement | Edit from First? | Reason |
|----------------|-----------------|--------|
| Static shot | yes | Same viewpoint, edit subject changes |
| Small pan (< 30 degrees) | yes | Minor reframe, edit subject changes |
| Large pan (> 30 degrees) | no | Significantly different framing |
| Dolly / track | no | Different distance to subject |
| Crane / jib | no | Different height and angle |
| FPV / fly-through | no | Completely different viewpoint |

### transition_description Requirements

The transition_description MUST include:

1. **Subject appearance** -- What the subject looks like (reference Phase 2 definitions)
2. **Movement trajectory** -- How the subject or camera moves through the clip
3. **State changes** -- What transforms between start and end
4. **Existence statements** -- Confirm what is and is not present in frame

| Quality | Example |
|---------|---------|
| Insufficient | "Camera pans across the city." |
| Sufficient | "The camera begins on a medium shot of demo_video_1 standing at the rain-soaked intersection, her silver hair catching neon reflections. She turns left and walks toward the flickering bar sign. The camera tracks alongside her, revealing graffiti-covered walls and steam rising from a grate. By the end of the shot, she stands at the bar entrance, hand reaching for the door handle, face half-lit by the red neon glow." |

### Physical Consistency Check

Before finalizing clip plans, verify physical plausibility:

| Constraint | Check |
|-----------|-------|
| Human movement speed | Can the subject realistically perform the action in the clip duration? |
| Camera movement speed | Is the camera move physically achievable in the timeframe? |
| Object persistence | Do objects that should remain visible stay in frame? |
| Spatial continuity | Does the environment layout stay consistent between clips? |
| Lighting continuity | Does the lighting direction stay consistent within a scene? |

**Common Mistakes to Avoid:**

| Mistake | Fix |
|---------|-----|
| Character teleports between clips | Add transition clip or cut |
| Camera covers impossible distance | Reduce distance or increase clip duration |
| Object appears/disappears without explanation | Add action showing object enter/exit |
| Lighting flips direction mid-scene | Keep light source consistent |
| Character outfit changes without reason | Reference Phase 2 outfit_description |

### Reference Image Requirements

List all reference images needed before Phase 4:

| # | Element | Description | Used In Clips |
|---|---------|-------------|---------------|
| 1 | (e.g., demo_video_1 front) | Full front view, Phase 2 appearance + outfit | 1, 3, 5, 7 |
| 2 | (e.g., demo_video_1 side) | Side profile, same appearance | 2, 4 |
| 3 | (e.g., bar_exterior) | The bar entrance, Phase 2 scene description | 3, 4 |
| ... | ... | ... | ... |

**Phase 3 → Phase 4 handoff:** Update Manifest with total clip count and complete clip plan. Immediately start Phase 4 — generate all reference images before generating any clip.

---

## Phase 4: Reference Image Generation (MANDATORY)

**This phase MUST be completed before any keyframe generation in Phase 5.**

### Generation Order

#### Step 1: Primary reference (for each element)

- Use Skill `nano-banana-pro`
- No reference images as input (this IS the first reference)
- Include full visual style spec from Phase 2
- White or neutral background for character references
- Prompt must include: "no text, no watermarks, no borders, no UI elements"
- Generate one clean, well-lit, unambiguous reference per element

#### Step 2: Additional angles/poses (if needed)

- Use Skill `nano-banana-pro`
- USE the primary reference from Step 1 as reference input
- Request specific angle: side view, 3/4 view, back view
- Maintain all appearance details from primary reference

> **NEVER generate additional reference images without using the primary reference as input.**
> This ensures visual consistency across all references for the same element.

### Reference Naming Convention

Save references with clear names:
- `ref_demo_video_1_front.png`
- `ref_demo_video_1_side.png`
- `ref_bar_exterior.png`

**Phase 4 → Phase 5 handoff:** Update Manifest with list of all reference image file names. Immediately proceed to Phase 5 — generate all clips sequentially, clip_01.mp4 first.

---

## Phase 5: Execution

### Global Rules

- ALL keyframes: aspect ratio from Phase 1 (16:9 or 9:16). **Never 1:1.**
- ALL keyframe prompts must reference the visual style spec from Phase 2
- Process clips sequentially (clip 1 first, then clip 2, etc.)

### First Keyframe Generation

**Decision tree:**

```text
first_keyframe_reuse = yes?
  YES --> Use previous clip's last keyframe image. Do not generate.
  NO  --> Generate new first keyframe (see below).
```

**Generating a new first keyframe:**

1. Tool: Skill `nano-banana-pro`
2. Reference images: Relevant Phase 4 references for elements in this frame
3. Aspect ratio: 16:9 or 9:16 (from Phase 1)
4. Prompt must include:
   - Visual style spec (from Phase 2)
   - Scene description (from clip spec)
   - first_keyframe_framing (from clip spec)
   - first_keyframe_visible_content (from clip spec)
   - Appearance details for all visible recurring elements (from Phase 2)
   - "no text, no watermarks"

### Last Keyframe Generation

**Decision tree:**

```text
last_keyframe_required = no?
  YES --> Skip. Video model interpolates freely.
  NO  --> last_keyframe_edit_from_first = yes?
            YES --> Edit mode (see below)
            NO  --> Generate mode (see below)
```

**Edit mode** (last_keyframe_edit_from_first = yes):

1. Tool: Skill `nano-banana-pro` with first keyframe as reference
2. Prompt describes ONLY the changes from first keyframe:
   - "Same scene, but the character has turned to face right"
   - "Same composition, but the door is now open and warm light spills out"
3. Do NOT re-describe the entire scene -- the reference image provides context
4. Verify the result shows clear interpolatable change from first keyframe

**Generate mode** (last_keyframe_edit_from_first = no):

1. Tool: Skill `nano-banana-pro`
2. Reference images: Phase 4 references + scene environment reference
3. Full prompt with:
   - Visual style spec
   - last_keyframe_framing
   - last_keyframe_visible_content
   - All appearance details for visible recurring elements
4. Verify visual consistency with first keyframe (lighting direction, color temperature, outfit)

### Consistency Checklist (After Each Keyframe Pair)

Before proceeding to video generation, verify:

- [ ] Last keyframe shows clear interpolatable change from first keyframe
- [ ] Lighting direction is consistent between both keyframes
- [ ] Color temperature matches between both keyframes
- [ ] Depth of field is consistent
- [ ] Character outfit and distinguishing features are identical
- [ ] Environment elements that should persist are present in both
- [ ] Aspect ratio is correct (16:9 or 9:16, not 1:1)

### Video Generation API

**Default: Veo 3.1 Fast.** Use Veo 3.1 (full) or Sora only if user explicitly requests higher quality or alternative model.

#### Veo 3.1 Fast / Veo 3.1 (Google GenAI SDK)

```python
import os, time
from google import genai
from google.genai import types

client = genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))

def generate_video_veo(prompt: str, output_path: str,
                       model: str = "veo-3.0-fast-generate-001",
                       aspect_ratio: str = "16:9",
                       duration_seconds: int = 6):
    """
    model options:
      "veo-3.0-fast-generate-001"  -- Veo 3.1 Fast (DEFAULT)
      "veo-3.0-generate-001"       -- Veo 3.1 full quality
    aspect_ratio: "16:9" or "9:16"
    duration_seconds: 4, 6, or 8
    """
    operation = client.models.generate_video(
        model=model,
        prompt=prompt,
        config=types.GenerateVideoConfig(
            aspect_ratio=aspect_ratio,
            duration_seconds=duration_seconds,
            number_of_videos=1,
        ),
    )
    # Poll until done (~60s Fast, ~140s full)
    while not operation.done:
        time.sleep(10)
        operation = client.operations.get(operation)

    video = operation.response.generated_videos[0]
    client.files.download(file=video.video, download_path=output_path)
    print(f"Saved: {output_path}")
    return output_path

# Example:
# generate_video_veo("Cinematic shot of...", "clip_01.mp4")
# generate_video_veo("...", "clip_01.mp4", model="veo-3.0-generate-001")
```

#### Sora (OpenAI API — alternative)

```python
import os, time
from openai import OpenAI

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def generate_video_sora(prompt: str, output_path: str,
                        duration: int = 5,
                        resolution: str = "480p",
                        aspect_ratio: str = "16:9"):
    """
    model: "sora-1.0-turbo" (fast) or "sora-1.0" (higher quality)
    resolution: "480p", "720p", "1080p"
    duration: 5 or 10 seconds
    aspect_ratio: "16:9" or "9:16"
    """
    response = client.video.generations.create(
        model="sora-1.0-turbo",
        prompt=prompt,
        duration=duration,
        resolution=resolution,
        size=f"{aspect_ratio}",
    )
    # Download the video bytes
    video_bytes = client.video.generations.content(response.id)
    with open(output_path, "wb") as f:
        f.write(video_bytes)
    print(f"Saved: {output_path}")
    return output_path
```

### Video Prompt Construction

Submit to the video generation model with a detailed prompt that includes:

1. **Visual style** (from Phase 2 spec)
2. **Pacing** (from clip spec: slow/medium/fast)
3. **transition_description** (full 2-4 sentence description from clip spec)
4. **Subject appearance** (from Phase 2 recurring elements)
5. **Scene** (from clip spec)
6. **Audio elements** (see table below)

**Audio in video prompt:**

| Audio Type | Include in Video Prompt? | How |
|-----------|-------------------------|-----|
| On-screen dialogue | Yes | Include dialogue text in prompt, model generates with lip sync |
| Singing | Yes | Include lyrics and style description in prompt |
| Sound effects | Yes | Describe sounds in prompt (e.g., "sound of rain on metal roof") |
| Embedded BGM | Yes | Describe music style and mood in prompt |
| Separate BGM | No | Added later in mixing |
| Narration | No | Generated separately via ElevenLabs |

### BGM Sourcing (if separate)

If BGM source = separate for any clips:

1. Search royalty-free music libraries:
   - Pixabay Music (https://pixabay.com/music/)
   - YouTube Audio Library
   - Uppbeat
   - Mixkit
2. Match the mood, tempo, and genre defined in Phase 2
3. Download and trim to needed duration
4. **NEVER generate music with Python scripts or code** -- always source from libraries

### Narration Generation

For each clip with narration_cue != "none":

1. Use Skill `elevenlabs`
2. Voice profile from Phase 2 (same voice for all clips)
3. Generate **clip by clip** -- not all narration at once
4. Text: the narration_cue from the clip spec
5. Verify duration fits within clip duration (leave 0.5s buffer at start and end)
6. If narration is too long, trim the text and regenerate

### Audio Summary Table

| Audio Type | Source | Tool |
|-----------|--------|------|
| On-screen dialogue | Video model (lip sync) | Video generation prompt |
| Singing | Video model (lip sync) | Video generation prompt |
| Sound effects | Video model | Video generation prompt |
| Embedded BGM | Video model | Video generation prompt |
| Separate BGM | Royalty-free library | Manual search and download |
| Off-screen narration | ElevenLabs | Skill `elevenlabs`, clip by clip |

**Phase 5 → Phase 6 handoff:** Update Manifest: list all clip_NN.mp4 files, all narration_NN.mp3 files, BGM track filename. Then immediately start Phase 6 assembly — no need to pause.

### Audio Mixing

When combining multiple audio tracks:

1. **Preserve ALL tracks** -- overlay, never replace
2. Narration must be clearly audible over BGM (narration -3dB, BGM -12dB as starting point)
3. Consistent volume levels across all clips
4. BGM should duck slightly during narration passages
5. Sound effects from video model are preserved as-is

---

## Phase 6: Assembly & Post-Production

Takes all generated clips + audio → finished video file with narration, music, and subtitles.

### Step 1: Concatenate Clips

```bash
# Via video_editor.py (recommended — FFmpeg under the hood)
python ~/.claude/skills/video-editor/video_editor.py concat \
  clip_01.mp4 clip_02.mp4 clip_03.mp4 \
  --transition fade \
  --transition-duration 0.3 \
  -o assembled_raw.mp4
```

Or programmatically with moviepy (when frame-precise control needed):

```python
from moviepy import VideoFileClip, concatenate_videoclips

def concat_clips(clip_paths: list, output_path: str, transition_sec: float = 0.0):
    clips = [VideoFileClip(p) for p in clip_paths]
    if transition_sec > 0:
        # Cross-fade between clips
        from moviepy import CompositeVideoClip
        # moviepy 2.x: use crossfadein
        result = concatenate_videoclips(clips, method="compose")
    else:
        result = concatenate_videoclips(clips, method="chain")
    result.write_videofile(output_path, codec="libx264", audio_codec="aac")
    for c in clips:
        c.close()
    return output_path
```

### Step 2: Mix Narration + BGM onto Video

```bash
# Quick option via video_editor.py (music overlay only, no narration):
python ~/.claude/skills/video-editor/video_editor.py process \
  assembled_raw.mp4 \
  --custom-music narration.mp3 \
  --music-volume 0.15 \
  -o assembled_with_audio.mp4
```

Full mix (video original audio + narration + BGM) — Python/FFmpeg:

```python
import subprocess

def mix_audio(video_path: str, narration_path: str, bgm_path: str,
              output_path: str,
              narration_db: float = -3, bgm_db: float = -12):
    """
    Overlay narration and BGM onto video using FFmpeg.
    narration_db: volume adjustment for narration (dB)
    bgm_db: volume adjustment for BGM (dB), should duck under narration
    """
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", narration_path,
        "-i", bgm_path,
        "-filter_complex",
        (
            f"[1:a]volume={narration_db}dB[narr];"
            f"[2:a]volume={bgm_db}dB,aloop=loop=-1:size=2e+09[bgm];"
            "[0:a][narr][bgm]amix=inputs=3:duration=first:dropout_transition=3[audio]"
        ),
        "-map", "0:v", "-map", "[audio]",
        "-c:v", "copy", "-c:a", "aac", "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path

# Without BGM (narration only):
def add_narration_only(video_path: str, narration_path: str, output_path: str):
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path, "-i", narration_path,
        "-filter_complex", "[0:a][1:a]amix=inputs=2:duration=first[audio]",
        "-map", "0:v", "-map", "[audio]",
        "-c:v", "copy", "-c:a", "aac",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path
```

### Step 3: Subtitles

Choose ONE method based on use case:

#### Option A: FFmpeg SRT burn-in (simple, offline)

Generate SRT from clip plan, then burn with FFmpeg:

```python
import subprocess

def generate_srt(clips: list) -> str:
    """
    clips: list of dicts with 'narration_cue' and 'duration' keys.
    Returns SRT string.
    """
    def fmt(sec: float) -> str:
        h = int(sec // 3600)
        m = int((sec % 3600) // 60)
        s = int(sec % 60)
        ms = int((sec - int(sec)) * 1000)
        return f"{h:02}:{m:02}:{s:02},{ms:03}"

    lines, idx, t = [], 1, 0.0
    for clip in clips:
        dur = clip.get("duration", 6)
        text = clip.get("narration_cue", "none")
        if text and text.lower() != "none":
            lines += [str(idx), f"{fmt(t)} --> {fmt(t + dur)}", text, ""]
            idx += 1
        t += dur
    return "\n".join(lines)


def burn_subtitles_ffmpeg(video_path: str, srt_path: str, output_path: str,
                          font: str = "Arial",
                          font_size: int = 24,
                          color: str = "&HFFFFFF",
                          outline_color: str = "&H000000",
                          position: str = "bottom"):
    """
    Burn SRT subtitles into video via FFmpeg.
    position: "bottom" (default) or "center"
    """
    valign = "2" if position == "bottom" else "8"  # ASS: 2=bottom, 8=top
    style = (
        f"FontName={font},FontSize={font_size},"
        f"PrimaryColour={color},OutlineColour={outline_color},"
        f"Outline=2,Shadow=1,MarginV=30,Alignment={valign}"
    )
    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", f"subtitles={srt_path}:force_style='{style}'",
        "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


# Usage:
# srt_content = generate_srt(clips)
# with open("subs.srt", "w", encoding="utf-8") as f:
#     f.write(srt_content)
# burn_subtitles_ffmpeg("video_with_audio.mp4", "subs.srt", "final.mp4")
```

#### Option B: your subtitle API (styled captions — Hormozi, MrBeast, Karaoke, etc.)

Best for: social media (9:16 vertical), viral-style captions, auto-transcription from speech.

```python
import os, time, requests

SUBMAGIC_API_KEY = os.getenv('SUBMAGIC_API_KEY')
BASE_URL = "https://api.submagic.co/v1"
headers = {"Authorization": f"Bearer {SUBMAGIC_API_KEY}"}

def add_submagic_captions(video_path: str, output_path: str,
                          style: str = "hormozi",
                          language: str = "auto"):
    """
    Styles: hormozi, mrbeast, minimal, karaoke, gradient, neon
    language: "auto" (detect), "ru", "en"
    """
    # 1. Upload
    with open(video_path, "rb") as f:
        res = requests.post(f"{BASE_URL}/upload",
                            headers={"Authorization": f"Bearer {SUBMAGIC_API_KEY}"},
                            files={"file": f}).json()
    video_id = res["video_id"]

    # 2. Generate captions
    task = requests.post(f"{BASE_URL}/captions/generate", headers={**headers, "Content-Type": "application/json"},
                         json={"video_id": video_id,
                               "caption_style": style,
                               "options": {"language": language,
                                           "highlight_keywords": True}}).json()
    task_id = task["task_id"]

    # 3. Poll until done
    while True:
        status = requests.get(f"{BASE_URL}/tasks/{task_id}", headers=headers).json()
        if status["status"] == "completed":
            # Download result
            video_bytes = requests.get(status["download_url"]).content
            with open(output_path, "wb") as f:
                f.write(video_bytes)
            print(f"SubtitleService done: {output_path}")
            return output_path
        elif status["status"] == "failed":
            raise RuntimeError(f"SubtitleService failed: {status}")
        time.sleep(5)
```

**When to choose SubtitleService vs FFmpeg:**

| Use Case | Method |
|----------|--------|
| Social media (TikTok/Reels/Shorts) | SubtitleService — viral styles |
| Cinematic / narrative film | FFmpeg SRT — clean burn-in |
| B2B / explainer | FFmpeg SRT — minimal style |
| Speech auto-transcription needed | SubtitleService — built-in transcription |
| Narration text already known | FFmpeg SRT — precise timing |

### Step 4: Full Assembly Pipeline

```python
def assemble_full_video(
    clip_paths: list,        # ["clip_01.mp4", "clip_02.mp4", ...]
    clips_spec: list,        # Phase 3 clip specs (with narration_cue, duration)
    narration_path: str,     # Combined narration audio (or None)
    bgm_path: str,           # BGM track (or None)
    output_path: str,
    subtitle_method: str = "ffmpeg",  # "ffmpeg" or "submagic"
    subtitle_style: str = "minimal",  # for submagic
):
    import os, subprocess

    # 1. Concat clips
    raw = output_path.replace(".mp4", "_raw.mp4")
    subprocess.run(
        ["python", os.path.expanduser("~/.claude/skills/video-editor/video_editor.py"),
         "concat", *clip_paths, "-o", raw],
        check=True
    )

    # 2. Mix audio
    audio_mixed = output_path.replace(".mp4", "_audio.mp4")
    if narration_path and bgm_path:
        mix_audio(raw, narration_path, bgm_path, audio_mixed)
    elif narration_path:
        add_narration_only(raw, narration_path, audio_mixed)
    else:
        audio_mixed = raw

    # 3. Subtitles
    final = output_path
    if subtitle_method == "submagic":
        add_submagic_captions(audio_mixed, final, style=subtitle_style)
    else:
        srt_content = generate_srt(clips_spec)
        srt_path = output_path.replace(".mp4", ".srt")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_content)
        burn_subtitles_ffmpeg(audio_mixed, srt_path, final)

    print(f"Final video ready: {final}")
    return final
```

### Step 5: Logo & Branding Overlay

Only run if Phase 0 Branding answers include logo=yes.

```python
import subprocess

def add_logo_overlay(
    video_path: str,
    logo_path: str,          # PNG with transparency (RGBA)
    output_path: str,
    position: str = "top-right",   # top-left | top-right | bottom-left | bottom-right | center
    scale: float = 0.12,           # fraction of video width
    opacity: float = 0.85,         # 0.0 to 1.0
    padding: int = 30,             # pixels from edge
    start_sec: float = 0.0,        # when logo appears (0 = always visible)
    duration_sec: float = 0.0,     # 0 = whole video
):
    """
    Overlay a PNG logo on video using FFmpeg overlay filter.
    Logo must be PNG with transparency for clean compositing.
    """
    # Map position string to FFmpeg overlay expression
    pos_map = {
        "top-left":     f"x={padding}:y={padding}",
        "top-right":    f"x=W-w-{padding}:y={padding}",
        "bottom-left":  f"x={padding}:y=H-h-{padding}",
        "bottom-right": f"x=W-w-{padding}:y=H-h-{padding}",
        "center":       "x=(W-w)/2:y=(H-h)/2",
    }
    xy = pos_map.get(position, pos_map["top-right"])

    # Build enable expression for timed overlay
    if duration_sec > 0:
        enable = f"enable='between(t,{start_sec},{start_sec + duration_sec})'"
    else:
        enable = f"enable='gte(t,{start_sec})'"

    filter_complex = (
        f"[1:v]scale=iw*{scale}:-1,format=rgba,"
        f"colorchannelmixer=aa={opacity}[logo];"
        f"[0:v][logo]overlay={xy}:{enable}[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-i", logo_path,
        "-filter_complex", filter_complex,
        "-map", "[out]", "-map", "0:a",
        "-c:v", "libx264", "-c:a", "copy",
        output_path
    ]
    subprocess.run(cmd, check=True)
    return output_path


# Outro card: freeze last frame + logo centered (for YouTube/Reels outro)
def add_outro_freeze(
    video_path: str,
    logo_path: str,
    output_path: str,
    freeze_duration: float = 3.0,
):
    """Extend video with a frozen last frame + centered logo as outro card."""
    import tempfile, os

    # Step 1: Get video duration
    probe = subprocess.run(
        ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", video_path],
        capture_output=True, text=True, check=True
    )
    import json
    duration = float(json.loads(probe.stdout)["format"]["duration"])

    # Step 2: Freeze last frame for freeze_duration seconds
    frozen = output_path.replace(".mp4", "_frozen.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-sseof", "-0.1", "-i", video_path,
        "-vf", f"tpad=stop_mode=clone:stop_duration={freeze_duration}",
        "-c:v", "libx264", "-c:a", "aac", frozen
    ], check=True)

    # Step 3: Overlay logo on frozen portion
    add_logo_overlay(frozen, logo_path, output_path,
                     position="center", scale=0.20, opacity=1.0,
                     start_sec=duration, duration_sec=freeze_duration)
    os.remove(frozen)
    return output_path
```

**When to use each:**

| Scenario | Function | Notes |
| -------- | -------- | ----- |
| Persistent watermark whole video | `add_logo_overlay(start_sec=0)` | Corner, 80-85% opacity |
| Logo appears after 3s | `add_logo_overlay(start_sec=3)` | Avoids covering opening frame |
| YouTube outro with freeze | `add_outro_freeze()` | 3s freeze + centered logo |
| No logo (Phase 0 answered "нет") | Skip Step 5 entirely | — |

### Assembly Checklist

- [ ] All clips downloaded and named `clip_NN.mp4` sequentially
- [ ] Narration per clip generated via ElevenLabs and concatenated
- [ ] BGM downloaded/selected from royalty-free pool
- [ ] SRT generated from narration_cue timings (or SubtitleService chosen)
- [ ] Subtitle method chosen: FFmpeg (offline/cinematic) vs SubtitleService (social)
- [ ] Logo overlay applied if Phase 0 branding=yes (Step 5)
- [ ] Final video exported: verify duration, audio sync, subtitle timing, logo position

---

## Prompt Engineering Reference

### Core Prompt Structure

#### 1. Camera & Movement

```text
[Camera type] + [Movement] + [Angle]
```

Examples:

- "wide-angle low-angle shot, slow forward tracking"
- "static shot with shallow depth of field"
- "cinematic FPV flying through"
- "slow 360 orbital macro shot, 100mm lens"
- "over-the-shoulder shot"

#### 2. Subject Description

```text
[Main subject] + [Action/State] + [Details]
```

Examples:

- "a lone cyborg standing on the rocky surface"
- "a chubby penguin DJ performs at a neon-lit ice rave"
- "a tired worker rubbing his temples in exhaustion"

#### 3. Environment & Setting

```text
[Location] + [Time/Atmosphere] + [Details]
```

Examples:

- "alien planet with bioluminescent flora and floating mineral shards"
- "wet cobblestone street with amber streetlights"
- "bright white studio infinite background"

#### 4. Lighting

```text
[Light source] + [Quality] + [Color tone]
```

Examples:

- "warm amber streetlights reflecting on wet pavement"
- "cool-toned rim lighting with glowing highlights"
- "golden hour warm lighting"
- "harsh fluorescent overhead lights and green glow of monochrome monitor"

#### 5. Style & Quality

```text
[Resolution] + [Style] + [Mood]
```

Examples:

- "8K, hyper-realistic, cinematic"
- "film noir aesthetic, high contrast, photorealistic"
- "retro aesthetic, shot as if on 1980s color film, slightly grainy"

#### 6. Audio (if supported)

```text
Sound of [ambient sounds], [specific sounds], [music if any]
```

Examples:

- "Sound of steady rain, hurried heavy footsteps on wet stone, distant faint jazz trumpet"
- "deep ambient alien soundscape with soft synthetic hums"

### Category Templates

#### Cinematic / Film Noir

```text
[Shot type] with [depth of field], [subject action], [environment with mood lighting].
[Ambient sounds]. [Style]: Film noir aesthetic, high contrast, photorealistic, no subtitles.
```

#### Macro / Nature

```text
Cinematic 8K macro video of [subject]. [Detailed description of materials/textures].
[Lighting description]. [Camera movement], [lens], [focus details].
Hyper-detailed [style keywords], [motion description].
```

#### Action / FPV

```text
[Speed descriptor] cinematic FPV [flying/racing] through [environment],
[movement details], highly realistic textures, dramatic lighting, vivid colors,
dynamic motion that feels immersive and intensely energetic.
```

#### Comedy / Character

```text
[Character description] [action] at [location]. [Supporting characters/elements].
[Key comedic moment]. [Lighting], [mood descriptors].
```

#### Horror / Suspense

```text
Cinematic [era] horror style. [Character] [action] in [dark setting] with only [light source].
[Camera shot] showing [threat element]. [Suspense build-up]. [Climactic reveal].
```

#### Sci-Fi / Fantasy

```text
[Camera setup], [subject] on [otherworldly location] with [fantastical elements],
[atmospheric details], [ambient description], [lighting style],
high-detail [genre] cinematic style.
```

### Technical Parameters

#### Duration

- Short clips: 4-8 seconds
- Standard: 8-16 seconds
- Extended: 16-30 seconds

#### Aspect Ratios

- Cinematic: 16:9
- Vertical/Mobile: 9:16
- Ultra-wide: 21:9

#### Motion Strength

- Subtle: 0.3-0.5
- Moderate: 0.5-0.7
- Dynamic: 0.7-0.9

### Negative Prompts (Always Include)

```text
text, watermark, logo, blur, motion blur, low resolution, grainy, pixelated,
ugly, deformed, disfigured, extra limbs, distorted proportions, artifacts
```

Add context-specific negatives:

- For realistic: "cartoon, anime, illustration"
- For bright scenes: "dark, underexposed"
- For clean shots: "noise, compression artifacts"

### Quality Boosters

Add these for better results:

- "8K resolution" / "4K ultra HD"
- "hyper-realistic" / "photorealistic"
- "cinematic quality"
- "professional cinematography"
- "sharp focus"
- "smooth motion"

---

## Tips

1. **Be specific** -- "wet cobblestone street" > "street"
2. **Describe materials and textures** -- "metallic crimson chassis" > "red car"
3. **Include motion details** -- "slowly turning her head" > "looking"
4. **Set the mood with lighting** -- include atmosphere and light sources
5. **Layer details** -- subject > environment > lighting > style
6. **Use sensory details** -- sounds, textures, temperatures
7. **Avoid conflicting styles** -- don't mix incompatible aesthetics

---

## Ken Burns Effects (Image Animation)

Convert static images into animated video clips using FFmpeg zoompan filters. Three built-in effects simulate camera motion on a still frame.

### Effects

| Effect | What It Does | Best For |
|--------|-------------|----------|
| `zoom_in` | Starts zoomed out (1.12x), slowly zooms to 1.0x, centered | Reveal shots, dramatic emphasis |
| `pan_right` | Fixed 1.15x zoom, pans left-to-right across the image | Landscapes, wide scenes, establishing shots |
| `zoom_out` | Starts at 1.0x, slowly zooms to 1.12x, centered | Pull-back reveals, endings |

### FFmpeg Filter Strings

Each effect pre-scales the image to ~112-115% of target resolution, then applies zoompan:

**zoom_in** (default):
```text
scale={W*1.12}:{H*1.12},zoompan=z='1.12-0.12*on/{FRAMES}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={FRAMES}:s={W}x{H}:fps=30
```

**pan_right**:
```text
scale={W*1.15}:{H*1.15},zoompan=z=1.15:x='0.15*iw*on/{FRAMES}':y='ih*0.075':d={FRAMES}:s={W}x{H}:fps=30
```

**zoom_out**:
```text
scale={W*1.12}:{H*1.12},zoompan=z='1.0+0.12*on/{FRAMES}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={FRAMES}:s={W}x{H}:fps=30
```

Where `FRAMES = duration * 30` (fps), `W`/`H` = target resolution (e.g., 1080x1920 for 9:16).

### Python Implementation

```python
import subprocess

def animate_frame(img_path: str, out_path: str, duration: float = 6.0,
                  effect: str = "zoom_in", width: int = 1080, height: int = 1920):
    """Ken Burns animation on a single frame.

    Args:
        img_path: Path to input image (PNG/JPG).
        out_path: Path to output video (MP4).
        duration: Clip duration in seconds.
        effect: One of 'zoom_in', 'pan_right', 'zoom_out'.
        width: Target video width.
        height: Target video height.
    """
    fps = 30
    frames = int(duration * fps)
    w, h = width, height

    if effect == "zoom_in":
        vf = (
            f"scale={int(w * 1.12)}:{int(h * 1.12)},"
            f"zoompan=z='1.12-0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    elif effect == "pan_right":
        vf = (
            f"scale={int(w * 1.15)}:{int(h * 1.15)},"
            f"zoompan=z=1.15:x='0.15*iw*on/{frames}':y='ih*0.075'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )
    else:  # zoom_out
        vf = (
            f"scale={int(w * 1.12)}:{int(h * 1.12)},"
            f"zoompan=z='1.0+0.12*on/{frames}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
            f":d={frames}:s={w}x{h}:fps={fps}"
        )

    subprocess.run([
        "ffmpeg", "-loop", "1", "-i", img_path,
        "-vf", vf, "-t", str(duration), "-r", str(fps),
        "-pix_fmt", "yuv420p", out_path, "-y", "-loglevel", "quiet",
    ], check=True)
    return out_path
```

### CLI Usage

```bash
python ~/.claude/skills/video-editor/video_editor.py ken-burns image.png \
  --duration 6 --effect zoom_in -o animated.mp4
```

### Integration with Video Generation Pipeline

Ken Burns fits into Phase 4/5 as a bridge between static reference images and video clips:

1. **Phase 4** generates reference images (Gemini / nano-banana-pro)
2. **Ken Burns** animates those images into video clips when AI video generation is unavailable or too expensive
3. Animated clips feed into **Phase 6** assembly pipeline as regular `clip_NN.mp4` files

**When to use Ken Burns instead of Veo/Sora:**

| Scenario | Use Ken Burns? |
|----------|---------------|
| Budget is zero (no Veo/Sora credits) | Yes -- free, local FFmpeg |
| Image-heavy explainer (charts, diagrams) | Yes -- better than AI video for static content |
| Need exact visual control | Yes -- image is exactly what you designed |
| Need realistic motion, people walking | No -- use Veo/Sora |
| Need camera parallax / 3D depth | No -- Ken Burns is 2D only |

---

## Music Ducking (Auto Voice/Music Balance)

Automatically lower background music volume during speech using FFmpeg volume filter driven by Whisper word timestamps.

### How It Works

1. Run Whisper on voiceover audio to get word-level timestamps
2. Merge close words into speech regions (gap < 0.5s = same region)
3. Build an FFmpeg volume filter with `between()` conditions for each region
4. During speech: volume = 0.12 (quiet), during gaps: volume = 0.25 (moderate)
5. Transition buffer of 0.3s smooths the volume changes

### FFmpeg Volume Filter Format

```text
volume='if(between(t,S1,E1)+between(t,S2,E2)+..., 0.12, 0.25)':eval=frame
```

Where `S1,E1` are start/end of each speech region (with 0.3s buffer).

### Python Implementation

```python
def get_speech_regions(audio_path: str) -> list[tuple[float, float]]:
    """Extract speech regions from Whisper word timestamps.

    Returns list of (start, end) tuples representing continuous speech.
    Adjacent words within 0.5s are merged into one region.
    """
    import whisper

    model = whisper.load_model("base")
    result = model.transcribe(str(audio_path), word_timestamps=True)

    words = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            words.append({"start": w["start"], "end": w["end"]})

    if not words:
        return [(0.0, 60.0)]  # fallback: treat entire audio as speech

    # Merge close words into regions (gap < 0.5s)
    regions = []
    region_start = words[0]["start"]
    region_end = words[0]["end"]

    for w in words[1:]:
        if w["start"] - region_end < 0.5:
            region_end = w["end"]
        else:
            regions.append((region_start, region_end))
            region_start = w["start"]
            region_end = w["end"]
    regions.append((region_start, region_end))
    return regions


def build_duck_filter(speech_regions: list[tuple[float, float]],
                      buffer: float = 0.3) -> str:
    """Build FFmpeg volume filter expression for ducking during speech.

    Args:
        speech_regions: List of (start, end) tuples from get_speech_regions().
        buffer: Seconds of padding around each region for smooth transition.

    Returns:
        FFmpeg volume filter string ready for -af flag.
    """
    if not speech_regions:
        return "volume=0.25"

    conditions = []
    for start, end in speech_regions:
        s = max(0, start - buffer)
        e = end + buffer
        conditions.append(f"between(t,{s:.2f},{e:.2f})")

    condition_expr = "+".join(conditions)
    return f"volume='if({condition_expr}, 0.12, 0.25)':eval=frame"
```

### CLI Usage

```bash
python ~/.claude/skills/video-editor/video_editor.py ducking mixed.mp4 \
  --timestamps voice_ts.json -o ducked.mp4
```

### Integration with Phase 6

In the assembly pipeline, ducking replaces the static `bgm_db=-12` approach:

```python
# Instead of flat volume reduction:
#   mix_audio(video, narration, bgm, output, bgm_db=-12)
# Use dynamic ducking:

regions = get_speech_regions("narration.mp3")
duck_filter = build_duck_filter(regions)

# Apply duck filter to BGM before mixing:
# ffmpeg -i bgm.mp3 -af "{duck_filter}" bgm_ducked.mp3
# Then mix: ffmpeg -i video.mp4 -i narration.mp3 -i bgm_ducked.mp3 ...
```

**Ducking vs flat volume:**

| Approach | Pros | Cons |
|----------|------|------|
| Flat BGM volume (-12dB) | Simple, predictable | Music too quiet in gaps, or too loud during speech |
| Dynamic ducking (Whisper) | Professional sound, music fills gaps naturally | Requires Whisper, adds ~10s processing |

---

## Free Captions (Whisper + ASS Word-Highlight)

Alternative to SubtitleService when budget is limited or offline processing is required. Uses OpenAI Whisper for transcription and generates ASS (Advanced SubStation Alpha) subtitles with per-word color highlighting.

### When to Use

| Criteria | SubtitleService | Whisper + ASS |
|----------|----------|---------------|
| Cost | Paid API | Free (local) |
| Internet required | Yes | No |
| Viral caption styles (Hormozi, MrBeast) | Yes | No (custom style only) |
| Word-by-word highlighting | Yes | Yes |
| Offline / air-gapped | No | Yes |
| Processing speed | ~30s (cloud) | ~10-20s (local GPU) |
| Language support | Auto-detect | 99 languages (Whisper) |
| Customization | Limited presets | Full ASS format control |

### Pipeline

1. **Whisper transcription** with `word_timestamps=True`
2. **Word grouping** -- 4 words per visible group (avoids overcrowded screen)
3. **ASS generation** -- one dialogue line per active word, with highlight override tags
4. **FFmpeg burn-in** -- `-vf "ass=captions.ass"`

### Step 1: Whisper Word Timestamps

```python
import whisper

def get_word_timestamps(audio_path: str, lang: str = "en") -> list[dict]:
    """Get word-level timestamps from Whisper.

    Args:
        audio_path: Path to audio file (MP3/WAV/M4A).
        lang: Language code (en, ru, es, etc.).

    Returns:
        List of {"word": str, "start": float, "end": float}.
    """
    model = whisper.load_model("base")
    result = model.transcribe(
        audio_path,
        language=lang[:2],
        word_timestamps=True,
    )
    words = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            words.append({
                "word": w["word"].strip(),
                "start": w["start"],
                "end": w["end"],
            })
    return words
```

### Step 2: Word Grouping

```python
def group_words(words: list[dict], group_size: int = 4) -> list[list[dict]]:
    """Group words into chunks for caption display.

    4 words per group is optimal for readability on 9:16 vertical video.
    """
    return [words[i:i + group_size] for i in range(0, len(words), group_size)]
```

### Step 3: ASS Subtitle Generation

ASS format allows per-character styling via override tags. The active (currently spoken) word gets yellow highlight + bold + larger font, while inactive words remain white.

**Active word tag:** `{\c&H00FFFF&\b1\fs80}WORD{\r}`
- `\c&H00FFFF&` = yellow in BGR hex
- `\b1` = bold
- `\fs80` = font size 80 (vs default 72)
- `{\r}` = reset to default style

```python
def generate_ass(words: list[dict], output_path: str,
                 video_width: int = 1080, video_height: int = 1920) -> str:
    """Generate ASS subtitle file with word-by-word color highlighting.

    Args:
        words: Word timestamps from get_word_timestamps().
        output_path: Path to write .ass file.
        video_width: Target video width.
        video_height: Target video height.

    Returns:
        Path to generated ASS file.
    """
    margin_v = int(video_height * 0.25)  # position at ~75% down from top

    header = f"""[Script Info]
Title: Pipeline Captions
ScriptType: v4.00+
PlayResX: {video_width}
PlayResY: {video_height}
WrapStyle: 0

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,72,&H00FFFFFF,&H000000FF,&H00000000,&H80000000,-1,0,0,0,100,100,0,0,3,3,0,2,40,40,{margin_v},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    def fmt_time(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    groups = group_words(words)
    events = []

    for group in groups:
        if not group:
            continue
        for active_idx, active_word in enumerate(group):
            parts = []
            for j, w in enumerate(group):
                if j == active_idx:
                    parts.append(f"{{\\c&H00FFFF&\\b1\\fs80}}{w['word']}{{\\r}}")
                else:
                    parts.append(w["word"])
            text = " ".join(parts)
            events.append(
                f"Dialogue: 0,{fmt_time(active_word['start'])},"
                f"{fmt_time(active_word['end'])},Default,,0,0,0,,{text}"
            )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(header + "\n".join(events))
    return output_path
```

### Step 4: FFmpeg Burn-In

```bash
ffmpeg -y -i video.mp4 -vf "ass=captions.ass" -c:a copy output.mp4
```

**Important:** FFmpeg must be compiled with `--enable-libass` for ASS support. Check with:

```bash
ffmpeg -filters 2>&1 | grep ass
```

### Full Pipeline Example

```python
# 1. Get timestamps
words = get_word_timestamps("narration.mp3", lang="ru")

# 2. Generate ASS
generate_ass(words, "captions.ass", video_width=1080, video_height=1920)

# 3. Burn into video
import subprocess
subprocess.run([
    "ffmpeg", "-y", "-i", "assembled_audio.mp4",
    "-vf", "ass=captions.ass", "-c:a", "copy", "final.mp4"
], check=True)
```

---

## Pexels Stock B-Roll (Free Fallback)

Free stock video from Pexels API as fallback when Veo/Sora/HeyGen are unavailable or budget is zero.

### API Endpoint

```text
GET https://api.your-stock-video.example/videos/search
  ?query=TERM
  &orientation=portrait    (or landscape)
  &per_page=15

Headers:
  Authorization: {PEXELS_API_KEY}
```

### Selection Logic

1. Search with descriptive query term
2. Filter: exact resolution match -- 1080x1920 (portrait) or 1920x1080 (landscape)
3. Sort by duration closest to target (default target: 15s)
4. Deduplicate via URL prefix (`link.split('.hd')[0]`)
5. Return first unused video URL

### Python Implementation

```python
import os
import requests


def search_pexels_videos(query: str, orientation: str = "portrait",
                         per_page: int = 15) -> dict:
    """Search Pexels video API.

    Args:
        query: Search term (e.g., 'city night traffic').
        orientation: 'portrait' or 'landscape'.
        per_page: Number of results (max 80).

    Returns:
        Raw JSON response from Pexels API.
    """
    url = "https://api.your-stock-video.example/videos/search"
    headers = {"Authorization": os.getenv("PEXELS_API_KEY")}
    params = {
        "query": query,
        "orientation": orientation,
        "per_page": per_page,
    }
    response = requests.get(url, headers=headers, params=params, timeout=15)
    response.raise_for_status()
    return response.json()


def get_best_video(query: str, orientation: str = "portrait",
                   target_duration: int = 15,
                   used_urls: list[str] | None = None) -> str | None:
    """Find the best matching Pexels video for a given query.

    Args:
        query: Search term.
        orientation: 'portrait' (9:16) or 'landscape' (16:9).
        target_duration: Preferred video duration in seconds.
        used_urls: List of URL prefixes already used (for deduplication).

    Returns:
        Direct download URL of the best match, or None if nothing found.
    """
    used_urls = used_urls or []
    data = search_pexels_videos(query, orientation)
    videos = data.get("videos", [])

    # Filter by exact resolution
    is_landscape = orientation == "landscape"
    if is_landscape:
        filtered = [v for v in videos
                    if v["width"] >= 1920 and v["height"] >= 1080
                    and v["width"] / v["height"] == 16 / 9]
    else:
        filtered = [v for v in videos
                    if v["width"] >= 1080 and v["height"] >= 1920
                    and v["height"] / v["width"] == 16 / 9]

    # Sort by duration closest to target
    sorted_videos = sorted(filtered, key=lambda x: abs(target_duration - int(x["duration"])))

    # Find first unused video with matching resolution
    target_w, target_h = (1920, 1080) if is_landscape else (1080, 1920)
    for video in sorted_videos:
        for vf in video["video_files"]:
            if vf["width"] == target_w and vf["height"] == target_h:
                url_prefix = vf["link"].split(".hd")[0]
                if url_prefix not in used_urls:
                    return vf["link"]

    return None
```

### CLI Usage

```bash
# Download a portrait b-roll clip about "city night rain"
python -c "
from video_gen_utils import get_best_video
url = get_best_video('city night rain', orientation='portrait')
if url:
    import requests
    r = requests.get(url)
    open('broll_city.mp4', 'wb').write(r.content)
"
```

### When to Use Pexels

| Scenario | Use Pexels? |
|----------|-------------|
| Zero budget, need generic b-roll | Yes |
| Veo/Sora rate-limited or unavailable | Yes (fallback) |
| Need specific branded content | No -- use AI generation |
| Need custom character/action | No -- use Veo/Sora |
| Explainer with stock footage inserts | Yes -- mix with AI clips |

### Rate Limits

- 200 requests/hour, 20,000 requests/month (free tier)
- Rate limit headers: `X-Ratelimit-Limit`, `X-Ratelimit-Remaining`, `X-Ratelimit-Reset`
- Attribution required: link to Pexels in video description (free license)

---

## Stage Resume (Crash Recovery)

JSON state machine embedded in the Production Manifest for crash recovery. If the pipeline fails mid-execution, re-running skips completed stages automatically.

### Pipeline Stages (Ordered)

| # | Stage | Artifacts |
|---|-------|-----------|
| 1 | `brief` | Production Plan text |
| 2 | `global` | Visual style, characters, voice profiles |
| 3 | `clip_plan` | Clip specification table |
| 4 | `ref_images` | Reference image file paths |
| 5 | `keyframes` | Keyframe image paths per clip |
| 6 | `videos` | Generated clip_NN.mp4 paths |
| 7 | `narration` | Narration audio paths per clip |
| 8 | `bgm` | BGM track path + duck filter |
| 9 | `assembly` | assembled_raw.mp4, assembled_audio.mp4 |
| 10 | `subtitles` | final.mp4 with burned subtitles |

### State API

```python
import json
from datetime import datetime, timezone
from pathlib import Path

STAGES = [
    "brief", "global", "clip_plan", "ref_images", "keyframes",
    "videos", "narration", "bgm", "assembly", "subtitles",
]


class PipelineState:
    """Tracks completion per stage in the Production Manifest JSON.

    Each stage records: status (done/failed), timestamp, artifact paths.
    Re-running the pipeline skips completed stages automatically.
    """

    def __init__(self, manifest: dict):
        self.manifest = manifest
        if "_pipeline_state" not in self.manifest:
            self.manifest["_pipeline_state"] = {}

    @property
    def state(self) -> dict:
        return self.manifest["_pipeline_state"]

    def is_done(self, stage: str) -> bool:
        """Check if a stage completed successfully."""
        return self.state.get(stage, {}).get("status") == "done"

    def is_failed(self, stage: str) -> bool:
        """Check if a stage failed."""
        return self.state.get(stage, {}).get("status") == "failed"

    def complete_stage(self, stage: str, artifacts: dict | None = None):
        """Mark a stage as completed with optional artifact metadata.

        Args:
            stage: Stage name from STAGES list.
            artifacts: Dict of artifact keys to file paths or values.
        """
        self.state[stage] = {
            "status": "done",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if artifacts:
            self.state[stage]["artifacts"] = artifacts

    def fail_stage(self, stage: str, error: str = ""):
        """Mark a stage as failed with error description."""
        self.state[stage] = {
            "status": "failed",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "error": error,
        }

    def get_artifact(self, stage: str, key: str, default=None):
        """Retrieve an artifact value from a completed stage."""
        return self.state.get(stage, {}).get("artifacts", {}).get(key, default)

    def reset(self):
        """Clear all pipeline state (for --force full re-run)."""
        self.manifest["_pipeline_state"] = {}

    def summary(self) -> str:
        """Human-readable status of all stages."""
        lines = []
        for stage in STAGES:
            status = self.state.get(stage, {}).get("status", "pending")
            marker = {"done": "+", "failed": "!", "pending": " "}.get(status, "?")
            lines.append(f"  [{marker}] {stage}")
        return "\n".join(lines)

    def save(self, path: str):
        """Write the manifest (with embedded state) to disk."""
        Path(path).write_text(
            json.dumps(self.manifest, indent=2, ensure_ascii=False)
        )
```

### Production Manifest with State

Add `_pipeline_state` field to the Production Manifest:

```json
{
  "title": "Product Demo Video",
  "phase": 5,
  "_pipeline_state": {
    "brief": {
      "status": "done",
      "timestamp": "2026-03-28T10:00:00+00:00"
    },
    "global": {
      "status": "done",
      "timestamp": "2026-03-28T10:02:00+00:00"
    },
    "clip_plan": {
      "status": "done",
      "timestamp": "2026-03-28T10:05:00+00:00",
      "artifacts": {"total_clips": 5}
    },
    "ref_images": {
      "status": "done",
      "timestamp": "2026-03-28T10:10:00+00:00",
      "artifacts": {"images": ["ref_hero_front.png", "ref_office.png"]}
    },
    "keyframes": {
      "status": "done",
      "timestamp": "2026-03-28T10:15:00+00:00"
    },
    "videos": {
      "status": "failed",
      "timestamp": "2026-03-28T10:25:00+00:00",
      "error": "Veo API timeout on clip_03"
    }
  }
}
```

### Resume Behavior

On re-run, the pipeline checks each stage:

```python
state = PipelineState(manifest)

for stage in STAGES:
    if state.is_done(stage):
        print(f"Skipping {stage} (already done)")
        continue
    if state.is_failed(stage):
        print(f"Retrying {stage} (previously failed: {state.state[stage].get('error')})")

    try:
        artifacts = run_stage(stage, state)
        state.complete_stage(stage, artifacts)
        state.save("manifest.json")
    except Exception as e:
        state.fail_stage(stage, str(e))
        state.save("manifest.json")
        raise  # stop pipeline, user can resume later
```

### Status Display

```text
Pipeline Status:
  [+] brief
  [+] global
  [+] clip_plan
  [+] ref_images
  [+] keyframes
  [!] videos          ← failed here, will retry on resume
  [ ] narration
  [ ] bgm
  [ ] assembly
  [ ] subtitles
```

---

## HeyGen Workflow Gateway as B-Roll Provider

Alternative to direct Veo 3.1 API calls: use HeyGen's Workflow Gateway for unified billing and access to multiple video generation providers.

### API Endpoint

```text
POST https://api.heygen.com/v1/workflows/executions

Headers:
  X-Api-Key: {HEYGEN_API_KEY}
  Content-Type: application/json

Body:
{
  "workflow_type": "GenerateVideoNode",
  "provider": "veo_3_1",
  "prompt": "Cinematic shot of...",
  "aspect_ratio": "16:9",
  "duration": 6
}
```

### Available Providers

| Provider | ID | Speed | Quality | Notes |
|----------|-----|-------|---------|-------|
| Veo 3.1 | `veo_3_1` | ~60s | High | Default, best speed/quality |
| Kling Pro | `kling_pro` | ~90s | High | Good for character motion |
| Sora v2 | `sora_v2` | ~90s | High | OpenAI via HeyGen |
| Runway Gen-4 | `runway_gen4` | ~120s | Highest | Best visual fidelity |

### When to Use HeyGen Gateway vs Direct API

| Scenario | Use HeyGen Gateway | Use Direct API |
|----------|-------------------|----------------|
| HeyGen credits available and want unified billing | Yes | No |
| Need to switch providers without code change | Yes | No |
| Need raw API control and lowest latency | No | Yes |
| Multi-scene avatar video (HeyGen + b-roll) | Yes -- same billing | No |
| No HeyGen subscription | No | Yes |

### Python Implementation

```python
import os
import time
import requests


def generate_via_heygen_workflow(
    prompt: str,
    output_path: str,
    provider: str = "veo_3_1",
    aspect_ratio: str = "16:9",
    duration: int = 6,
) -> str:
    """Generate video via HeyGen Workflow Gateway.

    Args:
        prompt: Video generation prompt.
        output_path: Path to save the output MP4.
        provider: One of 'veo_3_1', 'kling_pro', 'sora_v2', 'runway_gen4'.
        aspect_ratio: '16:9' or '9:16'.
        duration: Clip duration in seconds.

    Returns:
        Path to downloaded video file.

    Raises:
        RuntimeError: If generation fails or times out.
    """
    api_key = os.getenv("HEYGEN_API_KEY")
    if not api_key:
        raise RuntimeError("HEYGEN_API_KEY not set in environment")

    headers = {
        "X-Api-Key": api_key,
        "Content-Type": "application/json",
    }

    # Start generation
    resp = requests.post(
        "https://api.heygen.com/v1/workflows/executions",
        headers=headers,
        json={
            "workflow_type": "GenerateVideoNode",
            "provider": provider,
            "prompt": prompt,
            "aspect_ratio": aspect_ratio,
            "duration": duration,
        },
        timeout=30,
    )
    resp.raise_for_status()
    execution_id = resp.json()["data"]["execution_id"]

    # Poll for completion (max 5 minutes)
    for _ in range(60):
        time.sleep(5)
        status_resp = requests.get(
            f"https://api.heygen.com/v1/workflows/executions/{execution_id}",
            headers=headers,
            timeout=15,
        )
        status_resp.raise_for_status()
        data = status_resp.json()["data"]

        if data["status"] == "completed":
            video_url = data["output"]["video_url"]
            video_bytes = requests.get(video_url, timeout=60).content
            with open(output_path, "wb") as f:
                f.write(video_bytes)
            return output_path
        elif data["status"] == "failed":
            raise RuntimeError(f"HeyGen workflow failed: {data.get('error', 'unknown')}")

    raise RuntimeError("HeyGen workflow timed out after 5 minutes")
```

### Integration with Multi-Scene Pipeline

When producing HeyGen avatar videos with AI-generated b-roll inserts:

1. Avatar scenes: HeyGen avatar API (talking head)
2. B-roll scenes: HeyGen Workflow Gateway with `GenerateVideoNode`
3. Both billed through the same HeyGen account
4. Assembly: local FFmpeg concat (Phase 6)
