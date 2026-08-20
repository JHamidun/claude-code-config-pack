#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Higgsfield model router — decides per `job_set_type` (jst) whether to call a model
DIRECTLY (your own keys, cheaper / already paid) or via `hf.exe` (HF-exclusives).

Source of truth: ./references/model-provider-map.md (51-model map),
./references/hf-cli-anatomy.md (hf.exe commands), ./references/registries/registries-LIVE.md, ./references/exclusive-models-soul-ms-virality.md.

Stack assumed available:
  GOOGLE_API_KEY (google-genai: Veo, Nano Banana / Pro)
  RUNWAY_TOKEN_PLACEHOLDER     (Runway Unlimited = flat $0 marginal: Seedance 2.0, Kling 2.6/3.0)
  OPENAI_API_KEY (GPT-Image-2 / 1.5)
  REPLICATE_API_KEY (flux/recraft/topaz/wan/minimax/grok/seedance1.5/seedream/sam)
  Local GPU (rembg, Topaz)
NOT available: xAI, BFL, Topaz API, Recraft API, MiniMax, Kuaishou, AIMLAPI/PiAPI, WaveSpeed, fal.

CLI:
  python router.py route <jst>
  python router.py table
  python router.py generate <jst> --prompt "..." [--image up_id] [--aspect 9:16] [--resolution 720p] [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# Windows consoles default to cp1251/cp866 — force UTF-8 so output never crashes.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

# --------------------------------------------------------------------------- #
# Paths / config
# --------------------------------------------------------------------------- #
# Self-contained, relative-within-skill (GitHub-packageable).
# router.py lives at  video-generation/engines/higgsfield/scripts/router.py
_HERE = Path(__file__).resolve()
HF_EXE = _HERE.parent.parent / "bin" / "hf.exe"                       # engines/higgsfield/bin/hf.exe (gitignored — install: npm i -g @higgsfield/cli)
RUNWAY_CLIENT = _HERE.parent.parent.parent.parent / "scripts" / "runway_client.py"  # video-generation/scripts/runway_client.py (sibling in same skill)
# Credentials: env var first (get_token); file is a local fallback, NEVER shipped (.gitignore).
CREDENTIALS_FILE = Path(os.path.expanduser("~/.claude/.credentials.master.env"))

# upstream  : original model vendor (ByteDance, Google, OpenAI, BFL, ...)
# access    : "direct" (own keys, cheaper) | "hf" (HF-exclusive, no direct analog) | "no-key" (key needed)
# via       : concrete provider used for direct calls
# direct_id : model id at the direct provider
# keep_hf   : True  -> route through hf.exe (generate())
#             False -> emit the direct recipe (call vendor SDK yourself)
# recipe    : one-line how-to for the direct path
#
# Faithful to model-provider-map.md. "via" values:
#   google-genai | runway | replicate | openai | local | fal | aimlapi | wavespeed | higgsfield
ROUTES: dict[str, dict] = {
    # ===================== 🟢 DIRECT — VIDEO ===============================
    "veo3_1": {
        "upstream": "Google Veo 3.1",
        "access": "direct",
        "via": "google-genai",
        "direct_id": "veo-3.0-generate-001",
        "keep_hf": False,
        "recipe": "google-genai: GOOGLE_API_KEY, models.generate_videos(model='veo-3.0-generate-001'). "
                  "Fast: -fast-generate-001 ($0.10/s, 3-4x cheaper than HF).",
    },
    "veo3_1_lite": {
        "upstream": "Google Veo 3.1 Lite",
        "access": "direct",
        "via": "google-genai",
        "direct_id": "veo-3.1-lite-generate-preview",
        "keep_hf": False,
        "recipe": "google-genai: GOOGLE_API_KEY, model='veo-3.1-lite-generate-preview' (~$0.05/s, 3-4x cheaper than HF).",
    },
    "seedance_2_0": {
        "upstream": "ByteDance Seedance 2.0",
        "access": "direct",
        "via": "runway",
        "direct_id": "seedance-2.0",
        "keep_hf": False,
        "recipe": f"Runway Unlimited (RUNWAY_TOKEN_PLACEHOLDER) via {RUNWAY_CLIENT} model 'seedance-2.0' = $0 marginal "
                  "(flat) vs ~$1.25 HF. Workhorse — never burn HF credits.",
    },
    "seedance1_5": {
        "upstream": "ByteDance Seedance 1.5 Pro",
        "access": "direct",
        "via": "replicate",
        "direct_id": "bytedance/seedance-1.5-pro",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'bytedance/seedance-1.5-pro' ($0.022/s fast vs ~$1.25 HF). "
                  "Or Runway runway_client.py if it exposes 1.5.",
    },
    "kling2_6": {
        "upstream": "Kuaishou Kling 2.6",
        "access": "direct",
        "via": "runway",
        "direct_id": "kling-2.6-pro",
        "keep_hf": False,
        "recipe": f"Runway Unlimited (RUNWAY_TOKEN_PLACEHOLDER) via {RUNWAY_CLIENT} 'kling-2.6-pro' = $0 marginal (flat). "
                  "Fallback Replicate 'kwaivgi/kling-v2.6'.",
    },
    "kling3_0": {
        "upstream": "Kuaishou Kling 3.0",
        "access": "direct",
        "via": "runway",
        "direct_id": "kling-3.0",
        "keep_hf": False,
        "recipe": f"Runway Unlimited (RUNWAY_TOKEN_PLACEHOLDER) via {RUNWAY_CLIENT} 'kling-3.0' = $0 marginal (flat). "
                  "Fallback Replicate 'kwaivgi/kling-v3-omni-video'.",
    },
    "wan2_6": {
        "upstream": "Alibaba Wan 2.6",
        "access": "direct",
        "via": "replicate",
        "direct_id": "wan-video/wan-2.6-i2v",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'wan-video/wan-2.6-i2v' (~$0.10-0.15/s ~= HF).",
    },
    "wan2_7": {
        "upstream": "Alibaba Wan 2.7",
        "access": "direct",
        "via": "replicate",
        "direct_id": "wan-video/wan-2.7-i2v",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'wan-video/wan-2.7-i2v' (also -r2v/-image/-image-pro 4K) (~$0.10-0.15/s).",
    },
    "minimax_hailuo": {
        "upstream": "MiniMax Hailuo 02/2.3",
        "access": "direct",
        "via": "replicate",
        "direct_id": "minimax/hailuo-02",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'minimax/hailuo-02' ($0.27/6s). "
                  "WARNING: apply rembg afterwards (dark-gradient bg fix, see hailuo-dark-gradient-rembg-only-fix).",
    },
    "grok_video": {
        "upstream": "xAI Grok Imagine (video)",
        "access": "direct",
        "via": "replicate",
        "direct_id": "xai/grok-imagine-video",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'xai/grok-imagine-video' ($0.05-0.14/s, 3-5x cheaper, no xAI key needed).",
    },
    # ===================== 🟢 DIRECT — IMAGE ===============================
    "gpt_image_2": {
        "upstream": "OpenAI GPT-Image-2",
        "access": "direct",
        "via": "openai",
        "direct_id": "gpt-image-2",
        "keep_hf": False,
        "recipe": "OpenAI OPENAI_API_KEY images.generate / images.edit model='gpt-image-2' "
                  "($0.006-0.21/img, 3-6x cheaper than HF).",
    },
    "openai_hazel": {
        "upstream": "OpenAI GPT-Image-1.5 (Hazel)",
        "access": "direct",
        "via": "openai",
        "direct_id": "gpt-image-1.5",
        "keep_hf": False,
        "recipe": "OpenAI OPENAI_API_KEY model='gpt-image-1.5' (~-50% vs HF).",
    },
    "nano_banana_flash": {
        "upstream": "Google Nano Banana 2",
        "access": "direct",
        "via": "google-genai",
        "direct_id": "gemini-3.1-flash-image-preview",
        "keep_hf": False,
        "recipe": "google-genai GOOGLE_API_KEY model='gemini-3.1-flash-image-preview', "
                  "config response_modalities=['IMAGE','TEXT'] ($0.045-0.151/img ~= HF).",
    },
    "nano_banana_2": {
        "upstream": "Google Nano Banana Pro",
        "access": "direct",
        "via": "google-genai",
        "direct_id": "gemini-3-pro-image-preview",
        "keep_hf": False,
        "recipe": "google-genai GOOGLE_API_KEY model='gemini-3-pro-image-preview' ($0.134/img). "
                  "NOTE: HF credit (~$0.068) ~2x cheaper for plain single-shot Pro gen — use hf for one-off plain "
                  "Pro images if credits in budget; use direct for batch/pipelines.",
    },
    "seedream_v4_5": {
        "upstream": "ByteDance Seedream 4.5",
        "access": "direct",
        "via": "replicate",
        "direct_id": "bytedance/seedream-4.5",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'bytedance/seedream-4.5' ($0.035-0.05/img ~= HF).",
    },
    "seedream_v5_lite": {
        "upstream": "ByteDance Seedream 5-lite",
        "access": "direct",
        "via": "replicate",
        "direct_id": "bytedance/seedream-5-lite",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'bytedance/seedream-5-lite' ($0.035-0.05/img ~= HF).",
    },
    "flux_2": {
        "upstream": "BFL FLUX.2",
        "access": "direct",
        "via": "replicate",
        "direct_id": "black-forest-labs/flux-2-pro",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'black-forest-labs/flux-2-pro' (or -dev) (~$0.04/img, cheaper/equal).",
    },
    "flux_kontext": {
        "upstream": "BFL FLUX.1 Kontext (edit)",
        "access": "direct",
        "via": "replicate",
        "direct_id": "black-forest-labs/flux-kontext-pro",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'black-forest-labs/flux-kontext-pro' (~$0.04/edit ~=).",
    },
    "recraft_v4_1": {
        "upstream": "Recraft V4.1",
        "access": "direct",
        "via": "replicate",
        "direct_id": "recraft-ai/recraft-v4",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'recraft-ai/recraft-v4' (verify v4.1 slug) ($0.04/img ~=).",
    },
    "grok_image": {
        "upstream": "xAI Grok Imagine (image)",
        "access": "direct",
        "via": "replicate",
        "direct_id": "xai/grok-imagine-image",
        "keep_hf": False,
        "recipe": "Replicate REPLICATE_API_KEY 'xai/grok-imagine-image' ($0.02/img, 3-5x cheaper, no xAI key needed).",
    },
    # ===================== 🟢 DIRECT — UPSCALE / UTILITY ====================
    "topaz_image": {
        "upstream": "Topaz Photo AI",
        "access": "direct",
        "via": "local",
        "direct_id": "topazlabs/image-upscale",
        "keep_hf": False,
        "recipe": "LOCAL Topaz Photo AI on your-GPU ($0). Or Replicate 'topazlabs/image-upscale' ($0.05/24MP, -25% vs Topaz API).",
    },
    "topaz_video": {
        "upstream": "Topaz Video (Astra/Starlight)",
        "access": "direct",
        "via": "local",
        "direct_id": "topazlabs/video-upscale",
        "keep_hf": False,
        "recipe": "LOCAL Topaz Video AI on your-GPU ($0). Or Replicate 'topazlabs/video-upscale'.",
    },
    "image_background_remover": {
        "upstream": "rembg (U2Net/BiRefNet)",
        "access": "direct",
        "via": "local",
        "direct_id": "rembg",
        "keep_hf": False,
        "recipe": "LOCAL rembg[gpu] on your-GPU ($0). pip install rembg[gpu]; rembg i in.png out.png.",
    },
    "sam_3_video": {
        "upstream": "Meta SAM 3.1 (segment/remove bg)",
        "access": "direct",
        "via": "fal",
        "direct_id": "fal-ai/sam-3-1/video",
        "keep_hf": False,
        "recipe": "fal 'fal-ai/sam-3-1/video' ($0.005/16 frames, fal cheaper) or Replicate 'lucataco/sam3-video'. "
                  "NOTE: no fal key in stack -> if no fal/replicate, fall back to hf.",
    },
    # ===================== 🟡 NO-KEY (cheap if obtained) ====================
    "z_image": {
        "upstream": "Alibaba Z-Image Turbo",
        "access": "no-key",
        "via": "aimlapi",
        "direct_id": "alibaba/z-image-turbo",
        "keep_hf": True,  # no AIMLAPI/PiAPI key in stack -> use hf.exe until key obtained
        "recipe": "AIMLAPI 'alibaba/z-image-turbo' or PiAPI ($0.04/img). NOT on Replicate. "
                  "No AIMLAPI/PiAPI key in stack -> routed to hf.exe until a key is added.",
    },
    # ===================== 🔴 HF-EXCLUSIVES (keep hf.exe) ==================
    "soul_cast": {
        "upstream": "Higgsfield Soul Cast",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: Soul fine-tune + element consistency. type=video. params: aspect_ratio(16:9), "
                  "budget(fixed 10 in cinematic flow), prompt(object), character_params{genre,age,era,gender}. "
                  "Train via 'hf soul-id create --name X --soul-2 --image id1..id5'.",
    },
    "soul_location": {
        "upstream": "Higgsfield Soul Location",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: type=image. params: aspect_ratio(9 enums), prompt(string, required). "
                  "Architecture/materials only, no people; append Location Color Directive suffix to every prompt.",
    },
    "soul_cinematic": {
        "upstream": "Higgsfield Soul Cinematic",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: Soul cinematic flow (budget fixed 10). Character/location element orchestration.",
    },
    "text2image_soul_v2": {
        "upstream": "Higgsfield Soul v2 (text2image)",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: Soul v2 text-to-image fine-tune + Soul style_id registry. No direct analog.",
    },
    "soul_cinema_studio": {
        "upstream": "Higgsfield Soul Cinema Studio",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: Soul + Cinema Studio camera-preset orchestration.",
    },
    "marketing_studio_image": {
        "upstream": "Higgsfield Marketing Studio (image)",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive DTC Ads Engine: webproduct parser + brand-kit extractor + avatars. "
                  "params: aspect_ratio, input_images[], prompt(req), resolution(1k/2k/4k). CLI 'hf marketing-studio ...'.",
    },
    "marketing_studio_video": {
        "upstream": "Higgsfield Marketing Studio (video)",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: 9 ad modes (ugc/ugc_how_to/ugc_unboxing/product_showcase/product_review/tv_spot/"
                  "wild_card/ugc_virtual_try_on/virtual_try_on). params: mode, avatars[], product_ids[], hook_id, "
                  "setting_id, ad_reference_id, generate_audio, duration(15), medias[], aspect_ratio. "
                  "Run 'hf ms hooks list'/'settings list' first.",
    },
    "ms_image": {
        "upstream": "Higgsfield Marketing Studio (ms_image)",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: branded image gen. params: aspect_ratio, input_images[], prompt, resolution, "
                  "avatars[], product_ids[], brand_kit_id, batch_size, quality(low/med/high), folder_id.",
    },
    "brain_activity": {
        "upstream": "Higgsfield Virality Predictor",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: type=text. Proprietary TikTok/Reels trend DB + retention model -> Markdown report. "
                  "params: folder_id, medias[](video, required). CLI 'hf generate create brain_activity --video <url>'.",
    },
    "reframe": {
        "upstream": "Higgsfield Reframe (AI outpaint)",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: AI-outpaint aspect change (not crop). Direct analog = Runway Expand Video "
                  "Enterprise only ($500+/mo). ffmpeg crop loses content.",
    },
    "draw_to_video": {
        "upstream": "Higgsfield Draw-to-Video",
        "access": "hf",
        "via": "higgsfield",
        "direct_id": None,
        "keep_hf": True,
        "recipe": "HF-exclusive: canvas annotations (motion arrows) -> motion-control. No public canvas-input API.",
    },
}

# Aliases / display-name corrections from model-provider-map.md:
#   nano_banana_flash = "Nano Banana 2" = gemini-3.1-flash-image-preview
#   nano_banana_2     = "Nano Banana Pro" = gemini-3-pro-image-preview
ALIASES: dict[str, str] = {
    "veo3": "veo3_1",                 # base Veo -> closest direct entry
    "seedance_2_0_fast": "seedance_2_0",
    "grok_video_v15": "grok_video",
    "seedream_v4_5_lite": "seedream_v5_lite",
}


# --------------------------------------------------------------------------- #
# Credentials
# --------------------------------------------------------------------------- #
def load_env(path: Path = CREDENTIALS_FILE) -> dict[str, str]:
    """Parse a KEY=VALUE .env file (ignores comments / blanks). Strips quotes."""
    env: dict[str, str] = {}
    if not path.exists():
        return env
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        if key.startswith("export "):
            key = key[len("export "):].strip()
        val = val.strip().strip('"').strip("'")
        env[key] = val
    return env


def get_token(env: dict[str, str] | None = None) -> str | None:
    """HIGGSFIELD_ACCESS_TOKEN from process env first, then credentials file."""
    tok = os.environ.get("HIGGSFIELD_ACCESS_TOKEN")
    if tok:
        return tok
    if env is None:
        env = load_env()
    return env.get("HIGGSFIELD_ACCESS_TOKEN")


# --------------------------------------------------------------------------- #
# Routing
# --------------------------------------------------------------------------- #
def resolve(jst: str) -> tuple[str, dict | None]:
    """Resolve a jst (with alias support) to (canonical_jst, route_or_None)."""
    canon = ALIASES.get(jst, jst)
    return canon, ROUTES.get(canon)


def route(jst: str) -> dict:
    """Return a decision dict for a given job_set_type."""
    canon, r = resolve(jst)
    if r is None:
        return {
            "jst": jst,
            "known": False,
            "decision": "hf",  # safe default: unknown -> let hf.exe handle it
            "keep_hf": True,
            "reason": f"Unknown jst '{jst}' — not in ROUTES map. Defaulting to hf.exe "
                      f"(check 'hf model get {jst} --json' for live schema).",
            "via": "higgsfield",
            "command_hint": f'hf generate create {jst} ...',
        }
    keep_hf = bool(r["keep_hf"])
    decision = "hf" if keep_hf else "direct"
    if r["access"] == "no-key" and keep_hf:
        reason = f"No direct key in stack for {r['via']} — routed to hf.exe until key added. {r['recipe']}"
    elif keep_hf:
        reason = f"HF-exclusive ({r['upstream']}): no direct analog. {r['recipe']}"
    else:
        reason = f"Direct via {r['via']} = cheaper/equal. {r['recipe']}"
    out = {
        "jst": canon,
        "alias_of": jst if canon != jst else None,
        "known": True,
        "decision": decision,
        "keep_hf": keep_hf,
        "upstream": r["upstream"],
        "access": r["access"],
        "via": r["via"],
        "direct_id": r["direct_id"],
        "recipe": r["recipe"],
        "reason": reason,
    }
    if keep_hf:
        out["command_hint"] = f'hf generate create {canon} --prompt "..."'
    else:
        out["command_hint"] = _direct_command_hint(canon, r)
    return out


def _direct_command_hint(jst: str, r: dict) -> str:
    via = r["via"]
    if via == "runway":
        return f'python "{RUNWAY_CLIENT}" --model {r["direct_id"]} --prompt "..."  (RUNWAY_TOKEN_PLACEHOLDER, $0 marginal)'
    if via == "google-genai":
        return f"from google import genai -> client.models with model='{r['direct_id']}' (GOOGLE_API_KEY)"
    if via == "openai":
        return f"openai images.generate model='{r['direct_id']}' (OPENAI_API_KEY)"
    if via == "replicate":
        return f"replicate.run('{r['direct_id']}', input={{...}}) (REPLICATE_API_KEY)"
    if via == "local":
        return f"local on your-GPU: {r['direct_id']} ($0)"
    if via == "fal":
        return f"fal_client.run('{r['direct_id']}', ...)  (needs fal key; else Replicate/hf fallback)"
    return r["recipe"]


# --------------------------------------------------------------------------- #
# Generation
# --------------------------------------------------------------------------- #
def _run_hf(jst: str, params: dict, token: str, dry_run: bool = False) -> dict:
    """Invoke hf.exe `generate create <jst> ...`."""
    if not HF_EXE.exists():
        return {"ok": False, "error": f"hf.exe not found at {HF_EXE}"}
    if not token:
        return {"ok": False, "error": "HIGGSFIELD_ACCESS_TOKEN not set (env or credentials file)."}

    cmd: list[str] = [str(HF_EXE), "generate", "create", jst]
    for key, val in params.items():
        if val is None:
            continue
        flag = "--" + key.replace("_", "-")
        if isinstance(val, bool):
            if val:
                cmd.append(flag)
        elif isinstance(val, (list, tuple)):
            for item in val:
                cmd.extend([flag, str(item)])
        else:
            cmd.extend([flag, str(val)])

    pretty = " ".join(f'"{c}"' if " " in c else c for c in cmd)
    if dry_run:
        return {"ok": True, "dry_run": True, "command": pretty}

    child_env = dict(os.environ)
    child_env["HIGGSFIELD_ACCESS_TOKEN"] = token
    try:
        proc = subprocess.run(
            cmd, env=child_env, capture_output=True, text=True, timeout=900
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "hf.exe timed out (900s)", "command": pretty}
    return {
        "ok": proc.returncode == 0,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "command": pretty,
    }


def generate(jst: str, dry_run: bool = False, **params) -> dict:
    """
    Route and (optionally) execute generation for a job_set_type.

    keep_hf=True  -> subprocess hf.exe `generate create <jst> ...` with the params.
    keep_hf=False -> return the DIRECT recipe (caller invokes the vendor SDK).
    """
    decision = route(jst)
    canon = decision["jst"]

    if decision["keep_hf"]:
        token = get_token()
        result = _run_hf(canon, params, token or "", dry_run=dry_run)
        return {"routed": decision, "executed": "hf.exe", "result": result}

    # Direct path: we do not call third-party SDKs here — emit an actionable recipe.
    return {
        "routed": decision,
        "executed": "direct-recipe",
        "result": {
            "ok": True,
            "via": decision["via"],
            "direct_id": decision["direct_id"],
            "recipe": decision["recipe"],
            "command_hint": decision["command_hint"],
            "params": params,
            "note": "Direct call is cheaper/equal vs HF. Invoke the vendor path above with these params.",
        },
    }


# --------------------------------------------------------------------------- #
# Pretty printers
# --------------------------------------------------------------------------- #
def print_decision(jst: str) -> None:
    d = route(jst)
    if not d["known"]:
        print(f"[{d['jst']}]  decision=HF (unknown)")
        print(f"  {d['reason']}")
        print(f"  hint: {d['command_hint']}")
        return
    tag = "[HF] hf.exe" if d["keep_hf"] else "[*] DIRECT"
    alias = f"  (alias of {jst})" if d.get("alias_of") else ""
    print(f"[{d['jst']}]{alias}  ->  {tag}")
    print(f"  upstream : {d['upstream']}")
    print(f"  access   : {d['access']}   via: {d['via']}   direct_id: {d['direct_id']}")
    print(f"  reason   : {d['reason']}")
    print(f"  command  : {d['command_hint']}")


def print_table() -> None:
    direct = [k for k, v in ROUTES.items() if not v["keep_hf"]]
    hf_only = [k for k, v in ROUTES.items() if v["keep_hf"]]
    width = max(len(k) for k in ROUTES) + 2

    print("=" * 96)
    print("HIGGSFIELD MODEL ROUTER — routing table (faithful to model-provider-map.md)")
    print("=" * 96)
    print(f"{'job_set_type':<{width}}{'DECISION':<10}{'VIA':<14}{'DIRECT_ID / NOTE'}")
    print("-" * 96)

    print(f"--- DIRECT ({len(direct)}) — your keys, cheaper/equal ---")
    for k in direct:
        v = ROUTES[k]
        did = v["direct_id"] or "-"
        print(f"{k:<{width}}{'direct':<10}{v['via']:<14}{did}")

    print(f"\n--- hf.exe ({len(hf_only)}) — HF-exclusives / no direct key ---")
    for k in hf_only:
        v = ROUTES[k]
        note = "no-key" if v["access"] == "no-key" else v["upstream"]
        print(f"{k:<{width}}{'hf':<10}{v['via']:<14}{note}")

    if ALIASES:
        print("\n--- aliases ---")
        for a, c in ALIASES.items():
            print(f"{a:<{width}}->        {c}")

    print("-" * 96)
    print("Money rules: Seedance 2.0 + Kling 2.6/3.0 via Runway Unlimited = $0 marginal; "
          "GPT-Image 3-6x cheaper; Veo Fast/Lite 3-4x; rembg/Topaz local = $0; "
          "Grok via Replicate 3-5x. HF credits only for exclusives.")


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="router.py",
        description="Higgsfield model router: DIRECT (own keys) vs hf.exe (HF-exclusives).",
    )
    sub = p.add_subparsers(dest="command", required=True)

    pr = sub.add_parser("route", help="Print routing decision for a job_set_type")
    pr.add_argument("jst", help="job_set_type, e.g. seedance_2_0, soul_cast")
    pr.add_argument("--json", action="store_true", help="Emit raw JSON decision")

    sub.add_parser("table", help="Print the full routing table")

    pg = sub.add_parser("generate", help="Route + generate (hf.exe) or print direct recipe")
    pg.add_argument("jst", help="job_set_type")
    pg.add_argument("--prompt", help="Generation prompt")
    pg.add_argument("--image", help="upload_id / image input (hf: --image)")
    pg.add_argument("--aspect", dest="aspect_ratio", help="Aspect ratio, e.g. 9:16")
    pg.add_argument("--resolution", help="Resolution, e.g. 720p / 1080p / 2k")
    pg.add_argument("--duration", help="Duration/seconds for video")
    pg.add_argument("--seed", help="Seed")
    pg.add_argument("--batch-size", dest="batch_size", help="Batch size")
    pg.add_argument("--dry-run", action="store_true", help="Show hf.exe command without running")
    pg.add_argument("--json", action="store_true", help="Emit raw JSON result")
    return p


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "route":
        if args.json:
            print(json.dumps(route(args.jst), ensure_ascii=False, indent=2))
        else:
            print_decision(args.jst)
        return 0

    if args.command == "table":
        print_table()
        return 0

    if args.command == "generate":
        params = {
            k: v
            for k, v in {
                "prompt": args.prompt,
                "image": args.image,
                "aspect_ratio": args.aspect_ratio,
                "resolution": args.resolution,
                "duration": args.duration,
                "seed": args.seed,
                "batch_size": args.batch_size,
            }.items()
            if v is not None
        }
        out = generate(args.jst, dry_run=args.dry_run, **params)
        if args.json:
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            d = out["routed"]
            print_decision(args.jst)
            print("-" * 60)
            res = out["result"]
            if out["executed"] == "hf.exe":
                if res.get("dry_run"):
                    print(f"DRY RUN command:\n  {res['command']}")
                elif res.get("ok"):
                    print("hf.exe OK:")
                    print(res.get("stdout", "").strip())
                else:
                    print(f"hf.exe FAILED ({res.get('returncode')}): {res.get('error', '')}")
                    if res.get("stderr"):
                        print(res["stderr"].strip())
            else:
                print("DIRECT recipe (call vendor yourself, cheaper):")
                print(f"  via       : {res['via']}")
                print(f"  direct_id : {res['direct_id']}")
                print(f"  command   : {res['command_hint']}")
                print(f"  params    : {res['params']}")
        return 0 if out.get("result", {}).get("ok", True) else 1

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
