"""Acceptance test: CadQuery MCP -> STEP/STL/SVG -> Blender MCP import/save/render.

What it proves, end to end, through the same MCP servers Claude Code starts from .mcp.json:
- writes ONLY into a fresh --out folder (refuses a non-empty one), never next to itself;
- CadQuery: inspect (80 x 50 x 6 mm plate, 1 solid), export STEP/STL/SVG, render
  (the render tool answers image/svg+xml, so the preview is saved as cad_render.svg);
- Blender: copies the starter scene into --out (the shared starter is never opened in place),
  imports the STL, saves .blend, renders PNG with Cycles;
- checks units: 80x50x6 mm solid -> 0.08 x 0.05 x 0.006 m after the 0.001 import scale;
- writes acceptance-report.json with timings and sha256 of every artifact.

Paths come from arguments or environment variables (arguments win):
  --runtime  / LOCAL3D_RUNTIME  venv with blender-mcp and cadquery-mcp
                                (default: ~/.claude/tools/local-3d/runtime)
  --blender  / BLENDER_PATH     Blender executable (default: "blender" on PATH)
  --starter  / LOCAL3D_STARTER  starter scene (default: ../examples/starter.blend next to this file)

Run it with the runtime interpreter (it has the `mcp` client package). Server start is slow:
Blender 40-100 s, CadQuery 60-175 s, so one run takes several minutes.
  Windows:      %USERPROFILE%\\.claude\\tools\\local-3d\\runtime\\Scripts\\python.exe -B tools\\accept_local3d.py --out <empty dir>
  macOS/Linux:  ~/.claude/tools/local-3d/runtime/bin/python -B tools/accept_local3d.py --out <empty dir>
"""
import argparse
import asyncio
import base64
import hashlib
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_RUNTIME = Path.home() / ".claude" / "tools" / "local-3d" / "runtime"
DEFAULT_STARTER = HERE.parent / "examples" / "starter.blend"
CODE = """import cadquery as cq
result = cq.Workplane('XY').box(80, 50, 6).edges('|Z').fillet(5)
result = result.faces('>Z').workplane().rect(60, 30, forConstruction=True).vertices().hole(5)
show_object(result)
"""


def server_exe(runtime: Path, name: str) -> Path:
    """Console-script path inside a venv: Scripts/<name>.exe on Windows, bin/<name> elsewhere."""
    if sys.platform == "win32":
        return runtime / "Scripts" / f"{name}.exe"
    return runtime / "bin" / name


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def texts(response) -> str:
    return "\n".join(c.text for c in response.content if c.type == "text")


async def cad_phase(cfg: argparse.Namespace, out: Path, report: dict) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    t0 = time.monotonic()
    params = StdioServerParameters(command=str(server_exe(cfg.runtime, "cadquery-mcp")))
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            report["cadquery_init_s"] = round(time.monotonic() - t0, 1)
            tools = sorted(t.name for t in (await session.list_tools()).tools)
            report["cadquery_tools"] = tools
            assert {"inspect", "export", "render", "get_parameters"} <= set(tools), tools
            info = await session.call_tool("inspect", {"code": CODE})
            body = texts(info)
            assert not info.isError and "size: 80.0000" in body and "Solids: 1" in body, body
            report["cad_inspect"] = body[:600]
            for ext in ("step", "stl", "svg"):
                path = out / f"mounting_plate.{ext}"
                res = await session.call_tool("export", {"code": CODE, "filename": str(path)})
                assert not res.isError and path.exists() and path.stat().st_size > 100, texts(res)
            head = (out / "mounting_plate.step").read_bytes()[:64]
            assert b"ISO-10303-21" in head, head
            rendered = await session.call_tool("render", {"code": CODE})
            images = [c for c in rendered.content if c.type == "image"]
            assert images and not rendered.isError, texts(rendered)
            # CadQuery's render tool answers image/svg+xml; name the file by its real type, not ".png".
            ext = {"image/svg+xml": "svg", "image/png": "png", "image/jpeg": "jpg"}.get(images[0].mimeType, "bin")
            (out / f"cad_render.{ext}").write_bytes(base64.b64decode(images[0].data))
            report["cad_render_mime"] = images[0].mimeType
    report["cad_phase_s"] = round(time.monotonic() - t0, 1)


