#!/usr/bin/env python3
"""Two patterns on top of jev_client.py: a publication gate and a readable vector.

Jev answers typed questions with calibrated probabilities (see jev_client.py). The decision stays in
code; Jev only judges.

GATE. A battery of questions about a text; each answer becomes a hazard probability, and thresholds
that live in code turn hazards into an action:

    hazard >= block_at  and the check may block            -> block
    hazard >= review_at (or a soft check above block_at)   -> review   (a human looks)
    otherwise                                              -> pass
    precedence block > review > pass

Every way of not getting a trustworthy answer ends in review, never pass: Jev down, an answer that does
not validate or that no probability distribution can explain, a corrupt cache row, an empty or oversized
text, an exception inside a check (any Exception; KeyboardInterrupt and SystemExit are not caught).
Deterministic code checks (regexes) run first; a firing blocking check returns block with no API call, so
a text that looks like a secret never goes to the API. A serious violation is its own check with its own
severity, not a term in a weighted sum. The gate is advisory: it never publishes and never replaces the
owner's approval. The text goes to the Jev API of the chosen route (same as jev_client).

The API reports two decimals and a number may be off by almost a cent, so a hazard is the range the reported
numbers allow (each number +-0.01, an option the answer leaves out is unknown, all options sum to 1), not a
point. The action reads the range pessimistically: pass needs even the high end below review_at, block needs
even the low end at or above block_at, anything in between is review. The rounding rule is an assumption
backed by measurement, not by a vendor promise (see ROUND).

READABLE VECTOR. Every answer is one coordinate: a probability distribution over the options of one
question. A text (or a query, asked the same questions) becomes a vector you can read. The distance is
per question (total variation for yes/no and choice, normalized earth mover for ordered scores), so a
mismatch is explained by naming the question that disagrees. Adding an axis = adding a question.
Profiles refuse to be compared across different or unknown models and different axis sets.

    python jev_patterns.py gate --battery battery.json --text "..."        # exit 0 pass / 10 review / 11 block
    python jev_patterns.py calibrate --battery battery.json --examples examples.json
    python jev_patterns.py profile --axes axes.json --text "..."
    python jev_patterns.py rank --axes axes.json --query "..." --docs docs.json [--mode want|like] [--explain]
    python jev_patterns.py selftest                                         # offline, no API

Privacy: the cache keeps, under a keyed hash of (state, question, route, requested model), the validated
answer (type, probabilities, option labels, the chosen option or score, confidence), the build name that
answered and the time; the audit log keeps a keyed hash of the text and of the context, the length, the
battery fingerprint, the action and the hazard ranges. The key lives in a local file (JEV_PATTERNS_KEY,
default ~/.claude/cache/jev_patterns.key), so a stolen database or log alone cannot be used to test guesses
about short texts (the key file next to it can). This module never writes the judged text itself; option
labels and check names come from the battery you wrote, and a text that is shaped like a build name could
come back as the model name. A reason carries a status, a fixed phrase or a class name, a code check only
the position of its match (a call of ask_battery, profile or calibrate from Python re-raises the client's
own exceptions, whose text may quote the server). The cache TTL limits reuse, not retention:
AnswerCache.purge(0) deletes every row (SQLite overwrites the freed pages); backups and copies of the files
are not touched. The context goes to the API as it is: code checks look at the text only.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import hmac
import json
import math
import os
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Callable

try:
    import jev_client as jc
except ImportError:  # started from another directory
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import jev_client as jc

PASS, REVIEW, BLOCK = "pass", "review", "block"
_ORDER = {PASS: 0, REVIEW: 1, BLOCK: 2}
EXIT_CODES = {PASS: 0, REVIEW: 10, BLOCK: 11}
REVIEW_AT = 0.35      # vendor guardrails cookbook example (written for jev-1.12): a human looks from here ...
BLOCK_AT = 0.70       # ... and its strict policy acts from here (0.85 for the permissive one). The vendor
                      # says to tune both on labelled traffic of your own: see `calibrate`.
EPS = 1e-9            # float noise: 1 - 0.8 must still reach a 0.2 threshold
MIN_MASS = 0.5        # a Choice/Score answer covering less probability than this cannot be judged
POLICY = "range-2"    # the rule that turns an answer into an action; part of the audit fingerprint
                      # (range-1: +-0.005 per number; range-2: +-0.01 and the residual-to-one-option cases)
MAX_TEXT_CHARS = 100_000
DEFAULT_TTL_DAYS = 30
DEFAULT_DB = Path.home() / ".claude" / "cache" / "jev_patterns.sqlite"
DEFAULT_KEY = Path.home() / ".claude" / "cache" / "jev_patterns.key"
UNKNOWN_MODEL = "unknown"
# The API reports every probability with two decimals, and a reported number may be off by almost a cent, not by
# half a cent. Measured on the cached answers of 03.10.2026 (8283 Choice/Score answers): the numbers sum to
# exactly 1 in 98.6% and never to more than 1, and values such as 0.18000000000000002 (0.17 + 0.01) suggest that an
# option was nudged by a cent to make the total come out right. The vendor pages promise no rounding rule at all
# and the raw values are not available, so this is a reading of the evidence, not a known rule: see hazard_range
# for the case where the cents that rounding loses are handed to one option.
ROUND = 0.01
FEAS_EPS = 1e-12      # float noise when testing whether any distribution fits an answer (EPS is for thresholds)
# A build name such as jev-1.13.0 or typesafe/jev-1.13, short and of one narrow shape. An alias (jev-latest) or
# anything else counts as unknown, because it does not say which build answered. The shape is a barrier, not
# a proof: a text that itself looks like a build name would pass it, and a server could repeat such a text.
_MODEL_RE = re.compile(r"(?:[a-z0-9][a-z0-9_-]{0,15}/)?jev-[0-9]{1,3}(?:\.[0-9]{1,3}){0,3}(?:-[a-z0-9]{1,12})?",
                       re.IGNORECASE)
_NOTE_RE = re.compile(r"match at [0-9]{1,9}-[0-9]{1,9}")     # the only note of a code check that is kept
_CTRL = re.compile(r"[\x00-\x1f\x7f]")
_MAX_CLOCK_SKEW = 3600.0          # a cached row stamped further in the future than this is not trusted
_KEYS: dict = {}
_KEY_LOCK = threading.Lock()
_NO_CONTEXT, _UNAVAILABLE = object(), object()     # audit markers: no context was given / it could not be copied


class ProfileMismatch(ValueError):
    """Two profiles come from different or unknown models, or other axis sets: the distance would mean nothing."""


class GateError(jc.JevInputError):
    """A failure with a fixed message that holds nothing from the judged text: safe to show and to log."""


# --- keys, answer cache and batteries --------------------------------------------

def _read_key(path: Path):
    try:
        key = bytes.fromhex(path.read_text(encoding="ascii").strip())
    except (OSError, ValueError):
        return None
    return key if len(key) >= 16 else None


def _machine_key() -> bytes:
    """A local random key for hashing texts, created once and shared by every process.

    The file is published atomically (written under a temporary name, then hard-linked into place): two
    first runs never leave two different keys behind and a half-written file is never read. A file that is
    present but unusable is moved aside, not overwritten. When nothing can be written this run still works
    with a key kept in memory; its hashes simply do not match those of other runs."""
    path = Path(os.environ.get("JEV_PATTERNS_KEY") or DEFAULT_KEY)
    with _KEY_LOCK:
        if path in _KEYS:
            return _KEYS[path]
        key = _read_key(path)
        if key is None:
            key = os.urandom(32)
            tmp = None
            try:
                if path.is_dir() or path.is_symlink():  # not ours to move or replace: keep the key in memory
                    raise OSError("the key path is not a regular file")
                path.parent.mkdir(parents=True, exist_ok=True)
                tmp = path.with_name(f"{path.name}.{os.getpid()}.{os.urandom(4).hex()}.tmp")
                fd = os.open(str(tmp), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
                with os.fdopen(fd, "w", encoding="ascii") as f:
                    f.write(key.hex())
                if path.exists() and _read_key(path) is None:
                    # A damaged key file is kept aside. Two processes recovering at the very same moment can
                    # still end with different keys (the cost is repeated requests, never a wrong verdict).
                    os.replace(path, path.with_name(path.name + ".unusable"))
                try:
                    os.link(tmp, path)
                except FileExistsError:                 # another process published first: use its key
                    key = _read_key(path) or key
                except OSError:                         # a file system without hard links
                    if path.exists():
                        key = _read_key(path) or key
                    else:
                        os.replace(tmp, path)           # the temporary file is complete: nobody sees half of it
            except OSError:
                pass
            finally:
                if tmp is not None:
                    try:
                        os.unlink(tmp)
                    except OSError:
                        pass
        _KEYS[path] = key
        return key


def _check_secret(secret) -> bytes:
    jc._require(isinstance(secret, (bytes, bytearray)), "the hashing key must be bytes")
    key = memoryview(secret).tobytes()    # the real content, whatever len() and __bytes__ claim
    jc._require(len(key) >= 16, "the hashing key must be at least 16 bytes")
    return key


def _require_ttl(ttl_days) -> None:
    jc._require(type(ttl_days) in (int, float) and ttl_days == ttl_days and ttl_days >= 0,
                "ttl_days must be a number >= 0 (0 switches the cache off, inf never expires)")


def _text_digest(text: str, secret: bytes | None = None) -> str:
    key = _check_secret(secret) if secret is not None else _machine_key()
    return hmac.new(key, text.encode("utf-8", "surrogatepass"), hashlib.sha256).hexdigest()


def _model_name(value) -> str:
    """The model that answered, or 'unknown'. Never free text: it ends up in logs and caches."""
    return value if isinstance(value, str) and _MODEL_RE.fullmatch(value) else UNKNOWN_MODEL


# What the client says without a number or a name, by the start of the message. Anything else is reduced to
# the class name: the client's other messages may quote the server's reply, and a server may repeat the text.
_CLIENT_PHRASES = (("malformed response", "malformed response"), ("network (", "network error"),
                   ("response over the", "response too large"), ("no TYPESAFE_API_KEY", "no TYPESAFE_API_KEY"),
                   ("no OPENROUTER_API_KEY", "no OPENROUTER_API_KEY"))


# The messages this module itself raises: fixed words, at most a number. A GateError with any other message
# (a hostile object can raise one with the text in it) is reduced to its class name.
_GATE_MESSAGES = tuple(re.compile(p) for p in (
    r"empty text", r"text is over [0-9]+ characters", r"request is [0-9]+ bytes, over the [0-9]+ byte limit",
    r"state and questions must be finite JSON", r"the answer covers too little probability to judge",
    r"the answer is not a probability distribution", r"a score check needs an at_least level",
    r"hazard is not a probability", r"the battery changed after the gate was built",
    r"the axes changed after they were built"))


def _class_name(e: BaseException) -> str:
    return re.sub(r"[^A-Za-z0-9_.]", "?", type(e).__name__)[:40]


def _safe_error(e: BaseException) -> str:
    """A short reason that cannot contain the judged text: a fixed phrase, an HTTP status or a class name."""
    if isinstance(e, GateError):
        try:
            msg = str(e)
        except Exception:                      # an exception whose __str__ fails is still just a class name
            msg = ""
        s = msg if any(rx.fullmatch(msg) for rx in _GATE_MESSAGES) else _class_name(e)
    elif isinstance(e, jc.JevError):
        status = getattr(e, "status", 0)
        if type(status) is int and 100 <= status <= 599:
            s = f"HTTP {status}"
        else:
            msg = str(e)
            s = next((label for prefix, label in _CLIENT_PHRASES if msg.startswith(prefix)), _class_name(e))
    else:
        s = _class_name(e)
    return _CTRL.sub(" ", s)[:120]


def _clean_answer(question: dict, answer) -> dict:
    """Validate an answer exactly as the client does and keep only the fields the patterns use.
    Raises JevError for anything malformed, so a corrupt cache row or a strange API reply becomes a miss
    or a degraded review, never a silent pass."""
    jc.check_answers({"answers": {"q": answer}}, {"q": question})
    kind = question["type"]
    clean: dict = {"type": kind}
    if kind == "noul":
        clean["noul"] = float(answer["noul"])
        if jc._prob(answer.get("confidence")):
            clean["confidence"] = float(answer["confidence"])
        return clean
    probs = {str(k): float(v) for k, v in answer["probabilities"].items()}
    mass = math.fsum(probs.values())
    if not math.isfinite(mass) or mass < MIN_MASS:
        raise jc.JevError("the answer covers too little probability to judge")
    clean["probabilities"] = probs
    clean["confidence"] = float(answer["confidence"])
    clean[kind] = answer["choice"] if kind == "choice" else float(answer["score"])
    return clean


class AnswerCache:
    """Per-question answers keyed by a keyed hash of (state, question, route, requested model).

    The state text is never stored. Each answer keeps the model that actually produced it, so a vector
    can refuse to mix builds behind an alias such as jev-latest. A cache failure (locked, read-only or
    corrupt database) costs a repeated request, never a wrong verdict and never a lost paid answer.
    """

    def __init__(self, path=None, secret: bytes | None = None):
        self.path = Path(path or os.environ.get("JEV_PATTERNS_DB") or DEFAULT_DB)
        self.secret = _check_secret(secret) if secret is not None else _machine_key()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(str(self.path), check_same_thread=False, timeout=10)
        self._db.execute("PRAGMA secure_delete = ON")      # deleted answers are overwritten, not just unlinked
        self._db.execute("CREATE TABLE IF NOT EXISTS answers "
                         "(key TEXT PRIMARY KEY, model TEXT, answer TEXT, created REAL)")
        self._db.commit()

    def key(self, state, question, route, model) -> str:
        # Insertion order is part of the identity: the order of Choice options changes both the answer
        # (vendor jaggedness) and the layout of a vector, so keys are not sorted.
        blob = json.dumps({"s": state, "q": question, "r": route, "m": model},
                          ensure_ascii=False, allow_nan=False, separators=(",", ":"))
        return hmac.new(self.secret, b"jev-cache-v2\0" + blob.encode("utf-8", "surrogatepass"),
                        hashlib.sha256).hexdigest()

    def get(self, key, ttl_days):
        """(model, answer) of a fresh row, else None. A row is fresh when its stamp is a real number, not in
        the future and not older than ttl_days; a ttl that is NaN, negative, zero or not a number makes
        nothing fresh (zero means the cache is off)."""
        try:
            if not ttl_days >= 0 or ttl_days == 0:
                return None
            with self._lock:
                row = self._db.execute("SELECT model, answer, created FROM answers WHERE key=?",
                                       (key,)).fetchone()
            if not row:
                return None
            created = row[2]
            if type(created) not in (int, float) or not math.isfinite(created):
                return None
            age = time.time() - created
            if age < -_MAX_CLOCK_SKEW or age > ttl_days * 86400:
                return None
            return row[0], json.loads(row[1])
        except (sqlite3.Error, ValueError, TypeError):
            return None

    def put(self, key, model, answer):
        with self._lock:
            try:
                self._db.execute("INSERT OR REPLACE INTO answers VALUES (?,?,?,?)",
                                 (key, model, json.dumps(answer, ensure_ascii=False), time.time()))
                self._db.commit()
            except (sqlite3.Error, ValueError, TypeError):
                try:
                    self._db.rollback()
                except sqlite3.Error:
                    pass

    def purge(self, older_than_days: float) -> int:
        """Delete rows older than the given age; 0 deletes every row whatever its stamp. For a positive age the
        rows whose stamp is missing, unreadable or in the future go as well. Returns how many were removed.
        SQLite overwrites the freed pages (secure_delete); backups and copies of the file are not touched."""
        _require_ttl(older_than_days)
        with self._lock:
            if older_than_days == 0:
                cur = self._db.execute("DELETE FROM answers")
            else:
                now = time.time()
                try:
                    cutoff = now - float(older_than_days) * 86400
                except OverflowError:               # an age too large for a float: nothing is old enough
                    cutoff = float("-inf")
                cur = self._db.execute(
                    "DELETE FROM answers WHERE created IS NULL OR typeof(created) NOT IN ('real', 'integer') "
                    "OR created <= ? OR created > ?", (cutoff, now + _MAX_CLOCK_SKEW))
            self._db.commit()
            return cur.rowcount

    def close(self):
        with self._lock:
            self._db.close()


@dataclass
class Meta:
    models: set = field(default_factory=set)
    cost_usd: float = 0.0
    seconds: float = 0.0
    cached: int = 0
    requests: int = 0

    @property
    def model(self):
        return "|".join(sorted(self.models)) if self.models else None

    def add(self, other: "Meta"):
        self.models |= other.models
        self.cost_usd += other.cost_usd
        self.seconds += other.seconds
        self.cached += other.cached
        self.requests += other.requests


def _chunks(items: dict, size: int):
    keys = list(items)
    return [{k: items[k] for k in keys[i:i + size]} for i in range(0, len(keys), size)]


def _number(value) -> float:
    return float(value) if type(value) in (int, float) and math.isfinite(value) else 0.0


def _require_json(state, questions: dict) -> None:
    """State and questions must be finite JSON: checked first, so the cache keys cannot trip over them."""
    try:
        json.dumps({"state": state, "questions": questions}, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError):
        raise GateError("state and questions must be finite JSON") from None


def _preflight(state, requested_model, chunk: dict) -> None:
    """Refuse a request the client would refuse, before any request of the battery is paid for."""
    try:
        body = json.dumps({"state": state, "model": requested_model, "questions": chunk},
                          ensure_ascii=False, allow_nan=False).encode("utf-8")
    except (TypeError, ValueError):
        raise GateError("state and questions must be finite JSON") from None
    if len(body) > jc.MAX_BYTES:
        raise GateError(f"request is {len(body)} bytes, over the {jc.MAX_BYTES} byte limit")


def ask_battery(state, questions: dict, *, route=None, model=None, cache=None,
                ttl_days=DEFAULT_TTL_DAYS, timeout=30):
    """Ask any number of questions about one state; returns ({name: answer}, Meta).

    Splits into requests of at most 64 questions, answers what the cache already holds without a call
    (a cached row that does not validate counts as a miss), checks structure and size of every request
    before the first paid one. Answers are validated like the client does and stripped to the fields the
    patterns use. ttl_days=0 switches the cache off, reads and writes; NaN or a negative value is refused.
    State and questions are copied first, so a caller changing them while the call runs cannot make a
    cached answer belong to another question.
    """
    _require_ttl(ttl_days)
    route_name = jc._route_name(route)[0]
    requested = model or os.environ.get("JEV_MODEL") or jc.ROUTES[route_name][2]
    for chunk in _chunks(questions, jc.MAX_QUESTIONS):
        jc.validate_questions(chunk)
    _require_json(state, questions)
    state, questions = copy.deepcopy(state), copy.deepcopy(questions)
    live = cache if ttl_days != 0 else None
    keys = {name: live.key(state, q, route_name, requested) for name, q in questions.items()} if live else {}
    answers, todo, meta = {}, {}, Meta()
    for name, q in questions.items():
        hit = live.get(keys[name], ttl_days) if live is not None else None
        if hit:
            try:
                answers[name] = _clean_answer(q, hit[1])
                meta.models.add(_model_name(hit[0]))
                meta.cached += 1
                continue
            except (jc.JevError, KeyError, TypeError, ValueError):
                pass
        todo[name] = q
    for chunk in _chunks(todo, jc.MAX_QUESTIONS):
        _preflight(state, requested, chunk)
    for chunk in _chunks(todo, jc.MAX_QUESTIONS):
        # the very route and model the cache keys were made with, not arguments the environment could change
        out = jc.system_one(state, chunk, model=requested, timeout=timeout, route=route_name)
        resolved = _model_name(out.get("model"))
        meta.models.add(resolved)
        meta.requests += 1
        meta.cost_usd += _number(out.get("_cost_usd"))
        meta.seconds += _number(out.get("_seconds"))
        for name, q in chunk.items():
            answers[name] = _clean_answer(q, out["answers"][name])
            if live is not None:
                live.put(keys[name], resolved, answers[name])
    return answers, meta


# --- gate ---------------------------------------------------------------------

@dataclass(frozen=True)
class Check:
    """One question about a text and how its answer becomes a hazard probability."""
    name: str
    question: dict
    violation: str = "yes"           # noul: which answer is a violation, "yes" or "no"
    labels: tuple = ()               # choice: labels that count as a violation
    at_least: int | None = None      # score: level index from which it counts as a violation
    severity: str = REVIEW           # the strongest action this check may cause: block | review
    review_at: float | None = None   # None -> the gate default
    block_at: float | None = None


def _check_args(name, severity, review_at, block_at):
    jc._require(isinstance(name, str) and name.strip(), "a check needs a name")
    jc._require(severity in (BLOCK, REVIEW), f"severity of {name!r} must be 'block' or 'review'")
    for v in (review_at, block_at):
        jc._require(v is None or jc._prob(v), f"thresholds of {name!r} must be in [0, 1]")
    if review_at is not None and block_at is not None:
        jc._require(review_at <= block_at, f"review_at of {name!r} is above block_at")


def noul_check(name, instructions, *, violation="yes", severity=REVIEW, yes=None, no=None,
               review_at=None, block_at=None) -> Check:
    _check_args(name, severity, review_at, block_at)
    jc._require(violation in ("yes", "no"), f"violation of {name!r} must be 'yes' or 'no'")
    return Check(name, jc.noul(instructions, yes, no), violation=violation, severity=severity,
                 review_at=review_at, block_at=block_at)


def choice_check(name, instructions, options, labels, *, severity=REVIEW,
                 review_at=None, block_at=None) -> Check:
    _check_args(name, severity, review_at, block_at)
    q = jc.choice(instructions, options)
    labels = tuple(labels)
    jc._require(labels and len(set(labels)) == len(labels) and set(labels) <= set(q["criteria"]),
                f"violation labels of {name!r} must be a non-empty, duplicate-free subset of the options")
    return Check(name, q, labels=labels, severity=severity, review_at=review_at, block_at=block_at)


def score_check(name, instructions, levels, at_least, *, severity=REVIEW,
                review_at=None, block_at=None) -> Check:
    _check_args(name, severity, review_at, block_at)
    q = jc.score(instructions, levels)
    jc._require(type(at_least) is int and 0 <= at_least < len(levels),
                f"at_least of {name!r} must be a level index")
    return Check(name, q, at_least=at_least, severity=severity, review_at=review_at, block_at=block_at)


def _validate_check(c: Check, review_at: float, block_at: float) -> None:
    """The full check a Gate runs on every Check, including ones built by hand and the thresholds that
    actually apply (a local override combined with a gate default)."""
    ra = review_at if c.review_at is None else c.review_at
    ba = block_at if c.block_at is None else c.block_at
    _check_args(c.name, c.severity, c.review_at, c.block_at)
    jc._require(jc._prob(ra) and jc._prob(ba) and ra <= ba,
                f"thresholds of {c.name!r} must satisfy 0 <= review_at <= block_at <= 1 (got {ra}, {ba})")
    kind = c.question.get("type") if isinstance(c.question, dict) else None
    if kind == "noul":
        jc._require(c.violation in ("yes", "no"), f"violation of {c.name!r} must be 'yes' or 'no'")
    elif kind == "choice":
        crit = c.question.get("criteria") or {}
        jc._require(bool(c.labels) and len(set(c.labels)) == len(c.labels) and set(c.labels) <= set(crit),
                    f"violation labels of {c.name!r} must be a non-empty, duplicate-free subset of the options")
    elif kind == "score":
        n = len(c.question.get("criteria") or [])
        jc._require(type(c.at_least) is int and 0 <= c.at_least < n,
                    f"at_least of {c.name!r} must be a level index")
    else:
        raise jc.JevInputError(f"check {c.name!r} has an unsupported question type {kind!r}")


@dataclass(frozen=True)
class CodeCheck:
    """A deterministic test: returns a note when it fires (any value but None, even an empty string), None
    when it does not. Only a note of the form "match at 3-9" is kept in reports; any other note is replaced by
    "matched", because a note may carry the matched text, which may be a secret. `ident` names the version of
    the test for the audit fingerprint (regex_check fills it from the pattern); set it for your own functions."""
    name: str
    test: Callable[[str], "str | None"]
    severity: str = BLOCK
    ident: str = ""


def regex_check(name, pattern, *, flags=re.IGNORECASE, severity=BLOCK) -> CodeCheck:
    """A regex test. The note says where the match is, never what it is: matched text may be a secret.
    Python's re has no timeout: keep patterns simple (see docs on pathological backtracking)."""
    jc._require(severity in (BLOCK, REVIEW), f"severity of {name!r} must be 'block' or 'review'")
    rx = re.compile(pattern, flags)

    def test(text):
        m = rx.search(text)
        return f"match at {m.start()}-{m.end()}" if m else None
    ident = hashlib.sha256(f"{int(flags)}\0{pattern}".encode("utf-8")).hexdigest()[:10]
    return CodeCheck(name, test, severity, ident)


