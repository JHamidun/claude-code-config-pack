# Project commands and sync

## Mutation models

| Project         | Behavior                                                              |
| --------------- | --------------------------------------------------------------------- |
| Script-owned    | `build edit.jsx` creates/replaces its timeline                        |
| Existing/shared | Fresh `read`/`inspect` plus bounded `do` or `ops` changes             |
| Canonical       | Host-provided connection, ordered transactions and actor-scoped undo  |
| Legacy linked   | File pull/push; concurrent whole-file writes can overwrite each other |

```bash
higgsedit read PROJECT
higgsedit inspect PROJECT --id CLIP_ID --at 6.5
higgsedit do PROJECT --list
higgsedit do PROJECT trim --clipId CLIP_ID --start 1 --end 4
higgsedit ops PROJECT patch.json
```

`trim` changes edges in place without moving other clips; its start/end are
absolute scene seconds. `inspect --at` uses whole-project timeline seconds and
requires an ID or unambiguous name. Evaluated effects are not execution proof.
IDs/array paths can change after rebuilds; ops paths require current document state.

Other verbs include `place`, `insert_ripple`, `remove_ripple`, `broll`, `duck`,
`remove_silences`, and component placement/update. The installed `--list` and
per-verb `--help` provide parameters.

## Components and connections

`components build` compiles local modules; `component.place`, `component.patch`
and `component.update` operate on instances. [Component clocks](assembly.md).

Legacy `sync link|unlink|push|pull|clone|status|archive` manages file-backed sharing.
Canonical `sync attach` and `sync new-canonical` use supplied connection config;
legacy clone/link is not a substitute for canonical credentials.

The OpenAI tool surface has no editable-project publishing service. Local project
files are not hosted editor URLs. Canonical sync needs an explicitly supplied
connection; the skill does not supply credentials. Whole-script rebuild still
replaces the timeline.
