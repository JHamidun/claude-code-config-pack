#!/usr/bin/env python3
"""Jev (TypeSafe System One) — typed decisions in ~0.3 s instead of a generated answer.

Jev does not write text. It takes some state plus typed questions and returns calibrated
probabilities: yes/no (Noul), one-of-N (Choice, up to 255 options), a rubric level
(Score, 2–10 levels). All questions are answered in one parallel pass.

Route: the direct TypeSafe API by default (TYPESAFE_API_KEY). OpenRouter
(OPENROUTER_API_KEY, same body) only when chosen explicitly — route="openrouter",
--route openrouter or JEV_ROUTE=openrouter. There is no silent fallback between them.

    python jev_client.py ask "Письмо требует ответа сегодня?" --state "текст письма"
    python jev_client.py choose "Какой отдел?" billing technical sales --state "..."
    python jev_client.py score "Насколько клиент зол?" спокоен раздражён "в ярости" --state "..."
    python jev_client.py rank "почему бот молчит" --candidates cands.json   # {name: description}
    python jev_client.py raw request.json          # full API body, printed back as JSON
    python jev_client.py selftest
    python jev_client.py --route openrouter ask "..." --state "..."

Known limits (vendor-documented, jev-1.13): trained mostly on English — Russian works but
test before relying on it; no counting, arithmetic or date comparison (do those in code);
literal reading of the question; injected instructions inside state can move the answer.

Client limits, checked before the key is read or the network is touched: 1–64 questions,
non-empty instructions, unique non-empty Choice labels, request body ≤ 128000 bytes,
finite JSON only. Responses are validated; a malformed one raises JevError.

Credentials: only the one key the chosen route needs is read — from the environment or
from ~/.claude/.credentials.master.env — and os.environ is never modified.
"""
from __future__ import annotations

import argparse
import http.client
import json
import math
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PRICE_PER_TOKEN = 0.042 / 1_000_000   # input only; output tokens are free
MAX_CHOICE_OPTIONS = 255
MAX_QUESTIONS = 64
MAX_BYTES = 128_000                   # request body and response body, each
RETRY_STATUSES = {429, 529}           # rate limit / overloaded; nothing else is retried
RETRY_BUDGET_S = 5.0                  # total sleep across all retries of one call
ERROR_BODY_CHARS = 200
PROB_SUM_TOLERANCE = 0.02
# The API rounds every probability to 2 decimals (real 4-option answers sum to 0.99),
# so the sum can drift by up to 0.005 per label; widen the tolerance accordingly.
PROB_ROUNDING_PER_LABEL = 0.005
# Cloudflare in front of api.typesafe.ai has banned the default "Python-urllib/x.y"
# UA with 403 "error code: 1010" — always send an explicit one.
USER_AGENT = "jev-client/1.0 (+claude-code)"
CREDENTIALS_FILE = Path.home() / ".claude" / ".credentials.master.env"

# route name -> (endpoint, key variable, default model)
ROUTES = {
    "typesafe": ("https://api.typesafe.ai/v1/systemone", "TYPESAFE_API_KEY", "jev-latest"),
    # OpenRouter pins a dated build; there is no -latest alias there.
    "openrouter": ("https://openrouter.ai/api/v1/systemone", "OPENROUTER_API_KEY",
                   "typesafe/jev-1.13"),
}
DEFAULT_ROUTE = "typesafe"


class JevError(RuntimeError):
    """JevError(status, body) after an HTTP exchange, JevError(message) otherwise."""

    def __init__(self, status: int | str, body: str | None = None):
        if body is None:
            status, body, msg = 0, str(status), str(status)
        else:
            msg = f"Jev HTTP {status}: {body[:ERROR_BODY_CHARS]}"
        super().__init__(msg)
        self.status, self.body = status, body


class JevInputError(JevError, ValueError):
    """Invalid request, rejected before any key is read or any byte is sent."""


def _require(cond, message: str) -> None:
    if not cond:
        raise JevInputError(message)


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _content(value) -> bool:
    """Instructions, Score levels, Choice descriptions and Noul criteria: the API also takes
    a JSON object or array there (e.g. a level as {"what": ..., "examples": [...]})."""
    return _text(value) or (isinstance(value, (dict, list)) and bool(value))


