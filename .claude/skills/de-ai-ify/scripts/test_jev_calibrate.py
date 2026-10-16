"""Offline tests for jev_calibrate.py: stub client, temporary corpus, nothing touches the network.

Run from this folder:  python -m unittest -v test_jev_calibrate
"""
import io
import json
import os
import re
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import jev_audit as ja  # noqa: E402
import jev_calibrate as jc  # noqa: E402
from test_jev_audit import FakeJev, make_cfg  # noqa: E402

EXAMPLES_MD = """# Библиотека

## TG. Первый ответ

**Анна:** «вопрос»

```text
Первый абзац ответа.

Второй абзац ответа.
```

## Что НЕ делать

### Анти-пример

```text
Плохой ответ, его считать нельзя.
```

## TG. Второй ответ

```text
Одна строка.
```
"""

CORPUS_JSON = {
    "live_extra": [{"id": "a01", "source": "x", "paragraphs": ["Проверенный живой ответ."]}],
    "machine": [{"id": "m01", "occasion": "x", "paragraphs": [
        {"text": "Машинный абзац один.", "patterns": ["p01"], "voice": ["compliment_open"]},
        {"text": "Машинный абзац два.", "patterns": ["p02"], "voice": ["hook_question"]}]}],
    "hard_negatives": [{"id": "h01", "near_miss": "p01", "text": "Почти паттерн, но нет."}],
}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.examples = self.write("examples.md", EXAMPLES_MD)
        self.corpus = self.write("corpus.json", CORPUS_JSON)
        patches = [mock.patch.object(jc, "EXAMPLES", self.examples), mock.patch.object(jc, "CORPUS", self.corpus)]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def write(self, name, data):
        path = os.path.join(self.tmp.name, name)
        with open(path, "w", encoding="utf-8", newline="") as fh:
            fh.write(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
        return path


class Corpus(Base):
    def test_live_blocks_skip_the_anti_examples(self):
        blocks = jc.live_blocks()
        self.assertEqual(blocks, ["Первый абзац ответа.\n\nВторой абзац ответа.", "Одна строка."])

    def test_paragraph_items(self):
        items = {i["id"]: i for i in jc.build_corpus("paragraph")}
        self.assertEqual(sorted(items), ["hard-h01", "live-a01-p1", "live-ex01-p1", "live-ex01-p2", "live-ex02-p1",
                                         "machine-m01-p1", "machine-m01-p2"])
        self.assertEqual(items["live-ex01-p2"]["previous"], "Первый абзац ответа.")
        self.assertEqual(items["live-ex01-p1"]["previous"], "")
        self.assertTrue(items["live-a01-p1"]["verified"])
        self.assertFalse(items["live-ex01-p1"]["verified"])
        self.assertEqual(items["machine-m01-p2"]["patterns"], ["p02"])
        self.assertEqual(items["hard-h01"]["near_miss"], "p01")
        self.assertEqual(len(items["live-ex01-p1"]["sha1"]), 12)

    def test_reply_items_join_paragraphs_and_union_labels(self):
        items = {i["id"]: i for i in jc.build_corpus("reply")}
        self.assertEqual(sorted(items), ["live-a01", "live-ex01", "live-ex02", "machine-m01"])
        self.assertEqual(items["live-ex01"]["text"], "Первый абзац ответа.\n\nВторой абзац ответа.")
        self.assertEqual(items["machine-m01"]["patterns"], ["p01", "p02"])
        self.assertEqual(items["machine-m01"]["voice"], ["compliment_open", "hook_question"])

    def test_shipped_corpus_has_enough_positives_for_every_shipped_question(self):
        sys.modules  # the real files, not the temporary ones
        with mock.patch.object(jc, "EXAMPLES", os.path.join(jc.SKILLS, "comment-replies", "references", "examples.md")), \
                mock.patch.object(jc, "CORPUS", os.path.join(ja.REFS, "jev-calibration-corpus.json")):
            if not os.path.exists(jc.EXAMPLES):
                self.skipTest("examples.md is not on this machine")
            items = jc.build_corpus("paragraph")
            cfg = ja.load_questions(ja.DEFAULT_QUESTIONS)
            for qid, q in cfg["questions"].items():
                n = sum(1 for it in items if jc._is_positive(it, qid, q))
                self.assertGreaterEqual(n, jc.MIN_POSITIVES, qid)
            self.assertGreaterEqual(sum(1 for it in items if it["kind"] == "live"), 50)


def raw_for(rows, show_at=None):
    """rows: [(kind, id, near_miss, {qid: p})] -> (items, raw_data) for metrics()."""
    items, data = [], {"show_at": show_at or {}, "items": {}, "model_reported": ["jev-1.13.0"], "date": "2026-10-04",
                       "spent_usd": 0.01, "requests": len(rows)}
    for kind, iid, near, answers, patterns in rows:
        items.append({"id": iid, "kind": kind, "verified": False, "patterns": patterns, "voice": [],
                      "near_miss": near, "text": iid, "previous": "", "sha1": "x" * 12})
        data["items"][iid] = {"sha1": "x" * 12, "kind": kind, "answers": answers, "cost": 0.0001}
    return items, data


def cfg_for(*qids):
    return {"questions": {q: {"label_ru": q, "ask": "a", "yes": "y", "no": "n", "show_at": 0.5, "enabled": False}
                          for q in qids}, "calibration": {}}


class Rule(unittest.TestCase):
    """The pre-registered rule: false <= 5% on live, hit >= 60% on labelled machine paragraphs, >= 5 of them."""

    def verdict(self, live_flagged, live_total, hit, positives, thr=0.5):
        rows = [("live", f"l{i}", None, {"p01": 0.9 if i < live_flagged else 0.1}, []) for i in range(live_total)]
        rows += [("machine", f"m{i}", None, {"p01": 0.9 if i < hit else 0.1}, ["p01"]) for i in range(positives)]
        items, data = raw_for(rows, {"p01": thr})
        return jc.metrics(cfg_for("p01"), items, data)["p01"]

    def test_exactly_five_percent_false_passes_and_six_fails(self):
        self.assertTrue(self.verdict(1, 20, 5, 5)["pass"])
        self.assertFalse(self.verdict(2, 20, 5, 5)["pass"])

    def test_exactly_sixty_percent_hit_passes_and_forty_fails(self):
        self.assertTrue(self.verdict(0, 20, 3, 5)["pass"])
        self.assertFalse(self.verdict(0, 20, 2, 5)["pass"])

    def test_too_few_positives_is_not_a_pass(self):
        r = self.verdict(0, 20, 4, 4)
        self.assertFalse(r["pass"])
        self.assertIn("мало данных", r["reason"])

    def test_threshold_is_inclusive(self):
        rows = [("live", "l0", None, {"p01": 0.5}, []), ("machine", "m0", None, {"p01": 0.5}, ["p01"])]
        items, data = raw_for(rows, {"p01": 0.5})
        r = jc.metrics(cfg_for("p01"), items, data)["p01"]
        self.assertEqual((r["false"], r["hit"]), ([1, 1], [1, 1]))

    def test_counts_split_by_kind(self):
        rows = [("live", "l1", None, {"p01": 0.9, "p02": 0.1}, []),
                ("live", "l2", None, {"p01": 0.1, "p02": 0.1}, []),
                ("machine", "m1", None, {"p01": 0.9, "p02": 0.9}, ["p01"]),
                ("machine", "m2", None, {"p01": 0.9, "p02": 0.1}, ["p02"]),
                ("hard_negative", "h1", "p01", {"p01": 0.9, "p02": 0.9}, []),
                ("hard_negative", "h2", "p02", {"p01": 0.1, "p02": 0.1}, [])]
        items, data = raw_for(rows, {"p01": 0.5, "p02": 0.5})
        m = jc.metrics(cfg_for("p01", "p02"), items, data)
        self.assertEqual(m["p01"]["false"], [1, 2])
        self.assertEqual(m["p01"]["hit"], [1, 1])
        self.assertEqual(m["p01"]["other_machine"], [1, 1])      # m2 fires p01 but does not carry it
        self.assertEqual(m["p01"]["hard_negative"], [1, 1])      # h1 only
        self.assertEqual(m["p02"]["hard_negative"], [0, 1])      # h2 only

    def test_runtime_thresholds_beat_the_current_file(self):
        rows = [("live", "l0", None, {"p01": 0.6}, []), ("machine", "m0", None, {"p01": 0.6}, ["p01"])]
        items, data = raw_for(rows, {"p01": 0.7})
        cfg = cfg_for("p01")
        cfg["questions"]["p01"]["show_at"] = 0.1
        self.assertEqual(jc.metrics(cfg, items, data)["p01"]["false"], [0, 1])

    def test_voice_spec_picks_field_value_and_verified_negatives(self):
        q = {"calibrate": {"field": "voice", "value": "compliment_open", "negatives": "verified"}}
        machine = {"kind": "machine", "voice": ["compliment_open"], "patterns": []}
        live_ok = {"kind": "live", "verified": True}
        live_other = {"kind": "live", "verified": False}
        self.assertTrue(jc._is_positive(machine, "v1", q))
        self.assertTrue(jc._is_negative(live_ok, q))
        self.assertFalse(jc._is_negative(live_other, q))
        self.assertTrue(jc._is_negative(live_other, {}))


class RunAndResume(Base):
    def cfg(self, n=2):
        return make_cfg(n)

    def raw(self, budget=0.30):
        path = os.path.join(self.tmp.name, "raw.json")
        cfg = self.cfg()
        return path, jc.Raw(path, "paragraph", "jev-1.13.0", {q: 0.5 for q in cfg["questions"]}, budget)

    def test_run_writes_probabilities_hashes_and_no_text(self):
        path, raw = self.raw()
        cfg, items = self.cfg(), jc.build_corpus("paragraph")
        fake = FakeJev(probs={"p01": 0.9})
        sent, skipped, failed = jc.run(cfg, items, list(cfg["questions"]), raw, fake, "jev-1.13.0", workers=1)
        self.assertEqual((sent, skipped, failed), (len(items), 0, 0))
        with open(path, encoding="utf-8") as fh:
            text = fh.read()
        for secret_text in ("Первый абзац ответа", "Машинный абзац", "Почти паттерн", "Проверенный живой"):
            self.assertNotIn(secret_text, text)
        data = json.loads(text)
        self.assertEqual(data["model_reported"], ["jev-1.13.0"])
        self.assertEqual(data["requests"], len(items))
        self.assertAlmostEqual(data["spent_usd"], 0.0002 * len(items))
        self.assertEqual(data["items"]["live-ex01-p1"]["answers"], {"p01": 0.9, "p02": 0.1})

    def test_state_matches_production(self):
        _, raw = self.raw()
        cfg, items = self.cfg(), jc.build_corpus("paragraph")
        fake = FakeJev()
        jc.run(cfg, items, list(cfg["questions"]), raw, fake, "jev-1.13.0", workers=1)
        second = next(c for c in fake.calls if c["state"]["paragraph"] == "Второй абзац ответа.")
        self.assertEqual(second["state"], ja.build_state("Второй абзац ответа.", "Первый абзац ответа.",
                                                         "AUD", "PLAT"))
        self.assertTrue(all(c["route"] == "typesafe" and c["model"] == "jev-1.13.0" for c in fake.calls))

    def test_resume_skips_finished_items(self):
        path, raw = self.raw()
        cfg, items = self.cfg(), jc.build_corpus("paragraph")
        jc.run(cfg, items[:3], list(cfg["questions"]), raw, FakeJev(), "jev-1.13.0", workers=1)
        raw2 = jc.Raw(path, "paragraph", "jev-1.13.0", {}, 0.30)
        fake = FakeJev()
        sent, _, _ = jc.run(cfg, items, list(cfg["questions"]), raw2, fake, "jev-1.13.0", workers=1)
        self.assertEqual(sent, len(items) - 3)
        self.assertEqual(len(fake.calls), len(items) - 3)
        self.assertEqual(raw2.data["requests"], len(items))

    def test_raw_of_another_model_is_never_mixed(self):
        path, raw = self.raw()
        raw.save()
        with self.assertRaises(SystemExit) as ctx:
            jc.Raw(path, "paragraph", "jev-2.0.0", {}, 0.30)
        self.assertIn("новый --raw", str(ctx.exception))

    def test_changed_text_is_asked_again(self):
        path, raw = self.raw()
        cfg, items = self.cfg(), jc.build_corpus("paragraph")
        jc.run(cfg, items[:1], list(cfg["questions"]), raw, FakeJev(), "jev-1.13.0", workers=1)
        changed = [dict(items[0], text="Другой текст.", sha1=jc._sha("Другой текст."))]
        fake = FakeJev()
        jc.run(cfg, changed, list(cfg["questions"]), jc.Raw(path, "paragraph", "jev-1.13.0", {}, 0.30), fake,
               "jev-1.13.0", workers=1)
        self.assertEqual(len(fake.calls), 1)

    def test_budget_is_never_exceeded(self):
        path, raw = self.raw(budget=0.0012)
        cfg, items = self.cfg(), jc.build_corpus("paragraph")
        fake = FakeJev(cost=0.0002)
        sent, skipped, _ = jc.run(cfg, items, list(cfg["questions"]), raw, fake, "jev-1.13.0", workers=1)
        self.assertLessEqual(raw.data["spent_usd"], 0.0012 + 1e-12)
        self.assertGreater(skipped, 0)
        self.assertEqual(sent + skipped, len(items))

    def test_failures_are_counted_and_do_not_stop_the_run(self):
        _, raw = self.raw()
        cfg, items = self.cfg(), jc.build_corpus("paragraph")
        fake = FakeJev(fail={"Одна строка.": (503, "busy")})
        sent, _, failed = jc.run(cfg, items, list(cfg["questions"]), raw, fake, "jev-1.13.0", workers=1)
        self.assertEqual(failed, 1)
        self.assertEqual(sent, len(items) - 1)

    def test_reply_unit_sends_the_whole_reply(self):
        path = os.path.join(self.tmp.name, "raw-reply.json")
        cfg = self.cfg(1)
        raw = jc.Raw(path, "reply", "jev-1.13.0", {"p01": 0.5}, 0.30)
        items = jc.build_corpus("reply")
        fake = FakeJev()
        jc.run(cfg, items, ["p01"], raw, fake, "jev-1.13.0", workers=1, unit="reply")
        first = next(c for c in fake.calls if c["state"]["reply"].startswith("Первый абзац"))
        self.assertEqual(first["state"]["reply"], "Первый абзац ответа.\n\nВторой абзац ответа.")
        self.assertNotIn("paragraph", first["state"])


class Cli(Base):
    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = jc.main(args)
        return code, out.getvalue(), err.getvalue()

    def questions(self, n=2):
        return self.write("q.json", make_cfg(n, enabled=False))

    def test_run_without_public_is_refused_before_any_client_call(self):
        with mock.patch.object(ja, "_load_client", side_effect=AssertionError("client loaded")):
            code, _, err = self.run_main(["run", "--questions", self.questions(),
                                          "--raw", os.path.join(self.tmp.name, "r.json")])
        self.assertEqual(code, 2)
        self.assertIn("--public", err)

    def test_run_refuses_secret_shaped_corpus(self):
        bad = dict(CORPUS_JSON, live_extra=[{"id": "a01", "source": "x", "paragraphs": ["ключ sk-" + "A" * 24]}])
        self.write("corpus.json", bad)
        with mock.patch.object(ja, "_load_client", side_effect=AssertionError("client loaded")):
            code, _, err = self.run_main(["run", "--public", "--questions", self.questions(),
                                          "--raw", os.path.join(self.tmp.name, "r.json")])
        self.assertEqual(code, 2)
        self.assertIn("секрет", err)

    def test_run_then_report_apply_end_to_end(self):
        q = self.questions(2)
        raw = os.path.join(self.tmp.name, "r.json")
        fake = FakeJev(probs={"p01": 0.9})
        with mock.patch.object(ja, "_load_client", return_value=fake):
            code, out, _ = self.run_main(["run", "--public", "--questions", q, "--raw", raw, "--workers", "1"])
        self.assertEqual(code, 0)
        self.assertIn("api.typesafe.ai (США)", out)
        code, out, _ = self.run_main(["report", "--questions", q, "--raw", raw])
        self.assertEqual(code, 0)
        self.assertIn("| p01 |", out)
        with open(q, encoding="utf-8") as fh:
            before = json.load(fh)
        self.assertFalse(any(x["enabled"] for x in before["questions"].values()))   # report alone writes nothing
        code, _, _ = self.run_main(["report", "--questions", q, "--raw", raw, "--apply"])
        with open(q, encoding="utf-8") as fh:
            after = json.load(fh)
        self.assertEqual({k: v["show_at"] for k, v in after["questions"].items()},
                         {k: v["show_at"] for k, v in before["questions"].items()})
        self.assertIn("мало данных", after["questions"]["p01"]["status"])   # the tiny corpus has too few positives
        self.assertFalse(after["questions"]["p01"]["enabled"])
        self.assertTrue(after["calibration"]["status"].startswith("not calibrated"))
        self.assertEqual(after["calibration"]["model"], "jev-1.13.0")

    def test_report_detects_a_changed_corpus(self):
        q = self.questions(1)
        raw = os.path.join(self.tmp.name, "r.json")
        with mock.patch.object(ja, "_load_client", return_value=FakeJev()):
            self.run_main(["run", "--public", "--questions", q, "--raw", raw, "--workers", "1"])
        with open(self.examples, "a", encoding="utf-8") as fh:
            fh.write("\n## TG. Третий\n\n```text\nНовый текст.\n```\n")
        self.write("examples.md", EXAMPLES_MD.replace("Одна строка.", "Другая строка."))
        code, _, err = self.run_main(["report", "--questions", q, "--raw", raw])
        self.assertEqual(code, 2)
        self.assertIn("Корпус изменился", err)


class AtomicWrite(Base):
    def test_retries_a_refused_replace_then_succeeds(self):
        target = os.path.join(self.tmp.name, "a.json")
        real = os.replace
        calls = []

        def flaky(src, dst):
            calls.append(1)
            if len(calls) <= 2:
                raise PermissionError("held by another process")
            return real(src, dst)

        with mock.patch.object(jc.os, "replace", flaky), mock.patch.object(jc.time, "sleep"):
            jc.write_atomic(target, "{}\n")
        self.assertEqual(len(calls), 3)
        with open(target, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), "{}\n")
        self.assertFalse(os.path.exists(target + ".tmp"))

    def test_falls_back_to_a_direct_write_when_replace_never_works(self):
        target = os.path.join(self.tmp.name, "b.json")
        with mock.patch.object(jc.os, "replace", side_effect=PermissionError("locked")), \
                mock.patch.object(jc.time, "sleep"):
            jc.write_atomic(target, '{"k": 1}\n')
        with open(target, encoding="utf-8") as fh:
            self.assertEqual(fh.read(), '{"k": 1}\n')
        self.assertFalse(os.path.exists(target + ".tmp"))


