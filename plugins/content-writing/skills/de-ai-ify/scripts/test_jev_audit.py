"""Offline tests for jev_audit.py: a stub stands in for the Jev client, nothing touches the network.

Run from this folder:  python -m unittest -v test_jev_audit
"""
import io
import json
import os
import socket
import subprocess
import sys
import tempfile
import unittest
import urllib.request
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jev_audit as ja  # noqa: E402

SCRIPT = os.path.join(HERE, "jev_audit.py")
TEXT = "Первый абзац про дело.\n\nВторой абзац про другое.\n\nТретий абзац про третье."


class FakeJev:
    """Same surface as jev_client that jev_audit uses: noul, system_one, JevError."""

    class JevError(RuntimeError):
        def __init__(self, status, body=""):
            super().__init__(f"Jev HTTP {status}: {body}")
            self.status = status

    def __init__(self, probs=None, cost=0.0002, fail=None):
        self.calls, self.stdout_at_call = [], []
        self.probs, self.cost, self.fail = probs or {}, cost, fail or {}

    def noul(self, instructions, yes=None, no=None):
        return {"type": "noul", "instructions": instructions, "criteria": {"true": yes, "false": no}}

    def system_one(self, state, questions, model=None, timeout=30, retries=1, route=None):
        self.stdout_at_call.append(sys.stdout.getvalue() if hasattr(sys.stdout, "getvalue") else "")
        self.calls.append({"state": state, "questions": questions, "model": model, "route": route})
        text = state.get("paragraph", state.get("reply", ""))
        if text in self.fail:
            raise self.JevError(*self.fail[text])
        answers = {k: {"type": "noul", "noul": self.probs.get((text, k), self.probs.get(k, 0.1))}
                   for k in questions}
        return {"model": "jev-1.13.0", "answers": answers, "_cost_usd": self.cost, "_route": "typesafe"}


def make_cfg(n=3, enabled=True, show_at=0.5, calibrated_model="jev-1.13.0"):
    return {"schema": 1, "model": "jev-1.13.0", "preamble": "PRE.",
            "state_defaults": {"audience": "AUD", "platform": "PLAT"},
            "calibration": {"status": "x", "model": calibrated_model},
            "questions": {f"p{i:02d}": {"label_ru": f"метка {i}", "ask": f"Ask {i}?", "yes": "y", "no": "n",
                                       "show_at": show_at, "enabled": enabled} for i in range(1, n + 1)}}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def write(self, name, data):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
        return path

    def run_main(self, args, fake=None, env=None):
        out, err = io.StringIO(), io.StringIO()
        client = fake or FakeJev()
        with redirect_stdout(out), redirect_stderr(err), \
                mock.patch.object(ja, "_load_client", return_value=client), \
                mock.patch.dict(os.environ, env or {}):
            code = ja.main(args)
        return code, out.getvalue(), err.getvalue(), client


class LocalOnlyByDefault(Base):
    def test_no_flags_means_no_network_and_no_client(self):
        path = self.write("t.txt", TEXT)

        def boom(*a, **k):
            raise AssertionError("network used without --jev")

        out = io.StringIO()
        with redirect_stdout(out), \
                mock.patch.object(ja, "_load_client", side_effect=AssertionError("client loaded")), \
                mock.patch.object(socket.socket, "connect", boom), \
                mock.patch.object(urllib.request, "urlopen", boom):
            code = ja.main([path])
        self.assertEqual(code, 0)
        self.assertIn("Jev: выключен", out.getvalue())

    def test_client_module_is_not_even_imported(self):
        path = self.write("t.txt", TEXT)
        code = ("import sys; sys.path.insert(0, %r); import jev_audit; jev_audit.main([%r]); "
                "print('IMPORTED=' + str('jev_client' in sys.modules))" % (HERE, path))
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertIn("IMPORTED=False", proc.stdout.decode("utf-8"))

    def test_linter_errors_give_exit_one_and_public_alone_changes_nothing(self):
        path = self.write("t.txt", "Метка turn0search3 осталась.")
        code, out, _, fake = self.run_main([path, "--public"])
        self.assertEqual(code, 1)
        self.assertIn("ERROR turn-marker", out)
        self.assertEqual(fake.calls, [])