def _prob(value, high: float = 1.0) -> bool:
    return (type(value) in (int, float) and math.isfinite(value)
            and 0 <= value <= high)


# --- credentials and route --------------------------------------------------

def _key(name: str) -> str:
    """One variable: the environment first, then the credentials file. No side effects."""
    value = (os.environ.get(name) or "").strip()
    if value:
        return value
    try:
        lines = CREDENTIALS_FILE.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return ""
    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[7:].lstrip()
        key, sep, val = line.partition("=")
        if sep and key.strip() == name:
            return val.strip().strip('"').strip("'")
    return ""


def _route_name(route: str | None = None) -> tuple[str, bool]:
    """(route name, chosen explicitly?). The argument wins over JEV_ROUTE."""
    explicit = route or os.environ.get("JEV_ROUTE") or None
    name = (explicit or DEFAULT_ROUTE).strip().lower()
    _require(name in ROUTES, f"unknown route {name!r}; use one of: {', '.join(ROUTES)}")
    return name, bool(explicit)


def _route_key(name: str, explicit: bool) -> str:
    """The key of exactly this route. Never switches routes on its own."""
    var = ROUTES[name][1]
    key = _key(var)
    if not key:
        hint = ("; OpenRouter is used only when chosen explicitly: route='openrouter', "
                "--route openrouter or JEV_ROUTE=openrouter" if not explicit else "")
        raise JevError(f"no {var} in the environment or in {CREDENTIALS_FILE}{hint}")
    return key


# --- question builders ------------------------------------------------------

def noul(instructions, yes=None, no=None) -> dict:
    _require(_content(instructions), "Noul instructions must be non-empty text or a JSON object/array")
    q = {"type": "noul", "instructions": instructions}
    if yes or no:
        q["criteria"] = {k: v for k, v in (("true", yes), ("false", no)) if v}
    return q


def choice(instructions, options) -> dict:
    """options: any iterable of names, or {name: description or None}."""
    _require(_content(instructions), "Choice instructions must be non-empty text or a JSON object/array")
    if not isinstance(options, (dict, str, bytes)) and hasattr(options, "__iter__"):
        options = list(options)  # set, dict_keys, generator
    if isinstance(options, list):
        _require(all(_text(o) for o in options), "Choice labels must be non-empty text")
        _require(len(set(options)) == len(options), "Choice labels must be unique")
        crit = {o: None for o in options}
    else:
        crit = options
    _require(isinstance(crit, dict) and crit,
             "Choice needs at least one option: an iterable of labels or {label: description}")
    if len(crit) > MAX_CHOICE_OPTIONS:
        raise JevInputError(f"Choice takes at most {MAX_CHOICE_OPTIONS} options, got "
                            f"{len(crit)} — use rank(), which splits the roster")
    _require(all(_text(k) for k in crit), "Choice labels must be non-empty text")
    _require(all(v is None or _content(v) for v in crit.values()),
             "Choice descriptions must be None, text or a JSON object/array")
    return {"type": "choice", "instructions": instructions, "criteria": crit}


def score(instructions, levels: list) -> dict:
    _require(_content(instructions), "Score instructions must be non-empty text or a JSON object/array")
    _require(isinstance(levels, (list, tuple)) and 2 <= len(levels) <= 10,
             "Score needs 2–10 levels")
    _require(all(_content(v) for v in levels),
             "Score levels must be non-empty text or JSON objects/arrays")
    return {"type": "score", "instructions": instructions, "criteria": list(levels)}


def validate_questions(questions) -> None:
    """Re-run the builder checks on a questions dict (also covers raw requests)."""
    _require(isinstance(questions, dict) and 1 <= len(questions) <= MAX_QUESTIONS,
             f"Provide 1–{MAX_QUESTIONS} questions")
    for name, q in questions.items():
        _require(_text(name) and isinstance(q, dict), f"Invalid question {name!r}")
        kind, crit = q.get("type"), q.get("criteria")
        if kind == "noul":
            noul(q.get("instructions"))
            _require(crit is None or (isinstance(crit, dict) and crit
                                      and set(crit) <= {"true", "false"}
                                      and all(_content(v) for v in crit.values())),
                     f"Noul criteria of {name!r} must be {{'true'|'false': text or JSON}}")
        elif kind == "choice":
            _require(isinstance(crit, dict), f"Choice criteria of {name!r} must be an object")
            choice(q.get("instructions"), crit)
        elif kind == "score":
            score(q.get("instructions"), crit)
        else:
            raise JevInputError(f"Unsupported question type {kind!r} in {name!r}")


