"""Combine the local leak-scan rules and NVIDIA SkillSpector evidence; never auto-approve a skill."""

import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent


def _env_path(name, default):
    value = os.environ.get(name, "").strip()
    return Path(value).expanduser() if value else default


# Claude Code honours CLAUDE_CONFIG_DIR; otherwise the config lives in ~/.claude.
CLAUDE_DIR = _env_path("CLAUDE_CONFIG_DIR", Path.home() / ".claude")
# The local line is the scanner shared with leak-scan, not a copy.
LOCAL_SCANNER = CLAUDE_DIR / "skills" / "leak-scan" / "scripts" / "skill_injection_scan.py"
# Optional isolated SkillSpector venv; see references/skillspector-setup.md.
SKILLSPECTOR_HOME = _env_path("SKILLSPECTOR_HOME", CLAUDE_DIR / "tools" / "skillspector")
DEFAULT_NVIDIA = SKILLSPECTOR_HOME / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
# Importing skillspector.cli alone can take minutes on a loaded machine; 180 s lost whole reports.
DEFAULT_NVIDIA_TIMEOUT = 900
LOCAL_TIMEOUT = 180
# Reports and scanner state must never land in active skill/plugin roots.
PROTECTED_ROOTS = tuple(CLAUDE_DIR / part for part in ("skills", "plugins", "agents", "commands"))
MAX_FILES = 4000
MAX_BYTES = 40 * 1024 * 1024


def is_link(path):
    """Symlink or NTFS junction; Path.is_junction exists only on Python 3.12+."""
    if path.is_symlink():
        return True
    if hasattr(path, "is_junction"):
        return path.is_junction()
    if os.name == "nt":
        try:
            info = os.lstat(path)
        except OSError:
            return False
        return getattr(info, "st_reparse_tag", 0) == stat.IO_REPARSE_TAG_MOUNT_POINT
    return False


def preflight(target):
    target = target.absolute()
    for path in [target, *target.parents]:
        if is_link(path):
            raise ValueError("Filesystem links are not accepted")
    target = target.resolve(strict=True)
    if not (target.is_file() or target.is_dir()):
        raise ValueError("Target must be a regular local file or directory")
    count = total = 0
    paths = [target] if target.is_file() else target.rglob("*")
    for path in paths:
        if is_link(path):
            raise ValueError("Target contains a filesystem link; scan stopped before reading it")
        if path.is_file():
            details = path.stat()
            if details.st_nlink > 1:
                raise ValueError("Target contains a hard-linked file")
            count += 1
            total += details.st_size
            if count > MAX_FILES or total > MAX_BYTES or details.st_size > 2 * 1024 * 1024:
                raise ValueError("Target exceeds bounded local audit limits")
    return target


def child_environment(state):
    # Copy only non-secret runtime variables, not the agent's credential environment.
    allowed = ("SYSTEMROOT", "WINDIR", "SYSTEMDRIVE", "COMSPEC", "PATHEXT", "PATH")
    result = {key: os.environ[key] for key in allowed if key in os.environ}
    result.update({"HOME": str(state), "USERPROFILE": str(state), "TEMP": str(state),
                   "TMP": str(state), "XDG_CACHE_HOME": str(state),
                   "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8",
                   "LANGSMITH_TRACING": "false", "LANGCHAIN_TRACING_V2": "false",
                   "AWS_EC2_METADATA_DISABLED": "true", "SKILLSPECTOR_OSV_TIMEOUT": "1"})
    return result


def run_json(command, state, timeout=LOCAL_TIMEOUT):
    try:
        result = subprocess.run(command, cwd=state, env=child_environment(state),
                                stdin=subprocess.DEVNULL, capture_output=True,
                                text=True, encoding="utf-8", errors="replace", timeout=timeout)
    except subprocess.TimeoutExpired:
        # One slow line must not discard the other line's evidence or the report itself.
        return {"status": "incomplete", "reason": "timeout"}
    if len(result.stdout) > 4 * 1024 * 1024 or len(result.stderr) > 1024 * 1024:
        raise ValueError("Scanner output exceeded report limits")
    try:
        data = json.loads(result.stdout)
    except (ValueError, TypeError):
        return {"status": "incomplete", "exit_code": result.returncode,
                "reason": "Scanner did not return a JSON report; raw diagnostics withheld"}
    if not isinstance(data, dict):
        return {"status": "incomplete", "reason": "Unexpected report schema"}
    return {"exit_code": result.returncode, "data": data}


def summarize_local(result):
    if "data" not in result:
        return result
    data = result["data"]
    findings = [{"rule": f.get("rule_id"), "severity": f.get("severity"),
                 "file": f.get("path"), "line": f.get("line")}
                for f in data.get("findings", [])]
    incomplete = (result["exit_code"] not in (0, 1) or data.get("files_scanned", 0) == 0
                  or data.get("files_skipped", 0) > 0 or bool(data.get("vendor_dirs_skipped"))
                  or any(f["rule"] in ("fs.symlink", "fs.binary_artifact") for f in findings))
    return {"status": "incomplete" if incomplete else "completed",
            "exit_code": result["exit_code"], "files_scanned": data.get("files_scanned", 0),
            "files_skipped": data.get("files_skipped", 0), "findings": findings}


