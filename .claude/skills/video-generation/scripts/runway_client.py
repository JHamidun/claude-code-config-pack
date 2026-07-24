#!/usr/bin/env python3
"""
runway_client.py — Python client for Runway ML internal web API.

Auth: JWT from web app localStorage (RW_TOKEN_PLACEHOLDER). Stored in
~/.claude/.credentials.master.env as RUNWAY_TOKEN_PLACEHOLDER. Valid ~30 days.

Capabilities (no public Runway API key needed — uses paid web subscription):
  - Upload images/videos (3-stage S3 multipart)
  - Create generation tasks (Seedance 2.0, Gen-4.5, Kling 3.0, etc.)
  - Poll task status, fetch artifacts (video URLs)
  - Estimate credits cost
  - List sessions, teams, profile

Usage examples (CLI):

  # Profile / status
  python runway_client.py profile
  python runway_client.py teams
  python runway_client.py can-start seedance_2

  # Estimate cost
  python runway_client.py estimate seedance_2 --duration 5 --aspect 21:9 --resolution 720p

  # Upload an image (returns asset_id and CDN url)
  python runway_client.py upload C:/path/to/frame.jpg

  # Generate a Seedance 2.0 video (start frame keyframe)
  python runway_client.py generate \\
    --type seedance_2 \\
    --prompt "Eyes slowly open. Subtle head turn." \\
    --image C:/path/to/frame.jpg \\
    --duration 5 --aspect 21:9 --resolution 720p \\
    --wait --download out.mp4

  # Poll a task by id
  python runway_client.py task <task_id>
"""
import os
import sys
import io
import json
import time
import argparse
import mimetypes
from pathlib import Path
from typing import Optional, Dict, List

# Force UTF-8 stdout on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

try:
    from dotenv import load_dotenv
except ImportError:
    print("Install: pip install python-dotenv requests", file=sys.stderr)
    sys.exit(1)

import requests

load_dotenv(os.path.expanduser("~/.claude/.credentials.master.env"))

JWT = os.getenv("RUNWAY_TOKEN_PLACEHOLDER")
TEAM_ID = int(os.getenv("RUNWAY_TEAM_ID", "0"))
EMAIL = os.getenv("RUNWAY_USER_EMAIL", "")

API_BASE = "https://api.runwayml.com"
ORIGIN = "https://app.runwayml.com"


