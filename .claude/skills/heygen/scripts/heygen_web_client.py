#!/usr/bin/env python3
"""HeyGen WEB-session headless client (api2.heygen.com internal API).

Bills against the **web subscription** (Team Unlimited) instead of the empty $0
public-API wallet. Analog of suno_client.py / runway_client.py.

Auth = `heygen_token` cookie value (base64 JSON {token,token_type,created_at})
sent as header `x-guest-session-token`, plus `x-space-id`. Stored in
~/.claude/.credentials.master.env as HEYGEN_WEB_TOKEN / HEYGEN_WEB_SPACE_ID.
Re-capture when expired: see ../references/web-session.md.

Reverse-engineered 2026-06-05 (account with Team plan).
All endpoints below captured live from the HeyGen web app.
"""
import os, sys, json, base64, argparse, mimetypes, urllib.request, urllib.parse, urllib.error
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "https://api2.heygen.com"
CREDS = Path(os.path.expanduser("~/.claude/.credentials.master.env"))


def _load_env(name, default=None):
    v = os.environ.get(name)
    if v:
        return v
    if CREDS.exists():
        for line in CREDS.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    return default


class HeyGenWeb:
    def __init__(self, token=None, space_id=None):
        self.token = token or _load_env("HEYGEN_WEB_TOKEN")
        self.space_id = space_id or _load_env("HEYGEN_WEB_SPACE_ID")
        if not self.token:
            raise SystemExit("HEYGEN_WEB_TOKEN missing — re-capture from browser (references/web-session.md)")

    def token_info(self):
        try:
            return json.loads(base64.b64decode(self.token).decode())
        except Exception as e:
            return {"error": str(e)}

    def _headers(self, extra=None):
        h = {
            "x-guest-session-token": self.token,
            "x-space-id": self.space_id or "",
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "x-ver": "4.1.0",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                          "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "origin": "https://app.heygen.com",
            "referer": "https://app.heygen.com/",
        }
        if extra:
            h.update(extra)
        return h

    def call(self, path, method="GET", params=None, json_body=None):
        """Generic internal-API call. path e.g. '/v1/pacific/account.get'. Unwraps {data}."""
        url = BASE + path
        if params:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(params, doseq=True)
        data = json.dumps(json_body).encode() if json_body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                body = r.read().decode("utf-8", "ignore")
        except urllib.error.HTTPError as e:
            raise SystemExit(f"HTTP {e.code} {method} {path}\n{e.read().decode('utf-8','ignore')[:600]}")
        try:
            j = json.loads(body)
        except Exception:
            return {"_raw": body[:2000]}
        if isinstance(j, dict) and "data" in j and j.get("code") in (100, 0, None):
            return j["data"]
        return j

    # ================= READ: account / billing =================
    def account(self):      return self.call("/v1/pacific/account.get", params={"include_ff": "true"})
    def user(self):         return self.call("/v1/user.get")
    def subscription(self): return self.call("/v1/payment/subscription")
    def usage(self):        return self.call("/v1/account/usage")
    def spaces(self):       return self.call("/v1/space.list")

    def quota(self):
        sub = self.subscription(); s = sub.get("subscription", {})
        ents = {e["name"]: {"total": e.get("total"), "remain": e.get("remain"),
                            "unlimited": e.get("is_unlimited"), "unit": e.get("unit")}
                for e in sub.get("entitlements", [])}
        acc = self.account().get("user", {})
        return {"tier": s.get("tier"), "plan": s.get("plan_name"), "is_trial": s.get("is_trial"),
                "renews_ts": s.get("expired_ts"), "email": acc.get("email"),
                "video_duration_limit_s": acc.get("video_duration_limit"),
                "entitlements": ents, "usage": self.usage()}

    # ================= READ: avatars / voices =================
    def avatar_groups(self, limit=50, page=1):
        return self.call("/v2/avatar_group.private.list", params={"limit": limit, "page": page})
    def avatar_group(self, group_id):
        return self.call("/v2/avatar_group", params={"id": group_id})
    def looks(self, group_id, limit=50, page=1, type="all"):
        return self.call("/v2/avatar_group/look.list",
                         params={"group_id": group_id, "type": type, "page": page, "limit": limit})
    def avatar(self, look_id):
        return self.call("/v2/avatar.get", params={"look_id": look_id})
    def voices(self, group_id, is_public="false"):
        return self.call("/v1/avatar_group/voices.get",
                         params={"avatar_group_id": group_id, "is_public": is_public})

    # ================= READ: projects / videos =================
    ITEM_TYPES = ["video_translate", "video_translate_proofread", "heygen_video", "heygen_video_draft",
                  "interactive_video", "video_repurpose", "video_agent", "video_agent_edit",
                  "batch_video", "batch_video_translate", "batch_avatar_video_translate",
                  "heygen_podcast", "seedance_2", "upscale_video", "filler_removal"]

    def items(self, limit=24, item_types=None):
        return self.call("/v1/project/items", params={
            "limit": limit, "sort_key": "created_ts", "sort_order": "desc", "is_trash": "false",
            "item_types": item_types or self.ITEM_TYPES})

    def item_status(self, *item_ids):
        """Generic status poll for any created item (video/translate/agent/seedance)."""
        return self.call("/v1/project/items/status", params={"item_ids": list(item_ids)})

    def find_item(self, item_id):
        """Return the full project/items row for an id (has video_url/video_download_url when done)."""
        for x in self.items(limit=100).get("items", []):
            if item_id in (x.get("item_id"), x.get("video_id"), x.get("id")):
                return x
        return None

    def wait_item(self, item_id, *, max_min=15, poll_s=10):
        """Poll until completed/failed. Returns the item row (with video_url)."""
        import time
        deadline = time.time() + max_min * 60
        while time.time() < deadline:
            x = self.find_item(item_id)
            st = (x or {}).get("status")
            if st == "completed":
                return x
            if st == "failed":
                raise SystemExit(f"item {item_id} failed: {(x or {}).get('error_message')}")
            time.sleep(poll_s)
        raise SystemExit(f"item {item_id} not done in {max_min} min")

    @staticmethod
    def download(url, out):
        urllib.request.urlretrieve(url, out)
        return out

    # ================= WRITE: Video Translation =================
    def translate_preflight(self, input_type="url", duration=1, audio_only=False):
        return self.call("/v1/video_translate.preflight", method="POST",
                         json_body={"input_type": input_type, "duration": duration,
                                    "translate_audio_only": audio_only})

    def translate(self, *, video_url=None, input_video_id="", output_languages, name="translation",
                  precision=False, captions=False, audio_only=False, instruction="",
                  keep_same_format=False, speech_enhancement=False, disable_music=False):
        """POST /v3/video_translate.create. output_languages = NAMES e.g. ['Russian (Russia)'].
        video_url = public URL (google_url). precision=True → is_quality_mode."""
        return self.call("/v3/video_translate.create", method="POST", json_body={
            "name": name, "input_video_id": input_video_id, "google_url": video_url or "",
            "output_languages": output_languages, "instruction": instruction,
            "enable_video_stretching": True, "vocabulary": [], "source_type": "video_translate",
            "translate_audio_only": audio_only, "captions": captions,
            "keep_the_same_format": keep_same_format, "enable_speech_enhancement": speech_enhancement,
            "disable_music_track": disable_music, "recaptcha_token": "",
            "create_collection": True, "is_quality_mode": precision})

    def translations(self, limit=20):
        return self.call("/v2/video_translate/list", params={"limit": limit})
    def translate_languages(self):
        return self.call("/v2/video_translate/support_languages")

    # ================= WRITE: Video Agent (prompt-to-video) =================
    def agent_create(self, prompt, *, orientation="auto", duration="auto", agent_mode="super_agent"):
        """POST /v1/video_agent/sessions → {session_id, chat_id, ...}."""
        return self.call("/v1/video_agent/sessions", method="POST", json_body={
            "prompt": prompt,
            "config": {"orientation": orientation, "use_video_agent_v2a": True,
                       "chat_mode": "auto", "agent_mode": agent_mode},
            "chat_configuration": {"duration": duration, "orientation": orientation},
            "video_source_type": "video_agent", "subtype": "interactive_chat"})

    def agent_chat(self, session_id, chat_id, user_input, *, asset_references=None,
                   auto_proceed=False, engine_tier="default"):
        """POST /v2/video_agent/interactive_chat. asset_references=[{asset_type,asset_id,display_name,tag_id}]."""
        return self.call("/v2/video_agent/interactive_chat", method="POST", json_body={
            "session_id": session_id, "chat_id": chat_id, "user_input": user_input,
            "asset_references": asset_references or [], "auto_proceed": auto_proceed,
            "debug_mode": False, "engine_tier": engine_tier, "chat_mode": "auto",
            "chat_configuration": {}, "edit_plan": []})

    def agent_sessions(self, page_size=30):
        return self.call("/v1/video_agent/sessions", params={"page_size": page_size, "sort_by": "last_activity_ts"})
    def agent_session(self, session_id):
        return self.call(f"/v1/video_agent/sessions/{session_id}")
    def agent_history(self, session_id, page_size=40):
        return self.call(f"/v1/video_agent/sessions/{session_id}/chat", params={"page_size": page_size})
    def agent_artifacts(self, session_id, page_size=20):
        return self.call(f"/v1/video_agent/{session_id}/artifacts", params={"page_size": page_size})

    # ================= WRITE: Photo-to-Video (Avatar IV) =================
    def upload_photo(self, path):
        """GET presigned URL, PUT the image, return s3_key (use as photo_s3_key)."""
        info = self.call("/v1/avatar/video_generate/get_upload_photo_url")
        up = info["upload_url"]
        ct = mimetypes.guess_type(str(path))[0] or "image/jpeg"
        with open(path, "rb") as f:
            data = f.read()
        req = urllib.request.Request(up, data=data, method="PUT",
                                     headers={"content-type": ct, "x-amz-server-side-encryption": "AES256"})
        with urllib.request.urlopen(req, timeout=120) as r:
            r.read()
        return {"s3_key": info["s3_key"], "s3_url": info["s3_url"]}  # submit needs BOTH (API 2026-06)

    def avatar_iv(self, *, photo=None, photo_s3_key=None, photo_s3_url=None,
                  input_text=None, voice_id=None, audio_url=None, title="Avatar IV video",
                  video_orientation="portrait", **extra):
        """POST /v1/avatar/video_generate/submit. input_text+voice_id OR audio_url.
        Pass photo=upload_photo() (dict). API (2026-06) requires photo_s3_key+photo_s3_url+
        video_title+video_orientation; **extra passes any newly-required fields without code change."""
        if isinstance(photo, dict):
            photo_s3_key, photo_s3_url = photo.get("s3_key"), photo.get("s3_url")
        elif isinstance(photo, str):  # back-compat: a bare string = s3_url
            photo_s3_url = photo_s3_url or photo
        body = {"photo_s3_key": photo_s3_key, "photo_s3_url": photo_s3_url,
                "title": title, "video_title": title, "video_orientation": video_orientation, **extra}
        if input_text:
            body["text_voice_setting"] = {"input_text": input_text, "voice_id": voice_id}
        elif audio_url:
            body["audio_voice_setting"] = {"audio_url": audio_url}
        else:
            raise SystemExit("avatar_iv needs input_text+voice_id or audio_url")
        return self.call("/v1/avatar/video_generate/submit", method="POST", json_body=body)

    # ================= WRITE: Cinematic Avatar (Seedance 2) =================
    def seedance(self, *, prompt, avatar_look_ids, ratio="16:9", resolution="720p",
                 duration=10, enhance_prompt=True):
        """POST /v1/seedance2/submit. avatar_look_ids = 1-3 look IDs. ratio 16:9|9:16|1:1, res 720p|1080p, dur 4-15."""
        return self.call("/v1/seedance2/submit", method="POST", json_body={
            "prompt": prompt, "avatar_look_ids": avatar_look_ids, "ratio": ratio,
            "resolution": resolution, "duration": duration, "enhance_prompt": enhance_prompt})
    def seedance_list(self, limit=10, offset=0):
        return self.call("/v1/seedance2.list", params={"offset": offset, "limit": limit})

    # ================= WRITE: AI Studio (heygen_video, multi-scene) =================
    def studio_create_draft(self):
        """POST /v1/text_draft.create → {video_id}."""
        return self.call("/v1/text_draft.create", method="POST", json_body={})

    @staticmethod
    def _studio_draft(*, script, avatar_id, voice_id, avatar_group_id="", resolution="1080p",
                      width=1920, height=1080, fps=25, title="Untitled Video", brand_kit_id=None):
        """Build a minimal single-scene draft graph (one avatar + one TTS line)."""
        tts_id, scene_id, av_id = "tts00001", "scene001", "avtr0001"
        align = {"start": {"script_id": tts_id, "word_index": 0}, "end": {"script_id": tts_id, "word_index": -1}}
        script_block = {"elements": {tts_id: {"id": tts_id, "type": "tts",
                        "attributes": {"voice_id": voice_id, "voice_settings": {
                            "locale": "", "pitch": 0, "speed": 1, "volume": 1,
                            "voice_engine_settings": {"engine_type": "auto"}}}, "text": script}},
                        "timeline": [tts_id]}
        if brand_kit_id:
            script_block["brand_kit_id"] = brand_kit_id
        return {
            "script": script_block,
            "captions": {"elements": {}, "remove_punctuation": False},
            "background_audio": {"elements": {}},
            "visual": {"elements": {
                scene_id: {"id": scene_id, "type": "scene",
                           "content": {"elements": [av_id], "background_color": "#FFFFFF"}},
                av_id: {"id": av_id, "type": "avatar",
                        "attributes": {"animations": [], "opacity": 1,
                                       "position": {"offset": {"x": 0, "y": 0}, "type": "center"},
                                       "size": {"fit": "contain", "scale": {"x": 1, "y": 1},
                                                "crop": {"top": 0, "left": 0, "bottom": 0, "right": 0}},
                                       "transformation": {"rotate": {"angle": 0}}},
                        "content": {"avatar_id": avatar_id, "avatar_state_id": avatar_id,
                                    "render_type": "normal", "avatar_type": "photo_avatar",
                                    "avatar_group_id": avatar_group_id, "matting": False,
                                    "use_avatar_iv_model": True, "engine": "avatar_iv",
                                    "engine_settings": {"engine_type": "avatar_iv_turbo",
                                                        "model": "4.3_turbo_edge",
                                                        "resolution": resolution, "alpha": 0}}}},
                       "layout": [scene_id]},
            "alignments": {scene_id: {"element_id": scene_id, "alignment_info": align},
                           av_id: {"element_id": av_id, "alignment_info": align}},
        }

    def studio_save(self, video_id, draft, *, title="Untitled Video", width=1920, height=1080, fps=25):
        body = {"video_id": video_id, "title": title, "text_draft": draft,
                "video_output": {"resolution": {"width": width, "height": height}, "fps": fps, "caption": False}}
        return self.call("/v1/text_draft.save", method="POST", json_body=body)

    @staticmethod
    def _build_metadata(draft, width=1920, height=1080):
        """Build per-element metadata required by text_draft.generate (API v2025+)."""
        meta = {}
        for eid, el in draft.get("script", {}).get("elements", {}).items():
            if el.get("type") == "tts":
                meta[eid] = {"type": "tts", "element_id": eid, "duration": 0, "words": []}
        for eid, el in draft.get("visual", {}).get("elements", {}).items():
            if el.get("type") == "avatar":
                at = el.get("content", {}).get("avatar_type", "photo_avatar")
                meta[eid] = {"type": "avatar", "element_id": eid, "avatar_type": at,
                             "width": width, "height": height}
        return meta

    def studio_generate(self, video_id, draft, *, title="Untitled Video", width=1920, height=1080, fps=25):
        vo = {"resolution": {"width": width, "height": height}, "fps": fps, "caption": False}
        return self.call("/v1/text_draft.generate", method="POST", json_body={
            "video_id": video_id, "enable_watermark": False, "generate_type": "normal",
            "draft_details": {"title": title, "text_draft_with_metadata": {
                "text_draft": draft, "video_output": vo,
                "metadata": self._build_metadata(draft, width, height)}},
            "complete_tts_in_backend": True})

    def studio_video(self, *, script, avatar_id, voice_id, avatar_group_id="", resolution="1080p",
                     width=1920, height=1080, title="AI Studio video"):
        """High-level: create draft → save → generate a single-scene talking-head. Returns video_id."""
        vid = self.studio_create_draft()["video_id"]
        draft = self._studio_draft(script=script, avatar_id=avatar_id, voice_id=voice_id,
                                   avatar_group_id=avatar_group_id, resolution=resolution,
                                   width=width, height=height, title=title)
        self.studio_save(vid, draft, title=title, width=width, height=height)
        self.studio_generate(vid, draft, title=title, width=width, height=height)
        return vid

    # ================= Apps family (Upscale / Face Swap / Speech Cleanup / Auto Clips / B-Roll ...) =================
    # Generic pattern: file.upload → POST /v1/apps/<slug> → GET /v1/apps/<slug>/{id}/status → GET /v1/apps/output/{id}
    APP_SLUGS = ["upscale-video", "face-swap", "speech-cleanup", "auto-clips", "generate-b-roll",
                 "ppt-to-video", "pdf-to-video", "batch-mode"]  # URL slug = app name

    _FT = {"mp4": "video", "mov": "video", "webm": "video", "jpg": "image", "jpeg": "image",
           "png": "image", "webp": "image", "mp3": "audio", "wav": "audio", "m4a": "audio",
           "pdf": "document", "ppt": "document", "pptx": "document"}

    @staticmethod
    def _probe(path):
        """Best-effort {width,height,duration} via ffprobe; {} if unavailable."""
        import subprocess, json as _j
        try:
            out = subprocess.run(["ffprobe", "-v", "quiet", "-print_format", "json",
                                  "-show_streams", "-show_format", str(path)],
                                 capture_output=True, text=True, timeout=30).stdout
            d = _j.loads(out); dur = d.get("format", {}).get("duration")
            for s in d.get("streams", []):
                if s.get("width"):
                    return {"width": str(s["width"]), "height": str(s["height"]),
                            "duration": str(round(float(dur), 3)) if dur else ""}
        except Exception:
            pass
        return {}

    def file_upload(self, path, file_type=None):
        """3-step upload (file.url presign → PUT to S3 → file.upload register).
        Returns {id, url, width, height, duration, file_size}. URL=download_url on resource2.heygen.ai."""
        import requests, hashlib
        path = Path(path)
        data = path.read_bytes()
        md5 = hashlib.md5(data).hexdigest()
        ft = file_type or self._FT.get(path.suffix.lower().lstrip("."), "video")
        props = self._probe(path) if ft == "video" else {}
        fu = self.call("/v1/file.url", method="POST", json_body={
            "file_type": ft, "filename": path.name, "md5": md5, "properties": props})
        fid, put_url = fu["id"], fu.get("url")
        if put_url:  # presigned PUT (null => md5 dedup, already on server)
            # presigned signature covers x-amz-server-side-encryption (in SignedHeaders) — must send it
            requests.put(put_url, data=data,
                         headers={"x-amz-server-side-encryption": "AES256"}, timeout=600).raise_for_status()
        self.call("/v1/file.upload", method="POST", json_body={
            "name": path.name, "id": fid, "file_type": ft, "md5": md5,
            "pipeline": "asset", "upload_knowledge": False})
        return {"id": fid, "url": fu.get("download_url"), "key": fu.get("key"),
                "width": int(props.get("width", 0) or 0), "height": int(props.get("height", 0) or 0),
                "duration": float(props.get("duration", 0) or 0), "file_size": len(data)}

    def apps_run(self, slug, **params):
        return self.call(f"/v1/apps/{slug}", method="POST", json_body=params)
    def apps_estimate(self, slug, **params):
        return self.call(f"/v1/apps/{slug}/estimate", method="POST", json_body=params)
    def apps_status(self, slug, job_id):
        return self.call(f"/v1/apps/{slug}/{job_id}/status")
    def apps_output(self, job_id):
        return self.call(f"/v1/apps/output/{job_id}")
    def apps_recents(self, limit=20):
        return self.call("/v1/apps/recents", params={"limit": limit, "offset": 0})

    # --- Face Swap (dedicated namespace /v1/face_swap_v2.*) ---
    def face_swap(self, *, source_video_url, target_face_url, duration):
        """POST /v1/face_swap_v2.video.submit. source = target video, target_face_url = the face PNG."""
        return self.call("/v1/face_swap_v2.video.submit", method="POST", json_body={
            "source_video_url": source_video_url, "target_face_url": target_face_url, "duration": duration})
    def face_swap_status(self, job_id):
        return self.call("/v1/face_swap_v2.video.status", method="POST", json_body={"id": job_id})

    # --- Speech Cleanup / filler removal (app slug = filler-removal) ---
    def speech_cleanup_preview(self, *, video_url, duration, source_filename="video.mp4"):
        """POST /v1/apps/filler-removal/preview/create → preview job; then apps_run('filler-removal', ...) to render."""
        return self.call("/v1/apps/filler-removal/preview/create", method="POST", json_body={
            "video_url": video_url, "duration": duration, "source_filename": source_filename})

    # --- AI Video Generator / B-Roll (text→video via Seedance, no avatar) ---
    def ai_generate(self, *, prompt, type="video", provider="seedance_2", aspect_ratio="16:9",
                    duration="10", resolution="720p"):
        """POST /v1/file.ai_generate_element → {workflow_id}. type 'video'|'image'. Poll ai_generate_status."""
        import base64 as _b64
        eid = _b64.b16encode(os.urandom(4)).decode()[:8]
        return self.call("/v1/file.ai_generate_element", method="POST", json_body={
            "element": {"type": type, "id": eid, "provider": provider, "aspect_ratio": aspect_ratio,
                        "prompt": prompt, "config": {"duration": str(duration), "resolution": resolution}},
            "stats_trace_id": "video-generator", "source": "VideoGenerator_redesign"})
    def ai_generate_status(self, workflow_id):
        return self.call("/v1/file.ai_generate_element.check", params={"workflow_id": workflow_id})

    def upscale(self, video_path_or_url, *, to_4k=True, model="slp-2.5"):
        """Upscale a video. Accepts a local path (auto-uploads) or a public URL."""
        if str(video_path_or_url).startswith("http"):
            url, vw, vh, dur, sz = video_path_or_url, 0, 0, 0, 0
        else:
            u = self.file_upload(video_path_or_url); url, vw, vh, dur, sz = u["url"], u["width"], u["height"], u["duration"], u["file_size"]
        ow, oh = (3840, 2160) if to_4k else (1920, 1080)
        return self.apps_run("upscale-video", video_url=url, model=model, output_width=ow, output_height=oh,
                             video_width=vw, video_height=vh, duration=dur, file_size=sz)

    # ================= PPT / PDF → Video (converts deck → AI Studio draft) =================
    def ppt_to_video(self, file_path, *, generate_script=True, conversion_type="image_background",
                     extract_notes=False, ppt_uuid=None):
        """Convert a deck → heygen_video draft. Returns {workflow_id}; poll ppt_conversion_status;
        result opens as a create-v4 draft → render via studio_generate.

        ⚠️ The PPT converter ingests decks through a web-only react-dropzone path; a deck uploaded via
        the generic file.url/file.upload (asset pipeline) is NOT indexed by the converter → convert
        returns 400569 'Not found'. Pass `ppt_uuid` of a deck already uploaded through the PPT web page
        (app.heygen.com/apps → PPT/PDF to Video → drop deck), OR drive that page once. The convert
        endpoint + body below are exact and verified."""
        if not ppt_uuid:
            ppt_uuid = self.file_upload(file_path, file_type="document")["id"]  # best-effort; see warning
        name = Path(file_path).stem if file_path else "deck"
        try:
            return self.call("/v1/ent_ppt_pdf_conversion/convert", method="POST", json_body={
                "ppt_uuid": ppt_uuid, "conversion_type": conversion_type, "extract_notes": extract_notes,
                "generate_script": generate_script, "ppt_conversion_version": "v2", "template_name": name})
        except SystemExit as e:
            if "Not found" in str(e) or "400569" in str(e):
                raise SystemExit("PPT convert: deck not indexed by converter — upload it via the PPT web "
                                 "page first, then pass its ppt_uuid (see method docstring).")
            raise
    def ppt_conversion_status(self, workflow_id):
        return self.call("/v1/ent_ppt_pdf_conversion/status.get", params={"workflow_id": workflow_id})

    # ================= Batch Mode (scripts × avatars → many videos) =================
    def batch_mode(self, *, project_name, scripts, avatars, width=1080, height=1920, fps=25):
        """POST /v1/avatar/batch_mode/submit. scripts=[str]; avatars=[{avatar_id, voice_id,
        avatar_group_id?, avatar_type?('instant_avatar'|'photo_avatar'), name?}]. Builds scripts×avatars matrix."""
        vo = {"resolution": {"width": width, "height": height}, "fps": fps, "caption": False}
        batches = []
        for si, script in enumerate(scripts):
            vids = []
            for av in avatars:
                draft = self._studio_draft(script=script, avatar_id=av["avatar_id"], voice_id=av["voice_id"],
                                           avatar_group_id=av.get("avatar_group_id", ""))
                # batch uses avatar_type from caller (instant_avatar default)
                for el in draft["visual"]["elements"].values():
                    if el.get("type") == "avatar":
                        el["content"]["avatar_type"] = av.get("avatar_type", "instant_avatar")
                vids.append({"title": f"Script {si+1} - {av.get('name','avatar')}",
                             "text_draft_with_metadata": {"text_draft": draft, "video_output": vo}})
            batches.append({"batch_name": f"Script {si+1}", "batch_script": script, "avatar_batch_videos": vids})
        return self.call("/v1/avatar/batch_mode/submit", method="POST", json_body={
            "video_output": vo, "source_type": "avatar_video_batch_mode",
            "project_name": project_name, "batches": batches})

    # ================= WRITE: Image generation (Product Placement / standalone) =================
    def image_generate(self, *, prompts, reference_images=None, num_generations=1):
        """POST /v3/image/generate. reference_images = list of s3:// URIs (from upload_photo s3_url)."""
        return self.call("/v3/image/generate", method="POST", json_body={
            "prompts": prompts if isinstance(prompts, list) else [prompts],
            "reference_images": reference_images or [], "num_generations": num_generations})