def _hazard_cases(check: Check, answer: dict) -> list:
    """The (low, high) ranges of the violation probability that one validated answer allows, one per
    assumption about the rounding. The first is the plain reading; the others, for Choice and Score with more
    than two options, let any one reported option be the one that absorbed the rounding residual.
    Raises GateError for an answer that no distribution can explain or that carries less than MIN_MASS."""
    kind = check.question["type"]
    if kind == "noul":
        p = float(answer["noul"])
        lo, hi = max(0.0, p - ROUND), min(1.0, p + ROUND)
        return [(lo, hi) if check.violation == "yes" else (1.0 - hi, 1.0 - lo)]
    probs = {str(k): float(v) for k, v in answer["probabilities"].items()}
    mass = math.fsum(probs.values())
    if not math.isfinite(mass) or mass < MIN_MASS:
        raise GateError("the answer covers too little probability to judge")
    if kind == "choice":
        options, bad = list(check.question["criteria"]), set(check.labels)
    else:
        if check.at_least is None:
            raise GateError("a score check needs an at_least level")
        options = [str(i) for i in range(len(check.question["criteria"]))]
        bad = {str(i) for i in range(check.at_least, len(options))}
    base = {}
    for option in options:
        if option in probs:
            base[option] = (max(0.0, probs[option] - ROUND), min(1.0, probs[option] + ROUND))
        else:
            base[option] = (0.0, 1.0)
    lo_bad = math.fsum(base[o][0] for o in options if o in bad)
    hi_bad = math.fsum(base[o][1] for o in options if o in bad)
    lo_good = math.fsum(base[o][0] for o in options if o not in bad)
    hi_good = math.fsum(base[o][1] for o in options if o not in bad)

    def solve(lb, hb, lg, hg):
        if lb + lg > 1 + FEAS_EPS or hb + hg < 1 - FEAS_EPS:
            return None
        low, high = max(lb, 1.0 - hg), min(hb, 1.0 - lg)
        if low > high + FEAS_EPS:
            return None
        if low > high:                       # float noise only: the range is a single point
            low = high = (low + high) / 2
        return min(1.0, max(0.0, low)), min(1.0, max(0.0, high))

    cases = [solve(lo_bad, hi_bad, lo_good, hi_good)]
    spread = ROUND * (len(options) - 1)      # what the option that absorbed the residual may be off by
    if spread > ROUND:
        for m, r in probs.items():           # an omitted option is already anywhere in [0, 1]
            wide_lo, wide_hi = max(0.0, r - spread), min(1.0, r + spread)
            lo_m, hi_m = base[m]
            if m in bad:
                cases.append(solve(lo_bad - lo_m + wide_lo, hi_bad - hi_m + wide_hi, lo_good, hi_good))
            else:
                cases.append(solve(lo_bad, hi_bad, lo_good - lo_m + wide_lo, hi_good - hi_m + wide_hi))
    cases = [c for c in cases if c is not None]
    if not cases:
        raise GateError("the answer is not a probability distribution")
    return cases


