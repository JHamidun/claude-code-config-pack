"""Tests for harvest.py. Offline: no browser, no network, no real credentials.

    python -m unittest test_harvest -v
    HARVEST_REAL=1 HARVEST_REAL_DIR=<folder with saved captures> python -m unittest test_harvest -v
        # plus a read-only parse of your own saved captures (prints nothing but pass/fail)

The capture flow runs against a fake browser engine (duck-typed pages, contexts and responses), so the
control flow, the redaction and the files written are checked without launching Chromium. What this
cannot prove is how a real Playwright behaves: that needs one run on a real service.
"""

import argparse
import base64
import contextlib
import io
import json
import os
import py_compile
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import harvest as h  # noqa: E402  (our own script)

SCRIPT = HERE / "harvest.py"
NOW = 1_800_000_000

SECRET_TOKEN = "tok_live_SENTINEL_0123456789abcdefghijklmnopqrstuvwxyz"
SECRET_COOKIE = "cookie-secret-SENTINEL"
SECRET_PASSWORD = "hunter2-SENTINEL"
SECRET_CARD = "4111111111111111-SENTINEL"
SECRET_LOGIN = "login-pass-SENTINEL-7"  # a password under a name the masker has to recognise or be told about
PII_EMAIL = "alice.sentinel@example.test"
PII_SUB = "user-sub-SENTINEL"


def b64(obj):
    return base64.urlsafe_b64encode(json.dumps(obj).encode()).decode().rstrip("=")


def make_jwt(**payload):
    return "%s.%s.%s" % (b64({"alg": "HS256", "typ": "JWT"}), b64(payload), "sig-SENTINEL-abcdefghij")


JWT_WT = make_jwt(iat=NOW, exp=NOW + 86400, typ="WT", sub=PII_SUB)
SENTINELS = (SECRET_TOKEN, SECRET_COOKIE, SECRET_PASSWORD, SECRET_CARD, SECRET_LOGIN, PII_SUB, JWT_WT, "sig-SENTINEL")


def assert_clean(case, text, extra=()):
    for s in SENTINELS + tuple(extra):
        case.assertNotIn(s, text)


