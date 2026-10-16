"""Tests for gen_commands.py on synthetic client sources.

    python -m unittest test_gen_commands -v            # hermetic suite
    GEN_COMMANDS_REAL=1 python -m unittest test_gen_commands -v
        # plus a cross-check on real clients (read-only parse): ~/.claude/tools/tg_client.py by default,
        # or GEN_COMMANDS_CLIENTS=<path>[<os.pathsep><path>...] for your own

The synthetic sources are parsed, never executed: one of them would write a
sentinel file and abort if it ever ran.
"""

import json
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen_commands as gc  # noqa: E402  (our own script, not a target client)

SCRIPT = HERE / "gen_commands.py"


def src(text):
    return textwrap.dedent(text).lstrip()


def by_name(walker):
    return {" ".join(c.path): c for c in walker.commands}


def usages(cmd):
    return [gc.render_arg(a) for a in cmd.args if not a.hidden]


FLAT = src('''
    import argparse
    import asyncio

    def cmd_dialogs(client, args):
        pass

    async def main():
        parser = argparse.ArgumentParser(description="Demo CLI")
        parser.add_argument("--phone", default="", help="override phone")
        sub = parser.add_subparsers(dest="command")

        p = sub.add_parser("dialogs", help="List recent dialogs")
        p.add_argument("--limit", type=int, default=30)
        p.set_defaults(func=cmd_dialogs)

        p = sub.add_parser("send", help="Send a message | with a pipe")
        p.add_argument("target", help="chat id")
        p.add_argument("text", nargs="+")
        p.add_argument("--silent", action="store_true")
        p.add_argument("--mode", choices=["md", "html"], default="md")
        p.add_argument("--debug", help=argparse.SUPPRESS)

        sub.add_parser("folders", help="List folders")

        p = sub.add_parser("broadcast", help="Send to many", aliases=["bc"])
        p.add_argument("--targets", nargs="+", required=True)
        p.add_argument("--delay", type=float, default=2.0)

        args = parser.parse_args()

    if __name__ == "__main__":
        asyncio.run(main())
''')

NESTED = src('''
    import argparse

    def build_parser():
        parser = argparse.ArgumentParser(prog="tool")
        sub = parser.add_subparsers(dest="cmd", required=True)

        cfg = sub.add_parser("config", help="Manage config")
        cfg_sub = cfg.add_subparsers(dest="config_cmd")
        get = cfg_sub.add_parser("get", help="Read a value")
        get.add_argument("key")
        put = cfg_sub.add_parser("set", help="Write a value")
        put.add_argument("key")
        put.add_argument("value")

        remote = sub.add_parser("remote", help="Remotes")
        remote_sub = remote.add_subparsers()
        add = remote_sub.add_parser("add", help="Add a remote")
        add_sub = add.add_subparsers()
        origin = add_sub.add_parser("origin", help="Third level")
        origin.add_argument("--force", action="store_true")
        return parser

    def main():
        args = build_parser().parse_args()

    if __name__ == "__main__":
        main()
''')

HELPERS = src('''
    import argparse

    def add_common(p, json_default=False):
        p.add_argument("--json", action="store_true", default=json_default)
        p.add_argument("--limit", type=int, default=20)

    def command(sub, name, help_text, *, paid=False):
        p = sub.add_parser(name, help=help_text)
        add_common(p)
        if paid:
            p.add_argument("--yes", action="store_true", help="confirm a paid action")
        return p

    def build():
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers(dest="cmd")
        lst = command(sub, "list", "List items")
        lst.add_argument("--all", action="store_true")
        command(sub, "recalc", "Reissue (paid)", paid=True)
        grp = command(sub, "admin", "Admin tools")
        grp_sub = grp.add_subparsers()
        command(grp_sub, "purge", "Delete everything")
        return parser
''')

LOOPS = src('''
    import argparse

    SIMPLE = [("ping", "Check the session"), ("whoami", "Show the account")]
    WITH_ID = {"invoice": "Download an invoice", "confirm": "Mark paid"}

    def main():
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        for name, help_text in SIMPLE:
            sub.add_parser(name, help=help_text)
        for name, help_text in WITH_ID.items():
            p = sub.add_parser(name, help=help_text)
            p.add_argument("id")
        common = argparse.ArgumentParser(add_help=False)
        common.add_argument("--json", action="store_true")
        sub.add_parser("doctor", help="Check access", parents=[common])

    main()
''')

