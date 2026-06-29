"""
claude_design_client.py — HTTP client for claude.ai/design's Connect-RPC API.

Uses requests (sync) + cookies from auth.py. Supports the 8 minimum tools:
  list_projects, create_project, get_project, update_project_data,
  delete_project, chat (placeholder — streaming TBD), download_zip,
  get_handoff_token.
"""
from __future__ import annotations

import base64
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from auth import BASE_URL, DOWNLOAD_URL, base_headers


def _post(method: str, body: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """POST a Connect-RPC method with JSON body. Returns parsed JSON dict."""
    url = f"{BASE_URL}/{method}"
    body = body or {}
    r = requests.post(url, headers=base_headers(), json=body, timeout=60)
    if r.status_code >= 400:
        # Surface Connect-RPC error envelope
        try:
            err = r.json()
            raise RuntimeError(
                f"Connect-RPC {method} failed [{r.status_code}]: "
                f"{err.get('code', '?')} — {err.get('message', r.text[:200])}"
            )
        except json.JSONDecodeError:
            raise RuntimeError(
                f"Connect-RPC {method} failed [{r.status_code}]: {r.text[:300]}"
            )
    return r.json()


def list_projects(scope: str = "org") -> List[Dict[str, Any]]:
    """Return projects in the org. scope=org → ListOrgProjects, user → ListProjects."""
    method = "ListOrgProjects" if scope == "org" else "ListProjects"
    resp = _post(method, {})
    return resp.get("items", [])


def create_project(name: Optional[str] = None) -> Dict[str, Any]:
    """Create a new empty project. Returns {projectId}."""
    body: Dict[str, Any] = {}
    if name:
        body["name"] = name
    return _post("CreateProject", body)


def get_project(project_id: str, *, decode_data: bool = True) -> Dict[str, Any]:
    """Fetch project metadata. If decode_data=True, replaces base64 `data` blob with parsed JSON."""
    resp = _post("GetProject", {"projectId": project_id})
    if decode_data and "data" in resp and isinstance(resp["data"], str):
        try:
            decoded = base64.b64decode(resp["data"]).decode("utf-8")
            resp["data"] = json.loads(decoded)
        except Exception:
            pass  # leave as base64 string
    return resp


def update_project_data(project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Write arbitrary project state. `data` is the decoded project JSON
    (will be re-encoded to base64 internally by Anthropic's backend)."""
    encoded = base64.b64encode(
        json.dumps(data, ensure_ascii=False).encode("utf-8")
    ).decode("ascii")
    return _post("UpdateProjectData", {"projectId": project_id, "data": encoded})


def delete_project(project_id: str) -> Dict[str, Any]:
    """Delete project. Returns {} on success."""
    return _post("DeleteProject", {"projectId": project_id})


def remix_project(project_id: str) -> Dict[str, Any]:
    """Duplicate (= 'remix' in Anthropic terminology). Returns {newProjectId}."""
    return _post("RemixProject", {"projectId": project_id})


def get_handoff_token(project_id: str) -> Dict[str, Any]:
    """Mint a token usable by 'Handoff to Claude Code' workflow.
    Returns {token, expiresAt, ...}."""
    return _post("MintHandoffToken", {"projectId": project_id})


def get_preview_url(project_id: str) -> Dict[str, Any]:
    """Mint preview token. Returns {origin, token, expiresAt}."""
    return _post("MintPreviewToken", {"projectId": project_id})


def list_files(project_id: str) -> List[Dict[str, Any]]:
    """List files in a project. Returns [{name, path, type}, ...]."""
    resp = _post("ListFiles", {"projectId": project_id})
    return resp.get("entries", [])


def get_file(project_id: str, path: str) -> Dict[str, Any]:
    """Read a single file by path."""
    return _post("GetFile", {"projectId": project_id, "path": path})


def download_zip(project_id: str, dest_path: str | Path) -> Path:
    """Download the entire project as a ZIP (uses REST endpoint, not RPC)."""
    url = DOWNLOAD_URL.format(project_id=project_id)
    headers = base_headers()
    headers.pop("content-type", None)  # GET request
    r = requests.get(url, headers=headers, stream=True, timeout=120)
    r.raise_for_status()
    dest = Path(dest_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    with open(dest, "wb") as f:
        for chunk in r.iter_content(chunk_size=64 * 1024):
            if chunk:
                f.write(chunk)
    return dest


def chat_send(project_id: str, message: str, *, model: str = "claude-opus-4-7") -> Dict[str, Any]:
    """PLACEHOLDER for the streaming Chat call.

    Chat uses application/connect+proto with envelope framing — needs separate
    implementation. For Phase 1 (8 tools minimum) we surface this as 'not yet'
    and recommend users continue chatting via the UI; the rest of the API
    (project state read/write/list/download/handoff) is fully functional.
    """
    raise NotImplementedError(
        "claude_design_chat: streaming Chat envelope not yet implemented. "
        "Use the claude.ai/design web UI for now. "
        "Read-only RPCs (list/get/files) and Download ZIP work fully."
    )


# Convenience: get user info
def get_me() -> Dict[str, Any]:
    return _post("GetMe", {})
