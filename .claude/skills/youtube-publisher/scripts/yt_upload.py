#!/usr/bin/env python3
"""YouTube upload CLI -- resumable upload with metadata, captions, thumbnails, and scheduling.

Usage:
    python yt_upload.py upload video.mp4 --title "My Video" --tags "ai,tech"
    python yt_upload.py status VIDEO_ID
"""

import argparse
import functools
import json
import logging
import os
import sys
import time
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────
TOKEN_PATH = Path.home() / ".claude" / ".youtube-oauth-token.json"
DEFAULT_CLIENT_SECRETS = Path.home() / ".claude" / ".youtube-client-secrets.json"

VALID_PRIVACY = ("private", "unlisted", "public")
MAX_TITLE_LEN = 100
MAX_DESC_LEN = 5000


# ── Retry decorator (exponential backoff) ──────────────
def with_retry(max_retries: int = 2, base_delay: float = 5.0):
    """Retry with exponential backoff on exception.

    Delays: base_delay * 2^attempt (5s -> 10s -> 20s).
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc: Exception | None = None
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < max_retries:
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            "%s failed (attempt %d/%d): %s -- retrying in %.1fs",
                            func.__name__, attempt + 1, max_retries + 1, e, delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            "%s failed after %d attempts: %s",
                            func.__name__, max_retries + 1, e,
                        )
            raise last_exc  # type: ignore[misc]
        return wrapper
    return decorator


# ── Secure file write ──────────────────────────────────
def _write_secret_file(path: Path, content: str) -> None:
    """Write a file with 0600 permissions (owner read/write only).

    Uses os.open() with explicit mode to avoid a TOCTOU race.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(path), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(content)


# ── Auth ───────────────────────────────────────────────
def _get_credentials():
    """Load and refresh YouTube OAuth credentials.

    Returns:
        google.oauth2.credentials.Credentials ready for API calls.

    Raises:
        FileNotFoundError: Token file does not exist.
        RuntimeError: Token expired with no refresh token.
    """
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    if not TOKEN_PATH.exists():
        raise FileNotFoundError(
            f"YouTube OAuth token not found at {TOKEN_PATH}.\n"
            "Run: python yt_oauth_setup.py"
        )

    creds = Credentials.from_authorized_user_file(str(TOKEN_PATH))
    if creds.expired:
        if creds.refresh_token:
            creds.refresh(Request())
            _write_secret_file(TOKEN_PATH, creds.to_json())
            logger.info("OAuth token refreshed.")
        else:
            raise RuntimeError(
                "YouTube OAuth token is expired and has no refresh token.\n"
                "Re-run: python yt_oauth_setup.py"
            )
    return creds


def _build_youtube():
    """Build an authenticated YouTube API client.

    Returns:
        googleapiclient.discovery.Resource for YouTube v3.
    """
    from googleapiclient.discovery import build

    creds = _get_credentials()
    return build("youtube", "v3", credentials=creds)


# ── Upload ─────────────────────────────────────────────
@with_retry(max_retries=2, base_delay=5.0)
def _do_upload(
    video_path: Path,
    title: str,
    description: str,
    tags: list[str],
    category_id: str,
    privacy: str,
    lang: str,
    schedule: str | None,
    srt_path: Path | None,
    thumbnail_path: Path | None,
    playlist_id: str | None,
) -> str:
    """Upload video to YouTube with full metadata.

    Args:
        video_path: Path to the video file.
        title: Video title (max 100 chars).
        description: Video description (max 5000 chars).
        tags: List of tag strings.
        category_id: YouTube category ID.
        privacy: One of private, unlisted, public.
        lang: Default language code (e.g. en, ru).
        schedule: ISO 8601 datetime string for scheduled publish, or None.
        srt_path: Path to SRT caption file, or None.
        thumbnail_path: Path to thumbnail image, or None.
        playlist_id: YouTube playlist ID to add video to, or None.

    Returns:
        YouTube video URL (https://youtu.be/VIDEO_ID).
    """
    from googleapiclient.http import MediaFileUpload

    youtube = _build_youtube()

    # Build request body
    status_body: dict = {
        "privacyStatus": "private" if schedule else privacy,
        "selfDeclaredMadeForKids": False,
    }
    if schedule:
        status_body["publishAt"] = schedule

    body = {
        "snippet": {
            "title": title[:MAX_TITLE_LEN],
            "description": description[:MAX_DESC_LEN],
            "tags": tags,
            "categoryId": category_id,
            "defaultLanguage": lang,
            "defaultAudioLanguage": lang,
        },
        "status": status_body,
    }

    # Resumable upload
    logger.info("Uploading %s (%s)...", video_path.name, _human_size(video_path.stat().st_size))
    media = MediaFileUpload(str(video_path), chunksize=-1, resumable=True)
    req = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    response = None
    while response is None:
        status, response = req.next_chunk()
        if status:
            logger.info("Upload progress: %d%%", int(status.progress() * 100))

    video_id: str = response["id"]
    url = f"https://youtu.be/{video_id}"
    logger.info("Uploaded: %s", url)

    # Upload SRT captions
    if srt_path and srt_path.exists():
        try:
            youtube.captions().insert(
                part="snippet",
                body={
                    "snippet": {
                        "videoId": video_id,
                        "language": lang,
                        "name": lang.upper(),
                        "isDraft": False,
                    }
                },
                media_body=MediaFileUpload(str(srt_path), mimetype="application/octet-stream"),
            ).execute()
            logger.info("Captions uploaded from %s.", srt_path.name)
        except Exception as e:
            logger.error("Caption upload failed: %s", e)

    # Upload thumbnail
    if thumbnail_path and thumbnail_path.exists():
        try:
            mimetype = "image/png" if thumbnail_path.suffix.lower() == ".png" else "image/jpeg"
            youtube.thumbnails().set(
                videoId=video_id,
                media_body=MediaFileUpload(str(thumbnail_path), mimetype=mimetype),
            ).execute()
            logger.info("Thumbnail uploaded from %s.", thumbnail_path.name)
        except Exception as e:
            logger.error("Thumbnail upload failed: %s", e)

    # Add to playlist
    if playlist_id:
        try:
            youtube.playlistItems().insert(
                part="snippet",
                body={
                    "snippet": {
                        "playlistId": playlist_id,
                        "resourceId": {"kind": "youtube#video", "videoId": video_id},
                    }
                },
            ).execute()
            logger.info("Added to playlist %s.", playlist_id)
        except Exception as e:
            logger.error("Playlist add failed: %s", e)

    return url