CLASS_BASED = src('''
    import argparse

    class CLI:
        def __init__(self):
            self.parser = argparse.ArgumentParser()
            self.sub = self.parser.add_subparsers()
            self._register()

        def _register(self):
            p = self.sub.add_parser("status", help="Show status")
            p.add_argument("--verbose", action="store_true")
''')

UNRESOLVED = src('''
    import argparse

    def names():
        return load_from_somewhere()

    def main():
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_parser("known", help="Resolved fine")
        for n in names():
            sub.add_parser(n)
        later = [lambda s: s.add_parser("ghost")]

    main()
''')

# No __main__ guard (a console_scripts entry point): both functions build a
# parser, so each is walked as an entry and build_parser is reached twice.
TWO_ENTRIES = src('''
    import argparse

    def build_parser():
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        p = sub.add_parser("one", help="First")
        p.add_argument("--json", action="store_true")
        return parser

    def main():
        common = argparse.ArgumentParser(add_help=False)
        parser = build_parser()
        return parser.parse_args()
''')

NO_SUBCOMMANDS = src('''
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
''')


def sentinel_source(sentinel):
    return src(f'''
        import pathlib
        pathlib.Path({str(sentinel)!r}).write_text("executed")
        raise SystemExit("this file must never run")
        import argparse
        parser = argparse.ArgumentParser()
        sub = parser.add_subparsers()
        sub.add_parser("safe", help="Parsed, not run")
    ''')


class FlatTests(unittest.TestCase):
    def setUp(self):
        self.w = gc.extract(FLAT)
        self.cmds = by_name(self.w)

    def test_names_in_source_order(self):
        self.assertEqual([" ".join(c.path) for c in self.w.commands],
                         ["dialogs", "send", "folders", "broadcast"])

    def test_reused_variable_gets_its_own_arguments(self):
        self.assertEqual(usages(self.cmds["dialogs"]), ["[--limit=30]"])
        self.assertEqual(usages(self.cmds["send"]),
                         ["target", "text…", "[--silent]", "[--mode {md,html}=md]"])
        self.assertEqual(usages(self.cmds["folders"]), [])
        self.assertEqual(usages(self.cmds["broadcast"]), ["--targets …", "[--delay=2.0]"])

    def test_help_aliases_handler_and_globals(self):
        self.assertEqual(self.cmds["dialogs"].help, "List recent dialogs")
        self.assertEqual(self.cmds["broadcast"].aliases, ["bc"])
        self.assertEqual(self.cmds["dialogs"].handler, "cmd_dialogs")
        self.assertEqual([gc.render_arg(a) for a in self.w.global_args()], ["[--phone …]"])

    def test_suppressed_argument_is_hidden(self):
        hidden = [a for a in self.cmds["send"].args if a.hidden]
        self.assertEqual([a.flags for a in hidden], [["--debug"]])

    def test_markdown_escapes_pipes_and_lists_aliases(self):
        md = gc.render_markdown(self.w)
        self.assertIn("Send a message \\| with a pipe", md)
        self.assertIn("| `broadcast` (`bc`) |", md)
        self.assertIn("Общие флаги", md)
        self.assertEqual(md.count("\n| `"), 4)

    def test_no_warnings_and_full_reach(self):
        st = self.w.stats()
        self.assertEqual(self.w.warnings, [])
        self.assertEqual(st["add_parser_calls_in_file"], 4)
        self.assertEqual(st["add_parser_calls_reached"], 4)