class RunwayClient:
    """Runway ML internal web API client (uses paid subscription via JWT)."""

    def __init__(self, jwt: Optional[str] = None, team_id: Optional[int] = None):
        self.jwt = jwt or JWT
        self.team_id = team_id or TEAM_ID
        if not self.jwt:
            raise RuntimeError("Missing RUNWAY_TOKEN_PLACEHOLDER. Run `python runway_client.py extract-jwt` from logged-in browser.")
        self.session = requests.Session()
        headers = {
            "Authorization": f"Bearer {self.jwt}",
            "Origin": ORIGIN,
            "Referer": ORIGIN + "/",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        }
        if self.team_id:
            headers["X-Runway-Workspace"] = str(self.team_id)
        self.session.headers.update(headers)

    # ---------- Helpers ----------

    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        if params is None:
            params = {}
        if "asTeamId" not in params and self.team_id:
            params["asTeamId"] = self.team_id
        r = self.session.get(f"{API_BASE}{path}", params=params)
        r.raise_for_status()
        return r.json()

    def _post(self, path: str, json_body: Optional[Dict] = None, params: Optional[Dict] = None) -> Dict:
        params = params or {}
        if "asTeamId" not in params and self.team_id and "/uploads" not in path:
            # /uploads endpoint doesn't take asTeamId
            pass
        r = self.session.post(f"{API_BASE}{path}", json=json_body, params=params)
        if not r.ok:
            print(f"POST {path} → {r.status_code}: {r.text[:500]}", file=sys.stderr)
        r.raise_for_status()
        return r.json()

    # ---------- Profile / Teams ----------

    def profile(self) -> Dict:
        return self._get("/v1/profile")

    def profile_for_team(self) -> Dict:
        return self._get("/v1/profile_for_members")

    def features(self) -> Dict:
        return self._get("/v1/profile/features")

    def teams(self) -> Dict:
        return self._get("/v1/teams")

    def team_members(self, team_id: Optional[int] = None) -> Dict:
        tid = team_id or self.team_id
        return self._get(f"/v1/teams/{tid}/members")

    def can_start_task(self, feature: str = "seedance_2", mode: str = "credits") -> Dict:
        return self._get("/v1/tasks/can_start", {"asTeamId": self.team_id, "mode": mode, "feature": feature})

    # ---------- Cost Estimation ----------

    def estimate_cost(self, feature: str, task_options: Dict, count: int = 1) -> Dict:
        """Estimate credit cost before running.

        feature examples: 'seedance_2', 'gen4', 'gen4_turbo', 'kling_3', etc.
        task_options for seedance_2: {duration, resolution, aspectRatio, generateAudio}
        task_options for gen4: {seconds}
        """
        return self._post("/v1/billing/estimate_feature_cost_credits", {
            "feature": feature,
            "count": count,
            "asTeamId": self.team_id,
            "taskOptions": task_options,
        })

    # ---------- Upload (3-stage) ----------

    def upload_file(self, file_path: str, asset_type: str = "image") -> Dict:
        """Upload a file as a Runway dataset (asset).

        Returns: {dataset: {id, ...}, cdn_url, ...}
        Use dataset.id as assetId in referenceImages.
        """
        p = Path(file_path)
        if not p.exists():
            raise FileNotFoundError(file_path)
        size = p.stat().st_size
        filename = p.name
        mime = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        data = p.read_bytes()

        # 1. Get signed S3 URLs (PREVIEW + DATASET)
        preview = self._post("/v1/uploads", {"filename": filename, "numberOfParts": 1, "type": "DATASET_PREVIEW"})
        dataset = self._post("/v1/uploads", {"filename": filename, "numberOfParts": 1, "type": "DATASET"})

        # 2. PUT bytes to S3 (both preview and dataset use same bytes for simple case)
        def _put_s3(upload_url: str) -> str:
            r = requests.put(upload_url, data=data, headers={"Content-Type": mime})
            r.raise_for_status()
            etag = (r.headers.get("ETag") or r.headers.get("Etag") or "").strip('"')
            return etag

        preview_etag = _put_s3(preview["uploadUrls"][0])
        dataset_etag = _put_s3(dataset["uploadUrls"][0])

        # 3. Complete uploads
        preview_complete = self._post(
            f"/v1/uploads/{preview['id']}/complete",
            {"parts": [{"PartNumber": 1, "ETag": preview_etag}]},
        )
        dataset_complete = self._post(
            f"/v1/uploads/{dataset['id']}/complete",
            {"parts": [{"PartNumber": 1, "ETag": dataset_etag}]},
        )

        # 4. Get image dimensions if it's an image
        width, height = None, None
        if asset_type == "image":
            try:
                from PIL import Image
                img = Image.open(p)
                width, height = img.size
            except Exception:
                pass

        # 5. Create dataset record
        body = {
            "fileCount": 1,
            "name": filename,
            "uploadId": dataset["id"],
            "previewUploadIds": [preview["id"]],
            "type": {"name": asset_type, "type": asset_type, "isDirectory": False},
            "asTeamId": self.team_id,
            "privateInTeam": True,
        }
        if width and height:
            body["metadata"] = {"size": {"width": width, "height": height}}

        result = self._post("/v1/datasets", body)
        ds = result.get("dataset", result)
        ds["cdn_url"] = dataset_complete["url"]
        ds["preview_cdn_url"] = preview_complete["url"]
        return ds

    # ---------- Tasks ----------

    def create_task(self, task_type: str, options: Dict) -> Dict:
        """Create a generation task.

        task_type: 'seedance_2', 'gen4', 'kling_3', 'multi_shot_video', etc.
        options: model-specific. For seedance_2:
          {
            name: str,
            textPrompt: str,
            duration: int,
            aspectRatio: '21:9'|'16:9'|'9:16'|'3:4'|'4:3'|'1:1',
            resolution: '720p'|'1080p',
            generateAudio: bool,
            exploreMode: bool,
            referenceImages: [{assetId, url, type: 'first_frame'|'last_frame'}],
          }
        """
        return self._post("/v1/tasks", {"taskType": task_type, "options": options}, params={"asTeamId": self.team_id})

    def get_task(self, task_id: str) -> Dict:
        return self._get(f"/v1/tasks/{task_id}")

    def wait_task(self, task_id: str, poll_interval: float = 3.0, timeout: float = 1800) -> Dict:
        """Poll until task is SUCCEEDED or FAILED."""
        start = time.time()
        while True:
            data = self.get_task(task_id)
            task = data.get("task", data)
            status = task.get("status")
            progress = task.get("progressRatio", "?")
            print(f"[{int(time.time()-start)}s] status={status} progress={progress}", file=sys.stderr, flush=True)
            if status in ("SUCCEEDED", "FAILED", "CANCELED"):
                return task
            if time.time() - start > timeout:
                raise TimeoutError(f"Task {task_id} did not finish in {timeout}s")
            time.sleep(poll_interval)

    def list_artifacts(self, task: Dict) -> List[str]:
        """Extract output URLs from a finished task."""
        urls = []
        for art in task.get("artifacts", []) or []:
            if isinstance(art, dict):
                u = art.get("url") or art.get("preview_url")
                if u:
                    urls.append(u)
            elif isinstance(art, str):
                urls.append(art)
        return urls

    # ---------- Sessions ----------

    def get_session(self, session_id: str) -> Dict:
        return self._get(f"/v1/sessions/{session_id}")

    def session_assets(self, session_id: str, limit: int = 500) -> Dict:
        return self._get(f"/v1/sessions/{session_id}/assets", {"limit": limit})

    # ---------- Audio (TTS) ----------

    def voices(self) -> Dict:
        """List available TTS voices (Runway built-in + custom)."""
        return self._get("/v1/generated_audio/voices")

    # ---------- High-level helpers ----------

    def upscale_4k(self, task_artifact_id: str, session_id: Optional[str] = None,
                   parent_asset_group_id: Optional[str] = None, name: Optional[str] = None,
                   wait: bool = True) -> Dict:
        """Run 4K upscale on a completed task's artifact.

        task_artifact_id: id of artifact from a completed task (artifacts[].id, NOT task.id).
        session_id: optional sessionId (for UI grouping).
        parent_asset_group_id: optional asset group (folder).
        Returns finished task with upscaled artifact URL.
        """
        body = {
            "taskType": "media_upscale",
            "internal": False,
            "options": {
                "name": name or f"Upscale - {task_artifact_id[:8]}",
                "task_artifact_id": task_artifact_id,
                "exploreMode": True,
            },
            "asTeamId": self.team_id,
        }
        if session_id:
            body["sessionId"] = session_id
        if parent_asset_group_id:
            body["options"]["parent_asset_group_id"] = parent_asset_group_id
        result = self._post("/v1/tasks", body)
        task = result.get("task", result)
        if wait:
            task = self.wait_task(task["id"])
        return task

    def generate_image(
        self,
        prompt: str,
        num_images: int = 1,
        image_size: str = "1K",
        model: str = "gemini-3.1-flash-image-preview",
        explore_mode: bool = True,
        wait: bool = True,
        name: Optional[str] = None,
    ) -> Dict:
        """Generate image via Nano Banana 2 (Gemini 3.1 Flash Image).

        model: 'gemini-3.1-flash-image-preview' (Nano Banana 2)
        image_size: '1K' | '2K' | '4K'
        """
        body = {
            "taskType": "gemini_3_1_flash_image",
            "options": {
                "name": name or f"Nano Banana 2 - {prompt[:60]}",
                "text_prompt": prompt,
                "num_images": num_images,
                "image_size": image_size,
                "model": model,
                "exploreMode": explore_mode,
                "creationSource": "tool-mode",
            },
        }
        result = self._post("/v1/tasks", body, params={"asTeamId": self.team_id})
        task = result.get("task", result)
        if wait:
            task = self.wait_task(task["id"])
        return task

    def generate_gen4(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        seconds: int = 5,
        aspect_ratio: str = "16:9",
        flavor: str = "gen4",  # 'gen4' | 'gen4_turbo' | 'gen4.5'
        explore_mode: bool = True,
        wait: bool = True,
        name: Optional[str] = None,
    ) -> Dict:
        """Generate video via Runway Gen-4 family.

        flavor: 'gen4' (60c/s, image-to-video) | 'gen4_turbo' (25c/s, image-to-video) | 'gen4.5' (60c/s, text-to-video with keyframes)
        """
        # Aspect ratios → resolutions for Gen-4
        size_map = {
            "16:9": (1584, 672), "21:9": (1584, 672),
            "9:16": (672, 1584), "1:1": (1024, 1024),
            "4:3": (1280, 960), "3:4": (960, 1280),
        }
        w, h = size_map.get(aspect_ratio, (1584, 672))
        options = {"seconds": seconds, "exploreMode": explore_mode, "creationSource": "tool-mode"}
        if flavor == "gen4_turbo":
            options.update({
                "height": h, "width": w, "init_image": "", "imageAssetId": "", "route": "i2v",
            })
        elif flavor == "gen4.5":
            options.update({"height": h, "width": w, "route": "k2v", "keyframes": []})
        if image_path:
            ds = self.upload_file(image_path, "image")
            if flavor == "gen4_turbo":
                options["init_image"] = ds["cdn_url"]
                options["imageAssetId"] = ds["id"]
            elif flavor == "gen4.5":
                options["keyframes"] = [{"image": ds["cdn_url"], "timestamp": 0}]
        if name:
            options["name"] = name
        body = {"taskType": flavor, "options": options}
        result = self._post("/v1/tasks", body, params={"asTeamId": self.team_id})
        task = result.get("task", result)
        if wait:
            task = self.wait_task(task["id"])
        return task

    def generate_seedance(
        self,
        prompt: str,
        image_path: Optional[str] = None,
        end_image_path: Optional[str] = None,
        duration: int = 5,
        aspect_ratio: str = "16:9",
        resolution: str = "720p",
        generate_audio: bool = True,
        explore_mode: bool = True,
        wait: bool = True,
        name: Optional[str] = None,
    ) -> Dict:
        """High-level: upload image(s) + create Seedance 2.0 task. Returns finished task."""
        ref_images = []
        if image_path:
            ds = self.upload_file(image_path, "image")
            ref_images.append({"assetId": ds["id"], "url": ds["cdn_url"], "type": "first_frame"})
        if end_image_path:
            ds = self.upload_file(end_image_path, "image")
            ref_images.append({"assetId": ds["id"], "url": ds["cdn_url"], "type": "end_frame"})

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
        result = self.create_task("seedance_2", options)
        task = result.get("task", result)
        if wait:
            task = self.wait_task(task["id"])
        return task

    def download(self, url: str, out_path: str) -> str:
        """Download asset from URL."""
        r = requests.get(url, stream=True)
        r.raise_for_status()
        with open(out_path, "wb") as f:
            for chunk in r.iter_content(8192):
                f.write(chunk)
        return out_path


