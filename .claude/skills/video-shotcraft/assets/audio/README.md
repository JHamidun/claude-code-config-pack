# Audio assets (bgm/, sfx/) are not shipped with this plugin

The bundled background-music (`bgm/`) and sound-effects (`sfx/`) libraries (~36 MB of mp3)
are excluded from the distribution to keep the plugin small.

To use sound-design features, supply your own files:

- `bgm/` — a few royalty-free music tracks (see AUDITION-2026-07-27.md for the vibe map)
- `sfx/` — whooshes, clicks, risers etc. (see ATTRIBUTION.md for the original sources —
  all were downloaded from free libraries and can be re-fetched from there)

Scripts look these folders up by relative path, so just drop files in and re-run.