# ── Status ─────────────────────────────────────────────
def _check_status(video_id: str) -> None:
    """Check video processing status.

    Args:
        video_id: YouTube video ID.
    """
    youtube = _build_youtube()
    resp = youtube.videos().list(part="status,snippet,processingDetails", id=video_id).execute()

    items = resp.get("items", [])
    if not items:
        logger.error("Video not found: %s", video_id)
        sys.exit(1)

    video = items[0]
    snippet = video.get("snippet", {})
    status = video.get("status", {})

    print(f"Title:    {snippet.get('title', 'N/A')}")
    print(f"URL:      https://youtu.be/{video_id}")
    print(f"Privacy:  {status.get('privacyStatus', 'N/A')}")
    print(f"Upload:   {status.get('uploadStatus', 'N/A')}")

    publish_at = status.get("publishAt")
    if publish_at:
        print(f"Schedule: {publish_at}")

    proc = video.get("processingDetails", {})
    if proc:
        print(f"Process:  {proc.get('processingStatus', 'N/A')}")


# ── Helpers ────────────────────────────────────────────
def _human_size(nbytes: int) -> str:
    """Format byte count as human-readable string."""
    for unit in ("B", "KB", "MB", "GB"):
        if nbytes < 1024:
            return f"{nbytes:.1f} {unit}"
        nbytes /= 1024  # type: ignore[assignment]
    return f"{nbytes:.1f} TB"


# ── CLI ────────────────────────────────────────────────
def main() -> None:
    """Entry point for the YouTube upload CLI."""
    parser = argparse.ArgumentParser(
        description="YouTube upload CLI -- upload videos with metadata, captions, and thumbnails."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # upload subcommand
    up = sub.add_parser("upload", help="Upload a video to YouTube")
    up.add_argument("video", type=Path, help="Path to video file")
    up.add_argument("--title", type=str, default=None, help="Video title (max 100 chars)")
    up.add_argument("--description", type=str, default="", help="Video description")
    up.add_argument("--tags", type=str, default="", help="Comma-separated tags")
    up.add_argument("--category", type=int, default=28, help="Category ID (default: 28=Science&Tech)")
    up.add_argument("--thumbnail", type=Path, default=None, help="Path to thumbnail PNG/JPG")
    up.add_argument("--srt", type=Path, default=None, help="Path to SRT caption file")
    up.add_argument("--privacy", choices=VALID_PRIVACY, default="private", help="Privacy status")
    up.add_argument("--playlist", type=str, default=None, help="Playlist ID to add video to")
    up.add_argument("--schedule", type=str, default=None, help="ISO 8601 datetime for scheduled publish")
    up.add_argument("--lang", type=str, default="en", help="Default language (default: en)")

    # status subcommand
    st = sub.add_parser("status", help="Check video processing status")
    st.add_argument("video_id", type=str, help="YouTube video ID")

    args = parser.parse_args()

    try:
        if args.command == "upload":
            if not args.video.exists():
                logger.error("Video file not found: %s", args.video)
                sys.exit(1)

            title = args.title if args.title else args.video.stem
            tag_list = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

            url = _do_upload(
                video_path=args.video,
                title=title,
                description=args.description,
                tags=tag_list,
                category_id=str(args.category),
                privacy=args.privacy,
                lang=args.lang,
                schedule=args.schedule,
                srt_path=args.srt,
                thumbnail_path=args.thumbnail,
                playlist_id=args.playlist,
            )
            print(f"\nVideo URL: {url}")

        elif args.command == "status":
            _check_status(args.video_id)

    except FileNotFoundError as e:
        logger.error("%s", e)
        sys.exit(1)
    except RuntimeError as e:
        logger.error("%s", e)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("Interrupted.")
        sys.exit(130)


if __name__ == "__main__":
    main()