def check_answers(out, questions: dict) -> dict:
    """Validate the response body against the questions; fills a missing Score legend."""
    answers = out.get("answers") if isinstance(out, dict) else None
    if not isinstance(answers, dict):
        raise JevError("malformed response: no answers object")
    if set(answers) != set(questions):
        raise JevError(f"malformed response: answered {sorted(answers)}, "
                       f"asked {sorted(questions)}")
    for name, q in questions.items():
        a, kind = answers[name], q["type"]
        if not isinstance(a, dict) or a.get("type", kind) != kind:
            raise JevError(f"malformed response: answer {name!r} is not a {kind}")
        if kind == "noul":
            if not _prob(a.get("noul")):
                raise JevError(f"malformed response: noul of {name!r} is not in [0, 1]")
            continue
        if kind == "choice":
            labels = set(q["criteria"])
        else:
            labels = {str(i) for i in range(len(q["criteria"]))}
        probs = a.get("probabilities")
        if not (isinstance(probs, dict) and probs and set(probs) <= labels
                and all(_prob(v) for v in probs.values())):
            raise JevError(f"malformed response: probabilities of {name!r}")
        tolerance = max(PROB_SUM_TOLERANCE, PROB_ROUNDING_PER_LABEL * len(labels))
        if abs(sum(probs.values()) - 1) > tolerance:
            raise JevError(f"malformed response: probabilities of {name!r} sum to "
                           f"{sum(probs.values()):.3f}")
        if not _prob(a.get("confidence")):
            raise JevError(f"malformed response: confidence of {name!r}")
        if kind == "choice":
            picked = a.get("choice")
            if not isinstance(picked, str) or picked not in labels:
                raise JevError(f"malformed response: choice of {name!r} is not an option")
        else:
            if not _prob(a.get("score"), len(labels) - 1):
                raise JevError(f"malformed response: score of {name!r} is out of range")
            if not isinstance(a.get("legend"), dict):
                a["legend"] = {str(i): lvl for i, lvl in enumerate(q["criteria"])}
    return out


# --- transport --------------------------------------------------------------

