#!/usr/bin/env python3
"""Run local search-quality evaluations across fixed topics.

This is an optional local gate, not a required CI job. It compares a baseline
revision against a candidate checkout, computes deterministic regression
metrics, and optionally calls Gemini as a judge for graded relevance labels.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).parent))

from lib import env as envlib


REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TOPICS: List[Tuple[str, str]] = [
    ("nano banana pro prompting", "product"),
    ("codex vs claude code", "comparison"),
    ("anthropic odds", "prediction"),
    ("kanye west", "breaking_news"),
    ("remotion animations for Claude Code", "how_to"),
]
DEFAULT_SEARCH = "reddit,x,youtube,hn,polymarket"
SOURCE_KEYS = [
    "reddit",
    "x",
    "youtube",
    "tiktok",
    "instagram",
    "hackernews",
    "bluesky",
    "truthsocial",
    "polymarket",
    "websearch",
]
DEFAULT_JUDGE_MODEL = "gemini-3-pro-preview"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"


def slugify(topic: str) -> str:
    return "".join(c.lower() if c.isalnum() else "-" for c in topic).strip("-")


def path_without_node(path_value: str) -> str:
    parts = []
    for entry in path_value.split(os.pathsep):
        if not entry:
            continue
        if (Path(entry) / "node").exists():
            continue
        parts.append(entry)
    return os.pathsep.join(parts)


def write_exec_wrapper(path: Path, target: str, fixed_args: List[str]) -> None:
    quoted_target = shlex.quote(target)
    quoted_args = " ".join(shlex.quote(arg) for arg in fixed_args)
    path.write_text(f"#!/bin/sh\nexec {quoted_target} {quoted_args} \"$@\"\n")
    path.chmod(0o755)


def create_eval_tool_path(eval_home: Path, base_path: str) -> str:
    """Create safe wrapper binaries for local evaluation subprocesses."""
    bin_dir = eval_home / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)

    real_ytdlp = shutil.which("yt-dlp")
    if real_ytdlp:
        write_exec_wrapper(
            bin_dir / "yt-dlp",
            real_ytdlp,
            ["--ignore-config", "--no-cookies-from-browser"],
        )

    if not base_path:
        return str(bin_dir)
    return os.pathsep.join([str(bin_dir), base_path])


def stable_item_key(source: str, item: Dict[str, Any]) -> str:
    url = str(item.get("url") or "").strip()
    if url:
        return url
    item_id = str(item.get("id") or "").strip()
    text = item_text(source, item)
    return f"{source}:{item_id}:{text[:120]}"


def item_text(source: str, item: Dict[str, Any]) -> str:
    if source in {"x", "bluesky", "truthsocial"}:
        return str(item.get("text") or "").strip()
    if source == "polymarket":
        return str(item.get("question") or item.get("title") or "").strip()
    return str(item.get("title") or "").strip()


def build_ranked_items(report: Dict[str, Any], per_source_limit: int) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    for source in SOURCE_KEYS:
        items = list(report.get(source) or [])[:per_source_limit]
        for item in items:
            ranked.append({
                "source": source,
                "key": stable_item_key(source, item),
                "url": str(item.get("url") or "").strip(),
                "text": item_text(source, item),
                "score": float(item.get("score") or 0),
                "relevance": float(item.get("relevance") or 0),
                "date": item.get("date"),
            })
    ranked.sort(key=lambda item: (-item["score"], item["source"], item["key"]))
    return ranked


def url_sets_by_source(report: Dict[str, Any]) -> Dict[str, set[str]]:
    result: Dict[str, set[str]] = {}
    for source in SOURCE_KEYS:
        items = report.get(source) or []
        urls = {
            stable_item_key(source, item)
            for item in items
        }
        result[source] = urls
    return result


def jaccard(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set and not right_set:
        return 1.0
    union = left_set | right_set
    if not union:
        return 1.0
    return len(left_set & right_set) / len(union)


def retention(left: Iterable[str], right: Iterable[str]) -> float:
    left_set = set(left)
    right_set = set(right)
    if not left_set:
        return 1.0
    return len(left_set & right_set) / len(left_set)


def precision_at_k(ranking: List[Dict[str, Any]], judgments: Dict[str, int], k: int) -> float:
    top = ranking[:k]
    if not top:
        return 0.0
    hits = sum(1 for item in top if judgments.get(item["key"], 0) >= 2)
    return hits / len(top)


def ndcg_at_k(
    ranking: List[Dict[str, Any]],
    judgments: Dict[str, int],
    k: int,
    judged_pool: Optional[List[Dict[str, Any]]] = None,
) -> float:
    top = ranking[:k]
    if not top:
        return 0.0

    def dcg(grades: List[int]) -> float:
        total = 0.0
        for index, grade in enumerate(grades, start=1):
            total += (2**grade - 1) / math.log2(index + 1)
        return total

    actual = [judgments.get(item["key"], 0) for item in top]
    ideal_candidates = judged_pool or ranking
    ideal = sorted(
        (judgments.get(item["key"], 0) for item in ideal_candidates),
        reverse=True,
    )[:len(top)]
    ideal_score = dcg(ideal)
    if ideal_score == 0:
        return 0.0
    return dcg(actual) / ideal_score


def source_coverage_recall(
    ranking: List[Dict[str, Any]],
    judged_pool: List[Dict[str, Any]],
    judgments: Dict[str, int],
) -> float:
    good_sources = {item["source"] for item in judged_pool if judgments.get(item["key"], 0) >= 2}
    if not good_sources:
        return 1.0
    hit_sources = {
        item["source"]
        for item in ranking
        if judgments.get(item["key"], 0) >= 2
    }
    return len(hit_sources & good_sources) / len(good_sources)


def create_eval_env(include_web: bool) -> Tuple[Dict[str, str], Path]:
    config = envlib.get_config()
    eval_home = Path(tempfile.mkdtemp(prefix="last30days-eval-home-"))
    (eval_home / ".config").mkdir(parents=True, exist_ok=True)
    safe_path = create_eval_tool_path(
        eval_home,
        path_without_node(os.environ.get("PATH", "")),
    )
    passthrough = {
        "HOME": str(eval_home),
        "XDG_CONFIG_HOME": str(eval_home / ".config"),
        "PATH": safe_path,
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "LC_ALL": os.environ.get("LC_ALL", ""),
        "TMPDIR": os.environ.get("TMPDIR", ""),
        "PYTHONUTF8": "1",
        "LAST30DAYS_CONFIG_DIR": "",
        "BIRD_DISABLE_BROWSER_COOKIES": "1",
        "LAST30DAYS_DISABLE_BROWSER_COOKIES": "1",
    }
    for key in ("OPENAI_API_KEY", "XAI_API_KEY", "SCRAPER_API_KEY"):
        value = config.get(key)
        if value:
            passthrough[key] = value
    if include_web:
        for key in ("PARALLEL_API_KEY", "BRAVE_API_KEY", "OPENROUTER_API_KEY"):
            value = config.get(key)
            if value:
                passthrough[key] = value
    return passthrough, eval_home


def run_last30days(
    repo_dir: Path,
    topic: str,
    *,
    search: str,
    timeout_seconds: int,
    include_web: bool,
    env: Dict[str, str],
) -> Tuple[Dict[str, Any], str]:
    cmd = [
        sys.executable,
        "scripts/last30days.py",
        topic,
        "--emit",
        "json",
        "--search",
        search,
        "--timeout",
        str(timeout_seconds),
    ]
    if not include_web:
        cmd.append("--no-native-web")
    result = subprocess.run(
        cmd,
        cwd=repo_dir,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 30,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{repo_dir.name} failed for '{topic}' with exit {result.returncode}\n{result.stderr.strip()}"
        )
    return json.loads(result.stdout), result.stderr


def create_worktree(rev: str) -> Path:
    worktree_dir = Path(tempfile.mkdtemp(prefix="last30days-eval-"))
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree_dir), rev],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return worktree_dir


def remove_worktree(path: Path) -> None:
    subprocess.run(
        ["git", "worktree", "remove", "--force", str(path)],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )
    shutil.rmtree(path, ignore_errors=True)


def extract_gemini_text(payload: Dict[str, Any]) -> str:
    for candidate in payload.get("candidates", []):
        content = candidate.get("content") or {}
        for part in content.get("parts", []):
            text = part.get("text")
            if text:
                return text
    raise ValueError("Gemini response did not contain text")


def resolve_google_judge_api_key(config: Dict[str, Any]) -> Optional[str]:
    """Resolve the local canonical Google API key name.

    This workspace conventionally uses GOOGLE_API_KEY. We also accept the
    more Gemini-specific aliases for portability.
    """
    return (
        os.environ.get("GOOGLE_API_KEY")
        or config.get("GOOGLE_API_KEY")
        or os.environ.get("GEMINI_API_KEY")
        or config.get("GEMINI_API_KEY")
        or os.environ.get("GOOGLE_GENAI_API_KEY")
        or config.get("GOOGLE_GENAI_API_KEY")
    )


def call_gemini_judge(api_key: str, model: str, prompt: str) -> Dict[str, Any]:
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "responseMimeType": "application/json",
        },
    }
    url = GEMINI_API_URL.format(model=model, api_key=api_key)
    request = Request(
        url,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini HTTP {exc.code}: {detail}") from exc
    except URLError as exc:
        raise RuntimeError(f"Gemini request failed: {exc}") from exc
    return json.loads(extract_gemini_text(payload))


def build_judge_prompt(
    *,
    topic: str,
    query_type: str,
    items: List[Dict[str, Any]],
) -> str:
    item_lines = []
    for item in items:
        item_lines.append(
            "\n".join([
                f"- id: {item['key']}",
                f"  source: {item['source']}",
                f"  title: {item['text'][:220]}",
                f"  url: {item['url']}",
                f"  date: {item.get('date') or 'unknown'}",
            ])
        )
    joined = "\n".join(item_lines)
    return textwrap.dedent(
        f"""
        Judge search-result relevance for a last-30-days research tool.

        Topic: {topic}
        Query type: {query_type}

        Score each item on this 0-3 scale:
        - 0 = off-topic or clearly bad
        - 1 = weak or tangential
        - 2 = relevant and useful
        - 3 = highly relevant, one of the best results

        Focus on actual user intent, not just token overlap. Penalize items that
        only match generic words like "odds", "review", or "tips" without
        matching the real entity or subject. Favor items that would genuinely
        help answer the topic in the context of recent discussion.

        Return strict JSON with this shape:
        {{
          "judgments": [
            {{"id": "ITEM_ID", "grade": 0, "reason": "short reason"}}
          ]
        }}

        Items:
        {joined}
        """
    ).strip()


def get_judgments(
    *,
    output_dir: Path,
    slug: str,
    topic: str,
    query_type: str,
    items: List[Dict[str, Any]],
    judge_model: str,
    gemini_api_key: Optional[str],
) -> Dict[str, int]:
    cache_file = output_dir / "judgments" / f"{slug}.json"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    if cache_file.exists():
        cached = json.loads(cache_file.read_text())
        return {entry["id"]: int(entry["grade"]) for entry in cached.get("judgments", [])}

    if not gemini_api_key:
        return {}

    prompt = build_judge_prompt(topic=topic, query_type=query_type, items=items)
    payload = call_gemini_judge(gemini_api_key, judge_model, prompt)
    cache_file.write_text(json.dumps(payload, indent=2))
    return {entry["id"]: int(entry["grade"]) for entry in payload.get("judgments", [])}


def summarize_topic(
    *,
    topic: str,
    query_type: str,
    baseline_report: Dict[str, Any],
    candidate_report: Dict[str, Any],
    judged_pool: List[Dict[str, Any]],
    judgments: Dict[str, int],
    per_source_limit: int,
) -> Dict[str, Any]:
    baseline_ranked = build_ranked_items(baseline_report, per_source_limit)
    candidate_ranked = build_ranked_items(candidate_report, per_source_limit)

    baseline_sets = url_sets_by_source(baseline_report)
    candidate_sets = url_sets_by_source(candidate_report)

    metrics = {
        "topic": topic,
        "query_type": query_type,
        "baseline": {
            "precision_at_5": precision_at_k(baseline_ranked, judgments, 5),
            "ndcg_at_5": ndcg_at_k(baseline_ranked, judgments, 5, judged_pool),
            "source_coverage_recall": source_coverage_recall(baseline_ranked, judged_pool, judgments),
        },
        "candidate": {
            "precision_at_5": precision_at_k(candidate_ranked, judgments, 5),
            "ndcg_at_5": ndcg_at_k(candidate_ranked, judgments, 5, judged_pool),
            "source_coverage_recall": source_coverage_recall(candidate_ranked, judged_pool, judgments),
        },
        "stability": {
            "overall_jaccard": jaccard(
                set().union(*baseline_sets.values()),
                set().union(*candidate_sets.values()),
            ),
            "overall_retention_vs_baseline": retention(
                set().union(*baseline_sets.values()),
                set().union(*candidate_sets.values()),
            ),
            "per_source": {
                source: {
                    "baseline_count": len(baseline_sets[source]),
                    "candidate_count": len(candidate_sets[source]),
                    "jaccard": jaccard(baseline_sets[source], candidate_sets[source]),
                    "retention_vs_baseline": retention(baseline_sets[source], candidate_sets[source]),
                }
                for source in SOURCE_KEYS
            },
        },
    }
    return metrics


def write_markdown_summary(
    output_dir: Path,
    baseline_label: str,
    candidate_label: str,
    topic_summaries: List[Dict[str, Any]],
) -> None:
    lines = [
        f"# Search Quality Evaluation",
        "",
        f"- Baseline: `{baseline_label}`",
        f"- Candidate: `{candidate_label}`",
        f"- Generated: {datetime.now().isoformat(timespec='seconds')}",
        "",
        "## Topic Metrics",
        "",
        "| Topic | Base P@5 | Cand P@5 | Base nDCG@5 | Cand nDCG@5 | Jaccard | Retention |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ]
    for summary in topic_summaries:
        lines.append(
            "| {topic} | {bp:.2f} | {cp:.2f} | {bn:.2f} | {cn:.2f} | {jac:.2f} | {ret:.2f} |".format(
                topic=summary["topic"],
                bp=summary["baseline"]["precision_at_5"],
                cp=summary["candidate"]["precision_at_5"],
                bn=summary["baseline"]["ndcg_at_5"],
                cn=summary["candidate"]["ndcg_at_5"],
                jac=summary["stability"]["overall_jaccard"],
                ret=summary["stability"]["overall_retention_vs_baseline"],
            )
        )
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- `Precision@5` and `nDCG@5` depend on the judged union pool, not a full gold corpus.")
    lines.append("- `Source coverage recall` measures whether a run surfaced at least one judged-good result from the good sources in the judged pool.")
    lines.append("- `Jaccard` and `retention` are stability guards against baseline drift, not truth metrics.")
    (output_dir / "summary.md").write_text("\n".join(lines))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate last30days search quality locally")
    parser.add_argument("--baseline-rev", default="origin/main", help="Git revision for the baseline run")
    parser.add_argument("--candidate-rev", default=None, help="Optional git revision for the candidate run")
    parser.add_argument("--no-default-topics", action="store_true", help="Do not include the built-in 5-topic suite")
    parser.add_argument("--topic", action="append", default=[], help="Extra topic to evaluate (repeatable)")
    parser.add_argument("--search", default=DEFAULT_SEARCH, help="Comma-separated sources passed to --search")
    parser.add_argument("--timeout", type=int, default=180, help="Per-topic timeout passed to last30days")
    parser.add_argument("--per-source-limit", type=int, default=5, help="Items per source to judge")
    parser.add_argument("--include-web", action="store_true", help="Include web-search keys and native web backends")
    parser.add_argument("--judge-model", default=None, help="Gemini judge model override")
    parser.add_argument("--judge-provider", choices=["auto", "gemini", "none"], default="auto")
    parser.add_argument("--keep-worktrees", action="store_true", help="Leave temporary baseline/candidate worktrees on disk")
    parser.add_argument("--output-dir", default=None, help="Output directory (default: docs/test-results/search-quality-<timestamp>)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    output_dir = Path(args.output_dir) if args.output_dir else REPO_ROOT / "docs" / "test-results" / f"search-quality-{timestamp}"
    output_dir.mkdir(parents=True, exist_ok=True)

    topics = [] if args.no_default_topics else list(DEFAULT_TOPICS)
    topics.extend((topic, "custom") for topic in args.topic)
    if not topics:
        raise SystemExit("No topics configured. Use the default suite or pass --topic.")

    judge_config = envlib.get_config()
    judge_provider = args.judge_provider
    gemini_api_key = resolve_google_judge_api_key(judge_config)
    judge_model = args.judge_model or judge_config.get("GEMINI_MODEL") or DEFAULT_JUDGE_MODEL
    if judge_provider == "auto":
        judge_provider = "gemini" if gemini_api_key else "none"
    if judge_provider == "none":
        gemini_api_key = None

    eval_env, eval_home = create_eval_env(include_web=args.include_web)
    baseline_dir = create_worktree(args.baseline_rev)
    candidate_dir = create_worktree(args.candidate_rev) if args.candidate_rev else REPO_ROOT

    baseline_label = args.baseline_rev
    candidate_label = args.candidate_rev or "working-tree"
    topic_summaries: List[Dict[str, Any]] = []

    try:
        for topic, query_type in topics:
            slug = slugify(topic)
            baseline_report, baseline_stderr = run_last30days(
                baseline_dir,
                topic,
                search=args.search,
                timeout_seconds=args.timeout,
                include_web=args.include_web,
                env=eval_env,
            )
            candidate_report, candidate_stderr = run_last30days(
                candidate_dir,
                topic,
                search=args.search,
                timeout_seconds=args.timeout,
                include_web=args.include_web,
                env=eval_env,
            )

            topic_dir = output_dir / slug
            topic_dir.mkdir(parents=True, exist_ok=True)
            (topic_dir / "baseline.json").write_text(json.dumps(baseline_report, indent=2))
            (topic_dir / "candidate.json").write_text(json.dumps(candidate_report, indent=2))
            (topic_dir / "baseline.stderr.txt").write_text(baseline_stderr)
            (topic_dir / "candidate.stderr.txt").write_text(candidate_stderr)

            baseline_ranked = build_ranked_items(baseline_report, args.per_source_limit)
            candidate_ranked = build_ranked_items(candidate_report, args.per_source_limit)
            union_map = {item["key"]: item for item in baseline_ranked + candidate_ranked}
            judgments = get_judgments(
                output_dir=output_dir,
                slug=slug,
                topic=topic,
                query_type=query_type,
                items=list(union_map.values()),
                judge_model=judge_model,
                gemini_api_key=gemini_api_key,
            )

            summary = summarize_topic(
                topic=topic,
                query_type=query_type,
                baseline_report=baseline_report,
                candidate_report=candidate_report,
                judged_pool=list(union_map.values()),
                judgments=judgments,
                per_source_limit=args.per_source_limit,
            )
            topic_summaries.append(summary)

        payload = {
            "baseline": baseline_label,
            "candidate": candidate_label,
            "judge_provider": judge_provider,
            "judge_model": judge_model if gemini_api_key else None,
            "topics": topic_summaries,
        }
        (output_dir / "summary.json").write_text(json.dumps(payload, indent=2))
        write_markdown_summary(output_dir, baseline_label, candidate_label, topic_summaries)
        print(output_dir)
        return 0
    finally:
        if not args.keep_worktrees:
            remove_worktree(baseline_dir)
            if args.candidate_rev:
                remove_worktree(candidate_dir)
        shutil.rmtree(eval_home, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
