#!/usr/bin/env python3
"""Second reader for de-ai-ify: the local linter always, Jev only on request.

Default (no flags): the local linter ru_lint only. No network, no key is read, and
jev_client is not even imported.

Jev (TypeSafe API, hosted in the USA) runs only with BOTH flags:
    --jev      ask Jev the calibrated questions of references/jev-questions.json
    --public   you confirm the text is public: a post, a comment or an article that will be published
Client and internal texts are never sent without the owner's direct word for that very task. Before
anything leaves, the script prints how many paragraphs and characters go and where to. Text that
looks like a secret (key, token, private key, password) is never sent, with or without flags.

Jev hints are one more source for the defect list, not a gate: they never change the exit code.
A questions file may say "unit": "reply": then the whole text is one reply and every question is asked once
about it (the voice questions of references/jev-voice-questions.json work that way).
The questions are in English (vendor: English is the primary language), the text is Russian. Only
questions that passed references/jev-calibration.md are on; --include-uncalibrated adds the rest and
will produce false alarms.

Usage:
    python jev_audit.py FILE [--profile user|strict] [-v]
    python jev_audit.py FILE --jev --public [--audience TEXT] [--platform TEXT] [--json OUT]
    python jev_audit.py -        # text from stdin
Exit codes: 0 done, 1 the local linter found errors, 2 refusal, usage error or unreadable input.
"""
import argparse
import hashlib
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ru_lint  # noqa: E402  (same folder)

REFS = os.path.join(os.path.dirname(HERE), "references")
DEFAULT_QUESTIONS = os.path.join(REFS, "jev-questions.json")
CLIENT_DIR = "~/.claude/tools"            # the owner's hardened client lives here
DESTINATION = "api.typesafe.ai (США)"
ROUTE = "typesafe"                          # always the direct API; never OpenRouter from here
MAX_QUESTIONS = 64                          # per request: the client's own limit
MAX_BODY_BYTES = 128_000                    # request body: the client's own limit
MAX_PARAGRAPH_CHARS = 30_000                # far below the 32k-token state budget of the model
DEFAULT_MAX_PARAGRAPHS = 60
DEFAULT_MAX_COST = 0.05                     # USD per run; a 20-paragraph text costs about a cent

# Shapes of secrets that must never leave: the same ones the owner's pre-publish gate blocks
# (skills/jev/assets/battery-pre-publish.json).
SECRET_SHAPES = {
    "api-key": re.compile(r"sk-[A-Za-z0-9_-]{20,}|AIza[0-9A-Za-z_-]{30,}|gh[pousr]_[A-Za-z0-9]{30,}"
                          r"|xox[abprs]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}"),
    "private-key": re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    "telegram-bot-token": re.compile(r"\b\d{8,10}:[A-Za-z0-9_-]{35}\b"),
    "password": re.compile(r"(?:password|passwd|пароль|pwd)\s*[:=]\s*\S{6,}", re.IGNORECASE),
}
FENCE = re.compile(r"^ {0,3}(`{3,}|~{3,})")


class Refusal(Exception):
    """The run must stop before anything is sent."""


# --- questions ----------------------------------------------------------------

def load_questions(path):
    with open(path, "rb") as fh:
        cfg = json.loads(fh.read().decode("utf-8-sig"))
    qs = cfg.get("questions")
    if not isinstance(qs, dict) or not qs:
        raise ValueError("в файле вопросов нет раздела questions")
    for qid, q in qs.items():
        for field in ("ask", "yes", "no", "show_at"):
            if field not in q:
                raise ValueError(f"у вопроса {qid} нет поля {field}")
        if not isinstance(q["show_at"], (int, float)) or not 0 < q["show_at"] <= 1:
            raise ValueError(f"у вопроса {qid} порог показа вне (0, 1]")
    if cfg.setdefault("unit", "paragraph") not in ("paragraph", "reply"):
        raise ValueError("unit должен быть paragraph или reply")
    cfg.setdefault("preamble", "")
    cfg.setdefault("state_defaults", {})
    cfg.setdefault("calibration", {})
    return cfg


def selected_ids(cfg, include_uncalibrated=False):
    return [qid for qid, q in cfg["questions"].items() if include_uncalibrated or q.get("enabled")]


