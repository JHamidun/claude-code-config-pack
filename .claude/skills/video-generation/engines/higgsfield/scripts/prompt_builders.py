#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt_builders.py — Local replication of Higgsfield's prompt-engineering.

Self-contained, dependency-free Python port of the Higgsfield skill references:

  1. Cinematic Studio Camera Rig  (CAMERA_MAP / LENS_MAP / FOCAL_PERSPECTIVE /
     APERTURE_EFFECT) + buildNanoBananaPrompt -> build_cinematic_prompt(...)
     Verbatim port of Anil-matcha/Open-Higgsfield-AI src/lib/promptUtils.js.
  2. ENHANCE_TAGS + QUICK_PROMPTS.
  3. build_sandwich_prompt(...) — universal 4-layer SANDWICH Seedance prompt
     (per-doctrine style blocks: highMD / productMD / typographyMD /
     infographicMD / classicMD) + mandatory tail-freeze + SFX-only audio.
  4. build_board_spec(...) — storyboard-sheet board_specs dict
     (chess_pattern, brand_reveal R1-R8, font_pairing, panel_layouts,
     punch_lines).
  5. build_cinematic_5(brief) — 5-subagent cinematic pipeline stub
     (dramaturg -> director -> style-architect -> shot-planner ->
     prompt-writer) returning the structured dict.

CLI:
    python prompt_builders.py cinematic  --base "..." [--camera ...] [...]
    python prompt_builders.py sandwich   --doctrine highMD --shots ... [...]
    python prompt_builders.py board      --doctrine highMD [...]

Sources (all confirmed against the skill references on disk):
  - references/registries/REGISTRIES.md
  - references/subagents-md-clips.md
  - references/subagents-md-boards.md
  - references/cinematic-subagents-schemas.md
