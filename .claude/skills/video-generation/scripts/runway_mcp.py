#!/usr/bin/env python3
"""
runway_mcp.py — MCP server for Runway ML internal web API.

Exposes Runway operations as MCP tools so Claude Code can call them directly
without browser automation. Uses paid web subscription via JWT (no public API
key needed, no per-call billing).

Tools exposed:
  - runway_profile          — get user profile + active plan
  - runway_teams            — list teams
  - runway_can_start        — check task quota for a feature
  - runway_estimate_cost    — estimate credits cost before running
  - runway_upload           — upload an image/video file → returns asset_id, cdn_url
  - runway_generate_seedance — Seedance 2.0 video generation (async, returns task_id)
  - runway_get_task         — poll task status, fetch artifacts
  - runway_wait_task        — block until task completes (returns artifacts)
  - runway_download         — download artifact URL to local file
  - runway_list_voices      — list TTS voices
"""
import os
import sys
import io
import json
import asyncio
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Add this dir to path so we can import runway_client
sys.path.insert(0, str(Path(__file__).parent))

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print("Install: pip install mcp", file=sys.stderr)
    sys.exit(1)

from runway_client import RunwayClient

mcp = FastMCP("runway")
_client: RunwayClient | None = None


def get_client() -> RunwayClient:
    global _client
    if _client is None:
        _client = RunwayClient()
    return _client


@mcp.tool()
def runway_profile() -> dict:
    """Get the current Runway user profile, plan, and team info."""
    p = get_client().profile()
    u = p.get("user", p)
    return {
        "email": u.get("email"),
        "plan": u.get("plan"),
        "plans": u.get("plans"),
        "plan_expires": u.get("planExpires"),
        "team_id": u.get("id"),
        "username": u.get("username"),
    }


@mcp.tool()
def runway_teams() -> dict:
    """List teams the user belongs to."""
    return get_client().teams()


@mcp.tool()
def runway_can_start(feature: str = "seedance_2") -> dict:
    """Check whether a new task of the given feature can be started.

    feature: 'seedance_2' | 'gen4' | 'gen4_turbo' | 'kling_3' | 'multi_shot_video' | etc.
    """
    return get_client().can_start_task(feature)


@mcp.tool()
def runway_estimate_cost(
    feature: str,
    duration: int = 5,
    resolution: str = "720p",
    aspect_ratio: str = "16:9",
    generate_audio: bool = True,
) -> dict:
    """Estimate credits cost for a generation.

    feature: 'seedance_2' | 'gen4' | 'kling_3' | etc.
    For seedance_2: uses duration, resolution, aspectRatio, generateAudio.
    For gen4: uses 'seconds' (duration is reused).
    """
    if feature.startswith("seedance"):
        opts = {
            "duration": duration,
            "resolution": resolution,
            "aspectRatio": aspect_ratio,
            "generateAudio": generate_audio,
        }
    elif feature.startswith("gen4"):
        opts = {"seconds": duration}
    else:
        opts = {"duration": duration}
    return get_client().estimate_cost(feature, opts)


@mcp.tool()
def runway_upload(file_path: str, asset_type: str = "image") -> dict:
    """Upload a local file to Runway as an asset.

    Returns: {id (assetId), cdn_url, preview_cdn_url, name, ...}.
    Use the returned id as assetId in referenceImages when creating a task.

    asset_type: 'image' | 'video' | 'audio' (image for keyframes).
    """
    ds = get_client().upload_file(file_path, asset_type)
    return {
        "asset_id": ds["id"],
        "cdn_url": ds.get("cdn_url"),
        "preview_cdn_url": ds.get("preview_cdn_url"),
        "name": ds.get("name"),
    }


@mcp.tool()
def runway_generate_seedance(
    prompt: str,
    image_path: str | None = None,
    end_image_path: str | None = None,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    resolution: str = "720p",
    generate_audio: bool = True,
    explore_mode: bool = True,
    name: str | None = None,
    wait: bool = False,
) -> dict:
    """Generate a Seedance 2.0 video.

    image_path: optional start frame (will be uploaded). For text-only video, omit.
    end_image_path: optional end frame for keyframe interpolation.
    duration: seconds (Seedance supports 5).
    aspect_ratio: '21:9' | '16:9' | '9:16' | '3:4' | '4:3' | '1:1'.
    resolution: '720p' | '1080p'.
    explore_mode: True uses queue (no priority); False uses paid priority queue.
    wait: if True, block until task finishes and return artifacts.

    Returns: task object. If wait=False, includes status='RUNNING'/'THROTTLED' etc.
    Use runway_get_task or runway_wait_task to poll.
    """
    c = get_client()
    if wait:
        task = c.generate_seedance(
            prompt=prompt,
            image_path=image_path,
            end_image_path=end_image_path,
            duration=duration,
            aspect_ratio=aspect_ratio,
            resolution=resolution,
            generate_audio=generate_audio,
            explore_mode=explore_mode,
            wait=True,
            name=name,
        )
    else:
        # Submit only, return task_id immediately
        ref_images = []
        if image_path:
            ds = c.upload_file(image_path, "image")
            ref_images.append({"assetId": ds["id"], "url": ds["cdn_url"], "type": "first_frame"})
        if end_image_path:
            ds = c.upload_file(end_image_path, "image")
            ref_images.append({"assetId": ds["id"], "url": ds["cdn_url"], "type": "end_frame"})  # API param=end_frame (UI label "last frame" lies)
        if not name:
            name = f"Seedance — {prompt[:60]}"
        options = {
            "name": name,
            "textPrompt": prompt,
            "duration": duration,
            "aspectRatio": aspect_ratio,
            "resolution": resolution,
            "generateAudio": generate_audio,
            "exploreMode": explore_mode,
            "referenceImages": ref_images,
            "numGenerations": 1,
            "creationSource": "tool-mode",
        }
        result = c.create_task("seedance_2", options)
        task = result.get("task", result)

    return {
        "task_id": task.get("id"),
        "status": task.get("status"),
        "progress": task.get("progressRatio"),
        "eta_seconds": task.get("estimatedTimeToStartSeconds"),
        "artifacts": c.list_artifacts(task),
    }


