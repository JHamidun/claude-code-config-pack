"""Tests for client_skeleton.py. Offline: no real service, no real credentials, nothing leaves the machine.

    python -m unittest test_client_skeleton -v

The client is driven through main() with a scripted fake transport, so every request it would send is
recorded and checked. The tests that need the real urllib transport (redirects, headers, errors) start a
tiny HTTP server on 127.0.0.1 and talk to that only. The owner's real credentials file and session cache
are never read: both paths are redirected into a temporary folder.
"""

import contextlib
import http.server
import io
import json
import os
import py_compile
import re
import socket
import subprocess
import sys
import tempfile
import threading
import unittest
import urllib.parse
from pathlib import Path
from unittest import mock

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import client_skeleton as cs  # noqa: E402  (the template under test)

SCRIPT = HERE / "client_skeleton.py"
ORIGINAL_SESSION_FILE = cs.SESSION_FILE
BASE = "https://app.example.com/api"
TOKEN = "tok_SENTINEL_0123456789abcdefghijklmnopqrstuvwxyz"       # 40+ chars: also hit by the long-token mask
NEW_TOKEN = "new_SENTINEL_0123456789abcdefghijklmnopqrstuvwxyz"
PASSWORD = "pw-SENTINEL-s3cret"
EMAIL = "alice.sentinel@example.test"


class UnexpectedRequest(BaseException):
    """BaseException on purpose: main() must not turn a surprise request into a tidy 'unexpected error'."""


