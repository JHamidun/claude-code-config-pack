---
description: Draft blog posts, social media, email newsletters, landing pages, press releases, and case studies
argument-hint: "<content type and topic>"
---

# Draft Content

> If you see unfamiliar placeholders or need to check which tools are connected, see [CONNECTORS.md](../CONNECTORS.md).

Generate marketing content drafts tailored to a specific content type, audience, and brand voice.

## Trigger

User runs `/draft-content` or asks to draft, write, or create marketing content.

## Inputs

Gather the following from the user. If not provided, ask before proceeding:

1. **Content type** — one of:
   - Blog post
   - Social media post (specify platform: LinkedIn, Twitter/X, Instagram, Facebook)
   - Email newsletter
   - Landing page copy
   - Press release
   - Case study

2. **Topic** — the subject or theme of the content

3. **Target audience** — who this content is for (role, industry, seniority, pain points)

4. **Key messages** — 2-4 main points or takeaways to communicate

5. **Tone** — e.g., authoritative, conversational, inspirational, technical, witty (optional if brand voice is configured)

6. **Length** — target word count or format constraint (e.g., "1000 words", "280 characters", "3 paragraphs")

## Brand Voice

- If the user has a brand voice configured in their local settings file, apply it automatically. Inform the user that brand voice settings are being applied.
- If no brand voice is configured, ask: "Do you have brand voice guidelines you'd like me to follow? If not, I'll use a neutral professional tone."
- Apply the specified or default tone consistently throughout the draft.

## Content Generation by Type

### Blog Post

- Engaging headline (provide 2-3 options)
- Introduction with a hook (question, statistic, bold statement, or story)
- 3-5 organized sections with descriptive subheadings
- Supporting points, examples, or data references in each section
- Conclusion with a clear call to action
- SEO considerations: suggest a primary keyword, include it in the headline and first paragraph, use related keywords in subheadings

### Social Media Post

- Platform-appropriate format and length
- Hook in the first line
- Hashtag suggestions (3-5 relevant hashtags)
- Call to action or engagement prompt
- Emoji usage appropriate to brand and platform
- If LinkedIn: professional framing, paragraph breaks for readability
- If Twitter/X: concise, punchy, within character limit
- If Instagram: visual-first language, story-driven, hashtag block

### Email Newsletter

- Subject line (provide 2-3 options with open-rate considerations)
- Preview text
- Greeting
- Body sections with clear hierarchy
- Call to action button text
- Sign-off
- Unsubscribe note reminder

### Landing Page Copy

- Headline and subheadline
- Hero section copy
- Value propositions (3-4 benefit-driven bullets or sections)
- Social proof placeholder (suggest testimonial or stat placement)
- Primary and secondary CTAs
- FAQ section suggestions
- SEO: meta title and meta description suggestions

### Press Release

- Headline following press release conventions
- Dateline and location
- Lead paragraph (who, what, when, where, why)
- Supporting quotes (provide placeholder guidance)
- Company boilerplate placeholder
- Media contact placeholder
- Standard press release formatting

### Case Study

- Title emphasizing the result
- Customer overview (industry, size, challenge)
- Challenge section
- Solution section (what was implemented)
- Results section with metrics (prompt user for data)
- Customer quote placeholder
- Call to action

## SEO Considerations (for web content)

For blog posts, landing pages, and other web-facing content:

- Suggest a primary keyword based on the topic
- Recommend keyword placement: headline, first paragraph, subheadings, meta description
- Suggest internal and external linking opportunities
- Recommend a meta description (under 160 characters)
- Note image alt text opportunities

## Output

Present the draft with clear formatting. After the draft, include:

- A brief note on what brand voice and tone were applied
- Any SEO recommendations (for web content)
- Suggestions for next steps (e.g., "Review with your team", "Add customer quotes", "Pair with a visual")

Ask: "Would you like me to revise any section, adjust the tone, or create a variation for a different channel?"

## Template Library

Use these structural templates as the backbone for each content type. Adapt length and depth to the user's requirements.

### Blog Post Template (800-1500 words)

```text
1. HOOK (1-2 sentences)
   - Open with a surprising statistic, provocative question, or bold claim
   - Goal: stop the scroll, earn the next paragraph

2. PROBLEM (150-250 words)
   - Describe the pain point the reader recognizes
   - Use "you" language to create identification
   - Agitate: show consequences of inaction

3. SOLUTION (400-800 words)
   - Present the approach, framework, or product
   - Break into 3-5 subheadings with actionable detail
   - Include examples, data, or mini case studies
   - Use bullet points for scannability

4. CTA (50-100 words)
   - Summarize the key takeaway in one sentence
   - Single clear next action: download, sign up, contact, share
   - Optional: secondary CTA (subscribe, read related post)
```

### Social Media Template

**Twitter/X (max 280 characters):**

```text
HOOK — one punchy line that earns the click or retweet
VALUE — the insight, stat, or tip (compressed)
CTA — "Reply with yours", "Link in bio", "RT if you agree"
```

**Instagram (max 2200 characters caption):**

```text
HOOK — first line visible before "...more" (front-load value)
VALUE — 3-5 short paragraphs, line breaks between each
STORY — personal angle or customer story
CTA — ask a question, "Save this for later", "Tag someone who needs this"
HASHTAGS — block of 15-25 at the end or in first comment
```

**LinkedIn (max 3000 characters):**

