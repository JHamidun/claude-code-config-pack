#!/usr/bin/env python3
"""
Suno headless client — reverse-engineered internal API (studio-api-prod.suno.com).

Auth: Clerk. A short-lived Bearer (~1h, aud=suno-api) is minted from the durable
`__client` cookie via the Clerk token endpoint. Reads/list/download/status work fully
headless. Web generation (/api/generate/v2-web/) is captcha-gated (token_provider:1);
this client tries the non-web /api/generate/v2/ path — if Suno rejects it, fall back to
the browser (Playwright) for generation only, then use this client for everything else.

Creds (in ~/.claude/.credentials.master.env):
  SUNO_CLIENT_COOKIE   __client cookie value (durable; DevTools → Application → Cookies → suno.com → __client)
  SUNO_SESSION_ID      session_xxx (Clerk session id)
  SUNO_DEVICE_ID       device-id header (uuid)
  SUNO_BEARER          (optional) paste a fresh Bearer to use directly without __client (~1h)
  SUNO_USER_AGENT      (optional) UA string

CLI:
  python suno_client.py billing
  python suno_client.py list [--limit 20] [--workspace default]
  python suno_client.py status <clip_id>
  python suno_client.py download <clip_id> [--out out.mp3]
  python suno_client.py generate "<style/description>" [--instrumental] [--title T] [--model chirp-fenix]
  python suno_client.py token         # mint & print a Bearer (debug)
"""
import os
import sys
import json
import time
import base64
import argparse

import requests

BASE = "https://studio-api-prod.suno.com"
AUTH = "https://auth.suno.com"
CLERK_Q = "__clerk_api_version=2025-11-10&_clerk_js_version=5.117.0"
CDN = "https://cdn1.suno.ai"


def _load_env():
    p = os.path.expanduser("~/.claude/.credentials.master.env")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def _jwt_exp(tok):
    try:
        payload = tok.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("exp", 0)
    except Exception:
        return 0


