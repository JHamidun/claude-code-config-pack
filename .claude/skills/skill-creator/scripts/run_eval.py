#!/usr/bin/env python3
"""Run trigger evaluation for a skill description.

Tests whether a skill's description causes Claude to trigger (read the skill)
for a set of queries. Outputs results as JSON.
"""

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

# Запуск двумя способами, а не одним. Импорт `scripts.*` работает, только когда на
# sys.path стоит КОРЕНЬ навыка — это даёт `python -m scripts.<имя>` из каталога навыка.
# Прямой `python scripts/<имя>.py` кладёт на sys.path сам каталог scripts/, и тот же
# импорт падает `ModuleNotFoundError: No module named 'scripts'` — при папке scripts,
# лежащей на виду. Добавляем корень навыка сами: тогда обе формы запуска рабочие.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.utils import parse_skill_md


def find_project_root() -> Path:
    """Find the project root by walking up from cwd looking for .claude/.

    Mimics how Claude Code discovers its project root, so the command file
    we create ends up where claude -p will look for it.
    """
    current = Path.cwd()
    for parent in [current, *current.parents]:
        if (parent / ".claude").is_dir():
            return parent
    return current


class QueryFailed(RuntimeError):
    """A single `claude -p` run produced no verdict.

    Raised instead of returning False: a failed run is not evidence that the
    skill did not trigger, and counting it as False silently turns every
    negative test case into a pass (trigger_rate 0.0 < threshold).
    """


def _pump(stream, sink: "queue.Queue") -> None:
    """Consume a pipe in a background thread; `None` on the queue marks EOF.

    Portable replacement for select.select() on the child's stdout, which only
    accepts sockets on Windows.
    """
    try:
        for chunk in iter(stream.readline, b""):
            sink.put(chunk)
    except Exception:  # pragma: no cover - pipe torn down with the process
        pass
    finally:
        sink.put(None)  # EOF sentinel


