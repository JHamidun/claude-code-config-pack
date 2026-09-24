# Audio (music + voice + SFX)

Generates game audio in three layers — music, SFX, and voice — through the single
native audio tool. All three layers use the same tool; the layer is chosen by
the `model` parameter. Billed in workspace credits — no external API key. Use
when a scene needs a soundtrack, sound effects, or spoken character lines.

## Call

`generate_audio(model=..., prompt=..., duration=..., voice=..., count=1)`

For several independent clips (music bed, a handful of SFX, one voice line) use
`generate_audio_batch` instead — wrap each clip as one entry of `requests[]`,
same models and parameter rules — then `jobs_wait` and collect with one
`show_generation_by_ids`.

- Before calling, run `models_list({ type: "audio" })` to confirm the model list and
  the allowed `voice` values.
- `count` is always **1** — audio generation is single-sample.
- `get_cost: true` returns the credit cost without submitting a job (preflight).
- Pass only `model`, `prompt`, and the parameters listed per model below. **Never**
  pass provider-specific keys (`text`, `text_prompt`, `upload_audio_format`,
  `num_samples`, `seed`, `double_output`, `ambience`) — they are rejected.

### Per-model parameters — what is required vs forbidden

| `model` | Layer | `prompt` | `duration` | `voice` |
|---|---|---|---|---|
| `sonilo_music` | Music | required | **required** (positive seconds) | **forbidden** |
| `mirelo_text_to_audio` | SFX | required | **required** (positive seconds) | **forbidden** |
| `inworld_text_to_speech` | Voice | required | **forbidden** (do not pass) | **required** |

Passing a forbidden parameter is rejected, so keep the rules strict:
- `duration` is **only** for `sonilo_music` and `mirelo_text_to_audio`.
- `voice` is **only** for `inworld_text_to_speech`.

## Music — `sonilo_music`

- `prompt` is precise and descriptive, **≤ 2 sentences (1 is optimal)**, instrumental
  (no lyrics).
- Drive the mood from the scene's genre — there is no fixed list. Read the setting
  and translate it into tempo, key, instruments, and feel (e.g. horror → dark, minor,
  eerie; cozy → warm, velvety lo-fi, slow). Match the music to whatever the scene is.
- **`duration` is required.** Set it by energy, then loop the track on playback:
  - Energetic / intense / specific track → **`duration=30`**, looped.
  - Smooth / calm (e.g. lo-fi) → **`duration=40`**, looped.
  - Looping keeps it from getting repetitive too fast. (Looping is done on playback;
    it is not a tool parameter.)
- **Scope:** one track per scene or level. Open world → music starts only when there
  are enemies or bosses. Relaxed / chill game → music appears at occasional moments.
  Music should always sit quietly in the background while present.
- **At most 2 tracks per game**, preferably wordless.

## SFX — `mirelo_text_to_audio`

- Each SFX is **one isolated sound**, never a bundle of a whole scene.
- **`duration` is required** — match it to the length of the action it serves:
  - Pistol shot → `duration=1`.
  - A creaking building collapse → `duration=3`.
  - Thunder / lightning shaking everything → `duration=4` to `5`.
  - Continuous ambient (rain, ocean/water) → set a longer `duration` and **loop** it
    on playback, not a one-shot.
- **Generate at most 5 SFX**, chosen in this priority order:
  1. Main object / weapon and its interactions.
  2. Environment (e.g. a large battle scene, crowd).
  3. Motion cues (hand swings, hits, jumps).
  4. Ambient setting (rain, ocean, wind).
  5. One small extra detail, if room remains.

## Voice — `inworld_text_to_speech`

- `prompt` is the exact text the character speaks. **Do not pass `duration`.**
- **`voice` is required** and must be one of the allowed values from
  `models_list({ type: "audio" })`. Values are names in the form `"Name (lang)"`
  (e.g. `"Loretta (en)"`, `"Diego (es)"`). Do not invent a name; pick from the list.
- The voice name encodes both **gender** (by name) and **language** (the `(xx)`
  suffix). Use this to:
  - **Match gender** to the character.
  - **Match language** — use the language the voiceover is requested in; default to
    an English `(en)` voice.
- **One fixed voice per speaking entity:** decide up front who/what speaks, lock a
  single `voice` to each entity, and reuse it for all of that entity's lines. The
  agent writes a short script per entity and generates it line by line.

## Mix & ear-safety

The three models output clips at **different formats and loudness**, so the agent
must mix them itself, not just stack the raw outputs.

- **Normalize each clip to its target level** (in dBFS):
  - **Voice** ≈ **−6 dBFS** — loudest, always intelligible.
  - **SFX** ≈ **−10 to −12 dBFS** — below voice; peaks never exceed voice.
  - **Music** ≈ **−18 to −20 dBFS** — quiet background.
- **Layer by priority:** voice on top, then SFX, then music underneath.
- **Ear-safety limit:** the final mix true-peak stays **≤ −3 dBFS** — it never clips,
  and no layer exceeds its target. This is what keeps the mix from being harsh or
  startling.
- **Exception:** an intentional jump-scare / deliberately loud moment is the only
  case where an SFX may push past its normal level.

## Workflow

1. **Read the scene / genre** and decide which layers it needs — music, SFX, voice.
2. **Music** — one track for the scene/level via `sonilo_music` (required `duration`,
   30 or 40 by energy). Skip only if the user explicitly asks for no music.
3. **SFX** — at most 5 via `mirelo_text_to_audio`, each one isolated sound with a
   required `duration` matched to its action; ambient = loop on playback.
4. **Voice** — if anything speaks, lock one `voice` per entity via
   `inworld_text_to_speech` (no `duration`) and generate its lines.
5. **Mix** — normalize each clip to its level, layer by priority, keep the mix
   ears-safe (true-peak ≤ −3 dBFS).

## NOT for this skill / when to skip

- **Skip music** only when the user explicitly asks for no music.
- Otherwise, always produce at least a minimal sound set — even a single-player
  scene plays better with some audio, and NPCs or enemies can shout short, funny
  lines (voice layer). Default to some sound, never silence.