def hazard_range(check: Check, answer: dict) -> tuple:
    """(low, high): the violation probability that one validated answer still allows.

    The API reports two decimals and a reported number may be off by almost a cent, so every reported number
    stands for an interval of +-ROUND (the measurement behind that constant is next to it); an option the
    answer leaves out is unknown (anywhere in [0, 1]); and all options together sum to 1. The options that
    count as a violation and the others are summed separately and each side bounds the other (bad <= 1 - the
    least the others can hold, bad >= 1 - the most they can hold). Dividing by the reported total would hide a
    lost or surplus mass; this keeps it as uncertainty instead.
    One more case, because the cents that rounding loses may be handed to a single option: with k options that
    option can be off by up to ROUND * (k - 1). Which one is unknown, so the range is the union over every
    reported option (a Noul has two options and no such case). The tests check that the range holds the true
    value under several rounding rules (nearest, floor, largest remainder, residual to the largest or to a
    random option). An answer that no distribution can explain, or that carries less than MIN_MASS of the
    probability, raises GateError. The rounding rule is an assumption the vendor does not document."""
    cases = _hazard_cases(check, answer)
    return min(c[0] for c in cases), max(c[1] for c in cases)


def hazard(check: Check, answer: dict) -> float:
    """One number for display: the reported probability for a Noul, the middle of the plain reading of the
    answer (the first case of _hazard_cases) otherwise. Decisions use hazard_range, not this number."""
    if check.question["type"] == "noul":
        p = float(answer["noul"])
        h = p if check.violation == "yes" else 1.0 - p
        if not math.isfinite(h) or h < -EPS or h > 1 + EPS:
            raise GateError("hazard is not a probability")
        return min(1.0, max(0.0, h))
    low, high = _hazard_cases(check, answer)[0]
    return (low + high) / 2