class NestedTests(unittest.TestCase):
    def setUp(self):
        self.w = gc.extract(NESTED)
        self.cmds = by_name(self.w)

    def test_paths_of_sub_subparsers(self):
        self.assertEqual(list(self.cmds), ["config", "config get", "config set",
                                           "remote", "remote add", "remote add origin"])

    def test_groups_and_leaves(self):
        groups = {n for n, c in self.cmds.items() if c.has_sub}
        self.assertEqual(groups, {"config", "remote", "remote add"})
        self.assertEqual(usages(self.cmds["config set"]), ["key", "value"])
        self.assertEqual(usages(self.cmds["remote add origin"]), ["[--force]"])

    def test_counts(self):
        self.assertEqual(len(self.w.commands), 6)
        self.assertEqual(self.w.warnings, [])
        st = self.w.stats()
        self.assertEqual((st["top_level"], st["nested"], st["groups"]), (2, 4, 3))

    def test_builder_reached_twice_is_not_duplicated(self):
        w = gc.extract(TWO_ENTRIES)
        self.assertEqual([" ".join(c.path) for c in w.commands], ["one"])
        self.assertEqual(usages(w.commands[0]), ["[--json]"])
        self.assertEqual(w.warnings, [])


class HelperTests(unittest.TestCase):
    def setUp(self):
        self.w = gc.extract(HELPERS)
        self.cmds = by_name(self.w)

    def test_parser_created_inside_helper(self):
        self.assertEqual(list(self.cmds), ["list", "recalc", "admin", "admin purge"])
        self.assertEqual(self.cmds["recalc"].help, "Reissue (paid)")

    def test_arguments_from_helpers_and_caller(self):
        self.assertEqual(usages(self.cmds["list"]), ["[--json]", "[--limit=20]", "[--all]"])
        self.assertEqual(usages(self.cmds["admin purge"]), ["[--json]", "[--limit=20]"])

    def test_known_condition_takes_one_branch(self):
        self.assertIn("[--yes]", usages(self.cmds["recalc"]))
        self.assertNotIn("[--yes]", usages(self.cmds["list"]))
        self.assertNotIn("[--yes]", usages(self.cmds["admin"]))

    def test_nested_group_built_through_helper(self):
        self.assertTrue(self.cmds["admin"].has_sub)
        self.assertEqual(self.cmds["admin purge"].path, ("admin", "purge"))
        self.assertFalse(any(c.loose for c in self.w.commands))
        self.assertEqual(self.w.warnings, [])


class LoopAndParentsTests(unittest.TestCase):
    def test_loops_over_literals_and_parents(self):
        w = gc.extract(LOOPS)
        cmds = by_name(w)
        self.assertEqual(list(cmds), ["ping", "whoami", "invoice", "confirm", "doctor"])
        self.assertEqual(cmds["whoami"].help, "Show the account")
        self.assertEqual(usages(cmds["invoice"]), ["id"])
        self.assertEqual(usages(cmds["doctor"]), ["[--json]"])
        self.assertEqual(w.global_args(), [])
        self.assertEqual(w.warnings, [])


class ClassBasedTests(unittest.TestCase):
    def test_state_on_self_survives_method_calls(self):
        w = gc.extract(CLASS_BASED)
        cmds = by_name(w)
        self.assertEqual(list(cmds), ["status"])
        self.assertFalse(cmds["status"].loose)
        self.assertEqual(usages(cmds["status"]), ["[--verbose]"])


class GapTests(unittest.TestCase):
    def test_unresolved_name_and_unreached_call_are_reported(self):
        w = gc.extract(UNRESOLVED)
        names = [" ".join(c.path) for c in w.commands]
        self.assertEqual(names, ["known", "<?>"])
        messages = " ".join(x["message"] for x in w.warnings)
        self.assertIn("не вычисляется статически", messages)
        ghost_line = UNRESOLVED.splitlines().index(
            '    later = [lambda s: s.add_parser("ghost")]') + 1
        self.assertIn(ghost_line, [x["line"] for x in w.warnings])
        st = w.stats()
        self.assertEqual((st["add_parser_calls_in_file"], st["add_parser_calls_reached"]), (3, 2))


class NeverExecutedTests(unittest.TestCase):
    def test_target_source_is_parsed_not_run(self):
        with tempfile.TemporaryDirectory() as tmp:
            sentinel = Path(tmp) / "SENTINEL"
            w = gc.extract(sentinel_source(sentinel))
            self.assertEqual([" ".join(c.path) for c in w.commands], ["safe"])
            self.assertFalse(sentinel.exists(), "the target file was executed")