async def blender_phase(cfg: argparse.Namespace, out: Path, report: dict) -> None:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    t0 = time.monotonic()
    shutil.copy2(cfg.starter, out / "starter.blend")
    env = dict(os.environ, BLENDER_PATH=cfg.blender)
    params = StdioServerParameters(command=str(server_exe(cfg.runtime, "blender-mcp")), env=env)
    stl, blend, png = out / "mounting_plate.stl", out / "mounting_plate.blend", out / "mounting_plate.png"
    code = f"""import bpy
bpy.ops.wm.stl_import(filepath={str(stl)!r})
obj = bpy.context.object
obj.name = 'CAD_MountingPlate'
obj.scale = (0.001, 0.001, 0.001)
bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
if 'Cube' in bpy.data.objects:
    bpy.data.objects['Cube'].hide_render = True
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.length_unit = 'MILLIMETERS'
scene.render.engine = 'CYCLES'
scene.cycles.samples = 16
scene.render.resolution_x, scene.render.resolution_y = 800, 600
scene.camera.location = (0.095, -0.12, 0.10)
scene.camera.rotation_euler = (obj.location - scene.camera.location).to_track_quat('-Z', 'Y').to_euler()
scene.camera.data.clip_start = 0.001
scene.render.filepath = {str(png)!r}
bpy.ops.wm.save_as_mainfile(filepath={str(blend)!r})
bpy.ops.render.render(write_still=True)
result = {{'version': bpy.app.version_string, 'dimensions_m': [round(v, 5) for v in obj.dimensions]}}
"""
    async with stdio_client(params) as streams:
        async with ClientSession(*streams) as session:
            await session.initialize()
            report["blender_init_s"] = round(time.monotonic() - t0, 1)
            names = {t.name for t in (await session.list_tools()).tools}
            report["blender_tool_count"] = len(names)
            assert "execute_blender_code_for_cli" in names, sorted(names)
            res = await session.call_tool("execute_blender_code_for_cli",
                                          {"blend_file": str(out / "starter.blend"), "code": code})
            body = texts(res)
            report["blender_result"] = body[:800]
            assert not res.isError and png.exists() and png.stat().st_size > 10_000 and blend.exists(), body
            dims = [float(x) for x in re.findall(r"0\.0\d+", body.split("dimensions_m", 1)[-1])[:3]]
            assert len(dims) == 3 and sorted(dims) == sorted([0.08, 0.05, 0.006]), dims
            report["dimensions_m"] = dims
    report["blender_phase_s"] = round(time.monotonic() - t0, 1)


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Acceptance test for the local 3D workspace: CadQuery MCP -> STEP/STL/SVG -> "
                    "Blender MCP import/save/render. Starts both MCP servers (several minutes).")
    ap.add_argument("--out", required=True, type=Path,
                    help="fresh output folder; a non-empty folder is refused")
    ap.add_argument("--runtime", type=Path,
                    default=Path(os.environ.get("LOCAL3D_RUNTIME") or DEFAULT_RUNTIME),
                    help="venv with blender-mcp and cadquery-mcp (env LOCAL3D_RUNTIME; "
                         "default ~/.claude/tools/local-3d/runtime)")
    ap.add_argument("--blender", default=os.environ.get("BLENDER_PATH") or "blender",
                    help='Blender executable (env BLENDER_PATH; default "blender" on PATH)')
    ap.add_argument("--starter", type=Path,
                    default=Path(os.environ.get("LOCAL3D_STARTER") or DEFAULT_STARTER),
                    help="starter .blend copied into --out (env LOCAL3D_STARTER; "
                         "default ../examples/starter.blend next to this script)")
    return ap.parse_args()


async def main() -> int:
    cfg = parse_args()
    cfg.runtime = cfg.runtime.expanduser().resolve()
    cfg.starter = cfg.starter.expanduser().resolve()
    missing = [str(p) for p in (server_exe(cfg.runtime, "cadquery-mcp"), server_exe(cfg.runtime, "blender-mcp"),
                                cfg.starter) if not p.is_file()]
    if missing:
        raise SystemExit("not found (see SETUP.md): " + ", ".join(missing))
    out = cfg.out.expanduser().resolve()
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"refusing non-empty output folder: {out}")
    out.mkdir(parents=True, exist_ok=True)
    report: dict = {"out": str(out), "status": "FAIL"}
    try:
        await cad_phase(cfg, out, report)
        await blender_phase(cfg, out, report)
        report["status"] = "PASS"
    finally:
        report["artifacts"] = {p.name: {"bytes": p.stat().st_size, "sha256": sha(p)}
                               for p in sorted(out.iterdir()) if p.is_file() and p.suffix != ".json"}
        (out / "acceptance-report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps({k: v for k, v in report.items() if k not in ("cad_inspect", "blender_result")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
