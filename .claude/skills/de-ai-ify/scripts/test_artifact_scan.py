"""Tests for artifact_scan.py on synthetic strings only.

Run from this folder:  python -m unittest -v test_artifact_scan
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
import artifact_scan as scan  # noqa: E402

SCRIPT = os.path.join(HERE, "artifact_scan.py")


def kinds(text):
    return {kind for _, kind, _ in scan.scan_text(text)}


class TextTraces(unittest.TestCase):
    def test_each_text_kind_fires(self):
        samples = {
            "oaicite": [
                "Рынок вырос :contentReference[oaicite:0]{index=0} за год.",
                "Цифра из отчёта oai_citation:3‡example.com.",
            ],
            "turn-marker": [
                "Источник turn0search3 в конце.",
                "Данные citeturn0news2turn1search7 ниже.",
                "Новый вид метки turn0product1 тоже след.",
            ],
            "chatbot-utm": [
                "См. https://example.com/a?utm_source=chatgpt.com",
                "См. https://example.com/a?utm_source=openai&x=1",
                "См. https://example.com/a?utm_source=copilot.com",
                "См. https://example.com/a?referrer=grok.com",
            ],
            "grok-card": ['Текст <grok-card data-id="1"> хвост.', "grok_card://42"],
            "gemini-cite": [
                "Цифра [cite: 8] из отчёта.",
                "[cite_start]Начало цитаты.",
                "Конец фразы [span_2].",
                "https://your-serveraisearch.cloud.google.com/grounding-api-redirect/AbC",
            ],
            "internal-footnote": [
                "Как сказано 【4†source】 выше.",
                "[отчёт](sandbox:/mnt/data/report.xlsx)",
            ],
            "think-tag": ["Ответ готов.</think>", "<thinking>план</thinking> Итог."],
            "perplexity-upload": ["https://ppl-ai-file-upload.s3.amazonaws.com/x.pdf"],
            "placeholder": [
                "Здравствуйте, [Ваше имя]!",
                "Задача: [Опишите задачу клиента].",
                "Привет, [имя клиента].",
                "Источник: INSERT_SOURCE_URL",
                "Ссылка: PASTE_ARTICLE_URL_HERE",
                "Дата релиза 2026-XX-XX.",
            ],
        }
        for kind, texts in samples.items():
            for text in texts:
                with self.subTest(kind=kind, text=text):
                    self.assertIn(kind, kinds(text))

    def test_owner_voice_is_not_a_trace(self):
        # Dashes, math signs, separators and typography are voice, not traces:
        # porting the candidate's hard errors for them was rejected by the owner.
        text = (
            "Агент — это LLM + OS + файловая память. Откликов 500+, "
            "диапазон 10–20 минут, A vs B, x ≈ 5, a = b.\n\n---\n\n"
            "«Ёлочки», неразрывный пробел и узкий пробел на месте.\n"
            "Дата 2026-10-03, ссылка [Ваш сайт](https://example.com), чек-бокс [ ] и [x].\n"
            "Честно? Скорее всего, сработает. Return to step 2."
        )
        self.assertEqual(scan.scan_text(text), [])

    def test_quoted_in_code_is_skipped(self):
        text = (
            "Метки `turn0search0` и `</think>` выдают копипаст.\n"
            "```\n"
            ":contentReference[oaicite:1]{index=1}\n"
            "Здравствуйте, [Ваше имя]!\n"
            "```\n"
            "~~~\n"
            "?utm_source=chatgpt.com\n"
            "~~~\n"
        )
        self.assertEqual(scan.scan_text(text), [])

    def test_line_numbers_survive_fenced_block(self):
        text = "Первая.\n```python\nx = 1\n```\nСсылка ?utm_source=chatgpt.com\n"
        self.assertEqual(scan.scan_text(text), [(5, "chatbot-utm", 1)])

    def test_crlf_and_count_per_line(self):
        text = "чисто\r\na turn0search1 b turn0search2\r\n"
        self.assertEqual(scan.scan_text(text), [(2, "turn-marker", 2)])


class InvisibleTraces(unittest.TestCase):
    def test_zero_width_flagged_even_in_code(self):
        self.assertIn("zero-width", kinds("Обычныйтекст."))
        self.assertIn("zero-width", kinds("Код `ab` тоже."))
        self.assertIn("zero-width", kinds("Склейка⁠слов."))

    def test_zwj_inside_emoji_is_normal(self):
        family = "Семья \U0001F468\U0001F469\U0001F467 на даче."
        heart = "Огонь ❤️\U0001F525 тоже."
        self.assertEqual(scan.scan_text(family + "\n" + heart), [])
        self.assertIn("zero-width", kinds("Словослово"))

    def test_bom_only_at_start_is_fine(self):
        self.assertEqual(scan.scan_text("Текст без следов."), [])
        self.assertIn("zero-width", kinds("Текстс BOM внутри."))

    def test_pua_marker(self):
        self.assertIn("pua-marker", kinds("Фактciteturn0search1."))
        self.assertNotIn("pua-marker", kinds("Значок  из иконочного шрифта."))


class Cli(unittest.TestCase):
    def run_main(self, args):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = scan.main(args)
        return code, out.getvalue(), err.getvalue()

    def write(self, folder, name, data):
        path = os.path.join(folder, name)
        with open(path, "wb") as fh:
            fh.write(data)
        return path

    def test_prints_kind_never_the_matched_text(self):
        secret = "tok_SECRET_4242"
        body = (
            f"Ссылка https://example.com/?utm_source=chatgpt.com&token={secret}\n"
            f"Заглушка [Вставьте ключ {secret}]\n"
        )
        with tempfile.TemporaryDirectory() as d:
            path = self.write(d, "draft.md", body.encode("utf-8"))
            code, out, err = self.run_main([path])
        self.assertEqual(code, 1)
        for leaked in (secret, "example.com", "Вставьте", "utm_source"):
            self.assertNotIn(leaked, out + err)
        self.assertIn(f"{path}:1: chatbot-utm - ", out)
        self.assertIn(f"{path}:2: placeholder - ", out)

    def test_file_is_left_untouched(self):
        data = "Текст turn0search1 иневидимка.\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as d:
            path = self.write(d, "post.md", data)
            before = os.stat(path).st_mtime_ns
            self.run_main([path])
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), data)
            self.assertEqual(os.stat(path).st_mtime_ns, before)

    def test_exit_codes(self):
        with tempfile.TemporaryDirectory() as d:
            clean = self.write(d, "clean.md", "Чистый текст — с тире.\n".encode("utf-8"))
            dirty = self.write(d, "dirty.md", b"<think>\n")
            latin1 = self.write(d, "latin1.md", b"QQZX\xe9 turn0search1\n")
            self.assertEqual(self.run_main([clean])[0], 0)
            self.assertEqual(self.run_main([dirty])[0], 1)
            code, out, err = self.run_main([latin1])
            self.assertEqual(code, 2)
            self.assertIn("UnicodeDecodeError", err)
            self.assertNotIn("QQZX", out + err)
            self.assertEqual(self.run_main([os.path.join(d, "missing.md")])[0], 2)
            self.assertEqual(self.run_main([d])[0], 2)

    def test_stdin_as_script(self):
        env = dict(os.environ, PYTHONIOENCODING="utf-8")
        proc = subprocess.run(
            [sys.executable, SCRIPT, "-"],
            input="Строка один.\nКонец</think>\n".encode("utf-8"),
            capture_output=True, env=env,
        )
        self.assertEqual(proc.returncode, 1)
        self.assertIn("<stdin>:2: think-tag - ", proc.stdout.decode("utf-8", "replace"))


if __name__ == "__main__":
    unittest.main()
