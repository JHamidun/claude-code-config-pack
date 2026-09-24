# vo_and_captions.md — fixed-window ElevenLabs voiceover + subtitle handoff

## Voiceover — text2speech_v2 / ElevenLabs · ONE LINE PER BLOCK
- **One narrator voice for the whole video — call `list_voices` at intake** so the
  user can browse current voices and previews, then collect the visible voice name
  with native structured input when callable or one concise normal-chat question
  (no generated audition samples), with a one-line channel recommendation:
  **History → Arthur or Callum · Kids → Remy · Explainer → Remy, Roxie or Cillian ·
  Picture Story → match the tone.** These are also the auto-pick defaults for
  hands-off runs and voiceless briefs. Custom (element) voices work as well as presets. Record the picked pair and
  use the SAME `voice_id`+`voice_type` on EVERY line — never let lines come out in
  different voices; a take that comes back in a different timbre = `failed` → regenerate
  with the locked pair.
- **Intonation & mood live in the SCRIPT, not in the voice:** fit delivery to the channel
  type + topic (sombre topic → measured wording, fewer gags; playful → lighter lines,
  more performed brackets). The voice never changes mid-video.
- **Kids call-and-response:** the narrator addresses characters and the viewer by name
  ("Say hi to Masha!", "Can YOU count the apples?") and the video stages the visible
  reaction (see kids-styles.md). Questions go at the END of a line — the block boundary
  IS the answer beat, and the next line opens with the payoff ("That's right — three!").
  Never leave a ≥0.8s pause inside a line for the answer. Narrator-spoken sound-words
  ("whoosh!", "ding!") and catchphrases count as words in the Kids 17–21 budget.
- **One spoken line per block** (block N → `voiceNN.wav`). No timecodes, no big continuous
  chunk, no `adelay` juggling. One line = one 10s scene → perfect sync by construction.
