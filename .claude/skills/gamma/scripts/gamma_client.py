#!/usr/bin/env python3
"""
Gamma Generate API client (v1.0) — real, verified endpoints.

Docs: https://developers.gamma.app  (Generate API, GA since Nov 2025)
Base: https://public-api.gamma.app
Auth: header  X-API-KEY: sk-gamma-...   (NOT Authorization: Bearer)
Plan: requires Gamma Pro / Ultra / Teams / Business.

The API is asynchronous:
  1) POST /v1.0/generations           -> {"generationId": "..."}
  2) GET  /v1.0/generations/{id}       -> poll until status == "completed"
     completed response has: gammaUrl, gammaId, exportUrl (if exportAs set),
     credits.deducted, credits.remaining

CLI:
  python gamma_client.py generate "AI in Healthcare: trends and outlook" \
      --format presentation --num-cards 10 --export pptx --wait
  python gamma_client.py poll <generationId>

Key is read from env GAMMA_API_KEY (or --api-key). If unset, the client
tries ~/.claude/.credentials.master.env.

NOTE (2026-07-22): the GAMMA_API_KEY currently stored in
.credentials.master.env returns HTTP 401 "Invalid API key" — regenerate it
at gamma.app -> Settings -> API keys (needs a paid plan) before this works.
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import requests

BASE_URL = "https://public-api.gamma.app"
GEN_PATH = "/v1.0/generations"

FORMATS = ("presentation", "document", "social", "webpage")
TEXT_MODES = ("generate", "condense", "preserve")
EXPORT_AS = ("pdf", "pptx", "png")


def _load_key_from_creds() -> str | None:
    cred = Path.home() / ".claude" / ".credentials.master.env"
    if not cred.exists():
        return None
    for line in cred.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if line.startswith("GAMMA_API_KEY="):
            val = line.split("=", 1)[1].strip()
            if val and not val.startswith("os.getenv"):
                return val
    return None


def get_api_key(explicit: str | None = None) -> str:
    key = explicit or os.getenv("GAMMA_API_KEY") or _load_key_from_creds()
    if not key:
        sys.exit("ERROR: no Gamma API key. Set GAMMA_API_KEY or pass --api-key.")
    return key


def _headers(key: str) -> dict:
    return {"X-API-KEY": key, "Content-Type": "application/json"}


def create_generation(
    key: str,
    input_text: str,
    fmt: str = "presentation",
    text_mode: str = "generate",
    num_cards: int | None = None,
    export_as: str | None = None,
    theme_id: str | None = None,
    title: str | None = None,
    additional_instructions: str | None = None,
    tone: str | None = None,
    audience: str | None = None,
    image_source: str | None = None,
    image_model: str | None = None,
    extra: dict | None = None,
) -> dict:
    """POST /v1.0/generations. Returns dict with generationId."""
    payload: dict = {"inputText": input_text, "format": fmt, "textMode": text_mode}
    if num_cards is not None:
        payload["numCards"] = num_cards
    if export_as:
        payload["exportAs"] = export_as
    if theme_id:
        payload["themeId"] = theme_id
    if title:
        payload["title"] = title
    if additional_instructions:
        payload["additionalInstructions"] = additional_instructions
    text_opts = {}
    if tone:
        text_opts["tone"] = tone
    if audience:
        text_opts["audience"] = audience
    if text_opts:
        payload["textOptions"] = text_opts
    img_opts = {}
    if image_source:
        img_opts["source"] = image_source
    if image_model:
        img_opts["model"] = image_model
    if img_opts:
        payload["imageOptions"] = img_opts
    if extra:
        payload.update(extra)

    r = requests.post(BASE_URL + GEN_PATH, headers=_headers(key), json=payload, timeout=60)
    if r.status_code >= 400:
        sys.exit(f"ERROR {r.status_code}: {r.text}")
    return r.json()


def poll_generation(key: str, generation_id: str) -> dict:
    """GET /v1.0/generations/{id} once."""
    r = requests.get(
        f"{BASE_URL}{GEN_PATH}/{generation_id}", headers=_headers(key), timeout=60
    )
    if r.status_code >= 400:
        sys.exit(f"ERROR {r.status_code}: {r.text}")
    return r.json()


def wait_for(key: str, generation_id: str, interval: int = 5, timeout: int = 600) -> dict:
    """Poll until status is completed/failed or timeout (seconds)."""
    start = time.time()
    while True:
        data = poll_generation(key, generation_id)
        status = data.get("status")
        if status in ("completed", "failed"):
            return data
        if time.time() - start > timeout:
            sys.exit(f"TIMEOUT after {timeout}s; last status={status}")
        time.sleep(interval)


def main() -> None:
    ap = argparse.ArgumentParser(description="Gamma Generate API v1.0 client")
    ap.add_argument("--api-key", help="override GAMMA_API_KEY")
    sub = ap.add_subparsers(dest="cmd", required=True)

    g = sub.add_parser("generate", help="create a generation")
    g.add_argument("input_text", help="prompt, outline, or full content (<=400k chars)")
    g.add_argument("--format", default="presentation", choices=FORMATS)
    g.add_argument("--text-mode", default="generate", choices=TEXT_MODES)
    g.add_argument("--num-cards", type=int, help="1-75 depending on plan")
    g.add_argument("--export", dest="export_as", choices=EXPORT_AS)
    g.add_argument("--theme-id")
    g.add_argument("--title")
    g.add_argument("--instructions", dest="additional_instructions")
    g.add_argument("--tone")
    g.add_argument("--audience")
    g.add_argument("--image-source")
    g.add_argument("--image-model")
    g.add_argument("--wait", action="store_true", help="poll until completed")

    p = sub.add_parser("poll", help="poll one generation id")
    p.add_argument("generation_id")
    p.add_argument("--wait", action="store_true")

    args = ap.parse_args()
    key = get_api_key(args.api_key)

    if args.cmd == "generate":
        res = create_generation(
            key,
            args.input_text,
            fmt=args.format,
            text_mode=args.text_mode,
            num_cards=args.num_cards,
            export_as=args.export_as,
            theme_id=args.theme_id,
            title=args.title,
            additional_instructions=args.additional_instructions,
            tone=args.tone,
            audience=args.audience,
            image_source=args.image_source,
            image_model=args.image_model,
        )
        gen_id = res.get("generationId")
        print(json.dumps(res, ensure_ascii=False))
        if args.wait and gen_id:
            final = wait_for(key, gen_id)
            print(json.dumps(final, ensure_ascii=False, indent=2))
    elif args.cmd == "poll":
        if args.wait:
            print(json.dumps(wait_for(key, args.generation_id), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(poll_generation(key, args.generation_id), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
