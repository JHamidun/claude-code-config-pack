# Implementation and distribution boundary

This toolkit packages a reusable recorded-course editing workflow. It has no dependency on any particular lesson project or conversation history.

- Drawing engine: `assets/remotion/SketchPanel.tsx`.
- Stroke extraction and reveal masks: `scripts/trace.py` and `scripts/prepare.py`.
- Raw edits, composition and verification: `scripts/raw_edit.py`, `scripts/compose.py`, `scripts/qa.py`.
- Reusable illustration prompt and visual rules: `references/animation.md`.
- Generic project and scene templates: `scripts/project.py`.

These are bundled implementation files, not links to private project folders. Lesson-specific coordinates, timestamps and identities are not defaults. No personal recordings, logos, portraits, credentials, node_modules or proprietary fonts are bundled. Media, fonts and optional branding are supplied separately for each job.

Scripts automate execution of an explicit edit map, stroke extraction, frame-driven panels, composition, caption formatting, bounded batches and technical verification. Take selection, new art generation, semantic cuts, transcript corrections and perceptual A/V judgment still require editorial work. Do not promise autonomous content understanding from deterministic scripts.
