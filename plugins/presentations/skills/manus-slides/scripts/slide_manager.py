"""
Slide Manager - Core engine for Manus-style slide presentations.

Manages slide projects: initialization, modification, state tracking, and presentation.
Adapted from Manus AI slides pipeline for Claude Code.

Usage:
    python slide_manager.py init "Title" outline.json ./output
    python slide_manager.py modify ./project add '{"title": "New Slide"}'
    python slide_manager.py state ./project
    python slide_manager.py present ./project
"""

import json
import os
import sys
import uuid
import shutil
from pathlib import Path
from datetime import datetime


# --- Data Structures ---

def create_outline_entry(
    title: str,
    page_title: str = "",
    summary: str = "",
    image_plan: str = "",
    slide_template_key: str = "professional",
    slide_id: str = ""
) -> dict:
    """Create a slide outline entry matching Manus format."""
    return {
        "id": slide_id or str(uuid.uuid4())[:8],
        "title": title,
        "page_title": page_title or title,
        "summary": summary,
        "image_plan": image_plan,
        "slide_template_key": slide_template_key,
    }


def create_project_state(title: str, outline: list, mode: str = "html") -> dict:
    """Create initial project state (slide_state.json)."""
    return {
        "title": title,
        "mode": mode,  # "html" or "image"
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "outline": outline,
        "states": {},  # slide_id -> state ("edited" | "deleted" | "split_pending")
        "notes": {},   # slide_id -> speaker notes text
        "metadata": {
            "total_slides": len(outline),
            "active_slides": len(outline),
            "template_keys_used": list(set(s.get("slide_template_key", "professional") for s in outline)),
        }
    }


# --- Core Functions ---

def init_project(title: str, outline: list, output_dir: str, mode: str = "html") -> dict:
    """
    Initialize a slide project directory.

    Creates:
      - output_dir/
        - slide_state.json
        - slides/
          - slide_001.html (per slide)
        - screenshots/ (empty, for export)
        - images/ (empty, for image mode)

    Args:
        title: Presentation title
        outline: List of outline entry dicts
        output_dir: Directory to create project in
        mode: "html" or "image"

    Returns:
        Project state dict
    """
    project_dir = Path(output_dir)
    project_dir.mkdir(parents=True, exist_ok=True)
    (project_dir / "slides").mkdir(exist_ok=True)
    (project_dir / "screenshots").mkdir(exist_ok=True)
    (project_dir / "images").mkdir(exist_ok=True)

    # Ensure each outline entry has an ID
    for i, entry in enumerate(outline):
        if not entry.get("id"):
            entry["id"] = f"slide_{i+1:03d}"

    # Create state
    state = create_project_state(title, outline, mode)

    # Write state file
    state_path = project_dir / "slide_state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

    # Create placeholder HTML files for each slide
    for i, entry in enumerate(outline):
        slide_path = project_dir / "slides" / f"{entry['id']}.html"
        placeholder_html = _generate_placeholder_html(entry, i + 1, len(outline), title)
        with open(slide_path, "w", encoding="utf-8") as f:
            f.write(placeholder_html)

    return {
        "success": True,
        "project_dir": str(project_dir),
        "state_file": str(state_path),
        "slides_created": len(outline),
        "mode": mode,
    }


def modify_slide(project_dir: str, operation: str, slide_data: dict) -> dict:
    """
    Modify a slide in the project.

    Operations:
        - add: Add a new slide (slide_data: outline entry + position)
        - delete: Mark slide as deleted (slide_data: {id})
        - edit: Update slide content (slide_data: {id, html_content} or {id, ...fields})
        - split: Split a slide into two (slide_data: {id, new_slides: [entry1, entry2]})
        - reorder: Change slide order (slide_data: {order: [id1, id2, ...]})

    Returns:
        Result dict with success status
    """
    state = get_project_state(project_dir)
    if not state:
        return {"success": False, "error": "Project state not found"}

    project_path = Path(project_dir)

    if operation == "add":
        return _op_add(state, project_path, slide_data)
    elif operation == "delete":
        return _op_delete(state, project_path, slide_data)
    elif operation == "edit":
        return _op_edit(state, project_path, slide_data)
    elif operation == "split":
        return _op_split(state, project_path, slide_data)
    elif operation == "reorder":
        return _op_reorder(state, project_path, slide_data)
    else:
        return {"success": False, "error": f"Unknown operation: {operation}"}


