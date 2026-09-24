# Production from separate recordings

## Evidence and edit clock

Inventory camera, screen, mic, slides and notes: duration, PTS start, FPS/VFR, dimensions, sample rate, channels, file stability. Match takes by actual clap/content plus timestamps, not filenames alone. Record file roles and SHA256. `media_tools.py inventory` is read-only.

Choose one output FPS (normally 30 for speech/slides). The edit manifest records source path, source-in and final frame count for each take. Camera and audio may need different source-in values. Explicit convention: positive camera delay means later presentation, not a larger source trim. Use one edit map; cuts in speech must shift all subsequent visuals and captions.

`media_tools.py sync-candidate` compares the same sound in two recordings and returns candidate offset + match score. It does not prove lip sync. Check consonants/claps near start/middle/end and after each splice. Changing offset suggests drift/VFR, not a constant delay. Normalize CFR and resample once. Never repeatedly guess 100–200 ms corrections.

For stutters: review the complete phrase, make aligned A/V cuts, apply a tiny audio crossfade only if it prevents clicks without clipping a phoneme. Do not mechanically remove every pause. Recheck edited syllables by listening. No invented words or synthesized voice unless requested.

## Raw assembly

`raw_edit.py` executes a supplied edit-decision list. It does **not** decide which take is best or where a word ends. Each segment has an audio source/in point and independent visual layers/in points. Generated output is a new synchronized base.

1. Reset source PTS, sample to target FPS. Each segment duration equals its integer frame count.
2. Select the correct microphone track, not screen silence/desktop music. Consistent loudness, no clipping/doubled mic. Normalize only when measured and needed, not after each visual revision.
3. Green key: test hair, ears, hands and black clothes against light/dark/final backgrounds. A reference setup used the ffmpeg `colorkey` filter with color `0x00ff00`, similarity `0.3`, blend `0.12`, followed by `despill=green`; these are example values, not universal defaults. Crop values are take-specific. Preserve alpha when grading: split → alphaextract → grade RGB → alphamerge. Do not alter clothes/face to fix contrast.
4. Reframe without stretching. Bottom-anchor torso, one rounded mask, external shadow. Light background behind dark clothing; do not leave a cutout floating in mid-panel. Never key an already keyed render again.
5. Shots: split, enlarged diagram, speaker-large, concept, real screen. Continuous narration over silent screen B-roll. Real UI readable and free of personal sidebars/notifications.
6. Finalize audio once. Future visual revisions use `-c:a copy` plus hash equality. Save filter graphs/logs inside project.

## Captions

ASR is a draft: correct Russian punctuation, product names/numbers against speech. Captions follow spoken words, not notes. Export SRT. Wrap by font pixel width, max two lines. Overlong cues must be split at a natural phrase and assigned word/audio timings, not blindly shrunk.

`captions.py` creates ASS from reviewed SRT and a font file. It highlights only explicit configured terms. Without word timestamps it does not pretend to produce word-synced karaoke. Use a separate caption band; full-screen UI can have its own reviewed position. To move captions, regenerate from the same transcript rather than rerun ASR.

Use `--regions` with explicit time intervals for alternate positions over real UI. `transcribe.py` is an optional adapter to an existing local faster-whisper model; its SRT and word timing output are drafts, never auto-approved text. The core pipeline accepts reviewed transcripts from any provider.

If a finished base already has burned-in captions, never burn a duplicate layer. Protect its caption area from replacement graphics. New caption rendering copies audio unchanged.