def build_questions(client, cfg, ids):
    pre = cfg["preamble"].strip()
    out = {}
    for qid in ids:
        q = cfg["questions"][qid]
        ask = f"{pre} {q['ask']}".strip()
        out[qid] = client.noul(ask, yes=q["yes"], no=q["no"])
    return out


def chunks(ids, size=MAX_QUESTIONS):
    return [ids[i:i + size] for i in range(0, len(ids), size)]


# --- text ---------------------------------------------------------------------

def split_paragraphs(text):
    """Blocks of text separated by blank lines; code blocks, rules and lone headings are dropped."""
    if text.startswith("\ufeff"):
        text = text[1:]
    lines, fence, kept = text.replace("\r\n", "\n").replace("\r", "\n").split("\n"), None, []
    for line in lines:
        m = FENCE.match(line)
        if fence:
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence):
                fence = None
            kept.append("")
            continue
        if m:
            fence = m.group(1)
            kept.append("")
            continue
        kept.append(line)
    out = []
    for block in re.split(r"\n\s*\n", "\n".join(kept)):
        block = block.strip()
        if not block or re.fullmatch(r"(-{3,}|\*{3,}|_{3,})", block):
            continue
        if "\n" not in block and block.startswith("#"):
            continue
        out.append(block)
    return out


def find_secrets(paragraphs):
    """[(paragraph_no, kind)] without the matched text."""
    return [(i, kind) for i, p in enumerate(paragraphs, 1)
            for kind, rx in SECRET_SHAPES.items() if rx.search(p)]


def body_size(state, questions, model):
    return len(json.dumps({"state": state, "model": model, "questions": questions},
                          ensure_ascii=False, allow_nan=False).encode("utf-8"))


def fits(state, questions, model, limit=MAX_BODY_BYTES):
    text = state.get("paragraph", state.get("reply", ""))
    return len(text) <= MAX_PARAGRAPH_CHARS and body_size(state, questions, model) <= limit


def build_state(paragraph, previous, audience, platform):
    return {"paragraph": paragraph, "previous_paragraph": previous,
            "audience": audience, "platform": platform}


def build_reply_state(reply, audience, platform):
    return {"reply": reply, "audience": audience, "platform": platform}


def state_for(unit, texts, index, audience, platform):
    if unit == "reply":
        return build_reply_state(texts[index], audience, platform)
    return build_state(texts[index], texts[index - 1] if index else "", audience, platform)


# --- Jev run ------------------------------------------------------------------

def _load_client():
    """The owner's client: no redirects, own User-Agent, limits checked before the key is read."""
    if CLIENT_DIR not in sys.path:
        sys.path.insert(0, CLIENT_DIR)
    import jev_client
    return jev_client


class RunState:
    def __init__(self):
        self.lock = threading.Lock()
        self.cost = 0.0
        self.requests = 0
        self.stopped = None        # reason string when the run was cut short
        self.model_reported = None

    def add(self, out):
        with self.lock:
            self.requests += 1
            self.cost += float(out.get("_cost_usd") or 0.0)
            self.model_reported = out.get("model") or self.model_reported

    def stop(self, reason):
        with self.lock:
            self.stopped = self.stopped or reason


def ask_paragraph(client, cfg, ids, index, paragraphs, audience, platform, model, run, max_cost):
    """One paragraph (or the whole reply) through all question chunks. Returns (answers {qid: p}, skipped_reason or None)."""
    if run.stopped:
        return {}, run.stopped
    state = state_for(cfg.get("unit", "paragraph"), paragraphs, index, audience, platform)
    answers = {}
    for chunk in chunks(ids):
        questions = build_questions(client, cfg, chunk)
        if not fits(state, questions, model):
            return {}, "текст слишком длинный для одного запроса, пропущен"
        if run.cost >= max_cost:
            run.stop("остановлено по лимиту стоимости")
            return answers, run.stopped
        try:
            out = client.system_one(state, questions, model=model, route=ROUTE)
        except client.JevError as exc:
            status = getattr(exc, "status", 0)
            if status in (401, 402, 403):
                run.stop(f"остановлено, Jev отказал в доступе (HTTP {status})")
            return answers, f"Jev недоступен: {str(exc)[:160]}"
        run.add(out)
        for qid in chunk:
            answers[qid] = float(out["answers"][qid]["noul"])
    return answers, None


