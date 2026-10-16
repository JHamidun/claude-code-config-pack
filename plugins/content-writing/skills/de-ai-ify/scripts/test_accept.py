"""Tests for accept.py on synthetic strings only (no network, no files of the owner).

Run from this folder:  python -m unittest -v test_accept
"""
import io
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import accept  # noqa: E402

OLD = ("На сегодняшний день наша платформа является удобным решением для 15 009 клиентов. "
       "Подробности по ссылке https://example.com/a?x=1 и в письме {NAME}. "
       "Один из клиентов сказал: «это сэкономило нам неделю работы».")
NEW = ("Наша платформа — удобное решение для 15 009 клиентов. "
       "Подробности по ссылке https://example.com/a?x=1 и в письме {NAME}. "
       "Один из клиентов сказал: «это сэкономило нам неделю работы».")


def verdict(old, new, **kw):
    reasons, notes = accept.check(old, new, **kw)
    return reasons, notes


class Preserved(unittest.TestCase):
    def test_good_edit_is_accepted(self):
        reasons, _ = verdict(OLD, NEW)
        self.assertEqual(reasons, [])

    def test_number_lost_or_added(self):
        self.assertTrue(any("числа" in r for r in verdict(OLD, NEW.replace("15 009", "15 000"))[0]))
        self.assertTrue(any("числа" in r for r in verdict(OLD, NEW + " Уже 3 года.")[0]))

    def test_number_spelling_is_not_a_change(self):
        reasons, _ = verdict("Цена 1 000 рублей, рост 4,8 раза.", "Цена 1000 рублей, рост 4.8 раза.",
                             min_ratio=0.0)
        self.assertEqual([r for r in reasons if "числа" in r], [])

    def test_numbers_inside_links_are_not_numbers(self):
        reasons, _ = verdict("Смотри https://example.com/a?id=5 тут.", "Смотри https://example.com/a?id=5 тут же.",
                             min_ratio=0.0, max_ratio=2.0)
        self.assertEqual(reasons, [])

    def test_placeholder_lost_but_reorder_is_fine(self):
        self.assertTrue(any("плейсхолдеры" in r for r in verdict(OLD, NEW.replace("{NAME}", "клиент"))[0]))
        reasons, _ = verdict("Для {A} и {B} готово.", "Готово для {B} и {A}.", min_ratio=0.0)
        self.assertEqual(reasons, [])

    def test_tags_must_keep_order(self):
        old = "<p>Привет <b>мир</b> и <i>все</i> люди вокруг.</p>"
        self.assertEqual(verdict(old, "<p>Привет <b>мир</b> и <i>все</i> вокруг.</p>", min_ratio=0.0)[0], [])
        reasons, _ = verdict(old, "<p>Привет <i>все</i> и <b>мир</b> вокруг.</p>", min_ratio=0.0)
        self.assertTrue(any("html" in r for r in reasons))

    def test_link_changed(self):
        reasons, _ = verdict(OLD, NEW.replace("example.com/a?x=1", "example.com/b"))
        self.assertTrue(any("ссылки" in r for r in reasons))

    def test_link_with_trailing_punctuation_is_the_same_link(self):
        reasons, _ = verdict("Вот ссылка https://example.com/a. Всё.", "Вот: https://example.com/a, всё.",
                             min_ratio=0.0)
        self.assertEqual([r for r in reasons if "ссылки" in r], [])

    def test_quotation_must_stay_verbatim_but_scare_quotes_may_go(self):
        reasons, _ = verdict(OLD, NEW.replace("сэкономило нам неделю работы", "сэкономило неделю"))
        self.assertTrue(any("цитаты" in r for r in reasons))
        reasons, _ = verdict("Это «умный» подход к делу сегодня.", "Это умный подход к делу.", min_ratio=0.0)
        self.assertEqual([r for r in reasons if "цитаты" in r], [])


class LengthAndChange(unittest.TestCase):
    def test_lower_and_upper_bounds(self):
        old = "слово " * 100
        self.assertTrue(any("нижний" in r for r in verdict(old, "слово " * 50)[0]))
        self.assertEqual(verdict(old, "слово " * 65)[0], [])
        self.assertTrue(any("предел" in r for r in verdict(old, "слово " * 110)[0]))

    def test_micro_drops_the_lower_bound(self):
        old = "Нажмите кнопку, чтобы продолжить оформление заказа"
        self.assertTrue(any("нижний" in r for r in verdict(old, "Продолжить")[0]))
        self.assertEqual(verdict(old, "Продолжить", min_ratio=0.0)[0], [])

    def test_unchanged_text_is_accepted_with_a_note(self):
        reasons, notes = verdict("Текст чистый, цифры на месте: 4.", "Текст чистый, цифры на месте: 4.")
        self.assertEqual(reasons, [])
        self.assertIn("без изменений", notes)
        reasons, _ = verdict("Текст чистый, цифры на месте: 4.", "Текст чистый, цифры на месте: 4.",
                             require_change=True)
        self.assertEqual(reasons, ["без изменений"])

    def test_empty_inputs(self):
        self.assertEqual(verdict("", "текст")[0], ["исходный текст пуст"])
        self.assertEqual(verdict("текст", "  ")[0], ["правка пуста"])


