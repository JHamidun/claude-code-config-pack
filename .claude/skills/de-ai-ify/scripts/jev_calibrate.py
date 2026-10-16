#!/usr/bin/env python3
"""Calibrate the Jev questions of de-ai-ify: which of them may be switched on.

Protocol (the result is in ../references/jev-calibration.md):
  negatives  the owner's live replies (every fenced block of comment-replies/references/examples.md outside
             the anti-example section, plus the verified live replies of anchor-quotes.md);
  positives  synthetic machine drafts of references/jev-calibration-corpus.json, labelled by pattern while writing;
  rule       a question stays on only if it fires (probability >= its show_at) on at most 5% of the live
             paragraphs AND on at least 60% of the machine paragraphs that carry its pattern, with at least
             5 such paragraphs. show_at is fixed in the questions file BEFORE the run and is never tuned.

Commands:
    python jev_calibrate.py corpus                    offline: build the corpus and print its size
    python jev_calibrate.py run --public              LIVE: send the corpus to Jev (api.typesafe.ai, USA)
    python jev_calibrate.py report [--apply]          offline: recompute the metrics from the raw file;
                                                      --apply writes enabled/status into the questions file
`run` needs --public: every text of the corpus is public (published replies) or synthetic. It stops before
the budget (--budget, USD, counted from _cost_usd of the answers), resumes from the raw file (finished items are
skipped) and writes the raw file after every few items. The raw file holds probabilities and text hashes only.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import date

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jev_audit as ja  # noqa: E402  (same folder: the calibration runs the production path)

SKILLS = os.path.dirname(os.path.dirname(HERE))
EXAMPLES = os.path.join(SKILLS, "comment-replies", "references", "examples.md")
CORPUS = os.path.join(ja.REFS, "jev-calibration-corpus.json")
RAW = os.path.join(ja.REFS, "jev-calibration-raw.json")
MAX_FALSE_RATE = 0.05
MIN_HIT_RATE = 0.60
MIN_POSITIVES = 5
DEFAULT_BUDGET = 0.30
SAVE_EVERY = 8


# --- corpus ---------------------------------------------------------------------

def _sha(text):
    return hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]


def live_blocks(path=None):
    """Fenced blocks of examples.md that are real replies (the anti-example section is left out)."""
    with open(path or EXAMPLES, encoding="utf-8-sig") as fh:
        lines = fh.read().replace("\r\n", "\n").split("\n")
    blocks, inside, cur, head = [], False, [], ""
    for line in lines:
        if line.startswith("#"):
            head = line
        if line.strip().startswith("```"):
            if not inside:
                inside, cur = True, []
            else:
                inside = False
                if "Анти" not in head and "НЕ делать" not in head:
                    blocks.append("\n".join(cur).strip())
        elif inside:
            cur.append(line)
    return [b for b in blocks if b]


def _paras(text):
    return [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]


def build_corpus(unit="paragraph", examples=None, corpus_path=None):
    """Items: id, kind (live | machine | hard_negative), verified, patterns, voice, near_miss, text, previous, sha1.

    unit "paragraph": one item per paragraph, `previous` is the paragraph before it in the same reply.
    unit "reply": one item per reply or draft (hard negatives are paragraph-sized and are left out).
    """
    with open(corpus_path or CORPUS, encoding="utf-8") as fh:
        corpus = json.load(fh)
    replies = []   # (id, kind, verified, [paragraph dicts])
    for i, block in enumerate(live_blocks(examples), 1):
        replies.append((f"live-ex{i:02d}", "live", False, [{"text": p, "patterns": [], "voice": []} for p in _paras(block)]))
    for r in corpus["live_extra"]:
        replies.append((f"live-{r['id']}", "live", True, [{"text": p, "patterns": [], "voice": []} for p in r["paragraphs"]]))
    for d in corpus["machine"]:
        replies.append((f"machine-{d['id']}", "machine", False, d["paragraphs"]))
    items = []
    for rid, kind, verified, paras in replies:
        if unit == "reply":
            text = "\n\n".join(p["text"] for p in paras)
            items.append({"id": rid, "kind": kind, "verified": verified, "text": text, "previous": "",
                          "patterns": sorted({x for p in paras for x in p["patterns"]}),
                          "voice": sorted({x for p in paras for x in p["voice"]}), "near_miss": None})
            continue
        for k, p in enumerate(paras, 1):
            items.append({"id": f"{rid}-p{k}", "kind": kind, "verified": verified, "text": p["text"],
                          "previous": paras[k - 2]["text"] if k > 1 else "",
                          "patterns": p["patterns"], "voice": p["voice"], "near_miss": None})
    if unit == "paragraph":
        for h in corpus["hard_negatives"]:
            items.append({"id": f"hard-{h['id']}", "kind": "hard_negative", "verified": False, "text": h["text"],
                          "previous": "", "patterns": [], "voice": [], "near_miss": h["near_miss"]})
    for it in items:
        it["sha1"] = _sha(it["text"])
    return items


# --- run ------------------------------------------------------------------------

def write_atomic(path, text):
    """Write a file so that a crash never leaves it half-written. On Windows os.replace can be refused for a
    moment (an indexer or antivirus holds the target), so it is retried; the last resort is a direct write:
    a paid run must not die because a checkpoint could not be swapped in."""
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    for attempt in range(6):
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.05 * (attempt + 1))
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    try:
        os.remove(tmp)
    except OSError:
        pass


class Raw:
    def __init__(self, path, unit, model, show_at, budget):
        self.path, self.lock = path, threading.Lock()
        if os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                self.data = json.load(fh)
            if self.data.get("unit") != unit:
                raise SystemExit(f"{path}: прогон для unit={self.data.get('unit')}, а просили {unit}")
            if self.data.get("model_requested") != model:
                raise SystemExit(f"{path}: прогон на модели {self.data.get('model_requested')}, а идёт {model}; "
                                 f"смешивать нельзя, возьми новый --raw")
        else:
            self.data = {"schema": 1, "unit": unit, "model_requested": model, "model_reported": [],
                         "date": str(date.today()), "show_at": show_at, "budget_usd": budget,
                         "spent_usd": 0.0, "requests": 0, "items": {}}
        self.data["budget_usd"] = budget
        self.since_save = 0

    def done(self, item_id, sha):
        rec = self.data["items"].get(item_id)
        return bool(rec) and rec.get("sha1") == sha

    def add(self, item, answers, cost, model):
        with self.lock:
            self.data["items"][item["id"]] = {"sha1": item["sha1"], "kind": item["kind"], "answers": answers,
                                              "cost": round(cost, 8)}
            self.data["spent_usd"] = round(self.data["spent_usd"] + cost, 8)
            self.data["requests"] += 1
            if model and model not in self.data["model_reported"]:
                self.data["model_reported"].append(model)
            self.since_save += 1
            if self.since_save >= SAVE_EVERY:
                self.save_locked()

    def save(self):
        with self.lock:
            self.save_locked()

    def save_locked(self):
        write_atomic(self.path, json.dumps(self.data, ensure_ascii=False, indent=1) + "\n")
        self.since_save = 0


def run(cfg, items, ids, raw, client, model, workers=4, unit="paragraph"):
    """Send every item that is not in the raw file yet. Returns (sent, skipped_for_budget, failed)."""
    defaults = cfg["state_defaults"]
    todo = [it for it in items if not raw.done(it["id"], it["sha1"])]
    counters = {"sent": 0, "budget": 0, "failed": 0}
    lock = threading.Lock()
    seen_cost = [0.0003]

    def work(it):
        with lock:
            reserve = max(seen_cost) * max(1, workers)
            if raw.data["spent_usd"] + reserve > raw.data["budget_usd"]:
                counters["budget"] += 1
                return
        state = ({"reply": it["text"]} if unit == "reply" else {"paragraph": it["text"], "previous_paragraph": it["previous"]})
        state.update({"audience": defaults.get("audience", ""), "platform": defaults.get("platform", "")})
        answers, cost, model_seen = {}, 0.0, None
        for chunk in ja.chunks(ids):
            questions = ja.build_questions(client, cfg, chunk)
            if not ja.fits(state, questions, model):
                with lock:
                    counters["failed"] += 1
                return
            try:
                out = client.system_one(state, questions, model=model, route=ja.ROUTE)
            except client.JevError as exc:
                with lock:
                    counters["failed"] += 1
                print(f"{it['id']}: {str(exc)[:120]}", file=sys.stderr)
                return
            cost += float(out.get("_cost_usd") or 0.0)
            model_seen = out.get("model")
            for qid in chunk:
                answers[qid] = float(out["answers"][qid]["noul"])
        with lock:
            seen_cost.append(cost)
            counters["sent"] += 1
        raw.add(it, answers, cost, model_seen)

    def safe(it):
        try:
            work(it)
        except Exception as exc:   # one bad item must not lose the rest of a paid run
            with lock:
                counters["failed"] += 1
            print(f"{it['id']}: {type(exc).__name__}", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        list(pool.map(safe, todo))
    raw.save()
    return counters["sent"], counters["budget"], counters["failed"]


# --- report ---------------------------------------------------------------------

def _is_positive(item, qid, q):
    spec = q.get("calibrate") or {}
    field, value = spec.get("field", "patterns"), spec.get("value", qid)
    return item["kind"] == "machine" and value in item.get(field, [])


def _is_negative(item, q):
    spec = q.get("calibrate") or {}
    if spec.get("negatives") == "verified":
        return item["kind"] == "live" and item["verified"]
    return item["kind"] == "live"


def metrics(cfg, items, raw_data):
    """Per question: counts and the verdict by the pre-registered rule."""
    by_id = {it["id"]: it for it in items}
    answered = {i: by_id[i] for i in raw_data["items"] if i in by_id}
    out = {}
    for qid, q in cfg["questions"].items():
        thr = raw_data["show_at"].get(qid, q["show_at"])

        def fires(item):
            a = raw_data["items"][item["id"]]["answers"].get(qid)
            return None if a is None else a >= thr

        neg = [(it, fires(it)) for it in answered.values() if _is_negative(it, q)]
        pos = [(it, fires(it)) for it in answered.values() if _is_positive(it, qid, q)]
        other = [(it, fires(it)) for it in answered.values()
                 if it["kind"] == "machine" and not _is_positive(it, qid, q)]
        hard = [(it, fires(it)) for it in answered.values() if it["kind"] == "hard_negative" and it["near_miss"] == qid]
        live_rest = [(it, fires(it)) for it in answered.values() if it["kind"] == "live" and not _is_negative(it, q)]
        count = lambda rows: (sum(1 for _, f in rows if f), sum(1 for _, f in rows if f is not None))
        fp, n_neg = count(neg)
        hit, n_pos = count(pos)
        oth, n_oth = count(other)
        hd, n_hd = count(hard)
        lr, n_lr = count(live_rest)
        fp_rate = fp / n_neg if n_neg else None
        hit_rate = hit / n_pos if n_pos else None
        if n_pos < MIN_POSITIVES or not n_neg:
            verdict, reason = False, f"мало данных (положительных {n_pos}, живых {n_neg})"
        else:
            problems = []
            if fp_rate > MAX_FALSE_RATE + 1e-9:
                problems.append(f"ложных {fp}/{n_neg} = {fp_rate:.1%} (нужно не больше {MAX_FALSE_RATE:.0%})")
            if hit_rate < MIN_HIT_RATE - 1e-9:
                problems.append(f"попаданий {hit}/{n_pos} = {hit_rate:.1%} (нужно не меньше {MIN_HIT_RATE:.0%})")
            verdict, reason = not problems, "; ".join(problems) or "прошёл"
        out[qid] = {"show_at": thr, "false": [fp, n_neg], "hit": [hit, n_pos], "other_machine": [oth, n_oth],
                    "hard_negative": [hd, n_hd], "live_rest": [lr, n_lr], "pass": verdict, "reason": reason}
    return out


def fmt_rate(pair):
    k, n = pair
    return f"{k}/{n} ({k / n:.0%})" if n else "0/0"


def table(cfg, m):
    """Markdown table. A column for the live texts outside the negative set appears only when there are any."""
    extra = any(r.get("live_rest", [0, 0])[1] for r in m.values())
    head = ["вопрос", "паттерн", "порог", "ложные на живых", "попадания на машинных", "машинные без паттерна",
            "трудные отрицательные"] + (["прочие живые, справочно"] if extra else []) + ["итог"]
    rows = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for qid, r in m.items():
        q = cfg["questions"][qid]
        cells = [qid, q.get("label_ru", qid), str(r["show_at"]), fmt_rate(r["false"]), fmt_rate(r["hit"]),
                 fmt_rate(r["other_machine"]), fmt_rate(r["hard_negative"])]
        if extra:
            cells.append(fmt_rate(r["live_rest"]))
        cells.append(f"{'ВКЛ' if r['pass'] else 'выкл'}: {r['reason']}")
        rows.append("| " + " | ".join(cells) + " |")
    return "\n".join(rows)


def apply_to_file(path, cfg, m, raw_data):
    """Write enabled/status/calibration into the questions file. show_at is never touched."""
    for qid, r in m.items():
        q = cfg["questions"][qid]
        q["enabled"] = bool(r["pass"])
        q["status"] = "passed" if r["pass"] else "failed: " + r["reason"]
        q["calibration"] = {"false": f"{r['false'][0]}/{r['false'][1]}", "hit": f"{r['hit'][0]}/{r['hit'][1]}"}
    passed = [qid for qid, r in m.items() if r["pass"]]
    plural = {"reply": "replies"}.get(cfg.get("unit", "paragraph"), "paragraphs")
    models = raw_data.get("model_reported") or []
    cfg["calibration"] = {
        "status": (f"calibrated: {len(passed)} of {len(m)} questions passed" if passed
                   else "not calibrated: no question passed the thresholds"),
        "model": models[0] if len(models) == 1 else (None if not models else ", ".join(models)),
        "date": raw_data.get("date"), "spent_usd": raw_data.get("spent_usd"),
        "rule": f"false <= {MAX_FALSE_RATE:.0%} on live {plural} and hit >= {MIN_HIT_RATE:.0%} on "
                f"synthetic machine {plural} that carry the pattern, at least {MIN_POSITIVES} of them",
        "doc": cfg.get("calibration", {}).get("doc", "jev-calibration.md"),
        "raw": cfg.get("calibration", {}).get("raw", "jev-calibration-raw.json")}
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(cfg, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


# --- CLI ------------------------------------------------------------------------

def _load_cfg(path):
    cfg = ja.load_questions(path)
    return cfg, ja.selected_ids(cfg, include_uncalibrated=True)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Calibrate the Jev questions of de-ai-ify.")
    ap.add_argument("cmd", choices=["corpus", "run", "report"])
    ap.add_argument("--questions", default=ja.DEFAULT_QUESTIONS)
    ap.add_argument("--raw", default=RAW)
    ap.add_argument("--unit", choices=["paragraph", "reply"], default=None,
                    help="default: the unit named in the questions file, else paragraph")
    ap.add_argument("--public", action="store_true", help="confirm that the corpus is public or synthetic (run)")
    ap.add_argument("--budget", type=float, default=DEFAULT_BUDGET, help="USD, counted from _cost_usd")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", help="default: JEV_MODEL, else the model of the questions file")
    ap.add_argument("--apply", action="store_true", help="report: write enabled/status into the questions file")
    a = ap.parse_args(argv)

    try:
        cfg, ids = _load_cfg(a.questions)
    except (OSError, ValueError) as exc:
        print(f"файл вопросов не прочитан: {type(exc).__name__}", file=sys.stderr)
        return 2
    unit = a.unit or cfg.get("unit", "paragraph")
    items = build_corpus(unit)
    kinds = {k: sum(1 for i in items if i["kind"] == k) for k in ("live", "machine", "hard_negative")}
    if a.cmd == "corpus":
        print(f"unit {unit}: живых {kinds['live']}, машинных {kinds['machine']}, трудных отрицательных {kinds['hard_negative']}; "
              f"вопросов {len(ids)}")
        return 0

    if a.cmd == "run":
        if not a.public:
            print("Отказ: run отправляет корпус в " + ja.DESTINATION + ". Добавь --public: живые тексты опубликованы, "
                  "машинные синтетические.", file=sys.stderr)
            return 2
        secrets = ja.find_secrets([i["text"] for i in items])
        if secrets:
            print("Отказ: в корпусе есть текст, похожий на секрет; ничего не отправлено", file=sys.stderr)
            return 2
        model = a.model or os.environ.get("JEV_MODEL") or cfg.get("model")
        show_at = {qid: cfg["questions"][qid]["show_at"] for qid in ids}
        raw = Raw(a.raw, unit, model, show_at, a.budget)
        todo = sum(1 for it in items if not raw.done(it["id"], it["sha1"]))
        print(f"Jev: {todo} из {len(items)} текстов уйдёт в {ja.DESTINATION}; модель {model}; вопросов {len(ids)}; "
              f"бюджет ${a.budget:.2f}, уже потрачено ${raw.data['spent_usd']:.5f}", flush=True)
        try:
            client = ja._load_client()
        except Exception as exc:
            print(f"клиент Jev не загрузился: {type(exc).__name__}", file=sys.stderr)
            return 2
        sent, budget_skips, failed = run(cfg, items, ids, raw, client, model, a.workers, unit)
        print(f"отправлено {sent}, пропущено по бюджету {budget_skips}, сбоев {failed}; "
              f"потрачено ${raw.data['spent_usd']:.5f} из ${a.budget:.2f}; модель {raw.data['model_reported']}")
        return 0 if not failed and not budget_skips else 1

    with open(a.raw, encoding="utf-8") as fh:
        raw_data = json.load(fh)
    if raw_data.get("unit") != unit:
        print(f"сырой файл для unit={raw_data.get('unit')}", file=sys.stderr)
        return 2
    by_id = {i["id"]: i for i in items}
    drift = [i for i, rec in raw_data["items"].items() if i not in by_id or by_id[i]["sha1"] != rec["sha1"]]
    if drift:
        print(f"Корпус изменился с момента прогона ({len(drift)} текстов не совпали по хешу); пересчёт не делаю", file=sys.stderr)
        return 2
    m = metrics(cfg, items, raw_data)
    moved = [qid for qid, q in cfg["questions"].items() if raw_data["show_at"].get(qid, q["show_at"]) != q["show_at"]]
    if moved:
        print(f"ВНИМАНИЕ: пороги показа в файле вопросов изменены после прогона ({', '.join(moved)}); "
              f"в расчёте пороги из сырого файла", file=sys.stderr)
    print(table(cfg, m))
    print(f"\nзапросов {raw_data['requests']}, потрачено ${raw_data['spent_usd']:.5f}, модель {raw_data['model_reported']}, "
          f"дата {raw_data['date']}")
    if a.apply:
        apply_to_file(a.questions, cfg, m, raw_data)
        print("записано в", a.questions)
    return 0


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    sys.exit(main())
