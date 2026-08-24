"""Postiz REST client — self-hosted LinkedIn publishing alternative to Publora.

Postiz limitations (not bugs, design choice):
- Posts only — Postiz cannot react to or comment on arbitrary LinkedIn URLs
- Comments via /integration-trigger/:id only work on posts published THROUGH Postiz
- No reactions (LIKE/INSIGHTFUL/etc) on third-party posts

For engagement on other people's posts, stay on Publora (15 free/мес) or
use draft-only mode and copy-paste manually.

Auth header: Authorization: <RAW_API_KEY> (NO "Bearer" prefix)
Base URL: your own instance — https://<your-postiz-domain>/public/v1
          (self-hosted default port is 4007, so a local install is
           http://127.0.0.1:4007/public/v1)

Get API key: Postiz UI → Settings → Developers → Public API
"""
from __future__ import annotations
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

import requests


class PostizError(RuntimeError):
    pass


class PostizClient:
    # No default host on purpose: Postiz is self-hosted, so a baked-in URL would
    # silently send your posts to someone else's server. Set POSTIZ_BASE_URL.
    DEFAULT_BASE_URL = None

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 30.0,
    ):
        self.api_key = api_key or os.getenv("POSTIZ_API_KEY")
        if not self.api_key:
            raise PostizError(
                "POSTIZ_API_KEY not set. Put it in your environment (or copy "
                "~/.claude/templates/.credentials.master.env.example and fill it in) "
                "or pass api_key= explicitly. Get the key at Postiz UI → Settings → "
                "Developers → Public API."
            )
        resolved = base_url or os.getenv("POSTIZ_BASE_URL") or self.DEFAULT_BASE_URL
        if not resolved:
            raise PostizError(
                "POSTIZ_BASE_URL not set. Postiz is self-hosted — point it at YOUR "
                "instance, e.g. POSTIZ_BASE_URL=https://postiz.example.com/public/v1 "
                "(local install: http://127.0.0.1:4007/public/v1)."
            )
        self.base_url = resolved.rstrip("/")
        self.timeout = timeout
        self._session = requests.Session()
        # Postiz wants raw key, NO Bearer prefix
        self._session.headers.update(
            {
                "Authorization": self.api_key,
                "Content-Type": "application/json",
            }
        )

    # ---- Integrations -----------------------------------------------------

    def list_integrations(self) -> Any:
        """Return all connected social channels.

        Each integration dict has at least: `id`, `name`, `identifier` (e.g.
        "linkedin", "x", "instagram"), `picture`.

        Use this to find your LinkedIn integration ID for `create_post`.
        """
        r = self._session.get(self.base_url + "/integrations", timeout=self.timeout)
        return self._handle(r)

    def find_linkedin_integration_id(self) -> str:
        """Convenience: return the first LinkedIn integration ID, or raise.

        Picks `linkedin` over `linkedin-page` if both exist (personal first).
        """
        envvar = os.getenv("POSTIZ_LINKEDIN_INTEGRATION_ID")
        if envvar:
            return envvar
        integrations = self.list_integrations()
        for integ in integrations:
            if integ.get("identifier") == "linkedin":
                return integ["id"]
        for integ in integrations:
            if integ.get("identifier") == "linkedin-page":
                return integ["id"]
        raise PostizError(
            "No LinkedIn integration found in Postiz. Connect your LinkedIn "
            "account at the Postiz UI first (Channels → Add Channel → LinkedIn)."
        )

    # ---- Posts ------------------------------------------------------------

    def create_post(
        self,
        *,
        content: str,
        integration_id: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        media_urls: Optional[list[str]] = None,
        kind: str = "linkedin",
    ) -> dict[str, Any]:
        """Create a LinkedIn post via Postiz.

        Args:
            content: post text (up to 3,000 chars on LinkedIn)
            integration_id: Postiz integration UUID. If None, auto-detects LinkedIn.
            scheduled_time: ISO 8601 UTC, e.g. "2026-04-30T10:00:00Z". If None,
                Postiz schedules ~1 minute in the future ("now" semantics).
            media_urls: optional list of pre-uploaded media URLs (use upload() first).
            kind: settings type, usually "linkedin" or "linkedin-page".

        Returns Postiz response (includes post group ID for later updates).
        """
        if integration_id is None:
            integration_id = self.find_linkedin_integration_id()

        payload_value: list[dict[str, Any]] = [{"content": content}]
        if media_urls:
            payload_value[0]["image"] = [{"path": url} for url in media_urls]

        if scheduled_time is None:
            # Postiz "now" type still requires a scheduledFor — use ~1 min ahead
            scheduled_time = (
                datetime.now(timezone.utc) + timedelta(minutes=1)
            ).strftime("%Y-%m-%dT%H:%M:%SZ")

        body = {
            "type": "now",  # "now" | "draft" | "schedule"
            "date": scheduled_time,
            "posts": [
                {
                    "integration": {"id": integration_id},
                    "value": payload_value,
                    "group": "post",
                    "settings": {"__type": kind},
                }
            ],
        }
        return self._post("/posts", body)

    def schedule_post(
        self,
        *,
        content: str,
        scheduled_time: str,
        integration_id: Optional[str] = None,
        media_urls: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        """Schedule a post for a specific future time."""
        if integration_id is None:
            integration_id = self.find_linkedin_integration_id()

        payload_value: list[dict[str, Any]] = [{"content": content}]
        if media_urls:
            payload_value[0]["image"] = [{"path": url} for url in media_urls]

        body = {
            "type": "schedule",
            "date": scheduled_time,
            "posts": [
                {
                    "integration": {"id": integration_id},
                    "value": payload_value,
                    "group": "post",
                    "settings": {"__type": "linkedin"},
                }
            ],
        }
        return self._post("/posts", body)

    def list_posts(
        self,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        params = {}
        if start_date:
            params["startDate"] = start_date
        if end_date:
            params["endDate"] = end_date
        if status:
            params["status"] = status
        r = self._session.get(
            self.base_url + "/posts", params=params, timeout=self.timeout
        )
        return self._handle(r)

    def delete_post(self, post_id: str) -> dict[str, Any]:
        r = self._session.delete(
            f"{self.base_url}/posts/{post_id}", timeout=self.timeout
        )
        return self._handle(r)

    # ---- Media upload -----------------------------------------------------

    def upload(self, file_path: str) -> dict[str, Any]:
        """Upload an image/video file. Returns media URL for use in create_post."""
        # Drop the JSON Content-Type for multipart
        headers = {"Authorization": self.api_key}
        with open(file_path, "rb") as fh:
            r = requests.post(
                self.base_url + "/upload",
                files={"file": fh},
                headers=headers,
                timeout=self.timeout * 2,
            )
        return self._handle(r)

    # ---- Analytics --------------------------------------------------------

    def post_analytics(self, post_id: str, days: int = 7) -> dict[str, Any]:
        r = self._session.get(
            f"{self.base_url}/analytics/post/{post_id}",
            params={"date": days},
            timeout=self.timeout,
        )
        return self._handle(r)

    # ---- Internals --------------------------------------------------------

    def _post(self, path: str, json_body: dict[str, Any]) -> dict[str, Any]:
        r = self._session.post(
            self.base_url + path, json=json_body, timeout=self.timeout
        )
        return self._handle(r)

    @staticmethod
    def _handle(r: requests.Response) -> dict[str, Any]:
        if r.status_code >= 400:
            try:
                body = r.json()
            except Exception:
                body = {"error": r.text[:500]}
            raise PostizError(f"HTTP {r.status_code}: {body}")
        try:
            return r.json()
        except Exception:
            return {"raw": r.text}


if __name__ == "__main__":
    import json
    import sys

    cmd = sys.argv[1] if len(sys.argv) > 1 else "channels"
    client = PostizClient()
    if cmd == "channels":
        print(json.dumps(client.list_integrations(), indent=2, ensure_ascii=False))
    elif cmd == "linkedin-id":
        print(client.find_linkedin_integration_id())
    elif cmd == "post" and len(sys.argv) > 2:
        text = sys.argv[2]
        print(json.dumps(client.create_post(content=text), indent=2, ensure_ascii=False))
    else:
        print("Usage: python postiz_client.py [channels | linkedin-id | post <text>]")