class SunoClient:
    def __init__(self):
        _load_env()
        self.client_cookie = os.getenv("SUNO_CLIENT_COOKIE", "")
        self.session_id = os.getenv("SUNO_SESSION_ID", "")
        self.device_id = os.getenv("SUNO_DEVICE_ID", "")
        self.ua = os.getenv("SUNO_USER_AGENT",
                            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                            "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")
        self._bearer = os.getenv("SUNO_BEARER", "")
        self._exp = _jwt_exp(self._bearer) if self._bearer else 0
        self.s = requests.Session()

    # ---------- auth ----------
    def _mint(self):
        if not (self.client_cookie and self.session_id):
            raise RuntimeError("No SUNO_CLIENT_COOKIE/SUNO_SESSION_ID to mint a token "
                               "(and SUNO_BEARER missing/expired). Refresh creds — see skill.")
        url = f"{AUTH}/v1/client/sessions/{self.session_id}/tokens?{CLERK_Q}"
        r = self.s.post(url, headers={
            "cookie": f"__client={self.client_cookie}",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://suno.com", "referer": "https://suno.com/",
            "user-agent": self.ua,
        }, timeout=30)
        r.raise_for_status()
        jwt = r.json()["jwt"]
        self._bearer = jwt
        self._exp = _jwt_exp(jwt)
        return jwt

    def token(self):
        if self._bearer and time.time() < self._exp - 120:
            return self._bearer
        return self._mint()

    def _browser_token(self):
        ms = int(time.time() * 1000)
        b64 = base64.b64encode(json.dumps({"timestamp": ms}).encode()).decode()
        return json.dumps({"token": b64})

    def _headers(self, json_body=True):
        h = {
            "authorization": f"Bearer {self.token()}",
            "device-id": self.device_id,
            "browser-token": self._browser_token(),
            "origin": "https://suno.com", "referer": "https://suno.com/",
            "user-agent": self.ua, "affiliate-id": "undefined",
        }
        if json_body:
            h["content-type"] = "application/json"
        return h

    def _get(self, path, **kw):
        r = self.s.get(BASE + path, headers=self._headers(False), timeout=60, **kw)
        r.raise_for_status()
        return r.json()

    def _post(self, path, body):
        r = self.s.post(BASE + path, headers=self._headers(True), data=json.dumps(body), timeout=120)
        if r.status_code >= 400:
            raise RuntimeError(f"POST {path} -> {r.status_code}: {r.text[:300]}")
        return r.json()

    # ---------- reads ----------
    def billing(self):
        return self._get("/api/billing/info/")

    def list_clips(self, workspace="default", limit=20, cursor=None):
        body = {"cursor": cursor, "limit": limit, "filters": {
            "disliked": "False", "trashed": "False",
            "fromStudioProject": {"presence": "False"}, "stem": {"presence": "False"},
            "workspace": {"presence": "True", "workspaceId": workspace}}}
        return self._post("/api/feed/v3", body)

    def find_clip(self, clip_id, max_pages=10):
        cursor = None
        for _ in range(max_pages):
            data = self.list_clips(limit=50, cursor=cursor)
            items = data.get("clips") or data.get("items") or data.get("data") or []
            for c in items:
                if c.get("id") == clip_id:
                    return c
            cursor = data.get("cursor") or data.get("next_cursor")
            if not cursor:
                break
        return None

    def video_status(self, clip_id):
        return self._get(f"/api/video/generate/{clip_id}/status/")

    def download(self, clip_id, out=None):
        out = out or f"{clip_id}.mp3"
        url = f"{CDN}/{clip_id}.mp3"
        r = self.s.get(url, timeout=120)
        r.raise_for_status()
        with open(out, "wb") as f:
            f.write(r.content)
        return out

    # ---------- generate (non-web endpoint /api/generate/v2/ — NO captcha) ----------
    def generate(self, description, instrumental=True, title=None, model="chirp-fenix"):
        """Submit a generation. /api/generate/v2/ works headless without the web captcha.
        Returns the batch dict with 'clips' (each has an 'id' and status 'submitted')."""
        body = {
            "generation_type": "TEXT", "mv": model, "prompt": "",
            "gpt_description_prompt": description, "make_instrumental": bool(instrumental),
            "metadata": {"create_mode": "simple", "lyrics_model": "default"},
        }
        if title:
            body["title"] = title
        return self._post("/api/generate/v2/", body)

    def generate_custom(self, lyrics, tags, title=None, model="chirp-fenix"):
        """Custom mode: OUR lyrics + style tags (not GPT-written). Correct schema, but the
        /api/generate/v2/ endpoint is captcha-gated headless (422 token_validation_failed,
        2026-06). Use the Playwright UI recipe in SKILL.md gotcha #3 for custom songs; this
        method documents the exact payload for a future headless fix."""
        body = {
            "generation_type": "TEXT", "mv": model,
            "prompt": lyrics, "tags": tags,
            "make_instrumental": False,
            "metadata": {"create_mode": "custom", "lyrics_model": "default"},
        }
        if title:
            body["title"] = title
        return self._post("/api/generate/v2/", body)

    def wait_clips(self, clip_ids, timeout=300, poll=6):
        """Poll feed until given clip ids reach a terminal state. Returns {id: clip}."""
        done = {}
        start = time.time()
        ids = set(clip_ids)
        while ids and time.time() - start < timeout:
            data = self.list_clips(limit=50)
            items = data.get("clips") or data.get("items") or data.get("data") or []
            for c in items:
                cid = c.get("id")
                if cid in ids and c.get("status") in ("complete", "error", "streaming"):
                    if c.get("status") != "streaming":
                        done[cid] = c
                        ids.discard(cid)
            if not ids:
                break
            time.sleep(poll)
        return done

    def make_track(self, description, instrumental=True, title=None, model="chirp-fenix",
                   out_dir=".", timeout=300):
        """One-shot: generate -> wait -> download all resulting clips. Returns list of file paths."""
        batch = self.generate(description, instrumental=instrumental, title=title, model=model)
        ids = [c["id"] for c in batch.get("clips", []) if c.get("id")]
        done = self.wait_clips(ids, timeout=timeout)
        paths = []
        for cid in ids:
            c = done.get(cid)
            if c and c.get("status") == "complete":
                paths.append(self.download(cid, os.path.join(out_dir, f"suno_{cid}.mp3")))
        return paths


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("token")
    sub.add_parser("billing")
    p = sub.add_parser("list"); p.add_argument("--limit", type=int, default=20); p.add_argument("--workspace", default="default")
    p = sub.add_parser("status"); p.add_argument("clip_id")
    p = sub.add_parser("download"); p.add_argument("clip_id"); p.add_argument("--out")
    p = sub.add_parser("generate"); p.add_argument("desc"); p.add_argument("--instrumental", action="store_true"); p.add_argument("--title"); p.add_argument("--model", default="chirp-fenix")
    p = sub.add_parser("make"); p.add_argument("desc"); p.add_argument("--instrumental", action="store_true"); p.add_argument("--title"); p.add_argument("--model", default="chirp-fenix"); p.add_argument("--out-dir", default="."); p.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()
    c = SunoClient()
    if a.cmd == "token":
        print(c.token())
    elif a.cmd == "billing":
        print(json.dumps(c.billing(), ensure_ascii=False, indent=2)[:2000])
    elif a.cmd == "list":
        data = c.list_clips(workspace=a.workspace, limit=a.limit)
        items = data.get("clips") or data.get("items") or data.get("data") or data
        if isinstance(items, list):
            for it in items:
                print(it.get("id"), "|", it.get("status"), "|", (it.get("title") or "")[:40],
                      "|", it.get("audio_url") or "")
        else:
            print(json.dumps(data, ensure_ascii=False, indent=2)[:2000])
    elif a.cmd == "status":
        print(json.dumps(c.video_status(a.clip_id), ensure_ascii=False, indent=2)[:1500])
    elif a.cmd == "download":
        print("saved", c.download(a.clip_id, a.out))
    elif a.cmd == "generate":
        print(json.dumps(c.generate(a.desc, instrumental=a.instrumental, title=a.title, model=a.model),
                         ensure_ascii=False, indent=2)[:2000])
    elif a.cmd == "make":
        paths = c.make_track(a.desc, instrumental=a.instrumental, title=a.title, model=a.model,
                             out_dir=a.out_dir, timeout=a.timeout)
        print("downloaded:", paths)


if __name__ == "__main__":
    main()