# ---------- CLI ----------


def cmd_profile(args, c):
    p = c.profile()
    u = p.get("user", p)
    print(f"Email: {u.get('email')}")
    print(f"Plan: {u.get('plan')}")
    print(f"Plans: {u.get('plans')}")
    print(f"Plan expires: {u.get('planExpires')}")
    print(f"Team ID (URL): {u.get('username')}")


def cmd_teams(args, c):
    print(json.dumps(c.teams(), indent=2, ensure_ascii=False))


def cmd_features(args, c):
    print(json.dumps(c.features(), indent=2, ensure_ascii=False))


def cmd_can_start(args, c):
    print(json.dumps(c.can_start_task(args.feature), indent=2))


def cmd_estimate(args, c):
    if args.feature.startswith("seedance"):
        opts = {
            "duration": args.duration,
            "resolution": args.resolution,
            "aspectRatio": args.aspect,
            "generateAudio": args.audio,
        }
    elif args.feature.startswith("gen4"):
        opts = {"seconds": args.duration}
    else:
        opts = {"duration": args.duration}
    print(json.dumps(c.estimate_cost(args.feature, opts), indent=2))


def cmd_upload(args, c):
    ds = c.upload_file(args.path)
    print(json.dumps({"id": ds["id"], "cdn_url": ds["cdn_url"]}, indent=2))