class Refusals(Base):
    def test_jev_without_public_is_refused(self):
        path = self.write("t.txt", TEXT)
        with mock.patch.object(ja, "_load_client", side_effect=AssertionError("client loaded")):
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = ja.main([path, "--jev", "--questions", self.write("q.json", make_cfg())])
        self.assertEqual(code, 2)
        self.assertIn("--public", err.getvalue())

    def test_secret_shaped_text_is_never_sent(self):
        key = "sk-" + "A" * 24
        for body in (f"Мой ключ {key} лежит тут.", "pass" + "word: hunter2hunter2",
                     "-----BEGIN RSA " + "PRIVATE KEY-----", "123456789:" + "a" * 35):
            path = self.write("t.txt", body)
            code, out, err, fake = self.run_main(
                [path, "--jev", "--public", "--questions", self.write("q.json", make_cfg())])
            self.assertEqual(code, 2, body)
            self.assertEqual(fake.calls, [], body)
            self.assertNotIn(key, out + err)
            self.assertIn("секрет", err)

    def test_too_many_paragraphs(self):
        path = self.write("t.txt", "\n\n".join(f"Абзац номер {i} про дело." for i in range(5)))
        code, _, err, fake = self.run_main(
            [path, "--jev", "--public", "--max-paragraphs", "3", "--questions", self.write("q.json", make_cfg())])
        self.assertEqual(code, 2)
        self.assertEqual(fake.calls, [])
        self.assertIn("--max-paragraphs", err)

    def test_nothing_calibrated_means_no_call(self):
        path = self.write("t.txt", TEXT)
        q = self.write("q.json", make_cfg(enabled=False))
        code, out, _, fake = self.run_main([path, "--jev", "--public", "--questions", q])
        self.assertEqual(code, 0)
        self.assertEqual(fake.calls, [])
        self.assertIn("не откалиброван", out)
        code, out, _, fake = self.run_main([path, "--jev", "--public", "--include-uncalibrated", "--questions", q])
        self.assertEqual(len(fake.calls), 3)
        self.assertIn("неоткалиброванные", out)


class WhatIsSent(Base):
    def test_notice_is_printed_before_the_first_request(self):
        path = self.write("t.txt", TEXT)
        _, out, _, fake = self.run_main(
            [path, "--jev", "--public", "--workers", "1", "--questions", self.write("q.json", make_cfg())])
        self.assertTrue(fake.stdout_at_call)
        first = fake.stdout_at_call[0]
        self.assertIn("3 абз.", first)
        self.assertIn(f"{len(TEXT.replace(chr(10) * 2, ''))} зн.", first)
        self.assertIn("api.typesafe.ai (США)", first)

    def test_route_is_always_the_direct_api(self):
        path = self.write("t.txt", TEXT)
        _, _, _, fake = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", make_cfg())],
                                      env={"JEV_ROUTE": "openrouter"})
        self.assertTrue(all(c["route"] == "typesafe" for c in fake.calls))

    def test_state_has_paragraph_previous_audience_platform(self):
        path = self.write("t.txt", TEXT)
        _, _, _, fake = self.run_main(
            [path, "--jev", "--public", "--workers", "1", "--questions", self.write("q.json", make_cfg())])
        first, second = fake.calls[0]["state"], fake.calls[1]["state"]
        self.assertEqual(set(first), {"paragraph", "previous_paragraph", "audience", "platform"})
        self.assertEqual(first["previous_paragraph"], "")
        self.assertEqual(second["previous_paragraph"], "Первый абзац про дело.")
        self.assertEqual((first["audience"], first["platform"]), ("AUD", "PLAT"))
        _, _, _, fake = self.run_main(
            [path, "--jev", "--public", "--audience", "A2", "--platform", "P2", "--questions",
             self.write("q2.json", make_cfg())])
        self.assertTrue(all(c["state"]["audience"] == "A2" and c["state"]["platform"] == "P2" for c in fake.calls))

    def test_preamble_is_prepended_and_criteria_passed(self):
        path = self.write("t.txt", "Один абзац.")
        _, _, _, fake = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", make_cfg(1))])
        q = fake.calls[0]["questions"]["p01"]
        self.assertEqual(q["instructions"], "PRE. Ask 1?")
        self.assertEqual(q["criteria"], {"true": "y", "false": "n"})


