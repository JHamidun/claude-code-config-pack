"""Detect which publishing backend is configured and format user-facing messages.

The skills support **hybrid** backends — different backends for different ops:

  POSTS (linkedin-post-writer, content-planner, employee-advocacy):
    Tier 0 — manual: no env, output draft for copy-paste
    Tier 1a — postiz: POSTIZ_API_KEY set → self-hosted, free, unlimited
    Tier 1b — publora: PUBLORA_API_KEY + LINKEDIN_PLATFORM_ID → SaaS, 15/month free
    Tier 2 — diy: LINKEDIN_SKILLS_CUSTOM_POSTER → user-built poster

  ENGAGEMENT (linkedin-comment-drafter, reply-handler, thread-engagement):
    Tier 0 — manual: copy-paste
    Tier 1 — publora: comments + reactions on any LinkedIn URL
    Tier 2 — diy: LINKEDIN_SKILLS_CUSTOM_POSTER

  Postiz CANNOT do engagement (comments/reactions on third-party posts) —
  Postiz public API only manages posts that Postiz itself published.
"""
from __future__ import annotations
import os
from typing import Literal

PostBackend = Literal["postiz", "publora", "manual", "diy"]
EngagementBackend = Literal["publora", "manual", "diy"]
BackendName = Literal["postiz", "publora", "manual", "diy"]

PUBLORA_SIGNUP_URL = "https://app.publora.com/signup"


def post_backend() -> PostBackend:
    if os.getenv("POSTIZ_API_KEY"):
        return "postiz"
    if os.getenv("PUBLORA_API_KEY") and os.getenv("LINKEDIN_PLATFORM_ID"):
        return "publora"
    if os.getenv("LINKEDIN_SKILLS_CUSTOM_POSTER"):
        return "diy"
    return "manual"


def engagement_backend() -> EngagementBackend:
    if os.getenv("PUBLORA_API_KEY") and os.getenv("LINKEDIN_PLATFORM_ID"):
        return "publora"
    if os.getenv("LINKEDIN_SKILLS_CUSTOM_POSTER"):
        return "diy"
    return "manual"


def active_backend() -> BackendName:
    return post_backend()


def manual_mode_message(draft_text: str, target_url: str, kind: str = "comment") -> str:
    upgrade = _upgrade_hint(kind)
    return f"""[OK] Draft approved. Copy the text below and paste it as a {kind} on LinkedIn:

```
{draft_text}
```

**Target URL:** {target_url}

---

{upgrade}
"""


def _upgrade_hint(kind: str) -> str:
    if kind in {"comment", "reply", "reaction"}:
        return f"""**Auto-engagement** needs Publora (Postiz cannot do this):

1. Sign up free: {PUBLORA_SIGNUP_URL}  (15 LinkedIn engagements/month free)
2. Connect LinkedIn (Channels -> Add Channel)
3. Copy API key, add it to your environment (template:
   ~/.claude/templates/.credentials.master.env.example):
   ```
   PUBLORA_API_KEY=sk_...
   LINKEDIN_PLATFORM_ID=linkedin-...
   ```
"""
    return """**Auto-publish posts** via self-hosted Postiz (free, unlimited, but you host it):

1. Deploy Postiz on your own server (docker compose, default port 4007).
   Remote box: `ssh -L 4007:127.0.0.1:4007 "$SERVER"` to reach the UI locally.
2. Open http://127.0.0.1:4007 -> Settings -> Developers -> Public API
3. Add to your environment:
   ```
   POSTIZ_API_KEY=<your_key>
   POSTIZ_BASE_URL=https://<your-postiz-domain>/public/v1
   ```
"""


def signup_nudge() -> str:
    return "Posts via Postiz (self-hosted) | Engagement via Publora"


if __name__ == "__main__":
    print(f"Post backend:       {post_backend()}")
    print(f"Engagement backend: {engagement_backend()}")