def run_jev(client, cfg, ids, paragraphs, audience, platform, model, max_cost, workers=4):
    run = RunState()
    results = [None] * len(paragraphs)

    def work(i):
        try:
            results[i] = ask_paragraph(client, cfg, ids, i, paragraphs, audience, platform,
                                       model, run, max_cost)
        except Exception as exc:   # one bad paragraph must not lose the others
            results[i] = ({}, f"ошибка {type(exc).__name__}")

    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(paragraphs)))) as pool:
        list(pool.map(work, range(len(paragraphs))))
    return run, results


def hints(cfg, results):
    """[(paragraph_no, qid, probability)] at or above each question's show_at, strongest first per paragraph."""
    out = []
    for i, (answers, _) in enumerate(results, 1):
        for qid, p in answers.items():
            if p >= cfg["questions"][qid]["show_at"]:
                out.append((i, qid, p))
    return sorted(out, key=lambda t: (t[0], -t[2]))


def excerpt(s, n=50):
    s = " ".join(s.split())
    return s if len(s) <= n else s[:n - 1] + "…"


def write_json(path, cfg, run, model, paragraphs, results, lint_findings):
    """Probabilities and hashes only: the text itself is not written."""
    data = {"model_requested": model, "model_reported": run.model_reported,
            "cost_usd": round(run.cost, 6), "requests": run.requests, "stopped": run.stopped,
            "lint": [[f.level, f.line, f.rule] for f in lint_findings if f.level != "NOTE"],
            "paragraphs": [{"n": i, "chars": len(p), "sha1": hashlib.sha1(p.encode("utf-8")).hexdigest()[:12],
                            "skipped": reason, "answers": answers}
                           for i, (p, (answers, reason)) in enumerate(zip(paragraphs, results), 1)]}
    with open(path, "x", encoding="utf-8", newline="\n") as fh:   # never overwrite another run's file
        json.dump(data, fh, ensure_ascii=False, indent=1)
        fh.write("\n")


# --- CLI ----------------------------------------------------------------------

def _read(path):
    if path == "-":
        data = sys.stdin.buffer.read()
    else:
        with open(path, "rb") as fh:
            data = fh.read()
    return data.decode("utf-8-sig")


def build_parser():
    ap = argparse.ArgumentParser(description="De-AI second reader: local lint always, Jev only with --jev --public.")
    ap.add_argument("file", help="text file, or - for stdin")
    ap.add_argument("--profile", choices=ru_lint.PROFILES, default="user", help="local linter profile")
    ap.add_argument("-v", "--verbose", action="store_true", help="also print NOTE lines of the linter")
    ap.add_argument("--jev", action="store_true", help="also ask Jev (text leaves the machine, see --public)")
    ap.add_argument("--public", action="store_true", help="confirm that the text is public; required by --jev")
    ap.add_argument("--audience", help="who reads the text (goes to Jev as state.audience)")
    ap.add_argument("--platform", help="where it is published (goes to Jev as state.platform)")
    ap.add_argument("--questions", default=DEFAULT_QUESTIONS, help="questions file (default: references/jev-questions.json)")
    ap.add_argument("--include-uncalibrated", action="store_true", help="also ask the questions that did not pass calibration")
    ap.add_argument("--model", help="Jev model id; default: JEV_MODEL, else the one the questions were calibrated on")
    ap.add_argument("--json", metavar="OUT", help="write probabilities (no text) to a NEW file")
    ap.add_argument("--max-cost", type=float, default=DEFAULT_MAX_COST, help="stop sending after this many USD")
    ap.add_argument("--max-paragraphs", type=int, default=DEFAULT_MAX_PARAGRAPHS)
    ap.add_argument("--workers", type=int, default=4, help=argparse.SUPPRESS)
    return ap


