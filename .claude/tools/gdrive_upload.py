"""
Upload files/folders to Google Drive.
Usage:
  python gdrive_upload.py auth              # Authorize (one-time)
  python gdrive_upload.py upload <local_dir> <drive_folder_name>  # Upload folder
  python gdrive_upload.py list              # List root folders
"""
import sys, os, json
from pathlib import Path
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

TOKEN_FILE = Path.home() / ".claude" / ".gdrive-token.json"
CLIENT_FILE = Path.home() / ".claude" / "google_oauth_client.json"
SCOPES = ["https://www.googleapis.com/auth/drive.file"]

def get_service():
    if not TOKEN_FILE.exists():
        print("Not authorized. Run: python gdrive_upload.py auth")
        sys.exit(1)

    with open(CLIENT_FILE) as f:
        client = json.load(f)
    with open(TOKEN_FILE) as f:
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
    return build("drive", "v3", credentials=creds)

def authorize():
    with open(CLIENT_FILE) as f:
        client = json.load(f)

    client_config = client.get("installed", client.get("web", {}))
    flow = InstalledAppFlow.from_client_config(
        {"installed": client_config}, SCOPES
    )
    creds = flow.run_local_server(port=8090, prompt="consent")

    token_data = {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "scopes": SCOPES,
    }
    with open(TOKEN_FILE, "w") as f:
        json.dump(token_data, f)
    print(f"Authorized! Token saved to {TOKEN_FILE}")

def create_folder(service, name, parent_id=None):
    meta = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        meta["parents"] = [parent_id]

    folder = service.files().create(body=meta, fields="id").execute()
    return folder["id"]

def upload_file(service, local_path, parent_id):
    fname = os.path.basename(local_path)
    mime = "application/pdf" if fname.endswith(".pdf") else "application/octet-stream"

    meta = {"name": fname}
    if parent_id:
        meta["parents"] = [parent_id]

    media = MediaFileUpload(local_path, mimetype=mime, resumable=True)
    f = service.files().create(body=meta, media_body=media, fields="id,name").execute()
    return f

def upload_folder(local_dir, drive_folder_name):
    service = get_service()

    # Create root folder
    root_id = create_folder(service, drive_folder_name)
    print(f"Created Drive folder: {drive_folder_name} (ID: {root_id})")

    total = 0
    for subdir_name in sorted(os.listdir(local_dir)):
        subdir_path = os.path.join(local_dir, subdir_name)
        if not os.path.isdir(subdir_path):
            continue

        pdfs = [f for f in os.listdir(subdir_path) if f.endswith('.pdf')]
        if not pdfs:
            continue

        # Create subfolder
        sub_id = create_folder(service, subdir_name, root_id)
        print(f"\n  [{subdir_name}] {len(pdfs)} files -> folder ID: {sub_id}")

        for pdf in sorted(pdfs):
            pdf_path = os.path.join(subdir_path, pdf)
            try:
                upload_file(service, pdf_path, sub_id)
                total += 1
                print(f"    OK: {pdf}")
            except Exception as e:
                print(f"    FAIL: {pdf} - {e}")

    print(f"\n{'='*60}")
    print(f"DONE: {total} files uploaded to Google Drive")
    print(f"Folder: {drive_folder_name}")
    print(f"Link: https://drive.google.com/drive/folders/{root_id}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "auth":
        authorize()
    elif cmd == "list":
        service = get_service()
        results = service.files().list(
            q="mimeType='application/vnd.google-apps.folder' and 'root' in parents",
            fields="files(id, name)"
        ).execute()
        for f in results.get("files", []):
            print(f"  {f['name']} (ID: {f['id']})")
    elif cmd == "upload":
        if len(sys.argv) < 4:
            print("Usage: python gdrive_upload.py upload <local_dir> <drive_folder_name>")
            sys.exit(1)
        upload_folder(sys.argv[2], sys.argv[3])
    else:
        print(f"Unknown command: {cmd}")
