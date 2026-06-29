---
name: social-intel
description: "Cross-platform social media intelligence — build a complete dossier on any person, brand, or company across LinkedIn, Instagram, TikTok, X/Twitter, Facebook, Threads, Bluesky, YouTube, Snapchat, Pinterest via Scraping API. Use when user says: досье, кто этот человек, найди соцсети, social profile, обогати контакт, due diligence, KYC check, research person, find socials."
allowed-tools: Bash, Read, Write, WebSearch
---

# Social Intel — Cross-Platform Dossier

> One `SCRAPER_API_KEY` covers all 27 platforms. Load from `~/.claude/.credentials.master.env`.

## When to Use

- "досье на [имя/компанию]" — полный сбор по всем соцсетям
- "найди соцсети [имя]" — поиск профилей
- "обогати контакт" — добавить данные к существующему лиду
- "due diligence" / "KYC" — проверка контрагента
- "кто этот человек" — быстрый lookup
- Перед звонком (в связке с `call-prep`)
- Перед outreach (в связке с `draft-outreach`)

## API Reference

```
BASE = https://api.your-scraper.example
AUTH: x-api-key: $SCRAPER_API_KEY
```

### Person Profiles (1 credit each)

| Platform | Endpoint | Input |
|----------|----------|-------|
| LinkedIn | `/v1/linkedin/profile` | `?url=https://linkedin.com/in/username/` |
| Instagram | `/v1/instagram/profile` | `?username=handle` |
| Instagram Basic | `/v1/instagram/basic-profile` | `?username=handle` |
| TikTok | `/v1/tiktok/profile` | `?username=handle` |
| X/Twitter | `/v1/twitter/profile` | `?username=handle` |
| Facebook | `/v1/facebook/profile` | `?url=https://facebook.com/username` |
| Threads | `/v1/threads/profile` | `?username=handle` |
| Bluesky | `/v1/bluesky/profile` | `?handle=user.bsky.social` |
| YouTube | `/v1/youtube/channel` | `?handle=@channelname` |
| Snapchat | `/v1/snapchat/profile` | `?username=handle` |
| Twitch | `/v1/twitch/profile` | `?username=handle` |

### Company Profiles

| Platform | Endpoint | Input |
|----------|----------|-------|
| LinkedIn Company | `/v1/linkedin/company` | `?url=https://linkedin.com/company/name/` |
| Facebook Page | `/v1/facebook/profile` | `?url=https://facebook.com/pagename` |
| YouTube Channel | `/v1/youtube/channel` | `?handle=@channelname` |
| TikTok Brand | `/v1/tiktok/profile` | `?username=brandname` |
| Instagram Brand | `/v1/instagram/profile` | `?username=brandname` |

### Link Aggregators (find all socials at once)

| Service | Endpoint | Input |
|---------|----------|-------|
| Linktree | `/v1/linktree` | `?username=handle` |
| Komi | `/v1/komi` | `?username=handle` |
| Pillar | `/v1/pillar` | `?username=handle` |
| Linkbio | `/v1/linkbio` | `?username=handle` |

### Content (recent posts)

| Platform | Endpoint | Input |
|----------|----------|-------|
| LinkedIn Posts | `/v1/linkedin/company/posts` | `?url=company_url` |
| Instagram Posts | `/v2/instagram/user/posts` | `?username=handle` |
| Instagram Reels | `/v1/instagram/user/reels` | `?username=handle` |
| TikTok Videos | `/v3/tiktok/profile/videos` | `?username=handle` |
| X Tweets | `/v1/twitter/user-tweets` | `?username=handle` |
| Facebook Posts | `/v1/facebook/profile/posts` | `?url=facebook_url` |
| Threads Posts | `/v1/threads/user/posts` | `?username=handle` |
| Bluesky Posts | `/v1/bluesky/user/posts` | `?handle=user.bsky.social` |
| YouTube Videos | `/v1/youtube/channel-videos` | `?handle=@channelname` |

## Workflow: Full Person Dossier

### Step 1: Discover handles

Start with what you have (name, email, one social link). Use WebSearch to find other profiles:

```
WebSearch("[Full Name] site:linkedin.com/in")
WebSearch("[Full Name] site:instagram.com")
WebSearch("[Full Name] site:tiktok.com")
WebSearch("[Full Name] site:twitter.com OR site:x.com")
```

If they have a Linktree/Komi — fetch that first (gives all links):
```bash
source ~/.claude/.credentials.master.env
curl -s "https://api.your-scraper.example/v1/linktree?username=HANDLE" \
  -H "x-api-key: $SCRAPER_API_KEY"
```

### Step 2: Fetch profiles (parallel)

Run all available profile fetches in parallel Bash calls:

```bash
source ~/.claude/.credentials.master.env
API="https://api.your-scraper.example"
H="x-api-key: $SCRAPER_API_KEY"

# LinkedIn
curl -s "$API/v1/linkedin/profile?url=https://linkedin.com/in/USERNAME/" -H "$H" > /tmp/si_linkedin.json &

# Instagram
curl -s "$API/v1/instagram/profile?username=HANDLE" -H "$H" > /tmp/si_instagram.json &

# TikTok
curl -s "$API/v1/tiktok/profile?username=HANDLE" -H "$H" > /tmp/si_tiktok.json &

# Twitter/X
curl -s "$API/v1/twitter/profile?username=HANDLE" -H "$H" > /tmp/si_twitter.json &

# YouTube
curl -s "$API/v1/youtube/channel?handle=@HANDLE" -H "$H" > /tmp/si_youtube.json &

wait
echo "All profiles fetched"
```

### Step 3: Synthesize dossier

Read all JSON files and create a structured report:

```markdown
# Dossier: [Full Name]
Generated: [date]

## Identity
- **Name:** [from LinkedIn]
- **Title:** [headline]
- **Company:** [current position]
- **Location:** [city, country]
- **Bio:** [most detailed bio from any platform]

## Social Presence
| Platform | Handle | Followers | Posts | Engagement |
|----------|--------|-----------|-------|------------|
| LinkedIn | /in/xxx | [connections] | [posts] | — |
| Instagram | @xxx | [followers] | [posts] | [avg likes] |
| TikTok | @xxx | [followers] | [videos] | [avg views] |
| X/Twitter | @xxx | [followers] | [tweets] | [avg engagement] |
| YouTube | @xxx | [subscribers] | [videos] | [avg views] |

## Recent Activity (last 30 days)
- [Platform]: [summary of recent content themes]
- [Platform]: [notable posts or viral content]

## Professional Background
[From LinkedIn: experience, education, skills, certifications]

## Talking Points
- [Shared interests or connections]
- [Recent achievements or announcements]
- [Content themes they care about]
```

### Step 4: Save report

```bash
mkdir -p ~/Documents/Social-Intel
# Write the dossier to a markdown file
```

## Workflow: Company Dossier

Same approach but focus on:
1. LinkedIn Company page → size, industry, description
2. All social profiles → follower counts, content frequency
3. LinkedIn Company Posts → content strategy
4. Employee profiles (key people) → decision makers
5. Ad Library (→ use `ad-spy` skill) → advertising strategy

## Credit Budget

| Dossier Type | Typical Credits |
|-------------|----------------|
| Quick lookup (1 platform) | 1 |
| Person (5 platforms) | 5-7 |
| Person + content | 10-15 |
| Company full | 15-25 |
| Company + key people | 30-50 |

## Integration Chain

| Next Step | Skill |
|-----------|-------|
| Prepare for call | `call-prep` |
| Write outreach | `draft-outreach` |
| Add to CRM | `crm` |
| Ad intelligence | `ad-spy` |
| Deep topic research | `last30days` |
| Competitive analysis | `competitive-analysis` |
| KYC/Source of Wealth | Your Wealth Advisory manual process |

## Safety

- Only public data — no login-required content
- 1 credit per API call, plan budget before batch operations
- Store results locally (`~/Documents/Social-Intel/`), not in git
- Rate limit courtesy: 1s delay between sequential calls
- Do not use for harassment, stalking, or unauthorized surveillance