class Limits(Base):
    def test_at_most_64_questions_per_request(self):
        path = self.write("t.txt", "Один абзац.")
        _, _, _, fake = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", make_cfg(70))])
        sizes = sorted(len(c["questions"]) for c in fake.calls)
        self.assertEqual(sizes, [6, 64])
        asked = [k for c in fake.calls for k in c["questions"]]
        self.assertEqual(len(asked), len(set(asked)), 70)

    def test_chunks_helper(self):
        self.assertEqual([len(c) for c in ja.chunks(list(range(130)))], [64, 64, 2])
        self.assertEqual(ja.chunks([]), [])

    def test_body_limit_is_exact(self):
        qs = {"p01": FakeJev().noul("Ask?", "y", "n")}
        state = ja.build_state("Короткий абзац.", "", "A", "P")
        size = ja.body_size(state, qs, "jev-1.13.0")
        self.assertTrue(ja.fits(state, qs, "jev-1.13.0", limit=size))
        self.assertFalse(ja.fits(state, qs, "jev-1.13.0", limit=size - 1))

    def test_constants_match_the_real_client(self):
        sys.path.insert(0, ja.CLIENT_DIR)
        try:
            import jev_client
        except ImportError:
            self.skipTest("jev_client is not on this machine")
        self.assertEqual(ja.MAX_QUESTIONS, jev_client.MAX_QUESTIONS)
        self.assertEqual(ja.MAX_BODY_BYTES, jev_client.MAX_BYTES)

    def test_oversized_paragraph_is_skipped_not_sent(self):
        big = "а" * (ja.MAX_PARAGRAPH_CHARS + 1)
        path = self.write("t.txt", f"Первый.\n\n{big}\n\nТретий.")
        code, out, _, fake = self.run_main(
            [path, "--jev", "--public", "--workers", "1", "--questions", self.write("q.json", make_cfg(2))])
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.calls), 2)
        self.assertTrue(all(len(c["state"]["paragraph"]) <= ja.MAX_PARAGRAPH_CHARS for c in fake.calls))
        self.assertIn("абзац 2: текст слишком длинный", out)

    def test_cost_cap_stops_new_requests(self):
        path = self.write("t.txt", "\n\n".join(f"Абзац {i} про дело." for i in range(6)))
        _, out, _, fake = self.run_main(
            [path, "--jev", "--public", "--workers", "1", "--max-cost", "0.0003", "--questions",
             self.write("q.json", make_cfg(2))], fake=FakeJev(cost=0.0002))
        self.assertEqual(len(fake.calls), 2)
        self.assertIn("остановлено по лимиту стоимости", out)


class Model(Base):
    def test_pinned_model_is_sent(self):
        path = self.write("t.txt", "Один абзац.")
        _, out, _, fake = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", make_cfg(1))])
        self.assertEqual(fake.calls[0]["model"], "jev-1.13.0")
        self.assertNotIn("откалиброваны на", out)

    def test_env_override_works_and_warns(self):
        path = self.write("t.txt", "Один абзац.")
        _, out, _, fake = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", make_cfg(1))],
                                        env={"JEV_MODEL": "jev-9.9.9"})
        self.assertEqual(fake.calls[0]["model"], "jev-9.9.9")
        self.assertIn("откалиброваны на jev-1.13.0, а идёт jev-9.9.9", out)


