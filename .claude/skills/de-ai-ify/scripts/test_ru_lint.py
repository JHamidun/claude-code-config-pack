"""Tests for ru_lint.py on synthetic strings only (no network, no files of the owner).

Run from this folder:  python -m unittest -v test_ru_lint
"""
import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ru_lint as lint_mod  # noqa: E402

SCRIPT = os.path.join(HERE, "ru_lint.py")


def found(text, profile="user", level=None):
    return {(f.level, f.rule) for f in lint_mod.lint(text, profile) if level in (None, f.level)}


def rules(text, profile="user"):
    return {f.rule for f in lint_mod.lint(text, profile)}


class Profiles(unittest.TestCase):
    DASHES = "Привет — как дела — всё нормально — да. Дальше — больше — и ещё — раз."

    def test_unknown_profile_is_refused(self):
        with self.assertRaises(ValueError):
            lint_mod.lint("текст", "loose")

    def test_dashes_are_voice_in_default_profile(self):
        # the owner's own replies carry many dashes: no error, no warning in user
        self.assertEqual(found(self.DASHES, "user", "ERROR"), set())
        self.assertEqual(found(self.DASHES, "user", "WARN"), set())

    def test_dash_density_is_only_a_note(self):
        self.assertIn(("NOTE", "dash-density"), found(self.DASHES, "user"))

    def test_strict_makes_every_long_and_medium_dash_an_error(self):
        errs = [f for f in lint_mod.lint("Раз — два – три.", "strict") if f.rule == "dash"]
        self.assertEqual(len(errs), 2)
        self.assertTrue(all(f.level == "ERROR" for f in errs))

    def test_short_hyphen_is_not_an_error_even_in_strict(self):
        self.assertNotIn("dash", rules("Слово - слово, кто-то и по-русски.", "strict"))

    def test_math_signs_only_in_strict(self):
        text = "Рост 5+ часов, джуны vs сеньоры, LLM + OS."
        self.assertNotIn("math-sign", rules(text, "user"))
        self.assertIn("math-sign", rules(text, "strict"))

    def test_hr_in_body_only_in_strict_and_front_matter_is_skipped(self):
        text = "---\ntitle: x\n---\n\nАбзац про дело.\n\n---\n\nАбзац про другое."
        self.assertNotIn("hr-in-body", rules(text, "user"))
        hits = [f for f in lint_mod.lint(text, "strict") if f.rule == "hr-in-body"]
        self.assertEqual([f.line for f in hits], [7])


class FiguresOfSpeech(unittest.TestCase):
    def test_negative_parallelism_forms(self):
        for text in ("Это не просто инструмент, а философия.",
                     "Дело не в скорости, а в доверии.",
                     "Вопрос не в том, сколько стоит, а в том, что получишь.",
                     "Он не только считает, но и пишет.",
                     "Это не курс, это сообщество."):
            self.assertIn(("WARN", "negative-parallelism"), found(text), text)
            self.assertIn(("ERROR", "negative-parallelism"), found(text, "strict"), text)

    def test_cut_off_or_innocent_clauses_pass(self):
        for text in ("Он пришёл сюда не просто так.", "Он не просто это сделал.",
                     "Мы считаем не только по официальным данным.", "Он не только считает, но"):
            self.assertNotIn("negative-parallelism", rules(text), text)

    def test_quoted_figure_is_someone_elses_voice(self):
        text = "Он сказал: «Это не просто модель, а целая экосистема». Дальше шёл разбор."
        self.assertNotIn("negative-parallelism", rules(text, "strict"))

    def test_chopped_drama(self):
        self.assertIn(("WARN", "chopped-drama"), found("Без кода. Без настроек. Просто работает."))
        self.assertIn(("ERROR", "chopped-drama"), found("Без кода. Без настроек.", "strict"))


class SentencesAndParagraphs(unittest.TestCase):
    def test_same_verb_for_different_subjects_is_flagged(self):
        text = ("Первый сервис позволяет выгрузить отчёт за один клик. "
                "Второй сервис позволяет настроить рассылку без кода.")
        self.assertIn("verb-repeat", rules(text))

    def test_anaphora_for_rhythm_is_not(self):
        self.assertNotIn("verb-repeat", rules("Звонил. Звонил каждый день без перерыва и выходных."))

    def test_even_rhythm_needs_eight_sentences(self):
        seven = " ".join(["Это предложение содержит ровно семь слов подряд."] * 7)
        twelve = " ".join(["Это предложение содержит ровно семь слов подряд."] * 12)
        self.assertNotIn("even-rhythm", rules(seven))
        self.assertIn("even-rhythm", rules(twelve))

    def test_corridor_of_fifteen_to_twenty_two_words_is_even(self):
        s = "Мы вчера долго обсуждали с командой план работ на ближайший квартал и пришли к общему решению по срокам."
        self.assertTrue(15 <= len(s.split()) <= 22)
        self.assertIn("even-rhythm", rules(" ".join([s] * 8)))

    def test_no_short_sentences_needs_ten_sentences(self):
        long_s = "Мы вчера долго обсуждали с командой план работ на ближайший квартал и сроки."
        self.assertIn("no-short-sentences", rules(" ".join([long_s] * 10)))
        self.assertNotIn("no-short-sentences", rules(" ".join([long_s] * 9)))
        self.assertNotIn("no-short-sentences", rules(" ".join([long_s] * 9 + ["Работает."])))

    def test_uniform_paragraphs_need_five_of_five_words(self):
        para = "Мы обсудили план и согласовали сроки работ."
        same = "\n\n".join([para] * 5)
        varied = "\n\n".join([para, para + " " + para, "Ок, понял.", para * 3, para])
        self.assertIn("uniform-paragraphs", rules(same))
        self.assertNotIn("uniform-paragraphs", rules(varied))
        self.assertNotIn("uniform-paragraphs", rules("\n\n".join([para] * 4)))

    def test_lists_of_three(self):
        two_threes = "- а\n- б\n- в\n\nТекст.\n\n- г\n- д\n- е\n"
        three_and_four = "- а\n- б\n- в\n\nТекст.\n\n- г\n- д\n- е\n- ж\n"
        one_list = "- а\n- б\n- в\n"
        self.assertIn("lists-of-three", rules(two_threes))
        self.assertNotIn("lists-of-three", rules(three_and_four))
        self.assertNotIn("lists-of-three", rules(one_list))

    def test_bold_overuse_is_per_paragraph(self):
        self.assertIn("bold-overuse", rules("Тут **раз**, **два** и **три** акцента."))
        self.assertNotIn("bold-overuse", rules("Тут **раз** и **два** акцента."))

    def test_headings_lists_and_quotes_are_not_prose(self):
        text = "# Заголовок про дело и ещё слова\n\n> цитата про дело и ещё слова\n\n- пункт про дело и ещё слова\n"
        self.assertEqual(lint_mod.lint(text), [])