class ShippedFiles(unittest.TestCase):
    """The files that ship with the skill agree with each other and with their raw calibration data."""

    REAL_EXAMPLES = os.path.join(jc.SKILLS, "comment-replies", "references", "examples.md")

    def setUp(self):
        if not os.path.exists(self.REAL_EXAMPLES):
            self.skipTest("examples.md is not on this machine")
        patches = [mock.patch.object(jc, "EXAMPLES", self.REAL_EXAMPLES),
                   mock.patch.object(jc, "CORPUS", os.path.join(ja.REFS, "jev-calibration-corpus.json"))]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def check(self, questions_name, raw_names):
        cfg = ja.load_questions(os.path.join(ja.REFS, questions_name))
        unit = cfg["unit"]
        items = jc.build_corpus(unit)
        for raw_name in raw_names:
            with open(os.path.join(ja.REFS, raw_name), encoding="utf-8") as fh:
                raw = json.load(fh)
            self.assertEqual(raw["unit"], unit)
            self.assertEqual(raw["model_reported"], [cfg["model"]])
            self.assertEqual(raw["model_requested"], cfg["model"])
            # the raw file must still describe the corpus it was made from
            by_id = {i["id"]: i for i in items}
            for iid, rec in raw["items"].items():
                self.assertEqual(by_id[iid]["sha1"], rec["sha1"], iid)
            m = jc.metrics(cfg, items, raw)
            verdicts = {q: r["pass"] for q, r in m.items()}
            if raw_name == raw_names[0]:
                # enabled in the shipped file == the pre-registered rule applied to the raw data
                self.assertEqual({q: bool(v["enabled"]) for q, v in cfg["questions"].items()}, verdicts)
                self.assertEqual(raw["show_at"], {q: v["show_at"] for q, v in cfg["questions"].items()})
            else:
                # the replicate run reaches the same verdicts
                self.assertEqual(verdicts, {q: bool(v["enabled"]) for q, v in cfg["questions"].items()})
        self.assertEqual(cfg["calibration"]["model"], cfg["model"])
        for qid, q in cfg["questions"].items():
            self.assertEqual(q["status"] == "passed", q["enabled"], qid)
        return cfg

    def test_paragraph_questions_match_their_raw_runs(self):
        cfg = self.check("jev-questions.json", ["jev-calibration-raw.json", "jev-calibration-raw-run2.json"])
        self.assertTrue(any(q["enabled"] for q in cfg["questions"].values()))

    def test_voice_questions_match_their_raw_runs(self):
        cfg = self.check("jev-voice-questions.json",
                         ["jev-voice-calibration-raw.json", "jev-voice-calibration-raw-run2.json"])
        self.assertEqual(cfg["unit"], "reply")

    def test_voice_questions_have_enough_positives_and_no_verbatim_leak(self):
        cfg = ja.load_questions(os.path.join(ja.REFS, "jev-voice-questions.json"))
        items = jc.build_corpus("reply")
        for qid, q in cfg["questions"].items():
            positives = [it for it in items if jc._is_positive(it, qid, q)]
            self.assertGreaterEqual(len(positives), jc.MIN_POSITIVES, qid)
            examples = [x.strip("… .") for x in re.findall(r"«([^»]+)»", q["yes"])]
            for it in positives:
                for ex in examples:
                    self.assertNotIn(ex.lower(), it["text"].lower(), f"{qid}: example inside {it['id']}")