def get_project_state(project_dir: str) -> dict | None:
    """Read and return current project state."""
    state_path = Path(project_dir) / "slide_state.json"
    if not state_path.exists():
        return None
    with open(state_path, "r", encoding="utf-8") as f:
        return json.load(f)


def update_states_batch(project_dir: str, updates: dict) -> dict:
    """
    Batch update slide states.

    Args:
        updates: {slide_id: new_state, ...}
            new_state: "edited" | "deleted" | "split_pending"
    """
    state = get_project_state(project_dir)
    if not state:
        return {"success": False, "error": "Project state not found"}

    for slide_id, new_state in updates.items():
        if new_state in ("edited", "deleted", "split_pending"):
            state["states"][slide_id] = new_state
        else:
            return {"success": False, "error": f"Invalid state: {new_state}"}

    state["updated_at"] = datetime.now().isoformat()
    _update_metadata(state)
    _save_state(project_dir, state)

    return {"success": True, "updated": len(updates)}


def present(project_dir: str) -> dict:
    """
    Prepare presentation info: list active slides in order.

    Returns dict with:
        - slides: list of {id, title, path, has_content}
        - total: number of active slides
        - title: presentation title
    """
    state = get_project_state(project_dir)
    if not state:
        return {"success": False, "error": "Project state not found"}

    project_path = Path(project_dir)
    active_slides = []

    for entry in state["outline"]:
        sid = entry["id"]
        if state["states"].get(sid) == "deleted":
            continue

        slide_path = project_path / "slides" / f"{sid}.html"
        has_content = slide_path.exists() and slide_path.stat().st_size > 500

        active_slides.append({
            "id": sid,
            "title": entry["title"],
            "page_title": entry.get("page_title", entry["title"]),
            "template_key": entry.get("slide_template_key", "professional"),
            "path": str(slide_path),
            "has_content": has_content,
            "state": state["states"].get(sid, "pending"),
            "notes": state["notes"].get(sid, ""),
        })

    return {
        "success": True,
        "title": state["title"],
        "mode": state.get("mode", "html"),
        "total": len(active_slides),
        "slides": active_slides,
    }


def update_notes(project_dir: str, slide_id: str, notes: str) -> dict:
    """Update speaker notes for a slide."""
    state = get_project_state(project_dir)
    if not state:
        return {"success": False, "error": "Project state not found"}

    state["notes"][slide_id] = notes
    state["updated_at"] = datetime.now().isoformat()
    _save_state(project_dir, state)

    return {"success": True, "slide_id": slide_id}


# --- Internal Operations ---

