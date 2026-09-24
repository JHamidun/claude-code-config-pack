# Configurable design

Warm editorial studio is the approved starting point, not a compulsory brand.

- Stage: warm ivory/grey. Speaker panel slightly brighter with soft gradient.
- Paper defaults: `#F8F3EC`, ink `#171713`, muted `#69675F`, accent `#DAA400`.
- Dark defaults: `#000000`, ink `#F7F7F4`, muted `#BBBAB4`, accent `#FFD014`.
- Fonts supplied per project: readable heading, selective handwritten labels, plain captions. Never bundle Windows fonts in the skill.
- Corners around 18–26 px at 1080p; one faint edge, modest external shadow. No heavy permanent header or double bottom border.

Useful 1920×1080 content boxes x,y,w,h: split `[32,80,1280,720]`, large `[220,30,1480,832]`, diagram beside large speaker `[956,30,900,832]`. They are examples, not camera crop coordinates. Keep source proportions.

Reserve e.g. y=890–1030 for captions. Review actual UI before choosing a different safe region. Dynamics should serve meaning: speaker for personal statement, diagram for mechanism, enlarged slide for detail, real interface for clicks. A brief old-slide flash is a timeline bug, not a transition.

## Optional logos

`branding.logos: []` by default. Each entry is an authentic local image plus rectangle and optional visibility intervals. One, several or none; no logo, initials or author identity built in. Transparent PNG recommended. Preserve proportions, contrast and safe margins. Do not duplicate a mark already baked into a slide or cover controls/captions.

## Opening/ending

Frame 0 is a complete intended cover, not a blank animation state or accidental open-mouth frame. Export Preview.jpg. End on a stable summary; no half-drawn diagram or repeated audio syllable. Opening/real UI can be declared protected from overlay changes.