def band_for(check: Check, h: float, review_at=REVIEW_AT, block_at=BLOCK_AT, high=None) -> str:
    """The action one hazard asks for. `h` is the hazard, or the low end of its range when `high` is given.
    pass needs even the high end below review_at; block needs even the low end at or above block_at; a soft
    check (severity review) never goes past review."""
    ra = review_at if check.review_at is None else check.review_at
    ba = block_at if check.block_at is None else check.block_at
    high = h if high is None else high
    if h >= ba - EPS:
        return BLOCK if check.severity == BLOCK else REVIEW
    return REVIEW if high >= ra - EPS else PASS


@dataclass
class Reason:
    name: str
    source: str                  # code | jev | infra
    band: str                    # pass | review | block
    hazard: float | None         # for display: the range below decides, this is its middle (a Noul: as reported)
    detail: str = ""             # where a code check matched, or why the gate could not judge; never the text
    confidence: float | None = None
    low: float | None = None     # the range of the violation probability the rounded answer allows
    high: float | None = None


@dataclass
class Verdict:
    action: str
    reasons: list
    degraded: bool = False       # the gate could not judge fully; a block that was found anyway stays a block
    meta: Meta = field(default_factory=Meta)

    @property
    def exit_code(self) -> int:
        return EXIT_CODES[self.action]

    def to_dict(self) -> dict:
        return {"action": self.action, "degraded": self.degraded, "model": self.meta.model,
                "cost_usd": round(self.meta.cost_usd, 6), "seconds": round(self.meta.seconds, 3),
                "cached": self.meta.cached,
                "reasons": [{"name": r.name, "source": r.source, "band": r.band,
                             "hazard": None if r.hazard is None else round(r.hazard, 3),
                             "range": None if r.low is None or r.high is None
                             else [round(r.low, 3), round(r.high, 3)],
                             "confidence": r.confidence, "detail": _CTRL.sub(" ", r.detail)[:120]}
                            for r in self.reasons]}


def decide(reasons: list) -> str:
    return max((r.band for r in reasons), key=_ORDER.__getitem__, default=PASS)