class NoRedirect(urllib.request.HTTPRedirectHandler):
    """A redirect would carry the Authorization header to another host; refuse it."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _opener():
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


def _error_text(e: urllib.error.HTTPError, key: str) -> str:
    try:
        text = e.read(4096).decode("utf-8", "replace")
    except Exception:
        text = ""
    finally:
        e.close()
    return (text.replace(key, "***") if key else text).strip() or (e.reason or "")


def system_one(state, questions: dict, model: str | None = None,
               timeout: float = 30, retries: int = 1, *, route: str | None = None) -> dict:
    """One call. Returns the API body plus `_seconds`, `_cost_usd`, `_route`.

    Retries only 429/529, at most `retries` times and 5 s of waiting in total: a
    timed-out or failed request may already have been billed.
    """
    validate_questions(questions)
    name, explicit = _route_name(route)
    url, _, default_model = ROUTES[name]
    try:
        body = json.dumps({"state": state,
                           "model": model or os.environ.get("JEV_MODEL") or default_model,
                           "questions": questions},
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as e:
        raise JevInputError(f"state and questions must be finite JSON: {e}") from None
    _require(len(body) <= MAX_BYTES, f"request is {len(body)} bytes, over the {MAX_BYTES} "
                                     "byte limit — shorten the state or shortlist the options")
    key = _route_key(name, explicit)
    opener, budget, delay = _opener(), RETRY_BUDGET_S, 1.0
    for attempt in range(max(0, retries) + 1):
        req = urllib.request.Request(url, data=body, method="POST", headers={
            "Authorization": f"Bearer {key}", "Content-Type": "application/json",
            "User-Agent": USER_AGENT})
        t0 = time.perf_counter()
        try:
            with opener.open(req, timeout=timeout) as r:
                raw = r.read(MAX_BYTES + 1)
            break
        except urllib.error.HTTPError as e:
            text = _error_text(e, key)
            if e.code in RETRY_STATUSES and attempt < retries and budget > 0:
                try:
                    wait = float((e.headers or {}).get("retry-after") or delay)
                except (TypeError, ValueError):
                    wait = delay
                if not math.isfinite(wait):  # "Retry-After: nan" would make time.sleep raise
                    wait = delay
                wait = min(max(wait, 0.0), budget)
                time.sleep(wait)
                budget -= wait
                delay *= 2
                continue
            raise JevError(e.code, text) from None
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as e:
            reason = getattr(e, "reason", e)
            raise JevError(f"network ({name}): {type(e).__name__}: {reason}") from None
    if len(raw) > MAX_BYTES:
        raise JevError(f"response over the {MAX_BYTES} byte limit")
    try:
        out = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, ValueError):
        raise JevError(f"malformed response: not JSON ({raw[:80]!r})") from None
    check_answers(out, questions)
    usage = out.get("usage") if isinstance(out.get("usage"), dict) else {}
    out["_seconds"] = round(time.perf_counter() - t0, 3)
    out["_cost_usd"] = usage.get("cost", (usage.get("input_tokens") or 0) * PRICE_PER_TOKEN)
    out["_route"] = name
    return out


# --- one-liners -------------------------------------------------------------

def ask(question: str, state, yes: str | None = None, no: str | None = None, *,
        route: str | None = None) -> float:
    """Probability that the answer is yes."""
    return system_one(state, {"q": noul(question, yes, no)}, route=route)["answers"]["q"]["noul"]


def pick(question: str, options, state, *, route: str | None = None) -> tuple[str, dict, float]:
    a = system_one(state, {"q": choice(question, options)}, route=route)["answers"]["q"]
    return a["choice"], a["probabilities"], a["confidence"]


def rank(query: str, candidates: dict, instructions: str | None = None,
         state_extra: dict | None = None, *, route: str | None = None) -> list[tuple[str, float]]:
    """Order candidates {name: description} by how well each answers `query`.

    Uses one Choice per chunk of ≤255 options; with several chunks the winners of each
    are ranked again in a final round, so the probabilities stay comparable.
    """
    _require(isinstance(candidates, dict) and candidates, "rank() needs candidates")
    instr = instructions or ("Which of these options best answers the request? "
                             "Read what each option describes, not just its name.")
    state = {"request": query, **(state_extra or {})}
    names = list(candidates)
    chunks = [names[i:i + MAX_CHOICE_OPTIONS] for i in range(0, len(names), MAX_CHOICE_OPTIONS)]
    # Build every chunk's question first so a bad label fails before the first paid call.
    qs = [choice(instr, {n: candidates[n] for n in chunk}) for chunk in chunks]

    def one(q):
        a = system_one(state, {"q": q}, route=route)
        return sorted(a["answers"]["q"]["probabilities"].items(), key=lambda kv: -kv[1])

    if len(qs) == 1:
        return one(qs[0])
    finalists = [n for q in qs for n, _ in one(q)[:10]][:MAX_CHOICE_OPTIONS]
    return one(choice(instr, {n: candidates[n] for n in finalists}))


# --- CLI --------------------------------------------------------------------

def _read_state(a) -> object:
    if a.state_file:
        text = Path(a.state_file).read_text(encoding="utf-8")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    if a.state == "-":
        return sys.stdin.read()
    if a.state is None:
        raise SystemExit("нужен --state «текст» (или --state - для stdin, или --state-file)")
    return a.state


def _meta(out: dict) -> str:
    u = out.get("usage") or {}
    return (f"[{out.get('model')} · {out['_route']} · {out['_seconds']} с · "
            f"{u.get('input_tokens')} ток · ${out['_cost_usd']:.6f}]")


def main() -> int:
    reconf = getattr(sys.stdout, "reconfigure", None)
    if reconf:
        reconf(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    route_help = "typesafe (по умолчанию, или JEV_ROUTE) | openrouter — только явно"
    ap.add_argument("--route", choices=list(ROUTES), default=None, help=route_help)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def route_arg(p):
        # SUPPRESS keeps a subcommand from overwriting a --route given before it.
        p.add_argument("--route", choices=list(ROUTES), default=argparse.SUPPRESS,
                       help=route_help)

    def state_args(p):
        p.add_argument("--state", help="текст состояния, или - для stdin")
        p.add_argument("--state-file", help="файл: JSON (станет объектом) или текст")
        p.add_argument("--json", action="store_true", help="сырой ответ API")
        route_arg(p)

    p = sub.add_parser("ask", help="да/нет → вероятность «да» (Noul)")
    p.add_argument("question"); p.add_argument("--yes"); p.add_argument("--no")
    state_args(p)
    p = sub.add_parser("choose", help="один из вариантов (Choice)")
    p.add_argument("question"); p.add_argument("options", nargs="+")
    state_args(p)
    p = sub.add_parser("score", help="уровень по шкале (Score), уровни от низшего к высшему")
    p.add_argument("question"); p.add_argument("levels", nargs="+")
    state_args(p)
    p = sub.add_parser("rank", help="упорядочить кандидатов {имя: описание} под запрос")
    p.add_argument("query"); p.add_argument("--candidates", required=True)
    p.add_argument("-n", type=int, default=10)
    route_arg(p)
    p = sub.add_parser("raw", help="полное тело запроса из JSON-файла")
    p.add_argument("file")
    route_arg(p)
    p = sub.add_parser("selftest", help="живой вызов: RU и EN, три типа вопросов")
    route_arg(p)

    a = ap.parse_args()
    r = a.route
    try:
        if a.cmd == "ask":
            out = system_one(_read_state(a), {"q": noul(a.question, a.yes, a.no)}, route=r)
            if a.json: print(json.dumps(out, ensure_ascii=False, indent=1)); return 0
            print(f"да: {out['answers']['q']['noul']:.3f}   {_meta(out)}")
        elif a.cmd == "choose":
            out = system_one(_read_state(a), {"q": choice(a.question, a.options)}, route=r)
            if a.json: print(json.dumps(out, ensure_ascii=False, indent=1)); return 0
            ans = out["answers"]["q"]
            print(f"выбор: {ans['choice']}   уверенность {ans['confidence']:.2f}   {_meta(out)}")
            for k, v in sorted(ans["probabilities"].items(), key=lambda kv: -kv[1]):
                print(f"  {v:.3f}  {k}")
        elif a.cmd == "score":
            out = system_one(_read_state(a), {"q": score(a.question, a.levels)}, route=r)
            if a.json: print(json.dumps(out, ensure_ascii=False, indent=1)); return 0
            ans = out["answers"]["q"]
            print(f"оценка: {ans['score']:.2f} из 0…{len(a.levels) - 1}   "
                  f"уверенность {ans['confidence']:.2f}   {_meta(out)}")
            for k, v in ans["probabilities"].items():
                print(f"  {v:.3f}  {k}: {ans['legend'].get(k, '')}")
        elif a.cmd == "rank":
            cands = json.loads(Path(a.candidates).read_text(encoding="utf-8"))
            for name, prob in rank(a.query, cands, route=r)[:a.n]:
                print(f"  {prob:.3f}  {name}")
        elif a.cmd == "raw":
            req = json.loads(Path(a.file).read_text(encoding="utf-8"))
            out = system_one(req["state"], req["questions"], req.get("model"), route=r)
            print(json.dumps(out, ensure_ascii=False, indent=1))
        elif a.cmd == "selftest":
            for lang, state, q in [
                ("RU", "Помогите! Выплаты не проходят уже третий день.", "Сообщение срочное?"),
                ("EN", "Help! My payouts have been failing for 3 days.", "Is this urgent?"),
            ]:
                out = system_one(state, {
                    "urgent": noul(q),
                    "team": choice("Which team should handle this?",
                                   {"billing": "payments, invoices, refunds",
                                    "technical": "bugs, outages, integrations",
                                    "sales": "pricing, upgrades, new accounts"}),
                    "anger": score("How frustrated is the customer?",
                                   ["calm", "frustrated", "very angry"]),
                }, route=r)
                ans = out["answers"]
                print(f"{lang}: срочно {ans['urgent']['noul']:.2f} · отдел {ans['team']['choice']} "
                      f"({ans['team']['confidence']:.2f}) · злость {ans['anger']['score']:.2f}   "
                      f"{_meta(out)}")
    except JevError as e:
        print(f"ОШИБКА: {e}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