class Output(Base):
    def test_hints_at_or_above_show_at_only(self):
        path = self.write("t.txt", TEXT)
        probs = {("Первый абзац про дело.", "p01"): 0.93, ("Первый абзац про дело.", "p02"): 0.49,
                 ("Второй абзац про другое.", "p03"): 0.50}
        _, out, _, _ = self.run_main(
            [path, "--jev", "--public", "--questions", self.write("q.json", make_cfg())], fake=FakeJev(probs=probs))
        self.assertIn("абзац 1: p01 метка 1 (0.93)", out)
        self.assertIn("абзац 2: p03 метка 3 (0.50)", out)
        self.assertEqual([l for l in out.splitlines() if l.startswith("абзац") and "p02" in l], [])
        self.assertIn("подсказок 2", out)

    def test_per_question_show_at(self):
        cfg = make_cfg(2)
        cfg["questions"]["p02"]["show_at"] = 0.9
        path = self.write("t.txt", "Один абзац.")
        _, out, _, _ = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", cfg)],
                                     fake=FakeJev(probs={"p01": 0.6, "p02": 0.6}))
        self.assertIn("p01", out)
        self.assertNotIn("p02", out)

    def test_hints_never_change_exit_code(self):
        path = self.write("t.txt", "Один абзац.")
        code, _, _, _ = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", make_cfg(1))],
                                      fake=FakeJev(probs={"p01": 0.99}))
        self.assertEqual(code, 0)

    def test_json_has_no_text_and_never_overwrites(self):
        path = self.write("t.txt", TEXT)
        target = os.path.join(self.tmp.name, "out.json")
        args = [path, "--jev", "--public", "--json", target, "--questions", self.write("q.json", make_cfg())]
        code, _, _, _ = self.run_main(args)
        self.assertEqual(code, 0)
        with open(target, encoding="utf-8") as fh:
            raw = fh.read()
        for word in ("Первый абзац", "Второй абзац", "Третий абзац"):
            self.assertNotIn(word, raw)
        data = json.loads(raw)
        self.assertEqual(len(data["paragraphs"]), 3)
        self.assertEqual(len(data["paragraphs"][0]["sha1"]), 12)
        self.assertEqual(data["model_reported"], "jev-1.13.0")
        code, _, err, _ = self.run_main(args)
        self.assertEqual(code, 2)
        self.assertIn("--json", err)


class Failures(Base):
    def test_one_failed_paragraph_does_not_lose_the_rest(self):
        path = self.write("t.txt", TEXT)
        fake = FakeJev(probs={"p01": 0.9}, fail={"Второй абзац про другое.": (503, "busy")})
        code, out, _, _ = self.run_main(
            [path, "--jev", "--public", "--workers", "1", "--questions", self.write("q.json", make_cfg(1))], fake=fake)
        self.assertEqual(code, 0)
        self.assertIn("абзац 1: p01", out)
        self.assertIn("абзац 3: p01", out)
        self.assertIn("абзац 2: Jev недоступен", out)

    def test_access_error_stops_the_run(self):
        path = self.write("t.txt", TEXT)
        fake = FakeJev(fail={"Первый абзац про дело.": (401, "bad key")})
        code, out, _, _ = self.run_main(
            [path, "--jev", "--public", "--workers", "1", "--questions", self.write("q.json", make_cfg(1))], fake=fake)
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.calls), 1)
        self.assertIn("отказал в доступе (HTTP 401)", out)

    def test_client_that_cannot_load_keeps_the_linter_result(self):
        path = self.write("t.txt", TEXT)
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err), \
                mock.patch.object(ja, "_load_client", side_effect=ImportError("no client")):
            code = ja.main([path, "--jev", "--public", "--questions", self.write("q.json", make_cfg())])
        self.assertEqual(code, 0)
        self.assertIn("клиент не загрузился", out.getvalue())

    def test_broken_questions_file(self):
        path = self.write("t.txt", TEXT)
        for bad in ("{not json", json.dumps({"questions": {}}),
                    json.dumps({"questions": {"p01": {"ask": "a", "yes": "y", "no": "n", "show_at": 0}}})):
            code, _, err, fake = self.run_main([path, "--jev", "--public", "--questions", self.write("b.json", bad)])
            self.assertEqual(code, 2, bad)
            self.assertEqual(fake.calls, [])


def reply_cfg(n=2, enabled=True):
    cfg = make_cfg(n, enabled=enabled)
    cfg["unit"] = "reply"
    return cfg


