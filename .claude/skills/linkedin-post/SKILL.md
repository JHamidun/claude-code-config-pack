---
name: linkedin-post
description: Create and schedule LinkedIn posts with text, images, videos, and documents via your social MCP
---

# LinkedIn Post

Create and schedule LinkedIn posts using the your social MCP server. Supports text posts, single images, multi-image posts (grid layout), videos, and PDF documents.

## Prerequisites

**Plans:** Starter (free), Pro, Premium - LinkedIn is available on all plans including free.

### Getting Started

1. **Create account** at [your-publisher.example/register](https://your-publisher.example/register) (free)
2. **Connect LinkedIn** via OAuth in [SocialPublisher Dashboard](https://your-publisher.example/dashboard)
3. **Get API key** at [your-publisher.example/settings/api](https://your-publisher.example/settings/api)
4. **Configure MCP** in Claude Desktop (`~/.claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "social-poster": {
      "type": "http",
      "url": "https://mcp.your-publisher.example",
      "headers": {
        "Authorization": "Bearer YOUR_API_KEY"
      }
    }
  }
}
```

### REST API Fallback

If the MCP server is unavailable or returns errors, use the REST API directly:

**Base URL:** `https://api.your-publisher.example/api/v1`

**Authentication:** Use `x-social-poster-key` header (NOT `Authorization: Bearer`):

```bash
# Get your connected platforms
curl -X GET "https://api.your-publisher.example/api/v1/platform-connections" \
  -H "x-social-poster-key: sk_your_api_key"

# Create a post
curl -X POST "https://api.your-publisher.example/api/v1/create-post" \
  -H "x-social-poster-key: sk_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "platforms": ["linkedin-Tz9W5i6ZYG"],
    "content": "Your post content here",
    "scheduledTime": "2026-03-25T10:00:00Z"
  }'
```

**Platform ID Format:** `linkedin-{id}` where `{id}` is from `/platform-connections` response.

Example IDs: `linkedin-Tz9W5i6ZYG`, `linkedin-abc123xyz`

📖 **Full API documentation:** [docs.your-publisher.example](https://docs.your-publisher.example)

### Plan Limits

| Plan | Posts/month | Price |
|------|-------------|-------|
| Starter | 15 | Free |
| Pro | 100/account | $2.99/account/month |
| Premium | 500/account | $9.99/account/month |

## Platform Limits

| Feature | Limit |
|---------|-------|
| Characters | 3,000 max |
| Visible before "see more" | First 210 characters |
| Images | Up to 10 (grid layout, not swipeable carousel) |
| Image size | 5 MB max |
| Image formats | JPEG, PNG, GIF, WebP (WebP auto-converted) |
| Video duration | 30 minutes |
| Video size | 500 MB max |
| Video format | MP4 only |

## Available Tools

### create_post
Create a new LinkedIn post or schedule for later.

**Parameters:**
- `platforms`: Array including your LinkedIn connection ID (e.g., `["linkedin-abc123"]`)
- `content`: Post text (up to 3,000 characters)
- `scheduledTime`: ISO 8601 datetime (**required** - for immediate posting, use current time + 1 minute)

### get_upload_url
Get a presigned URL to upload media.

**Parameters:**
- `postGroupId`: The post ID to attach media to
- `fileName`: File name (e.g., "chart.png")
- `contentType`: MIME type (e.g., "image/jpeg", "video/mp4", "application/pdf")
- `type`: "image" or "video"

### list_posts / update_post / delete_post
Manage your scheduled and draft posts.

## Mentioning People and Companies

LinkedIn posts support @mentions using URN syntax:

```
@{urn:li:person:MEMBER_ID|Display Name}       # Mention a person
@{urn:li:organization:ORG_ID|Company Name}    # Mention a company
```

**Example:**
```
Great insights from @{urn:li:person:YOUR_LINKEDIN_PERSON_ID|Author} at @{urn:li:organization:YOUR_LINKEDIN_ORG_ID|Your Company Inc}!
```

**Important:** The display name must exactly match the LinkedIn profile name (case-sensitive), including company suffixes like "Inc", "LLC", etc.

## Important API Restrictions

1. **No organic carousels**: Swipeable multi-image carousels are NOT available via API (only for sponsored content). Multi-image posts appear as a grid layout.

2. **No mixed media**: Cannot combine images with videos or documents in the same post.

3. **No rich text**: LinkedIn API does not support bold, italic, or other formatting. Use plain text or Unicode characters for emphasis.

4. **PDF alternative for carousels**: To share multi-page swipeable content, upload a PDF document instead.

## Examples

### Simple Text Post
```
Schedule a LinkedIn post for tomorrow at 9 AM:
"We're thrilled to announce the release of our AI writing assistant. After 18 months of development, we're ready to help teams write better content faster."
```

### Post with Mention
```
Create a LinkedIn post mentioning our CEO:
"Excited to share insights from @{urn:li:person:YOUR_LINKEDIN_PERSON_ID|Author} on the future of AI in content creation."
```

### Multi-Image Post
```
Create a LinkedIn post with 4 product screenshots showing our new dashboard features.
```
Note: Images will appear in a grid layout, not as a swipeable carousel.

### PDF Document Post
```
Share our Q4 report as a PDF on LinkedIn with a summary caption.
```
This is the best way to share multi-page carousel-like content.

## Best Practices

1. **First line matters**: First 210 characters appear before "see more" - make them compelling
2. **Optimal length**: Posts under 1,300 characters tend to perform better
3. **Posting times**: Tuesday-Thursday, 8-10 AM in your audience's timezone
4. **Hashtags**: Use 3-5 relevant hashtags - they're supported as plain text
5. **Engagement**: End with a question to encourage comments

## Troubleshooting

| Error | Cause | Solution |
|-------|-------|----------|
| "Account not connected" | LinkedIn OAuth expired | Reconnect in SocialPublisher dashboard |
| "MEDIA_ASSET_PROCESSING_FAILED" | File too large or wrong format | Check: images < 5 MB, videos < 500 MB MP4 |
| "Rate limited" (429) | Too many API calls | Wait and retry with backoff |
| "Cannot mix media types" | Images + video in same post | Use only one media type per post |
| MCP unavailable | Server issue | Use REST API fallback (see above) |

---

## Comments, Replies & Reactions (REST)

Тот же `SOCIAL_POSTER_API_KEY` покрывает не только посты, но и комменты с реакциями. URL-парсер и готовые Python-обёртки лежат в `${WORKSPACE}/tools/linkedin-skills/lib/`.

### URL → URN parser

LinkedIn использует 3 типа URN: `activity`, `share`, `ugcPost`. URL-форматы тоже три. Парсер их нормализует:

```bash
# Один файл, без зависимостей кроме stdlib
python ${WORKSPACE}/tools/linkedin-skills/lib/url_parser.py \
  "https://www.linkedin.com/posts/dharmesh_activity-7448808898326654978-iW20"

# Output:
# {
#   "post_activity_id": "7448808898326654978",
#   "post_urn": "urn:li:activity:7448808898326654978",
#   "comment_id": null,
#   "comment_urn": null,
#   "url_type": "post"
# }
```

URL коммента (`?commentUrn=urn%3Ali%3Acomment%3A%28activity%3APOST%2CCOMMENT%29`) парсится в полный комплект `post_urn + comment_id + comment_urn`.

### POST /linkedin-comments

```bash
curl -X POST "https://api.your-publisher.example/api/v1/linkedin-comments" \
  -H "x-social-poster-key: $SOCIAL_POSTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "postedId": "urn:li:activity:7448808898326654978",
    "message": "Concrete take + a question that earns a reply.",
    "platformId": "linkedin-Tz9W5i6ZYG"
  }'
```

**Лимит:** 1,250 символов на коммент. Поддержка @mentions через `@{urn:li:person:ID|Name}`.

### POST /linkedin-comments — reply на коммент

LinkedIn flattens thread to **2 уровня**. Если отвечаешь на ответ — `parentComment` всё равно ссылается на **top-level коммент**, не на reply, иначе API ругнётся.

```bash
curl -X POST "https://api.your-publisher.example/api/v1/linkedin-comments" \
  -H "x-social-poster-key: $SOCIAL_POSTER_API_KEY" \
  -d '{
    "postedId": "urn:li:activity:7448808898326654978",
    "message": "Reply text",
    "platformId": "linkedin-Tz9W5i6ZYG",
    "parentComment": "urn:li:comment:(urn:li:activity:7448808898326654978,7449095071892672512)"
  }'
```

### POST /linkedin-reactions

Валидные типы: `LIKE`, `PRAISE`, `EMPATHY`, `INTEREST`, `APPRECIATION`, `ENTERTAINMENT`.

⚠️ **`INSIGHTFUL` НЕ валиден** в your social API — маппится в `INTEREST` автоматически в Python-клиенте, но если шлёшь `curl` напрямую — используй сразу `INTEREST`.

```bash
curl -X POST "https://api.your-publisher.example/api/v1/linkedin-reactions" \
  -H "x-social-poster-key: $SOCIAL_POSTER_API_KEY" \
  -d '{
    "postedId": "urn:li:activity:7448808898326654978",
    "platformId": "linkedin-Tz9W5i6ZYG",
    "reactionType": "INTEREST"
  }'
```

### DELETE /linkedin-comments

```bash
curl -X DELETE "https://api.your-publisher.example/api/v1/linkedin-comments" \
  -H "x-social-poster-key: $SOCIAL_POSTER_API_KEY" \
  -d '{"postedId": "...", "commentId": "...", "platformId": "..."}'
```

### Готовый Python wrapper

```python
import sys
sys.path.insert(0, "${WORKSPACE}/tools/linkedin-skills")
from lib import SocialPublisherClient, parse_linkedin_url

parsed = parse_linkedin_url("https://www.linkedin.com/posts/dharmesh_activity-7448808898326654978-iW20")
client = SocialPublisherClient()  # берёт SOCIAL_POSTER_API_KEY из env
client.create_reaction(
    post_urn=parsed["post_urn"],
    platform_id="linkedin-Tz9W5i6ZYG",
    reaction_type="INTEREST",
)
client.create_comment(
    post_urn=parsed["post_urn"],
    message="Sharp comment with a question.",
    platform_id="linkedin-Tz9W5i6ZYG",
)
```

### Best practice — react before comment

Посты, которые сначала получают реакцию автора, а потом коммент — выше в feed автора. Pause 8-15 секунд между реакцией и комментом, чтобы это не выглядело как боттинг. Готовый CLI:

```bash
python ${WORKSPACE}/tools/linkedin-skills/scripts/post_comment.py \
  "<POST_URL>" "<COMMENT_TEXT>" --reaction INTEREST
```

### URN fallback при 404

Иногда `url_parser` возвращает `urn:li:activity:...`, а каноничный URN на бэке — `urn:li:ugcPost:...`. Если POST падает с 404:
1. Через HarvestAPI/ScraperVendor дотянуть `/linkedin/post-comments` для этого поста.
2. Из любого существующего коммента взять поле `postId` — это и есть каноничный URN.
3. Повторить POST с правильным URN.

### Связанные скиллы

- `linkedin-comment-drafter` — драфтит коммент с 7 проверенными паттернами и approval-картой
- `linkedin-reply-handler` — корректно обрабатывает 2-level flattening для replies
- `linkedin-thread-engagement` — мониторит твои комменты на ответ автора (6-24h PublicAuthor3 window)