def _text_problem(text: str):
    """Why a text cannot be judged at all, or None. Shared by the gate and by calibrate."""
    if not text.strip():
        return "empty text"
    if len(text) > MAX_TEXT_CHARS:
        return f"text is over {MAX_TEXT_CHARS} characters"
    return None


def _run_code_checks(code_checks, text: str):
    """-> (reasons, degraded). A check that raises is a review reason and does not stop the others."""
    reasons, degraded = [], False
    for cc in code_checks:
        try:
            note = cc.test(text)
        except Exception as e:      # a broken check must not hide what the others found
            degraded = True
            reasons.append(Reason(cc.name, "infra", REVIEW, None, f"code check failed: {_class_name(e)}"))
            continue
        if note is not None:
            kept = note if isinstance(note, str) and _NOTE_RE.fullmatch(note) else "matched"
            reasons.append(Reason(cc.name, "code", cc.severity, 1.0, kept))
    return reasons, degraded


def _frozen(c: Check) -> Check:
    """A private copy that a later change to the caller's lists and dicts cannot reach."""
    jc._require(isinstance(c.labels, (list, tuple)), f"labels of {c.name!r} must be a list or a tuple")
    return replace(c, question=copy.deepcopy(c.question), labels=tuple(c.labels))


class Gate:
    def __init__(self, checks=(), code_checks=(), *, review_at=REVIEW_AT, block_at=BLOCK_AT,
                 route=None, model=None, cache=None, ttl_days=DEFAULT_TTL_DAYS, timeout=30,
                 audit_path=None):
        checks, code_checks = tuple(checks), tuple(code_checks)
        jc._require(all(isinstance(c, Check) for c in checks), "checks must be Check objects")
        jc._require(all(isinstance(c, CodeCheck) for c in code_checks), "code_checks must be CodeCheck objects")
        jc._require(checks or code_checks,
                    "the battery is empty: a gate with no checks would pass everything")
        _require_ttl(ttl_days)
        # Private copies: a battery that was validated here stays as validated, whatever the caller does later
        self.checks, self.code_checks = tuple(_frozen(c) for c in checks), code_checks
        names = [c.name for c in self.checks] + [c.name for c in self.code_checks]
        jc._require(len(set(names)) == len(names), "check names must be unique")
        jc._require(jc._prob(review_at) and jc._prob(block_at) and review_at <= block_at,
                    "need 0 <= review_at <= block_at <= 1")
        for c in self.checks:     # a broken battery is a programming error: fail now, not at judging time
            _validate_check(c, review_at, block_at)
        for cc in self.code_checks:
            _check_args(cc.name, cc.severity, None, None)
            jc._require(callable(cc.test), f"code check {cc.name!r} must be callable")
        self._questions = {c.name: c.question for c in self.checks}
        for chunk in _chunks(self._questions, jc.MAX_QUESTIONS):
            jc.validate_questions(chunk)
        self.review_at, self.block_at = review_at, block_at
        self.route, self.model, self.cache = route, model, cache
        self.ttl_days, self.timeout = ttl_days, timeout
        self.audit_path = Path(audit_path) if audit_path else None
        self.fingerprint = self._fingerprint()

    def _fingerprint(self) -> str:
        """Identity of the battery, the thresholds and the decision rule. Computed again at every judgement:
        a battery that was edited after the gate was built (the attributes are public) is refused, not used."""
        blob = json.dumps([[c.name, c.question, c.violation, list(c.labels), c.at_least, c.severity,
                            c.review_at, c.block_at] for c in self.checks]
                          + [[cc.name, cc.severity, cc.ident] for cc in self.code_checks]
                          + [self.review_at, self.block_at, POLICY, ROUND, FEAS_EPS, EPS, MIN_MASS],
                          ensure_ascii=False, separators=(",", ":"))
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:12]

    @property
    def can_block(self) -> bool:
        return any(c.severity == BLOCK for c in self.checks) or any(cc.severity == BLOCK for cc in self.code_checks)

    def judge(self, text: str, *, context=None) -> Verdict:
        jc._require(isinstance(text, str), "the text to judge must be a string")
        reasons: list = []
        meta, degraded = Meta(), False
        snapshot = _NO_CONTEXT if context is None else _UNAVAILABLE      # what the audit will hash
        try:
            problem = _text_problem(text)
            if problem:
                raise GateError(problem)
            # Code checks first: a block found here must survive whatever fails below (a copy of the context,
            # the fingerprint, the API).
            reasons, degraded = _run_code_checks(self.code_checks, text)
            if self._fingerprint() != self.fingerprint:
                raise GateError("the battery changed after the gate was built")
            if self.checks and not any(r.band == BLOCK for r in reasons):
                # One private snapshot for the whole call: an edit that lands while the request is in flight
                # changes neither the questions, nor the checks, nor the thresholds used on the answers.
                checks = tuple(copy.deepcopy(c) for c in self.checks)
                review_at, block_at = self.review_at, self.block_at
                questions = {c.name: c.question for c in checks}
                if context is not None:
                    snapshot = copy.deepcopy(context)      # the request, the cache and the audit see one context
                state = text if context is None else {"text": text, "context": snapshot}
                answers, meta = ask_battery(state, questions, route=self.route, model=self.model,
                                            cache=self.cache, ttl_days=self.ttl_days, timeout=self.timeout)
                for c in checks:
                    try:
                        a = answers[c.name]
                        lo, hi = hazard_range(c, a)
                        h = hazard(c, a)
                        band = band_for(c, lo, review_at, block_at, high=hi)
                        note = "" if band == band_for(c, h, review_at, block_at) \
                            else f"rounding range {lo:.3f}-{hi:.3f}"
                        reasons.append(Reason(c.name, "jev", band, h, note, a.get("confidence"), lo, hi))
                    except Exception as e:     # one unreadable answer must not decide for the others
                        degraded = True
                        reasons.append(Reason(c.name, "infra", REVIEW, None, _safe_error(e)))
        except Exception as e:   # outage, bad key, oversize text, malformed answer, corrupt cache: fail closed
            degraded = True
            name = "jev-unavailable" if isinstance(e, jc.JevError) and not isinstance(e, GateError) else "gate-error"
            reasons.append(Reason(name, "infra", REVIEW, None, _safe_error(e)))
        verdict = Verdict(decide(reasons), reasons, degraded, meta)
        try:
            self._audit(text, snapshot, verdict)
        except Exception as e:
            verdict.degraded = True
            verdict.reasons.append(Reason("audit-failed", "infra", REVIEW, None, _class_name(e)))
            verdict.action = decide(verdict.reasons)
        return verdict

    def _audit(self, text, context, v: Verdict):
        if not self.audit_path:
            return
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "text": _text_digest(text)[:16], "chars": len(text),
               "context": None if context is _NO_CONTEXT else "unavailable" if context is _UNAVAILABLE else
               _text_digest(json.dumps(context, ensure_ascii=False, sort_keys=True))[:16],
               "battery": self.fingerprint, "policy": POLICY,
               "review_at": self.review_at, "block_at": self.block_at,
               "action": v.action, "degraded": v.degraded, "model": v.meta.model,
               "cost_usd": round(v.meta.cost_usd, 6), "cached": v.meta.cached,
               "reasons": [{"name": r.name, "source": r.source, "band": r.band,
                            "hazard": None if r.hazard is None else round(r.hazard, 3),
                            "range": None if r.low is None or r.high is None
                            else [round(r.low, 3), round(r.high, 3)]}
                           for r in v.reasons]}
        self.audit_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.audit_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def calibrate(checks, examples, *, code_checks=(), review_grid=(0.2, 0.35, 0.5),
              block_grid=(0.6, 0.7, 0.85, 0.95), workers=4, **ask_kw) -> dict:
    """Ask the battery once per labelled example (cache hits and code blocks need no request), then sweep
    thresholds offline (no more calls).

    examples: [{"id": optional, "text": ..., "expect": "pass" | "review" | "block"}].
    Miss kinds: missed = expected review/block but passed; soft = expected block but only review;
    over_block = expected pass/review but blocked; over_review = expected pass but review.
    Checks with their own review_at/block_at keep them in every cell (listed in local_thresholds): the
    sweep only moves the gate defaults. `best` minimises (missed, over_block, over_review, soft) in that
    order: a stated cost policy, not a universal optimum.
    A cell decides exactly as a Gate does (each hazard is a range, an unusable text or a failing code check is
    a review). Cells a Gate would refuse (review_at above block_at for any check, local overrides included)
    are skipped and counted in `skipped_cells`.
    """
    review_grid, block_grid = tuple(review_grid), tuple(block_grid)     # a generator is read more than once
    # The very validation a Gate applies (types, severities, labels, names, schema, ttl), with defaults wide
    # enough that every local threshold is legal; thresholds are checked cell by cell below. The checks used
    # from here on are the gate's private copies.
    gate = Gate(checks, code_checks, review_at=0.0, block_at=1.0, ttl_days=ask_kw.get("ttl_days", DEFAULT_TTL_DAYS))
    checks, code_checks = gate.checks, gate.code_checks
    jc._require(len(examples) > 0, "calibrate needs at least one labelled example")
    jc._require(review_grid and block_grid and all(jc._prob(x) for x in review_grid + block_grid),
                "grids must be non-empty with values in [0, 1]")
    ids = []
    for i, ex in enumerate(examples):
        jc._require(ex.get("expect") in _ORDER and isinstance(ex.get("text"), str),
                    f"example {i}: needs text and expect in pass|review|block")
        ids.append(ex.get("id", i))
    jc._require(len(set(map(str, ids))) == len(ids), "example ids must be unique")
    qs = gate._questions

    def one(ex):
        # Same stages as Gate.judge: an unusable text is a review, a failing code check is a review reason
        problem = _text_problem(ex["text"])
        if problem:
            return [Reason("gate-error", "infra", REVIEW, None, problem)], {}, Meta()
        code, _ = _run_code_checks(code_checks, ex["text"])
        if checks and not any(r.band == BLOCK for r in code):
            answers, meta = ask_battery(ex["text"], qs, **ask_kw)
            return code, {c.name: (hazard(c, answers[c.name]), *hazard_range(c, answers[c.name]))
                          for c in checks}, meta
        return code, {}, Meta()

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        runs = list(pool.map(one, examples))
    total = Meta()
    for _, _, m in runs:
        total.add(m)

    def effective(c, ra, ba):
        return ra if c.review_at is None else c.review_at, ba if c.block_at is None else c.block_at

    grid, skipped = [], 0
    for ra in review_grid:
        for ba in block_grid:
            if ra > ba or any(lo_hi[0] > lo_hi[1] for lo_hi in (effective(c, ra, ba) for c in checks)):
                skipped += 1           # a Gate would refuse these thresholds, so the cell says nothing about it
                continue
            row = {"review_at": ra, "block_at": ba, "ok": 0, "missed": 0, "soft": 0,
                   "over_block": 0, "over_review": 0}
            for ex, (code, hz, _) in zip(examples, runs):
                got = decide(code + [Reason(c.name, "jev", band_for(c, hz[c.name][1], ra, ba, high=hz[c.name][2]),
                                            hz[c.name][0]) for c in checks if c.name in hz])
                exp = ex["expect"]
                if got == exp:
                    row["ok"] += 1
                elif got == PASS:
                    row["missed"] += 1
                elif exp == BLOCK:
                    row["soft"] += 1
                elif got == BLOCK:
                    row["over_block"] += 1
                else:
                    row["over_review"] += 1
            row["accuracy"] = round(row["ok"] / len(examples), 3)
            grid.append(row)
    best = min(grid, key=lambda r: (r["missed"], r["over_block"], r["over_review"], r["soft"]), default=None)
    return {"examples": len(examples), "cost_usd": round(total.cost_usd, 6), "model": total.model,
            "cached": total.cached, "requests": total.requests, "grid": grid, "best": best,
            "skipped_cells": skipped,
            "local_thresholds": [c.name for c in checks if c.review_at is not None or c.block_at is not None],
            "hazards": {ids[i]: {k: v[0] for k, v in hz.items()} for i, (_, hz, _) in enumerate(runs)},
            "ranges": {ids[i]: {k: [v[1], v[2]] for k, v in hz.items()} for i, (_, hz, _) in enumerate(runs)}}


