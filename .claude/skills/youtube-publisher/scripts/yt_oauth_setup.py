#!/usr/bin/env python3
"""YouTube OAuth Setup -- one-time authorization for YouTube Data API v3.

Opens a browser for Google sign-in and saves the OAuth token to
~/.claude/.youtube-oauth-token.json with 0600 permissions.

Prerequisites:
  1. Go to https://console.cloud.google.com
  2. Create a project (or use an existing one)
  3. Enable the YouTube Data API v3
  4. Create OAuth 2.0 credentials (Desktop app type)
  5. Download client_secret.json -> save to ~/.claude/.youtube-client-secrets.json
     (or set YOUTUBE_CLIENT_SECRETS env var)

Usage:
  python yt_oauth_setup.py
"""

import os
import sys
from pathlib import Path

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.force-ssl",
    "https://www.googleapis.com/auth/youtubepartner",
]

TOKEN_PATH = Path.home() / ".claude" / ".youtube-oauth-token.json"
DEFAULT_CLIENT_SECRETS = Path.home() / ".claude" / ".youtube-client-secrets.json"


def main() -> None:
    """Run the OAuth setup flow."""
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
    except ImportError:
        print("Missing dependency. Install with:")
        print("  pip install google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    client_secrets_path = Path(
        os.environ.get("YOUTUBE_CLIENT_SECRETS", str(DEFAULT_CLIENT_SECRETS))
    )

    print("YouTube OAuth Setup")
    print("=" * 50)
    print()
    print(f"Client secrets: {client_secrets_path}")
    print(f"Token output:   {TOKEN_PATH}")
    print()

    if not client_secrets_path.exists():
        print(f"Client secrets file not found: {client_secrets_path}")
        print()
        print("To fix this:")
        print("  1. Go to https://console.cloud.google.com")
        print("  2. APIs & Services -> Credentials")
        print("  3. Create Credentials -> OAuth 2.0 Client ID -> Desktop app")
        print("  4. Download the JSON file")
        print(f"  5. Save it to {DEFAULT_CLIENT_SECRETS}")
        print(f"     Or set YOUTUBE_CLIENT_SECRETS env var to the file path")
        sys.exit(1)

    print("Opening browser for Google sign-in...")
    flow = InstalledAppFlow.from_client_secrets_file(str(client_secrets_path), SCOPES)
    creds = flow.run_local_server(port=0)

    # Save token with restricted permissions (0600)
    TOKEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(TOKEN_PATH), os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        f.write(creds.to_json())

    print()
    print(f"Token saved to {TOKEN_PATH}")
    print()
    print("Setup complete. You can now upload videos with yt_upload.py.")


if __name__ == "__main__":
    main()
