# Retained legacy routes

These five Python scripts preserve the previous skill's style bank, HTML management,
templates/export and cinematic prompt constructor. Their schemas differ from `exec_sketch.py`.
Do not feed a new exec-sketch manifest into a legacy script.

```sh
python -B scripts/whiteboard_generator.py styles
python -B scripts/whiteboard_generator.py recommend "business training"
python -B scripts/slide_templates.py list
python -B scripts/slide_templates.py categories
python -B scripts/build_visual_prompt.py --help
python -B scripts/build_visual_prompt.py --subject "A folder becoming an application" --still --aspect 16:9
```

HTML project: `slide_manager.py init <title> <outline.json> <new-project> html`;
`slide_manager.py state <project>`; `slide_manager.py notes <project> <slide-id> <text>`;
`slide_manager.py modify <project> <operation> <json>`.
Exporter: `slide_export.py pdf|pptx|html <project> [output]`; `screenshots <project>` writes to `<project>/screenshots/`.
Install optional requirements from `scripts/requirements-legacy.txt`; HTML screenshot export
also needs Playwright Chromium. Legacy HTML templates can request CDN Tailwind and Google Fonts.
For air-gapped work use the new exec-sketch route, or vendor those resources under appropriate licenses.

## Optional image-provider route

`whiteboard_generator.py generate <legacy-config.json> <output> [style]` and
`whiteboard_generator.py test <prompt> <output> [style]` make network calls and cost money.
In an interactive Claude Code session this is the normal AI-styles route; in unattended runs
(cron, bots, agent swarms) get explicit approval to spend on a paid key first. The SDK and the
key load lazily, only for an actual generation — `GOOGLE_API_KEY` from the environment or `~/.claude/.credentials.master.env`,
`GEMINI_API_KEY` dropped first, model `gemini-3.1-flash-image-preview` unless
`MANUS_SLIDES_MODEL` says otherwise (ladder: `~/.claude/config/models.md`). Keys never enter
manifests, prompts, artifacts or logs; provider errors are printed with the key masked.
`styles`, `recommend`, `pptx`, `notes-pptx` and `html` work without a key.

Legacy config generation may reuse files by name; legacy `pptx`/`notes-pptx` map sorted image
files by position. For new work, bind their generated images into `exec_sketch.py` and use the
strict new builder rather than those legacy packaging paths. Legacy regeneration is not atomic.
Historical catalog model names are dated observations, not verified current availability.