def cmd_voices(args, c):
    v = c.voices()
    voices = v.get("voices", []) if isinstance(v, dict) else v
    for voice in voices:
        if isinstance(voice, dict):
            print(f"  {voice.get('id', '?')[:16]}... | {voice.get('name', '?'):20s} | {voice.get('description', '')[:60]}")


def cmd_task(args, c):
    data = c.get_task(args.id)
    task = data.get("task", data)
    print(f"ID: {task.get('id')}")
    print(f"Type: {task.get('taskType')}")
    print(f"Status: {task.get('status')}")
    print(f"Progress: {task.get('progressRatio')} | ETA: {task.get('estimatedTimeToStartSeconds')}s")
    arts = c.list_artifacts(task)
    if arts:
        print(f"Artifacts ({len(arts)}):")
        for a in arts:
            print(f"  {a}")


def cmd_generate(args, c):
    if args.type == "seedance_2":
        task = c.generate_seedance(
            prompt=args.prompt,
            image_path=args.image,
            end_image_path=args.end_image,
            duration=args.duration,
            aspect_ratio=args.aspect,
            resolution=args.resolution,
            generate_audio=args.audio,
            explore_mode=not args.no_explore,
            wait=args.wait,
            name=args.name,
        )
    elif args.type in ("gen4", "gen4_turbo", "gen4.5"):
        task = c.generate_gen4(
            prompt=args.prompt,
            image_path=args.image,
            seconds=args.duration,
            aspect_ratio=args.aspect,
            flavor=args.type,
            explore_mode=not args.no_explore,
            wait=args.wait,
            name=args.name,
        )
    elif args.type == "image":
        task = c.generate_image(
            prompt=args.prompt,
            num_images=args.num_images,
            image_size=args.image_size,
            explore_mode=not args.no_explore,
            wait=args.wait,
            name=args.name,
        )
    else:
        raise SystemExit(f"Generation type '{args.type}' not yet implemented in CLI")

    print(f"\nFinal status: {task.get('status')}")
    arts = c.list_artifacts(task)
    if arts:
        print("Artifacts:")
        for a in arts:
            print(f"  {a}")
        if args.download and arts:
            out = args.download
            c.download(arts[0], out)
            print(f"Saved → {out}")


