# Kids · Talking Characters (`talking_characters: true`)

Read this only for a Kids run whose sound alternates between the narrator and the cast.
Every other run ignores this file.

Odd blocks are **narration**: the external narrator speaks and every character keeps
their mouth closed. Even blocks are **dialogue**: at most two named characters speak
inside the generated `minimax_h3` clip. Duration stays unchanged:
`blocks = ceil(requested_seconds / 10)` and the alternation continues across all blocks.

The flag changes the whole script, not only the prompts:

- Keep one chronological story. Each dialogue block must be caused by the narration
  before it and set up the narration after it. A dialogue block that can move elsewhere
  without breaking the story must be rewritten.
- Narration blocks use 17–21 words per 10 seconds. Dialogue blocks use 16–22 words total
  across all speakers so turn-taking does not create long dead air.
- A dialogue block names at most two speaking characters. Give each one turn, two only
  when essential. Never introduce knowledge or a character before the story has shown it.
- The clip's native voices are accepted for dialogue blocks. Character timbre may vary;
  keep visual identity, wardrobe, palette, and the shared delivery direction stable.
- Narration blocks receive normal fixed-window `narrator` takes. Dialogue blocks use the
  clip's own full-length audio: extract it, normalize it to −16 LUFS, and pass it to the
  assembler as that block's `voiceNN.wav`. Never center or replace dialogue audio because
  it must stay locked to the lips.
- SONG MODE and Talking Characters are mutually exclusive in one video. An explicit song
  request wins. `channel_dna.talking_characters` describes this video only and does not
  lock the next episode.
- All other Kids rules remain: four cuts, narrator/character/viewer interplay, default
  wordless music bed, the same style key, and the same asset roster.

In `script_manifest.json`, set top-level `talking_characters:true` and alternate
`block_kind:"narration"|"dialogue"` starting with narration. For a dialogue block,
`vo_line` is the combined spoken text in playback order and `speakers` lists its one or
two ordered speaker names; keep the speaker-attributed lines in the authored script. The
motion validator enforces the flag, alternation, word bands, and speaker count.