# --- readable vector ------------------------------------------------------------

@dataclass(frozen=True)
class Axis:
    name: str
    question: dict
    weight: float = 1.0


class Axes:
    """A named, ordered set of questions. The hash covers names, questions and their order (the order of
    Choice options included), not weights, so re-weighting never forces re-profiling. Questions are copied
    on construction: later changes to the caller's dicts cannot desynchronise the hash."""

    def __init__(self, axes):
        self.axes = tuple(Axis(a.name, copy.deepcopy(a.question), a.weight) for a in axes)
        jc._require(self.axes, "axes must not be empty")
        names = [a.name for a in self.axes]
        jc._require(len(set(names)) == len(names), "axis names must be unique")
        jc._require(all(type(a.weight) in (int, float) and math.isfinite(a.weight) and a.weight > 0
                        for a in self.axes), "axis weights must be positive numbers")
        for chunk in _chunks({a.name: a.question for a in self.axes}, jc.MAX_QUESTIONS):
            jc.validate_questions(chunk)
        self.hash = self._compute_hash()

    def _compute_hash(self) -> str:
        blob = json.dumps([[a.name, a.question] for a in self.axes], ensure_ascii=False,
                          allow_nan=False, separators=(",", ":"))
        return hashlib.sha256(b"jev-axes-v2\0" + blob.encode("utf-8")).hexdigest()[:12]

    def verify(self) -> None:
        """Refuse axes that were edited after they were built (`axes.axes[i].question` is a public dict): the
        hash on a profile would no longer describe the questions it was made from."""
        if self._compute_hash() != self.hash:
            raise GateError("the axes changed after they were built")

    def questions(self, mode="like") -> dict:
        """The questions to ask, as copies: changing them cannot change the axes behind the hash."""
        jc._require(mode in ("like", "want"), "mode must be 'like' or 'want'")
        self.verify()
        return {a.name: copy.deepcopy(_want(a.question) if mode == "want" else a.question) for a in self.axes}


_WANT = ("The state is a request, not a document. Answer for the document the requester is looking for. ")


def _want(question: dict) -> dict:
    """Same options, but asked about the document a request is looking for."""
    q = dict(question)
    ins = q["instructions"]
    q["instructions"] = _WANT + ins if isinstance(ins, str) else {"framing": _WANT.strip(), "question": ins}
    return q


def distribution(question: dict, answer: dict) -> list:
    """One answer as a probability vector: [no, yes] for noul, option order for choice, level order for score."""
    kind = question["type"]
    if kind == "noul":
        p = float(answer["noul"])
        return [1.0 - p, p]
    probs = answer["probabilities"]
    labels = list(question["criteria"]) if kind == "choice" else [str(i) for i in range(len(question["criteria"]))]
    v = [float(probs.get(label, 0.0)) for label in labels]
    s = math.fsum(v)
    jc._require(math.isfinite(s) and s >= MIN_MASS, "the answer covers too little probability")
    return [x / s for x in v]


def tv(p, q) -> float:
    """Total variation distance, in [0, 1]."""
    jc._require(len(p) == len(q), "distributions of different sizes cannot be compared")
    return 0.5 * math.fsum(abs(a - b) for a, b in zip(p, q))


def emd_norm(p, q) -> float:
    """Earth mover's distance between ordered distributions, divided by its maximum (n - 1)."""
    jc._require(len(p) == len(q), "distributions of different sizes cannot be compared")
    if len(p) < 2:
        return 0.0
    cum = total = 0.0
    for a, b in zip(p, q):
        cum += a - b
        total += abs(cum)
    return total / (len(p) - 1)


def _axis_distance(axis: Axis, p, q) -> float:
    return emd_norm(p, q) if axis.question["type"] == "score" else tv(p, q)


