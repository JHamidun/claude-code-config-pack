"""Shared helpers for LinkedIn Skills.

Two publishing backends supported:
- PubloraClient — SaaS, supports posts + comments + reactions on any LinkedIn URL
- PostizClient — self-hosted, supports posts only (cannot engage with third-party posts)

Use Postiz for posts (free, unlimited), Publora for engagement (free 15/мес).
backend_selector.active_backend() picks based on env vars:
  POSTIZ_API_KEY → "postiz" for posts
  PUBLORA_API_KEY + LINKEDIN_PLATFORM_ID → "publora" for posts and engagement
  neither → "manual" (draft-only, copy-paste)
"""
from .url_parser import parse_linkedin_url, build_parent_comment_urn
from .publora_client import PubloraClient, PubloraError
from .postiz_client import PostizClient, PostizError
from .approval import render_approval_card
from .backend_selector import (
    active_backend,
    post_backend,
    engagement_backend,
    manual_mode_message,
    signup_nudge,
    PUBLORA_SIGNUP_URL,
)

__all__ = [
    "parse_linkedin_url",
    "build_parent_comment_urn",
    "PubloraClient",
    "PubloraError",
    "PostizClient",
    "PostizError",
    "render_approval_card",
    "active_backend",
    "post_backend",
    "engagement_backend",
    "manual_mode_message",
    "signup_nudge",
    "PUBLORA_SIGNUP_URL",
]