class FakeTransport:
    """Scripted transport: replies are consumed in order, a request nobody scripted fails the test."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), []

    def __call__(self, method, url, headers, body, timeout):
        self.calls.append({"method": method, "url": url, "headers": dict(headers), "body": body})
        if not self.replies:
            raise UnexpectedRequest("%s %s" % (method, url))
        reply = self.replies.pop(0)
        if isinstance(reply, BaseException):
            raise reply
        return reply

    def shape(self):
        return [(c["method"], urllib.parse.urlsplit(c["url"]).path) for c in self.calls]

    def writes(self):
        return [c for c in self.calls if c["method"] not in ("GET", "HEAD")]


def jr(obj, status=200, headers=None):
    return status, dict({"Content-Type": "application/json"}, **(headers or {})), json.dumps(obj).encode()


def raw(status, body, ctype="text/html", headers=None):
    return status, dict({"Content-Type": ctype}, **(headers or {})), body if isinstance(body, bytes) else body.encode()


class Base(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        for patcher in (
            mock.patch.object(cs, "CREDENTIALS_FILE", self.root / "credentials.env"),
            mock.patch.object(cs, "SESSION_FILE", self.root / ".sessions" / "example.json"),
            mock.patch.object(cs, "BASE_URL", BASE),
            mock.patch.object(cs, "SINGLE_SESSION", False),
            mock.patch.object(cs, "EXPIRED_BODY_MARKERS", ()),
            mock.patch.object(cs, "MAX_RELOGINS", 1),
            mock.patch.object(cs, "DOCTOR_PATH", "/me"),
            mock.patch.dict(os.environ, {}, clear=False),  # restores os.environ, whatever load_env() adds
        ):
            patcher.start()
            self.addCleanup(patcher.stop)
        for name in (cs.TOKEN_ENV, *cs.LOGIN_ENVS, cs.ENV_PREFIX + "_NO_RELOGIN", cs.ENV_PREFIX + "_DEBUG"):
            os.environ.pop(name, None)
        cs.SECRET_VALUES.clear()

    def creds(self, token=None, login=False):
        lines = []
        if token:
            lines.append("%s=%s" % (cs.TOKEN_ENV, token))
        if login:
            lines += ["%s=%s" % (cs.LOGIN_ENVS[0], EMAIL), "%s=%s" % (cs.LOGIN_ENVS[1], PASSWORD)]
        (self.root / "credentials.env").write_text("\n".join(lines) + "\n", encoding="utf-8")

    def run_cli(self, argv, transport=None):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = cs.main(argv, transport=transport)
            except SystemExit as exc:  # argparse: --help and usage errors
                code = exc.code
        return code, out.getvalue(), err.getvalue()

    def assert_no_secrets(self, text):
        for secret in (TOKEN, NEW_TOKEN, PASSWORD):
            self.assertNotIn(secret, text)


# ------------------------------------------------------------------------------------------ basics
class CliBasics(Base):
    def test_compiles(self):
        py_compile.compile(str(SCRIPT), doraise=True)

    def test_help_lists_commands_options_and_exit_codes(self):
        code, out, err = self.run_cli(["--help"])
        self.assertEqual(code, 0)
        for word in ("doctor", "login", "api", "items", "rename", "buy", "exit codes", "--no-relogin", "--json", "--limit"):
            self.assertIn(word, out)
        for command in ("doctor", "login", "api", "items", "rename", "buy"):
            self.assertEqual(self.run_cli([command, "--help"])[0], 0, command)
        self.assertIn("--yes", self.run_cli(["buy", "--help"])[1])
        self.assertNotIn("--yes", self.run_cli(["items", "--help"])[1], "a read command has no change flags")

    def test_json_flag_before_and_after_the_command(self):
        self.creds(token=TOKEN)
        for argv in (["--json", "items"], ["items", "--json"]):
            code, out, err = self.run_cli(argv, FakeTransport(jr({"items": [1]})))
            self.assertEqual(code, 0, err)
            self.assertEqual(out.count("\n"), 1, "compact JSON: a single line")
            self.assertEqual(json.loads(out), {"ok": True, "data": {"items": [1]}})

    def test_usage_errors_exit_2_with_empty_stdout(self):
        for argv in ([], ["nope"], ["items", "--page", "x"], ["rename", "only-one-argument"]):
            code, out, err = self.run_cli(argv)
            self.assertEqual(code, 2, argv)
            self.assertEqual(out, "")
            self.assertTrue(err.strip(), argv)

    def test_usage_errors_follow_the_error_contract(self):
        """Wrong arguments are errors like any other: ERROR and NEXT lines, or one JSON object with --json. Exit 2, stdout empty."""
        for argv in ([], ["nope"], ["rename", "only-one-argument"], ["items", "--page", "x"], ["items", "--limit", "-3"]):
            with self.subTest(argv=argv):
                code, out, err = self.run_cli(argv)
                self.assertEqual((code, out), (2, ""))
                self.assertTrue(err.startswith("ERROR:"), err)
                self.assertIn("NEXT: run:", err)
                self.assertIn("--help", err)
                code, out, err = self.run_cli(argv + ["--json"])
                self.assertEqual((code, out), (2, ""))
                doc = json.loads(err)
                self.assertFalse(doc["ok"])
                self.assertEqual((doc["error"]["kind"], doc["error"]["exit"]), ("usage", 2))
                self.assertIn("--help", doc["error"]["hint"])
        self.assertIn("rename", json.loads(self.run_cli(["rename", "--json"])[2])["error"]["hint"], "a subcommand error points at that subcommand's help")

    def test_source_has_no_token_literals_and_no_default_for_secret_names(self):
        source = SCRIPT.read_text(encoding="utf-8")
        self.assertEqual(re.findall(r"""["'][A-Za-z0-9_\-]{32,}["']""", source), [])
        self.assertEqual(re.findall(r"os\.environ\.get\((?:TOKEN_ENV|name)\s*,", source), [], "a default for a secret rides the wrong key silently")


# ------------------------------------------------------------------------------------------ doctor
class DoctorTests(Base):
    def snapshot(self):
        return sorted((str(p.relative_to(self.root)), p.stat().st_mtime_ns) for p in self.root.rglob("*"))

    def test_nothing_configured_is_exit_3_and_sends_nothing(self):
        t = FakeTransport()
        code, out, err = self.run_cli(["doctor", "--json"], t)
        self.assertEqual(code, 3)
        self.assertEqual(t.calls, [])
        report = json.loads(out)
        self.assertFalse(report["ok"])
        self.assertTrue(report["next"])
        failed = [c for c in report["checks"] if not c["ok"]]
        self.assertEqual({c["check"] for c in failed}, {"credentials file", "authentication"})
        self.assertTrue(all(c["fix"] for c in failed), "every failed check says how to fix it")

    def test_valid_session_is_one_safe_read_and_writes_nothing(self):
        self.creds(token=TOKEN, login=True)
        before = self.snapshot()
        t = FakeTransport(jr({"id": 1}))
        code, out, err = self.run_cli(["doctor", "--json"], t)
        self.assertEqual(code, 0, out + err)
        self.assertEqual(t.shape(), [("GET", "/api/me")])
        self.assertEqual(t.calls[0]["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertEqual(self.snapshot(), before, "doctor must not create or touch any file")
        self.assertTrue(json.loads(out)["ok"])

    def test_expired_session_is_exit_4_and_never_logs_in(self):
        self.creds(token=TOKEN, login=True)  # a login IS possible: doctor must still not use it
        t = FakeTransport(jr({"error": "expired"}, 401))
        code, out, err = self.run_cli(["doctor", "--json"], t)
        self.assertEqual(code, 4)
        self.assertEqual(t.shape(), [("GET", "/api/me")], "no login request, no retry")
        self.assertIn("login", json.loads(out)["next"])
        self.assertFalse(cs.SESSION_FILE.exists())

    def test_login_possible_but_no_token_yet_is_exit_4_not_3(self):
        self.creds(login=True)
        t = FakeTransport()
        code, out, err = self.run_cli(["doctor", "--json"], t)
        self.assertEqual(code, 4)
        self.assertEqual(t.calls, [])
        report = json.loads(out)
        self.assertEqual(report["next"], "run: login")
        self.assertTrue(next(c for c in report["checks"] if c["check"] == "authentication")["ok"])

    def test_server_error_and_network_error_are_exit_1(self):
        self.creds(token=TOKEN)
        code, out, err = self.run_cli(["doctor", "--json"], FakeTransport(jr({"e": 1}, 500)))
        self.assertEqual(code, 1)
        self.assertIn("HTTP 500", json.dumps(json.loads(out)["checks"]))
        down = cs.CliError(cs.EXIT_FAIL, "network error: refused", "check the connection", kind="network")
        code, out, err = self.run_cli(["doctor", "--json"], FakeTransport(down))
        self.assertEqual(code, 1)
        self.assertIn("unreachable", json.dumps(json.loads(out)["checks"]))

    def test_offline_and_missing_doctor_path_skip_the_read(self):
        self.creds(token=TOKEN)
        t = FakeTransport()
        self.assertEqual(self.run_cli(["doctor", "--offline", "--json"], t)[0], 0)
        with mock.patch.object(cs, "DOCTOR_PATH", None):
            self.assertEqual(self.run_cli(["doctor", "--json"], t)[0], 0)
        self.assertEqual(t.calls, [])

    def test_secret_values_are_never_printed(self):
        self.creds(token=TOKEN, login=True)
        for argv in (["doctor"], ["doctor", "--json"], ["doctor", "--offline"]):
            code, out, err = self.run_cli(argv, FakeTransport(jr({"id": 1})))
            self.assertEqual(code, 0, err)
            self.assert_no_secrets(out + err)
            self.assertNotIn(EMAIL, out + err)

    def test_a_failed_check_never_carries_the_wording_of_a_passed_one(self):
        code, out, err = self.run_cli(["doctor", "--json"], FakeTransport())  # no credentials file, nothing set
        checks = {c["check"]: c for c in json.loads(out)["checks"]}
        self.assertFalse(checks["credentials file"]["ok"])
        self.assertIn("not found", checks["credentials file"]["detail"])
        self.assertNotIn("present", checks["credentials file"]["detail"])
        self.assertFalse(checks["authentication"]["ok"])
        self.assertNotIn("can mint one", checks["authentication"]["detail"])
        self.assertIn(cs.TOKEN_ENV, checks["authentication"]["detail"])
        self.creds(login=True)
        checks = {c["check"]: c for c in json.loads(self.run_cli(["doctor", "--offline", "--json"], FakeTransport())[1])["checks"]}
        self.assertTrue(checks["credentials file"]["ok"])
        self.assertIn("present", checks["credentials file"]["detail"])
        self.assertIn("can mint one", checks["authentication"]["detail"])

    def test_plain_http_base_url_is_a_config_error_except_on_localhost(self):
        self.creds(token=TOKEN)
        with mock.patch.object(cs, "BASE_URL", "http://app.example.com/api"):
            self.assertEqual(self.run_cli(["doctor", "--offline", "--json"])[0], 3)
        with mock.patch.object(cs, "BASE_URL", "http://127.0.0.1:9/api"):
            self.assertEqual(self.run_cli(["doctor", "--offline", "--json"])[0], 0)


# ------------------------------------------------------------------------------------------ session
class SessionTests(Base):
    def login_ok(self):
        return jr({"token": NEW_TOKEN})

    def test_401_logs_in_once_retries_and_caches_the_new_token(self):
        self.creds(token=TOKEN, login=True)
        t = FakeTransport(jr({}, 401), self.login_ok(), jr({"items": [1]}))
        code, out, err = self.run_cli(["items", "--json"], t)
        self.assertEqual(code, 0, err)
        self.assertEqual(t.shape(), [("GET", "/api/items"), ("POST", "/api/auth/login"), ("GET", "/api/items")])
        self.assertEqual(t.calls[0]["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertEqual(t.calls[2]["headers"]["Authorization"], "Bearer " + NEW_TOKEN)
        self.assertEqual(json.loads(t.calls[1]["body"]), {"email": EMAIL, "password": PASSWORD})
        self.assert_no_secrets(out + err)
        self.assertEqual(json.loads(cs.SESSION_FILE.read_text(encoding="utf-8"))["token"], NEW_TOKEN)
        self.assertEqual(list(cs.SESSION_FILE.parent.glob("*.tmp")), [])
        t2 = FakeTransport(jr({"items": []}))
        self.assertEqual(self.run_cli(["items", "--json"], t2)[0], 0)
        self.assertEqual(len(t2.calls), 1, "the next run uses the cached session, no login")
        self.assertEqual(t2.calls[0]["headers"]["Authorization"], "Bearer " + NEW_TOKEN)

    def test_a_second_401_after_the_login_is_exit_4(self):
        self.creds(token=TOKEN, login=True)
        t = FakeTransport(jr({}, 401), self.login_ok(), jr({}, 401))
        code, out, err = self.run_cli(["items"], t)
        self.assertEqual(code, 4)
        self.assertEqual([m for m, _ in t.shape()].count("POST"), 1)
        self.assertIn("still unauthorized", err)
        self.assertIn("NEXT:", err)

    def test_no_relogin_flag_and_env_switch_the_login_off(self):
        self.creds(token=TOKEN, login=True)
        t = FakeTransport(jr({}, 401))
        code, out, err = self.run_cli(["items", "--no-relogin"], t)
        self.assertEqual((code, len(t.calls)), (4, 1))
        self.assertIn("NEXT:", err)
        os.environ[cs.ENV_PREFIX + "_NO_RELOGIN"] = "1"
        t = FakeTransport(jr({}, 401))
        self.assertEqual((self.run_cli(["items"], t)[0], len(t.calls)), (4, 1))

    def test_single_session_service_is_never_logged_in_by_itself(self):
        self.creds(token=TOKEN, login=True)
        with mock.patch.object(cs, "SINGLE_SESSION", True):
            t = FakeTransport(jr({}, 401))
            code, out, err = self.run_cli(["items"], t)
            self.assertEqual((code, len(t.calls)), (4, 1))
            self.assertIn("ONE session per account", err)
            # the explicit login is a paid-class action here: dry run, then --apply is refused, then --yes works
            t = FakeTransport()
            code, out, err = self.run_cli(["login", "--json"], t)
            self.assertEqual((code, t.calls, json.loads(out)["dry_run"]), (0, [], True))
            self.assertEqual(self.run_cli(["login", "--apply"], FakeTransport())[0], 5)
            t = FakeTransport(self.login_ok())
            code, out, err = self.run_cli(["login", "--yes", "--json"], t)
            self.assertEqual((code, t.shape()), (0, [("POST", "/api/auth/login")]))
            self.assertEqual(json.loads(cs.SESSION_FILE.read_text(encoding="utf-8"))["token"], NEW_TOKEN)
            self.assert_no_secrets(out + err)

    def test_login_is_capped_per_run(self):
        self.creds(token=TOKEN, login=True)
        t = FakeTransport(
            jr({}, 401),                 # GET /quote -> expired
            self.login_ok(),             # the one allowed login
            jr({"price": 1}),            # GET /quote retried
            jr({}, 401),                 # POST /buy -> expired again
        )
        code, out, err = self.run_cli(["buy", "SKU-1", "--yes"], t)
        self.assertEqual(code, 4)
        self.assertEqual([m for m, _ in t.shape()].count("POST"), 2, "one login plus the one /buy attempt, no second login")
        self.assertEqual(t.shape()[-1], ("POST", "/api/buy"))
        self.assertIn("not logging in a second time", err)

    def test_every_expiry_signal_is_recognised(self):
        self.creds(token=TOKEN, login=True)
        cases = {
            "redirect to the login page": raw(302, b"", headers={"Location": "https://app.example.com/login?next=/api/items"}),
            "login form instead of JSON": raw(200, '<html><form><input type="password" name="password"></form></html>'),
        }
        for label, reply in cases.items():
            with self.subTest(label):
                t = FakeTransport(reply)
                code, out, err = self.run_cli(["items", "--no-relogin"], t)
                self.assertEqual((code, len(t.calls)), (4, 1))
        with self.subTest("marker in a 200 body"), mock.patch.object(cs, "EXPIRED_BODY_MARKERS", ("token expired",)):
            t = FakeTransport(jr({"error": "Token Expired, sign in again"}))
            self.assertEqual(self.run_cli(["items", "--no-relogin"], t)[0], 4)

    def test_403_is_a_plan_problem_not_a_session_problem(self):
        self.creds(token=TOKEN, login=True)
        t = FakeTransport(jr({"error": "upgrade"}, 403))
        code, out, err = self.run_cli(["items"], t)
        self.assertEqual((code, len(t.calls)), (1, 1), "no login attempt")
        self.assertIn("plan or role", err)

    def test_missing_login_pair_and_refused_login(self):
        self.creds(token=TOKEN)
        code, out, err = self.run_cli(["items"], FakeTransport(jr({}, 401)))
        self.assertEqual(code, 3)
        self.assertIn("EXAMPLE_EMAIL", err)
        self.assertIn("NEXT:", err)
        self.assert_no_secrets(err)
        self.creds(token=TOKEN, login=True)
        t = FakeTransport(jr({}, 401), jr({"error": "bad credentials"}, 401))
        code, out, err = self.run_cli(["items"], t)
        self.assertEqual(code, 4)
        self.assertIn("login was refused", err)
        self.assertEqual(t.shape()[1], ("POST", "/api/auth/login"))
        self.assert_no_secrets(err)


    def test_login_dry_run_sends_nothing_even_on_a_many_sessions_service(self):
        """--dry-run always wins. Without it a login on a many-sessions service still runs at once."""
        self.creds(token=TOKEN, login=True)
        t = FakeTransport()
        code, out, err = self.run_cli(["login", "--dry-run", "--json"], t)
        self.assertEqual((code, t.calls), (0, []))
        doc = json.loads(out)
        self.assertEqual((doc["ok"], doc["dry_run"]), (True, True))
        self.assertNotIn("logged_in", doc)
        self.assertFalse(cs.SESSION_FILE.exists(), "a dry run must not write the session cache")
        t = FakeTransport(self.login_ok())
        code, out, err = self.run_cli(["login", "--json"], t)
        self.assertEqual((code, t.shape()), (0, [("POST", "/api/auth/login")]))
        self.assertTrue(json.loads(out)["data"]["logged_in"])

    def used_token(self, argv=("items", "--json")):
        t = FakeTransport(jr({"items": []}))
        code, out, err = self.run_cli(list(argv), t)
        self.assertEqual(code, 0, err)
        return t.calls[0]["headers"]["Authorization"]

    def test_a_token_pasted_into_the_env_after_the_cache_was_written_wins(self):
        """The hint says: log in by hand, put the new token into the variable, run doctor. A stale session cache must not shadow it."""
        cs.write_session_token("EXPIRED-" + TOKEN)       # written when no hand-copied token existed
        self.creds(token=TOKEN)
        self.assertEqual(self.used_token(), "Bearer " + TOKEN)
        report = json.loads(self.run_cli(["doctor", "--offline", "--json"], FakeTransport())[1])
        self.assertIn("env " + cs.TOKEN_ENV, next(c for c in report["checks"] if c["check"] == "authentication")["detail"])

    def test_a_cache_written_after_the_env_token_beats_that_older_env_token(self):
        os.environ[cs.TOKEN_ENV] = TOKEN                  # the hand-copied token that was current when the cache was minted
        cs.write_session_token(NEW_TOKEN)
        self.creds(token=TOKEN)                           # the file still holds the same old value
        self.assertEqual(self.used_token(), "Bearer " + NEW_TOKEN)
        os.environ.pop(cs.TOKEN_ENV)
        self.creds(token="pasted-later-" + TOKEN)         # the owner replaces it afterwards: now the env token is the newer one
        self.assertEqual(self.used_token(), "Bearer pasted-later-" + TOKEN)

    def test_a_cache_without_a_tag_and_a_cache_without_an_env_token(self):
        cs.SESSION_FILE.parent.mkdir(parents=True)
        cs.SESSION_FILE.write_text(json.dumps({"token": "EXPIRED-" + TOKEN}), encoding="utf-8")  # hand-made: no tag, nothing to compare
        self.assertEqual(self.used_token(), "Bearer EXPIRED-" + TOKEN, "with no env token the cache is all there is")
        self.creds(token=TOKEN)
        self.assertEqual(self.used_token(), "Bearer " + TOKEN, "an explicit env token beats an untagged cache")

    def test_the_session_file_never_holds_the_password_or_the_hand_copied_token(self):
        self.creds(token=TOKEN, login=True)
        t = FakeTransport(jr({}, 401), self.login_ok(), jr({"items": []}))
        self.assertEqual(self.run_cli(["items", "--json"], t)[0], 0)
        text = cs.SESSION_FILE.read_text(encoding="utf-8")
        for secret in (PASSWORD, EMAIL, TOKEN):
            self.assertNotIn(secret, text)
        self.assertEqual(json.loads(text)["env_fp"], cs.fingerprint(TOKEN))


# ------------------------------------------------------------------------------------------ changes
class GateTests(Base):
    def setUp(self):
        super().setUp()
        self.creds(token=TOKEN)

    def test_a_reversible_change_is_a_dry_run_by_default(self):
        t = FakeTransport()
        code, out, err = self.run_cli(["rename", "5", "New name", "--json"], t)
        self.assertEqual((code, t.calls), (0, []))
        doc = json.loads(out)
        self.assertEqual((doc["ok"], doc["dry_run"], doc["risk"]), (True, True, "write"))
        self.assertEqual(doc["plan"]["body"], {"name": "New name"})
        self.assertEqual((doc["plan"]["method"], doc["plan"]["path"]), ("PUT", "/items/5"))
        self.assertIn("--apply", doc["hint"])

    def test_dry_run_always_wins(self):
        for flags in (["--dry-run", "--apply"], ["--dry-run", "--yes"], ["--dry-run", "--apply", "--yes"]):
            with self.subTest(flags):
                t = FakeTransport(jr({"price": 1}))  # buy reads the price, and only that
                code, out, err = self.run_cli(["buy", "SKU-1", "--json"] + flags, t)
                self.assertEqual(code, 0, err)
                self.assertTrue(json.loads(out)["dry_run"])
                self.assertEqual(t.writes(), [])
                t = FakeTransport()
                code, out, err = self.run_cli(["rename", "5", "x", "--json"] + flags, t)
                self.assertEqual((code, t.calls), (0, []))

    def test_apply_sends_exactly_one_put(self):
        t = FakeTransport(jr({"id": 5, "name": "New name"}))
        code, out, err = self.run_cli(["rename", "5", "New name", "--apply", "--json"], t)
        self.assertEqual(code, 0, err)
        self.assertEqual(t.shape(), [("PUT", "/api/items/5")])
        self.assertEqual(json.loads(t.calls[0]["body"]), {"name": "New name"})
        self.assertEqual(t.calls[0]["headers"]["Content-Type"], "application/json")
        self.assertEqual(json.loads(out)["data"]["name"], "New name")

    def test_a_paid_action_reads_the_price_first_and_needs_yes(self):
        quote = {"price": 15.9, "currency": "BRL"}
        t = FakeTransport(jr(quote))
        code, out, err = self.run_cli(["buy", "SKU-1", "--json"], t)
        self.assertEqual(code, 0, err)
        self.assertEqual(t.shape(), [("GET", "/api/quote")])
        self.assertEqual(urllib.parse.parse_qs(urllib.parse.urlsplit(t.calls[0]["url"]).query), {"sku": ["SKU-1"]})
        doc = json.loads(out)
        self.assertEqual((doc["dry_run"], doc["risk"], doc["plan"]["cost"]), (True, "paid", quote))
        self.assertIn("--yes", doc["hint"])

        t = FakeTransport(jr(quote))
        code, out, err = self.run_cli(["buy", "SKU-1", "--apply", "--json"], t)
        self.assertEqual(code, 5, "--apply is not enough for a paid action")
        self.assertEqual(t.writes(), [])
        error = json.loads(err)["error"]
        self.assertEqual((error["kind"], error["exit"]), ("needs_yes", 5))
        self.assertEqual(error["plan"]["cost"], quote)
        self.assertEqual(out, "")

        t = FakeTransport(jr(quote), jr({"order": 7}, 201))
        code, out, err = self.run_cli(["buy", "SKU-1", "--qty", "2", "--yes", "--json"], t)
        self.assertEqual(code, 0, err)
        self.assertEqual(t.shape(), [("GET", "/api/quote"), ("POST", "/api/buy")], "the price is read BEFORE the changing request")
        self.assertEqual(json.loads(t.calls[1]["body"]), {"sku": "SKU-1", "qty": 2})

    def test_when_the_price_cannot_be_read_nothing_is_changed(self):
        t = FakeTransport(jr({"error": "boom"}, 500))
        code, out, err = self.run_cli(["buy", "SKU-1", "--yes"], t)
        self.assertEqual(code, 1)
        self.assertEqual(t.shape(), [("GET", "/api/quote")])
        self.assertIn("HTTP 500", err)

    def test_api_changes_are_gated_like_everything_else(self):
        data = '{"a": 1}'
        for method in ("POST", "put", "PATCH", "DELETE"):
            with self.subTest(method):
                t = FakeTransport()
                code, out, err = self.run_cli(["api", "/things", "--method", method, "--data", data, "--json"], t)
                self.assertEqual((code, t.calls), (0, []))
                doc = json.loads(out)
                self.assertEqual((doc["dry_run"], doc["risk"], doc["plan"]["body"]), (True, "paid", {"a": 1}))
                t = FakeTransport()
                self.assertEqual(self.run_cli(["api", "/things", "--method", method, "--apply"], t)[0], 5)
                self.assertEqual(t.calls, [])
        t = FakeTransport()
        self.assertEqual(self.run_cli(["api", "/things", "--method", "POST", "--yes", "--dry-run"], t)[0], 0)
        self.assertEqual(t.calls, [])
        t = FakeTransport(jr({"ok": 1}, 201))
        code, out, err = self.run_cli(["api", "/things", "--method", "POST", "--data", data, "--yes", "--json"], t)
        self.assertEqual((code, t.shape()), (0, [("POST", "/api/things")]))
        self.assertEqual(json.loads(t.calls[0]["body"]), {"a": 1})
        self.assertEqual(json.loads(out), {"ok": True, "status": 201, "data": {"ok": 1}})

    def test_api_get_runs_at_once_with_query_parameters(self):
        t = FakeTransport(jr({"x": 1}))
        code, out, err = self.run_cli(["api", "/items", "--query", "page=2", "--query", "per_page=5", "--json"], t)
        self.assertEqual(code, 0, err)
        self.assertEqual(t.calls[0]["url"], BASE + "/items?page=2&per_page=5")
        self.assertEqual(json.loads(out), {"ok": True, "status": 200, "data": {"x": 1}})

    def test_api_bad_arguments_are_usage_errors_with_a_next_step(self):
        for argv in (["api", "/x", "--data", "{not json"], ["api", "/x", "--query", "novalue"]):
            with self.subTest(argv):
                t = FakeTransport()
                code, out, err = self.run_cli(argv, t)
                self.assertEqual((code, t.calls, out), (2, [], ""))
                self.assertIn("NEXT:", err)

    def test_the_session_never_goes_to_another_host(self):
        for target in ("https://evil.example.test/steal", "http://app.example.com/api/items",
                       "https://app.example.com.evil.test/x", "https://app.example.com@evil.test/x"):
            with self.subTest(target):
                t = FakeTransport()
                code, out, err = self.run_cli(["api", target], t)
                self.assertEqual((code, t.calls), (2, []))
                self.assert_no_secrets(out + err)
        t = FakeTransport(jr({"ok": 1}))
        self.assertEqual(self.run_cli(["api", BASE + "/items"], t)[0], 0)
        self.assertEqual(t.calls[0]["url"], BASE + "/items")
        t = FakeTransport(jr({}))
        self.assertEqual(self.run_cli(["api", "//evil.example.test/x"], t)[0], 0)
        self.assertTrue(t.calls[0]["url"].startswith(BASE + "/evil.example.test/x"), "a protocol-relative path stays under BASE_URL")

    def test_a_path_with_a_space_or_non_ascii_letters_is_percent_encoded_not_a_crash(self):
        """`api "/my path"` used to die with InvalidURL and `api "/файл"` with UnicodeEncodeError, both as 'a bug in the client'."""
        cases = (("/my path", "/my%20path"), ("/файл", "/%D1%84%D0%B0%D0%B9%D0%BB"), ("/a b?q=c d&x=ю", "/a%20b?q=c%20d&x=%D1%8E"),
                 ("/already%20encoded", "/already%20encoded"), ("/items?page=2", "/items?page=2"), ("/a:b@c;d,e=f", "/a:b@c;d,e=f"),
                 ("/x#fragment", "/x"), ("my path", "/my%20path"))
        for given, sent in cases:
            with self.subTest(given):
                t = FakeTransport(jr({"ok": 1}))
                code, out, err = self.run_cli(["api", given, "--json"], t)
                self.assertEqual((code, err), (0, ""))
                self.assertEqual(t.calls[0]["url"], BASE + sent)
                t.calls[0]["url"].encode("ascii")  # what http.client needs: nothing else may reach the wire
        t = FakeTransport(jr({}))  # the same rule for a full URL of the allowed host
        self.assertEqual(self.run_cli(["api", BASE + "/my path?q=a b"], t)[0], 0)
        self.assertEqual(t.calls[0]["url"], BASE + "/my%20path?q=a%20b")
        t = FakeTransport(jr({}))
        self.assertEqual(self.run_cli(["api", "/items", "--query", "q=файл x"], t)[0], 0)
        self.assertEqual(t.calls[0]["url"], BASE + "/items?q=%D1%84%D0%B0%D0%B9%D0%BB+x")

    def test_a_control_character_in_the_path_is_a_usage_error_not_a_bug_in_the_client(self):
        for bad in ("/line\nbreak", "/tab\there", "/nul\x00", "/del\x7f", "https://app.example.com/api/x\r\nHost: evil"):
            for extra in ([], ["--method", "POST"]):  # a dry run of a changing call must not look fine and fail only on --apply
                with self.subTest(bad=bad, extra=extra):
                    t = FakeTransport()
                    code, out, err = self.run_cli(["api", bad, "--json"] + extra, t)
                    self.assertEqual((code, out, t.calls), (2, "", []))
                    error = json.loads(err)["error"]
                    self.assertEqual(error["kind"], "usage")
                    self.assertIn("control character", error["message"])
                    self.assertNotIn("bug in the client", err)
                    self.assertTrue(error["hint"])
        code, out, err = self.run_cli(["api", "/line\nbreak"], FakeTransport())
        self.assertEqual(code, 2)
        self.assertTrue(err.startswith("ERROR:") and "NEXT:" in err, err)

    def test_a_command_that_forgets_the_gate_cannot_change_anything(self):
        def forgetful(c, args):
            c.call("PUT", "/items/1", body={"name": "x"})  # a new command that never calls gate()

        t = FakeTransport(jr({}))
        with mock.patch.object(cs, "cmd_rename", forgetful):
            code, out, err = self.run_cli(["rename", "1", "x", "--apply"], t)
        self.assertEqual((code, t.calls), (1, []), "the request never reached the transport")
        self.assertIn("without passing gate()", err)

    def test_client_level_guard_and_reads_that_need_no_gate(self):
        t = FakeTransport(jr({}), jr({}), jr({}))
        c = cs.Client(transport=t)
        with self.assertRaises(cs.CliError) as raised:
            c.call("POST", "/x", body={})
        self.assertEqual(raised.exception.kind, "bug")
        self.assertEqual(t.calls, [])
        c.call("GET", "/x")
        c.call("HEAD", "/x")
        self.assertEqual([call["method"] for call in t.calls], ["GET", "HEAD"])
        c.armed = True
        c.call("POST", "/x", body={})
        self.assertEqual(t.calls[-1]["method"], "POST")


# ------------------------------------------------------------------------------------------ output and errors
class OutputTests(Base):
    def setUp(self):
        super().setUp()
        self.creds(token=TOKEN, login=True)

    def test_long_lists_are_cut_by_items_and_still_valid_json(self):
        items = [{"id": i} for i in range(250)]
        code, out, err = self.run_cli(["items", "--json"], FakeTransport(jr({"items": items})))
        doc = json.loads(out)
        self.assertEqual(len(doc["data"]["items"]), 100)
        self.assertEqual(doc["truncated"], [{"path": "$.data.items", "kind": "items", "shown": 100, "total": 250}])
        doc = json.loads(self.run_cli(["items", "--limit", "0", "--json"], FakeTransport(jr({"items": items})))[1])
        self.assertEqual(len(doc["data"]["items"]), 250)
        self.assertNotIn("truncated", doc)
        for argv in (["items", "--limit", "7", "--json"], ["--limit", "7", "items", "--json"]):
            doc = json.loads(self.run_cli(argv, FakeTransport(jr({"items": items})))[1])
            self.assertEqual(len(doc["data"]["items"]), 7, argv)

    def test_limit_zero_lifts_every_cut_long_strings_included(self):
        """The hint says 'use --limit 0 for everything': it used to leave strings cut at MAX_STRING characters."""
        text = "x" * (cs.MAX_STRING + 10000)
        items = [{"id": i} for i in range(250)]
        doc = json.loads(self.run_cli(["api", "/page", "--json"], FakeTransport(jr({"text": text})))[1])
        self.assertEqual(len(doc["data"]["text"]), cs.MAX_STRING)
        self.assertEqual(doc["truncated"], [{"path": "$.data.text", "kind": "chars", "shown": cs.MAX_STRING, "total": len(text)}])
        for argv in (["api", "/page", "--limit", "0", "--json"], ["--limit", "0", "api", "/page", "--json"]):
            doc = json.loads(self.run_cli(argv, FakeTransport(jr({"text": text, "items": items})))[1])
            self.assertEqual((len(doc["data"]["text"]), len(doc["data"]["items"])), (len(text), 250), argv)
            self.assertNotIn("truncated", doc)
        code, out, err = self.run_cli(["api", "/page"], FakeTransport(jr({"text": text})))
        self.assertIn("use --limit 0 for everything", err, "the hint is shown for a cut string")
        code, out, err = self.run_cli(["api", "/page", "--limit", "0"], FakeTransport(jr({"text": text})))
        self.assertEqual((len(json.loads(out)["data"]["text"]), err), (len(text), ""), "and following it really removes the cut and the hint")
        with mock.patch.object(cs, "MAX_STRING", 50):  # a small cap still applies to a non-zero limit
            doc = json.loads(self.run_cli(["api", "/page", "--limit", "5", "--json"], FakeTransport(jr({"text": "y" * 500})))[1])
        self.assertEqual(len(doc["data"]["text"]), 50)
        helptext = " ".join(self.run_cli(["items", "--help"])[1].split())
        self.assertIn("0 = no cut at all", helptext)

    def test_a_negative_limit_is_a_usage_error_not_a_silent_cut(self):
        """A negative slice would drop the last N items and still say ok."""
        for argv in (["items", "--limit", "-3"], ["--limit", "-1", "items"], ["items", "--limit", "x"]):
            with self.subTest(argv=argv):
                t = FakeTransport(jr({"items": list(range(500))}))
                code, out, err = self.run_cli(argv + ["--json"], t)
                self.assertEqual((code, out, t.calls), (2, "", []))
                self.assertEqual(json.loads(err)["error"]["kind"], "usage")
        self.assertEqual(cs.limit_arg("0"), 0)
        self.assertEqual(cs.limit_arg("7"), 7)

    def test_long_strings_are_cut_and_marked(self):
        with mock.patch.object(cs, "MAX_STRING", 50):
            doc = json.loads(self.run_cli(["api", "/page", "--json"], FakeTransport(jr({"text": "x" * 500})))[1])
        self.assertEqual(len(doc["data"]["text"]), 50)
        self.assertEqual(doc["truncated"], [{"path": "$.data.text", "kind": "chars", "shown": 50, "total": 500}])

    def test_without_json_the_output_is_readable_json_and_the_cut_is_announced_on_stderr(self):
        code, out, err = self.run_cli(["items"], FakeTransport(jr({"items": list(range(150))})))
        self.assertEqual(json.loads(out)["truncated"][0]["total"], 150)
        self.assertIn("(output cut:", err)
        self.assertGreater(out.count("\n"), 5, "indented for reading")

    def test_a_reply_that_is_not_json_is_wrapped_not_crashed_on(self):
        code, out, err = self.run_cli(["api", "/page", "--json"], FakeTransport(raw(200, "<html>hi</html>")))
        self.assertEqual(json.loads(out)["data"], {"content_type": "text/html", "text": "<html>hi</html>"})

    def test_every_error_names_the_next_step(self):
        cases = {
            "required query parameter": raw(404, "<html>not found</html>"),
            "cloud storage": raw(404, "<Error><Code>InvalidArgument</Code></Error>", ctype="application/xml"),
            "rate limited": raw(429, "slow down", ctype="text/plain"),
            "server error": raw(500, "boom", ctype="text/plain"),
            "unexpected redirect": raw(302, b"", headers={"Location": "https://elsewhere.example.test/x"}),
            "compare the request": jr({"error": "bad"}, 400),
        }
        for hint, reply in cases.items():
            with self.subTest(hint):
                code, out, err = self.run_cli(["items"], FakeTransport(reply))
                self.assertEqual((code, out), (1, ""))
                self.assertTrue(err.startswith("ERROR:"), err)
                self.assertIn("NEXT:", err)
                self.assertIn(hint, err)

    def test_with_json_the_error_is_one_json_object_on_stderr(self):
        code, out, err = self.run_cli(["--json", "items"], FakeTransport(jr({"error": "boom"}, 500)))
        self.assertEqual((code, out), (1, ""))
        doc = json.loads(err)
        self.assertFalse(doc["ok"])
        self.assertEqual((doc["error"]["kind"], doc["error"]["exit"], doc["error"]["status"]), ("http", 1, 500))
        self.assertTrue(doc["error"]["hint"])

    def test_error_text_cannot_leak_the_session_or_the_password(self):
        body = "debug token=%s password=%s %s" % (TOKEN, PASSWORD, "A" * 60)
        code, out, err = self.run_cli(["--json", "api", "/x"], FakeTransport(raw(500, body, ctype="text/plain")))
        self.assertEqual(code, 1)
        self.assert_no_secrets(err)
        self.assertIn("<secret>", err)
        self.assertIn("<redacted>", err)

    def test_an_unexpected_exception_is_a_readable_error_not_a_traceback(self):
        def boom(c, args):
            raise ValueError("kaboom %s" % TOKEN)

        with mock.patch.object(cs, "cmd_items", boom):
            code, out, err = self.run_cli(["items"], FakeTransport())
        self.assertEqual((code, out), (1, ""))
        self.assertIn("unexpected error: ValueError", err)
        self.assertIn("NEXT:", err)
        self.assertNotIn("Traceback", err)
        self.assert_no_secrets(err)
        os.environ[cs.ENV_PREFIX + "_DEBUG"] = "1"
        with mock.patch.object(cs, "cmd_items", boom), self.assertRaises(ValueError):
            self.run_cli(["items"], FakeTransport())


# ------------------------------------------------------------------------------------------ secrets and files
class ConfigTests(Base):
    def test_load_env_reads_the_credentials_file_only_and_never_overrides(self):
        (self.root / "credentials.env").write_text(
            '# comment\n\nSENT_A="quoted value"\nexport SENT_B=exported\nSENT_C=\'single\'\nnot a pair\n  SENT_D = spaced \nSENT_E=from the file\n',
            encoding="utf-8")
        os.environ["SENT_E"] = "already set"
        self.assertTrue(cs.load_env())
        self.assertEqual([os.environ[k] for k in ("SENT_A", "SENT_B", "SENT_C", "SENT_D", "SENT_E")],
                         ["quoted value", "exported", "single", "spaced", "already set"])

    def test_a_bom_at_the_start_of_the_credentials_file_does_not_eat_the_first_name(self):
        """Notepad and some editors save UTF-8 with a BOM: the first variable used to become a name with a BOM char in front and vanish."""
        (self.root / "credentials.env").write_bytes(b"\xef\xbb\xbf" + ("%s=%s\nSENT_B=2\n" % (cs.TOKEN_ENV, TOKEN)).encode("utf-8"))
        self.assertTrue(cs.load_env())
        self.assertEqual(os.environ.get(cs.TOKEN_ENV), TOKEN)
        self.assertEqual(os.environ.get("SENT_B"), "2")

    def test_missing_credentials_file_is_not_an_error_by_itself(self):
        self.assertFalse(cs.load_env())

    def test_session_cache_lives_under_dot_claude_outside_any_repository(self):
        self.assertEqual(ORIGINAL_SESSION_FILE, Path.home() / ".claude" / ".sessions" / (cs.SERVICE + ".json"))

    def test_session_file_is_atomic_and_holds_only_the_token(self):
        cs.write_session_token("tok-123456")
        data = json.loads(cs.SESSION_FILE.read_text(encoding="utf-8"))
        self.assertEqual(set(data), {"token", "saved_at", "env_fp"}, "the token, the time and a 12-character tag of the hand-copied token")
        self.assertEqual(data["env_fp"], "", "no hand-copied token was set: the tag is empty")
        self.assertEqual(cs.read_session_token(), "tok-123456")
        self.assertEqual(list(cs.SESSION_FILE.parent.glob("*.tmp")), [])
        cs.SESSION_FILE.write_text("{not json", encoding="utf-8")
        self.assertIsNone(cs.read_session_token())
        cs.SESSION_FILE.write_text(json.dumps({"token": 12345}), encoding="utf-8")
        self.assertIsNone(cs.read_session_token())

    def test_scrub_masks_known_secrets_and_long_tokens_but_not_short_noise(self):
        cs.remember("abc")          # too short to be worth masking: it would eat ordinary words
        cs.remember("secretvalue")
        self.assertEqual(cs.scrub("x abc secretvalue y"), "x abc <secret> y")
        self.assertEqual(cs.scrub("k=" + "Z" * 45), "k=<redacted>")
        self.assertEqual(len(cs.scrub("word " * 100)), 200, "plain text is only cut to the limit")
        self.assertEqual(cs.scrub("y" * 500), "<redacted>", "a long unbroken run looks like a token")


# ------------------------------------------------------------------------------------------ the real urllib transport
class LoopbackServer:
    """A tiny HTTP server on 127.0.0.1. handler(method, path, headers, body) -> (status, headers, body_bytes)."""

    def __init__(self, handler):
        outer = self
        self.requests = []

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def handle_any(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                outer.requests.append({"method": self.command, "path": self.path, "headers": dict(self.headers), "body": body})
                status, headers, payload = handler(self.command, self.path, dict(self.headers), body)
                self.send_response(status)
                for key, value in headers.items():
                    self.send_header(key, value)
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = do_PUT = do_DELETE = do_PATCH = handle_any

        self.httpd = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = self.httpd.server_address[1]
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)

    @property
    def base(self):
        return "http://127.0.0.1:%d/api" % self.port

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.httpd.shutdown()
        self.httpd.server_close()
        self.thread.join(5)


class RealTransportTests(Base):
    def setUp(self):
        super().setUp()
        self.creds(token=TOKEN)
        patcher = mock.patch("urllib.request.getproxies", return_value={})  # loopback must never go through a system proxy
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_against(self, server, argv):
        with mock.patch.object(cs, "BASE_URL", server.base):
            return self.run_cli(argv)

    def test_a_request_carries_the_session_and_the_default_headers(self):
        with LoopbackServer(lambda m, p, h, b: (200, {"Content-Type": "application/json"}, b'{"items":[{"id":1}]}')) as server:
            code, out, err = self.run_against(server, ["items", "--json"])
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(out)["data"]["items"], [{"id": 1}])
        request = server.requests[0]
        self.assertEqual(request["path"], "/api/items?page=1")
        self.assertEqual(request["headers"]["Authorization"], "Bearer " + TOKEN)
        self.assertEqual(request["headers"]["Accept"], "application/json")
        self.assertIn("example-client", request["headers"]["User-Agent"])

    def test_a_path_with_a_space_or_non_ascii_letters_really_reaches_the_server_encoded(self):
        reply = (200, {"Content-Type": "application/json"}, b"{}")
        with LoopbackServer(lambda m, p, h, b: reply) as server:
            for given in ("/my path", "/файл", "/a b?q=ю"):
                code, out, err = self.run_against(server, ["api", given, "--json"])
                self.assertEqual((code, err), (0, ""), given)
        self.assertEqual([r["path"] for r in server.requests], ["/api/my%20path", "/api/%D1%84%D0%B0%D0%B9%D0%BB", "/api/a%20b?q=%D1%8E"])

    def test_a_redirect_is_never_followed_so_the_session_cannot_follow_it(self):
        with LoopbackServer(lambda m, p, h, b: (200, {"Content-Type": "text/plain"}, b"stolen")) as other:
            target = "http://127.0.0.1:%d/stolen" % other.port
            with LoopbackServer(lambda m, p, h, b: (302, {"Location": target}, b"")) as server:
                code, out, err = self.run_against(server, ["items", "--json"])
        self.assertEqual(other.requests, [], "the redirect target must never be contacted")
        self.assertEqual(len(server.requests), 1)
        self.assertEqual(code, 1)
        self.assertIn("unexpected redirect", err)

    def test_a_redirect_to_the_login_page_means_the_session_is_gone(self):
        with LoopbackServer(lambda m, p, h, b: (302, {"Location": "/login?next=%2Fapi%2Fitems"}, b"")) as server:
            code, out, err = self.run_against(server, ["items", "--no-relogin"])
        self.assertEqual(code, 4)
        self.assertEqual(len(server.requests), 1)

    def test_http_errors_are_answers_not_crashes(self):
        with LoopbackServer(lambda m, p, h, b: (404, {"Content-Type": "text/html"}, b"<html>spa</html>")) as server:
            code, out, err = self.run_against(server, ["items"])
        self.assertEqual(code, 1)
        self.assertIn("required query parameter", err)

    def test_connection_refused_is_a_network_error_with_a_hint(self):
        probe = socket.socket()
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
        probe.close()
        with mock.patch.object(cs, "BASE_URL", "http://127.0.0.1:%d/api" % port):
            code, out, err = self.run_cli(["--json", "items"])
        self.assertEqual(code, 1)
        error = json.loads(err)["error"]
        self.assertEqual(error["kind"], "network")
        self.assertTrue(error["hint"])

    def test_a_change_reaches_the_server_only_with_yes(self):
        reply = (201, {"Content-Type": "application/json"}, b'{"ok":1}')
        with LoopbackServer(lambda m, p, h, b: reply) as server:
            for flags in ([], ["--apply"], ["--dry-run", "--yes"]):
                self.run_against(server, ["api", "/things", "--method", "POST", "--data", '{"a": 1}'] + flags)
            self.assertEqual(server.requests, [], "dry run, refused --apply and --dry-run --yes sent nothing")
            code, out, err = self.run_against(server, ["api", "/things", "--method", "POST", "--data", '{"a": 1}', "--yes", "--json"])
        self.assertEqual(code, 0, err)
        self.assertEqual(len(server.requests), 1)
        request = server.requests[0]
        self.assertEqual((request["method"], request["path"]), ("POST", "/api/things"))
        self.assertEqual(request["headers"]["Content-Type"], "application/json")
        self.assertEqual(json.loads(request["body"]), {"a": 1})


# ------------------------------------------------------------------------------------------ our own generator
class GeneratorTests(unittest.TestCase):
    def test_gen_commands_sees_exactly_the_commands_in_the_source(self):
        source = SCRIPT.read_text(encoding="utf-8")
        regex_names = re.findall(r"""add_parser\(\s*["']([^"']+)["']""", source)
        result = subprocess.run([sys.executable, str(HERE / "gen_commands.py"), str(SCRIPT), "--json", "--strict"],
                                capture_output=True, text=True, encoding="utf-8", timeout=180)
        self.assertEqual(result.returncode, 0, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual([c["path"][-1] for c in data["commands"]], regex_names)
        self.assertEqual(regex_names, ["doctor", "login", "api", "items", "rename", "buy"])
        self.assertEqual(data["warnings"], [])


if __name__ == "__main__":
    unittest.main()
