"""
Download PDF attachments from Gmail messages.
Usage: python gmail_download_attachments.py <email>:<message_id> <output_dir>
"""
import sys, os, json, base64
from pathlib import Path
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

TOKENS_DIR = Path.home() / ".claude" / ".gmail-tokens"
CLIENT_FILE = Path.home() / ".claude" / "google_oauth_client.json"
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]

def get_service(email):
    token_file = TOKENS_DIR / f"{email}.json"
    if not token_file.exists():
        print(f"No token for {email}")
        return None

    with open(CLIENT_FILE) as f:
        client = json.load(f)

    with open(token_file) as f:
        token_data = json.load(f)

    client_config = client.get("installed", client.get("web", {}))
    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_config["client_id"],
        client_secret=client_config["client_secret"],
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=creds)

def download_attachments(email, message_id, output_dir):
    service = get_service(email)
    if not service:
        return []

    msg = service.users().messages().get(userId="me", id=message_id).execute()

    downloaded = []
    parts = msg.get("payload", {}).get("parts", [])

    def process_parts(parts, depth=0):
        for part in parts:
            filename = part.get("filename", "")
            mime = part.get("mimeType", "")

            # Recurse into nested parts
            if part.get("parts"):
                process_parts(part["parts"], depth + 1)

            if not filename:
                continue

            # Only download PDFs and common invoice formats
            if not any(filename.lower().endswith(ext) for ext in ['.pdf', '.xlsx', '.csv', '.html']):
                continue

            body = part.get("body", {})
            att_id = body.get("attachmentId")

            if att_id:
                att = service.users().messages().attachments().get(
                    userId="me", id=att_id, messageId=message_id
                ).execute()
                data = base64.urlsafe_b64decode(att["data"])
            elif body.get("data"):
                data = base64.urlsafe_b64decode(body["data"])
            else:
                continue

            filepath = os.path.join(output_dir, filename)
            # Avoid overwriting
            if os.path.exists(filepath):
                base, ext = os.path.splitext(filename)
                filepath = os.path.join(output_dir, f"{base}_{message_id[:8]}{ext}")

            with open(filepath, "wb") as f:
                f.write(data)

            downloaded.append((filename, len(data)))
            print(f"  OK: {filename} ({len(data)} bytes)")

    process_parts(parts)

    if not downloaded:
        print(f"  No PDF attachments found in {email}:{message_id}")

    return downloaded

if __name__ == "__main__":
    if any(a in ("-h", "--help") for a in sys.argv[1:]):
        print("Usage: python gmail_download_attachments.py <email>:<message_id> <output_dir>")
        sys.exit(0)
    if len(sys.argv) < 3:
        print("Usage: python gmail_download_attachments.py <email>:<message_id> <output_dir>")
        sys.exit(1)

    if ":" not in sys.argv[1]:
        print(f"ERROR: first argument must be <email>:<message_id>, got: {sys.argv[1]!r}", file=sys.stderr)
        sys.exit(2)
    email, mid = sys.argv[1].split(":", 1)
    output_dir = sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)

    download_attachments(email, mid, output_dir)