- **Line prompt format — delivery direction, not pacing:** send every line as
  `[ {DELIVERY}, {optional block mood}, starts speaking immediately] [00:00-00:09] {text}`.
  {DELIVERY} is ONE direction phrase composed once for the whole video to fit the channel
  type + topic (e.g. `wry conversational explainer, neutral accent, bright dry timbre,
  lively pace`) and repeated VERBATIM on every line — that keeps the timbre consistent
  across blocks. {optional block mood} is 2–4 words for this block's beat (`a bright
  knowing reveal`, `hushed conspiratorial`). `starts speaking immediately` kills the
  leading pause. ElevenLabs ignores the `[00:00-00:09]` window for pacing; word count
  is the only length lever.
- **Measured retries:** the initial word band is not an unbreakable retry floor.
  After converted WAVs exist, run `${HF_WORKFLOWS}/faceless-video/scripts/measure_narration_takes.py`
  with `--script script_manifest.json --voice-dir work/voices --duration-seconds {requested_seconds}`
  in that same call. For measured overlong slots only, follow `recommended_words`
  and revalidate with the cumulative `--duration-retry-blocks` set (17-word floor
  per full block). Passing takes are immutable. Soft 7.2–7.8s is accepted only
  after one retry; a hard miss after three attempts is a failure, not a deliverable.
- **Length: each line should naturally fill most of its block** (the assembler CENTRES
  detected speech inside the block, ignoring the file's edge silences). With the
  timecode format write **20–23 words**, comma-light, at most TWO sentences. Enforce
  **7.8–9.5s detected speech**, `rate=ok` (≤2.9 wps), and **no internal pause ≥0.8s** —
  the assembler flags pausey takes (WARN with the pause
  length); rewrite flowing and regenerate, don't ship stalls. This applies to Kids too:
  use the 17–21-word range with an EXCITED {DELIVERY} cue and bounded performed
  brackets (`${FACELESS_STYLES_DIR}/references/kids-styles.md §Kids voice pace`) — warmth = word choice, not pauses.
  Convert each returned MP3 with the narrator skill's reverse-trim/fade recipe before
  measurement. **If detected speech exceeds its block or `rate=RUSHED` → rewrite it shorter and regenerate.
  NEVER `atempo` /
  speed-up / slow-down / pitch-shift** to fit. Do NOT touch `speech_rate` unless asked.
  A clearly sparse first take should be rewritten denser; after the bounded retry
  budget, fail any take that still misses the hard window or delivery gates. Prefer one flowing
  clause over clipped sentences and keep commas sparse: TTS pauses ~0.7s at every
  period and ~0.5s at every comma, so fewer of them both shortens the take and removes
  the pausey feel.
- **Emotion in [square brackets]** — performed non-verbals: `[scoffs] [dry laugh] [sighs]
  [chuckles] [mock gasp] [whispers]`. Round-paren `(cues)` = direction, not spoken. Each
  performed bracket adds time — count it against the block duration.
- Open with a hook question when asked ("Have you ever wondered why…"). Numbers spelled out.
  Characters never lip-sync (external narrator).

## Assemble
In ordinary ChatGPT motion-video runs, download completed block and narration results
as ordered `blockNN.mp4` / `voiceNN.wav` pairs inside `sandbox_exec`, write
`pairs.txt`, and run
`${HF_WORKFLOWS}/faceless-video/scripts/finish_video.sh` with ordered
clip/voice URL files. Its motion path calls
`${HF_WORKFLOWS}/faceless-video/scripts/assemble_final.sh --out work/output/final.mp4 --blocks N --manifest pairs.txt
[--music bed.mp3] [--stepped 12]`. This sandbox FFmpeg script is the canonical path,
not a fallback. Do not call `explainer_video` merely to stitch completed media.
`--blocks N` is REQUIRED and the manifest is written for EVERY run (mispaired or
missing lines are hard fails). Captions are NOT part of assembly — Phase 7 invokes
the `subtitles` skill afterwards. It centers each narration line in its fixed block,
concatenates to **N×10s** (never shortened), and enforces the LEVEL LAW: voice 1.0
always, the clips' diegetic SFX kept under it at ~0.12, optional music bed at ~0.10
generic / **0.05 for the kids-look default bed**, DUCKED under speech by a
sidechain keyed on the voice (both hard-clamped ≤0.20) + `loudnorm -16 LUFS`;
outputs ONE file with no leading freeze. Diegetic SFX already live in the clips (whooshes, sparkles for Kids). Music
bed when the user supplied a file or explicitly asked — PLUS the Kids channel, where
a wordless bed is ON BY DEFAULT. A due bed needs no file: it is GENERATED before
the AUDIO review with
`sonilo_music` at the VIDEO's exact duration (≤600s in one request — verified;
longer = join parts; `${FACELESS_STYLES_DIR}/references/kids-styles.md §Kids music bed`); otherwise run
without `--music` —
voices + the clips' diegetic SFX are the mix. Never block delivery on a bed, never
substitute the speech model for music (`seed_audio` speaks; use
`generate_audio_batch` with `model:"sonilo_music"` for the bed).

## Subtitles — DELEGATED to the `subtitles` skill

Captions are no longer built here. When subtitles are on, Phase 7 invokes the
**`subtitles`** skill on the assembled cut and passes:

- the assembled video;
- `script_manifest.json` as the AUTHORED WORDING (Whisper stays the clock — every
  displayed word comes from the exact `vo_line` / `phrase`);
- the look: `clean` (default) · `paper` (torn cream label, handwritten — storybook
  tones) · `bold` (UGC ALL-CAPS with platform safe zones).

That skill owns the ≤5 words / ≤32 chars sizing, the three burners, per-language
font coverage, the Whisper dependency and the "unavailable → deliver unsubbed and
say so" fallback. Two things stay non-negotiable no matter who asks: **timings come
from Whisper only** (never from the script, never estimated) and **captions stay
small, single-line and out of the way**.

The caption scripts are preinstalled in the Higgsfield sandbox at
`${HF_WORKFLOWS}/subtitles/scripts/`. Use them only
through `sandbox_exec`; never resolve or execute a local `subtitles/scripts/`
directory.