def _op_add(state: dict, project_path: Path, data: dict) -> dict:
    """Add a new slide."""
    entry = create_outline_entry(
        title=data.get("title", "New Slide"),
        page_title=data.get("page_title", ""),
        summary=data.get("summary", ""),
        image_plan=data.get("image_plan", ""),
        slide_template_key=data.get("slide_template_key", "professional"),
    )

    position = data.get("position", len(state["outline"]))
    state["outline"].insert(position, entry)
    state["states"][entry["id"]] = "edited"

    # Create HTML file
    slide_path = project_path / "slides" / f"{entry['id']}.html"
    html_content = data.get("html_content", "")
    if not html_content:
        html_content = _generate_placeholder_html(
            entry, position + 1, len(state["outline"]), state["title"]
        )
    with open(slide_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    state["updated_at"] = datetime.now().isoformat()
    _update_metadata(state)
    _save_state(str(project_path), state)

    return {"success": True, "slide_id": entry["id"], "operation": "add"}


def _op_delete(state: dict, project_path: Path, data: dict) -> dict:
    """Mark slide as deleted."""
    sid = data.get("id")
    if not sid:
        return {"success": False, "error": "Slide ID required"}

    state["states"][sid] = "deleted"
    state["updated_at"] = datetime.now().isoformat()
    _update_metadata(state)
    _save_state(str(project_path), state)

    return {"success": True, "slide_id": sid, "operation": "delete"}


def _op_edit(state: dict, project_path: Path, data: dict) -> dict:
    """Update slide content or metadata."""
    sid = data.get("id")
    if not sid:
        return {"success": False, "error": "Slide ID required"}

    # Update outline entry fields
    for entry in state["outline"]:
        if entry["id"] == sid:
            for field in ("title", "page_title", "summary", "image_plan", "slide_template_key"):
                if field in data:
                    entry[field] = data[field]
            break

    # Update HTML content if provided
    if "html_content" in data:
        slide_path = project_path / "slides" / f"{sid}.html"
        with open(slide_path, "w", encoding="utf-8") as f:
            f.write(data["html_content"])

    state["states"][sid] = "edited"
    state["updated_at"] = datetime.now().isoformat()
    _update_metadata(state)
    _save_state(str(project_path), state)

    return {"success": True, "slide_id": sid, "operation": "edit"}


def _op_split(state: dict, project_path: Path, data: dict) -> dict:
    """Split one slide into multiple."""
    sid = data.get("id")
    new_slides = data.get("new_slides", [])
    if not sid or len(new_slides) < 2:
        return {"success": False, "error": "Slide ID and at least 2 new_slides required"}

    # Find position of original slide
    position = None
    for i, entry in enumerate(state["outline"]):
        if entry["id"] == sid:
            position = i
            break

    if position is None:
        return {"success": False, "error": f"Slide {sid} not found"}

    # Mark original as deleted
    state["states"][sid] = "deleted"

    # Insert new slides at position
    new_ids = []
    for j, ns in enumerate(new_slides):
        entry = create_outline_entry(
            title=ns.get("title", f"Split {j+1}"),
            page_title=ns.get("page_title", ""),
            summary=ns.get("summary", ""),
            image_plan=ns.get("image_plan", ""),
            slide_template_key=ns.get("slide_template_key", "professional"),
        )
        state["outline"].insert(position + 1 + j, entry)
        state["states"][entry["id"]] = "edited"
        new_ids.append(entry["id"])

        # Create HTML file
        slide_path = project_path / "slides" / f"{entry['id']}.html"
        html_content = ns.get("html_content", "")
        if not html_content:
            html_content = _generate_placeholder_html(
                entry, position + 2 + j, len(state["outline"]), state["title"]
            )
        with open(slide_path, "w", encoding="utf-8") as f:
            f.write(html_content)

    state["updated_at"] = datetime.now().isoformat()
    _update_metadata(state)
    _save_state(str(project_path), state)

    return {"success": True, "original_id": sid, "new_ids": new_ids, "operation": "split"}


def _op_reorder(state: dict, project_path: Path, data: dict) -> dict:
    """Reorder slides."""
    new_order = data.get("order", [])
    if not new_order:
        return {"success": False, "error": "Order list required"}

    id_to_entry = {e["id"]: e for e in state["outline"]}
    reordered = []
    for sid in new_order:
        if sid in id_to_entry:
            reordered.append(id_to_entry[sid])

    # Append any slides not in new_order (safety)
    for entry in state["outline"]:
        if entry["id"] not in new_order:
            reordered.append(entry)

    state["outline"] = reordered
    state["updated_at"] = datetime.now().isoformat()
    _save_state(str(project_path), state)

    return {"success": True, "operation": "reorder", "new_order": [e["id"] for e in reordered]}


# --- Helpers ---

def _save_state(project_dir: str, state: dict):
    """Save state to disk."""
    state_path = Path(project_dir) / "slide_state.json"
    with open(state_path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _update_metadata(state: dict):
    """Recalculate metadata from current state."""
    active = [e for e in state["outline"] if state["states"].get(e["id"]) != "deleted"]
    state["metadata"]["total_slides"] = len(state["outline"])
    state["metadata"]["active_slides"] = len(active)
    state["metadata"]["template_keys_used"] = list(set(
        e.get("slide_template_key", "professional") for e in active
    ))


def _generate_placeholder_html(entry: dict, number: int, total: int, pres_title: str) -> str:
    """Generate placeholder HTML for a slide."""
    title = entry.get("title", "Untitled")
    page_title = entry.get("page_title", title)
    summary = entry.get("summary", "")
    template_key = entry.get("slide_template_key", "professional")

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{page_title}</title>
<script src="https://cdn.tailwindcss.com"></script>
<style>
  body {{ margin: 0; padding: 0; width: 1280px; height: 720px; overflow: hidden; }}
  .slide {{ width: 1280px; height: 720px; position: relative; }}
</style>
</head>
<body>
<div class="slide flex flex-col items-center justify-center bg-gradient-to-br from-slate-900 to-slate-800 text-white p-16">
  <div class="text-sm text-slate-400 mb-4">{pres_title} &mdash; Slide {number}/{total}</div>
  <h1 class="text-4xl font-bold mb-6 text-center">{title}</h1>
  <p class="text-xl text-slate-300 text-center max-w-3xl">{summary}</p>
  <div class="absolute bottom-6 right-8 text-sm text-slate-500">Template: {template_key}</div>
</div>
</body>
</html>"""


# --- CLI ---

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: slide_manager.py <command> [args...]"}))
        sys.exit(1)

    command = sys.argv[1]

    try:
        if command == "init":
            if len(sys.argv) < 5:
                print(json.dumps({"error": "Usage: init <title> <outline.json> <output_dir> [mode]"}))
                sys.exit(1)

            title = sys.argv[2]
            outline_path = sys.argv[3]
            output_dir = sys.argv[4]
            mode = sys.argv[5] if len(sys.argv) > 5 else "html"

            with open(outline_path, "r", encoding="utf-8") as f:
                outline = json.load(f)

            result = init_project(title, outline, output_dir, mode)
            print(json.dumps(result, ensure_ascii=False))

        elif command == "modify":
            if len(sys.argv) < 5:
                print(json.dumps({"error": "Usage: modify <project_dir> <operation> <data_json>"}))
                sys.exit(1)

            project_dir = sys.argv[2]
            operation = sys.argv[3]
            data = json.loads(sys.argv[4])

            result = modify_slide(project_dir, operation, data)
            print(json.dumps(result, ensure_ascii=False))

        elif command == "state":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: state <project_dir>"}))
                sys.exit(1)

            state = get_project_state(sys.argv[2])
            if state:
                print(json.dumps(state, ensure_ascii=False))
            else:
                print(json.dumps({"error": "State file not found"}))
                sys.exit(1)

        elif command == "present":
            if len(sys.argv) < 3:
                print(json.dumps({"error": "Usage: present <project_dir>"}))
                sys.exit(1)

            result = present(sys.argv[2])
            print(json.dumps(result, ensure_ascii=False))

        elif command == "notes":
            if len(sys.argv) < 5:
                print(json.dumps({"error": "Usage: notes <project_dir> <slide_id> <notes_text>"}))
                sys.exit(1)

            result = update_notes(sys.argv[2], sys.argv[3], sys.argv[4])
            print(json.dumps(result, ensure_ascii=False))

        elif command == "update-states":
            if len(sys.argv) < 4:
                print(json.dumps({"error": "Usage: update-states <project_dir> <updates_json>"}))
                sys.exit(1)

            updates = json.loads(sys.argv[3])
            result = update_states_batch(sys.argv[2], updates)
            print(json.dumps(result, ensure_ascii=False))

        else:
            print(json.dumps({"error": f"Unknown command: {command}"}))
            sys.exit(1)

    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)


if __name__ == "__main__":
    main()