def _print(x):
    print(json.dumps(x, ensure_ascii=False, indent=2, default=str))


def main():
    ap = argparse.ArgumentParser(description="HeyGen web-session client (api2 internal API, Team plan)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for c in ("whoami", "quota", "account", "subscription", "usage", "avatars", "items",
              "agent-sessions", "translations", "translate-languages", "seedance-list"):
        sub.add_parser(c)
    sub.add_parser("looks").add_argument("group_id")
    sub.add_parser("avatar").add_argument("look_id")
    sub.add_parser("voices").add_argument("group_id")
    s = sub.add_parser("status"); s.add_argument("item_ids", nargs="+")
    s = sub.add_parser("translate"); s.add_argument("video_url"); s.add_argument("languages", help="comma-separated NAMES")
    s.add_argument("--precision", action="store_true")
    s = sub.add_parser("agent"); s.add_argument("prompt")
    s = sub.add_parser("seedance"); s.add_argument("prompt"); s.add_argument("look_ids", help="comma-separated")
    s.add_argument("--ratio", default="16:9"); s.add_argument("--res", default="720p"); s.add_argument("--dur", type=int, default=10)
    s = sub.add_parser("image"); s.add_argument("prompt"); s.add_argument("--refs", default="")
    s = sub.add_parser("avatar-iv"); s.add_argument("photo"); s.add_argument("text"); s.add_argument("voice_id")
    s = sub.add_parser("studio"); s.add_argument("script"); s.add_argument("avatar_id"); s.add_argument("voice_id")
    s.add_argument("--group", default=""); s.add_argument("--res", default="1080p")
    sub.add_parser("apps-recents")
    s = sub.add_parser("ai-video"); s.add_argument("prompt"); s.add_argument("--ratio", default="16:9"); s.add_argument("--res", default="720p"); s.add_argument("--dur", default="10")
    s = sub.add_parser("face-swap"); s.add_argument("video_url"); s.add_argument("face_url"); s.add_argument("--dur", type=float, default=5)
    s = sub.add_parser("ppt"); s.add_argument("file"); s.add_argument("--no-script", action="store_true")
    s = sub.add_parser("upscale"); s.add_argument("video"); s.add_argument("--1080", dest="hd", action="store_true")
    s = sub.add_parser("apps"); s.add_argument("slug"); s.add_argument("--json", default="{}")
    s = sub.add_parser("download"); s.add_argument("item_id"); s.add_argument("out"); s.add_argument("--wait", action="store_true")
    s = sub.add_parser("call"); s.add_argument("path"); s.add_argument("--method", default="GET"); s.add_argument("--json", default=None)
    args = ap.parse_args()
    c = HeyGenWeb()

    if args.cmd == "whoami":
        acc = c.account().get("user", {})
        _print({"email": acc.get("email"), "user_id": acc.get("user_id"), "space_id": c.space_id,
                "token": c.token_info(), "video_duration_limit_s": acc.get("video_duration_limit")})
    elif args.cmd == "quota":              _print(c.quota())
    elif args.cmd == "account":            _print(c.account())
    elif args.cmd == "subscription":       _print(c.subscription())
    elif args.cmd == "usage":              _print(c.usage())
    elif args.cmd == "avatars":            _print(c.avatar_groups())
    elif args.cmd == "items":              _print(c.items())
    elif args.cmd == "agent-sessions":     _print(c.agent_sessions())
    elif args.cmd == "translations":       _print(c.translations())
    elif args.cmd == "translate-languages":_print(c.translate_languages())
    elif args.cmd == "seedance-list":      _print(c.seedance_list())
    elif args.cmd == "looks":              _print(c.looks(args.group_id))
    elif args.cmd == "avatar":             _print(c.avatar(args.look_id))
    elif args.cmd == "voices":             _print(c.voices(args.group_id))
    elif args.cmd == "status":             _print(c.item_status(*args.item_ids))
    elif args.cmd == "translate":
        _print(c.translate(video_url=args.video_url, output_languages=[x.strip() for x in args.languages.split(",")],
                           precision=args.precision))
    elif args.cmd == "agent":              _print(c.agent_create(args.prompt))
    elif args.cmd == "seedance":
        _print(c.seedance(prompt=args.prompt, avatar_look_ids=[x.strip() for x in args.look_ids.split(",")],
                          ratio=args.ratio, resolution=args.res, duration=args.dur))
    elif args.cmd == "image":
        _print(c.image_generate(prompts=[args.prompt], reference_images=[x for x in args.refs.split(",") if x]))
    elif args.cmd == "avatar-iv":
        photo = c.upload_photo(args.photo)
        _print(c.avatar_iv(photo=photo, input_text=args.text, voice_id=args.voice_id))
    elif args.cmd == "studio":
        vid = c.studio_video(script=args.script, avatar_id=args.avatar_id, voice_id=args.voice_id,
                             avatar_group_id=args.group, resolution=args.res)
        print(f"video_id={vid}  (poll: status {vid} ; download: download {vid} out.mp4 --wait)")
    elif args.cmd == "apps-recents":       _print(c.apps_recents())
    elif args.cmd == "ai-video":           _print(c.ai_generate(prompt=args.prompt, aspect_ratio=args.ratio, resolution=args.res, duration=args.dur))
    elif args.cmd == "face-swap":          _print(c.face_swap(source_video_url=args.video_url, target_face_url=args.face_url, duration=args.dur))
    elif args.cmd == "ppt":                _print(c.ppt_to_video(args.file, generate_script=not args.no_script))
    elif args.cmd == "upscale":            _print(c.upscale(args.video, to_4k=not args.hd))
    elif args.cmd == "apps":               _print(c.apps_run(args.slug, **json.loads(args.json)))
    elif args.cmd == "download":
        x = c.wait_item(args.item_id) if args.wait else c.find_item(args.item_id)
        if not x:
            raise SystemExit(f"item {args.item_id} not found")
        url = x.get("video_download_url") or x.get("video_url")
        if not url:
            raise SystemExit(f"no URL yet (status={x.get('status')}) — add --wait")
        c.download(url, args.out)
        print(f"DOWNLOADED {args.out} ({x.get('status')})")
    elif args.cmd == "call":
        body = json.loads(args.json) if args.json else None
        _print(c.call(args.path, method=args.method, json_body=body))


if __name__ == "__main__":
    main()