def run_single_query(
    query: str,
    skill_name: str,
    skill_description: str,
    timeout: int,
    project_root: str,
    model: str | None = None,
) -> bool:
    """Run a single query and return whether the skill was triggered.

    Creates a command file in .claude/commands/ so it appears in Claude's
    available_skills list, then runs `claude -p` with the raw query.
    Uses --include-partial-messages to detect triggering early from
    stream events (content_block_start) rather than waiting for the
    full assistant message, which only arrives after tool execution.

    Raises QueryFailed when the run gives no verdict (CLI missing, non-zero
    exit, no events, timeout). Never turns a broken run into `False`.
    """
    unique_id = uuid.uuid4().hex[:8]
    clean_name = f"{skill_name}-skill-{unique_id}"
    project_commands_dir = Path(project_root) / ".claude" / "commands"
    command_file = project_commands_dir / f"{clean_name}.md"

    try:
        project_commands_dir.mkdir(parents=True, exist_ok=True)
        # Use YAML block scalar to avoid breaking on quotes in description
        indented_desc = "\n  ".join(skill_description.split("\n"))
        command_content = (
            f"---\n"
            f"description: |\n"
            f"  {indented_desc}\n"
            f"---\n\n"
            f"# {skill_name}\n\n"
            f"This skill handles: {skill_description}\n"
        )
        command_file.write_text(command_content)

        # Resolve through PATHEXT: an npm install of Claude Code ships only
        # claude.cmd/.ps1, and CreateProcess("claude") appends .exe — it would
        # not find the CLI at all.
        claude_bin = shutil.which("claude") or "claude"

        cmd = [
            claude_bin,
            "-p", query,
            "--output-format", "stream-json",
            "--verbose",
            "--include-partial-messages",
        ]
        if model:
            cmd.extend(["--model", model])

        # Remove CLAUDECODE env var to allow nesting claude -p inside a
        # Claude Code session. The guard is for interactive terminal conflicts;
        # programmatic subprocess usage is safe.
        env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=project_root,
                env=env,
            )
        except FileNotFoundError as exc:
            raise QueryFailed(
                "`claude` CLI not found on PATH — the eval cannot run. "
                "Install Claude Code and make sure `claude --version` works."
            ) from exc

        triggered = False
        events_seen = 0
        start_time = time.time()
        # Track state for stream event detection
        pending_tool_name = None
        accumulated_json = ""

        # Pump both pipes from background threads. select.select() cannot be
        # used here: on Windows it accepts sockets only (WinError 10038/10093),
        # so the old polling loop raised on every run and the exception was
        # laundered into "did not trigger".
        stdout_q: "queue.Queue" = queue.Queue()
        stderr_q: "queue.Queue" = queue.Queue()
        threading.Thread(target=_pump, args=(process.stdout, stdout_q), daemon=True).start()
        threading.Thread(target=_pump, args=(process.stderr, stderr_q), daemon=True).start()
        stderr_seen: list = []

        def _stderr_tail(limit: int = 500) -> str:
            while True:
                try:
                    chunk = stderr_q.get_nowait()
                except queue.Empty:
                    break
                if chunk:
                    stderr_seen.append(chunk)
            text = b"".join(stderr_seen).decode("utf-8", errors="replace").strip()
            return text[-limit:] if text else "<no stderr>"

        try:
            while True:
                left = timeout - (time.time() - start_time)
                if left <= 0:
                    raise QueryFailed(
                        f"timed out after {timeout}s with no verdict "
                        f"(events seen: {events_seen}; stderr: {_stderr_tail(200)})"
                    )

                try:
                    raw = stdout_q.get(timeout=min(left, 0.5))
                except queue.Empty:
                    continue
                if raw is None:  # EOF sentinel from the pump
                    break

                line = raw.decode("utf-8", errors="replace").strip()
                if not line:
                    continue

                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                events_seen += 1

                # Early detection via stream events
                if event.get("type") == "stream_event":
                    se = event.get("event", {})
                    se_type = se.get("type", "")

                    if se_type == "content_block_start":
                        cb = se.get("content_block", {})
                        if cb.get("type") == "tool_use":
                            tool_name = cb.get("name", "")
                            if tool_name in ("Skill", "Read"):
                                pending_tool_name = tool_name
                                accumulated_json = ""
                            else:
                                return False

                    elif se_type == "content_block_delta" and pending_tool_name:
                        delta = se.get("delta", {})
                        if delta.get("type") == "input_json_delta":
                            accumulated_json += delta.get("partial_json", "")
                            if clean_name in accumulated_json:
                                return True

                    elif se_type in ("content_block_stop", "message_stop"):
                        if pending_tool_name:
                            return clean_name in accumulated_json
                        if se_type == "message_stop":
                            return False

                # Fallback: full assistant message
                elif event.get("type") == "assistant":
                    message = event.get("message", {})
                    for content_item in message.get("content", []):
                        if content_item.get("type") != "tool_use":
                            continue
                        tool_name = content_item.get("name", "")
                        tool_input = content_item.get("input", {})
                        if tool_name == "Skill" and clean_name in tool_input.get("skill", ""):
                            triggered = True
                        elif tool_name == "Read" and clean_name in tool_input.get("file_path", ""):
                            triggered = True
                        return triggered

                elif event.get("type") == "result":
                    return triggered

            # Stream ended without a verdict — that is a broken run, not a "no".
            try:
                rc = process.wait(timeout=max(1.0, timeout - (time.time() - start_time)))
            except subprocess.TimeoutExpired:
                rc = None
            if rc not in (0, None):
                raise QueryFailed(
                    f"`claude -p` exited with code {rc} after {events_seen} event(s). "
                    f"stderr: {_stderr_tail()}"
                )
            if events_seen == 0:
                raise QueryFailed(
                    "`claude -p` produced no stream-json events — the CLI is not "
                    f"authenticated or not usable here. stderr: {_stderr_tail()}"
                )
            return triggered
        finally:
            # Clean up process on any exit path (return, exception, timeout)
            if process.poll() is None:
                process.kill()
                process.wait()
    finally:
        if command_file.exists():
            command_file.unlink()