def cmd_upscale(args, c):
    task = c.upscale_4k(
        task_artifact_id=args.artifact_id,
        name=args.name,
        wait=args.wait,
    )
    print(f"\nFinal status: {task.get('status')}")
    arts = c.list_artifacts(task)
    if arts:
        print("Artifacts:")
        for a in arts:
            print(f"  {a}")
        if args.download and arts:
            c.download(arts[0], args.download)
            print(f"Saved → {args.download}")


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("profile")
    sub.add_parser("teams")
    sub.add_parser("features")

    p = sub.add_parser("can-start")
    p.add_argument("feature", default="seedance_2", nargs="?")

    p = sub.add_parser("estimate")
    p.add_argument("feature")
    p.add_argument("--duration", type=int, default=5)
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--resolution", default="720p")
    p.add_argument("--audio", action="store_true", default=True)

    p = sub.add_parser("upload")
    p.add_argument("path")

    p = sub.add_parser("task")
    p.add_argument("id")

    sub.add_parser("voices")

    p = sub.add_parser("generate")
    p.add_argument("--type", default="seedance_2",
                   help="seedance_2 | gen4 | gen4_turbo | gen4.5 | image")
    p.add_argument("--prompt", required=True)
    p.add_argument("--image", help="Start frame image path (video) or omit for text-only")
    p.add_argument("--end-image", help="End frame image path (Seedance only)")
    p.add_argument("--duration", type=int, default=5, help="Video seconds (5/10)")
    p.add_argument("--aspect", default="16:9")
    p.add_argument("--resolution", default="720p", help="Seedance: 720p|1080p")
    p.add_argument("--audio", action="store_true", default=True)
    p.add_argument("--no-explore", action="store_true", help="Disable Explore Mode (uses paid credits)")
    p.add_argument("--wait", action="store_true", default=True)
    p.add_argument("--name", default=None)
    p.add_argument("--download", default=None, help="Save first artifact to this path after success")
    # image-specific
    p.add_argument("--num-images", type=int, default=1, help="image: 1..4")
    p.add_argument("--image-size", default="1K", help="image: 1K|2K|4K")

    p = sub.add_parser("upscale", help="4K upscale a completed task's artifact")
    p.add_argument("artifact_id", help="Artifact id (NOT task id) from a completed task")
    p.add_argument("--name", default=None)
    p.add_argument("--wait", action="store_true", default=True)
    p.add_argument("--download", default=None)

    args = ap.parse_args()
    c = RunwayClient()
    {
        "profile": cmd_profile,
        "teams": cmd_teams,
        "features": cmd_features,
        "can-start": cmd_can_start,
        "estimate": cmd_estimate,
        "upload": cmd_upload,
        "task": cmd_task,
        "voices": cmd_voices,
        "generate": cmd_generate,
        "upscale": cmd_upscale,
    }[args.cmd](args, c)


if __name__ == "__main__":
    main()
