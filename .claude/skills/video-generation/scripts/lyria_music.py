"""Lyria 2 (Vertex AI) — instrumental music generation with multi-sample crossfade.

Vertex AI Predict endpoint requires OAuth2 service account, NOT API key.
API key returns 401 UNAUTHENTICATED immediately.

GOTCHA: `seed` is incompatible with `sample_count > 1`. Including both → 400.
Each sample is fixed-length ~30s 48 kHz stereo WAV. For longer BGM, request N
samples and crossfade them with ffmpeg acrossfade (chained pairwise for 3+).

Env vars (~/.claude/.credentials.master.env):
    GOOGLE_CLOUD_PROJECT_ID        — Google Cloud project ID (Vertex AI)
    GOOGLE_SERVICE_ACCOUNT_KEY_PATH — absolute path to service-account.json

CLI:
    python lyria_music.py "Minimalist cinematic, 85 BPM, piano + ambient pads" \\
        --samples 3 --duration 72 --out music.wav
"""
# UTF-8 на выход. Консоль Windows по умолчанию cp1251/cp866/cp1252, и первый же
# не-ASCII символ (кириллица, →, ✓) валит процесс UnicodeEncodeError — обычно на
# --help, то есть ДО любой полезной работы. errors="replace" оставляет вывод
# читаемым, если терминал всё же не UTF-8.
import sys as _sys
for _s in (_sys.stdout, _sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

import argparse
import base64
import os
import subprocess
import sys
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import service_account

load_dotenv(os.path.expanduser("~/.claude/.credentials.master.env"))

PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
SA_PATH = os.path.expanduser(os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY_PATH", ""))
LOCATION = "us-central1"
MODEL = "lyria-002"
SAMPLE_SECONDS = 30  # Lyria 2 fixed sample length


def get_access_token() -> str:
    creds = service_account.Credentials.from_service_account_file(
        SA_PATH,
        scopes=["https://www.googleapis.com/auth/cloud-platform"],
    )
    creds.refresh(Request())
    return creds.token


def call_lyria(prompt: str, *, sample_count: int, negative: str | None,
               seed: int | None) -> list[bytes]:
    if sample_count > 1 and seed is not None:
        raise ValueError("Lyria 2: `seed` is not supported when sample_count > 1")

    instance: dict = {"prompt": prompt}
    if negative:
        instance["negative_prompt"] = negative
    if seed is not None:
        instance["seed"] = seed
    instance["sample_count"] = sample_count

    url = (
        f"https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT}"
        f"/locations/{LOCATION}/publishers/google/models/{MODEL}:predict"
    )
    headers = {
        "Authorization": f"Bearer {get_access_token()}",
        "Content-Type": "application/json",
    }
    body = {"instances": [instance], "parameters": {}}

    print(f"[..] Lyria 2: {sample_count} samples × {SAMPLE_SECONDS}s")
    t0 = time.time()
    r = requests.post(url, json=body, headers=headers, timeout=300)
    if r.status_code != 200:
        print(f"[ERR] HTTP {r.status_code}: {r.text[:800]}")
        return []
    preds = r.json().get("predictions", [])
    print(f"[OK] {len(preds)} samples in {time.time()-t0:.0f}s")
    return [base64.b64decode(p["bytesBase64Encoded"]) for p in preds
            if p.get("bytesBase64Encoded")]


def stitch(samples: list[Path], target: Path, duration: int,
           crossfade: int) -> None:
    """Chain acrossfade pairwise: A>B>C>... then trim to `duration`, fade out."""
    if not samples:
        raise SystemExit("no samples to stitch")

    n = len(samples)
    if n == 1:
        cmd = [
            "ffmpeg", "-y", "-stream_loop", "-1", "-i", str(samples[0]),
            "-t", str(duration),
            "-af", f"afade=t=out:st={max(duration-4,0)}:d=4",
            str(target),
        ]
    else:
        # Build chained acrossfade via filter_complex
        inputs: list[str] = []
        for s in samples:
            inputs += ["-i", str(s)]
        chain_parts: list[str] = []
        current = "[0:a]"
        for i in range(1, n):
            label = f"[m{i}]"
            chain_parts.append(
                f"{current}[{i}:a]acrossfade=d={crossfade}:c1=tri:c2=tri{label}"
            )
            current = label
        final = (
            f"{current}atrim=end={duration},asetpts=PTS-STARTPTS,"
            f"afade=t=out:st={max(duration-4,0)}:d=4[out]"
        )
        fc = ";".join(chain_parts + [final])
        cmd = ["ffmpeg", "-y", *inputs, "-filter_complex", fc, "-map", "[out]",
               str(target)]

    print(f"[..] ffmpeg stitch {n} sample(s) -> {target.name}")
    r = subprocess.run(cmd, capture_output=True,
                       encoding="utf-8", errors="replace")
    if r.returncode != 0:
        print(r.stderr[-1500:])
        raise SystemExit(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt", help="Music prompt")
    ap.add_argument("--negative", default="vocals, speech, percussion drops, EDM, cheesy")
    ap.add_argument("--samples", type=int, default=2,
                    help="Number of Lyria samples to request (each 30s)")
    ap.add_argument("--duration", type=int, default=60,
                    help="Target duration in seconds (after crossfade trim)")
    ap.add_argument("--crossfade", type=int, default=4,
                    help="Crossfade overlap in seconds")
    ap.add_argument("--seed", type=int, default=None,
                    help="Random seed (only with --samples 1)")
    ap.add_argument("--out", default="music.wav",
                    help="Output WAV path")
    ap.add_argument("--encode-m4a", action="store_true",
                    help="Also write AAC m4a next to the WAV")
    args = ap.parse_args()

    if not PROJECT or not SA_PATH or not os.path.exists(SA_PATH):
        print("Missing GOOGLE_CLOUD_PROJECT_ID or GOOGLE_SERVICE_ACCOUNT_KEY_PATH")
        return 1

    wavs = call_lyria(args.prompt, sample_count=args.samples,
                      negative=args.negative, seed=args.seed)
    if not wavs:
        return 2

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    raw_dir = out_path.parent / "_lyria_raw"
    raw_dir.mkdir(exist_ok=True)
    samples: list[Path] = []
    for i, data in enumerate(wavs, start=1):
        p = raw_dir / f"sample_{i:02d}.wav"
        p.write_bytes(data)
        samples.append(p)

    stitch(samples, out_path, args.duration, args.crossfade)
    print(f"[OK] -> {out_path} ({out_path.stat().st_size//1024} KB)")

    if args.encode_m4a:
        m4a = out_path.with_suffix(".m4a")
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(out_path),
             "-c:a", "aac", "-b:a", "192k", str(m4a)],
            check=True, capture_output=True,
        )
        print(f"[OK] -> {m4a}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