def _relative_weights(axes: Axes) -> list:
    """Weights divided by the largest one: the mean cannot overflow however large the weights are."""
    wmax = max(ax.weight for ax in axes.axes)
    return [ax.weight / wmax for ax in axes.axes]


@dataclass
class Profile:
    axes_hash: str
    model: str | None
    dims: dict
    mode: str = "like"
    meta: Meta = field(default_factory=Meta)


def profile(text, axes: Axes, *, mode="like", route=None, model=None, cache=None,
            ttl_days=DEFAULT_TTL_DAYS, timeout=30) -> Profile:
    questions = axes.questions(mode)         # verified copies: the profile is built from these, not from live axes
    answers, meta = ask_battery(text, questions, route=route, model=model, cache=cache,
                                ttl_days=ttl_days, timeout=timeout)
    axes.verify()                            # axes edited while the request was out: the hash would lie
    dims = {a.name: distribution(questions[a.name], answers[a.name]) for a in axes.axes}
    return Profile(axes.hash, meta.model, dims, mode, meta)


def profile_many(texts: dict, axes: Axes, *, workers=4, **kw):
    """Profile many texts concurrently. Returns ({id: Profile}, {id: short error}); one failure of any
    kind keeps the rest."""
    done, errors = {}, {}

    def one(item):
        key, text = item
        try:
            done[key] = profile(text, axes, **kw)
        except Exception as e:
            errors[key] = _safe_error(e)

    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        list(pool.map(one, texts.items()))
    return done, errors


def _single_known(model) -> bool:
    """One named build: the format _model_name lets through, so '' or a joined 'a|b' never counts as known."""
    return isinstance(model, str) and model != UNKNOWN_MODEL and _MODEL_RE.fullmatch(model) is not None


def _compatible(a: Profile, b: Profile, axes: Axes, allow_mix: bool):
    if allow_mix:
        return
    axes.verify()
    if a.axes_hash != axes.hash or b.axes_hash != axes.hash:
        raise ProfileMismatch("profile was built with a different set of questions")
    if not (_single_known(a.model) and _single_known(b.model)) or a.model != b.model:
        raise ProfileMismatch(f"profiles come from different, mixed or unknown models ({a.model!r} vs {b.model!r}); "
                              "re-profile with one model or pass allow_mix=True")
    for ax in axes.axes:
        if ax.name not in a.dims or ax.name not in b.dims:
            raise ProfileMismatch(f"profile has no answer for the axis {ax.name!r}")


def distance(a: Profile, b: Profile, axes: Axes, *, allow_mix=False) -> float:
    _compatible(a, b, axes, allow_mix)
    rel = _relative_weights(axes)
    return math.fsum(r * _axis_distance(ax, a.dims[ax.name], b.dims[ax.name])
                     for r, ax in zip(rel, axes.axes)) / math.fsum(rel)


def explain(a: Profile, b: Profile, axes: Axes, *, top=5, allow_mix=False) -> list:
    """The questions that disagree most, with both distributions: which question failed."""
    _compatible(a, b, axes, allow_mix)
    rel = _relative_weights(axes)
    total = math.fsum(rel)
    rows = []
    for r, ax in zip(rel, axes.axes):
        d = _axis_distance(ax, a.dims[ax.name], b.dims[ax.name])
        ins = ax.question["instructions"]
        rows.append({"axis": ax.name, "distance": round(d, 3), "weight": ax.weight,
                     "share": round(r * d / total, 3), "_share": r * d / total,
                     "a": [round(x, 3) for x in a.dims[ax.name]],
                     "b": [round(x, 3) for x in b.dims[ax.name]],
                     "question": ins if isinstance(ins, str) else json.dumps(ins, ensure_ascii=False)})
    rows.sort(key=lambda row: -row["_share"])
    for row in rows:
        del row["_share"]
    return rows[:top]


def rank_profiles(query: Profile, docs: dict, axes: Axes, *, top=10, allow_mix=False) -> list:
    """[(id, similarity)] with similarity = 1 - distance, best first."""
    scored = [(k, 1.0 - distance(query, p, axes, allow_mix=allow_mix)) for k, p in docs.items()]
    scored.sort(key=lambda kv: -kv[1])
    return scored[:top]


# --- specs and CLI ---------------------------------------------------------------

def check_from_spec(spec: dict) -> Check:
    kind = spec.get("type")
    common = {"severity": spec.get("severity", REVIEW), "review_at": spec.get("review_at"),
              "block_at": spec.get("block_at")}
    if kind == "noul":
        return noul_check(spec["name"], spec["instructions"], violation=spec.get("violation", "yes"),
                          yes=spec.get("yes"), no=spec.get("no"), **common)
    if kind == "choice":
        return choice_check(spec["name"], spec["instructions"], spec["options"], spec["labels"], **common)
    if kind == "score":
        return score_check(spec["name"], spec["instructions"], spec["levels"], spec["at_least"], **common)
    raise jc.JevInputError(f"unknown check type {kind!r}")


def axis_from_spec(spec: dict) -> Axis:
    kind = spec.get("type")
    if kind == "noul":
        q = jc.noul(spec["instructions"], spec.get("yes"), spec.get("no"))
    elif kind == "choice":
        q = jc.choice(spec["instructions"], spec["options"])
    elif kind == "score":
        q = jc.score(spec["instructions"], spec["levels"])
    else:
        raise jc.JevInputError(f"unknown axis type {kind!r}")
    return Axis(spec["name"], q, float(spec.get("weight", 1.0)))


def load_battery(spec: dict):
    """-> (checks, code_checks, review_at, block_at) from a battery JSON object."""
    checks = [check_from_spec(s) for s in spec.get("checks", [])]
    code = [regex_check(s["name"], s["regex"], severity=s.get("severity", BLOCK),
                        flags=re.IGNORECASE if "i" in s.get("flags", "i") else re.NOFLAG)
            for s in spec.get("code_checks", [])]
    return checks, code, spec.get("review_at", REVIEW_AT), spec.get("block_at", BLOCK_AT)


def load_axes(spec: dict) -> Axes:
    return Axes([axis_from_spec(s) for s in spec["axes"]])


def _read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def _text_arg(a) -> str:
    if getattr(a, "file", None):
        return Path(a.file).read_text(encoding="utf-8")
    if a.text == "-":
        return sys.stdin.read()
    if a.text is None:
        raise jc.JevInputError("need --text «text» (or --text - for stdin, or --file)")
    return a.text


def _open_cache(a):
    """The cache is an optimisation: if it cannot be opened the command goes on without it."""
    if a.no_cache:
        return None
    try:
        return AnswerCache(a.db)
    except (OSError, sqlite3.Error) as e:
        print(f"ПРЕДУПРЕЖДЕНИЕ: кеш недоступен ({type(e).__name__}), работаю без него", file=sys.stderr)
        return None


def _selftest() -> int:
    ok = True

    def check(cond, what):
        nonlocal ok
        print(("ok   " if cond else "FAIL ") + what)
        ok = ok and cond

    check(abs(tv([1, 0], [0, 1]) - 1) < 1e-9, "tv: opposite yes/no = 1")
    check(tv([.3, .7], [.3, .7]) == 0, "tv: identical = 0")
    check(abs(emd_norm([1, 0, 0], [0, 0, 1]) - 1) < 1e-9, "emd: ends of a scale = 1")
    check(emd_norm([1, 0, 0], [0, 1, 0]) < emd_norm([1, 0, 0], [0, 0, 1]), "emd: near < far")
    q = jc.score("x", ["a", "b", "c"])
    check(distribution(q, {"probabilities": {"0": .2, "1": .3, "2": .5}}) == [.2, .3, .5], "distribution: score")
    c = noul_check("n", "x", severity=BLOCK)
    check(band_for(c, .8) == BLOCK and band_for(c, .4) == REVIEW and band_for(c, .1) == PASS, "bands: block/review/pass")
    soft = noul_check("s", "x")
    check(band_for(soft, .99) == REVIEW, "bands: a soft check never blocks")
    check(band_for(noul_check("n", "x", violation="no", review_at=0.2), 1 - 0.8) == REVIEW, "bands: float noise at a threshold")
    n = noul_check("n", "x", severity=BLOCK)
    lo, hi = hazard_range(n, {"noul": 0.70})
    check(abs(lo - 0.69) < 1e-9 and abs(hi - 0.71) < 1e-9, "range: a Noul is its reported number +-0.01")
    check(band_for(n, lo, high=hi) == REVIEW and band_for(n, 0.33, high=0.34) == PASS,
          "range: block needs the low end at block_at, pass needs the high end below review_at")
    two = choice_check("c", "x", ["a", "b"], ["a"])
    lo, hi = hazard_range(two, {"probabilities": {"a": 0.49, "b": 0.50}})
    check(abs(lo - 0.49) < 1e-9 and abs(hi - 0.50) < 1e-9, "range: .49 + .50 stays between .49 and .50")
    return 0 if ok else 1