def run_main(argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = h.main(argv)
    return code, out.getvalue(), err.getvalue()


def entry(method, url, status=200, body=None, req_body=None, route="", ctype="application/json", req_headers=None):
    e = {"method": method, "url": url, "status": status, "route": route, "resource_type": "xhr",
         "req_headers": req_headers or {}, "resp_content_type": ctype}
    if body is not None:
        e["resp_body"] = body if isinstance(body, str) else json.dumps(body)
    if req_body is not None:
        e["req_body"] = req_body if isinstance(req_body, str) else json.dumps(req_body)
    return e


API = "https://app.example.test"


def fixture_entries():
    return [
        entry("GET", API + "/api/v1/items?page=1&per_page=20", body={"items": [{"id": 1, "name": "a", "owner": {"email": PII_EMAIL}}], "total": 1}, route="#/items"),
        entry("GET", API + "/api/v1/items?page=2&per_page=20", body={"items": [{"id": 2, "name": "b", "owner": None}], "total": 2}, route="#/items"),
        entry("GET", API + "/api/v1/items/123456", body={"id": 123456, "name": "x"}),
        entry("GET", API + "/api/v1/items/987654", body={"id": 987654, "name": "y"}),
        entry("GET", API + "/api/v1/items/777?x=1", status=404, ctype="text/html", body="<!doctype html><html>spa</html>"),
        entry("POST", API + "/api/v1/orders", status=201, body={"order": 1},
              req_body={"sku": "A1", "qty": 2, "card_number": SECRET_CARD}),
        entry("POST", API + "/api/v1/orders", status=201, body={"order": 2}, req_body={"sku": "B2", "qty": 1}),
        entry("POST", API + "/search/run", ctype="application/json", body={"sid": "s1"},
              req_body="query=abc&hash=def", req_headers={"content-type": "application/x-www-form-urlencoded"}),
        entry("GET", API + "/api/auth/session", body={"user": {"name": "Alice"}, "accessToken": SECRET_TOKEN, "expires": "2026-12-01"}),
        entry("GET", "https://cdn.example.test/api/v2/config", body={"flags": {"a": True}}),
        entry("OPTIONS", API + "/api/v1/items", status=204),
    ]


# --------------------------------------------------------------------------------------- redaction
class RedactionTests(unittest.TestCase):
    def test_text_masks_jwt_bearer_and_long_tokens_but_keeps_short_ids(self):
        text = "t=%s b=Bearer abcdefgh12345678 long=%s id=12345 path=/api/v1/items" % (JWT_WT, SECRET_TOKEN)
        out = h.redact_text(text)
        assert_clean(self, out)
        self.assertIn("<jwt>", out)
        self.assertIn("Bearer <redacted>", out)
        self.assertIn("id=12345", out)
        self.assertIn("/api/v1/items", out)

    def test_json_masks_sensitive_keys_at_any_depth_and_keeps_names(self):
        obj = {"user": "alice", "password": SECRET_PASSWORD, "nested": {"accessToken": SECRET_TOKEN, "list": [{"api_key": "k1", "n": 1}]},
               "cookies": [{"name": "a", "value": SECRET_COOKIE}], "ok": True}
        out = h.redact_json(obj)
        text = json.dumps(out)
        assert_clean(self, text)
        self.assertEqual(out["user"], "alice")
        self.assertEqual(out["password"], "<redacted>")
        self.assertEqual(out["nested"]["accessToken"], "<redacted>")
        self.assertEqual(out["nested"]["list"][0]["n"], 1)
        self.assertIs(out["ok"], True)

    def test_body_json_form_and_truncated_json(self):
        js = h.redact_body(json.dumps({"password": SECRET_PASSWORD, "a": 1}), "application/json")
        self.assertNotIn(SECRET_PASSWORD, js)
        self.assertIn('"a": 1', js)
        form = h.redact_body("user=alice&password=%s&page=2" % SECRET_PASSWORD, "application/x-www-form-urlencoded")
        self.assertEqual(form, "user=alice&password=<redacted>&page=2")
        cut = h.redact_body('{"items": [1,2,3], "token": "%s", "more": "tru' % SECRET_TOKEN, "application/json")
        self.assertNotIn(SECRET_TOKEN, cut)

    def test_url_masks_sensitive_query_values_only(self):
        url = "https://api.example.test/v1/items?token=%s&page=2&sig=abc&q=hello" % SECRET_COOKIE
        out = h.redact_url(url)
        self.assertNotIn(SECRET_COOKIE, out)
        self.assertIn("token=<redacted>", out)
        self.assertIn("sig=<redacted>", out)
        self.assertIn("page=2", out)
        self.assertIn("q=hello", out)

    def test_url_masks_a_query_inside_the_hash_route(self):
        url = "https://app.example.test/#/billing?access_token=%s&tab=2" % SECRET_COOKIE
        out = h.redact_url(url)
        self.assertNotIn(SECRET_COOKIE, out)
        self.assertEqual(out, "https://app.example.test/#/billing?access_token=<redacted>&tab=2")
        self.assertEqual(h.redact_url("https://app.example.test/api/v1/items"), "https://app.example.test/api/v1/items")

    def test_headers_keep_scheme_and_cookie_names_not_values(self):
        out = h.redact_headers({
            "Authorization": "Bearer " + SECRET_TOKEN, "cookie": "oauth-token=%s; __C=zz" % SECRET_COOKIE,
            "set-cookie": "sid=%s; Path=/; HttpOnly" % SECRET_COOKIE, "x-csrf-token": "abc", "x-device-id": "dev-1",
            "referer": "https://app.example.test/",
        })
        assert_clean(self, json.dumps(out))
        self.assertEqual(out["Authorization"], "Bearer <redacted>")
        self.assertIn("oauth-token", out["cookie"])
        self.assertIn("__C", out["cookie"])
        self.assertIn("sid", out["set-cookie"])
        self.assertEqual(out["x-csrf-token"], "<redacted>")
        self.assertEqual(out["x-device-id"], "dev-1")
        self.assertEqual(out["referer"], "https://app.example.test/")

    PASSWORD_NAMES = (
        "password", "Password", "passwd", "pass", "pwd", "senha", "Senha", "senhaAtual", "nova_senha", "pw", "passcode",
        "pass_phrase", "passphrase", "user_pwd", "new_password", "oldPass", "login_pass", "userpass", "mot_de_passe",
        "clave", "contrasena", "contraseña", "palavra-passe", "kennwort", "parol", "пароль", "otp", "otp_code", "OTPCode",
        "otpcode", "totp", "pin", "jwt", "sessid",
    )

    def test_password_words_in_other_languages_and_compound_names_are_masked(self):
        """A password called 'senha', 'user_pwd' or 'oldPass' is a password: JSON, form, query, header and cut-off JSON alike."""
        for name in self.PASSWORD_NAMES:
            with self.subTest(name=name):
                self.assertNotIn(SECRET_LOGIN, json.dumps(h.redact_json({name: SECRET_LOGIN}), ensure_ascii=False))
                self.assertNotIn(SECRET_LOGIN, h.redact_form("user=a&%s=%s&page=2" % (name, SECRET_LOGIN)))
                self.assertNotIn(SECRET_LOGIN, h.redact_url("https://app.example.test/api/x?%s=%s&page=2" % (name, SECRET_LOGIN)))
                self.assertNotIn(SECRET_LOGIN, json.dumps(h.redact_headers({"X-" + name: SECRET_LOGIN}), ensure_ascii=False))
                cut = '{"a": 1, "%s": "%s", "tr' % (name, SECRET_LOGIN)
                self.assertNotIn(SECRET_LOGIN, h.redact_body(cut, "application/json"))
        self.assertEqual(h.redact_form("user=a&senha=%s&page=2" % SECRET_LOGIN), "user=a&senha=<redacted>&page=2")
        self.assertEqual(h.redact_headers({"X-Senha": SECRET_LOGIN, "X-Pwd": SECRET_LOGIN}), {"X-Senha": "<redacted>", "X-Pwd": "<redacted>"})

    def test_short_roots_match_whole_words_so_ordinary_names_survive(self):
        """'pass', 'otp', 'pin', 'clave', 'sid' are masked as words, never as pieces of 'passenger', 'footprint', 'spinner'."""
        plain = {"passenger": "Bob", "passport": "AB123", "footprint": "x", "spinner": "y", "enclave": "z", "inside": "a", "side": "left",
                 "residence": "city", "provider": "google", "consider": "yes", "author": "ann", "optional": "no", "name": "Alice",
                 "email": PII_EMAIL, "page": 2, "per_page": 20, "status": "ok", "sort_key": "name", "x-device-id": "d-1"}
        self.assertEqual(h.redact_json(plain), plain)
        self.assertEqual(h.redact_headers({"X-Custom-Header": "v", "X-Forwarded-For": "YOUR_PUBLIC_IP"}), {"X-Custom-Header": "v", "X-Forwarded-For": "YOUR_PUBLIC_IP"})
        self.assertEqual(h.redact_form("passenger=Bob&footprint=1&page=2"), "passenger=Bob&footprint=1&page=2")

    def test_code_ticket_and_sid_are_masked_only_when_the_value_looks_like_a_credential(self):
        """'code' is also country_code and status_code: a one-time code, a CAS ticket and a session id go, prose and small numbers stay."""
        masked = {"code": "123456", "verification_code": "Zx9-S3cret", "codigo": "654321", "ticket": "ST-1234-abcdef", "sid": "kqLp3Zx8aBc", "auth_code": "4/0AXabc123"}
        out = h.redact_json(masked)
        self.assertEqual(set(out.values()), {"<redacted>"})
        kept = {"code": 200, "status_code": 404, "country_code": "BR", "currency_code": "BRL", "error_code": "not_found", "sid": "s1",
                "ticket": {"id": 5, "subject": "printer broken"}, "ticket_subject": "Printer is broken", "ticket_id": 5}
        self.assertEqual(h.redact_json(kept), kept, "a helpdesk ticket object keeps its structure")
        self.assertEqual(h.redact_url("https://app.example.test/cb?code=%s&state=ok&country_code=BR" % SECRET_LOGIN),
                         "https://app.example.test/cb?code=<redacted>&state=ok&country_code=BR")
        self.assertEqual(h.redact_headers({"X-Verification-Code": SECRET_LOGIN, "X-Sid": SECRET_LOGIN})["X-Sid"], "<redacted>")

    def test_a_name_value_pair_hides_the_value_when_the_name_is_secret(self):
        """Cookie lists, HAR headers and form-field arrays carry the secret name as DATA: {"name": "access_token", "value": ...}."""
        body = {"storage": [{"name": "access_token", "value": SECRET_LOGIN}, {"name": "theme", "value": "dark"}],
                "headers": [{"name": "Authorization", "value": "Bearer abcdefgh12345678"}, {"name": "Accept", "value": "*/*"}],
                "fields": [{"key": "senha", "val": SECRET_LOGIN}, {"field": "page", "value": 2}, {"name": "Alice", "value": 5}]}
        out = h.redact_json(body)
        self.assertNotIn(SECRET_LOGIN, json.dumps(out))
        self.assertNotIn("abcdefgh12345678", json.dumps(out))
        self.assertEqual(out["storage"], [{"name": "access_token", "value": "<redacted>"}, {"name": "theme", "value": "dark"}])
        self.assertEqual(out["headers"][1], {"name": "Accept", "value": "*/*"})
        self.assertEqual(out["fields"][1:], [{"field": "page", "value": 2}, {"name": "Alice", "value": 5}])

    def test_strings_that_hold_json_a_form_or_a_url_are_redacted_inside(self):
        out = h.redact_json({
            "payload": json.dumps({"senha": SECRET_LOGIN, "x": 1}),
            "data": "username=a&senha=%s" % SECRET_LOGIN,
            "redirect": "https://app.example.test/cb?code=%s&state=ok" % SECRET_LOGIN,
            "note": "plain text, nothing to hide",
            "filter": "status=active",
        })
        self.assertNotIn(SECRET_LOGIN, json.dumps(out))
        self.assertEqual(json.loads(out["payload"]), {"senha": "<redacted>", "x": 1})
        self.assertEqual(out["data"], "username=a&senha=<redacted>")
        self.assertEqual((out["note"], out["filter"]), ("plain text, nothing to hide", "status=active"))

    def test_a_token_after_the_hash_without_a_question_mark_is_masked(self):
        """Implicit OAuth hands the token back as '#access_token=...&token_type=...', no '?' in sight."""
        url = "https://oauth.example.test/cb#access_token=%s&expires_in=3600" % SECRET_LOGIN
        self.assertEqual(h.redact_url(url), "https://oauth.example.test/cb#access_token=<redacted>&expires_in=3600")
        self.assertEqual(h.redact_url("https://app.example.test/#/billing"), "https://app.example.test/#/billing")

    def test_strict_mode_hides_every_value_of_a_login_body_and_keeps_the_keys(self):
        """The safety net for names nobody listed: whatever the password field is called, it is masked in a login request."""
        js = json.loads(h.redact_body(json.dumps({"email": PII_EMAIL, "xyzzy": SECRET_LOGIN, "remember": True, "n": 3, "nested": {"q": "v"}}),
                                      "application/json", strict=True))
        self.assertEqual(js, {"email": "<redacted>", "xyzzy": "<redacted>", "remember": True, "n": "<redacted>", "nested": {"q": "<redacted>"}})
        self.assertEqual(h.redact_body("user=a&xyzzy=%s" % SECRET_LOGIN, "application/x-www-form-urlencoded", strict=True),
                         "user=<redacted>&xyzzy=<redacted>")
        self.assertEqual(h.redact_body("<login>%s</login>" % SECRET_LOGIN, "text/xml", strict=True), "<redacted:len=%d>" % len("<login>%s</login>" % SECRET_LOGIN))
        self.assertNotIn(SECRET_LOGIN, h.redact_body('{"email": "a", "xyzzy": "%s", "tr' % SECRET_LOGIN, "application/json", strict=True))
        # the normal mode keeps what is not secret
        self.assertEqual(json.loads(h.redact_body(json.dumps({"xyzzy": "v", "n": 3}), "application/json")), {"xyzzy": "v", "n": 3})
        for url in ("https://a.test/api/auth/login", "https://a.test/v1/session", "https://a.test/api/users/me/password", "https://a.test/oauth/token",
                    "https://a.test/api/signup", "https://a.test/api/auth/senha"):
            self.assertTrue(h.is_secret_body_url(url), url)
        for url in ("https://a.test/api/v1/items", "https://a.test/api/v1/orders?token=abc", "https://a.test/search/run"):
            self.assertFalse(h.is_secret_body_url(url), url)

    def test_the_recorder_masks_a_password_under_an_unknown_name_in_a_login_request_only(self):
        rec = make_recorder()
        body = json.dumps({"email": PII_EMAIL, "xyzzy": SECRET_LOGIN})
        for url in (API + "/api/auth/login", API + "/api/v1/things"):
            rec.on_response(FakeResponse(url, 200, {"content-type": "application/json"}, "{}",
                                         FakeRequest("POST", headers={"content-type": "application/json"}, post_data=body,
                                                     all_headers={"content-type": "application/json"})))
        login, other = rec.entries
        self.assertEqual(json.loads(login["req_body"]), {"email": "<redacted>", "xyzzy": "<redacted>"})
        self.assertEqual(json.loads(other["req_body"])["xyzzy"], SECRET_LOGIN, "not a login endpoint: only names the masker knows are hidden")
        keep = make_recorder(keep_secrets=True)
        keep.on_response(FakeResponse(API + "/api/auth/login", 200, {"content-type": "application/json"}, "{}",
                                      FakeRequest("POST", post_data=body)))
        self.assertIn(SECRET_LOGIN, keep.entries[0]["req_body"], "--keep-secrets is the only switch")

    @staticmethod
    def _post(rec, url, body, response="{}"):
        rec.on_response(FakeResponse(url, 200, {"content-type": "application/json"}, response,
                                     FakeRequest("POST", headers={"content-type": "application/json"}, post_data=body,
                                                 all_headers={"content-type": "application/json"})))
        return rec.entries[-1]

    def test_login_addresses_of_other_frameworks_and_languages_get_the_strict_request_mask(self):
        """Devise (/users/sign_in), Portuguese, ASP.NET and German login addresses: a field nobody listed ({'u','p'}) is still hidden."""
        body = json.dumps({"u": PII_EMAIL, "p": SECRET_LOGIN})
        for path in ("/users/sign_in", "/entrar", "/acesso", "/Account/Logon", "/ANMELDEN", "/users/sign_up", "/api/log_in"):
            self.assertTrue(h.is_secret_body_url(API + path), path)
            sent = json.loads(self._post(make_recorder(all_xhr=True), API + path, body)["req_body"])
            self.assertEqual(sent, {"u": "<redacted>", "p": "<redacted>"}, path)
        # strict stays reserved for login-like paths: an ordinary endpoint keeps its harmless values
        self.assertFalse(h.is_secret_body_url(API + "/api/v1/things"))
        self.assertFalse(h.is_secret_body_url(API + "/graphql"), "no body, nothing that names a login")
        self.assertEqual(json.loads(self._post(make_recorder(all_xhr=True), API + "/api/v1/things", body)["req_body"])["u"], PII_EMAIL)

    def test_graphql_is_strict_only_when_the_operation_names_a_login(self):
        login = json.dumps({"query": 'mutation{login(email:"a@b.c",password:"%s"){token}}' % SECRET_LOGIN})
        named = json.dumps({"operationName": "SignIn", "query": "mutation SignIn($i: In!){ go(input: $i){ ok } }",
                            "variables": {"i": {"u": "a", "p": SECRET_LOGIN}}})
        plain = json.dumps({"operationName": "Books", "query": "query Books { books { id title author { name } } }", "variables": {"page": 2}})
        self.assertTrue(h.is_secret_body_url(API + "/graphql", login))
        self.assertTrue(h.is_secret_body_url(API + "/GraphQL", named), "case does not matter")
        self.assertTrue(h.is_secret_body_url(API + "/graphql?query=mutation%7Blogin(password:%22x%22)%7D"), "a GET carries the text in the query string")
        self.assertFalse(h.is_secret_body_url(API + "/graphql", plain), "'author' is not 'auth': an ordinary query keeps its body")
        for body in (login, named):
            self.assertNotIn(SECRET_LOGIN, self._post(make_recorder(), API + "/graphql", body)["req_body"])
        self.assertEqual(self._post(make_recorder(), API + "/graphql", plain)["req_body"], plain)

    def test_a_login_response_hides_any_token_shaped_value_whatever_the_field_is_called(self):
        opaque = "9f86d081884c7d659a2feaa0c55ad015"  # 32 characters: shorter than the 40-character opaque-token mask
        user = {"name": "Alice Smith", "email": PII_EMAIL, "id": 7, "role": "admin"}
        body = json.dumps({"access": opaque, "refresh": opaque, "t": opaque + "x", "user": user})
        masked = json.loads(h.redact_body(body, "application/json", tokens=True))
        self.assertEqual(masked, {"access": "<redacted>", "refresh": "<redacted>", "t": "<redacted>", "user": user},
                         "the keys and the ordinary values stay, only token-shaped strings go")
        self.assertIn(opaque, h.redact_body(body, "application/json"), "off unless the endpoint is login-like")
        cut = h.redact_body('{"access": "%s", "name": "Alice Smith", "tr' % opaque, "application/json", tokens=True)
        self.assertNotIn(opaque, cut)
        self.assertIn("Alice Smith", cut)
        rec = make_recorder(all_xhr=True)
        for path in ("/api/auth/login", "/users/sign_in", "/Account/Logon"):
            self.assertNotIn(opaque, self._post(rec, API + path, "{}", body)["resp_body"], path)
        self.assertIn(opaque, self._post(rec, API + "/api/v1/items", "{}", body)["resp_body"], "an ordinary API response is not touched")
        self.assertIn(opaque, self._post(make_recorder(keep_secrets=True), API + "/api/auth/login", "{}", body)["resp_body"], "--keep-secrets is the only switch")
        gql = json.dumps({"operationName": "Login", "query": "mutation Login { login { sessionish } }"})
        self.assertNotIn(opaque, self._post(make_recorder(), API + "/graphql", gql, json.dumps({"data": {"login": {"sessionish": opaque}}}))["resp_body"])


# --------------------------------------------------------------------------------------- jwt and auth hints
class JwtTests(unittest.TestCase):
    def test_claims_carry_lifetime_and_nothing_personal(self):
        claims = h.jwt_claims(JWT_WT)
        self.assertEqual(claims["typ"], "WT")
        self.assertEqual(claims["lifetime_s"], 86400)
        self.assertEqual(claims["exp"], NOW + 86400)
        self.assertNotIn(PII_SUB, json.dumps(claims))
        self.assertIsNone(h.jwt_claims("not-a-jwt"))
        self.assertIsNone(h.jwt_claims("YOUR_JWT_TOKEN"))

    def test_scan_finds_nested_tokens_like_a_workspace_list(self):
        obj = [{"workspaceToken": JWT_WT, "region": "x"}, {"refreshToken": make_jwt(iat=NOW, exp=NOW + 30 * 86400, typ="WRT")}]
        found = h.scan_jwts(obj)
        self.assertEqual([p for p, _ in found], ["$[0].workspaceToken", "$[1].refreshToken"])
        self.assertEqual(found[1][1]["lifetime_s"], 30 * 86400)

    def test_humanize(self):
        self.assertEqual(h.humanize_seconds(45), "45s")
        self.assertEqual(h.humanize_seconds(7200), "2h")
        self.assertEqual(h.humanize_seconds(86400 * 30), "30d")
        self.assertEqual(h.humanize_seconds(-3600), "-60m")

    def test_hints_describe_cookies_storage_and_headers_without_values(self):
        cookies = [
            {"name": "oauth-token", "domain": "app.example.test", "path": "/", "value": SECRET_COOKIE, "expires": NOW + 7200, "httpOnly": True, "secure": True, "sameSite": "Lax"},
            {"name": "sid", "domain": "app.example.test", "path": "/", "value": "x", "expires": -1},
            {"name": "jwtcookie", "domain": "app.example.test", "path": "/", "value": JWT_WT, "expires": NOW + 86400},
        ]
        storages = {
            "localStorage": {"ctbz-token": JWT_WT, "pld_123456789:workspaceList": json.dumps([{"workspaceToken": JWT_WT}]), "theme": "dark"},
            "sessionStorage": {},
        }
        entries = [
            {"method": "GET", "url": API + "/api/auth/session", "status": 200, "req_headers": {"authorization": "Bearer <redacted>", "x-device-id": "d", "cookie": "<cookie names: oauth-token, sid>"},
             "resp_body": json.dumps({"accessToken": "<redacted>", "expires": "e"}), "set_cookie_names": ["sid"]},
        ]
        hints = h.build_auth_hints(cookies, storages, entries, now=NOW)
        text = json.dumps(hints)
        assert_clean(self, text)
        by_name = {c["name"]: c for c in hints["cookies"]}
        self.assertEqual(by_name["oauth-token"]["expires_in"], "2h")
        self.assertTrue(by_name["sid"]["session_cookie"])
        self.assertEqual(by_name["jwtcookie"]["jwt"]["typ"], "WT")
        keys = {i["key"]: i for i in hints["storage"]["localStorage"]}
        self.assertEqual(keys["ctbz-token"]["kind"], "jwt")
        self.assertEqual(keys["ctbz-token"]["jwt"]["lifetime"], "24h")
        self.assertIn("<id>", " ".join(keys), "ids inside storage keys are masked")
        nested = [i for i in hints["storage"]["localStorage"] if i["kind"] == "json"][0]
        self.assertEqual(nested["jwt_paths"][0]["path"], "$[0].workspaceToken")
        self.assertEqual(hints["request_headers"]["authorization_schemes"], {"Bearer": 1})
        self.assertIn("x-device-id", hints["request_headers"]["custom_headers"])
        self.assertEqual(hints["request_headers"]["cookie_names_sent"], ["oauth-token", "sid"])
        self.assertEqual(hints["auth_endpoints"][0]["path"], "/api/auth/session")
        self.assertIn("accessToken", hints["auth_endpoints"][0]["response_keys"])
        self.assertTrue(any("Authorization header" in n for n in hints["notes"]))

    def test_cookie_only_session_is_called_out(self):
        hints = h.build_auth_hints([{"name": "sid", "domain": "d", "path": "/", "value": "v", "expires": NOW + 60}], {}, [], now=NOW)
        self.assertTrue(any("cookie-based" in n for n in hints["notes"]))

    def test_hints_mask_an_e_mail_or_an_id_inside_cookie_and_storage_names(self):
        """auth_hints.json is pasted into the api map: a name that embeds an address must not carry it there."""
        cookies = [{"name": "user:%s:prefs" % PII_EMAIL, "domain": "d", "path": "/", "value": "v", "expires": NOW + 60}]
        storages = {"localStorage": {"profile:%s" % PII_EMAIL: "x", "pld_123456789:list": "y"}, "sessionStorage": {}}
        entries = [{"method": "GET", "url": API + "/api/me", "status": 200, "set_cookie_names": ["track:%s" % PII_EMAIL],
                    "req_headers": {"cookie": "<cookie names: user:%s:prefs, sid>" % PII_EMAIL}}]
        hints = h.build_auth_hints(cookies, storages, entries, now=NOW)
        text = json.dumps(hints)
        self.assertNotIn(PII_EMAIL, text)
        self.assertNotIn("alice.sentinel", text)
        self.assertEqual(hints["request_headers"]["cookie_names_sent"], ["sid", "track:<email>", "user:<email>:prefs"])
        self.assertEqual(hints["cookies"][0]["name"], "user:<email>:prefs")
        self.assertEqual(sorted(i["key"] for i in hints["storage"]["localStorage"]), ["pld_<id>:list", "profile:<email>"])

    def test_an_e_mail_or_an_id_used_as_a_json_key_or_a_cookie_name_is_masked_in_every_output(self):
        """The path inside a JSON value (auth_hints.json) and the cookie names in the stored headers (api_map.json) follow the same rule as the key names."""
        token = make_jwt(iat=NOW, exp=NOW + 3600)
        info = h.describe_storage({"k": json.dumps({PII_EMAIL: {"idToken": token}, "ws_123456789": {"t": token}})}, NOW)
        self.assertEqual(sorted(i["path"] for i in info[0]["jwt_paths"]), ["$.<email>.idToken", "$.ws_<id>.t"])
        self.assertNotIn("alice.sentinel", json.dumps(info))
        hdr = h.redact_headers({"Cookie": "sid_%s=abc; other=def" % PII_EMAIL, "Set-Cookie": "track_%s=1; Path=/" % PII_EMAIL})
        self.assertEqual(hdr["Cookie"], "<cookie names: <email>, other>")
        self.assertEqual(hdr["Set-Cookie"], "<set-cookie names: <email>>")
        rec = make_recorder()
        rec.on_response(FakeResponse(API + "/api/me", 200, {"content-type": "application/json", "set-cookie": "track_%s=1; Path=/" % PII_EMAIL}, "{}",
                                     FakeRequest("GET", all_headers={"cookie": "other=1; sid_%s=abc" % PII_EMAIL})))
        stored = rec.entries[0]
        self.assertNotIn("alice.sentinel", json.dumps(stored))
        self.assertEqual(stored["req_headers"]["cookie"], "<cookie names: other, <email>>")
        self.assertEqual(stored["set_cookie_names"], ["<email>"])
        hints = h.build_auth_hints([], {}, rec.entries, now=NOW)
        self.assertEqual(hints["request_headers"]["cookie_names_sent"], ["<email>", "other"], "a masked last name must survive the round trip through the stored header")
        keep = make_recorder(keep_secrets=True)
        keep.on_response(FakeResponse(API + "/api/me", 200, {"content-type": "application/json", "set-cookie": "track_%s=1; Path=/" % PII_EMAIL}, "{}",
                                      FakeRequest("GET", all_headers={"cookie": "sid_%s=abc" % PII_EMAIL})))
        self.assertIn("alice.sentinel", json.dumps(keep.entries[0]), "--keep-secrets keeps the real names")


# --------------------------------------------------------------------------------------- filters and routes
class FilterAndRouteTests(unittest.TestCase):
    def test_host_suffix_include_exclude_and_all_xhr(self):
        hosts = ["example.test"]
        self.assertTrue(h.url_allowed("https://api.example.test/api/v1/x", hosts))
        self.assertFalse(h.url_allowed("https://notexample.test/api/v1/x", hosts))
        self.assertFalse(h.url_allowed("https://api.example.test/static/app.js", hosts))
        self.assertTrue(h.url_allowed("https://api.example.test/static/app.js", hosts, all_xhr=True))
        self.assertFalse(h.url_allowed("https://api.example.test/api/mixpanel/track", hosts))
        self.assertFalse(h.url_allowed("https://api.example.test/api/v1/x", ["other.test"]))
        self.assertTrue(h.url_allowed("https://anything.test/api/v1/x", []))

    def test_resolve_route(self):
        start = "https://app.example.test/panel/#/home"
        self.assertEqual(h.resolve_route(start, "#/billing"), "https://app.example.test/panel/#/billing")
        self.assertEqual(h.resolve_route(start, "/settings"), "https://app.example.test/settings")
        self.assertEqual(h.resolve_route(start, "reports"), "https://app.example.test/panel/reports")
        self.assertEqual(h.resolve_route(start, "https://other.test/x"), "https://other.test/x")

    def test_pick_routes_skips_unsafe_foreign_duplicate_and_files(self):
        start = "https://app.example.test/panel/#/home"
        hrefs = [
            start, "https://app.example.test/panel/#/billing", "https://app.example.test/panel/#/logout", "mailto:a@b.test",
            "https://evil.test/x", "https://app.example.test/panel/#/billing", "https://app.example.test/files/report.pdf",
            "https://app.example.test/panel/#/account/delete", "https://app.example.test/", "javascript:void(0)",
            "https://app.example.test/panel/#/settings", "https://app.example.test/sign-out",
        ]
        self.assertEqual(h.pick_routes(hrefs, start), ["https://app.example.test/panel/#/billing", "https://app.example.test/panel/#/settings"])
        self.assertEqual(h.pick_routes(hrefs, start, limit=1), ["https://app.example.test/panel/#/billing"])

    def test_gitignore_created_never_edited(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertEqual(h.ensure_gitignore(td, ["out/", ".profile/"]), "created")
            self.assertEqual(h.ensure_gitignore(td, ["out/", ".profile/"]), "ok")
            gi = Path(td) / ".gitignore"
            gi.write_text("node_modules/\n", encoding="utf-8")
            self.assertEqual(h.ensure_gitignore(td, ["out/", ".profile/"]), ["out/", ".profile/"])
            self.assertEqual(gi.read_text(encoding="utf-8"), "node_modules/\n")


# --------------------------------------------------------------------------------------- summarizing
class SummarizeTests(unittest.TestCase):
    def setUp(self):
        self.summary = h.summarize(fixture_entries())
        self.by = {(g["method"], g["path"]): g for g in self.summary["endpoints"]}

    def test_grouping_templating_and_options_dropped(self):
        self.assertEqual(self.summary["calls"], 10, "OPTIONS preflights are not counted")
        self.assertIn(("GET", "/api/v1/items/{n}"), self.by)
        self.assertEqual(self.by[("GET", "/api/v1/items/{n}")]["calls"], 3)
        self.assertEqual(self.by[("GET", "/api/v1/items")]["calls"], 2)
        self.assertEqual(sorted(self.summary["hosts"]), ["https://app.example.test", "https://cdn.example.test"])

    def test_query_names_and_always_present_marking(self):
        md = h.render_markdown(self.summary)
        self.assertIn("**`page`**", md)
        self.assertIn("**`per_page`**", md)
        one = self.by[("GET", "/api/v1/items/{n}")]
        self.assertEqual(one["query"], {"x": 1})
        self.assertNotIn("**`x`**", md, "present in 1 of 3 calls: not marked as always present")

    def test_shapes_merge_and_flags(self):
        items = self.by[("GET", "/api/v1/items")]
        self.assertEqual(items["resp_shape"]["items"][0]["owner"], {"email": "str"}, "object that is sometimes null keeps its structure")
        self.assertIn("html-404", self.by[("GET", "/api/v1/items/{n}")]["flags"])
        orders = self.by[("POST", "/api/v1/orders")]
        self.assertEqual({"mutating", "risky"}, orders["flags"] & {"mutating", "risky"})
        self.assertEqual(orders["req_shape"], {"sku": "str", "qty": "int", "card_number": "str"})
        self.assertEqual(self.by[("POST", "/search/run")]["req_shape"], {"query": "str", "hash": "str"})
        self.assertIn("auth", self.by[("GET", "/api/auth/session")]["flags"])

    def test_markdown_never_carries_values(self):
        md = h.render_markdown(self.summary, "Demo")
        assert_clean(self, md, extra=(PII_EMAIL, "Alice", "123456", "987654"))
        self.assertIn("\U0001F4E6", md)
        self.assertIn("| Метод | Путь |", md)
        self.assertIn("HTML 404 instead of JSON", md)
        self.assertIn("name suggests money", md)
        self.assertIn("accessToken", md)
        self.assertIn("owner.email", md)

    def test_json_summary_is_serializable(self):
        data = json.loads(json.dumps(h.jsonable_summary(self.summary)))
        self.assertEqual(len(data["endpoints"]), len(self.summary["endpoints"]))

    def test_dynamic_map_keys_with_ids_or_emails_are_masked(self):
        shape = h.json_shape({"users": {PII_EMAIL: {"n": 1}, "123456789": {"n": 2}}})
        text = json.dumps(shape)
        self.assertNotIn(PII_EMAIL, text)
        self.assertNotIn("123456789", text)

    def test_merge_shape_types(self):
        self.assertEqual(h.merge_shape("str", "int"), "int|str")
        self.assertEqual(h.merge_shape("str", "null"), "null|str")
        self.assertEqual(h.merge_shape("null", {"a": "int"}), {"a": "int"})
        self.assertEqual(h.merge_shape({"a": "str"}, {"b": "int"}), {"a": "str", "b": "int"})
        self.assertEqual(h.merge_shape([], [{"a": 1}]), [{"a": 1}])

    def test_older_probe_shapes_are_understood(self):
        old = [
            {"m": "GET", "url": API + "/api/v1/things?id=1", "status": 200},
            {"method": "PUT", "url": API + "/api/v1/things/42/confirm", "status": 200, "body": '{"flag": false}'},
            {"method": "GET", "url": API + "/api/v1/stuff", "status": 200, "headers": {"accept": "application/json"}, "resp_body": '{"a": 1}'},
            {"url": ""},
            "junk",
        ]
        s = h.summarize(old)
        self.assertEqual(s["calls"], 3)
        by = {(g["method"], g["path"]): g for g in s["endpoints"]}
        self.assertEqual(by[("PUT", "/api/v1/things/{n}/confirm")]["req_shape"], {"flag": "bool"})
        self.assertEqual(by[("GET", "/api/v1/stuff")]["resp_shape"], {"a": "int"})

    def test_auth_flag_needs_a_real_auth_word_in_the_path(self):
        s = h.summarize([entry("GET", API + "/api/v1/lessons/1", body={"a": 1}), entry("GET", API + "/api/sso/start", body={"a": 1}),
                         entry("POST", API + "/api/auth/login", body={"a": 1})])
        flags = {g["path"]: g["flags"] for g in s["endpoints"]}
        self.assertNotIn("auth", flags["/api/v1/lessons/{n}"], "'sso' inside 'lessons' is not an SSO endpoint")
        self.assertIn("auth", flags["/api/sso/start"])
        self.assertIn("auth", flags["/api/auth/login"])

    def test_templatize_path(self):
        self.assertEqual(h.templatize_path("/api/v4/invoice/1234567890123456/download"), "/api/v4/invoice/{n}/download")
        self.assertEqual(h.templatize_path("/x/123e4567-e89b-12d3-a456-426614174000"), "/x/{uuid}")
        self.assertEqual(h.templatize_path("/x/deadbeefdeadbeefdead"), "/x/{hex}")
        self.assertEqual(h.templatize_path("/x/Ab3dEf6hIj9kLm2nOp5qRs8t"), "/x/{token}")
        self.assertEqual(h.templatize_path("/api/v4/items"), "/api/v4/items")


# --------------------------------------------------------------------------------------- bundles
JS_SAMPLE = """
!function(){var a="/api/v1/items",b='/api/v1/items/${id}/rename',c=`/rest/orders`,d="/assets/logo.png",
e="/static/js/app.js",f="https://api.example.test/graphql",g="https://www.google-analytics.com/collect",
h="/login",i="/x",j="/2026/10/04",k="https://api.other.test/v2/things";
function refund(r){return axios.post("/api/v1/orders/refund",{reason:r,token:"tok_live_SENTINEL_0123456789abcdefghijklmnopqrstuvwxyz"})}
}();
""" + ("// filler line to keep the next mention far away\n" * 40) + """
function noise(){return "the word refund in plain text with no http call near it at all, just prose to read"}
""" + ("// padding\n" * 60)


class BundleTests(unittest.TestCase):
    def test_paths_strong_first_and_noise_dropped(self):
        found = h.extract_paths_from_js(JS_SAMPLE)
        paths = [f["path"] for f in found]
        for good in ("/api/v1/items", "/api/v1/items/${id}/rename", "/rest/orders", "https://api.example.test/graphql",
                     "/api/v1/orders/refund", "/login"):
            self.assertIn(good, paths)
        for bad in ("/assets/logo.png", "/static/js/app.js", "/x", "/2026/10/04", "https://www.google-analytics.com/collect"):
            self.assertNotIn(bad, paths)
        strong = {f["path"]: f["strong"] for f in found}
        self.assertTrue(strong["/api/v1/items"])
        self.assertFalse(strong["/login"])
        flags = [f["strong"] for f in found]
        self.assertEqual(flags, sorted(flags, reverse=True), "strong paths come first")

    def test_host_filter_for_absolute_urls(self):
        paths = [f["path"] for f in h.extract_paths_from_js(JS_SAMPLE, hosts=["example.test"])]
        self.assertIn("https://api.example.test/graphql", paths)
        self.assertNotIn("https://api.other.test/v2/things", paths)

    def test_stub_detection_matches_the_106_byte_gotcha(self):
        self.assertTrue(h.is_stub("x" * 106))
        self.assertFalse(h.is_stub(JS_SAMPLE))

    def test_context_shows_the_call_next_to_the_word_and_masks_tokens(self):
        snippets = h.context_snippets(JS_SAMPLE, "refund")
        self.assertEqual(len(snippets), 2, "function name and path literal sit next to axios.post; the prose mention does not")
        self.assertTrue(all("axios.post" in sn for sn in snippets))
        for sn in snippets:
            assert_clean(self, sn)
        self.assertEqual(h.context_snippets(JS_SAMPLE, "nonexistentword"), [])


# --------------------------------------------------------------------------------------- recorder
class FakeRequest:
    def __init__(self, method="GET", rtype="xhr", headers=None, post_data=None, all_headers=None):
        self.method, self.resource_type, self.headers, self.post_data = method, rtype, headers or {}, post_data
        self._all = all_headers

    def all_headers(self):
        if self._all is None:
            raise RuntimeError("not available")
        return self._all


class FakeResponse:
    def __init__(self, url, status=200, headers=None, body="", request=None, text_raises=False):
        self.url, self.status, self.headers, self._body = url, status, headers or {}, body
        self.request, self._raises = request or FakeRequest(), text_raises

    def text(self):
        if self._raises:
            raise RuntimeError("body gone")
        return self._body


def make_recorder(**kw):
    return h.Recorder(kw.pop("hosts", ["example.test"]), **kw)


class RecorderTests(unittest.TestCase):
    def test_accepts_api_xhr_and_ignores_the_rest(self):
        rec = make_recorder()
        rec.on_response(FakeResponse(API + "/api/v1/items", body="{}", headers={"content-type": "application/json"}))
        rec.on_response(FakeResponse(API + "/static/app.js", request=FakeRequest(rtype="script")))
        rec.on_response(FakeResponse(API + "/logo.png", request=FakeRequest(rtype="image")))
        rec.on_response(FakeResponse(API + "/api/mixpanel/track", headers={"content-type": "application/json"}, body="{}"))
        rec.on_response(FakeResponse("https://other.test/api/v1/x", headers={"content-type": "application/json"}, body="{}"))
        rec.on_response(FakeResponse(API + "/page", request=FakeRequest(rtype="document")))
        self.assertEqual([e["url"] for e in rec.entries], [API + "/api/v1/items"])
        self.assertEqual(rec.scripts, [API + "/static/app.js"])

    def test_redacts_by_default(self):
        rec = make_recorder()
        req = FakeRequest("POST", headers={"content-type": "application/json", "authorization": "Bearer " + SECRET_TOKEN},
                          post_data=json.dumps({"password": SECRET_PASSWORD, "sku": "A"}),
                          all_headers={"content-type": "application/json", "authorization": "Bearer " + SECRET_TOKEN,
                                       "cookie": "sid=%s" % SECRET_COOKIE})
        rec.on_response(FakeResponse(API + "/api/v1/login?token=%s&page=1" % SECRET_COOKIE, 200,
                                     {"content-type": "application/json", "set-cookie": "sid=%s; Path=/" % SECRET_COOKIE},
                                     json.dumps({"accessToken": SECRET_TOKEN, "user": {"name": "a"}}), req))
        text = json.dumps(rec.entries)
        assert_clean(self, text)
        e = rec.entries[0]
        self.assertEqual(e["req_headers"]["authorization"], "Bearer <redacted>")
        self.assertIn("sid", e["req_headers"]["cookie"])
        self.assertEqual(e["set_cookie_names"], ["sid"])
        self.assertIn("page=1", e["url"])
        self.assertEqual(json.loads(e["resp_body"])["user"], {"name": "a"})
        self.assertEqual(e["status"], 200)

    def test_keep_secrets_is_the_only_switch(self):
        rec = make_recorder(keep_secrets=True)
        rec.on_response(FakeResponse(API + "/api/v1/x", 200, {"content-type": "application/json"}, json.dumps({"token": SECRET_TOKEN})))
        self.assertIn(SECRET_TOKEN, json.dumps(rec.entries))

    def test_falls_back_when_all_headers_is_missing_and_survives_broken_bodies(self):
        rec = make_recorder()
        rec.on_response(FakeResponse(API + "/api/v1/a", 200, {"content-type": "application/json"}, "", FakeRequest(headers={"x-device-id": "d"}), text_raises=True))
        self.assertEqual(rec.entries[0]["req_headers"], {"x-device-id": "d"})
        self.assertIn("resp_err", rec.entries[0])

        class Broken:
            @property
            def request(self):
                raise RuntimeError("boom")

        rec.on_response(Broken())  # must not raise
        self.assertEqual(len(rec.entries), 1)

    def test_response_cap_is_flagged(self):
        rec = make_recorder(max_resp=50)
        rec.on_response(FakeResponse(API + "/api/v1/big", 200, {"content-type": "application/json"}, json.dumps({"a": "x" * 500})))
        self.assertTrue(rec.entries[0]["resp_truncated"])
        self.assertEqual(rec.entries[0]["resp_len"], len(json.dumps({"a": "x" * 500})))

    def test_route_label_is_stored(self):
        rec = make_recorder()
        rec.route = "#/billing"
        rec.on_response(FakeResponse(API + "/api/v1/a", 200, {"content-type": "application/json"}, "{}"))
        self.assertEqual(rec.entries[0]["route"], "#/billing")

    def test_only_xhr_and_fetch_are_recorded_even_under_an_include_pattern(self):
        """A /api/ URL is not enough: an image, a document or a font behind such a URL is not an API call."""
        rec = make_recorder()
        for rtype in ("image", "document", "font", "stylesheet", "media", "websocket", "other"):
            rec.on_response(FakeResponse(API + "/api/v1/file-%s" % rtype, headers={"content-type": "application/json"}, body="{}",
                                         request=FakeRequest(rtype=rtype)))
        self.assertEqual(rec.entries, [])
        for rtype in ("xhr", "fetch"):
            rec.on_response(FakeResponse(API + "/api/v1/call-%s" % rtype, headers={"content-type": "application/json"}, body="{}",
                                         request=FakeRequest(rtype=rtype)))
        self.assertEqual([e["resource_type"] for e in rec.entries], ["xhr", "fetch"])


# --------------------------------------------------------------------------------------- capture flow with a fake engine
LOGIN_URL = API + "/login"


class FakeLocator:
    def __init__(self, n):
        self._n = n

    def count(self):
        return self._n


class FakeApiRequest:
    def __init__(self, bodies):
        self.bodies = bodies

    def get(self, url):
        body = self.bodies.get(url)
        return type("R", (), {"status": 200 if body is not None else 404, "text": lambda self_: body or ""})()


class FakePage:
    def __init__(self, ctx, need_login=False, login_after=3, hrefs=(), script=None, bodies=None, ready_count=1, fail_goto=False):
        self.ctx, self.need_login, self.login_after, self.fail_goto = ctx, need_login, login_after, fail_goto
        self.hrefs, self.script, self.ready_count = list(hrefs), script or {}, ready_count
        self.url, self.handlers, self.visited, self.polls = "about:blank", [], [], 0
        self.request = FakeApiRequest(bodies or {})
        self.shots = []

    def on(self, event, cb):
        if event == "response":
            self.handlers.append(cb)

    def goto(self, url, wait_until=None, timeout=None):
        if self.fail_goto:
            raise RuntimeError("net::ERR_NAME_NOT_RESOLVED")
        self.visited.append(url)
        self.url = LOGIN_URL if (self.need_login and len(self.visited) == 1) else url
        for resp in self.script.get(url, []):
            for cb in self.handlers:
                cb(resp)

    def wait_for_timeout(self, ms):
        self.polls += 1
        if self.need_login and self.url == LOGIN_URL and self.polls >= self.login_after:
            self.url = API + "/home"  # the human finished logging in

    def screenshot(self, path=None, full_page=None):
        Path(path).write_bytes(b"png")
        self.shots.append(path)

    def inner_text(self, selector):
        return "visible text"

    def evaluate(self, js):
        if "sessionStorage" in js:
            return {}
        return {"ctbz-token": JWT_WT, "theme": "dark"}

    def eval_on_selector_all(self, selector, js):
        return self.hrefs

    def locator(self, selector):
        return FakeLocator(self.ready_count)


class FakeContext:
    def __init__(self, page_factory):
        self.pages = [page_factory(self)]
        self.page_handlers, self.closed = [], False

    def new_page(self):
        raise AssertionError("the first page should be reused")

    def on(self, event, cb):
        self.page_handlers.append((event, cb))

    def cookies(self):
        return [{"name": "oauth-token", "domain": "app.example.test", "path": "/", "value": SECRET_COOKIE, "expires": NOW + 7200}]

    def close(self):
        self.closed = True


class FakePlaywright:
    def __init__(self, page_factory):
        self.page_factory, self.launch_kwargs, self.ctx = page_factory, None, None
        self.chromium = self

    def launch_persistent_context(self, **kwargs):
        self.launch_kwargs = kwargs
        self.ctx = FakeContext(self.page_factory)
        return self.ctx

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def json_resp(url, body, method="GET", status=200, post_data=None, headers=None, rtype="xhr"):
    req = FakeRequest(method, rtype, headers or {}, post_data, all_headers={"authorization": "Bearer " + SECRET_TOKEN, "cookie": "oauth-token=%s" % SECRET_COOKIE})
    return FakeResponse(url, status, {"content-type": "application/json", "set-cookie": "oauth-token=%s; Path=/" % SECRET_COOKIE},
                        json.dumps(body), req)


def default_script():
    return {
        API + "/": [json_resp(API + "/api/v1/me", {"name": "a", "email": PII_EMAIL})],
        API + "/#/billing": [
            json_resp(API + "/api/v1/invoices?page=1", {"items": [{"id": 1}], "token": SECRET_TOKEN}),
            json_resp(API + "/api/v1/invoices/pay", {"ok": True}, "POST", 201, json.dumps({"id": 1, "card_number": SECRET_CARD, "password": SECRET_PASSWORD})),
            FakeResponse(API + "/static/app.js", request=FakeRequest(rtype="script")),
        ],
    }


class CaptureFlowTests(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.work = Path(self.td.name)
        self.addCleanup(self.td.cleanup)
        self.fake = None
        self._orig = (h.load_engine, h.clock)
        h.clock = lambda: NOW

    def tearDown(self):
        h.load_engine, h.clock = self._orig

    def run_capture(self, extra=(), out="out", url_suffix="", **page_kw):
        script = page_kw.pop("script", default_script())

        def factory(ctx):
            return FakePage(ctx, script=script, **page_kw)

        self.fake = FakePlaywright(factory)
        h.load_engine = lambda name: (lambda: self.fake)
        argv = ["capture", "--url", API + "/" + url_suffix, "--out", str(self.work / out), "--profile", str(self.work / ".profile"),
                "--wait-ms", "1", "--login-wait", "6"] + list(extra)
        code, out, err = run_main(argv)
        return code, err

    def out_files(self):
        return {p.name: p for p in (self.work / "out").glob("*") if p.is_file()}

    def test_logged_in_walk_writes_clean_outputs(self):
        code, err = self.run_capture(["--route", "#/billing"])
        self.assertEqual(code, 0, err)
        files = self.out_files()
        self.assertTrue({"api_map.json", "endpoints.md", "auth_hints.json", "routes.json"} <= set(files))
        entries = json.loads(files["api_map.json"].read_text(encoding="utf-8"))
        self.assertEqual([e["url"].split("?")[0].replace(API, "") for e in entries], ["/api/v1/me", "/api/v1/invoices", "/api/v1/invoices/pay"])
        self.assertEqual(entries[1]["route"], "#/billing")
        for name in ("api_map.json", "endpoints.md", "auth_hints.json", "routes.json"):
            assert_clean(self, files[name].read_text(encoding="utf-8"))
        md = files["endpoints.md"].read_text(encoding="utf-8")
        self.assertNotIn(PII_EMAIL, md)
        self.assertIn("/api/v1/invoices", md)
        self.assertIn("name suggests money", md)
        hints = json.loads(files["auth_hints.json"].read_text(encoding="utf-8"))
        self.assertEqual(hints["cookies"][0]["expires_in"], "2h")
        self.assertEqual(hints["storage"]["localStorage"][0]["jwt"]["lifetime"], "24h")
        self.assertEqual(json.loads(files["routes.json"].read_text(encoding="utf-8"))["visited"], [API + "/#/billing"])
        self.assertTrue(self.fake.ctx.closed)

    def test_launch_arguments_and_gitignore(self):
        self.run_capture()
        kw = self.fake.launch_kwargs
        self.assertFalse(kw["headless"], "headed by default: headless gets bundle stubs")
        self.assertEqual(kw["user_data_dir"], str(self.work / ".profile"))
        self.assertIn("--disable-blink-features=AutomationControlled", kw["args"])
        gi = (self.work / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("out/", gi)
        self.assertIn(".profile/", gi)
        self.run_capture(["--headless"])
        self.assertTrue(self.fake.launch_kwargs["headless"])

    def test_waits_for_a_human_login(self):
        code, err = self.run_capture(["--route", "#/billing"], need_login=True, login_after=3)
        self.assertEqual(code, 0, err)
        self.assertIn("log in by hand", err)
        self.assertTrue((self.work / "out" / "api_map.json").exists())

    def test_login_never_completed_is_exit_4_and_writes_no_map(self):
        code, err = self.run_capture(need_login=True, login_after=10 ** 9)
        self.assertEqual(code, 4)
        self.assertIn("NEXT:", err)
        self.assertFalse((self.work / "out" / "api_map.json").exists())
        self.assertTrue(self.fake.ctx.closed)

    def test_headless_without_session_fails_fast(self):
        code, err = self.run_capture(["--headless"], need_login=True, login_after=3)
        self.assertEqual(code, 4)
        self.assertIn("without --headless", err)

    def test_ready_selector_overrides_url_check(self):
        code, err = self.run_capture(["--ready-selector", "#app-menu"], need_login=False, ready_count=0, login_after=10 ** 9)
        self.assertEqual(code, 4, "selector never appears: not logged in even though the URL has no login hint")
        code, err = self.run_capture(["--ready-selector", "#app-menu"], ready_count=1)
        self.assertEqual(code, 0, err)

    def test_login_only_warms_the_session_without_walking_routes(self):
        code, err = self.run_capture(["--login-only", "--route", "#/billing"])
        self.assertEqual(code, 0, err)
        self.assertIn("auth_hints.json", set(self.out_files()))
        self.assertEqual(self.fake.ctx.pages[0].visited, [API + "/"], "only the start page, no route walk")
        entries = json.loads((self.work / "out" / "api_map.json").read_text(encoding="utf-8"))
        self.assertEqual([e["url"].replace(API, "") for e in entries], ["/api/v1/me"], "what the login page itself called is still recorded")
        self.assertEqual(json.loads((self.work / "out" / "routes.json").read_text(encoding="utf-8"))["visited"], [])

    def test_discover_never_visits_logout_or_delete(self):
        hrefs = [API + "/#/billing", API + "/#/logout", API + "/#/account/delete", API + "/#/reports", "https://evil.test/x"]
        code, err = self.run_capture(["--discover", "--route", "/#/reports"], hrefs=hrefs)
        self.assertEqual(code, 0, err)
        visited = self.fake.ctx.pages[0].visited
        self.assertEqual(visited[1:], [API + "/#/reports", API + "/#/billing"])
        self.assertFalse(any("logout" in v or "delete" in v or "evil" in v for v in visited))

    def test_explicit_unsafe_route_is_refused_too(self):
        code, err = self.run_capture(["--route", "#/logout", "--route", "#/billing"])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.fake.ctx.pages[0].visited[1:], [API + "/#/billing"])

    def test_a_named_route_that_looks_unsafe_is_reported_and_allow_route_visits_it(self):
        code, err = self.run_capture(["--route", "#/cancel-subscription?token=%s" % SECRET_LOGIN, "--route", "#/billing"])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.fake.ctx.pages[0].visited[1:], [API + "/#/billing"])
        self.assertIn("[skip]", err, "a route the user asked for is never dropped in silence")
        self.assertIn("cancel-subscription", err)
        self.assertIn("--allow-route", err)
        self.assertNotIn(SECRET_LOGIN, err, "the skip line is redacted like every other output")
        code, err = self.run_capture(["--route", "#/billing", "--allow-route", "#/cancel-subscription"])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.fake.ctx.pages[0].visited[1:], [API + "/#/billing", API + "/#/cancel-subscription"])
        self.assertNotIn("[skip]", err)

    def test_discover_stays_silent_about_links_it_filters_out_and_still_never_visits_them(self):
        code, err = self.run_capture(["--discover"], hrefs=[API + "/#/logout", API + "/#/reports"])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.fake.ctx.pages[0].visited[1:], [API + "/#/reports"])
        self.assertNotIn("[skip]", err)

    def test_sso_inside_a_word_is_not_a_login_page(self):
        """The default login hint 'sso' sat inside '/lessons/1': a logged-in landing page waited out the whole --login-wait."""
        code, err = self.run_capture(url_suffix="lessons/1")
        self.assertEqual(code, 0, err)
        self.assertNotIn("log in by hand", err)
        args = argparse.Namespace(ready_selector=None, login_hint=list(h.DEFAULT_LOGIN_HINTS))
        for url, expected in ((API + "/lessons/1", True), (API + "/associates/2", True), (API + "/dashboard", True),
                              ("https://sso.example.test/start", False), (API + "/auth/sso/callback", False), (API + "/login?next=/", False),
                              (API + "/signin", False), ("https://accounts.example.test/sign-in", False)):
            page = FakePage(None)
            page.url = url
            self.assertEqual(h.logged_in(page, args), expected, url)

    def test_gitignore_is_written_in_each_folder_when_out_and_profile_are_apart(self):
        """Both folders hold a live session: with different parents each parent gets its own .gitignore (or a warning)."""
        code, err = self.run_capture(out="a/out")  # the profile stays in work/.profile: another parent folder
        self.assertEqual(code, 0, err)
        self.assertIn("out/", (self.work / "a" / ".gitignore").read_text(encoding="utf-8"))
        self.assertIn(".profile/", (self.work / ".gitignore").read_text(encoding="utf-8"))
        self.assertIn("[git] wrote", err)
        (self.work / "b").mkdir()
        (self.work / "b" / ".gitignore").write_text("node_modules/\n", encoding="utf-8")
        code, err = self.run_capture(out="b/out")
        self.assertEqual(code, 0, err)
        self.assertIn("WARNING", err, "an existing .gitignore is never edited, but the missing entry is reported")
        self.assertEqual((self.work / "b" / ".gitignore").read_text(encoding="utf-8"), "node_modules/\n")

    def test_a_login_request_with_a_password_under_any_name_leaves_nothing_in_out(self):
        script = default_script()
        script[API + "/"] += [
            json_resp(API + "/api/auth/login", {"ok": True}, "POST", 200, json.dumps({"email": PII_EMAIL, "senha": SECRET_LOGIN})),
            json_resp(API + "/api/auth/entrar", {"ok": True}, "POST", 200, json.dumps({"login": "a", "xyzzy": SECRET_LOGIN})),
            json_resp(API + "/api/auth/form", {"ok": True}, "POST", 200, "user=a&frobnicate=%s" % SECRET_LOGIN),
        ]
        code, err = self.run_capture(script=script)
        self.assertEqual(code, 0, err)
        for name in ("api_map.json", "endpoints.md", "auth_hints.json", "routes.json"):
            self.assertNotIn(SECRET_LOGIN, (self.work / "out" / name).read_text(encoding="utf-8"), name)
        entries = {e["url"].replace(API, ""): e for e in json.loads((self.work / "out" / "api_map.json").read_text(encoding="utf-8"))}
        self.assertEqual(set(json.loads(entries["/api/auth/entrar"]["req_body"])), {"login", "xyzzy"}, "the keys stay: they are the shape of the call")
        self.assertEqual(entries["/api/auth/form"]["req_body"], "user=<redacted>&frobnicate=<redacted>")

    def test_keep_secrets_and_save_session_are_explicit(self):
        code, err = self.run_capture(["--route", "#/billing", "--keep-secrets", "--save-session"])
        self.assertEqual(code, 0, err)
        self.assertIn("--keep-secrets", err)
        self.assertIn(SECRET_TOKEN, (self.work / "out" / "api_map.json").read_text(encoding="utf-8"))
        self.assertIn(SECRET_COOKIE, (self.work / "out" / "session.raw.json").read_text(encoding="utf-8"))
        code, err = self.run_capture(["--route", "#/billing"], out="out-default")
        self.assertEqual(code, 0, err)
        self.assertFalse((self.work / "out-default" / "session.raw.json").exists(), "raw session only with --save-session")
        assert_clean(self, (self.work / "out-default" / "api_map.json").read_text(encoding="utf-8"))

    def test_screenshots_and_text_are_opt_in(self):
        self.run_capture(["--route", "#/billing"], out="plain")
        self.assertFalse((self.work / "plain" / "shots").exists())
        self.assertEqual(list((self.work / "plain").glob("text_*.txt")), [])
        code, err = self.run_capture(["--route", "#/billing", "--shots", "--save-text"], out="rich")
        self.assertEqual(code, 0, err)
        self.assertEqual(len(list((self.work / "rich" / "shots").glob("*.png"))), 1)
        self.assertEqual(len(list((self.work / "rich").glob("text_*.txt"))), 1)

    def test_bundles_are_fetched_stubs_flagged_and_paths_listed(self):
        script = default_script()
        script[API + "/#/billing"] += [FakeResponse(API + "/static/stub.js", request=FakeRequest(rtype="script"))]
        bodies = {API + "/static/app.js": JS_SAMPLE, API + "/static/stub.js": "x" * 106}
        code, err = self.run_capture(["--route", "#/billing", "--bundles"], script=script, bodies=bodies)
        self.assertEqual(code, 0, err)
        info = json.loads((self.work / "out" / "bundle_endpoints.json").read_text(encoding="utf-8"))
        self.assertEqual(len(info["stubs"]), 1)
        self.assertEqual(len(info["files"]), 1)
        listed = [p["path"] for paths in info["files"].values() for p in paths]
        self.assertIn("/api/v1/orders/refund", listed)
        self.assertEqual(len(list((self.work / "out" / "bundles").glob("*.js"))), 1)
        self.assertIn("stub", err)

    def test_start_page_that_does_not_open_is_a_clear_exit_1(self):
        code, err = self.run_capture(fail_goto=True)
        self.assertEqual(code, 1)
        self.assertIn("cannot open", err)
        self.assertIn("NEXT:", err)
        self.assertNotIn("Traceback", err)
        self.assertTrue(self.fake.ctx.closed)

    def test_out_or_profile_inside_the_skill_folder_is_refused_before_anything_is_created(self):
        h.load_engine = lambda name: (_ for _ in ()).throw(AssertionError("the engine must not be loaded"))
        inside_out = h.SKILL_DIR / "scripts" / "out-must-not-exist"
        inside_profile = h.SKILL_DIR / ".profile-must-not-exist"
        code, out, err = run_main(["capture", "--url", API + "/", "--out", str(inside_out), "--profile", str(self.work / "p")])
        self.assertEqual(code, 2)
        self.assertIn("inside the skill folder", err)
        code, out, err = run_main(["capture", "--url", API + "/", "--out", str(self.work / "o"), "--profile", str(inside_profile)])
        self.assertEqual(code, 2)
        self.assertFalse(inside_out.exists())
        self.assertFalse(inside_profile.exists())

    def test_skill_folder_is_found_by_its_skill_md_and_a_copied_script_is_not_guarded(self):
        self.assertEqual(h.SKILL_DIR, HERE.parent, "the real skill folder is the one with SKILL.md")
        (self.work / "skill" / "scripts").mkdir(parents=True)
        (self.work / "skill" / "SKILL.md").write_text("---\nname: x\n---\n", encoding="utf-8")
        script = self.work / "skill" / "scripts" / "harvest.py"
        script.write_text("", encoding="utf-8")
        self.assertEqual(h.find_skill_dir(script), (self.work / "skill").resolve())
        # a script copied into a service folder (no SKILL.md above it) must not refuse its own out/ and .profile/
        copied = self.work / "tools" / "service-re" / "harvest.py"
        copied.parent.mkdir(parents=True)
        copied.write_text("", encoding="utf-8")
        self.assertIsNone(h.find_skill_dir(copied))
        self.assertFalse(h.inside(copied.parent / "out", None))
        self.assertTrue(h.inside(self.work / "skill" / "scripts" / "out", (self.work / "skill").resolve()))

    def test_missing_routes_file_is_exit_2_before_the_browser_starts(self):
        h.load_engine = lambda name: (_ for _ in ()).throw(AssertionError("the engine must not be loaded"))
        code, out, err = run_main(["capture", "--url", API + "/", "--out", str(self.work / "o"), "--profile", str(self.work / "p"),
                                   "--routes-file", str(self.work / "no-such-routes.txt")])
        self.assertEqual(code, 2)
        self.assertIn("NEXT:", err)

    def test_routes_file_is_read_and_comments_are_skipped(self):
        rf = self.work / "routes.txt"
        rf.write_text("\n".join(["# comment", "#/billing", "", "/#/reports"]) + "\n", encoding="utf-8")
        code, err = self.run_capture(["--routes-file", str(rf)])
        self.assertEqual(code, 0, err)
        self.assertEqual(self.fake.ctx.pages[0].visited[1:], [API + "/#/billing", API + "/#/reports"])

    def test_tokens_in_the_start_url_and_routes_are_redacted_in_every_output(self):
        script = {}
        code, err = self.run_capture(["--route", "#/billing?access_token=%s" % SECRET_COOKIE],
                                     script=script, url_suffix="?token=%s" % SECRET_COOKIE)
        self.assertEqual(code, 0, err)
        for name in ("endpoints.md", "routes.json", "api_map.json", "auth_hints.json"):
            self.assertNotIn(SECRET_COOKIE, (self.work / "out" / name).read_text(encoding="utf-8"), name)

    def test_a_token_in_a_discovered_link_or_the_start_url_reaches_no_file_name_no_file_and_no_log_line(self):
        """--discover writes the links it found into routes.json and logs every visit: a signed link (?token=, #access_token=,
        ?X-Amz-Signature=) must be masked there, in the error text of a failed visit, in screenshot/text file names and in the bundle list."""
        tok = "TOKLEAK77abc"
        hrefs = [API + "/magic/login?token=%s&x=1" % tok, API + "/#/reports?access_token=%s" % tok, API + "/p?ticket=%s1" % tok,
                 API + "/files/x?X-Amz-Signature=%s" % tok, API + "/#/boom?token=%s" % tok]

        class BoomPage(FakePage):
            def goto(self, url, wait_until=None, timeout=None):
                if "boom" in url:  # Playwright puts the address into the text of its timeout errors
                    raise RuntimeError('Page.goto: Timeout 45000ms exceeded.\nCall log:\n  - navigating to "%s", waiting until "domcontentloaded"' % url)
                super().goto(url, wait_until, timeout)

        js = "var a=1;" * 100 + 'fetch("https://app.example.test/api/v1/export?token=%s&x=1");' % tok
        script = {API + "/?token=%s#/billing?access_token=%s" % (tok, tok): [
            FakeResponse(API + "/static/app.js", request=FakeRequest(rtype="script")),
            json_resp(API + "/api/v1/dl/" + tok + "z" * 40, {"ok": True})]}  # a long opaque token in the PATH of a call, not in its query
        self.fake = FakePlaywright(lambda ctx: BoomPage(ctx, script=script, hrefs=hrefs, bodies={API + "/static/app.js": js}))
        h.load_engine = lambda name: (lambda: self.fake)

        def argv_for(folder):
            return ["capture", "--url", API + "/?token=%s#access_token=%s" % (tok, tok), "--out", str(self.work / folder),
                    "--profile", str(self.work / ".profile"), "--wait-ms", "1", "--login-wait", "6", "--discover", "--shots", "--save-text",
                    "--bundles", "--route", "#/billing?access_token=%s" % tok]

        code, _, err = run_main(argv_for("out"))
        self.assertEqual(code, 0, err)
        visited = self.fake.ctx.pages[0].visited
        self.assertTrue(any("magic/login?token=" + tok in v for v in visited), "the links were really visited: %s" % visited)
        self.assertIn("[crawl]", err)
        self.assertIn("ERR:", err, "the failed visit is reported")
        out = self.work / "out"
        routes = json.loads((out / "routes.json").read_text(encoding="utf-8"))
        self.assertEqual(len(routes["discovered"]), 5)
        self.assertIn(API + "/magic/login?token=<redacted>&x=1", routes["discovered"], "the link stays recognisable, only the secret goes")
        self.assertIn(API + "/#/reports?access_token=<redacted>", routes["discovered"])
        spots = {"stderr": err.lower()}
        for p in out.rglob("*"):
            rel = p.relative_to(out).as_posix()
            spots["name " + rel] = rel.lower()
            if p.is_file() and not rel.startswith("bundles/"):  # saved bundle code is kept as the server sent it: public source, not our capture
                spots[rel] = p.read_text(encoding="utf-8", errors="replace").lower()
        for where, text in spots.items():
            self.assertNotIn(tok.lower()[:7], text, "the token leaked into " + where)
        listed = [p["path"] for paths in json.loads((out / "bundle_endpoints.json").read_text(encoding="utf-8"))["files"].values() for p in paths]
        self.assertIn("https://app.example.test/api/v1/export?token=<redacted>&x=1", listed)
        # --keep-secrets is still the one switch that writes the real addresses
        code, _, err = run_main(argv_for("out-keep") + ["--keep-secrets"])
        self.assertEqual(code, 0, err)
        self.assertIn(tok, (self.work / "out-keep" / "routes.json").read_text(encoding="utf-8"))
        self.assertIn("[crawl] " + API + "/magic/login?token=" + tok, err)

    def test_missing_engine_is_a_clear_exit_1(self):
        def boom(name):
            raise ImportError("No module named playwright")

        h.load_engine = boom
        code, out, err = run_main(["capture", "--url", API + "/", "--out", str(self.work / "o"), "--profile", str(self.work / "p")])
        self.assertEqual(code, 1)
        self.assertIn("NEXT: pip install", err)

    def test_host_defaults_to_start_url_and_can_be_widened(self):
        script = default_script()
        script[API + "/"].append(json_resp("https://api.example.test/v1/other", {"a": 1}))
        code, err = self.run_capture(script=script)
        self.assertEqual(code, 0, err)
        urls = [e["url"] for e in json.loads((self.work / "out" / "api_map.json").read_text(encoding="utf-8"))]
        self.assertFalse(any("api.example.test" in u for u in urls), "app.example.test only: api.example.test is another host")
        code, err = self.run_capture(["--host", "example.test"], script=script)
        urls = [e["url"] for e in json.loads((self.work / "out" / "api_map.json").read_text(encoding="utf-8"))]
        self.assertTrue(any("api.example.test" in u for u in urls))