class Cliches(unittest.TestCase):
    def test_new_cliche_is_rejected(self):
        reasons, _ = verdict("Платформа помогает команде работать быстрее.",
                             "Платформа является помощником команды в работе.", min_ratio=0.0)
        self.assertTrue(any("штампы" in r for r in reasons))

    def test_leftover_is_a_note_unless_asked(self):
        old = "Платформа является помощником команды в работе и экономит время."
        new = "Платформа является помощником команды и экономит время."
        reasons, notes = verdict(old, new, min_ratio=0.0)
        self.assertEqual(reasons, [])
        self.assertTrue(any("остались" in n for n in notes))
        reasons, _ = verdict(old, new, min_ratio=0.0, no_leftovers=True)
        self.assertTrue(any("остались" in r for r in reasons))

    def test_cliche_inside_a_quotation_is_not_counted(self):
        old = "Он сказал: «на сегодняшний день всё является сложным» и ушёл."
        reasons, notes = verdict(old, old.replace("и ушёл", "и вышел"), min_ratio=0.0)
        self.assertEqual(reasons, [])
        self.assertEqual(notes, [])

    def test_plural_data_is_not_the_cliche_dannyy(self):
        reasons, _ = verdict("Взяли отчёт по продажам.", "Взяли данные по продажам.", min_ratio=0.0)
        self.assertEqual([r for r in reasons if "штампы" in r], [])


class Profiles(unittest.TestCase):
    def test_chatbot_trace_left_in_the_edit_is_rejected(self):
        old = "Рынок вырос turn0search3 за год заметно."
        reasons, _ = verdict(old, "Рынок вырос turn0search3 за год.", min_ratio=0.0)
        self.assertTrue(any("turn-marker" in r for r in reasons))
        self.assertEqual(verdict(old, "Рынок вырос за год.", min_ratio=0.0)[0], [])

    def test_dash_is_fine_by_default_and_an_error_in_strict(self):
        old = "Рынок вырос за год заметно и быстро."
        new = "Рынок вырос за год — заметно и быстро."
        self.assertEqual(verdict(old, new, min_ratio=0.0, max_ratio=2.0)[0], [])
        reasons, _ = verdict(old, new, profile="strict", min_ratio=0.0, max_ratio=2.0)
        self.assertTrue(any("dash" in r for r in reasons))


class Cli(unittest.TestCase):
    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = accept.main(args)
        return code, out.getvalue(), err.getvalue()

    def test_exit_codes_and_no_text_in_output(self):
        secret = "SECRETTOKEN123"
        with tempfile.TemporaryDirectory() as d:
            old = os.path.join(d, "old.txt")
            new = os.path.join(d, "new.txt")
            with open(old, "w", encoding="utf-8") as fh:
                fh.write(f"Платформа помогает команде 15 раз, ключ {secret} внутри.")
            with open(new, "w", encoding="utf-8") as fh:
                fh.write(f"Платформа помогает команде 16 раз, ключ {secret} внутри.")
            code, out, err = self.run_main([old, new])
            self.assertEqual(code, 1)
            self.assertIn("REJECT числа", out)
            self.assertNotIn(secret, out + err)
            self.assertEqual(self.run_main([old, old])[0], 0)
            self.assertEqual(self.run_main([old, os.path.join(d, "missing.txt")])[0], 2)
            self.assertEqual(self.run_main(["-", "-"])[0], 2)

    def test_micro_flag(self):
        with tempfile.TemporaryDirectory() as d:
            old = os.path.join(d, "old.txt")
            new = os.path.join(d, "new.txt")
            with open(old, "w", encoding="utf-8") as fh:
                fh.write("Нажмите кнопку, чтобы продолжить оформление заказа")
            with open(new, "w", encoding="utf-8") as fh:
                fh.write("Продолжить")
            self.assertEqual(self.run_main([old, new])[0], 1)
            self.assertEqual(self.run_main([old, new, "--micro"])[0], 0)


if __name__ == "__main__":
    unittest.main()
