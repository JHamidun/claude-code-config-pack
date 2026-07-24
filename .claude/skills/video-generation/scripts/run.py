#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run.py — TURNKEY video-generation orchestrator.

One entry point: a brief → the whole pipeline under one launch (intake → flow select →
prompt build → model route [DIRECT-first, hf.exe only for exclusives] → parallel generate
[keyframes ×N + clips ×N] → audio → ffmpeg assemble → final platform export).

Mirrors a dev-workflow: deterministic fan-out + an approval GATE before the expensive
clip stage. Default mode is --dry-run (builds & prints the full PLAN, spends nothing).

It REUSES the existing scripts (no duplication):
  prompt kitchen → engines/higgsfield/scripts/prompt_builders.py
  model routing  → engines/higgsfield/scripts/router.py   (DIRECT vs hf.exe)
  keyframes      → scripts/nano_banana_keyframes.py        (Nano / Gemini, direct)
  clips          → scripts/runway_client.py (Seedance/Kling $0) | veo_image_to_video.py
  voiceover      → scripts/elevenlabs_voiceover.py          (YourFirstName voice)
  music          → scripts/lyria_music.py | elevenlabs_music.py
  assembly       → scripts/ffmpeg_assemble.py (VO+music+brand) | engines/.../assemble.py (atoms)

USAGE
  python run.py --brief brief.json                 # dry-run: print PLAN + write out/plan.json
  python run.py --brief brief.json --execute       # run it (GATE before clips; --yes to skip)
  python run.py --flow cinematic --story "..." --aspect 21:9 --platform youtube   # inline brief

BRIEF schema (JSON) — all optional except brief/story:
  {
    "flow": "cinematic|highMD|productMD|typographyMD|infographicMD|classicMD|simple",
    "brief": "premise / story / message",
    "aspect": "9:16|16:9|21:9|1:1",   "platform": "tiktok|reels|youtube|x|generic",
    "duration": 30,                    "palette": ["#0a0a0a","#00e5ff","#ff003c"],
    "voiceover_text": "...", "voice": "YOUR_ELEVENLABS_VOICE_ID", "music_prompt": "...",
    "scenes": [ {"prompt": "...", "motion": "slow push-in", "keyframe": "auto|path.png"} ],
    "out_dir": "./out"
  }
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass

HERE = Path(__file__).resolve().parent                       # video-generation/scripts
SKILL = HERE.parent                                          # video-generation
ENGINE = SKILL / "engines" / "higgsfield" / "scripts"
sys.path.insert(0, str(ENGINE))
import prompt_builders as pb   # noqa: E402
import router as rt           # noqa: E402

PARALLEL_KEYFRAMES = 4   # Nano empirical ceiling
PARALLEL_CLIPS = 2       # Runway exploreMode throttles ~3 → 2 is safer (Veo-fallback covers throttle anyway)

ASPECT_PLATFORM = {
    "tiktok": "9:16", "reels": "9:16", "shorts": "9:16",
    "youtube": "16:9", "x": "16:9", "generic": "16:9",
}

# --------------------------------------------------------------------------- #
# 1-2. INTAKE + FLOW SELECT
# --------------------------------------------------------------------------- #
def load_brief(args) -> dict:
    if args.brief:
        b = json.loads(Path(args.brief).read_text(encoding="utf-8"))
    else:
        b = {}
    # CLI overrides
    for k in ("flow", "aspect", "platform", "duration", "story", "out_dir"):
        v = getattr(args, k, None)
        if v is not None:
            b["brief" if k == "story" else k] = v
    b.setdefault("brief", b.get("story", ""))
    b.setdefault("flow", "simple")
    b.setdefault("platform", "generic")
    b.setdefault("aspect", ASPECT_PLATFORM.get(b["platform"], "16:9"))
    b.setdefault("duration", 30)
    b.setdefault("palette", [])
    b.setdefault("out_dir", "./out")
    b.setdefault("scenes", [])
    return b


MD_DOCTRINES = {"highMD", "productMD", "typographyMD", "infographicMD", "classicMD"}