# --------------------------------------------------------------------------------------- command line
class CliTests(unittest.TestCase):
    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)

    def test_compiles(self):
        py_compile.compile(str(SCRIPT), doraise=True)

    def test_help_and_usage_errors(self):
        r = self.run_cli("--help")
        self.assertEqual(r.returncode, 0)
        for word in ("capture", "summarize", "bundles", "exit codes"):
            self.assertIn(word, r.stdout)
        self.assertEqual(self.run_cli().returncode, 2)
        self.assertEqual(self.run_cli("capture").returncode, 2, "--url is required")
        self.assertEqual(self.run_cli("capture", "--help").returncode, 0)

    def test_summarize_roundtrip_and_missing_file(self):
        with tempfile.TemporaryDirectory() as td:
            src = Path(td) / "api_map.json"
            src.write_text(json.dumps(fixture_entries()), encoding="utf-8")
            r = self.run_cli("summarize", str(src))
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("## Endpoints", r.stdout)
            self.assertIn("/api/v1/items/{n}", r.stdout)
            assert_clean(self, r.stdout, extra=(PII_EMAIL,))
            dest = Path(td) / "endpoints.md"
            r = self.run_cli("summarize", str(src), "--out", str(dest))
            self.assertEqual(r.returncode, 0)
            self.assertEqual(r.stdout, "", "table goes to the file, stdout stays empty")
            self.assertIn("## Endpoints", dest.read_text(encoding="utf-8"))
            r = self.run_cli("summarize", str(src), "--json")
            self.assertEqual(json.loads(r.stdout)["calls"], 10)
            r = self.run_cli("summarize", str(Path(td) / "nope.json"))
            self.assertEqual(r.returncode, 1)
            self.assertIn("NEXT:", r.stderr)
            bad = Path(td) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            self.assertEqual(self.run_cli("summarize", str(bad)).returncode, 1)

    def test_bundles_folder_with_stub_and_real(self):
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "app.js").write_text(JS_SAMPLE, encoding="utf-8")
            (Path(td) / "stub.js").write_text("x" * 106, encoding="utf-8")
            r = self.run_cli("bundles", td, "--grep", "refund")
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertIn("2 files, 1 stubs", r.stdout)
            self.assertIn("STUB (106 bytes)", r.stdout)
            self.assertIn("/api/v1/orders/refund", r.stdout)
            self.assertIn("call context for 'refund'", r.stdout)
            assert_clean(self, r.stdout)
            r = self.run_cli("bundles", td, "--json", "--strong-only")
            data = json.loads(r.stdout)
            real = [d for d in data if not d.get("stub")][0]
            self.assertTrue(all(p["strong"] for p in real["paths"]))
            r = self.run_cli("bundles", str(Path(td) / "does-not-exist"))
            self.assertEqual(r.returncode, 1)
            self.assertIn("NEXT:", r.stderr)
            self.assertNotIn("Traceback", r.stderr)

    def test_bundles_without_js_is_exit_1(self):
        with tempfile.TemporaryDirectory() as td:
            r = self.run_cli("bundles", td)
            self.assertEqual(r.returncode, 1)
            self.assertIn("NEXT:", r.stderr)


class RealDataTests(unittest.TestCase):
    """Opt-in: your own saved captures (current or older probe shapes, real data). Nothing is printed.

    HARVEST_REAL_DIR is a folder with call lists saved as JSON (for example <service>-re/out); files that
    are not lists of calls (auth_hints.json, routes.json) are skipped.
    """

    @unittest.skipUnless(os.environ.get("HARVEST_REAL") == "1" and os.environ.get("HARVEST_REAL_DIR"),
                         "set HARVEST_REAL=1 and HARVEST_REAL_DIR=<folder with saved captures> to parse your own captures")
    def test_real_captures_parse(self):
        real = Path(os.environ["HARVEST_REAL_DIR"]).expanduser()
        parsed = 0
        for path in sorted(real.glob("*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            if not (isinstance(data, list) and any(isinstance(x, dict) and isinstance(x.get("url"), str) for x in data)):
                continue
            s = h.summarize(data)
            self.assertGreater(len(s["endpoints"]), 0, path.name)
            json.dumps(h.jsonable_summary(s))
            h.render_markdown(s)
            parsed += 1
        self.assertGreater(parsed, 0, "no saved call list (a JSON list of {url, ...}) in HARVEST_REAL_DIR")


if __name__ == "__main__":
    unittest.main()