class ApplyToFile(Base):
    def test_enabled_follows_the_verdict_and_show_at_is_untouched(self):
        cfg = make_cfg(2, enabled=False, show_at=0.5)
        path = self.write("q.json", cfg)
        m = {"p01": {"show_at": 0.5, "false": [0, 20], "hit": [5, 6], "other_machine": [0, 1], "hard_negative": [0, 1],
                     "pass": True, "reason": "прошёл"},
             "p02": {"show_at": 0.5, "false": [3, 20], "hit": [5, 6], "other_machine": [0, 1], "hard_negative": [0, 1],
                     "pass": False, "reason": "ложных 3/20"}}
        raw = {"model_reported": ["jev-1.13.0"], "date": "2026-10-04", "spent_usd": 0.0123}
        jc.apply_to_file(path, cfg, m, raw)
        with open(path, encoding="utf-8") as fh:
            out = json.load(fh)
        self.assertTrue(out["questions"]["p01"]["enabled"])
        self.assertFalse(out["questions"]["p02"]["enabled"])
        self.assertEqual(out["questions"]["p01"]["status"], "passed")
        self.assertTrue(out["questions"]["p02"]["status"].startswith("failed"))
        self.assertEqual(out["questions"]["p01"]["show_at"], 0.5)
        self.assertEqual(out["calibration"]["status"], "calibrated: 1 of 2 questions passed")
        self.assertEqual(out["calibration"]["model"], "jev-1.13.0")
        self.assertEqual(ja.selected_ids(out), ["p01"])


if __name__ == "__main__":
    unittest.main()
