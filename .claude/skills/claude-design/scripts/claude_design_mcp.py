"""
claude_design_mcp.py — MCP server exposing 8 minimum tools for claude.ai/design.

Run via mcp.json:
  "claude-design": {
    "type": "stdio",
    "command": "python",
    "args": ["-m", "claude_design_mcp"],
    "env": {
      "CLAUDE_DESIGN_COOKIES": "${CLAUDE_DESIGN_COOKIES}",
      "CLAUDE_DESIGN_ORG_UUID": "${CLAUDE_DESIGN_ORG_UUID}"
    }
  }
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

# Ensure UTF-8 stdout/stderr (Windows defaults to cp1251)
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Make local module imports work both as -m and direct python
sys.path.insert(0, str(Path(__file__).parent))

from mcp.server.fastmcp import FastMCP  # noqa: E402

import claude_design_client as client  # noqa: E402

mcp = FastMCP("claude-design")


@mcp.tool()
def claude_design_list_projects(scope: str = "org") -> list[dict]:
    """List Claude Design projects in the user's org.

    Args:
        scope: 'org' for ListOrgProjects (all team), 'user' for personal.

    Returns: list of {projectId, name, viewedAt, ownerEmail, sharing, type}.
    """
    return client.list_projects(scope=scope)


@mcp.tool()
def claude_design_create_project(name: str | None = None) -> dict:
    """Create an empty Claude Design project.

    Args:
        name: optional project name (otherwise default 'Untitled').

    Returns: {projectId} of the new project.
    """
    return client.create_project(name=name)


@mcp.tool()
def claude_design_get_project(project_id: str, decode_data: bool = True) -> dict:
    """Fetch project metadata + full project state.

    Args:
        project_id: UUID of the project.
        decode_data: if True (default), decode the base64 `data` blob to a JSON
                     object. Set False to keep raw base64.

    Returns: {projectId, name, ownerEmail, createdAt, updatedAt, sharing, data, ...}.
        `data` contains chats[], activeSkills, viewState, etc.
    """
    return client.get_project(project_id, decode_data=decode_data)


@mcp.tool()
def claude_design_update_project_data(project_id: str, data: dict) -> dict:
    """Write the entire project state back. `data` should be the decoded JSON
    object (chats, activeSkills, viewState, etc.). Will be re-encoded to base64
    internally before sending.

    DANGER: this overwrites the whole project state. To safely edit, fetch
    via get_project first, mutate, then write back.

    Returns: {} on success.
    """
    return client.update_project_data(project_id, data)


@mcp.tool()
def claude_design_delete_project(project_id: str) -> dict:
    """Permanently delete a Claude Design project. No confirmation."""
    return client.delete_project(project_id)


@mcp.tool()
def claude_design_download_zip(project_id: str, dest_path: str) -> str:
    """Download the entire project filesystem as a ZIP archive.

    Args:
        project_id: UUID of the project.
        dest_path: absolute path where the ZIP should be written.
                   Parent dir is created if missing.

    Returns: absolute path of the saved ZIP.
    """
    p = client.download_zip(project_id, dest_path)
    return str(p)


@mcp.tool()
def claude_design_get_handoff_token(project_id: str) -> dict:
    """Mint a Handoff-to-Claude-Code token for the project.
    Use this when you want to continue work in Claude Code with the project's
    files/context attached.

    Returns: {token, expiresAt} (token is short-lived, ~10–15 min typically).
    """
    return client.get_handoff_token(project_id)


@mcp.tool()
def claude_design_chat(project_id: str, message: str, model: str = "claude-opus-4-7") -> dict:
    """[NOT YET IMPLEMENTED — Phase 2]

    Send a message to Claude Design and run the agent in the project.
    Streaming Chat uses Connect-RPC envelope framing (application/connect+proto)
    which needs separate implementation. For now, use the claude.ai/design web
    UI for chat; the rest of the API (read state, list files, download ZIP,
    handoff) works fully.
    """
    return {
        "error": "not_implemented",
        "message": "claude_design_chat is Phase 2. Use the web UI at claude.ai/design for now.",
    }


# === Helper tools (bonus, beyond the 8 minimum) ============================

@mcp.tool()
def claude_design_list_files(project_id: str) -> list[dict]:
    """List files in a Claude Design project. Returns [{name, path, type}, ...]."""
    return client.list_files(project_id)


@mcp.tool()
def claude_design_get_file(project_id: str, path: str) -> dict:
    """Read a single file from a project by relative path."""
    return client.get_file(project_id, path)


@mcp.tool()
def claude_design_remix_project(project_id: str) -> dict:
    """Duplicate a project (Anthropic calls this 'Remix'). Returns {newProjectId}."""
    return client.remix_project(project_id)


@mcp.tool()
def claude_design_get_preview_url(project_id: str) -> dict:
    """Mint a preview token for the project's sandbox subdomain.
    Returns: {origin, token, expiresAt} where origin = `https://<id>.claudeusercontent.com`.
    """
    return client.get_preview_url(project_id)


@mcp.tool()
def claude_design_get_me() -> dict:
    """Get authenticated user info: {accountUuid, organizationUuid, email, displayName, orgName}."""
    return client.get_me()


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
