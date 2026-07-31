#!/usr/bin/env python3
"""B-roll generation runner: Runway Seedance 2 (exploreMode, unlimited sub).

Handles account-level 429 throttle: keeps up to CONCURRENCY tasks in flight,
submits one at a time, polls running tasks, recovers SUCCEEDED by task_id.
get_task returns {"task": {...}} — always unwrap.

Usage:
  python broll_runner.py shots_all.json          # submit+poll+download missing
  python broll_runner.py shots_all.json --status
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.home() / ".claude/skills/video-generation/scripts"))
from runway_client import RunwayClient  # noqa: E402

BASE = Path(__file__).parent
STATE_F = BASE / "broll" / "state.json"
CONCURRENCY = 3
SUBMIT_GAP = 8       # seconds between successful submits
THROTTLE_BACKOFF = 60


def load_state():
    if STATE_F.exists():
        return json.loads(STATE_F.read_text(encoding="utf-8"))
    return {}


def save_state(st):
    STATE_F.write_text(json.dumps(st, indent=1, ensure_ascii=False), encoding="utf-8")


def unwrap(r):
    return r.get("task", r) if isinstance(r, dict) else r


def done_file(sid):
    f = BASE / "broll" / f"{sid}.mp4"
    return f.exists() and f.stat().st_size > 100_000


def main():
    shots = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    c = RunwayClient()
    st = load_state()

    if "--status" in sys.argv:
        ok = 0
        for s in shots:
            f = done_file(s["id"])
            ok += f
            print(f"{s['id']}: {st.get(s['id'], {}).get('status', 'NONE')} {'[OK]' if f else ''}")
        print(f"\n{ok}/{len(shots)} downloaded")
        return

    # try to recover any task_ids first
    todo = []
    for s in shots:
        sid = s["id"]
        if done_file(sid):
            continue
        rec = st.get(sid, {})
        tid = rec.get("task_id")
        if tid:
            try:
                t = unwrap(c.get_task(tid))
                if t.get("status") == "SUCCEEDED":
                    arts = c.list_artifacts(t)
                    if arts:
                        c.download(arts[0], str(BASE / "broll" / f"{sid}.mp4"))
                        print(f"recovered {sid}", flush=True)
                        st[sid]["status"] = "DONE"
                        save_state(st)
                        continue
                elif t.get("status") in ("RUNNING", "PENDING", "THROTTLED"):
                    pass  # still in flight, keep its tid
                else:
                    rec.pop("task_id", None)  # failed/canceled, resubmit
            except Exception:
                pass
        todo.append(s)

    print(f"{len(todo)} shots to do", flush=True)
    active = {}  # sid -> tid
    # seed active from in-flight task_ids
    for s in list(todo):
        rec = st.get(s["id"], {})
        if rec.get("task_id") and rec.get("status") in ("RUNNING", "PENDING", "THROTTLED", "SUBMITTED"):
            active[s["id"]] = rec["task_id"]

    queue = [s for s in todo if s["id"] not in active]

    while queue or active:
        # submit while slots free
        while queue and len(active) < CONCURRENCY:
            s = queue[0]
            try:
                img = s.get("image")
                t = unwrap(c.generate_seedance(
                    prompt=s["prompt"],
                    image_path=str(BASE / img) if img else None,
                    duration=s.get("duration", 5),
                    aspect_ratio="9:16",
                    resolution=s.get("resolution", "720p"),
                    generate_audio=False, explore_mode=True, wait=False,
                    name=f"matt_{s['id']}",
                ))
                tid = t["id"]
                st[s["id"]] = {"task_id": tid, "status": "SUBMITTED"}
                save_state(st)
                active[s["id"]] = tid
                queue.pop(0)
                print(f"submitted {s['id']} {tid[:8]} (active={len(active)})", flush=True)
                time.sleep(SUBMIT_GAP)
            except Exception as e:
                msg = str(e)
                if "429" in msg:
                    print(f"429 throttle (active={len(active)}), backoff {THROTTLE_BACKOFF}s", flush=True)
                else:
                    print(f"SUBMIT ERR {s['id']}: {msg[:100]}", flush=True)
                    time.sleep(15)
                break  # go poll active

        if not active:
            time.sleep(THROTTLE_BACKOFF if queue else 1)
            continue

        time.sleep(15)
        for sid in list(active):
            try:
                t = unwrap(c.get_task(active[sid]))
            except Exception as e:
                print(f"poll err {sid}: {str(e)[:60]}", flush=True)
                continue
            status = t.get("status")
            st[sid]["status"] = status
            save_state(st)
            if status == "SUCCEEDED":
                arts = c.list_artifacts(t)
                if arts:
                    out = BASE / "broll" / f"{sid}.mp4"
                    c.download(arts[0], str(out))
                    print(f"DONE {sid} ({out.stat().st_size//1024}KB) [{len(active)-1} active, {len(queue)} queued]", flush=True)
                    st[sid]["status"] = "DONE"
                    save_state(st)
                del active[sid]
            elif status in ("FAILED", "CANCELED"):
                print(f"FAILED {sid}: {json.dumps(t.get('failure', t.get('error', '?')))[:150]}", flush=True)
                del active[sid]
                st[sid].pop("task_id", None)
                queue.append(next(s for s in shots if s["id"] == sid))  # retry
                save_state(st)

    print("ALL DONE", flush=True)


if __name__ == "__main__":
    main()