def summarize_nvidia(result):
    if "data" not in result:
        return result
    data = result["data"]
    if not (isinstance(data.get("issues"), list)
            and isinstance(data.get("analysis_completeness"), dict)
            and isinstance(data.get("risk_assessment"), dict)):
        return {"status": "incomplete", "reason": "Unexpected report schema; scan one skill at a time"}
    findings = [{"rule": f.get("id"), "severity": f.get("severity"),
                 "file": f.get("location", {}).get("file"),
                 "line": f.get("location", {}).get("start_line")}
                for f in data["issues"]]
    coverage = data["analysis_completeness"]
    safe_coverage = {key: coverage.get(key) for key in (
        "is_complete", "coverage_percent", "fully_inspected_files",
        "partially_inspected_files", "entirely_uninspected_files")}
    safe_coverage["limitations_count"] = len(coverage.get("limitations", []))
    safe_coverage["analyzer_statuses"] = [{"analyzer_id": a.get("analyzer_id"),
        "status": a.get("status"), "reason_code": a.get("reason_code")}
        for a in coverage.get("analyzer_statuses", [])]
    complete = (result["exit_code"] in (0, 1) and data.get("execution_successful") is True
                and coverage.get("is_complete") is True)
    return {"status": "completed" if complete else "incomplete",
            "exit_code": result["exit_code"], "risk_score": data["risk_assessment"].get("score"),
            "severity": data["risk_assessment"].get("severity"), "analysis_completeness": safe_coverage,
            "llm_used": False, "network_enabled": False, "findings": findings}


EPILOG = """environment:
  CLAUDE_CONFIG_DIR   Claude config dir (default ~/.claude); the local scanner is
                      <dir>/skills/leak-scan/scripts/skill_injection_scan.py
  SKILLSPECTOR_HOME   SkillSpector venv (default <Claude config dir>/tools/skillspector);
                      absent runtime = NVIDIA line "unavailable", exit 2, never clean

exit codes: 0 both lines completed, no findings; 1 findings; 2 a line incomplete,
unavailable, or an error. No exit code is an installation approval."""


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, epilog=EPILOG,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("target", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--nvidia-python", type=Path, default=DEFAULT_NVIDIA,
                        help="SkillSpector venv interpreter (default: %(default)s)")
    parser.add_argument("--nvidia-timeout", type=int, default=DEFAULT_NVIDIA_TIMEOUT,
                        help="seconds before the NVIDIA line is reported incomplete (default: %(default)s)")
    args = parser.parse_args(argv)
    if args.nvidia_timeout <= 0:
        raise ValueError("--nvidia-timeout must be a positive number of seconds")
    target = preflight(args.target)
    output = args.output.absolute()
    if output.resolve().is_relative_to(target if target.is_dir() else target.parent):
        raise ValueError("Report must be outside the scanned target directory")
    if any(output.resolve().is_relative_to(root.resolve()) for root in PROTECTED_ROOTS):
        raise ValueError("Report must not be written into an active skill/plugin root; use the session scratchpad")
    output.parent.mkdir(parents=True, exist_ok=True)
    state = output.parent / (".audit-state-" + uuid.uuid4().hex)
    state.mkdir()
    if LOCAL_SCANNER.is_file():
        local = summarize_local(run_json(
            [sys.executable, "-I", "-B", str(LOCAL_SCANNER), str(target), "--json", "--include-vendor"], state))
    else:
        local = {"status": "unavailable", "reason": "leak-scan scanner not installed",
                 "expected": str(LOCAL_SCANNER)}
    if args.nvidia_python.is_file():
        nvidia = summarize_nvidia(run_json(
            [str(args.nvidia_python), "-I", "-B", str(HERE / "nvidia_static.py"), "scan", str(target),
             "--no-llm", "--format", "json", "--fail-on-incomplete", "--fail-on-findings"], state,
            timeout=args.nvidia_timeout))
    else:
        nvidia = {"status": "unavailable", "reason": "SkillSpector runtime not installed",
                  "expected": str(args.nvidia_python),
                  "setup": "skills/skill-manager/references/skillspector-setup.md"}
    report = {"schema_version": 2, "target": str(target), "local": local, "nvidia": nvidia,
              "nvidia_timeout_seconds": args.nvidia_timeout,
              "semantic_review": "pending", "verdict": "CAUTION",
              "auto_install_authorized": False,
              "limitations": ["Static evidence is not an approval; review target source and all findings",
                              "NVIDIA live OSV checks are unavailable in network-disabled mode",
                              "Raw snippets and messages are withheld to avoid copying secrets into reports"]}
    output.write_text(json.dumps(report, ensure_ascii=True, indent=2), encoding="utf-8")
    summary = {"report": str(output), "local": local["status"], "nvidia": nvidia["status"],
               "local_findings": len(local.get("findings", [])),
               "nvidia_findings": len(nvidia.get("findings", [])), "semantic_review": "pending"}
    for name, line in (("local", local), ("nvidia", nvidia)):
        if line["status"] != "completed" and line.get("reason"):
            summary[name + "_reason"] = line["reason"]
    print(json.dumps(summary))
    if any(item["status"] != "completed" for item in (local, nvidia)):
        return 2
    return 1 if local.get("findings") or nvidia.get("findings") else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, OSError, subprocess.SubprocessError) as error:
        print(json.dumps({"status": "incomplete", "error_type": type(error).__name__,
                          "detail": str(error) if isinstance(error, ValueError) else "Diagnostic withheld"}))
        raise SystemExit(2)