def _cli_error(e: BaseException) -> str:
    """What the command line says about a failure: problems with files and configuration in words, and for
    everything that touched the text only what _safe_error allows, so a message never repeats the text."""
    if isinstance(e, json.JSONDecodeError):
        s = f"invalid JSON ({e.msg}, line {e.lineno}, column {e.colno})"
    elif isinstance(e, UnicodeDecodeError):
        s = f"cannot read the file as {e.encoding}"
    elif isinstance(e, KeyError):
        s = f"missing field {e.args[0]!r}" if e.args and isinstance(e.args[0], str) else "missing field"
    elif isinstance(e, OSError):
        s = " ".join(x for x in (type(e).__name__ + ":", e.strerror or "", str(e.filename or "")) if x)
    elif isinstance(e, jc.JevInputError):
        s = str(e)            # the client's validators and our own fixed messages: configuration, never the text
    else:
        s = _safe_error(e)
    return _CTRL.sub(" ", s)[:300]


def main() -> int:
    reconf = getattr(sys.stdout, "reconfigure", None)
    if reconf:
        reconf(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, text=True):
        p.add_argument("--route", choices=list(jc.ROUTES), default=None)
        p.add_argument("--db", help="путь к кешу ответов (по умолчанию ~/.claude/cache/jev_patterns.sqlite)")
        p.add_argument("--no-cache", action="store_true")
        p.add_argument("--json", action="store_true")
        if text:
            p.add_argument("--text", help="текст или - для stdin")
            p.add_argument("--file", help="файл с текстом")

    p = sub.add_parser("gate", help="батарея вопросов о тексте → pass / review / block (коды выхода 0 / 10 / 11)")
    p.add_argument("--battery", required=True)
    p.add_argument("--review-at", type=float)
    p.add_argument("--block-at", type=float)
    p.add_argument("--audit", help="JSONL-журнал решений (хеш текста с ключом, без самого текста)")
    common(p)
    p = sub.add_parser("calibrate", help="размеченные примеры → таблица порогов без лишних вызовов")
    p.add_argument("--battery", required=True)
    p.add_argument("--examples", required=True)
    common(p, text=False)
    p = sub.add_parser("profile", help="вектор ответов для текста")
    p.add_argument("--axes", required=True)
    p.add_argument("--mode", choices=["like", "want"], default="like")
    common(p)
    p = sub.add_parser("rank", help="упорядочить документы по близости к запросу")
    p.add_argument("--axes", required=True)
    p.add_argument("--query", required=True)
    p.add_argument("--docs", required=True, help='JSON {id: текст}')
    p.add_argument("--mode", choices=["like", "want"], default="want",
                   help="как спрашивать про запрос: want = «какой документ он ищет» (по умолчанию), like = как про документ")
    p.add_argument("-n", type=int, default=10)
    p.add_argument("--explain", action="store_true")
    common(p, text=False)
    sub.add_parser("selftest", help="офлайн-проверка чистых функций")

    a = ap.parse_args()
    if a.cmd == "selftest":
        return _selftest()
    cache = None
    try:
        cache = _open_cache(a)
        return _run(a, cache)
    except Exception as e:
        print(f"ОШИБКА: {_cli_error(e)}", file=sys.stderr)
        return 2
    finally:
        if cache is not None:
            cache.close()


def _run(a, cache) -> int:
    if a.cmd == "gate":
        checks, code, ra, ba = load_battery(_read_json(a.battery))
        gate = Gate(checks, code, review_at=a.review_at if a.review_at is not None else ra,
                    block_at=a.block_at if a.block_at is not None else ba,
                    route=a.route, cache=cache, audit_path=a.audit)
        if not gate.can_block:
            print("ПРЕДУПРЕЖДЕНИЕ: в батарее нет ни одной блокирующей проверки, block невозможен", file=sys.stderr)
        v = gate.judge(_text_arg(a))
        if a.json:
            print(json.dumps(v.to_dict(), ensure_ascii=False, indent=1))
        else:
            print(f"ВЕРДИКТ: {v.action}   (код выхода {v.exit_code})" + ("   [проверка неполная]" if v.degraded else ""))
            for r in v.reasons:
                h = "-" if r.hazard is None else f"{r.hazard:.2f}"
                print(f"  {r.band:6} {r.source:5} {r.name}  {h}" + (f"  {_CTRL.sub(' ', r.detail)[:80]}" if r.detail else ""))
            print(f"[{v.meta.model} · {v.meta.seconds:.2f} с · ${v.meta.cost_usd:.6f} · из кеша {v.meta.cached}]")
        return v.exit_code
    if a.cmd == "calibrate":
        checks, code, _, _ = load_battery(_read_json(a.battery))
        out = calibrate(checks, _read_json(a.examples), code_checks=code, route=a.route, cache=cache)
        if a.json:
            print(json.dumps(out, ensure_ascii=False, indent=1))
        else:
            print(f"примеров {out['examples']} · запросов {out['requests']} · ${out['cost_usd']} · модель {out['model']} · из кеша {out['cached']}")
            if out["local_thresholds"]:
                print("свои пороги у проверок (в таблице не меняются):", ", ".join(out["local_thresholds"]))
            if out["skipped_cells"]:
                print(f"пропущено ячеек, которые Gate бы отверг (review_at выше block_at): {out['skipped_cells']}")
            print("review_at block_at  верно  пропущено  мягко  лишний_block  лишний_review")
            for r in out["grid"]:
                print(f"{r['review_at']:9} {r['block_at']:8} {r['ok']:6} {r['missed']:10} {r['soft']:6} "
                      f"{r['over_block']:13} {r['over_review']:14}")
            print("лучшие пороги (меньше всего пропусков, потом лишних block):", out["best"])
        return 0
    if a.cmd == "profile":
        axes = load_axes(_read_json(a.axes))
        pr = profile(_text_arg(a), axes, mode=a.mode, route=a.route, cache=cache)
        if a.json:
            print(json.dumps({"axes_hash": pr.axes_hash, "model": pr.model, "mode": pr.mode, "dims": pr.dims},
                             ensure_ascii=False, indent=1))
        else:
            print(f"[{pr.model} · оси {pr.axes_hash} · режим {pr.mode}]")
            for name, dist in pr.dims.items():
                print(f"  {name}: " + " ".join(f"{x:.2f}" for x in dist))
        return 0
    if a.cmd == "rank":
        axes = load_axes(_read_json(a.axes))
        qp = profile(a.query, axes, mode=a.mode, route=a.route, cache=cache)
        docs, errors = profile_many(_read_json(a.docs), axes, route=a.route, cache=cache)
        ranked = rank_profiles(qp, docs, axes, top=a.n)
        why = {k: explain(qp, docs[k], axes, top=2) for k, _ in ranked} if a.explain else {}
        if a.json:
            print(json.dumps({"ranked": ranked, "errors": errors, "explain": why}, ensure_ascii=False, indent=1))
        else:
            for k, s in ranked:
                print(f"  {s:.3f}  {k}")
                for r in why.get(k, []):
                    print(f"         ↳ {r['axis']}: расхождение {r['distance']}  запрос {r['a']}  документ {r['b']}")
            for k, e in errors.items():
                print(f"  ОШИБКА {k}: {e}", file=sys.stderr)
        return 0 if docs else 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
