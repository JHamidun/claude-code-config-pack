# Provenance and licenses

skill-manager combines material from several upstream sources. Each keeps its own
license; the pack's own MIT license covers only the pack's original parts.

## NVIDIA SkillSpector (Apache-2.0)

- Upstream: https://github.com/NVIDIA/SkillSpector
- Pinned commit: d162d9b343e559be13df8ebba093df3bc9d58c90 (package 2.11.2)
- Skill: `skills/skill-inspector/SKILL.md`,
  SHA256 89ab1550769752ffbad782ee63fee3c345d546bded672adaac5fd03d2941aa84
- License: Apache-2.0, bundled as `LICENSE` in this folder.
- `references/nvidia-upstream.md` is the original skill, kept verbatim for comparison
  and attribution only, not as additional execution instructions.
- Adapted from it: the review workflow, semantic-review checklist and APPROVE /
  CAUTION / REJECT rubric in `references/audit.md`.
- Changes (this list is the Apache-2.0 notice of modification): a second static line
  (the local `leak-scan` rules); the wrapper `scripts/audit_skill.py` running both
  lines; `scripts/nvidia_static.py` running the SkillSpector CLI with Python-level
  network blocking; credential-stripped child environment; sanitized reports without
  raw snippets; conservative completeness handling (a missing, timed-out or partial
  line is never reported clean); runtime location configurable via
  `SKILLSPECTOR_HOME`; report language policy.
- SkillSpector itself is not bundled. It is installed separately into an isolated
  venv (`references/skillspector-setup.md`); `references/runtime-lock.txt` records
  the dependency set of a known working install.
- Not endorsed by NVIDIA and not a security certification.

## Matt Pocock, ask-matt (MIT)

- Upstream: https://github.com/mattpocock/skills/tree/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/ask-matt
- License: MIT, bundled as `LICENSE-MATT` in this folder.
- Adapted in `references/routing.md`: situation branches, phase boundary and the
  recommend-and-stop rule are kept. The handwritten map of one author's skills is
  replaced by the local inventory plus public catalogs; fixed context thresholds,
  automatic delegation/context clearing, the global setup prerequisite and
  assumptions about installed skills are removed.

## Vercel Labs find-skills and skills.sh

- Upstream: https://github.com/vercel-labs/skills/tree/main/skills/find-skills,
  catalog https://skills.sh (repository license: MIT).
- Only discovery concepts are adapted in `references/discovery.md`; no text or code
  is copied, and the `npx skills` CLI is not bundled.

## SkillsMP

- Community skill catalog https://skillsmp.com with an MCP endpoint
  https://skillsmp.com/mcp. Nothing from it is bundled; the pack does not configure
  it. Users who want it add the server themselves (`references/discovery.md`); the
  service's own terms apply.

## This pack

- The local static line is the pack's `leak-scan` scanner
  (`leak-scan/scripts/skill_injection_scan.py`), called in place rather than copied.
  Its idea and part of its rules come from `virgiliojr94/book-to-skill`
  (`tools/scan_generated_skill.py`), as noted in `leak-scan`.
- The pack's former `skill-audit` skill was merged into `references/audit.md`;
  `skill-audit` stays as a pointer stub so old references keep working.

## Maintenance

Keep SkillSpector commit-pinned. Review an upstream update (diff, license, new
dependencies) before rebuilding the venv, audit known fixtures with the new build,
then update the pinned commit here, in `skillspector-setup.md` and in
`runtime-lock.txt`. Never update during an ordinary audit.