class ChatbotTraces(unittest.TestCase):
    def test_trace_is_an_error_in_both_profiles(self):
        for prof in ("user", "strict"):
            self.assertIn(("ERROR", "turn-marker"), found("Источник turn0search3 в конце.", prof))

    def test_zero_width_is_a_warning(self):
        self.assertIn(("WARN", "zero-width"), found("Невидимыйсимвол."))

    def test_quoted_trace_in_code_is_skipped(self):
        self.assertEqual(found("Метка `turn0search3` в коде."), set())

    def test_line_numbers_match_the_input(self):
        text = "Первая строка.\n\nВторая строка с turn0search3."
        self.assertEqual([f.line for f in lint_mod.lint(text) if f.rule == "turn-marker"], [3])

    def test_bom_and_crlf_do_not_shift_or_invent_findings(self):
        self.assertEqual(lint_mod.lint("Обычный текст.\r\n\r\nВторой абзац.\r\n"), [])


class OwnerVoiceIsClean(unittest.TestCase):
    """Short live-style replies: default profile stays silent (no errors, no warnings)."""

    REPLIES = [
        "Это да. И скорость перестройки ускоряется быстрее, чем мы успеваем её обсуждать.",
        "Нина, спасибо что заметила — Telegram съел линк. Поправил, теперь работает.\n\n"
        "Кстати, если будешь прогонять — попробуй сразу две версии: одно резюме под текущую роль, "
        "другое под смежную.",
        "Согласен по всей логике. Самый надёжный выключатель — выдернуть питание, и именно на это "
        "никто не пойдёт, потому что на том же канале деньги.",
    ]

    def test_no_errors_and_no_warnings(self):
        for text in self.REPLIES:
            bad = [f for f in lint_mod.lint(text) if f.level != "NOTE"]
            self.assertEqual(bad, [], text)


class Cli(unittest.TestCase):
    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = lint_mod.main(args)
        return code, out.getvalue(), err.getvalue()

    def write(self, folder, name, data):
        path = os.path.join(folder, name)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def test_exit_codes_and_file_untouched(self):
        with tempfile.TemporaryDirectory() as d:
            clean = self.write(d, "clean.md", "Обычный текст про дело.\n".encode("utf-8"))
            dirty = self.write(d, "dirty.md", "Источник turn0search3.\n".encode("utf-8"))
            with open(dirty, "rb") as fh:
                before = fh.read()
            self.assertEqual(self.run_main([clean])[0], 0)
            self.assertEqual(self.run_main([dirty])[0], 1)
            self.assertEqual(self.run_main([os.path.join(d, "missing.md")])[0], 2)
            self.assertEqual(self.run_main([d])[0], 2)
            bad = self.write(d, "bad.bin", b"\xff\xfe\x00\x01")
            self.assertEqual(self.run_main([bad])[0], 2)
            with open(dirty, "rb") as fh:
                self.assertEqual(fh.read(), before)

    def test_warnings_alone_exit_zero_and_strict_fails_on_dashes(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write(d, "t.md", "Раз — два.\n".encode("utf-8"))
            self.assertEqual(self.run_main([path])[0], 0)
            self.assertEqual(self.run_main([path, "--profile", "strict"])[0], 1)

    def test_notes_only_with_verbose(self):
        with tempfile.TemporaryDirectory() as d:
            path = self.write(d, "t.md", ("Привет — как дела — всё нормально — да.\n").encode("utf-8"))
            self.assertNotIn("NOTE", self.run_main([path])[1])
            self.assertIn("NOTE", self.run_main([path, "-v"])[1])

    def test_trace_text_is_never_printed(self):
        secret = "SECRETTOKEN123"
        with tempfile.TemporaryDirectory() as d:
            path = self.write(d, "t.md",
                              f"См. https://example.com/a?utm_source=chatgpt.com&k={secret}\n".encode("utf-8"))
            code, out, err = self.run_main([path])
            self.assertEqual(code, 1)
            self.assertIn("chatbot-utm", out)
            self.assertNotIn(secret, out + err)

    def test_stdin_as_script(self):
        proc = subprocess.run([sys.executable, SCRIPT, "-"], input="Метка turn0search3.\n".encode("utf-8"),
                              capture_output=True)
        self.assertEqual(proc.returncode, 1)
        self.assertIn("<stdin>:1: ERROR turn-marker", proc.stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