class CliTests(unittest.TestCase):
    def run_cli(self, source, *flags):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / "client.py"
            target.write_text(source, encoding="utf-8")
            sentinel = Path(tmp) / "SENTINEL"
            proc = subprocess.run([sys.executable, str(SCRIPT), str(target), *flags],
                                  capture_output=True, text=True, encoding="utf-8")
            self.assertFalse(sentinel.exists())
            return proc

    def test_markdown_to_stdout_summary_to_stderr(self):
        proc = self.run_cli(NESTED)
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertTrue(proc.stdout.startswith("| Команда | Что делает | Аргументы |"))
        self.assertIn("`remote add origin`", proc.stdout)
        self.assertIn("команд 6", proc.stderr)

    def test_json_is_parseable(self):
        proc = self.run_cli(HELPERS, "--json")
        self.assertEqual(proc.returncode, 0, proc.stderr)
        data = json.loads(proc.stdout)
        self.assertEqual([c["name"] for c in data["commands"]],
                         ["list", "recalc", "admin", "admin purge"])
        self.assertEqual(data["stats"]["commands"], 4)

    def test_strict_fails_on_gaps_and_passes_when_clean(self):
        self.assertEqual(self.run_cli(UNRESOLVED).returncode, 0)
        self.assertEqual(self.run_cli(UNRESOLVED, "--strict").returncode, 4)
        self.assertEqual(self.run_cli(FLAT, "--strict").returncode, 0)

    def test_no_subcommands_exit_3(self):
        proc = self.run_cli(NO_SUBCOMMANDS)
        self.assertEqual(proc.returncode, 3)
        self.assertIn("add_parser", proc.stderr)

    def test_syntax_error_exit_1(self):
        proc = self.run_cli("def broken(:\n")
        self.assertEqual(proc.returncode, 1)
        self.assertIn("не разбирается", proc.stderr)

    def test_sentinel_file_through_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            sentinel = Path(tmp) / "SENTINEL"
            target = Path(tmp) / "client.py"
            target.write_text(sentinel_source(sentinel), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCRIPT), str(target)],
                                  capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn("`safe`", proc.stdout)
            self.assertFalse(sentinel.exists(), "the target file was executed")


REAL_CLIENTS = [os.path.expanduser(p) for p in
                os.environ.get("GEN_COMMANDS_CLIENTS", "~/.claude/tools/tg_client.py").split(os.pathsep) if p]


@unittest.skipUnless(os.environ.get("GEN_COMMANDS_REAL") == "1",
                     "set GEN_COMMANDS_REAL=1 to cross-check real clients")
class RealClientTests(unittest.TestCase):
    """Independent oracle: for a flat CLI the AST count must equal a regex count."""

    def test_ast_count_matches_regex_count(self):
        for path in REAL_CLIENTS:
            if not Path(path).exists():
                continue
            with self.subTest(path=path):
                text = gc.load(path)
                regex_names = re.findall(r"""add_parser\(\s*["']([^"']+)["']""", text)
                w = gc.extract(text, filename=path)
                self.assertEqual(len(w.commands), len(regex_names))
                self.assertEqual([c.path[-1] for c in w.commands], regex_names)
                self.assertEqual(w.warnings, [])


SUPPRESS_DEFAULT = src('''
    import argparse

    def main():
        common = argparse.ArgumentParser(add_help=False)
        common.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
        common.add_argument("--limit", type=int, default=argparse.SUPPRESS, help="items kept")
        ap = argparse.ArgumentParser(parents=[common])
        sub = ap.add_subparsers(dest="cmd")
        p = sub.add_parser("items", parents=[common])
        p.add_argument("--page", type=int, default=1)
''')


class SuppressDefaultTests(unittest.TestCase):
    def test_suppress_default_is_not_shown_as_a_default_value(self):
        w = gc.extract(SUPPRESS_DEFAULT)
        text = " ".join(usages(by_name(w)["items"]))
        self.assertNotIn("SUPPRESS", text)
        self.assertIn("[--limit …]", text)
        self.assertIn("[--page=1]", text, "a real default is still shown")


if __name__ == "__main__":
    unittest.main()