```text
HOOK — bold first line, then line break
STORY/INSIGHT — 3-6 short paragraphs with white space
TAKEAWAY — numbered list or single bold statement
CTA — "Agree? Disagree? Drop your take below."
```

### Email Newsletter Template

```text
SUBJECT LINE — 6-10 words, curiosity or benefit-driven, avoid spam triggers
   Provide 3 options: (A) curiosity gap, (B) benefit-first, (C) urgency/FOMO

PREVIEW TEXT — 40-90 characters, complements (not repeats) the subject line

BODY:
  1. Opening hook (1-2 sentences, personal or timely)
  2. Main content block (the value: insight, tutorial, announcement)
  3. Supporting block (secondary story, curated links, quick tip)
  4. CTA — single primary button, benefit-oriented label
  5. Sign-off — brief, human, consistent with brand voice

FOOTER — unsubscribe link, address, social links
```

### Landing Page Template

```text
ABOVE THE FOLD:
  HEADLINE — 6-12 words, benefit-driven, specific
  SUBHEADLINE — 15-25 words, clarify what + for whom + outcome
  PRIMARY CTA — button with action verb + benefit ("Start free trial")
  HERO VISUAL — suggest image/video direction

BENEFITS SECTION:
  3-4 blocks, each: icon + heading + 1-2 sentence description
  Focus on outcomes, not features

SOCIAL PROOF:
  Testimonial quotes (name, role, company, photo)
  Logos of known clients
  Metrics: "X+ users", "Y/5 rating", "Z% uptime"

HOW IT WORKS:
  3 steps: simple numbered process

OBJECTION HANDLING:
  FAQ accordion (5-7 common questions)

FINAL CTA:
  Repeat headline benefit + CTA button
  Optional: secondary CTA ("Book a demo" vs "Start free")
```

### Press Release Template

```text
HEADLINE — factual, newsworthy, no hype adjectives
  Format: [Company] [Action Verb] [What] to [Benefit/Impact]

DATELINE — CITY, State/Country (Date) --

LEAD PARAGRAPH (who, what, when, where, why):
  One paragraph, 2-3 sentences, covers all 5 W's
  Most important information first (inverted pyramid)

BODY:
  Para 2: expand on the "why" — context, market need, problem solved
  Para 3: quote from company executive (name, title, company)
  Para 4: details — features, availability, pricing, partnerships
  Para 5: quote from partner, customer, or analyst (social proof)
  Para 6: future outlook or next steps

BOILERPLATE:
  "About [Company]" — 3-4 sentences: what, founded, mission, key metric
  Website URL

MEDIA CONTACT:
  Name, Title, Email, Phone
```

## Brand Voice Auto-Fetch

Before generating any content, resolve brand voice settings in this priority order:

1. **Local config file** — check `~/.claude/config/brand-voice.json`

   Expected schema:

   ```json
   {
     "brand_name": "Company",
     "tone": ["authoritative", "approachable"],
     "vocabulary": { "prefer": ["solution", "platform"], "avoid": ["synergy", "disrupt"] },
     "sentence_style": "short, direct, active voice",
     "emoji_policy": "minimal | none | liberal",
     "formality": "semi-formal"
   }
   ```

   If found, apply silently and note in the output footer: "Brand voice applied from config."

2. **Notion MCP** — if local config is absent, query Notion MCP for a page titled "Brand Voice" or "Brand Guidelines"
   - Extract tone, vocabulary, and style directives
   - If found, apply and note: "Brand voice fetched from Notion."

3. **Fallback** — if neither source is available, ask the user:
   > "No brand voice config found. Please describe your preferred tone (e.g., professional, playful, technical) or I will use a neutral professional tone."

When brand voice is resolved, enforce it across:

- Word choice (prefer/avoid lists)
- Sentence length and structure
- Emoji and punctuation style
- Level of formality and jargon

## SEO Integration

Apply SEO optimization for all web-facing content (blog posts, landing pages, case studies).

### Keyword Strategy

- **Primary keyword**: suggest one based on topic; place in headline, first paragraph, one subheading, meta description, and URL slug
- **Secondary keywords**: suggest 2-3 related/long-tail variations; distribute naturally across subheadings and body paragraphs
- **Keyword density**: aim for 1-2% for primary, mention secondaries 1-2 times each

### SERP Research

Before drafting blog posts and landing pages:

- Use WebSearch or Firecrawl MCP to check the current top 5-10 results for the target primary keyword
- Note content gaps (topics competitors miss) and content patterns (formats that rank)
- Report findings to the user as a brief "SERP snapshot" before drafting:

```text
SERP Snapshot for "[keyword]":
- Top results focus on: [themes]
- Average word count: ~[N] words
- Content gap opportunity: [what is missing]
```

### Meta Tags

Include at the end of web content drafts:

```text
SEO Metadata:
  Title tag: [50-60 chars, primary keyword near the front]
  Meta description: [150-160 chars, includes primary keyword, ends with CTA or benefit]
  URL slug: /[lowercase-hyphenated-keyword]
  Open Graph title: [can match or vary from title tag]
  Open Graph description: [slightly more casual than meta description]
```

### Readability

- Target **Flesch-Kincaid Grade Level 8-10** (accessible to a broad audience)
- Short paragraphs (2-4 sentences max)
- Use transition words between sections
- Prefer active voice over passive
- Break up walls of text with subheadings, bullets, bold keywords
- If the draft reads above grade 10, simplify: shorter sentences, simpler words, fewer subordinate clauses