# --------------------------------------------------------------------------- #
# 3. PROMPT BUILD (uses prompt_builders.py — the captured Higgsfield kitchen)
# --------------------------------------------------------------------------- #
def build_prompts(b: dict) -> dict:
    flow = b["flow"]
    out = {"flow": flow}
    if flow == "cinematic":
        out["cinematic_5"] = pb.build_cinematic_5({
            "premise": b["brief"], "aspect": b["aspect"], "color": b.get("palette"),
        })
        clips = out["cinematic_5"]["cinematic_prompt_writer"]  # list of per-clip dicts
        out["scenes"] = [{"prompt": c.get("prompt_text", ""), "motion": "", "keyframe": "auto"}
                         for c in clips]
    elif flow in MD_DOCTRINES:
        out["board"] = pb.build_board_spec(flow, b["palette"], brand=b.get("brand"))
        shots = b.get("scenes") or [f"beat {i+1}" for i in range(6)]
        out["sandwich"] = pb.build_sandwich_prompt(
            [s.get("prompt", s) if isinstance(s, dict) else s for s in shots],
            flow, b["palette"], b["aspect"])
        out["scenes"] = [{"prompt": out["sandwich"]["prompt_text"], "motion": "",
                          "keyframe": "board"}]  # MD = one continuous clip from the board sheet
    else:  # simple / explicit scenes — camera-rig per scene
        scenes = b.get("scenes") or [{"prompt": b["brief"], "motion": "slow push-in"}]
        out["scenes"] = [{
            "prompt": pb.build_cinematic_prompt(s.get("prompt", "") if isinstance(s, dict) else s),
            "motion": (s.get("motion", "") if isinstance(s, dict) else ""),
            "keyframe": (s.get("keyframe", "auto") if isinstance(s, dict) else "auto"),
        } for s in scenes]
    return out


# --------------------------------------------------------------------------- #
# 4. MODEL ROUTE (router.py — DIRECT-first; hf.exe only for exclusives)
# --------------------------------------------------------------------------- #
def plan_routing(b: dict, prompts: dict) -> dict:
    n = len(prompts["scenes"])
    kf_model = "gpt_image_2" if b["flow"] in MD_DOCTRINES else "nano_banana_2"
    video_model = "seedance_2_0"
    kf = rt.route(kf_model)
    clip = rt.route(video_model)
    routing = {
        "keyframes": {"model": kf_model, "n": n, "decision": kf["decision"],
                      "via": kf.get("via"), "command": kf.get("command_hint")},
        "clips": {"model": video_model, "n": n, "decision": clip["decision"],
                  "via": clip.get("via"), "command": clip.get("command_hint")},
    }
    if b.get("voiceover_text"):
        routing["voiceover"] = {"engine": "elevenlabs", "voice": b.get("voice", "YOUR_ELEVENLABS_VOICE_ID")}
    if b.get("music_prompt"):
        routing["music"] = {"engine": "lyria2 (commercial-safe) | elevenlabs_music (≤30s)"}
    return routing


def estimate(b: dict, routing: dict) -> dict:
    n = routing["clips"]["n"]
    per = b["duration"] / max(1, n)
    seed_direct = routing["clips"]["via"] == "runway"
    return {
        "scenes": n, "sec_per_scene": round(per, 1), "total_sec": b["duration"],
        "clip_cost": "$0 marginal (Runway Unlimited)" if seed_direct else "see router",
        "keyframe_cost": "$0–low (own GOOGLE/OPENAI key)",
        "note": "hf.exe credits spent ONLY on exclusives (none in this plan)"
                if routing["clips"]["decision"] == "direct" else "plan uses hf.exe — check credits",
    }


def build_plan(b: dict) -> dict:
    prompts = build_prompts(b)
    routing = plan_routing(b, prompts)
    return {
        "intake": {k: b[k] for k in ("flow", "aspect", "platform", "duration", "out_dir")},
        "brief": b["brief"][:300],
        "prompts": prompts,
        "routing": routing,
        "estimate": estimate(b, routing),
        "assembly": {"tool": "ffmpeg_assemble.py (VO+music+brand) → assemble.py platform_export",
                     "platform_export": "-14 LUFS / GOP 2s / h264 high@4.2"},
    }


