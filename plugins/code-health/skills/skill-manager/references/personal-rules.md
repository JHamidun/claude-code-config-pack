# Personal audit coverage

The adapted scanner preserves the owner's 35 original rule IDs and adds
`fs.reference_escape`, for 36 IDs total.

- Hidden Unicode and hidden markdown/encoded payloads.
- English/Russian prompt overrides, fake system/tool messages, covert autonomy,
  memory poisoning and excessive permission declarations.
- Credential access/exfiltration shapes, suspicious sinks, encoded payloads.
- Remote execution, eval/exec, detached processes, destructive shell commands.
- Protected agent configuration writes and undeclared persistence.
- Hook registration and dangerous commands.
- MCP declarations, arbitrary commands and remote endpoints.
- npm lifecycle declarations plus bounded inspection of referenced local scripts.
- Permission-mode widening in bundled settings (`config.permission_widening`).
- Filesystem links (symlinks and NTFS junctions, never descended into) and binary artifacts requiring additional review.

The copied lifecycle analyzer previously could read ../outside.js. The Codex
adaptation rejects paths outside the target and link/junction ancestors.
Claude port, 23.09.2026: the boundary check is lexical and runs before any filesystem call — the
earlier `resolve()`-first order made Windows open an SMB session to a UNC host from package.json
(NTLM hash exposure); the tree walk also no longer descends into NTFS junctions.
Claude port: that fix now lives in the canonical scanner
`~/.claude/skills/leak-scan/scripts/skill_injection_scan.py` (36 rule IDs, see
`--list-rules`), which skill-manager calls directly instead of keeping a copy.

Patterns detect syntax, not intent. Documentation may describe attacks; novel
attacks can evade every rule. Vendor inclusion is enabled in the wrapper, but
scanner-internal exclusions still need inventory/closure review. Binary,
unreadable, skipped or missing source is not safe because findings are empty.
