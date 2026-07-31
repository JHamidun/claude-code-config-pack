# Video Montage Skill for Claude Code

Complete video editing pipeline for vertical reels (9:16, 1080x1920) — subtitles, voiceover, assembly, text reels, audio mixing, color management, and QA. Plus advanced techniques: word-accurate subtitle/card sync, pop-up dictionary cards, image sourcing (real vs AI), music-video lip-sync, platform safe zones, and anti-fingerprint uniquification for reposts.

## Installation

```bash
# Clone
git clone https://github.com/anthropics/video-montage-skill.git

# Copy into your project's skills directory
cp -r video-montage-skill/video-montage your-project/skills/
```

Or download ZIP and unpack `video-montage/` into `your-project/skills/`.

Claude Code picks up skills automatically — no restart needed.

## Requirements

- **ffmpeg** with libass and drawtext filters
- **whisper** — `pip install openai-whisper`
- **Python 3** with Pillow — `pip install Pillow`
- **yt-dlp** — `pip install yt-dlp` (for downloading reference reels)
- **ElevenLabs API key** (for TTS voiceover, optional)

## What's inside

```
video-montage/
  SKILL.md                        — full pipeline reference (Claude Code reads this)
  scripts/
    gen_subs.py                   — SRT to ASS subtitle converter (Impact / Helvetica)
    gen_text_overlay.py           — text overlay PNG generator with auto font sizing
```

## What you can ask Claude Code

**Subtitles:**
- "Add subtitles to my video"
- "Generate subs with Helvetica font"
- "There's an AI voice in the video, transcribe everything"

**Voiceover:**
- "Generate TTS voiceover for this script using ElevenLabs"
- "Split this script into segments with pauses"

**Video assembly:**
- "Combine these clips into a reel"
- "Prep this iPhone clip for editing — fix HDR and frame rate"
- "Add Ken Burns zoom to this photo"

**Text reels:**
- "Make a text reel with this quote over clip.mp4"
- "Dim the background 27% and overlay centered text"

**Audio:**
- "Add background music at 8% volume"
- "Clean up the voiceover — remove silence and stumbles"
- "Add a sound effect at the 3 second mark"

**QA:**
- "Check if subtitles are correct in the final video"
- "Verify the ending isn't cut off"

**Advanced:**
- "Sync these subtitles to the exact words in the song"
- "Add pop-up dictionary cards that land on each slang term"
- "Find a real photo/logo for each card (no AI faces)"
- "Lip-sync these phone takes to the finished track"
- "Keep everything inside the TikTok/Reels safe zone"
- "Make this repost unique so Instagram doesn't flag it as duplicate"

## Scripts — standalone usage

Each script works independently from the command line:

```bash
# Subtitles: SRT to ASS
python3 scripts/gen_subs.py input.srt output.ass --font helvetica

# Text overlay PNG
python3 scripts/gen_text_overlay.py --text "Your quote" --output overlay.png --font Impact --font-size 72
```

## License

MIT