# --------------------------------------------------------------------------- #
# 5-6. EXECUTE (parallel fan-out + GATE) — shells out to the real scripts
# --------------------------------------------------------------------------- #
def _run(cmd: list[str], label: str) -> dict:
    print(f"  ▸ {label}: {' '.join(str(c) for c in cmd)}")
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800)
        return {"label": label, "ok": r.returncode == 0, "out": (r.stdout or "")[-400:],
                "err": (r.stderr or "")[-400:]}
    except Exception as e:  # noqa: BLE001
        return {"label": label, "ok": False, "err": str(e)}


def execute(b: dict, plan: dict, assume_yes: bool) -> dict:
    out_dir = Path(b["out_dir"]).resolve()
    (out_dir / "keyframes").mkdir(parents=True, exist_ok=True)
    (out_dir / "clips").mkdir(parents=True, exist_ok=True)
    scenes = plan["prompts"]["scenes"]
    results = {"keyframes": [], "clips": [], "audio": [], "assemble": None}

    # --- Phase 5a: keyframes (parallel) — write shots.json, call nano_banana_keyframes.py ---
    shots = [{"slug": f"kf_{i:02d}", "prompt": s["prompt"], "anchor": i == 0}
             for i, s in enumerate(scenes) if s.get("keyframe") == "auto"]
    if shots:
        (out_dir / "shots.json").write_text(json.dumps(shots, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"\n[Phase 5a] {len(shots)} keyframes (parallel ≤{PARALLEL_KEYFRAMES}) → Nano/Gemini (direct)")
        results["keyframes"].append(_run(
            [sys.executable, str(HERE / "nano_banana_keyframes.py"), str(out_dir / "shots.json"),
             "--out", str(out_dir / "keyframes"), "--mode", "chained"], "keyframes"))

    # --- GATE before expensive clip stage ---
    if not assume_yes:
        print("\n⏸  APPROVAL GATE — keyframes done. Review them, then re-run with --execute --yes "
              "to render clips, or stop here. (Gate per Phase 5b doctrine.)")
        return results

    # --- Phase 5b: clips (parallel) — Seedance via Runway ($0), AUTO-FALLBACK to Veo on 429/throttle ---
    print(f"\n[Phase 5b] {len(scenes)} clips (parallel ≤{PARALLEL_CLIPS}) → Seedance/Runway ($0), Veo-fallback on throttle")
    def _veo_fallback(i, s, kf, out_clip):
        """Runway throttled/failed → render this clip via Veo (own GOOGLE_API_KEY, no Runway limit)."""
        if not kf.exists():
            return {"label": f"clip_{i:02d}", "ok": False, "err": "no keyframe for Veo fallback"}
        cj = out_dir / f"_veo_{i:02d}.json"
        cj.write_text(json.dumps([{"slug": f"kf_{i:02d}", "prompt": s["prompt"][:1000]}]), encoding="utf-8")
        rv = _run([sys.executable, str(HERE / "veo_image_to_video.py"), str(cj),
                   "--keyframes", str(out_dir / "keyframes"), "--out", str(out_dir / "clips"),
                   "--aspect", b["aspect"], "--duration", "6", "--workers", "1"], f"clip_{i:02d} VEO-fallback")
        veo_out = out_dir / "clips" / f"kf_{i:02d}.mp4"
        if veo_out.exists():
            veo_out.replace(out_clip)
            rv["ok"] = True
        return rv
    def render_clip(i_s):
        i, s = i_s
        kf = (out_dir / "keyframes" / f"kf_{i:02d}.png")
        out_clip = out_dir / "clips" / f"clip_{i:02d}.mp4"
        cmd = [sys.executable, str(HERE / "runway_client.py"), "generate",
               "--prompt", s["prompt"][:3400], "--duration", "5",
               "--aspect", b["aspect"], "--resolution", "720p", "--download", str(out_clip)]
        if kf.exists():
            cmd[3:3] = ["--image", str(kf)]
        r = {}
        for attempt in range(2):  # Runway with one 429-backoff retry
            r = _run(cmd, f"clip_{i:02d}" + (f" retry{attempt}" if attempt else ""))
            if r.get("ok") and out_clip.exists():
                return r
            if "429" not in (r.get("err", "") + r.get("out", "")):
                break
            time.sleep(20 * (attempt + 1))
        return _veo_fallback(i, s, kf, out_clip)  # Runway dead → Veo
    with ThreadPoolExecutor(max_workers=PARALLEL_CLIPS) as ex:
        results["clips"] = list(ex.map(render_clip, list(enumerate(scenes))))

    # --- Audio (optional) ---
    vo_path, music_path = out_dir / "vo.mp3", out_dir / "music.wav"
    if b.get("voiceover_text"):
        (out_dir / "vo.txt").write_text(b["voiceover_text"], encoding="utf-8")
        results["audio"].append(_run(
            [sys.executable, str(HERE / "elevenlabs_voiceover.py"), str(out_dir / "vo.txt"),
             "--out", str(vo_path), "--voice-id", b.get("voice", "YOUR_ELEVENLABS_VOICE_ID")], "voiceover"))
    if b.get("music_prompt"):
        results["audio"].append(_run(
            [sys.executable, str(HERE / "lyria_music.py"), b["music_prompt"],
             "--duration", str(b["duration"]), "--out", str(music_path)], "music"))

    # --- Phase 6: assemble (mix VO+music if present) → platform export ---
    print("\n[Phase 6] assemble → platform export")
    clips = sorted(str(p) for p in (out_dir / "clips").glob("clip_*.mp4"))
    final = out_dir / f"final_{b['platform']}.mp4"
    if clips:
        assembled = out_dir / "assembled.mp4"
        has_audio = (vo_path.exists() or music_path.exists())
        if has_audio:  # full pipeline: concat + VO/music mix + mux (ffmpeg_assemble.py)
            manifest = {"clips": [{"path": c} for c in clips], "aspect": b["aspect"],
                        "duration": b["duration"], "music_volume": 0.30}
            if vo_path.exists():
                manifest["voiceover"] = str(vo_path)
            if music_path.exists():
                manifest["music"] = str(music_path)
            (out_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
            results["assemble"] = _run(
                [sys.executable, str(HERE / "ffmpeg_assemble.py"), str(out_dir / "manifest.json"),
                 "--out", str(assembled)], "assemble(mix)")
        else:  # video-only
            results["assemble"] = _run(
                [sys.executable, str(ENGINE / "assemble.py"), "concat", *clips, str(assembled)], "concat")
        if assembled.exists():
            results["assemble"] = _run(
                [sys.executable, str(ENGINE / "assemble.py"), "platform_export", str(assembled), str(final)],
                "platform_export")
            print(f"\n✅ DONE → {final}")
    return results


# --------------------------------------------------------------------------- #
def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Turnkey video-generation orchestrator")
    ap.add_argument("--brief", help="brief JSON file")
    ap.add_argument("--flow"); ap.add_argument("--story"); ap.add_argument("--aspect")
    ap.add_argument("--platform"); ap.add_argument("--duration", type=int); ap.add_argument("--out-dir", dest="out_dir")
    ap.add_argument("--execute", action="store_true", help="run the plan (default: dry-run)")
    ap.add_argument("--yes", action="store_true", help="skip the approval gate before clips")
    args = ap.parse_args(argv)

    b = load_brief(args)
    plan = build_plan(b)
    out_dir = Path(b["out_dir"]).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")

    print("=" * 70)
    print(f"TURNKEY PLAN — flow={b['flow']}  aspect={b['aspect']}  platform={b['platform']}  {b['duration']}s")
    print("=" * 70)
    print(f"Scenes        : {len(plan['prompts']['scenes'])}")
    print(f"Keyframes     : {plan['routing']['keyframes']['decision'].upper()} "
          f"via {plan['routing']['keyframes']['via']} ({plan['routing']['keyframes']['model']})")
    print(f"Clips         : {plan['routing']['clips']['decision'].upper()} "
          f"via {plan['routing']['clips']['via']} ({plan['routing']['clips']['model']})")
    print(f"Estimate      : {plan['estimate']['clip_cost']} | {plan['estimate']['note']}")
    print(f"Plan written  : {out_dir / 'plan.json'}")

    if not args.execute:
        print("\n[DRY-RUN] nothing spent. Add --execute to render (GATE before clips; --yes to skip gate).")
        return 0

    res = execute(b, plan, args.yes)
    print("\n--- EXECUTION SUMMARY ---")
    print(json.dumps({k: (v if not isinstance(v, list) else [r.get("label") + ("✓" if r.get("ok") else "✗")
                          for r in v]) for k, v in res.items()}, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