def main(argv=None):
    a = build_parser().parse_args(argv)
    try:
        text = _read(a.file)
    except (OSError, UnicodeDecodeError) as exc:
        name = "<stdin>" if a.file == "-" else a.file
        print(f"{name}: не прочитан, {type(exc).__name__}", file=sys.stderr)
        return 2
    name = "<stdin>" if a.file == "-" else a.file

    findings = ru_lint.lint(text, a.profile)
    for f in findings:
        if f.level != "NOTE" or a.verbose:
            print(ru_lint.format_finding(name, f))
    errors = sum(f.level == "ERROR" for f in findings)
    warns = sum(f.level == "WARN" for f in findings)
    print(f"Линтер: профиль {a.profile}; ошибок {errors}, предупреждений {warns}")
    code = 1 if errors else 0

    if not a.jev:
        print("Jev: выключен, работает только локальный линтер. Для публичного текста: --jev --public")
        return code
    try:
        return _jev_step(a, text, findings, code)
    except Refusal as why:
        print(f"Jev: отказ. {why}", file=sys.stderr)
        return 2


def _jev_step(a, text, findings, code):
    if not a.public:
        raise Refusal("--jev отправляет текст в " + DESTINATION + ". Добавь --public, если текст публичный. "
                      "Клиентские и внутренние тексты без прямого слова владельца не отправляются.")
    try:
        cfg = load_questions(a.questions)
    except (OSError, ValueError) as exc:
        raise Refusal(f"файл вопросов не прочитан: {type(exc).__name__}") from None
    ids = selected_ids(cfg, a.include_uncalibrated)
    if not ids:
        print("Jev: ни один вопрос не откалиброван (references/jev-calibration.md), Jev не вызывается")
        return code
    if a.include_uncalibrated:
        print("Jev: включены неоткалиброванные вопросы, ложных срабатываний может быть много")

    reply_unit = cfg.get("unit") == "reply"
    paragraphs = [text.strip()] if reply_unit and text.strip() else ([] if reply_unit else split_paragraphs(text))
    if not paragraphs:
        print("Jev: в тексте нет абзацев для проверки")
        return code
    if len(paragraphs) > a.max_paragraphs:
        raise Refusal(f"абзацев {len(paragraphs)}, больше лимита {a.max_paragraphs} (--max-paragraphs)")
    secrets = find_secrets(paragraphs)
    if secrets:
        found = ", ".join(f"абзац {i}: {kind}" for i, kind in secrets)
        raise Refusal(f"текст похож на секрет ({found}); ничего не отправлено")

    audience = a.audience or cfg["state_defaults"].get("audience", "")
    platform = a.platform or cfg["state_defaults"].get("platform", "")
    calibrated_on = (cfg.get("calibration") or {}).get("model") or cfg.get("model")
    model = a.model or os.environ.get("JEV_MODEL") or cfg.get("model")
    chars = sum(len(p) for p in paragraphs)
    what = "ответ" if reply_unit else f"{len(paragraphs)} абз."
    print(f"Jev: {what}, {chars} зн. уйдёт в {DESTINATION}; модель {model}; вопросов {len(ids)}", flush=True)
    if calibrated_on and model != calibrated_on:
        print(f"Jev: пороги откалиброваны на {calibrated_on}, а идёт {model}: подсказкам верить меньше")

    try:
        client = _load_client()
    except Exception as exc:   # a missing client must not lose the linter result
        print(f"Jev: клиент не загрузился ({type(exc).__name__}), остался локальный линтер")
        return code
    run, results = run_jev(client, cfg, ids, paragraphs, audience, platform, model, a.max_cost, a.workers)

    label = (lambda i: "ответ") if reply_unit else (lambda i: f"абзац {i}")
    for i, qid, p in hints(cfg, results):
        q = cfg["questions"][qid]
        print(f"{label(i)}: {qid} {q.get('label_ru', qid)} ({p:.2f}) «{excerpt(paragraphs[i - 1])}»")
    for i, (_, reason) in enumerate(results, 1):
        if reason:
            print(f"{label(i)}: {reason}")
    total = len(hints(cfg, results))
    print(f"Jev: подсказок {total}; запросов {run.requests}, ${run.cost:.5f}; "
          f"модель {run.model_reported or model}" + (f"; {run.stopped}" if run.stopped else ""))
    if a.json:
        try:
            write_json(a.json, cfg, run, model, paragraphs, results, findings)
        except OSError as exc:
            print(f"--json: не записано, {type(exc).__name__} (файл должен быть новым)", file=sys.stderr)
            return 2
    return code


if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="replace")
    sys.exit(main())
