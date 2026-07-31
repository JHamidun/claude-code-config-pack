#!/usr/bin/env python3
"""Two-sided pairwise judge: A-vs-B and B-vs-A, keep only on a vote majority.

Guards against position bias (LLM judges systematically favor the first
option) and against the generator grading its own output: this runs as a
separate process with only the two artifacts, no authorship information.

    python pairwise_judge.py --champion old.md --candidate new.md \
        --criteria "clarity, factual density, absence of filler"

Exit code 0 = keep candidate, 1 = keep champion (tie included).
EVAL_JUDGE_STUB=1 runs offline with a deterministic fake judge.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

PROMPT = """You are judging two versions of the same artifact.

Criteria: {criteria}

Judge quality only. Do NOT favor a version because it appears first.
Do NOT reward length for its own sake. If they are equivalent, answer "tie".
You are not told which one is the reference, the baseline, or the newer draft;
do not speculate about it.

Return ONLY JSON: {{"winner": "A" | "B" | "tie", "reason": "<one sentence>"}}

--- VERSION A ---
{a}

--- VERSION B ---
{b}
"""


def ask(cmd: list[str], prompt: str) -> dict:
    if os.environ.get("EVAL_JUDGE_STUB") == "1":
        h = hashlib.sha1(prompt.encode("utf-8")).hexdigest()
        return {"winner": ["A", "B", "tie"][int(h[:2], 16) % 3], "reason": "stub"}
    res = subprocess.run(cmd, input=prompt, capture_output=True, text=True,
                         encoding="utf-8", errors="replace",
                         timeout=int(os.environ.get("EVAL_JUDGE_TIMEOUT", "180")))
    if res.returncode != 0:
        raise RuntimeError(f"judge failed rc={res.returncode}: {res.stderr[:300]}")
    m = re.search(r"\{.*\}", res.stdout, re.S)
    if not m:
        raise ValueError(f"judge returned no JSON: {res.stdout[:200]!r}")
    return json.loads(m.group(0))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--champion", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--criteria", required=True)
    ap.add_argument("--judge-cmd", default=os.environ.get(
        "EVAL_JUDGE_CMD", "claude -p --output-format text"))
    ap.add_argument("--rounds", type=int, default=1,
                    help="repeat the swapped pair N times (odd N breaks ties)")
    a = ap.parse_args()

    champ = Path(a.champion).read_text("utf-8", errors="replace")
    cand = Path(a.candidate).read_text("utf-8", errors="replace")
    cmd = a.judge_cmd.split()

    votes = {"candidate": 0, "champion": 0, "tie": 0}
    log = []
    for i in range(a.rounds):
        # order 1: A=candidate, B=champion
        r1 = ask(cmd, PROMPT.format(criteria=a.criteria, a=cand, b=champ))
        # order 2: A=champion, B=candidate
        r2 = ask(cmd, PROMPT.format(criteria=a.criteria, a=champ, b=cand))
        for r, cand_letter in ((r1, "A"), (r2, "B")):
            w = str(r.get("winner", "tie")).strip()
            if w == cand_letter:
                votes["candidate"] += 1
            elif w == "tie":
                votes["tie"] += 1
            else:
                votes["champion"] += 1
        log.append({"round": i + 1, "order1": r1, "order2": r2})

    keep = votes["candidate"] > votes["champion"]
    margin = "clear" if votes["champion"] == 0 and votes["candidate"] > 0 else "slight"
    print(json.dumps({
        "votes": votes,
        "keep_candidate": keep,
        "margin": margin if keep else "-",
        "verdict": "keep" if keep else "rollback (tie holds the champion)",
        "rounds": log,
    }, ensure_ascii=False, indent=2))
    return 0 if keep else 1


if __name__ == "__main__":
    sys.exit(main())