def run_eval(
    eval_set: list[dict],
    skill_name: str,
    description: str,
    num_workers: int,
    timeout: int,
    project_root: Path,
    runs_per_query: int = 1,
    trigger_threshold: float = 0.5,
    model: str | None = None,
) -> dict:
    """Run the full eval set and return results.

    A run that failed is recorded as an error, never as `not triggered`:
    counting failures as False makes every negative case pass and produces a
    pass-rate computed on zero data.
    """
    results = []

    if shutil.which("claude") is None:
        raise RuntimeError(
            "`claude` CLI not found on PATH — trigger evals shell out to "
            "`claude -p`. Install Claude Code first (`claude --version` must work)."
        )

    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        future_to_info = {}
        for item in eval_set:
            for run_idx in range(runs_per_query):
                future = executor.submit(
                    run_single_query,
                    item["query"],
                    skill_name,
                    description,
                    timeout,
                    str(project_root),
                    model,
                )
                future_to_info[future] = (item, run_idx)

        query_triggers: dict[str, list[bool]] = {}
        query_errors: dict[str, list[str]] = {}
        query_items: dict[str, dict] = {}
        for future in as_completed(future_to_info):
            item, _ = future_to_info[future]
            query = item["query"]
            query_items[query] = item
            query_triggers.setdefault(query, [])
            query_errors.setdefault(query, [])
            try:
                query_triggers[query].append(future.result())
            except Exception as e:
                # NOT appended as False — a failed run carries no verdict.
                query_errors[query].append(f"{type(e).__name__}: {e}")
                print(f"ERROR: run failed for {query[:60]!r}: {e}", file=sys.stderr)

    errored_runs = 0
    unusable = 0
    for query, triggers in query_triggers.items():
        item = query_items[query]
        errors = query_errors.get(query, [])
        errored_runs += len(errors)
        should_trigger = item["should_trigger"]
        entry = {
            "query": query,
            "should_trigger": should_trigger,
            "runs": len(triggers),
            "errors": len(errors),
        }
        if not triggers:
            # Every run of this query broke: no rate can be computed. Refusing
            # to guess is the point — a 0.0 here would pass every negative case.
            unusable += 1
            entry.update({
                "trigger_rate": None,
                "triggers": 0,
                "pass": None,
                "error": errors[0] if errors else "no runs completed",
            })
        else:
            trigger_rate = sum(triggers) / len(triggers)
            if should_trigger:
                did_pass = trigger_rate >= trigger_threshold
            else:
                did_pass = trigger_rate < trigger_threshold
            entry.update({
                "trigger_rate": trigger_rate,
                "triggers": sum(triggers),
                "pass": did_pass,
            })
            if errors:
                entry["error"] = errors[0]
        results.append(entry)

    passed = sum(1 for r in results if r["pass"] is True)
    total = len(results)
    scored = sum(1 for r in results if r["pass"] is not None)

    if unusable:
        print(
            f"ERROR: {unusable}/{total} eval queries have no usable run "
            f"({errored_runs} failed run(s)). Their score is null, not a pass — "
            "do not read the summary as a real result.",
            file=sys.stderr,
        )

    return {
        "skill_name": skill_name,
        "description": description,
        "results": results,
        "summary": {
            "total": total,
            "scored": scored,
            "passed": passed,
            "failed": scored - passed,
            "unusable": unusable,
            "errored_runs": errored_runs,
            "trustworthy": unusable == 0 and errored_runs == 0,
        },
    }


def main():
    parser = argparse.ArgumentParser(description="Run trigger evaluation for a skill description")
    parser.add_argument("--eval-set", required=True, help="Path to eval set JSON file")
    parser.add_argument("--skill-path", required=True, help="Path to skill directory")
    parser.add_argument("--description", default=None, help="Override description to test")
    parser.add_argument("--num-workers", type=int, default=10, help="Number of parallel workers")
    parser.add_argument("--timeout", type=int, default=30, help="Timeout per query in seconds")
    parser.add_argument("--runs-per-query", type=int, default=3, help="Number of runs per query")
    parser.add_argument("--trigger-threshold", type=float, default=0.5, help="Trigger rate threshold")
    parser.add_argument("--model", default=None, help="Model to use for claude -p (default: user's configured model)")
    parser.add_argument("--verbose", action="store_true", help="Print progress to stderr")
    args = parser.parse_args()

    eval_set = json.loads(Path(args.eval_set).read_text())
    skill_path = Path(args.skill_path)

    if not (skill_path / "SKILL.md").exists():
        print(f"Error: No SKILL.md found at {skill_path}", file=sys.stderr)
        sys.exit(1)

    name, original_description, content = parse_skill_md(skill_path)
    description = args.description or original_description
    project_root = find_project_root()

    if args.verbose:
        print(f"Evaluating: {description}", file=sys.stderr)

    try:
        output = run_eval(
            eval_set=eval_set,
            skill_name=name,
            description=description,
            num_workers=args.num_workers,
            timeout=args.timeout,
            project_root=project_root,
            runs_per_query=args.runs_per_query,
            trigger_threshold=args.trigger_threshold,
            model=args.model,
        )
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    summary = output["summary"]
    if args.verbose:
        print(
            f"Results: {summary['passed']}/{summary['scored']} passed "
            f"(of {summary['total']} queries; {summary['unusable']} unusable)",
            file=sys.stderr,
        )
        for r in output["results"]:
            status = "ERROR" if r["pass"] is None else ("PASS" if r["pass"] else "FAIL")
            rate_str = f"{r['triggers']}/{r['runs']}" if r["runs"] else "no runs"
            print(f"  [{status}] rate={rate_str} expected={r['should_trigger']}: {r['query'][:70]}", file=sys.stderr)

    print(json.dumps(output, indent=2))

    # Exit non-zero when the numbers above are not a real measurement.
    if summary["unusable"]:
        print(
            f"Error: {summary['unusable']} query(ies) produced no usable run — "
            "this report is not a measurement.",
            file=sys.stderr,
        )
        sys.exit(2)
    if summary["errored_runs"]:
        print(
            f"Warning: {summary['errored_runs']} individual run(s) failed; "
            "rates are computed on the runs that did complete.",
            file=sys.stderr,
        )


if __name__ == "__main__":
    main()
