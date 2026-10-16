---
name: content-engine
description: "Platform-native контент из одного исходника под X, LinkedIn, Threads, Bluesky, TikTok, YouTube, рассылку. Триггеры: «контент для соцсетей», «кросспост». Публикация → postiz."
origin: ECC
---

# Content Engine

One source, many surfaces — platform-native content that does not flatten the author's voice into
platform slop, and does not ship the same fake post in four costumes.

## When to Activate

- X posts or threads, LinkedIn posts, launch updates, newsletter issues
- scripts for short-form video or YouTube explainers
- repurposing articles, podcasts, demos, docs, or internal notes into public content
- a launch sequence or content system around a product, insight, or narrative
- the user says "crosspost", "post this everywhere", or "adapt this for X and LinkedIn"

## Non-Negotiables

1. Start from source material, not generic post formulas.
2. Adapt for the platform's constraints, not its stereotypes — format changes, persona does not.
3. One post carries one actual claim.
4. Never ship identical copy on two platforms.
5. Specificity beats adjectives.
6. No engagement bait, CTA, question, or moral unless the source earned it or the user asks.

## Voice Handling

`brand-voice` is the canonical voice layer. Run it first when there are multiple downstream
outputs, when the user explicitly cares about style, or when the content is launch, outreach, or
reputation-sensitive — including for your brand voice.

Reuse the resulting `VOICE PROFILE` instead of building a second voice model or a per-platform ad
hoc checklist. Two voice models drift apart, and the drift shows up as the author sounding like a
different person on each platform. Override only if the user asks for a fresh one this campaign.

## Hard Bans

Delete and rewrite any of these:
- "In today's rapidly evolving landscape"
- "game-changer", "revolutionary", "cutting-edge"
- "Excited to share"
- "here's why this matters" unless it is followed immediately by something concrete
- generic "professional takeaway" or "here's what I learned" paragraphs absent from the source
- a reply-farming closing question ("What do you think?") added because the platform expects one
- forced casualness on LinkedIn
- "link in bio" unless that is literally true
- fake engagement padding that was not present in the source material

## Platform Adaptation Rules

### X

- open with the strongest claim, artifact, or tension
- keep the compression if the source voice is compressed
- use a thread only when one post would collapse the argument; then each post must advance it
- no hashtags, no padding with context the audience does not need

### LinkedIn

- expand only enough for people outside the immediate niche to follow
- no fake lesson or founder-reflection framing unless the source really is reflective; no corporate
  inspiration cadence, no praise-stacking, no "journey" filler
- do not sand the author into a polished "professional tone" if they are naturally sharper

### Threads

- keep it readable and direct
- no fake hyper-casual creator copy; do not paste the LinkedIn version and shorten it

### Bluesky

- keep it concise, preserve the author's cadence
- no hashtags, no feed-gaming language

### Short Video

- script around the visual sequence and proof points
- first seconds should show the result, problem, or punch
- do not write narration that sounds better on paper than on screen

### YouTube

- show the result or tension early
- organize by argument or progression, not filler sections
- use chaptering only when it helps clarity

### Newsletter

- open with the point, conflict, or artifact; do not warm up for a paragraph
- every section needs to add something new

## Repurposing Flow

1. Pick the anchor: the strongest item in the source set — articles and essays, the original X post
   or thread, launch notes, changelogs, docs, internal memos, demos, transcripts, screenshots,
   prior posts from the same author.
2. Extract 3 to 7 atomic claims or scenes.
3. Rank them by sharpness, novelty, and proof.
4. Assign one strong idea per output.
5. Adapt structure for each platform, strip platform-shaped filler.
6. Run the quality gate.

## Deliverables and Posting Order

Return: a short voice profile if voice matching matters; the core angle; platform-native drafts,
strongest native version first, then the secondary platforms; a note on what changed per platform
and why; posting order and staggered timing only if the user wants sequencing help; gaps and
publishing constraints to resolve before publishing.

Do not add cross-platform references unless useful. Most of the time a post should stand on its own.

## Quality Gate

Before delivering:
- every draft sounds like the intended author, not the platform stereotype, and every version reads
  like the same author under different constraints
- every draft contains a real claim, proof point, or concrete observation
- nothing from Hard Bans survived; no version feels padded or sanitized
- no copy is duplicated verbatim across platforms unless requested
- extra context added for LinkedIn or the newsletter is actually necessary
- any CTA is earned and user-approved

## Related Skills

- `brand-voice` — voice profiles; `social-intel` — сбор свежих постов автора
- `postiz` — ДЕФОЛТНАЯ публикация (14 платформ), одобренные версии отдавай туда; `publora-post` —
  только эксклюзивы Publora: LinkedIn-аналитика/реакции/комменты, Telegram; свой Telegram-бот — `tg-bot-publish`
- `tg-post` / `linkedin-post-author` — когда текст должен быть именно голосом пользователя (RU)
