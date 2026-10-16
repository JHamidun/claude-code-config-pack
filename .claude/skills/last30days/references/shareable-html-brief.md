# Shareable HTML brief

How to produce the standalone HTML brief.
**Read only when the user asked for a shareable brief / HTML file.** Companion: `references/save-html-brief.md`.

## SHAREABLE HTML BRIEF (when the user asked for one)

**This section fires if EITHER prompt-level trigger is true:**

- The user included an HTML-looking argument such as `--emit=html`, `--emit:html`, or `--html` in the skill prompt. Treat this as a strong user intent signal for HTML; do not confuse it with the complete Python CLI contract.
- The user's natural-language request asks for an HTML brief, shareable doc, or file for sharing (Slack, email, Notion, "give it to me in HTML", "export as HTML", etc). Use your judgment for phrasing variants; a literal flag is not required.

**If neither trigger fires, skip this entire section and proceed to WAIT FOR USER'S RESPONSE.** No HTML save flow, no reference read needed.

**When triggered, you MUST:**

- Read `references/save-html-brief.md` BEFORE proceeding to WAIT FOR USER'S RESPONSE
- Follow that file's instructions exactly - it is the canonical source for the save flow
- End with the artifact handoff defined there: saved HTML path, open the local file when the host can do so, and a concise confirmation for requests where HTML is the requested deliverable
- If the user explicitly asks for a hosted/shareable web link, follow the opt-in publishing instructions in the reference file. Never publish by default.

**You MUST NOT:**

- Improvise the HTML save flow from memory or from instructions you've seen before
- Skip the reference read because the steps "look familiar"
- Save to a different path than the reference specifies
- Add data quality warnings, debug headers, or safety notes to the saved HTML
- Re-research the topic for the HTML render - the engine cache covers the second invocation
- Upload or publish the HTML to a third-party host unless the user explicitly asked for hosted sharing and you have told them the link may be public/indexed unless password-protected

**Why the directive is forceful:** the reference file is the only source of truth for the save flow. Skipping it produces broken artifacts - wrong path conventions, missing synthesis content, leaked engine debug output, or warnings that don't belong in shareable docs.

---