@mcp.tool()
def runway_generate_image(
    prompt: str,
    num_images: int = 1,
    image_size: str = "1K",
    model: str = "gemini-3.1-flash-image-preview",
    explore_mode: bool = True,
    name: str | None = None,
    wait: bool = True,
) -> dict:
    """Generate image via Nano Banana 2 (Gemini 3.1 Flash Image).

    image_size: '1K' | '2K' | '4K'
    num_images: 1..4
    """
    c = get_client()
    task = c.generate_image(
        prompt=prompt,
        num_images=num_images,
        image_size=image_size,
        model=model,
        explore_mode=explore_mode,
        wait=wait,
        name=name,
    )
    return {
        "task_id": task.get("id"),
        "status": task.get("status"),
        "progress": task.get("progressRatio"),
        "artifacts": c.list_artifacts(task),
    }


@mcp.tool()
def runway_generate_gen4(
    prompt: str,
    image_path: str | None = None,
    seconds: int = 5,
    aspect_ratio: str = "16:9",
    flavor: str = "gen4",
    explore_mode: bool = True,
    name: str | None = None,
    wait: bool = True,
) -> dict:
    """Generate video via Runway Gen-4 family.

    flavor: 'gen4' (60c/s) | 'gen4_turbo' (25c/s, image-to-video) | 'gen4.5' (text-to-video w/ keyframes)
    image_path: required for gen4_turbo (i2v); optional for gen4.5 keyframe.
    """
    c = get_client()
    task = c.generate_gen4(
        prompt=prompt,
        image_path=image_path,
        seconds=seconds,
        aspect_ratio=aspect_ratio,
        flavor=flavor,
        explore_mode=explore_mode,
        wait=wait,
        name=name,
    )
    return {
        "task_id": task.get("id"),
        "status": task.get("status"),
        "progress": task.get("progressRatio"),
        "artifacts": c.list_artifacts(task),
    }


@mcp.tool()
def runway_upscale_4k(
    task_artifact_id: str,
    name: str | None = None,
    wait: bool = True,
) -> dict:
    """Run 4K upscale on a completed task's artifact.

    task_artifact_id: id of artifact (NOT task id) — get it from artifacts[].id of a finished task.
    """
    c = get_client()
    task = c.upscale_4k(task_artifact_id=task_artifact_id, name=name, wait=wait)
    return {
        "task_id": task.get("id"),
        "status": task.get("status"),
        "artifacts": c.list_artifacts(task),
    }


@mcp.tool()
def runway_get_task(task_id: str) -> dict:
    """Get status of a task by id. Returns status + artifact URLs if completed.

    Possible statuses: PENDING, THROTTLED, RUNNING, SUCCEEDED, FAILED, CANCELED.
    """
    c = get_client()
    data = c.get_task(task_id)
    task = data.get("task", data)
    return {
        "task_id": task.get("id"),
        "task_type": task.get("taskType"),
        "status": task.get("status"),
        "progress": task.get("progressRatio"),
        "eta_seconds": task.get("estimatedTimeToStartSeconds"),
        "error": task.get("error"),
        "artifacts": c.list_artifacts(task),
    }


@mcp.tool()
def runway_wait_task(task_id: str, timeout: int = 1800, poll_interval: int = 5) -> dict:
    """Block until task completes (or fails). Returns final task state with artifacts.

    timeout: max seconds to wait (default 30 min).
    poll_interval: seconds between status checks.
    """
    c = get_client()
    task = c.wait_task(task_id, poll_interval=float(poll_interval), timeout=float(timeout))
    return {
        "task_id": task.get("id"),
        "status": task.get("status"),
        "progress": task.get("progressRatio"),
        "error": task.get("error"),
        "artifacts": c.list_artifacts(task),
    }


@mcp.tool()
def runway_download(url: str, out_path: str) -> dict:
    """Download an artifact (or any URL) to a local file.

    Useful for saving Seedance video outputs after a task SUCCEEDED.
    The artifact URLs from runway_get_task are signed (JWT) and expire — download soon.
    """
    c = get_client()
    p = c.download(url, out_path)
    return {"saved_to": p, "size_bytes": Path(p).stat().st_size}


@mcp.tool()
def runway_list_voices(limit: int = 30) -> dict:
    """List Runway built-in TTS voices."""
    v = get_client().voices()
    voices = v.get("voices", []) if isinstance(v, dict) else v
    if not isinstance(voices, list):
        return {"voices": []}
    out = []
    for voice in voices[:limit]:
        if isinstance(voice, dict):
            out.append({
                "id": voice.get("id"),
                "name": voice.get("name"),
                "description": voice.get("description"),
                "language": voice.get("language"),
            })
    return {"voices": out, "total": len(voices)}


if __name__ == "__main__":
    mcp.run()
