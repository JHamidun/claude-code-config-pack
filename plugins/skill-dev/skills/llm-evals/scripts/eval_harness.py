#!/usr/bin/env python3
"""Two-tier eval harness: code graders (deterministic) + LLM-judge graders.

Stdlib only. The judge calls the Claude CLI by subscription (no API key),
caches every judge call on disk, and can run fully offline in stub mode.

Layout it expects (all paths configurable):

    <evaldir>/
      tasks.jsonl          one JSON object per line: {"id": "...", "prompt": "..."}
      graders.py           defines GRADERS: list[Grader]
      runs/<task_id>/
        output.*           the artifact produced by the system under test
        score.json         written by this harness
        baseline.score.json  written with --baseline
        judge_cache.json   memoized judge calls

Usage:
    python eval_harness.py --dir ./myeval                 # grade everything
    python eval_harness.py --dir ./myeval --baseline      # pin this run as baseline
    python eval_harness.py --dir ./myeval --only task_a task_b
    EVAL_JUDGE_STUB=1 python eval_harness.py --dir ./myeval   # offline smoke run

graders.py contract:

    from eval_harness import Grader

    def slide_count(ctx):
        return len(ctx.artifact_text.splitlines())

    GRADERS = [
        Grader("Lines", "code", "line count", slide_count, scale=(0, 20, 5)),
        Grader("Clarity", "judge", "judge 0-5", lambda ctx:
               ctx.judge("Score clarity 0-5.", ctx.artifact_text, ["score"])["score"]),
    ]
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import statistics
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

# --------------------------------------------------------------- grader API


@dataclass
class Grader:
    """One column of the scorecard.

    kind: "code"  -> deterministic, no model call, cheap, runs in the fast loop
          "judge" -> model call, subjective, runs in the full loop
    scale: (min, max, good) where good is "high" | "low" | an exact number.
    """

    name: str
    kind: str
    description: str
    grade: Callable[["Ctx"], Any]
    scale: tuple[float, float, Any] | None = None
    fmt: Callable[[float], str] | None = None


@dataclass
class Ctx:
    task_id: str
    task: dict
    artifact_path: Path | None
    artifact_text: str
    run_dir: Path
    judge: Callable[..., dict]
    extra: dict = field(default_factory=dict)


# --------------------------------------------------------------- judge call


class Judge:
    """Memoized LLM-judge. One cache file per task dir; key = sha1(prompt)."""

    def __init__(self, cache_path: Path, cmd: list[str], stub: bool = False):
        self.cache_path = cache_path
        self.cmd = cmd
        self.stub = stub
        self.calls = 0
        try:
            self.cache = json.loads(cache_path.read_text("utf-8"))
        except Exception:
            self.cache = {}

    def __call__(self, rubric: str, content: str, keys: list[str]) -> dict:
        prompt = (
            f"{rubric}\n\n"
            "Judge quality only. Do not reward length for its own sake. "
            "Do not favor content because it appears first. "
            "Use the full range of the scale, not only the good end.\n"
            f"Return ONLY JSON with keys: {', '.join(keys)} (+ optional \"comment\").\n\n"
            "--- CONTENT ---\n" + content
        )
        key = hashlib.sha1(prompt.encode("utf-8")).hexdigest()
        if key in self.cache:
            return self.cache[key]
        out = self._stub(key, keys) if self.stub else self._invoke(prompt)
        parsed = _parse_json(out, keys)
        self.cache[key] = parsed
        self.calls += 1
        return parsed

    def _stub(self, key: str, keys: list[str]) -> str:
        # Deterministic pseudo-scores so the harness is testable offline.
        vals = {k: int(key[i * 2 : i * 2 + 2], 16) % 6 for i, k in enumerate(keys)}
        vals["comment"] = "stub"
        return json.dumps(vals)

    def _invoke(self, prompt: str) -> str:
        res = subprocess.run(
            self.cmd,
            input=prompt,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=int(os.environ.get("EVAL_JUDGE_TIMEOUT", "180")),
        )
        if res.returncode != 0:
            raise RuntimeError(f"judge failed rc={res.returncode}: {res.stderr[:400]}")
        return res.stdout

    def flush(self) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(self.cache, ensure_ascii=False, indent=1), "utf-8"
        )


def _parse_json(text: str, keys: list[str]) -> dict:
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError(f"judge returned no JSON: {text[:200]!r}")
    data = json.loads(m.group(0))
    missing = [k for k in keys if k not in data]
    if missing:
        raise ValueError(f"judge JSON missing keys {missing}: {data}")
    return data


# --------------------------------------------------------------- runner


def load_graders(path: Path) -> list[Grader]:
    import importlib.util

    spec = importlib.util.spec_from_file_location("graders_mod", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["graders_mod"] = mod
    sys.modules.setdefault("eval_harness", sys.modules[__name__])
    spec.loader.exec_module(mod)
    return list(mod.GRADERS)


def load_tasks(path: Path, only: list[str]) -> list[dict]:
    tasks = [
        json.loads(line)
        for line in path.read_text("utf-8").splitlines()
        if line.strip()
    ]
    return [t for t in tasks if not only or t["id"] in only]


def build_ctx(task: dict, runs: Path, judge_cmd: list[str], stub: bool) -> tuple[Ctx, Judge]:
    run_dir = runs / task["id"]
    artifacts = sorted(p for p in run_dir.glob("output.*") if p.is_file())
    art = artifacts[0] if artifacts else None
    text = ""
    if art is not None:
        try:
            text = art.read_text("utf-8", errors="replace")
        except Exception:
            text = ""  # binary artifact: code graders parse it themselves
    judge = Judge(run_dir / "judge_cache.json", judge_cmd, stub)
    return Ctx(task["id"], task, art, text, run_dir, judge), judge


def grade_task(task, graders, runs, judge_cmd, stub, pin_baseline) -> dict:
    ctx, judge = build_ctx(task, runs, judge_cmd, stub)
    values: dict[str, Any] = {}
    errors: dict[str, str] = {}
    for g in graders:
        try:
            values[g.name] = g.grade(ctx)
        except Exception as e:  # infra failure != model failure, keep it separate
            values[g.name] = "ERR"
            errors[g.name] = f"{type(e).__name__}: {e}"
    judge.flush()
    ctx.run_dir.mkdir(parents=True, exist_ok=True)
    payload = {"taskId": task["id"], "results": values, "errors": errors,
               "judge_calls": judge.calls}
    blob = json.dumps(payload, ensure_ascii=False, indent=2)
    (ctx.run_dir / "score.json").write_text(blob, "utf-8")
    if pin_baseline:
        (ctx.run_dir / "baseline.score.json").write_text(blob, "utf-8")
    prev = {}
    if not pin_baseline:
        try:
            prev = json.loads((ctx.run_dir / "baseline.score.json").read_text("utf-8"))["results"]
        except Exception:
            prev = {}
    return {"taskId": task["id"], "values": values, "previous": prev, "errors": errors}


# --------------------------------------------------------------- report


def cell(g: Grader, v: Any, prev: Any) -> str:
    s = g.fmt(v) if (g.fmt and isinstance(v, (int, float))) else str(
        round(v, 2) if isinstance(v, float) else v
    )
    if isinstance(v, (int, float)) and isinstance(prev, (int, float)) and v != prev:
        d = round(v - prev, 2)
        s = f"{s} ({'+' if d > 0 else ''}{d})"
    return s


def verdict(g: Grader, v: Any) -> str:
    """Directional read of one cell against its scale: good / mid / bad."""
    if not isinstance(v, (int, float)) or not g.scale:
        return "-"
    lo, hi, good = g.scale
    span = (hi - lo) or 1
    if isinstance(good, (int, float)) and good not in ("high", "low"):
        t = 1 - abs(v - good) / span
    else:
        t = (v - lo) / span
        if good == "low":
            t = 1 - t
    return "good" if t >= 0.75 else ("mid" if t >= 0.4 else "bad")


def markdown_report(results: list[dict], graders: list[Grader]) -> str:
    head = "| task | " + " | ".join(g.name for g in graders) + " |"
    sep = "|---" * (len(graders) + 1) + "|"
    rows = [
        "| " + r["taskId"] + " | "
        + " | ".join(cell(g, r["values"].get(g.name, "-"), r["previous"].get(g.name))
                     for g in graders) + " |"
        for r in results
    ]
    lines = ["## Scorecard", "", head, sep, *rows, ""]
    aggs = []
    for g in graders:
        nums = [r["values"][g.name] for r in results
                if isinstance(r["values"].get(g.name), (int, float))]
        if nums:
            aggs.append(f"{g.name}={statistics.mean(nums):.2f}")
    if aggs:
        lines += ["**Mean per grader:** " + "  ·  ".join(aggs), ""]
    errs = [f"- `{r['taskId']}` / {k}: {v}"
            for r in results for k, v in r["errors"].items()]
    if errs:
        lines += ["### Infra errors (excluded from model verdict)", "", *errs, ""]
    flags = [f"- `{r['taskId']}` / {g.name} = {r['values'][g.name]} -> bad"
             for r in results for g in graders
             if verdict(g, r["values"].get(g.name)) == "bad"]
    if flags:
        lines += ["### Cells in the red", "", *flags, ""]
    return "\n".join(lines)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dir", default=".", help="eval directory")
    ap.add_argument("--tasks", default=None, help="default <dir>/tasks.jsonl")
    ap.add_argument("--graders", default=None, help="default <dir>/graders.py")
    ap.add_argument("--runs", default=None, help="default <dir>/runs")
    ap.add_argument("--only", nargs="*", default=[], help="task ids")
    ap.add_argument("--baseline", action="store_true", help="pin this run as baseline")
    ap.add_argument("--code-only", action="store_true", help="fast loop: skip judge graders")
    ap.add_argument("--judge-cmd", default=os.environ.get(
        "EVAL_JUDGE_CMD", "claude -p --output-format text"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--report", default=None, help="write markdown report here")
    a = ap.parse_args()

    d = Path(a.dir).resolve()
    tasks_p = Path(a.tasks) if a.tasks else d / "tasks.jsonl"
    graders_p = Path(a.graders) if a.graders else d / "graders.py"
    runs = Path(a.runs) if a.runs else d / "runs"

    graders = load_graders(graders_p)
    if a.code_only:
        graders = [g for g in graders if g.kind == "code"]
    tasks = load_tasks(tasks_p, a.only)
    stub = os.environ.get("EVAL_JUDGE_STUB") == "1"
    judge_cmd = a.judge_cmd.split()

    results: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.workers) as ex:
        futs = {ex.submit(grade_task, t, graders, runs, judge_cmd, stub, a.baseline): t
                for t in tasks}
        for f in concurrent.futures.as_completed(futs):
            t = futs[f]
            try:
                results.append(f.result())
            except Exception as e:  # one task dying must not abort the scorecard
                print(f"[{t['id']}] FAILED: {e}", file=sys.stderr)
    results.sort(key=lambda r: r["taskId"])

    md = markdown_report(results, graders)
    print(md)
    out = Path(a.report) if a.report else runs / "report.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(md, "utf-8")
    print(f"\nreport -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
