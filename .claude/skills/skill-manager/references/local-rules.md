# Local scanner coverage

The local line is `leak-scan`'s `scripts/skill_injection_scan.py`: 36 rule IDs
(`--list-rules` prints the exact set), the 35 original ones plus `fs.reference_escape`.

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

`fs.reference_escape` closes a hole in the lifecycle analyzer: a `package.json`
script could point at `../outside.js` and make the scanner read outside the target.
Paths outside the target and link/junction ancestors are now rejected. The boundary
check is lexical and runs before any filesystem call: resolving the path first would
make Windows open an SMB session to a UNC host named in `package.json` (NTLM hash
exposure). The tree walk also does not descend into NTFS junctions.

skill-manager calls this scanner in place instead of keeping a copy, so a rule fix
lands in both `leak-scan` and the audit at once.

Patterns detect syntax, not intent. Documentation may describe attacks; novel
attacks can evade every rule. Vendor inclusion is enabled in the wrapper, but
scanner-internal exclusions still need inventory/closure review. Binary,
unreadable, skipped or missing source is not safe because findings are empty.
