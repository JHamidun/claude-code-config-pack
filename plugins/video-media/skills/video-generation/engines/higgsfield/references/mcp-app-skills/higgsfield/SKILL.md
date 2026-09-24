---
name: higgsfield
description: >
  Resolve and execute named Higgsfield presets and slash commands, or browse
  Viral and Marketing Studio preset galleries. Resolve a named preset before
  loading production workflows suggested by its name, including cover or
  unboxing workflows; only returned instructions can request those helpers.
  Also route named /MODEL_NAME invocations. Ordinary model questions, media
  generation and Marketing Studio brand-kit records use direct tools.
  Mentioning Higgsfield alone, quoted/translated commands and explicitly
  negated commands are not invocations.
---

# Higgsfield presets and commands

Resolve an explicitly selected preset or command before choosing another creative workflow. A product image alone does not override the user's chosen entry.

## Browse

- Both Viral and Marketing Studio: `get_presets` without `source`.
- `/effects`: `source:"viral"`.
- `/product`: `source:"marketing_studio", category:"product-shot"`.
- `/motion`: `source:"marketing_studio", category:"motion"`.
- `/marketing-studio`: `source:"marketing_studio"`.
- Bundled recipes and commands: `get_preset_instructions` without `preset`.

Browsing does not submit jobs. The widget handles pagination; request another page only when the user asks. A catalog listing is not a resolved entry: load the chosen ID before execution.

## Resolve and follow the entry

For `/genjutsu`, resolve the named server command first; its instructions choose the motion-transfer or object-replacement model. Do not treat the family name as a concrete model ID.

For other named entries, call `get_preset_instructions` with the exact slash token before requesting media. Examples: `/hero-shot`, `/reel-cover`, `/genjutsu`, `/use-after-effects`. Read references only when the returned instructions require them.

- **Recipe:** follow its prompt, supported customization and generation workflow. Do not substitute a generic photoshoot or reinterpret the master prompt.
- **Workflow:** follow the selected instructions and their required tools; collect missing inputs before submitting.
- **Setup or instructions:** use the required environment. A cloud sandbox cannot install or control a desktop application. Loading instructions does not install software or prove a connection; respect the user's requested setup/editing scope and verify any claimed connection.
- **Gallery entry:** the text response includes its input schema and exact detail lookup. Map relevant attachments to unambiguous slots, upload each once, then call `get_presets` once with source, preset_id and any initial_inputs. Leave missing fields for the widget. A bare gallery slash, preview or browse request opens the detail only. Generate only when the user requests it or uses Recreate. Check input readiness; available capability is not permission. Never send catalog IDs to ordinary generate_image or generate_video.

When a token unambiguously names a supported generation model, use the matching generation tool with the user's brief and media. Resolve unfamiliar model IDs through `models_search` and `models_get`. A bare model name is not a generation brief: collect the subject or prompt and required media before submitting.

A `not_found` result means the token is a plain-language hint, not a blocker: infer the intended output from the token, the request, attached media and the conversation, then complete it with ordinary tools and sensible defaults. Do not say the preset or command does not exist or ask the user to pick another one; never pass the token as a preset, catalog or model ID. Ask only when no outcome can be inferred, and ask about the outcome, not the command.

## Deliver once

For ordinary generate_* results, use the auto-updating generation widget and `jobs_wait` with `timeout_seconds:15`; do not open a duplicate display unless requested.

After execute_preset or a widget message with submitted job IDs, never execute again. For one job, use job_display and jobs_wait. For multiple jobs, wait in groups of at most eight and display the complete indexed set with show_generation_by_ids (up to 24 per call). Preserve returned order; do not use history to rediscover these jobs. A timeout can leave submission unknown: do not repeat an action merely because its response was lost.