"""

from __future__ import annotations

import argparse
import json
from typing import Any, Dict, List, Optional, Sequence


# =============================================================================
# 1. CINEMATIC STUDIO — CAMERA RIG (label -> prompt-token maps)
#    Verbatim from REGISTRIES.md / promptUtils.js. Default rig:
#    Modular 8K Digital / Creative Tilt Lens / 35mm / f/1.4.
# =============================================================================

# Camera body (camera_model_id) — label -> prompt token.
CAMERA_MAP: Dict[str, str] = {
    "Modular 8K Digital": "modular 8K digital cinema camera",
    "Full-Frame Cine Digital": "full-frame digital cinema camera",
    "Grand Format 70mm Film": "grand format 70mm film camera",
    "Studio Digital S35": "Super 35 studio digital camera",
    "Classic 16mm Film": "classic 16mm film camera",
    "Premium Large Format Digital": "premium large-format digital cinema camera",
}

# Lens (camera_lens_id) — label -> prompt token.
LENS_MAP: Dict[str, str] = {
    "Creative Tilt": "creative tilt lens effect",
    "Compact Anamorphic": "compact anamorphic lens",
    "Extreme Macro": "extreme macro lens",
    "70s Cinema Prime": "1970s cinema prime lens",
    "Classic Anamorphic": "classic anamorphic lens",
    "Premium Modern Prime": "premium modern prime lens",
    "Warm Cinema Prime": "warm-toned cinema prime",
    "Swirl Bokeh Portrait": "swirl bokeh portrait lens",
    "Vintage Prime": "vintage prime lens",
    "Halation Diffusion": "halation diffusion filter",
    "Clinical Sharp Prime": "ultra-sharp clinical prime",
}

# Focal length (camera_focal_length_id) — focal (str/int) -> perspective phrase.
FOCAL_PERSPECTIVE: Dict[str, str] = {
    "8": "ultra-wide",
    "14": "wide-angle",
    "24": "wide dynamic",
    "35": "natural cinematic",
    "50": "standard portrait",
    "85": "classic portrait",
}

# Aperture (camera_aperture_id) — aperture token -> depth-of-field effect.
APERTURE_EFFECT: Dict[str, str] = {
    "f/1.4": "shallow depth of field, creamy bokeh",
    "f/4": "balanced depth of field",
    "f/11": "deep focus, sharp foreground to background",
}

# Defaults (confirmed: Modular 8K Digital / Creative Tilt / 35mm / f/1.4).
DEFAULT_CAMERA = "Modular 8K Digital"
DEFAULT_LENS = "Creative Tilt"
DEFAULT_FOCAL = "35"
DEFAULT_APERTURE = "f/1.4"


def build_cinematic_prompt(
    base: str,
    camera: str = DEFAULT_CAMERA,
    lens: str = DEFAULT_LENS,
    focal: Any = DEFAULT_FOCAL,
    aperture: str = DEFAULT_APERTURE,
) -> str:
    """Port of buildNanoBananaPrompt (Open-Higgsfield-AI promptUtils.js), 1:1.

    JS reference:
        return [
          basePrompt,
          `shot on a ${CAMERA_MAP[camera]}`,
          `using a ${LENS_MAP[lens]} at ${focalLength}mm (${FOCAL_PERSPECTIVE[focalLength]})`,
          `aperture ${aperture}`,
          APERTURE_EFFECT[aperture],
          "cinematic lighting", "natural color science", "high dynamic range",
          "professional photography, ultra-detailed, 8K resolution"
        ].filter(Boolean).join(", ");

    Unknown keys degrade gracefully: the body/lens token falls back to the raw
    label, perspective/aperture-effect fall back to empty (filtered out), exactly
    mirroring JS `undefined` -> dropped-by-filter(Boolean) behaviour.
    """
    focal_key = str(focal)
    camera_token = CAMERA_MAP.get(camera, camera)
    lens_token = LENS_MAP.get(lens, lens)
    perspective = FOCAL_PERSPECTIVE.get(focal_key, "")
    aperture_effect = APERTURE_EFFECT.get(aperture, "")

    lens_clause = f"using a {lens_token} at {focal_key}mm"
    if perspective:
        lens_clause += f" ({perspective})"

    parts = [
        base,
        f"shot on a {camera_token}",
        lens_clause,
        f"aperture {aperture}",
        aperture_effect,
        "cinematic lighting",
        "natural color science",
        "high dynamic range",
        "professional photography, ultra-detailed, 8K resolution",
    ]
    # filter(Boolean) — drop falsy entries.
    return ", ".join(p for p in parts if p)


# =============================================================================
# 2. ENHANCE_TAGS + QUICK_PROMPTS (REGISTRIES.md)
# =============================================================================

ENHANCE_TAGS: Dict[str, List[str]] = {
    "quality": [
        "professional photography",
        "ultra-detailed",
        "8K resolution",
        "high dynamic range",
        "award-winning",
    ],
    "lighting": [
        "cinematic lighting",
        "golden hour",
        "dramatic studio lighting",
        "soft diffused light",
        "neon glow",
        "volumetric rays",
    ],
    "mood": [
        "moody atmosphere",
        "serene and peaceful",
        "epic and dramatic",
        "warm and cozy",
        "dark and mysterious",
    ],
    "style": [
        "photorealistic",
        "oil painting",
        "watercolor",
        "digital art",
        "concept art",
        "anime",
        "cyberpunk",
    ],
}

QUICK_PROMPTS: Dict[str, str] = {
    "Portrait": "professional portrait, 85mm lens, shallow depth of field, "
    "natural skin tones, soft window light",
    "Landscape": "sweeping landscape, golden hour, wide-angle, "
    "dramatic clouds, rich natural color",
    "Product": "product shot on clean white background, studio softbox "
    "lighting, sharp focus, commercial photography",
    "Fantasy": "epic fantasy scene, volumetric god rays, concept-art "
    "rendering, intricate detail, dramatic atmosphere",
    "Sci-Fi": "futuristic sci-fi cityscape, neon cyberpunk glow, rain-slicked "
    "streets, cinematic reflections",
    "Food": "editorial food photography, warm appetizing tones, shallow depth "
    "of field, soft natural light, garnished detail",
    "Architecture": "striking architecture, dramatic angles, strong leading "
    "lines, golden-hour contrast, ultra-detailed",
    "Fashion": "high-fashion Vogue editorial, dramatic studio lighting, bold "
    "styling, sharp couture detail",
}


# =============================================================================
# 3. UNIVERSAL 4-LAYER SANDWICH SEEDANCE PROMPT  (subagents-md-clips.md)
# =============================================================================

# Per-doctrine STYLE & PALETTE/SYSTEM block + camera doctrine + transitions.
# Each entry drives LAYER 2 (style block) and the camera-doctrine wording used
# in LAYER 3/4 and per-shot CAMERA cues.
DOCTRINE_BLOCKS: Dict[str, Dict[str, str]] = {
    "highMD": {
        "label": "highMD-clip — kinetic brand reel",
        "style": (
            "High-energy, hyperkinetic brand reel. Action-tier CGI commercial "
            "register. Saturated high contrast. Shot on ARRI Alexa Mini LF, "
            "180-degree shutter motion blur, fine 35mm grain."
        ),
        "camera_doctrine": "Hyperkinetic Chaos camera moves",
        "camera_cues": "Vertigo Pull / Crash-out Reveal / Drop-dive Past / "
        "Whip-pan Smear",
        "transition": (
            "Dramatic Particle Dissolve (chrome-dust / glitch): {source} "
            "dissolves through chrome-dust particles and reassembles as "
            "{target} over 0.4-0.6s"
        ),
        "variety": (
            "Variety Mandate: adjacent shots must change axis "
            "(X -> Y -> rotation -> hover -> push-in)."
        ),
    },
    "productMD": {
        "label": "productMD-clip — premium product (9 shots 3x3)",
        "style": (
            "15-second luxury chiaroscuro product commercial. Subject: product "
            "from @Image1, engineering-grade identity. Background: void black "
            "#000000. Lighting: volumetric beams + dust motes. Camera: Bot&Dolly "
            "Iris robotic arm precision."
        ),
        "camera_doctrine": "Bot&Dolly Iris robotic-arm precision (no shake)",
        "camera_cues": "Bot&Dolly snap / Programmed orbital sweep / Mechanical "
        "lift-and-rotate 45 degrees / Vertical Y-axis crane",
        "transition": (
            "Programmed robotic match-cut: {source} sweeps off via precision arc "
            "and reassembles as {target} over 0.4-0.6s"
        ),
        "variety": (
            "Overlays ONLY on shots 01/08/09 (white). Shots 02-07 = clean "
            "capture, no text. Special Beat on shot 04."
        ),
    },
    "typographyMD": {
        "label": "typographyMD-clip — type hero (6 shots)",
        "style": (
            "Typography-driven brand reel. 2d-editorial register. Massive 3D "
            "letterforms filling 80% of frame. Studio lighting, soft depth of "
            "field."
        ),
        "camera_doctrine": "static / Drift lock-on / slow glide (letters move, "
        "not the camera)",
        "camera_cues": "static hold / Drift lock-on / slow glide",
        "transition": (
            "INK FLOW / HALFTONE MORPH / DRAMATIC UNFURL: the letters of "
            "{source} flow and re-form into the letters of {target} over "
            "0.4-0.6s"
        ),
        "variety": "TEXT REVEAL: each shot reveals different words.",
    },
    "infographicMD": {
        "label": "infographicMD-clip — data / charts",
        "style": (
            "Data-driven infographic reel. Clean motion-graphics register. "
            "Layered Reveals: axes -> bar growth -> number ignites. Only real "
            "numbers (HR-5)."
        ),
        "camera_doctrine": "stable camera, Layered Reveals (axes -> bars -> "
        "number)",
        "camera_cues": "locked-off stable / subtle push-in on data",
        "transition": (
            "Data state transition via Dramatic Object Morph: {source} "
            "(e.g. bar chart) flows materially into {target} (e.g. line chart) "
            "over 0.4-0.6s"
        ),
        "variety": "Layered Reveals; data-state transitions between scenes.",
    },
    "classicMD": {
        "label": "classicMD-clip — classic hold",
        "style": (
            "Classic cinematic brand reel. Restrained, elegant register. "
            "Measured holds, deliberate composition, timeless color science."
        ),
        "camera_doctrine": "measured holds and slow deliberate moves",
        "camera_cues": "slow push-in / gentle drift / locked hold",
        "transition": (
            "Elegant cross-dissolve: {source} gently dissolves and resolves "
            "into {target} over 0.4-0.6s"
        ),
        "variety": "Classic hold: let each composition breathe before the cut.",
    },
}

# Mandatory tail freeze (subagents-md-clips.md step 6).
TAIL_FREEZE = (
    "13.7-15s MANDATORY SILENT TAIL PAUSE: hold final endcard composition "
    "completely silently, full brightness/saturation, camera motionless, "
    "subtle ambient room-tone drone only."
)


def _palette_clause(palette: Sequence[str]) -> str:
    """Render 'Palette: #HEX1,#HEX2,#HEX3'."""
    return "Palette: " + ",".join(palette)


def _normalize_shot(shot: Any, idx: int) -> Dict[str, Any]:
    """Coerce a shot entry (str or dict) into the canonical shot dict."""
    if isinstance(shot, str):
        return {"subject": shot}
    if isinstance(shot, dict):
        return dict(shot)
    return {"subject": str(shot)}


def build_sandwich_prompt(
    shots: List[Any],
    doctrine: str,
    palette: List[str],
    aspect: str = "9:16",
) -> Dict[str, Any]:
    """Universal 4-layer SANDWICH Seedance prompt from a storyboard.

    Implements the universal SANDWICH (subagents-md-clips.md):
      LAYER 1 (Opening, anti-grid)
      STYLE & PALETTE/SYSTEM BLOCK (per-doctrine) + Palette + camera/optics
      CHOREOGRAPHY SHOTS 1..N (LAYER 2 prefix + SUBJECT/CAMERA/LIGHT/PARALLAX,
        optional TEXT IN FRAME, TRANSITION between shots)
      LAYER 3 (Final Shot Lock) on the last shot
      LAYER 4 (Final Reminder)
      MANDATORY TAIL FREEZE 13.7-15s
      AUDIO: SFX-only, no dialogue, no music.

    Each shot may be a plain string (used as SUBJECT) or a dict with optional
    keys: subject, action, camera, light, parallax, text, sfx, transition.

    Returns the structured dict (prompt_text + closing_shot + elements_used +
    duration), matching the cinematic-prompt-writer JSON shape.
    """
    block = DOCTRINE_BLOCKS.get(doctrine, DOCTRINE_BLOCKS["classicMD"])
    norm_shots = [_normalize_shot(s, i) for i, s in enumerate(shots)]
    n = len(norm_shots)

    segments: List[str] = []

    # ---- LAYER 1: Opening (anti-grid) -----------------------------------
    segments.append(
        f"CRITICAL: Animate as ONE single continuous full-frame {aspect} "
        f"cinematic film. @Image1 is a PLANNING BRIEF — translate every panel "
        f"into an individual cinematic shot that occupies the complete {aspect} "
        f"screen, one shot at a time. Use @Image1 ONLY as visual reference for "
        f"composition/palette/identity — NEVER render the storyboard sheet "
        f"itself, its chrome layer, panel borders, or grid layout as scene "
        f"content."
    )

    # ---- STYLE & PALETTE/SYSTEM BLOCK -----------------------------------
    style_segment = (
        f"{block['style']} {_palette_clause(palette)}. "
        f"Camera doctrine: {block['camera_doctrine']} "
        f"({block['camera_cues']}). {block['variety']}"
    )
    segments.append(style_segment)

    # ---- CHOREOGRAPHY SHOTS 1..N ----------------------------------------
    sfx_cues: List[str] = []
    for i, shot in enumerate(norm_shots, start=1):
        is_last = i == n
        subject = shot.get("subject", f"shot {i}")
        action = shot.get("action", "")
        camera = shot.get("camera", block["camera_cues"].split(" / ")[0])
        light = shot.get("light", "cinematic key + rim, motivated practicals")
        parallax = shot.get("parallax", "FG 100% / MG 60% / BG 25%")

        # LAYER 2 prefix.
        shot_lines: List[str] = [
            f"SHOT {i:02d}: ENTIRE {aspect} frame fills with {subject}."
        ]

        subj_action = subject if not action else f"{subject}, {action}"
        shot_lines.append(
            f"SUBJECT: {subj_action} + CAMERA: {camera} + LIGHT: {light} + "
            f"PARALLAX: {parallax}."
        )

        # Optional TEXT IN FRAME (kinetic typography).
        text = shot.get("text")
        if text:
            position = shot.get("text_position", "centered")
            shot_lines.append(
                f"TEXT IN FRAME: '{text}' — bold kinetic typography, {position}. "
                f"TEXT PERSISTENCE: remains visible throughout."
            )

        # LAYER 3: Final Shot Lock (on last shot).
        if is_last:
            shot_lines.append(
                f"THIS FINAL SHOT IS A SINGLE FULL-FRAME COMPOSITION FILLING "
                f"THE ENTIRE {aspect} SCREEN. The frame surface is pure "
                f"brand-reveal scene content corner to corner."
            )

        # TRANSITION (junction to the NEXT shot, so not after the last).
        if not is_last:
            nxt = norm_shots[i].get("subject", f"shot {i + 1}")
            morph = block["transition"].format(source=subject, target=nxt)
            t_time = shot.get("transition_time", f"{i * 2:.1f}s")
            shot_lines.append(f"TRANSITION {t_time}: {morph}.")

        # Collect SFX cue for the audio block.
        sfx = shot.get("sfx")
        if sfx:
            sfx_cues.append(f"[{i:02d}] {sfx}")

        segments.append(" ".join(shot_lines))

    # ---- LAYER 4: Final Reminder ----------------------------------------
    segments.append(
        f"FINAL OUTPUT REMINDER: ONE single continuous full-frame {aspect} "
        f"cinematic film. Each shot is a complete fullscreen scene with "
        f"{block['camera_doctrine']} and DRAMATIC MATCH-CUT TRANSITIONS between "
        f"scenes."
    )

    # ---- MANDATORY TAIL FREEZE ------------------------------------------
    segments.append(TAIL_FREEZE)

    # ---- AUDIO (SFX-only) -----------------------------------------------
    sfx_text = "; ".join(sfx_cues) if sfx_cues else "ambient room-tone only"
    segments.append(
        f"Audio: ambient SFX only, no dialogue, no music (music in post). "
        f"Sound cues: {sfx_text}. SFX-only, speech absent."
    )

    prompt_text = " ".join(segments)
    closing_shot = norm_shots[-1].get("subject", "") if norm_shots else ""

    return {
        "case": "md-clip",
        "doctrine": doctrine,
        "doctrine_label": block["label"],
        "aspect": aspect,
        "palette": list(palette),
        "prompt_text": prompt_text,
        "closing_shot": closing_shot,
        "elements_used": [s.get("subject", "") for s in norm_shots],
        "duration": 15,
    }


# =============================================================================
# 4. STORYBOARD BOARD SPEC  (subagents-md-boards.md)
# =============================================================================

# Brand-reveal catalog R1-R8 (board_specs.brand_reveal_type).
BRAND_REVEAL_CATALOG: Dict[str, str] = {
    "R1": "Material assembly — brand mark coalesces from the signature material "
    "(liquid glass / lava / chrome).",
    "R2": "Volumetric beam reveal — product/logo lit by a single robotic beam in "
    "void black.",
    "R3": "Light-streak draw-on — logo drawn by a fast travelling light streak.",
    "R4": "Particle convergence — dust/sparks converge into the brand mark.",
    "R5": "Data-to-logo morph — final metric/chart morphs into the brand mark.",
    "R6": "Liquid pour fill — brand mark fills via liquid pour / ink flood.",
    "R7": "Typographic lockup — display + accent type snap into final lockup.",
    "R8": "Match-cut reveal — last scene object match-cuts directly into logo.",
}

# Per-doctrine board defaults (subagents-md-boards.md "Специфика").
BOARD_DOCTRINE_DEFAULTS: Dict[str, Dict[str, Any]] = {
    "highMD": {
        "format": "9:16",
        "grid": "3x2",
        "panels": 6,
        "sheet_bg": "#000000",
        "camera_mode": "Hyperkinetic",
        "chess_pattern": "B",
        "text_panel_ids": ["02", "04", "06"],
        "brand_reveal_type": "R1",
        "font_pairing": {"display": "Futura Condensed", "accent": "Futura"},
        "material_lock": "liquid glass / lava / chrome",
        "tier": "auto",
        "effects": "motion blur + bloom; NARRATIVE BEAT = peak phase "
        "(splash 1.2s, shatter 2.1s)",
    },
    "productMD": {
        "format": "16:9",
        "grid": "3x3",
        "panels": 9,
        "sheet_bg": "#DDDDDD",
        "camera_mode": "Bot&Dolly robotic",
        "chess_pattern": "Hybrid",
        "text_panel_ids": ["01", "08", "09"],
        "brand_reveal_type": "R2",
        "font_pairing": {"display": "Helvetica", "accent": "Helvetica Mono"},
        "material_lock": "engineering identity (PRODUCT BIBLE @Image1)",
        "tier": "director",
        "effects": "3px borders / 28px gutters / 40px margin; chrome monospace "
        "tech-notes (ACTION/CAMERA/LIGHT); Shot 04 = trick",
    },
    "typographyMD": {
        "format": "9:16",
        "grid": "3x2",
        "panels": 6,
        "sheet_bg": "#F5EDDF",
        "camera_mode": "static / drift",
        "chess_pattern": "A",
        "text_panel_ids": ["01", "03", "05"],
        "brand_reveal_type": "R7",
        "font_pairing": {"display": "Playfair Display", "accent": "Inter Mono"},
        "material_lock": "Type-As-Subject (letters 50-90% of frame)",
        "tier": "director",
        "effects": "size hierarchy L -> M -> S; 2-Font Lock; Tier(c) full chrome",
    },
    "infographicMD": {
        "format": "9:16",
        "grid": "3x2",
        "panels": 6,
        "sheet_bg": "cool charcoal",
        "camera_mode": "stable / layered reveal",
        "chess_pattern": "Hybrid",
        "text_panel_ids": ["02", "04", "06"],
        "brand_reveal_type": "R5",
        "font_pairing": {"display": "Inter Tight", "accent": "Inter Mono"},
        "material_lock": "HR-2 numbers 15-40% of height; HR-5 real "
        "metric_values_from_brief only",
        "tier": "guided",
        "effects": "step-build (axes -> bars -> number); Layout C; Tier(b) "
        "panel-captions chrome",
    },
    "classicMD": {
        "format": "16:9",
        "grid": "3x2",
        "panels": 6,
        "sheet_bg": "#111111",
        "camera_mode": "measured hold",
        "chess_pattern": "A",
        "text_panel_ids": ["01", "06"],
        "brand_reveal_type": "R8",
        "font_pairing": {"display": "Garamond", "accent": "Inter"},
        "material_lock": "timeless signature element",
        "tier": "auto",
        "effects": "elegant holds; deliberate composition",
    },
}

# Panel-layout codes A..G (board_specs.panel_layouts values).
PANEL_LAYOUT_CODES = ["A", "B", "C", "D", "E", "F", "G"]


def build_board_spec(
    doctrine: str,
    palette: List[str],
    panels: Optional[List[Any]] = None,
    brand: Optional[str] = None,
) -> Dict[str, Any]:
    """Build the universal board_specs dict (subagents-md-boards.md).

    Produces: chess_pattern, brand_reveal (type + R1-R8 description),
    font_pairing, panel_layouts, punch_lines, plus the full board_specs /
    panels / prompt scaffold for a gpt_image_2 storyboard sheet.

    `panels` may be omitted (auto-built from the doctrine panel count) or a
    list of strings/dicts describing each panel.
    """
    d = BOARD_DOCTRINE_DEFAULTS.get(doctrine, BOARD_DOCTRINE_DEFAULTS["classicMD"])
    panel_count = d["panels"]
    brand = brand or "BRAND"

    # Normalize / auto-fill panels.
    norm_panels: List[Dict[str, Any]] = []
    text_ids = set(d["text_panel_ids"])
    brand_panel_id = f"{panel_count:02d}"
    for i in range(1, panel_count + 1):
        pid = f"{i:02d}"
        role = "text" if pid in text_ids else "visual"
        if pid == brand_panel_id:
            role = "brand"
        caption = ""
        if panels and i <= len(panels):
            src = panels[i - 1]
            if isinstance(src, str):
                caption = src
            elif isinstance(src, dict):
                caption = src.get("caption", "")
                role = src.get("role", role)
        norm_panels.append(
            {
                "id": pid,
                "timecode": f"{(i - 1) * 2.0:.1f}s",
                "role": role,
                "caption": caption,
            }
        )

    # panel_layouts: {"01":"A", "02":"B", ...} cycling A..G.
    panel_layouts = {
        f"{i:02d}": PANEL_LAYOUT_CODES[(i - 1) % len(PANEL_LAYOUT_CODES)]
        for i in range(1, panel_count + 1)
    }

    # punch_lines: keyed per text panel (auto placeholders unless provided).
    punch_lines: Dict[str, str] = {}
    for pid in d["text_panel_ids"]:
        cap = ""
        if panels:
            idx = int(pid) - 1
            if 0 <= idx < len(panels):
                src = panels[idx]
                cap = src if isinstance(src, str) else src.get("caption", "")
        punch_lines[pid] = cap or f"<punch line for panel {pid}>"

    reveal_type = d["brand_reveal_type"]
    board_specs = {
        "project_title": f"{brand} — {doctrine}",
        "duration": 15,
        "format": d["format"],
        "style_aesthetic": d["camera_mode"],
        "camera_mode": d["camera_mode"],
        "palette": list(palette),
        "tone_descriptors": [],
        "style_descriptors": [],
        "chess_pattern": d["chess_pattern"],
        "text_panel_ids": list(d["text_panel_ids"]),
        "brand_panel_id": brand_panel_id,
        "brand_mode": "logo_reveal",
        "brand_reveal_type": reveal_type,
        "brand_reveal": {reveal_type: BRAND_REVEAL_CATALOG.get(reveal_type, "")},
        "font_pairing": dict(d["font_pairing"]),
        "panel_layouts": panel_layouts,
        "punch_lines": punch_lines,
        "brand_tagline": f"{brand} — tagline",
    }

    # gpt_image_2 board prompt (universal board structure).
    board_prompt = (
        f"GRID LAYOUT & CHROME: {d['grid']} grid storyboard sheet, "
        f"sheet background {d['sheet_bg']}, hairline gutters, metadata chips "
        f"only in chrome margins. "
        f"STYLE & PALETTE LOCK: {d['camera_mode']} register, palette "
        f"{','.join(palette)}, ALL PANELS COHERENT WORLD. "
        f"SUBJECT & MATERIAL LOCK: {d['material_lock']}; signature element "
        f"consistent across panels. "
        f"PANEL BREAKDOWN 01..{panel_count}: each panel = CONTENT / NARRATIVE "
        f"BEAT / LIGHT[TYPE/DIRECTION/DOES] / EFFECTS ({d['effects']}). "
        f"TEXT IN PANEL: chess-pattern '{d['chess_pattern']}' on panels "
        f"{','.join(d['text_panel_ids'])}. "
        f"BRAND REVEAL: Panel {brand_panel_id}, type {reveal_type} — "
        f"{BRAND_REVEAL_CATALOG.get(reveal_type, '')} "
        f"RULE 10 SAFETY: no metadata-chips inside panels, only in chrome fields."
    )

    return {
        "case": "motion-design-board",
        "input_tier": d["tier"],
        "doctrine": doctrine,
        "board_specs": board_specs,
        "panels": norm_panels,
        "prompt": board_prompt,
    }


# =============================================================================
# 5. CINEMATIC 5-SUBAGENT PIPELINE  (cinematic-subagents-schemas.md)
#    dramaturg -> director -> style-architect -> shot-planner -> prompt-writer
# =============================================================================


def _clip_count(brief: Dict[str, Any]) -> int:
    """Resolve clip count (4 / 8 / 12) from the brief."""
    n = int(brief.get("clips", 4) or 4)
    if n <= 4:
        return 4
    if n <= 8:
        return 8
    return 12


def build_cinematic_5(brief: Dict[str, Any]) -> Dict[str, Any]:
    """Chain the 5 cinematic enhancer subagents into one structured dict.

    Stub orchestration that returns the canonical JSON shapes from
    cinematic-subagents-schemas.md for each stage:
      1. cinematic-dramaturg     (Want/Mask/Tell, narrative_shape, arc, tension)
      2. cinematic-director      (vision, motifs, rhythm_map, bold_image, notes)
      3. cinematic-style-architect (film_lock, scene_locks, dp_reference)
      4. cinematic-shot-planner  (shot_plan, junctions, transition_table, ledger)
      5. cinematic-prompt-writer (final 5-block prompt_text per clip)

    `brief` keys (all optional): premise, genre, characters (list of dicts),
    locations (list), clips, aspect, resolution, audio.
    """
    if isinstance(brief, str):
        brief = {"premise": brief}

    premise = brief.get("premise", "")
    genre = brief.get("genre", "drama")
    aspect = brief.get("aspect", "16:9")
    resolution = brief.get("resolution", "1080p")
    n_clips = _clip_count(brief)

    # Characters / locations (with safe defaults).
    chars_in = brief.get("characters") or [
        {"name": "Protagonist", "appearance": "to be defined in Phase 1"}
    ]
    locs_in = brief.get("locations") or [
        {"name": "Primary location", "description": premise or "a single set",
         "mood": "tense"}
    ]

    # ---- 1) cinematic-dramaturg -----------------------------------------
    characters = []
    for c in chars_in:
        characters.append(
            {
                "name": c.get("name", "Character"),
                "want": c.get("want", "external goal"),
                "mask": c.get("mask", "the facade they present"),
                "tell": c.get("tell", "the hidden vulnerability"),
                "appearance": c.get("appearance", "for Phase 1"),
            }
        )
    locations = [
        {
            "name": l.get("name", "Location"),
            "description": l.get("description", ""),
            "mood": l.get("mood", "neutral"),
        }
        for l in locs_in
    ]
    arc_clips = []
    functions = [
        "Exposition",
        "Inciting incident",
        "Rising action",
        "Midpoint turn",
        "Complication",
        "Crisis",
        "Climax",
        "Reversal",
        "Falling action",
        "Resolution beat",
        "Coda",
        "Final image",
    ]
    for i in range(1, n_clips + 1):
        arc_clips.append(
            {
                "n": i,
                "function": functions[(i - 1) % len(functions)],
                "description": f"Clip {i} advances the {genre} through "
                f"{functions[(i - 1) % len(functions)].lower()}.",
            }
        )
    # Simple symmetric tension curve scaled to clip count.
    tension_curve = [3 + (i % 4) * 2 for i in range(n_clips)]
    if n_clips >= 4:
        tension_curve[-1] = max(3, tension_curve[-1] - 4)

    dramaturg = {
        "mode_recommendation": brief.get(
            "mode_recommendation", "full_lw" if n_clips > 4 else "lite"
        ),
        "characters": characters,
        "locations": locations,
        "narrative_shape": brief.get("narrative_shape", "Unraveling"),
        "arc_structure": {"type": str(n_clips), "clips": arc_clips},
        "tension_curve": tension_curve,
        "genre_engine": {
            "genre": genre,
            "story_engine": brief.get("story_engine", "character under pressure"),
            "resolution_form": brief.get("resolution_form", "earned reversal"),
        },
    }

    # ---- 2) cinematic-director ------------------------------------------
    bold_index = min(3, n_clips)
    director_notes = []
    rhythm_cycle = ["HOLD", "measured", "staccato"]
    for i in range(1, n_clips + 1):
        director_notes.append(
            {
                "clip_n": i,
                "tempo": rhythm_cycle[(i - 1) % len(rhythm_cycle)],
                "motifs_here": [],
                "camera_move": "slow push-in revealing psychology",
                "is_bold_image": i == bold_index,
            }
        )
    director = {
        "vision": brief.get("vision", f"A {genre} told through restraint and "
                                      f"one unforgettable image."),
        "controlling_idea": brief.get(
            "controlling_idea", "What is hidden cannot stay hidden."
        ),
        "motifs": brief.get("motifs", ["recurring light motif", "a held object"]),
        "rhythm_map": [rhythm_cycle[(i) % len(rhythm_cycle)] for i in
                       range(min(3, n_clips))],
        "camera_narration_moves": [
            f"Clip {i}: camera move revealing character psychology"
            for i in range(1, n_clips + 1)
        ],
        "bold_image": {
            "clip_index": bold_index,
            "description": "one striking, burned-in frame",
        },
        "director_notes": director_notes,
        "variety_seed": brief.get("variety_seed", "vs-001"),
    }

    # ---- 3) cinematic-style-architect -----------------------------------
    style_architect = {
        "film_lock": {
            "color": brief.get("color", "teal-and-amber, filmic"),
            "temp": brief.get("temp", "warm"),
            "sensor": brief.get("sensor", "ARRI Alexa 65"),
            "lens": brief.get("lens", "Vintage Anamorphic"),
            "light_philosophy": brief.get(
                "light_philosophy", "Motivated single-source light shaping mood."
            ),
            "camera_energy": brief.get(
                "camera_energy", "No handheld shakes; deliberate, locked moves."
            ),
            "ratio": aspect,
            "resolution": resolution,
        },
        "scene_locks": [
            {
                "scene_group": list(range(1, n_clips + 1)),
                "light_setup": "key from frame-left, soft fill, hard rim",
                "time_weather": brief.get("time_weather", "dusk, clear"),
            }
        ],
        "dp_reference": brief.get("dp_reference", "Roger Deakins (under the hood)"),
        "user_facing_style": brief.get(
            "user_facing_style",
            "A warm, anamorphic look — deliberate camera, single-source light, "
            "rich filmic color.",
        ),
    }

    # ---- 4) cinematic-shot-planner --------------------------------------
    shot_plan = []
    junctions = []
    transition_table = []
    junction_types = ["Continuous", "Scene_change", "Temporal_ellipsis"]
    for i in range(1, n_clips + 1):
        open_shot = f"Wide establishing shot for clip {i}"
        close_shot = f"Close-up resolving clip {i}"
        shot_plan.append(
            {
                "clip_n": i,
                "function": functions[(i - 1) % len(functions)],
                "duration": "12s",
                "beats": [
                    f"physical action A in zone X (clip {i})",
                    "reaction B conveyed through micro-expression",
                ],
                "tension": tension_curve[i - 1] if i - 1 < len(tension_curve)
                else 3,
                "opening_shot": open_shot,
                "closing_shot": close_shot,
            }
        )
        if i < n_clips:
            jt = junction_types[(i - 1) % len(junction_types)]
            junctions.append(
                {"pair": f"{i}->{i + 1}", "type": jt, "bridge": "match on action"}
            )
            transition_table.append(
                {
                    "clip_n": i,
                    "end_state": f"end state of clip {i}",
                    "junction_type": jt,
                    "bridge": "match on action",
                    "start_state_next": f"start state of clip {i + 1}",
                }
            )
    shot_planner = {
        "shot_plan": shot_plan,
        "junctions": junctions,
        "transition_table": transition_table,
        "state_ledger": {
            "initial_states": brief.get(
                "initial_states", {"protagonist_wardrobe": "as established"}
            ),
            "deltas": brief.get("deltas", []),
        },
    }

    # ---- 5) cinematic-prompt-writer (final, 5-block per clip) -----------
    fl = style_architect["film_lock"]
    sl = style_architect["scene_locks"][0]
    prompt_writer: List[Dict[str, Any]] = []
    for sp in shot_plan:
        i = sp["clip_n"]
        env_id = f"env_{i}"
        char_ids = [
            f"{c['name'].lower().replace(' ', '_')}_char_id" for c in characters
        ]
        cast_clause = "; ".join(
            f"<element-tag value=\"{cid}\">…</element-tag> is "
            f"{characters[k].get('appearance', 'as defined')}"
            for k, cid in enumerate(char_ids)
        )
        block1 = (
            f"Cinematic film still, shot on {fl['sensor']} with {fl['lens']}. "
            f"{sl['light_setup']} matching {fl['light_philosophy']} Color graded "
            f"as {fl['color']}, {fl['temp']} temperature. Visual rendering: "
            f"fine grain, soft halation, natural skin texture."
        )
        block2 = (
            f"Set: <element-tag value=\"{env_id}\">…</element-tag> which is "
            f"{locations[0]['description'] or 'the primary set'}, featuring the "
            f"anchor object as a central anchor. Cast: {cast_clause}."
        )
        block3 = (
            f"Opening frame: {sp['opening_shot']}. Initial states: "
            f"{shot_planner['state_ledger']['initial_states']}."
        )
        block4 = (
            f"Action sequence: Beat 1: {sp['beats'][0]}. Beat 2: {sp['beats'][1]} "
            f"with Acting block — micro-pauses before eye movement, eye-line "
            f"shift, catch-lights in the pupils, audible breath, visible skin "
            f"pore detail. Beat 3 (Transition/State Delta): action triggering "
            f"the next state."
        )
        audio_scheme = brief.get(
            "audio",
            "ambient bed with synchronized cues, no dialogue unless specified",
        )
        block5 = (
            f"Closing frame ends on {sp['closing_shot']}. Audio and sound "
            f"design: {audio_scheme}."
        )
        prompt_text = " ".join([block1, block2, block3, block4, block5])
        prompt_writer.append(
            {
                "clip_n": i,
                "prompt_text": prompt_text,
                "closing_shot": sp["closing_shot"],
                "elements_used": [
                    f"<element-tag value=\"{cid}\">…</element-tag>"
                    for cid in char_ids
                ]
                + [f"<element-tag value=\"{env_id}\">…</element-tag>"],
                "duration": 12,
            }
        )

    return {
        "case": "cinematic-flow",
        "model": "seedance_2_0",
        "brief": {"premise": premise, "genre": genre, "clips": n_clips,
                  "aspect": aspect},
        "cinematic_dramaturg": dramaturg,
        "cinematic_director": director,
        "cinematic_style_architect": style_architect,
        "cinematic_shot_planner": shot_planner,
        "cinematic_prompt_writer": prompt_writer,
    }


# =============================================================================
# CLI
# =============================================================================


def _parse_list(value: Optional[str]) -> List[str]:
    """Split a comma/pipe-delimited CLI string into a clean list."""
    if not value:
        return []
    raw = value.replace("|", ",")
    return [item.strip() for item in raw.split(",") if item.strip()]


def _build_cli() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="prompt_builders",
        description="Local Higgsfield prompt-engineering builders.",
    )
    sub = p.add_subparsers(dest="command", required=True)

    # cinematic ----------------------------------------------------------
    c = sub.add_parser("cinematic", help="Camera-rig cinematic image prompt.")
    c.add_argument("--base", required=True, help="Base subject prompt.")
    c.add_argument("--camera", default=DEFAULT_CAMERA)
    c.add_argument("--lens", default=DEFAULT_LENS)
    c.add_argument("--focal", default=DEFAULT_FOCAL)
    c.add_argument("--aperture", default=DEFAULT_APERTURE)

    # sandwich -----------------------------------------------------------
    s = sub.add_parser("sandwich", help="4-layer SANDWICH Seedance prompt.")
    s.add_argument(
        "--doctrine",
        default="classicMD",
        choices=list(DOCTRINE_BLOCKS.keys()),
    )
    s.add_argument(
        "--shots",
        required=True,
        help="Shots separated by '|' (each used as SUBJECT).",
    )
    s.add_argument("--palette", default="#000000,#FFFFFF,#888888")
    s.add_argument("--aspect", default="9:16")

    # board --------------------------------------------------------------
    b = sub.add_parser("board", help="Storyboard board_specs sheet.")
    b.add_argument(
        "--doctrine",
        default="classicMD",
        choices=list(BOARD_DOCTRINE_DEFAULTS.keys()),
    )
    b.add_argument("--palette", default="#000000,#FFFFFF,#888888")
    b.add_argument("--brand", default="BRAND")
    b.add_argument(
        "--panels",
        default="",
        help="Optional panel captions separated by '|'.",
    )

    return p


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _build_cli().parse_args(argv)

    if args.command == "cinematic":
        out: Any = build_cinematic_prompt(
            args.base, args.camera, args.lens, args.focal, args.aperture
        )
    elif args.command == "sandwich":
        shots = [s.strip() for s in args.shots.split("|") if s.strip()]
        out = build_sandwich_prompt(
            shots, args.doctrine, _parse_list(args.palette), args.aspect
        )
    elif args.command == "board":
        panels = [p.strip() for p in args.panels.split("|") if p.strip()] or None
        out = build_board_spec(
            args.doctrine, _parse_list(args.palette), panels, args.brand
        )
    else:  # pragma: no cover - argparse enforces a valid command.
        return 2

    if isinstance(out, str):
        print(out)
    else:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