class ReplyUnit(Base):
    """A questions file with "unit": "reply": the whole text is one reply, asked once."""

    def test_whole_text_goes_in_one_request_with_the_reply_key(self):
        path = self.write("t.txt", TEXT)
        code, out, _, fake = self.run_main(
            [path, "--jev", "--public", "--questions", self.write("q.json", reply_cfg())])
        self.assertEqual(code, 0)
        self.assertEqual(len(fake.calls), 1)
        state = fake.calls[0]["state"]
        self.assertEqual(set(state), {"reply", "audience", "platform"})
        self.assertEqual(state["reply"], TEXT)
        self.assertIn("Jev: ответ, ", out)
        self.assertIn("уйдёт в api.typesafe.ai (США)", out)

    def test_hints_say_reply_not_paragraph(self):
        path = self.write("t.txt", TEXT)
        _, out, _, _ = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", reply_cfg())],
                                     fake=FakeJev(probs={"p01": 0.9}))
        self.assertIn("ответ: p01 метка 1 (0.90)", out)
        self.assertNotIn("абзац 1:", out)

    def test_notice_comes_before_the_request_and_secrets_still_stop_it(self):
        path = self.write("t.txt", TEXT)
        _, _, _, fake = self.run_main([path, "--jev", "--public", "--workers", "1", "--questions",
                                       self.write("q.json", reply_cfg())])
        self.assertIn("уйдёт в api.typesafe.ai", fake.stdout_at_call[0])
        bad = self.write("s.txt", "ключ sk-" + "A" * 24)
        code, _, err, fake = self.run_main([bad, "--jev", "--public", "--questions", self.write("q2.json", reply_cfg())])
        self.assertEqual(code, 2)
        self.assertEqual(fake.calls, [])

    def test_unknown_unit_is_refused(self):
        cfg = make_cfg()
        cfg["unit"] = "page"
        path = self.write("t.txt", TEXT)
        code, _, err, fake = self.run_main([path, "--jev", "--public", "--questions", self.write("q.json", cfg)])
        self.assertEqual(code, 2)
        self.assertEqual(fake.calls, [])


class Paragraphs(unittest.TestCase):
    def test_splitting(self):
        text = ("# Заголовок\r\n\r\nПервый абзац\r\nв две строки.\r\n\r\n```\r\nкод\r\n\r\nещё код\r\n```\r\n\r\n"
                "---\r\n\r\n- пункт один\r\n- пункт два\r\n\r\nПоследний.")
        self.assertEqual(ja.split_paragraphs(text),
                         ["Первый абзац\nв две строки.", "- пункт один\n- пункт два", "Последний."])

    def test_empty_text(self):
        self.assertEqual(ja.split_paragraphs("  \n\n \n"), [])


class Shipped(unittest.TestCase):
    """The questions file that ships with the skill."""

    def test_file_loads_and_is_well_formed(self):
        cfg = ja.load_questions(ja.DEFAULT_QUESTIONS)
        self.assertTrue(14 <= len(cfg["questions"]) <= 16)
        for qid, q in cfg["questions"].items():
            self.assertTrue(q["ask"].rstrip().endswith("?"), qid)
            self.assertTrue(q["yes"] and q["no"], qid)
            self.assertIsInstance(q["enabled"], bool)
        self.assertTrue(cfg["preamble"])
        self.assertTrue(cfg["state_defaults"]["audience"] and cfg["state_defaults"]["platform"])

    def test_all_shipped_questions_fit_one_request_and_the_byte_limit_is_enforced(self):
        cfg = ja.load_questions(ja.DEFAULT_QUESTIONS)
        qs = ja.build_questions(FakeJev(), cfg, list(cfg["questions"]))
        self.assertLessEqual(len(qs), ja.MAX_QUESTIONS)
        defaults = cfg["state_defaults"]
        small = ja.build_state("Короткий абзац.", "", defaults["audience"], defaults["platform"])
        self.assertTrue(ja.fits(small, qs, cfg["model"]))
        # 30 000 four-byte characters pass the character cap but not the 128 000 byte limit
        wide = ja.build_state("😀" * ja.MAX_PARAGRAPH_CHARS, "", defaults["audience"], defaults["platform"])
        self.assertLessEqual(len(wide["paragraph"]), ja.MAX_PARAGRAPH_CHARS)
        self.assertGreater(ja.body_size(wide, qs, cfg["model"]), ja.MAX_BODY_BYTES)
        self.assertFalse(ja.fits(wide, qs, cfg["model"]))


if __name__ == "__main__":
    unittest.main()
