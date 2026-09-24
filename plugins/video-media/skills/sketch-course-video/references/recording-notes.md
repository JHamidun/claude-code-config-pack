# Recording and notes

Record face, mic and screen simultaneously into separate files, in semantic blocks. Clap/spoken take number for synchronization. Do not bake facecam into the only screen recording. Silent UI insert can later overlay continuous speech.

OBS: use consistent 16:9 canvas/output and FPS, not arbitrary desktop dimensions. Reset source transform, fit preserving proportions. Hide unused lower sources so slides/green background do not show through uncovered canvas. Verify real files with a 15–30 s test, not just preview. Source Record must have correct start mode, unique filenames and the right mic track; current UI/options should be rechecked.

4K30 helps reframing only if camera and concurrent recording are stable; 1080p30 is sufficient for many lessons. A higher nominal resolution does not fix light/focus. NVIDIA background replacement is usable after inspecting gestures/hair; green replacement is not stored transparency. No green clothes. Camera over light background keeps dark clothing distinct.

Notes: full ready-to-speak paragraphs, not short bullets. First slide introduces course/material, speaker slide introduces author once. Explain workspace/why/what before building even when an installer handles setup. Mark `[SCREEN]`, `[PAUSE]`, `[EDIT]` separately. Keep natural user voice.

Export UTF-8 TXT and PPTX notes. One physical line per spoken paragraph, blank lines between paragraphs; reader app wraps to window width. No hard wraps at 60/80 characters, separator rulers or repeated introductions. `media_tools.py unwrap-notes` writes a separate copy and preserves blank paragraph breaks; review stage directions.
