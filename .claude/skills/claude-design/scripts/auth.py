"""
auth.py — Cookie & header management for claude.ai/design Connect-RPC.

Pattern matches Perplexity / Plaud / Studio MCPs: cookies live in env var as
JSON dict, this module rebuilds the Cookie header + adds Connect-RPC bits.

ENV:
  CLAUDE_DESIGN_COOKIES — JSON string {cookieName: cookieValue, ...}
                          Required cookies (extract via DevTools):
                            __ssid, lastActiveOrg, anthropic-device-id
                          PLUS the httpOnly session cookie (likely sessionKey).
  CLAUDE_DESIGN_ORG_UUID — Organization UUID (from `lastActiveOrg` cookie or
                          via GetMe RPC). Sent as x-organization-uuid header.
"""
from __future__ import annotations

import json
import os
from typing import Dict


BASE_URL = "https://claude.ai/design/anthropic.<internal>.api.v1alpha.<Service>"
DOWNLOAD_URL = "https://claude.ai/design/v1/design/projects/{project_id}/download"


def _parse_cookies(env_value: str) -> Dict[str, str]:
    """Parse CLAUDE_DESIGN_COOKIES env (JSON dict OR raw header string)."""
    env_value = env_value.strip()
    if not env_value:
        return {}
    if env_value.startswith("{"):
        try:
            data = json.loads(env_value)
            return {str(k): str(v) for k, v in data.items()}
        except json.JSONDecodeError:
            pass
    # Fallback: raw cookie-header form  "k=v; k2=v2"
    out = {}
    for pair in env_value.split(";"):
        pair = pair.strip()
        if "=" in pair:
            k, _, v = pair.partition("=")
            out[k.strip()] = v.strip()
    return out


def get_cookies() -> Dict[str, str]:
    raw = os.environ.get("CLAUDE_DESIGN_COOKIES", "")
    cookies = _parse_cookies(raw)
    if not cookies:
        raise RuntimeError(
            "CLAUDE_DESIGN_COOKIES env var is empty or malformed. "
            "Expected JSON dict like {\"__ssid\":\"...\",\"sessionKey\":\"...\"}.\n"
            "How to extract: open https://claude.ai/design in Chrome, F12 → "
            "Application → Cookies → claude.ai → copy needed cookies."
        )
    return cookies


def get_org_uuid() -> str:
    org = os.environ.get("CLAUDE_DESIGN_ORG_UUID", "").strip()
    if org:
        return org
    # Try to derive from `lastActiveOrg` cookie
    try:
        return get_cookies().get("lastActiveOrg", "").strip() or _raise_org()
    except Exception:
        return _raise_org()


def _raise_org() -> str:
    raise RuntimeError(
        "CLAUDE_DESIGN_ORG_UUID env var is empty and could not be derived "
        "from `lastActiveOrg` cookie. Set it explicitly to the organization "
        "UUID (e.g. YOUR_ANTHROPIC_ORG_UUID)."
    )


def cookie_header() -> str:
    """Build a `Cookie:` header value from the env-supplied cookie dict."""
    cookies = get_cookies()
    return "; ".join(f"{k}={v}" for k, v in cookies.items())


def base_headers(extra: Dict[str, str] | None = None) -> Dict[str, str]:
    """Standard headers for every Connect-RPC unary call (JSON variant)."""
    headers = {
        "content-type": "application/json",
        "connect-protocol-version": "1",
        "x-organization-uuid": get_org_uuid(),
        "cookie": cookie_header(),
        "user-agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        ),
        "referer": "https://claude.ai/design",
    }
    if extra:
        headers.update(extra)
    return headers
