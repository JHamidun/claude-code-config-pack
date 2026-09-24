"""Offline contract and safety tests for ~/.claude/tools/jev_client.py.

Public API under test: system_one positional, ask -> float, pick -> tuple,
rank -> list with chunking, JevError(status, body).
No network: every request goes to a fake opener; no real credentials are read.

The client is looked up next to this skill first (<claude dir>/tools/jev_client.py,
three levels above this file), then in $CLAUDE_CONFIG_DIR/tools, then in ~/.claude/tools.

    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest ~/.claude/skills/jev/tests -q
    python ~/.claude/skills/jev/tests/test_jev_client.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

def _find_source() -> Path:
    here = Path(__file__).resolve()
    candidates = [here.parents[3] / "tools" / "jev_client.py"]   # tests -> jev -> skills -> <claude dir>
    config_dir = os.environ.get("CLAUDE_CONFIG_DIR")
    if config_dir:
        candidates.append(Path(config_dir).expanduser() / "tools" / "jev_client.py")
    candidates.append(Path.home() / ".claude" / "tools" / "jev_client.py")
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("jev_client.py not found; looked in: "
                            + ", ".join(str(p) for p in candidates))


SOURCE = _find_source()
ROUTE_VARS = ("TYPESAFE_API_KEY", "OPENROUTER_API_KEY", "JEV_ROUTE", "JEV_MODEL")


def load_module(name: str = "jev_client"):
    spec = importlib.util.spec_from_file_location(name, SOURCE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


jev = load_module()


def body_of(answers: dict, **extra) -> dict:
    return {"model": "jev-1.13.0", "answers": answers,
            "usage": {"input_tokens": 10, "output_tokens": 2}, **extra}


NOUL_OK = body_of({"q": {"type": "noul", "noul": 0.8}})


class FakeOpener:
    """Stands in for build_opener(...): each item is a dict body, bytes or an exception."""

    def __init__(self, *items):
        self.items = list(items)
        self.calls = []

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        item = self.items.pop(0) if len(self.items) > 1 else self.items[0]
        if isinstance(item, BaseException):
            raise item
        data = item if isinstance(item, bytes) else json.dumps(item).encode("utf-8")
        return io.BytesIO(data)


def http_error(code: int, body: bytes = b"", headers: dict | None = None):
    return urllib.error.HTTPError("https://api.typesafe.ai/v1/systemone", code, "err",
                                  headers or {}, io.BytesIO(body))


class Base(unittest.TestCase):
    def setUp(self):
        env = patch.dict(os.environ)
        env.start()
        self.addCleanup(env.stop)
        for var in ROUTE_VARS:
            os.environ.pop(var, None)
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)
        creds = patch.object(jev, "CREDENTIALS_FILE", self.tmp / "missing.env")
        creds.start()
        self.addCleanup(creds.stop)
        sleep = patch.object(jev.time, "sleep")
        self.sleep = sleep.start()
        self.addCleanup(sleep.stop)

    def opener(self, *items) -> FakeOpener:
        fake = FakeOpener(*items)
        p = patch.object(jev.urllib.request, "build_opener", return_value=fake)
        self.build_opener = p.start()
        self.addCleanup(p.stop)
        return fake


# --- import-time behaviour and credentials ----------------------------------

class ImportAndKeys(Base):
    def test_import_has_no_filesystem_reads(self):
        with patch("builtins.open", side_effect=AssertionError("unexpected read")), \
                patch("pathlib.Path.read_text", side_effect=AssertionError("unexpected read")):
            exec(compile(SOURCE.read_bytes(), str(SOURCE), "exec"), {"__name__": "not_main"})

    def test_import_does_not_add_keys_to_environ(self):
        home = self.tmp / "home"
        (home / ".claude").mkdir(parents=True)
        (home / ".claude" / ".credentials.master.env").write_text(
            "TYPESAFE_API_KEY=file-typesafe\nJEV_TEST_CANARY=leaked\nOTHER_SECRET=x\n",
            encoding="utf-8")
        with patch.dict(os.environ, {"USERPROFILE": str(home), "HOME": str(home)}):
            before = dict(os.environ)
            fresh = load_module("jev_client_fresh")
            self.assertEqual(fresh.CREDENTIALS_FILE, home / ".claude" / ".credentials.master.env")
            self.assertEqual(dict(os.environ), before)
            # Reading the key lazily must not leak it (or anything else) into os.environ.
            self.assertEqual(fresh._key("TYPESAFE_API_KEY"), "file-typesafe")
            self.assertEqual(dict(os.environ), before)
            self.assertNotIn("JEV_TEST_CANARY", os.environ)

    def test_key_reads_only_the_requested_variable(self):
        f = self.tmp / "creds.env"
        f.write_text('# comment\nOPENROUTER_API_KEY="or-key"\nexport TYPESAFE_API_KEY=ts-key\n',
                     encoding="utf-8")
        with patch.object(jev, "CREDENTIALS_FILE", f):
            self.assertEqual(jev._key("TYPESAFE_API_KEY"), "ts-key")
            self.assertEqual(jev._key("OPENROUTER_API_KEY"), "or-key")
            self.assertEqual(jev._key("NOT_THERE"), "")
            os.environ["TYPESAFE_API_KEY"] = "env-wins"
            self.assertEqual(jev._key("TYPESAFE_API_KEY"), "env-wins")

    def test_key_from_file_is_used_for_request(self):
        f = self.tmp / "creds.env"
        f.write_text("TYPESAFE_API_KEY=from-file\n", encoding="utf-8")
        fake = self.opener(NOUL_OK)
        with patch.object(jev, "CREDENTIALS_FILE", f):
            jev.ask("q", "state")
        self.assertEqual(fake.calls[0][0].get_header("Authorization"), "Bearer from-file")
        self.assertNotIn("TYPESAFE_API_KEY", os.environ)


# --- builders and pre-flight validation -------------------------------------

class Builders(Base):
    def test_empty_choice(self):
        with self.assertRaises(jev.JevError):
            jev.choice("q", [])
        with self.assertRaises(jev.JevError):
            jev.choice("q", {})

    def test_duplicate_choice(self):
        with self.assertRaises(jev.JevError):
            jev.choice("q", ["a", "a"])

    def test_blank_label_and_instructions(self):
        for bad in (["a", " "], ["a", ""], {"": "x"}):
            with self.assertRaises(jev.JevError):
                jev.choice("q", bad)
        for builder in (lambda: jev.noul(""), lambda: jev.choice("  ", ["a"]),
                        lambda: jev.score("", ["a", "b"])):
            with self.assertRaises(jev.JevError):
                builder()

    def test_choice_limit(self):
        with self.assertRaises(jev.JevError):
            jev.choice("q", {str(i): "x" for i in range(256)})
        self.assertEqual(len(jev.choice("q", {str(i): "x" for i in range(255)})["criteria"]), 255)

    def test_score_limits(self):
        for levels in ([], ["x"], ["x"] * 11, ["a", ""]):
            with self.assertRaises(jev.JevError):
                jev.score("q", levels)

    def test_input_errors_stay_value_errors(self):
        # Old callers caught ValueError from choice()/score(); keep that working.
        with self.assertRaises(ValueError):
            jev.choice("q", {str(i): "x" for i in range(256)})
        with self.assertRaises(ValueError):
            jev.score("q", ["one"])

    def test_noul_criteria_shape(self):
        self.assertEqual(jev.noul("q", yes="y")["criteria"], {"true": "y"})
        self.assertNotIn("criteria", jev.noul("q"))

    def test_structured_content_is_accepted(self):
        # Vendor docs: instructions, Choice descriptions, Score levels and Noul criteria may be JSON.
        levels = [{"what": "Off-topic", "examples": ["a recipe"]},
                  {"what": "On-topic", "examples": ["the asked question"]}]
        self.assertEqual(jev.score({"task": "rate relevance"}, levels)["criteria"], levels)
        crit = jev.choice({"task": "pick"}, {"a": {"what": "first"}, "b": None})["criteria"]
        self.assertEqual(crit["a"], {"what": "first"})
        self.assertEqual(jev.noul(["check", "this"], yes={"when": "true"})["criteria"],
                         {"true": {"when": "true"}})
        jev.validate_questions({"q": {"type": "score", "instructions": {"t": 1}, "criteria": levels},
                                "n": {"type": "noul", "instructions": "i",
                                      "criteria": {"true": {"when": "x"}}}})

    def test_empty_or_scalar_structures_rejected(self):
        for bad in (lambda: jev.score("q", ["a", {}]), lambda: jev.score({}, ["a", "b"]),
                    lambda: jev.choice([], ["a"]), lambda: jev.choice("q", {"a": []}),
                    lambda: jev.score("q", ["a", 3]), lambda: jev.noul(5)):
            with self.assertRaises(jev.JevInputError):
                bad()

    def test_choice_accepts_any_iterable_of_labels(self):
        for opts in ({"b", "a"}, {"a": None, "b": None}.keys(), (x for x in ["a", "b"]), ("a", "b")):
            self.assertEqual(set(jev.choice("q", opts)["criteria"]), {"a", "b"})
        with self.assertRaises(jev.JevInputError):
            jev.choice("q", "ab")   # a bare string is not a list of labels

    def test_question_count_limits(self):
        fake = self.opener(NOUL_OK)
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"
        for qs in ({}, {f"q{i}": jev.noul("q") for i in range(65)}):
            with self.assertRaises(jev.JevError):
                jev.system_one("s", qs)
        self.assertEqual(fake.calls, [])

    def test_raw_questions_are_validated(self):
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"
        fake = self.opener(NOUL_OK)
        bad = [{"q": {"type": "choice", "instructions": "i", "criteria": ["a", "a"]}},
               {"q": {"type": "noul", "instructions": ""}},
               {"q": {"type": "magic", "instructions": "i"}},
               {"q": {"type": "noul", "instructions": "i", "criteria": {"maybe": "x"}}}]
        for qs in bad:
            with self.assertRaises(jev.JevError):
                jev.system_one("s", qs)
        self.assertEqual(fake.calls, [])

    def test_input_size_precedes_credentials(self):
        # No key anywhere: the size error must come first, and nothing is sent.
        fake = self.opener(NOUL_OK)
        with self.assertRaisesRegex(jev.JevError, "byte limit"):
            jev.ask("q", "x" * 128_000)
        self.assertEqual(fake.calls, [])

    def test_non_finite_state_rejected_before_credentials(self):
        fake = self.opener(NOUL_OK)
        with self.assertRaisesRegex(jev.JevError, "finite JSON"):
            jev.system_one({"x": float("nan")}, {"q": jev.noul("q")})
        self.assertEqual(fake.calls, [])


# --- routes ------------------------------------------------------------------

class Routes(Base):
    def test_missing_key_mentions_explicit_openrouter(self):
        fake = self.opener(NOUL_OK)
        with self.assertRaisesRegex(jev.JevError, "TYPESAFE_API_KEY") as caught:
            jev.ask("q", "state")
        self.assertIn("--route openrouter", str(caught.exception))
        self.assertEqual(fake.calls, [])

    def test_openrouter_never_used_silently(self):
        os.environ["OPENROUTER_API_KEY"] = "fake-or-key"
        fake = self.opener(NOUL_OK)
        with self.assertRaisesRegex(jev.JevError, "TYPESAFE_API_KEY"):
            jev.ask("q", "state")
        self.assertEqual(fake.calls, [])

    def test_direct_route_request_shape(self):
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"
        fake = self.opener(NOUL_OK)
        p = jev.ask("q", "state")
        self.assertEqual(p, 0.8)
        request, timeout = fake.calls[0]
        self.assertEqual(request.full_url, "https://api.typesafe.ai/v1/systemone")
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(json.loads(request.data)["model"], "jev-latest")   # default unchanged
        self.assertEqual(timeout, 30)
        self.assertEqual(request.get_header("User-agent"), "jev-client/1.0 (+claude-code)")
        self.assertEqual(request.get_header("Authorization"), "Bearer fake-test-key")
        self.assertEqual(request.get_header("Content-type"), "application/json")

    def test_opener_has_no_proxy_and_no_redirect(self):
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"
        self.opener(NOUL_OK)
        jev.ask("q", "state")
        handlers = self.build_opener.call_args.args
        proxy = [h for h in handlers if isinstance(h, jev.urllib.request.ProxyHandler)]
        self.assertEqual(len(proxy), 1)
        self.assertEqual(proxy[0].proxies, {})
        self.assertTrue(any(isinstance(h, jev.NoRedirect) for h in handlers))

    def test_redirect_denied(self):
        self.assertIsNone(jev.NoRedirect().redirect_request(
            None, None, 307, "", {}, "https://attacker.invalid"))

    def test_openrouter_by_argument(self):
        os.environ["OPENROUTER_API_KEY"] = "fake-or-key"
        fake = self.opener(NOUL_OK)
        out = jev.system_one("s", {"q": jev.noul("q")}, route="openrouter")
        self.assertEqual(out["_route"], "openrouter")
        self.assertEqual(fake.calls[0][0].full_url, jev.ROUTES["openrouter"][0])
        self.assertEqual(json.loads(fake.calls[0][0].data)["model"], "typesafe/jev-1.13")

    def test_openrouter_by_env(self):
        os.environ["OPENROUTER_API_KEY"] = "fake-or-key"
        os.environ["JEV_ROUTE"] = "openrouter"
        fake = self.opener(NOUL_OK)
        jev.ask("q", "s")
        self.assertEqual(fake.calls[0][0].full_url, jev.ROUTES["openrouter"][0])

    def test_explicit_route_missing_key_has_no_fallback(self):
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"
        fake = self.opener(NOUL_OK)
        with self.assertRaisesRegex(jev.JevError, "OPENROUTER_API_KEY"):
            jev.ask("q", "s", route="openrouter")
        self.assertEqual(fake.calls, [])

    def test_unknown_route(self):
        with self.assertRaisesRegex(jev.JevError, "unknown route"):
            jev.ask("q", "s", route="elsewhere")

    def test_jev_model_override_and_positional_model(self):
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"
        os.environ["JEV_MODEL"] = "jev-1.13.0"
        fake = self.opener(NOUL_OK, NOUL_OK)
        jev.system_one("s", {"q": jev.noul("q")})
        self.assertEqual(json.loads(fake.calls[0][0].data)["model"], "jev-1.13.0")
        jev.system_one("s", {"q": jev.noul("q")}, "jev-custom")      # positional model
        self.assertEqual(json.loads(fake.calls[1][0].data)["model"], "jev-custom")


# --- transport errors and retries -------------------------------------------

class Transport(Base):
    def setUp(self):
        super().setUp()
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"

    def test_http_error_no_retry_or_leak(self):
        fake = self.opener(http_error(401, b"auth failed for fake-test-key " + b"x" * 500))
        with self.assertRaises(jev.JevError) as caught:
            jev.ask("q", "private state")
        msg = str(caught.exception)
        self.assertEqual(caught.exception.status, 401)
        self.assertTrue(msg.startswith("Jev HTTP 401: auth failed"))
        self.assertNotIn("fake-test-key", msg)
        self.assertNotIn("Bearer", msg)
        self.assertNotIn("private state", msg)
        self.assertLessEqual(len(msg), len("Jev HTTP 401: ") + 200)
        self.assertEqual(len(fake.calls), 1)

    def test_cloudflare_body_is_kept(self):
        self.opener(http_error(403, b"error code: 1010"))
        with self.assertRaisesRegex(jev.JevError, "error code: 1010"):
            jev.ask("q", "s")

    def test_retry_once_on_429(self):
        fake = self.opener(http_error(429, b"slow down"), NOUL_OK)
        self.assertEqual(jev.ask("q", "s"), 0.8)
        self.assertEqual(len(fake.calls), 2)
        self.assertEqual(self.sleep.call_count, 1)

    def test_default_is_one_retry(self):
        fake = self.opener(http_error(529, b"overloaded"))
        with self.assertRaises(jev.JevError):
            jev.ask("q", "s")
        self.assertEqual(len(fake.calls), 2)

    def test_retry_wait_is_capped_at_five_seconds(self):
        fake = self.opener(http_error(429, b"", {"retry-after": "100"}))
        with self.assertRaises(jev.JevError):
            jev.system_one("s", {"q": jev.noul("q")}, retries=3)
        waited = sum(c.args[0] for c in self.sleep.call_args_list)
        self.assertLessEqual(waited, 5.0)
        self.assertEqual(len(fake.calls), 2)   # budget gone after the first wait

    def test_retries_zero(self):
        fake = self.opener(http_error(429, b""))
        with self.assertRaises(jev.JevError):
            jev.system_one("s", {"q": jev.noul("q")}, retries=0)
        self.assertEqual(len(fake.calls), 1)
        self.sleep.assert_not_called()

    def test_no_retry_on_server_error_or_network(self):
        for err in (http_error(500, b"boom"), urllib.error.URLError("down"), TimeoutError()):
            fake = self.opener(err)
            with self.assertRaises(jev.JevError):
                jev.ask("q", "s")
            self.assertEqual(len(fake.calls), 1)
        self.sleep.assert_not_called()

    def test_retry_after_nan_or_inf_falls_back_to_delay(self):
        for header in ("nan", "inf", "-inf"):
            fake = self.opener(http_error(429, b"", {"retry-after": header}), NOUL_OK)
            self.sleep.reset_mock()
            self.assertEqual(jev.ask("q", "s"), 0.8)
            self.assertEqual(len(fake.calls), 2)
            self.assertEqual(self.sleep.call_args.args[0], 1.0)

    def test_response_size_cap(self):
        self.opener(b" " * (jev.MAX_BYTES + 1))
        with self.assertRaisesRegex(jev.JevError, "byte limit"):
            jev.ask("q", "s")

    def test_non_json_response(self):
        self.opener(b"<html>cloudflare</html>")
        with self.assertRaisesRegex(jev.JevError, "not JSON"):
            jev.ask("q", "s")


# --- response validation ------------------------------------------------------

class Answers(Base):
    def test_invalid_noul(self):
        for answer in ({"noul": float("nan")}, {"noul": 1.1}, {"noul": True}, {},
                       {"noul": -0.1}, {"type": "choice", "noul": 0.5}):
            with self.assertRaises(jev.JevError):
                jev.check_answers({"answers": {"q": answer}}, {"q": jev.noul("q")})

    def test_question_mismatch(self):
        q = {"q": jev.noul("q")}
        for out in ({"answers": {}}, {"answers": {"q": {"noul": 0.1}, "extra": {"noul": 0.1}}},
                    {}, {"answers": []}, []):
            with self.assertRaises(jev.JevError):
                jev.check_answers(out, q)

    def test_invalid_distribution(self):
        q = {"q": jev.choice("q", ["a", "b"])}
        bad = [{"choice": "a", "confidence": 0.5, "probabilities": {"a": 0.2}},
               {"choice": "c", "confidence": 0.5, "probabilities": {"a": 1.0}},
               {"choice": "a", "confidence": 0.5, "probabilities": {"a": 0.9, "zzz": 0.1}},
               {"choice": "a", "confidence": 1.5, "probabilities": {"a": 1.0}},
               {"choice": "a", "probabilities": {"a": 1.0}},
               {"choice": "a", "confidence": 0.5, "probabilities": {}},
               {"choice": "a", "confidence": 0.5, "probabilities": {"a": float("inf")}}]
        for answer in bad:
            with self.assertRaises(jev.JevError):
                jev.check_answers({"answers": {"q": answer}}, q)

    def test_choice_accepts_two_decimal_rounding(self):
        # Real answers are rounded to 2 decimals: 4 options summing to 0.99 are normal,
        # and 30 near-flat options can drift further. Those must pass.
        q4 = {"q": jev.choice("q", ["a", "b", "c", "d"])}
        jev.check_answers({"answers": {"q": {"choice": "a", "confidence": 0.9, "probabilities":
                                             {"a": 0.93, "b": 0.01, "c": 0.0, "d": 0.05}}}}, q4)
        labels = [f"n{i}.md" for i in range(30)]
        flat = {n: 0.03 for n in labels}          # true 1/30 each, rounded down: sum 0.90
        q30 = {"q": jev.choice("q", labels)}
        jev.check_answers({"answers": {"q": {"choice": "n0.md", "confidence": 0.1,
                                             "probabilities": flat}}}, q30)

    def test_unhashable_choice_is_jev_error(self):
        q = {"q": jev.choice("q", ["a", "b"])}
        for picked in (["a"], {"a": 1}, 1, None):
            with self.assertRaises(jev.JevError):
                jev.check_answers({"answers": {"q": {"choice": picked, "confidence": 0.5,
                                                     "probabilities": {"a": 1.0}}}}, q)

    def test_score_response(self):
        q = {"q": jev.score("q", ["low", "high"])}
        out = jev.check_answers({"answers": {"q": {"score": 0.5, "confidence": 0.1,
                                                   "probabilities": {"0": 0.5, "1": 0.5}}}}, q)
        self.assertEqual(out["answers"]["q"]["legend"], {"0": "low", "1": "high"})
        with self.assertRaises(jev.JevError):
            jev.check_answers({"answers": {"q": {"score": 1.5, "confidence": 0.1,
                                                 "probabilities": {"0": 0.5, "1": 0.5}}}}, q)
        with self.assertRaises(jev.JevError):
            jev.check_answers({"answers": {"q": {"score": 0.5, "confidence": 0.1,
                                                 "probabilities": {"0": 0.5, "2": 0.5}}}}, q)

    def test_bad_answer_raises_jev_error_not_key_error(self):
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"
        self.opener(body_of({"other": {"noul": 0.5}}))
        with self.assertRaises(jev.JevError):
            jev.ask("q", "s")


# --- public API shapes ---------------------------------------------------------

def choice_answer(probs: dict, pick_: str | None = None) -> dict:
    best = pick_ or max(probs, key=probs.get)
    return body_of({"q": {"type": "choice", "choice": best, "confidence": 0.7,
                          "probabilities": probs}})


class Shapes(Base):
    def setUp(self):
        super().setUp()
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"

    def test_system_one_body_extras(self):
        self.opener(NOUL_OK)
        out = jev.system_one("s", {"q": jev.noul("q")})
        self.assertEqual(out["answers"]["q"]["noul"], 0.8)
        self.assertEqual(out["_route"], "typesafe")
        self.assertIn("_seconds", out)
        self.assertAlmostEqual(out["_cost_usd"], 10 * jev.PRICE_PER_TOKEN)
        self.assertEqual(out["usage"]["output_tokens"], 2)

    def test_pick_shape(self):
        self.opener(choice_answer({"a": 0.2, "b": 0.8}))
        self.assertEqual(jev.pick("q", ["a", "b"], "s"), ("b", {"a": 0.2, "b": 0.8}, 0.7))

    def test_rank_single_chunk(self):
        self.opener(choice_answer({"a": 0.1, "b": 0.9}))
        self.assertEqual(jev.rank("q", {"a": "aa", "b": "bb"}), [("b", 0.9), ("a", 0.1)])

    def test_rank_large_is_chunked_with_final_round(self):
        names = [f"s{i}" for i in range(300)]
        cands = {n: f"desc {n}" for n in names}
        calls = []

        def fake_system_one(state, questions, model=None, timeout=30, retries=1, *, route=None):
            crit = questions["q"]["criteria"]
            calls.append(list(crit))
            probs = {n: 0.0 for n in crit}
            probs[next(iter(crit))] = 1.0
            return {"answers": {"q": {"probabilities": probs}}}

        with patch.object(jev, "system_one", side_effect=fake_system_one):
            ranking = jev.rank("q", cands)
        self.assertEqual([len(c) for c in calls], [255, 45, 20])
        self.assertTrue(all(len(c) <= 255 for c in calls))
        self.assertEqual(ranking[0], ("s0", 1.0))

    def test_rank_bad_label_fails_before_first_call(self):
        cands = {f"s{i}": "x" for i in range(300)}
        cands[""] = "blank label in the second chunk"
        with patch.object(jev, "system_one") as call, self.assertRaises(jev.JevError):
            jev.rank("q", cands)
        call.assert_not_called()

    def test_route_keyword_passes_through_helpers(self):
        os.environ["OPENROUTER_API_KEY"] = "fake-or-key"
        fake = self.opener(NOUL_OK, choice_answer({"a": 1.0}), choice_answer({"a": 1.0}))
        jev.ask("q", "s", route="openrouter")
        jev.pick("q", ["a"], "s", route="openrouter")
        jev.rank("q", {"a": "x"}, route="openrouter")
        self.assertTrue(all(c[0].full_url == jev.ROUTES["openrouter"][0] for c in fake.calls))


# --- CLI ------------------------------------------------------------------------

class Cli(Base):
    def setUp(self):
        super().setUp()
        os.environ["TYPESAFE_API_KEY"] = "fake-test-key"

    def run_cli(self, *argv, stdin: str = "") -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with patch.object(sys, "argv", ["jev_client.py", *argv]), \
                patch.object(sys, "stdin", io.StringIO(stdin)), \
                contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = jev.main()
        return code, out.getvalue(), err.getvalue()

    def test_ask_with_state_from_stdin(self):
        fake = self.opener(NOUL_OK)
        code, out, _ = self.run_cli("ask", "q?", "--yes", "да", "--state", "-", stdin="из stdin")
        self.assertEqual(code, 0)
        self.assertIn("да: 0.800", out)
        sent = json.loads(fake.calls[0][0].data)
        self.assertEqual(sent["state"], "из stdin")
        self.assertEqual(sent["questions"]["q"]["criteria"], {"true": "да"})

    def test_state_file_json_and_json_flag(self):
        f = self.tmp / "state.json"
        f.write_text('{"mail": "текст"}', encoding="utf-8")
        fake = self.opener(NOUL_OK)
        code, out, _ = self.run_cli("ask", "q?", "--state-file", str(f), "--json")
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["answers"]["q"]["noul"], 0.8)
        self.assertEqual(json.loads(fake.calls[0][0].data)["state"], {"mail": "текст"})

    def test_route_flag_before_and_after_subcommand(self):
        os.environ["OPENROUTER_API_KEY"] = "fake-or-key"
        fake = self.opener(NOUL_OK)
        self.run_cli("--route", "openrouter", "ask", "q?", "--state", "s")
        self.run_cli("ask", "q?", "--state", "s", "--route", "openrouter")
        self.assertEqual([c[0].full_url for c in fake.calls], [jev.ROUTES["openrouter"][0]] * 2)

    def test_raw(self):
        f = self.tmp / "req.json"
        f.write_text(json.dumps({"state": "s", "questions": {"q": {"type": "noul",
                                                                    "instructions": "i"}},
                                 "model": "jev-1.13.0"}), encoding="utf-8")
        fake = self.opener(NOUL_OK)
        code, out, _ = self.run_cli("raw", str(f))
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out)["_route"], "typesafe")
        self.assertEqual(json.loads(fake.calls[0][0].data)["model"], "jev-1.13.0")

    def test_raw_request_cannot_override_endpoint(self):
        f = self.tmp / "req.json"
        f.write_text(json.dumps({"state": "s", "url": "https://attacker.invalid/x",
                                 "questions": {"q": {"type": "noul", "instructions": "i"}}}),
                     encoding="utf-8")
        fake = self.opener(NOUL_OK)
        self.assertEqual(self.run_cli("raw", str(f))[0], 0)
        self.assertEqual(fake.calls[0][0].full_url, jev.ROUTES["typesafe"][0])

    def test_rank_candidates(self):
        f = self.tmp / "cands.json"
        f.write_text(json.dumps({"alpha": "первый", "beta": "второй"}), encoding="utf-8")
        self.opener(choice_answer({"alpha": 0.25, "beta": 0.75}))
        code, out, _ = self.run_cli("rank", "запрос", "--candidates", str(f))
        self.assertEqual(code, 0)
        self.assertEqual(out.split(), ["0.750", "beta", "0.250", "alpha"])

    def test_score_and_choose_output(self):
        self.opener(body_of({"q": {"type": "score", "score": 1.0, "confidence": 0.9,
                                   "legend": {"0": "low", "1": "high"},
                                   "probabilities": {"0": 0.0, "1": 1.0}}}),
                    choice_answer({"x": 0.6, "y": 0.4}))
        code, out, _ = self.run_cli("score", "q?", "low", "high", "--state", "s")
        self.assertEqual(code, 0)
        self.assertIn("1: high", out)
        code, out, _ = self.run_cli("choose", "q?", "x", "y", "--state", "s")
        self.assertIn("выбор: x", out)

    def test_errors_exit_2_without_secrets(self):
        self.opener(http_error(401, b"bad key"))
        code, _, err = self.run_cli("ask", "q?", "--state", "s")
        self.assertEqual(code, 2)
        self.assertIn("Jev HTTP 401", err)
        self.assertNotIn("fake-test-key", err)
        code, _, err = self.run_cli("choose", "q?", "a", "a", "--state", "s")
        self.assertEqual(code, 2)
        self.assertIn("unique", err)


if __name__ == "__main__":
    unittest.main(verbosity=2)
