"""
OSINT recon CLI for Claude Code.
Request-driven reconnaissance over PUBLIC sources only: IP geo/ASN, DNS, RDAP whois,
BGP prefixes, Certificate Transparency, open ports (Shodan InternetDB), HTTP security
headers, sanctions/PEP screening, CVE lookup, subdomain enumeration, full recon summary.

Philosophy: no daemons, no pollers, no docker. You ask -> it fetches -> it prints.
Anything requiring continuous polling (live flight/vessel/satellite maps) is deliberately
OUT OF SCOPE.

Credentials (all OPTIONAL): ~/.claude/.credentials.master.env
    SHODAN_API_KEY         - richer `ports` output (banners, org, last-seen)
    OPENSANCTIONS_API_KEY  - `sanctions` via OpenSanctions API (else OFAC SDN fallback)

Sources: ip-api.com, ipinfo.io, dns.google, cloudflare-dns.com, rdap.org, rdap.arin.net,
         stat.ripe.net, crt.sh, api.certspotter.com, internetdb.shodan.io,
         api.opensanctions.org, sanctionslistservice.ofac.treas.gov, services.nvd.nist.gov

Usage: python osint_client.py <command> [args] [--json]
"""

import argparse
import concurrent.futures
import csv
import io
import ipaddress
import json
import os
import re
import socket
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")


def load_env():
    env_path = Path.home() / ".claude" / ".credentials.master.env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip('"').strip("'")
                if key and not os.environ.get(key):
                    os.environ[key] = value


load_env()

# Optional fast paths (stdlib-first, these are pure accelerators)
try:
    import requests  # noqa
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import dns.resolver  # noqa
    import dns.exception  # noqa
    HAS_DNSPYTHON = True
except ImportError:
    HAS_DNSPYTHON = False


UA = "osint-client/1.0 (OSINT recon CLI; public-sources only)"
DEFAULT_TIMEOUT = 15
CACHE_DIR = Path.home() / ".claude" / "cache" / "osint"

DNS_TYPES = ["A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA"]


# ========== SECRET REDACTION ==========

_SECRET_PARAM_RE = re.compile(
    r"((?:api[-_]?key|apikey|key|access[-_]?token|token|secret|password|passwd|auth)"
    r"\s*[=:]\s*)([^&\s'\"<>]{4,})", re.I)
_SECRET_VALUES = None


def _secret_values():
    """Values of credential-looking env vars, so they can never reach the terminal."""
    global _SECRET_VALUES
    if _SECRET_VALUES is None:
        _SECRET_VALUES = []
        for name, value in os.environ.items():
            if not value or len(value) < 8:
                continue
            if re.search(r"(KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDENTIAL|SESSION)", name, re.I):
                _SECRET_VALUES.append((name, value))
        _SECRET_VALUES.sort(key=lambda kv: -len(kv[1]))
    return _SECRET_VALUES


def redact(text):
    """Strip API keys out of anything we are about to print (URLs land in exceptions)."""
    text = str(text)
    for name, value in _secret_values():
        if value in text:
            text = text.replace(value, f"<{name}:redacted>")
    return _SECRET_PARAM_RE.sub(lambda m: m.group(1) + "<redacted>", text)


# ========== ERRORS ==========

class OsintError(Exception):
    """Human-readable failure - printed without a traceback."""

    def __str__(self):
        return redact(super().__str__())


class BlockedTarget(OsintError):
    """SSRF guard refused the target."""


class RateLimited(OsintError):
    """Source returned HTTP 429."""


# ========== SSRF GUARD ==========

def _ip_verdict(ip_str):
    """Return None if the IP may be contacted, else a human reason to refuse."""
    try:
        ip = ipaddress.ip_address(ip_str)
    except ValueError:
        return f"'{ip_str}' is not a valid IP address"
    if ip_str in ("169.254.169.254", "fd00:ec2::254", "YOUR_PUBLIC_IP"):
        return f"{ip} is a cloud metadata endpoint"
    if ip.is_unspecified:
        return f"{ip} is the unspecified address"
    if ip.is_loopback:
        return f"{ip} is loopback"
    if ip.is_link_local:
        return f"{ip} is link-local (includes cloud metadata 169.254.169.254)"
    if ip.is_private:
        return f"{ip} is a private/internal address"
    if ip.is_multicast:
        return f"{ip} is multicast"
    if ip.is_unspecified:
        return f"{ip} is unspecified"
    if ip.is_reserved:
        return f"{ip} is reserved"
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped:
        inner = _ip_verdict(str(ip.ipv4_mapped))
        if inner:
            return f"{ip} maps to non-public {inner}"
    return None


def guard_ip(ip_str):
    """Raise BlockedTarget for private/loopback/metadata/reserved addresses."""
    reason = _ip_verdict(ip_str)
    if reason:
        raise BlockedTarget(
            f"SSRF guard: refusing to query {ip_str} - {reason}. "
            "This tool only touches public internet targets."
        )
    return ip_str


DOTTED_QUAD_RE = re.compile(r"^\d{1,4}(\.\d{1,4}){3}$")


def require_target(value, what="target"):
    """Reject blank arguments before they reach a resolver ('' resolves to the local host)."""
    value = (value or "").strip()
    if not value:
        raise OsintError(f"Empty {what} - give something to look up "
                         f"(e.g. example.com or YOUR_PUBLIC_IP)")
    return value


def to_ascii_host(host):
    """Punycode an IDN so URLs, RDAP paths and CT name matching all speak the same alphabet."""
    try:
        host.encode("ascii")
        return host
    except UnicodeEncodeError:
        pass
    try:
        return host.encode("idna").decode("ascii")
    except Exception:
        try:  # per-label fallback (encode('idna') rejects some mixed strings)
            return ".".join(
                lbl if lbl.isascii() else lbl.encode("idna").decode("ascii")
                for lbl in host.split(".") if lbl != "")
        except Exception:
            raise OsintError(f"'{host}' is not a valid international domain name")


def resolve_host(host, want_all=True):
    """Resolve a hostname to IPs via the OS resolver. Returns list of IP strings."""
    host = require_target(host, "hostname")
    if DOTTED_QUAD_RE.match(host):
        raise OsintError(f"'{host}' looks like an IPv4 address but is not a valid one "
                         "(each octet must be 0-255)")
    host = to_ascii_host(host)
    try:
        infos = socket.getaddrinfo(host, None, proto=socket.IPPROTO_TCP)
    except socket.gaierror as e:
        raise OsintError(f"DNS resolution failed for '{host}': {e.strerror or e}")
    ips = []
    for info in infos:
        ip = info[4][0]
        if ip not in ips:
            ips.append(ip)
    return ips if want_all else ips[:1]


def guard_hostname(host):
    """Resolve a hostname and refuse if ANY resolved address is non-public."""
    host = require_target(host, "hostname")
    try:
        ipaddress.ip_address(host)
        return [guard_ip(host)]
    except ValueError:
        pass
    if host.lower() in ("localhost", "localhost.localdomain") or host.lower().endswith(".localhost"):
        raise BlockedTarget(f"SSRF guard: refusing to query '{host}' - localhost alias")
    ips = resolve_host(host)
    for ip in ips:
        reason = _ip_verdict(ip)
        if reason:
            raise BlockedTarget(
                f"SSRF guard: refusing to query '{host}' - it resolves to {ip} ({reason})."
            )
    return ips


def guard_url(url):
    """Validate scheme + host of a URL before fetching it. Returns (url, parsed, ips)."""
    url = require_target(url, "URL")
    if "://" not in url:
        url = "https://" + url
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise BlockedTarget(f"SSRF guard: refusing scheme '{parsed.scheme}' (only http/https)")
    if not parsed.hostname:
        raise OsintError(f"Cannot parse a hostname out of '{url}'")
    ascii_host = to_ascii_host(parsed.hostname)
    if ascii_host != parsed.hostname:  # IDN -> punycode, or http clients choke on the Location
        netloc = ascii_host + (f":{parsed.port}" if parsed.port else "")
        if parsed.username:
            netloc = parsed.username + (f":{parsed.password}" if parsed.password else "") + "@" + netloc
        parsed = parsed._replace(netloc=netloc)
        url = parsed.geturl()
    ips = guard_hostname(ascii_host)
    return url, parsed, ips


# ========== HTTP ==========

REDIRECT_STATUSES = (301, 302, 303, 307, 308)
MAX_REDIRECTS = 5


def _one_hop(url, timeout, hdrs, method, retry_5xx, src):
    """One HTTP call, no redirect following, retried once on 5xx/network error."""
    last_exc = None
    for attempt in (1, 2):
        try:
            if HAS_REQUESTS:
                resp = requests.request(method, url, headers=hdrs, timeout=timeout,
                                        allow_redirects=False)
                status, rheaders, body = resp.status_code, dict(resp.headers), resp.content
            else:
                status, rheaders, body, _ = _urllib_request(url, timeout, hdrs, method, False)
        except Exception as e:  # network-level failure
            last_exc = e
            if attempt == 1:
                time.sleep(1.5)
                continue
            raise OsintError(f"{src}: request failed ({type(e).__name__}: {e})")

        if status == 429:
            retry_after = rheaders.get("Retry-After") or rheaders.get("retry-after")
            hint = f" Retry-After: {retry_after}s." if retry_after else ""
            raise RateLimited(
                f"{src}: rate limit hit (HTTP 429).{hint} "
                "Wait a bit and retry, or add the optional API key for this source."
            )
        if status >= 500 and retry_5xx and attempt == 1:
            time.sleep(1.5)
            continue
        return status, rheaders, body

    raise OsintError(f"{src}: request failed ({last_exc})")


def http_request(url, timeout=DEFAULT_TIMEOUT, headers=None, method="GET",
                 allow_redirects=True, retry_5xx=True, source=None):
    """
    HTTP call with SSRF-guarded redirect following.
    Returns (status, headers_dict, body_bytes, final_url).

    Redirects are followed MANUALLY so every hop passes guard_url() first - letting
    requests/urllib follow them internally would let a public host bounce us into
    127.0.0.1 or a cloud metadata endpoint before any guard runs.
    Retries once on 5xx / timeout / connection reset. Raises RateLimited on 429.
    """
    src = source or urllib.parse.urlparse(url).hostname or url
    hdrs = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        hdrs.update(headers)

    current = url
    for hop in range(MAX_REDIRECTS + 1):
        status, rheaders, body = _one_hop(current, timeout, hdrs, method, retry_5xx, src)
        location = rheaders.get("Location") or rheaders.get("location")
        if not (allow_redirects and status in REDIRECT_STATUSES and location):
            return status, rheaders, body, current
        nxt = urllib.parse.urljoin(current, location.strip())
        if not urllib.parse.urlparse(nxt).scheme:
            raise OsintError(f"{src}: cannot follow redirect to '{truncate(location, 120)}'")
        nxt, _parsed, _ips = guard_url(nxt)  # raises BlockedTarget on private/metadata hops
        current = nxt
    raise OsintError(f"{src}: more than {MAX_REDIRECTS} redirects - giving up")


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **kw):
        return None


def _urllib_request(url, timeout, hdrs, method, allow_redirects):
    req = urllib.request.Request(url, headers=hdrs, method=method)
    opener = urllib.request.build_opener() if allow_redirects else \
        urllib.request.build_opener(_NoRedirect)
    try:
        with opener.open(req, timeout=timeout) as resp:
            return resp.status, dict(resp.headers), resp.read(), resp.url
    except urllib.error.HTTPError as e:
        body = b""
        try:
            body = e.read()
        except Exception:
            pass
        return e.code, dict(e.headers or {}), body, url


def fetch_json(url, timeout=DEFAULT_TIMEOUT, headers=None, source=None, ok_statuses=(200,)):
    """GET + parse JSON. Raises OsintError with a readable message on failure."""
    hdrs = {"Accept": "application/json"}
    if headers:
        hdrs.update(headers)
    src = source or urllib.parse.urlparse(url).hostname or url
    status, rheaders, body, _ = http_request(url, timeout=timeout, headers=hdrs, source=src)
    if status not in ok_statuses:
        snippet = body[:180].decode("utf-8", "replace").strip().replace("\n", " ")
        raise OsintError(f"{src}: HTTP {status}{(' - ' + snippet) if snippet else ''}")
    if not body.strip():
        raise OsintError(f"{src}: empty response")
    try:
        return json.loads(body.decode("utf-8", "replace"))
    except json.JSONDecodeError:
        snippet = body[:180].decode("utf-8", "replace").strip().replace("\n", " ")
        raise OsintError(f"{src}: response is not JSON - {snippet}")


# ========== OUTPUT HELPERS ==========

OK, WARN, BAD, INFO, HIT = "[ OK ]", "[WARN]", "[FAIL]", "[ -- ]", "[ HIT]"

# The TLD alternative must accept punycode ("xn--p1ai" for .рф, "xn--fiqs8s" for .中国):
# a plain [a-z]{2,63} silently dropped EVERY name under an internationalised TLD, so
# `certs`/`subdomains` reported a confident "0 names" for .рф domains that do have certs.
HOSTNAME_RE = re.compile(
    r"^(?=.{1,253}$)([a-z0-9_](?:[a-z0-9_-]{0,61}[a-z0-9_])?\.)+"
    r"(?:xn--[a-z0-9-]{2,59}|[a-z]{2,63})$")


def valid_hostname(name):
    """CT logs carry emails and free-text CNs alongside real DNS names - filter those out."""
    return bool(name) and "@" not in name and " " not in name and bool(HOSTNAME_RE.match(name))


def under_domain(name, domain):
    """True only for the apex itself or a real subdomain.

    A bare endswith() also accepts 'notexample.com' for 'example.com', which would
    attribute somebody else's host to the target's attack surface.
    """
    return name == domain or name.endswith("." + domain)


def emit(data, as_json, printer):
    """Print JSON or a human view."""
    if as_json:
        print(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        printer(data)


def hr(title=None):
    if title:
        print(f"\n=== {title} ===")
    else:
        print("-" * 62)


def kv(key, value, width=18):
    if value in (None, "", [], {}):
        return
    if isinstance(value, list):
        value = ", ".join(str(v) for v in value)
    print(f"  {key:<{width}} {value}")


def truncate(text, limit=300):
    text = " ".join(str(text or "").split())
    return text if len(text) <= limit else text[: limit - 1] + "…"


def normalize_domain(raw):
    original = (raw or "").strip()
    raw = original.lower()
    if "://" in raw:
        raw = urllib.parse.urlparse(raw).hostname or raw
    raw = raw.strip("/").split("/")[0].split("@")[-1].split(":")[0]
    if raw.endswith("."):
        raw = raw[:-1]
    if not raw or " " in raw or "." not in raw:
        raise OsintError(f"'{original}' does not look like a domain name")
    ascii_domain = to_ascii_host(raw)
    if ascii_domain != raw:
        # CT logs, RDAP and HTTP all store/expect punycode - matching on the unicode
        # form silently returns zero results.
        print(f"(IDN {raw} -> {ascii_domain})", file=sys.stderr)
    return ascii_domain


def is_ip(value):
    try:
        ipaddress.ip_address(value)
        return True
    except ValueError:
        return False


def clamp_positive(value, flag):
    """A limit of 0 or -5 used to yield a confident, silent 'nothing found'."""
    if value is None:
        return value
    if value < 1:
        raise OsintError(f"{flag} must be 1 or greater (got {value})")
    return value


# ========== ip ==========

def source_ip_api(ip, timeout=DEFAULT_TIMEOUT):
    fields = ("status,message,continent,country,countryCode,region,regionName,city,zip,"
              "lat,lon,timezone,isp,org,as,asname,reverse,mobile,proxy,hosting,query")
    data = fetch_json(f"http://ip-api.com/json/{urllib.parse.quote(ip)}?fields={fields}",
                      timeout=timeout, source="ip-api.com")
    if data.get("status") != "success":
        raise OsintError(f"ip-api.com: {data.get('message', 'lookup failed')}")
    asn, _, as_name = (data.get("as") or "").partition(" ")
    return {
        "ip": data.get("query"), "source": "ip-api.com",
        "country": data.get("country"), "country_code": data.get("countryCode"),
        "region": data.get("regionName"), "city": data.get("city"),
        "zip": data.get("zip") or None, "continent": data.get("continent"),
        "lat": data.get("lat"), "lon": data.get("lon"), "timezone": data.get("timezone"),
        "asn": asn or None, "as_name": as_name or data.get("asname"),
        "isp": data.get("isp"), "org": data.get("org") or None,
        "reverse_dns": data.get("reverse") or None,
        "flags": {"mobile": data.get("mobile"), "proxy_vpn_tor": data.get("proxy"),
                  "hosting_datacenter": data.get("hosting")},
    }


def source_ipinfo(ip, timeout=DEFAULT_TIMEOUT):
    data = fetch_json(f"https://ipinfo.io/{urllib.parse.quote(ip)}/json",
                      timeout=timeout, source="ipinfo.io")
    loc = (data.get("loc") or ",").split(",")
    org = data.get("org") or ""
    asn, _, as_name = org.partition(" ")
    return {
        "ip": data.get("ip"), "source": "ipinfo.io",
        "country": data.get("country"), "country_code": data.get("country"),
        "region": data.get("region"), "city": data.get("city"),
        "zip": data.get("postal"), "continent": None,
        "lat": loc[0] or None, "lon": loc[1] if len(loc) > 1 else None,
        "timezone": data.get("timezone"),
        "asn": asn if asn.startswith("AS") else None,
        "as_name": as_name or None, "isp": org or None, "org": org or None,
        "reverse_dns": data.get("hostname"), "flags": {},
    }


def cmd_ip(args):
    target = require_target(args.address, "IP/hostname")
    if not is_ip(target):
        ips = guard_hostname(target)
        resolved_from = target
        target = ips[0]
        print(f"(resolved {resolved_from} -> {target})", file=sys.stderr)
    guard_ip(target)

    try:
        data = source_ip_api(target, args.timeout)
    except (OsintError, RateLimited) as e:
        print(f"(ip-api.com unavailable: {e}; trying ipinfo.io)", file=sys.stderr)
        data = source_ipinfo(target, args.timeout)

    def show(d):
        hr(f"IP {d['ip']}  ({d['source']})")
        kv("Country", f"{d.get('country')} ({d.get('country_code')})" if d.get("country") else None)
        kv("Region / City", " / ".join(x for x in [d.get("region"), d.get("city")] if x))
        kv("Postal", d.get("zip"))
        kv("Coordinates", f"{d.get('lat')}, {d.get('lon')}" if d.get("lat") else None)
        kv("Timezone", d.get("timezone"))
        kv("ASN", f"{d.get('asn')} {d.get('as_name') or ''}".strip())
        kv("ISP", d.get("isp"))
        kv("Org", d.get("org"))
        kv("Reverse DNS", d.get("reverse_dns"))
        flags = [k for k, v in (d.get("flags") or {}).items() if v]
        if flags:
            kv("Flags", flags)

    emit(data, args.json, show)


# ========== dns ==========

def dns_via_dnspython(domain, rtypes, timeout=DEFAULT_TIMEOUT):
    resolver = dns.resolver.Resolver()
    resolver.lifetime = timeout
    resolver.timeout = timeout
    out = {}
    for rt in rtypes:
        try:
            answers = resolver.resolve(domain, rt)
            out[rt] = sorted(r.to_text().strip('"') if rt == "TXT" else r.to_text()
                             for r in answers)
        except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
            out[rt] = []
        except dns.exception.DNSException:
            out[rt] = []
    return out, "dnspython (system resolver)"


DOH_ENDPOINTS = [
    ("https://dns.google/resolve", {"Accept": "application/json"}, "dns.google"),
    ("https://cloudflare-dns.com/dns-query", {"Accept": "application/dns-json"}, "cloudflare-dns.com"),
]


def dns_via_doh(domain, rtypes, timeout=DEFAULT_TIMEOUT):
    last_err = None
    for base, headers, name in DOH_ENDPOINTS:
        out = {}
        try:
            for rt in rtypes:
                url = f"{base}?name={urllib.parse.quote(domain)}&type={rt}"
                data = fetch_json(url, headers=headers, timeout=timeout, source=name)
                records = []
                for ans in data.get("Answer", []) or []:
                    val = ans.get("data", "")
                    if rt == "TXT":
                        val = val.strip('"')
                    records.append(val)
                out[rt] = sorted(set(records))
            return out, f"DNS-over-HTTPS ({name})"
        except (OsintError, RateLimited) as e:
            last_err = e
            continue
    raise OsintError(f"All DoH resolvers failed: {last_err}")


def collect_dns(domain, rtypes=None, prefer_doh=False, timeout=DEFAULT_TIMEOUT):
    rtypes = rtypes or DNS_TYPES
    if HAS_DNSPYTHON and not prefer_doh:
        try:
            records, via = dns_via_dnspython(domain, rtypes, timeout)
            if any(records.values()):
                return records, via
        except Exception:
            pass
    return dns_via_doh(domain, rtypes, timeout)


# Types both dnspython and DoH understand; anything else silently returned "no records".
KNOWN_DNS_TYPES = {"A", "AAAA", "MX", "NS", "TXT", "CNAME", "SOA", "PTR", "SRV", "CAA",
                   "DS", "DNSKEY", "NAPTR", "TLSA", "SPF", "HINFO", "SVCB", "HTTPS", "ANY"}


def cmd_dns(args):
    domain = normalize_domain(args.domain)
    rtypes = [t.strip().upper() for t in args.types.split(",") if t.strip()] if args.types \
        else DNS_TYPES
    if not rtypes:
        raise OsintError("--types is empty - give at least one record type, e.g. --types A,MX")
    unknown = [t for t in rtypes if t not in KNOWN_DNS_TYPES]
    if unknown:
        raise OsintError(f"unknown DNS record type(s): {', '.join(unknown)}. "
                         f"Supported: {', '.join(sorted(KNOWN_DNS_TYPES))}")
    records, via = collect_dns(domain, rtypes, prefer_doh=args.doh, timeout=args.timeout)
    data = {"domain": domain, "resolver": via, "records": records,
            "total": sum(len(v) for v in records.values())}

    def show(d):
        hr(f"DNS {d['domain']}")
        print(f"  via {d['resolver']}")
        for rt in rtypes:
            values = d["records"].get(rt) or []
            if not values:
                print(f"  {rt:<6} -")
                continue
            print(f"  {rt:<6} {values[0]}")
            for v in values[1:]:
                print(f"  {'':<6} {v}")
        if not d["total"]:
            print("\n  No records found (domain may not exist or has no public DNS).")

    emit(data, args.json, show)


# ========== whois (RDAP) ==========

def rdap_entities(entities, depth=0):
    """Flatten RDAP entity vCards into readable roles."""
    out = []
    for ent in entities or []:
        roles = ent.get("roles") or []
        name = handle = email = None
        vcard = ent.get("vcardArray")
        if isinstance(vcard, list) and len(vcard) > 1:
            for item in vcard[1]:
                if not isinstance(item, list) or len(item) < 4:
                    continue
                if item[0] == "fn":
                    name = item[3]
                elif item[0] == "email" and not email:
                    email = item[3]
        handle = ent.get("handle")
        out.append({"roles": roles, "name": name, "handle": handle, "email": email})
        if depth < 1:
            out.extend(rdap_entities(ent.get("entities"), depth + 1))
    return out


def rdap_events(events):
    out = {}
    for ev in events or []:
        action = ev.get("eventAction")
        date = ev.get("eventDate")
        if action and date and action not in out:
            out[action] = date
    return out


def cmd_whois(args):
    target = require_target(args.target, "domain/IP")
    if is_ip(target):
        guard_ip(target)
        kind = "ip"
        urls = [f"https://rdap.org/ip/{target}", f"https://rdap.arin.net/registry/ip/{target}"]
    else:
        target = normalize_domain(target)
        kind = "domain"
        urls = [f"https://rdap.org/domain/{target}"]

    raw = last_err = None
    for url in urls:
        try:
            raw = fetch_json(url, source=urllib.parse.urlparse(url).hostname, timeout=args.timeout)
            break
        except (OsintError, RateLimited) as e:
            last_err = e
    if raw is None:
        note = ("  A 404 here means one of two things: the name is not registered, OR the zone "
                "has no\n  public RDAP server (.ru, .su, .xn--p1ai/.рф and a number of other "
                "ccTLDs do not) -\n  RDAP cannot tell those apart. Cross-check with `dns "
                f"{target}`: records => registered."
                if "404" in str(last_err) else
                "  Note: some ccTLDs (.ru, .su, .xn--p1ai/.рф and others) have no public "
                "RDAP server.")
        raise OsintError(f"RDAP lookup failed for {target}: {last_err}\n{note}")

    events = rdap_events(raw.get("events"))
    entities = rdap_entities(raw.get("entities"))
    registrar = next((e["name"] for e in entities if "registrar" in (e.get("roles") or [])), None)
    abuse = next((e["email"] for e in entities
                  if "abuse" in (e.get("roles") or []) and e.get("email")), None)
    nameservers = [ns.get("ldhName") for ns in raw.get("nameservers") or [] if ns.get("ldhName")]

    data = {
        "target": target, "kind": kind,
        "name": raw.get("ldhName") or raw.get("name"),
        "handle": raw.get("handle"),
        "status": raw.get("status") or [],
        "events": events,
        "registered": events.get("registration"),
        "expires": events.get("expiration"),
        "last_changed": events.get("last changed") or events.get("last update of RDAP database"),
        "registrar": registrar,
        "abuse_email": abuse,
        "nameservers": nameservers,
        "entities": entities,
        "cidr": raw.get("handle") if kind == "ip" else None,
        "start_address": raw.get("startAddress"), "end_address": raw.get("endAddress"),
        "ip_type": raw.get("type"), "country": raw.get("country"),
        "port43": raw.get("port43"),
    }

    def show(d):
        hr(f"RDAP {d['target']} ({d['kind']})")
        kv("Name", d.get("name"))
        kv("Handle", d.get("handle"))
        if d["kind"] == "ip":
            kv("Range", f"{d.get('start_address')} - {d.get('end_address')}"
               if d.get("start_address") else None)
            kv("Type", d.get("ip_type"))
            kv("Country", d.get("country"))
        kv("Registrar", d.get("registrar"))
        kv("Registered", d.get("registered"))
        kv("Expires", d.get("expires"))
        kv("Last changed", d.get("last_changed"))
        kv("Status", d.get("status"))
        kv("Nameservers", d.get("nameservers"))
        kv("Abuse contact", d.get("abuse_email"))
        kv("Legacy whois", d.get("port43"))
        others = [e for e in d["entities"] if e.get("name") and "registrar" not in (e.get("roles") or [])]
        if others:
            print("  Entities:")
            for e in others[:8]:
                print(f"    - {', '.join(e['roles']) or 'unknown'}: {e['name'] or e['handle']}"
                      + (f" <{e['email']}>" if e.get("email") else ""))

    emit(data, args.json, show)


# ========== asn ==========

def ripe(call, resource, timeout=DEFAULT_TIMEOUT):
    url = (f"https://stat.ripe.net/data/{call}/data.json"
           f"?resource={urllib.parse.quote(str(resource))}&sourceapp=osint-client")
    payload = fetch_json(url, timeout=timeout, source="stat.ripe.net")
    return payload.get("data") or {}


def asn_from_ip(ip):
    data = ripe("network-info", ip)
    asns = data.get("asns") or []
    prefix = data.get("prefix")
    if not asns:
        raise OsintError(f"No ASN announcement found for {ip} (RIPEstat)")
    return asns[0], prefix


def cmd_asn(args):
    require_target(args.target, "AS number/IP")
    target = str(args.target).strip().upper().replace("AS", "") if not is_ip(args.target) \
        else args.target.strip()
    origin_prefix = None
    if is_ip(target):
        guard_ip(target)
        asn, origin_prefix = asn_from_ip(target)
    else:
        if not target.isdigit():
            raise OsintError(f"'{args.target}' is neither an AS number (e.g. AS15169) nor an IP")
        asn = target

    overview = ripe("as-overview", f"AS{asn}", timeout=args.timeout)
    try:
        prefixes = [p.get("prefix") for p in (ripe("announced-prefixes", f"AS{asn}",
                    timeout=args.timeout).get("prefixes") or []) if p.get("prefix")]
    except (OsintError, RateLimited) as e:
        prefixes = []
        print(f"(prefixes unavailable: {e})", file=sys.stderr)

    neighbours = {"left_upstream": [], "right_downstream": [], "uncertain": []}
    try:
        nb = ripe("asn-neighbours", f"AS{asn}", timeout=args.timeout)
        for n in nb.get("neighbours") or []:
            entry = {"asn": n.get("asn"), "type": n.get("type"), "power": n.get("power")}
            if n.get("type") == "left":
                neighbours["left_upstream"].append(entry)
            elif n.get("type") == "right":
                neighbours["right_downstream"].append(entry)
            else:
                neighbours["uncertain"].append(entry)
    except (OsintError, RateLimited) as e:
        print(f"(neighbours unavailable: {e})", file=sys.stderr)

    data = {
        "asn": f"AS{asn}",
        "holder": overview.get("holder"),
        "announced": overview.get("announced"),
        "type": overview.get("type"),
        "resource": overview.get("resource"),
        "block": (overview.get("block") or {}).get("desc"),
        "origin_prefix_for_ip": origin_prefix,
        "prefix_count": len(prefixes),
        "prefixes": prefixes if args.all_prefixes else prefixes[:25],
        "prefixes_truncated": (not args.all_prefixes) and len(prefixes) > 25,
        "upstreams": neighbours["left_upstream"],
        "downstreams": neighbours["right_downstream"],
        "source": "stat.ripe.net (RIPE RIS)",
    }

    def show(d):
        hr(f"{d['asn']}  {d.get('holder') or ''}")
        kv("Announced", d.get("announced"))
        kv("Block", d.get("block"))
        if d.get("origin_prefix_for_ip"):
            kv("Origin prefix", d["origin_prefix_for_ip"])
        kv("Prefixes", d["prefix_count"])
        for p in d["prefixes"]:
            print(f"    {p}")
        if d["prefixes_truncated"]:
            print(f"    ... +{d['prefix_count'] - len(d['prefixes'])} more (use --all-prefixes)")
        kv("Upstreams", f"{len(d['upstreams'])} ASNs")
        for n in d["upstreams"][:12]:
            print(f"    AS{n['asn']} (seen by {n.get('power')} peers)")
        kv("Downstreams", f"{len(d['downstreams'])} ASNs")
        for n in d["downstreams"][:12]:
            print(f"    AS{n['asn']} (seen by {n.get('power')} peers)")
        print(f"\n  source: {d['source']}")

    emit(data, args.json, show)


# ========== certs / subdomains ==========

def ct_crtsh(domain, timeout=40):
    """Certificate Transparency via crt.sh. Flaky under load -> two param forms."""
    q = urllib.parse.quote(f"%.{domain}")
    urls = [f"https://crt.sh/?Identity={q}&output=json", f"https://crt.sh/?q={q}&output=json"]
    last = None
    for url in urls:
        try:
            rows = fetch_json(url, timeout=timeout, source="crt.sh")
            names, issuers = set(), {}
            for row in rows:
                for name in (row.get("name_value") or "").splitlines():
                    name = name.strip().lower().lstrip("*.")
                    if under_domain(name, domain) and valid_hostname(name):
                        names.add(name)
                iss = row.get("issuer_name") or ""
                if iss:
                    issuers[iss] = issuers.get(iss, 0) + 1
            return sorted(names), issuers, "crt.sh", len(rows)
        except (OsintError, RateLimited) as e:
            last = e
    raise OsintError(f"crt.sh unavailable: {last}")


def ct_certspotter(domain, timeout=30):
    url = ("https://api.certspotter.com/v1/issuances"
           f"?domain={urllib.parse.quote(domain)}&include_subdomains=true"
           "&expand=dns_names&expand=issuer")
    rows = fetch_json(url, timeout=timeout, source="api.certspotter.com")
    names, issuers = set(), {}
    for row in rows:
        for name in row.get("dns_names") or []:
            name = name.strip().lower().lstrip("*.")
            if under_domain(name, domain) and valid_hostname(name):
                names.add(name)
        iss = (row.get("issuer") or {}).get("name") or ""
        if iss:
            issuers[iss] = issuers.get(iss, 0) + 1
    return sorted(names), issuers, "api.certspotter.com", len(rows)


def collect_ct(domain, timeout=40):
    try:
        return ct_crtsh(domain, timeout)
    except (OsintError, RateLimited) as e:
        print(f"(crt.sh failed: {e}; falling back to CertSpotter)", file=sys.stderr)
        return ct_certspotter(domain, min(timeout, 30))


def cmd_certs(args):
    domain = normalize_domain(args.domain)
    args.limit = clamp_positive(args.limit, "--limit")
    names, issuers, source, cert_count = collect_ct(domain, args.timeout)
    data = {"domain": domain, "source": source, "certificates_seen": cert_count,
            "unique_names": len(names), "names": names,
            "issuers": sorted(issuers.items(), key=lambda kv: -kv[1])[:10]}

    def show(d):
        hr(f"Certificate Transparency: {d['domain']}  ({d['source']})")
        kv("Certs seen", d["certificates_seen"])
        kv("Unique names", d["unique_names"])
        for n in d["names"][: args.limit]:
            print(f"    {n}")
        if len(d["names"]) > args.limit:
            print(f"    ... +{len(d['names']) - args.limit} more (--limit)")
        if d["issuers"]:
            print("  Top issuers:")
            for iss, cnt in d["issuers"][:5]:
                print(f"    {cnt:>4}x {truncate(iss, 90)}")
        print("\n  Note: CT logs are historical - names may be stale or never deployed.")

    emit(data, args.json, show)


def _resolve_one(name):
    try:
        infos = socket.getaddrinfo(name, None, proto=socket.IPPROTO_TCP)
        ips = sorted({i[4][0] for i in infos})
        return name, ips
    except Exception:
        return name, []


def cmd_subdomains(args):
    domain = normalize_domain(args.domain)
    args.limit = clamp_positive(args.limit, "--limit")
    args.workers = clamp_positive(args.workers, "--workers")
    names, _issuers, source, _cnt = collect_ct(domain, args.timeout)
    names = [n for n in names if n != domain] if args.exclude_apex else names
    if not names:
        raise OsintError(f"No names found in CT logs for {domain}")

    checked = names[: args.limit]
    results = []
    if args.no_resolve:
        results = [{"name": n, "ips": [], "status": "unchecked"} for n in checked]
    else:
        socket.setdefaulttimeout(args.timeout)
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
            for name, ips in pool.map(_resolve_one, checked):
                results.append({"name": name, "ips": ips,
                                "status": "resolved" if ips else "dead"})
        results.sort(key=lambda r: (r["status"] != "resolved", r["name"]))

    alive = [r for r in results if r["status"] == "resolved"]
    data = {"domain": domain, "source": source, "found_in_ct": len(names),
            "checked": len(results), "resolved": len(alive),
            "dead": len(results) - len(alive) if not args.no_resolve else None,
            "subdomains": results}

    def show(d):
        hr(f"Subdomains {d['domain']}  ({d['source']})")
        kv("Found in CT", d["found_in_ct"])
        kv("Checked", d["checked"])
        if not args.no_resolve:
            kv("Resolved / dead", f"{d['resolved']} / {d['dead']}")
        print()
        for r in d["subdomains"]:
            mark = OK if r["status"] == "resolved" else (INFO if r["status"] == "dead" else "[  ? ]")
            ips = ", ".join(r["ips"][:3]) + (" …" if len(r["ips"]) > 3 else "")
            print(f"  {mark} {r['name']:<45} {ips}")
        if d["found_in_ct"] > d["checked"]:
            print(f"\n  ... +{d['found_in_ct'] - d['checked']} more names not checked (--limit)")

    emit(data, args.json, show)


# ========== ports ==========

def cmd_ports(args):
    target = require_target(args.ip, "IP/hostname")
    if not is_ip(target):
        ips = guard_hostname(target)
        print(f"(resolved {target} -> {ips[0]})", file=sys.stderr)
        target = ips[0]
    guard_ip(target)

    key = os.environ.get("SHODAN_API_KEY")
    data = None
    if key and not args.no_key:
        try:
            raw = fetch_json(
                f"https://api.shodan.io/shodan/host/{target}?key={urllib.parse.quote(key)}",
                timeout=args.timeout, source="api.shodan.io")
            services = []
            for item in raw.get("data") or []:
                services.append({
                    "port": item.get("port"), "transport": item.get("transport"),
                    "product": item.get("product"), "version": item.get("version"),
                    "banner": truncate(item.get("data"), 160),
                })
            data = {
                "ip": target, "source": "api.shodan.io (SHODAN_API_KEY)",
                "ports": sorted(raw.get("ports") or []),
                "hostnames": raw.get("hostnames") or [],
                "cpes": raw.get("cpes") or [], "tags": raw.get("tags") or [],
                "vulns": sorted(raw.get("vulns") or []),
                "org": raw.get("org"), "isp": raw.get("isp"), "os": raw.get("os"),
                "country": raw.get("country_name"), "last_update": raw.get("last_update"),
                "services": services,
            }
        except (OsintError, RateLimited) as e:
            print(f"(Shodan API failed: {e}; falling back to free InternetDB)", file=sys.stderr)

    if data is None:
        raw = fetch_json(f"https://internetdb.shodan.io/{target}",
                         timeout=args.timeout, source="internetdb.shodan.io")
        data = {
            "ip": raw.get("ip", target), "source": "internetdb.shodan.io (free, no key)",
            "ports": sorted(raw.get("ports") or []),
            "hostnames": raw.get("hostnames") or [],
            "cpes": raw.get("cpes") or [], "tags": raw.get("tags") or [],
            "vulns": sorted(raw.get("vulns") or []), "services": [],
        }

    def show(d):
        hr(f"Exposure {d['ip']}  ({d['source']})")
        kv("Hostnames", d.get("hostnames"))
        kv("Org / ISP", " / ".join(x for x in [d.get("org"), d.get("isp")] if x) or None)
        kv("Country", d.get("country"))
        kv("Last update", d.get("last_update"))
        kv("Open ports", ", ".join(str(p) for p in d["ports"]) or "none seen")
        kv("Tags", d.get("tags"))
        kv("Software (CPE)", d.get("cpes"))
        if d.get("services"):
            print("  Services:")
            for s in d["services"]:
                head = f"{s['port']}/{s.get('transport') or 'tcp'}"
                prod = " ".join(x for x in [s.get("product"), s.get("version")] if x)
                print(f"    {head:<10} {prod or ''}")
                if s.get("banner"):
                    print(f"    {'':<10} {s['banner']}")
        if d["vulns"]:
            print(f"  {BAD} Known CVEs ({len(d['vulns'])}):")
            for v in d["vulns"][:20]:
                print(f"      {v}")
            if len(d["vulns"]) > 20:
                print(f"      ... +{len(d['vulns']) - 20} more")
        else:
            print(f"  {OK} No CVEs listed for this host")
        print("\n  Note: Shodan data is a periodic scan snapshot, not a live check.")

    emit(data, args.json, show)


# ========== headers ==========

SEC_HEADERS = [
    ("strict-transport-security", "HSTS", True),
    ("content-security-policy", "CSP", True),
    ("x-frame-options", "X-Frame-Options", True),
    ("x-content-type-options", "X-Content-Type-Options", True),
    ("referrer-policy", "Referrer-Policy", True),
    ("permissions-policy", "Permissions-Policy", False),
    ("cross-origin-opener-policy", "COOP", False),
    ("cross-origin-resource-policy", "CORP", False),
]
DISCLOSURE_HEADERS = ["server", "x-powered-by", "x-aspnet-version", "x-aspnetmvc-version",
                      "x-generator", "x-drupal-cache", "x-runtime"]


def audit_headers(headers, is_https, cookies):
    lower = {k.lower(): v for k, v in headers.items()}
    findings, score, maxscore = [], 0, 0

    for key, label, required in SEC_HEADERS:
        value = lower.get(key)
        weight = 2 if required else 1
        maxscore += weight
        if key == "strict-transport-security":
            if not is_https:
                findings.append((INFO, label, "n/a over plain HTTP"))
                maxscore -= weight
                continue
            if not value:
                findings.append((BAD, label, "missing - no HTTPS enforcement"))
                continue
            m = re.search(r"max-age\s*=\s*(\d+)", value)
            age = int(m.group(1)) if m else 0
            if age < 15552000:
                findings.append((WARN, label, f"max-age={age} (<180d recommended minimum)"))
                score += 1
            elif "includesubdomains" not in value.lower():
                findings.append((WARN, label, "no includeSubDomains"))
                score += 1
            else:
                findings.append((OK, label, truncate(value, 80)))
                score += weight
        elif key == "content-security-policy":
            if not value:
                findings.append((BAD, label, "missing - no XSS/injection mitigation"))
                continue
            weak = [t for t in ("'unsafe-inline'", "'unsafe-eval'") if t in value.lower()]
            if weak:
                findings.append((WARN, label, f"present but weak: {', '.join(weak)}"))
                score += 1
            else:
                findings.append((OK, label, truncate(value, 80)))
                score += weight
        elif key == "x-frame-options":
            frame_anc = "frame-ancestors" in (lower.get("content-security-policy") or "").lower()
            if value:
                good = value.strip().lower() in ("deny", "sameorigin")
                findings.append((OK if good else WARN, label, value))
                score += weight if good else 1
            elif frame_anc:
                findings.append((OK, label, "absent, but CSP frame-ancestors covers clickjacking"))
                score += weight
            else:
                findings.append((BAD, label, "missing - clickjacking possible"))
        elif key == "x-content-type-options":
            if value and value.strip().lower() == "nosniff":
                findings.append((OK, label, value))
                score += weight
            elif value:
                findings.append((WARN, label, f"unexpected value: {value}"))
                score += 1
            else:
                findings.append((BAD, label, "missing - MIME sniffing allowed"))
        else:
            if value:
                findings.append((OK, label, truncate(value, 80)))
                score += weight
            else:
                findings.append((WARN if required else INFO, label, "missing"))

    disclosure = {h: lower[h] for h in DISCLOSURE_HEADERS if h in lower}
    acao = lower.get("access-control-allow-origin")
    extra = []
    if acao == "*":
        extra.append((WARN, "CORS", "Access-Control-Allow-Origin: * (open to any origin)"))
    if disclosure:
        extra.append((WARN, "Disclosure",
                      ", ".join(f"{k}: {v}" for k, v in disclosure.items())))
    for c in cookies:
        cl = c.lower()
        missing = [f for f, t in (("Secure", "secure"), ("HttpOnly", "httponly"),
                                  ("SameSite", "samesite")) if t not in cl]
        if missing:
            name = c.split("=")[0]
            extra.append((WARN, "Cookie", f"{name}: missing {', '.join(missing)}"))

    pct = round(100 * score / maxscore) if maxscore else 0
    grade = "A" if pct >= 90 else "B" if pct >= 75 else "C" if pct >= 55 else \
            "D" if pct >= 35 else "F"
    return findings, extra, score, maxscore, pct, grade


def cmd_headers(args):
    url, parsed, ips = guard_url(args.url)
    status, rheaders, body, final_url = http_request(
        url, timeout=args.timeout, method="GET", allow_redirects=not args.no_redirect,
        source=parsed.hostname)
    final_parsed = urllib.parse.urlparse(final_url)
    if final_parsed.hostname and final_parsed.hostname != parsed.hostname:
        guard_hostname(final_parsed.hostname)

    cookies = []
    raw_cookie = rheaders.get("Set-Cookie") or rheaders.get("set-cookie")
    if raw_cookie:
        cookies = [raw_cookie] if isinstance(raw_cookie, str) else list(raw_cookie)

    findings, extra, score, maxscore, pct, grade = audit_headers(
        rheaders, final_parsed.scheme == "https", cookies)

    redirected = final_url.rstrip("/") != url.rstrip("/")
    data = {
        "url": url, "final_url": final_url, "redirected": redirected, "status": status,
        "resolved_ips": ips, "grade": grade, "score": f"{score}/{maxscore}", "percent": pct,
        "checks": [{"verdict": v.strip("[] "), "header": h, "detail": d} for v, h, d in findings],
        "notes": [{"verdict": v.strip("[] "), "topic": h, "detail": d} for v, h, d in extra],
        "headers": {k: v for k, v in rheaders.items()},
    }

    def show(d):
        hr(f"Security headers: {d['final_url']}")
        kv("HTTP status", d["status"])
        if d["redirected"]:
            kv("Redirected to", d["final_url"])
        kv("Resolved IPs", d["resolved_ips"])
        kv("Grade", f"{d['grade']}  ({d['score']}, {d['percent']}%)")
        print()
        for verdict, header, detail in findings:
            print(f"  {verdict} {header:<26} {detail}")
        if extra:
            print()
            for verdict, topic, detail in extra:
                print(f"  {verdict} {topic:<26} {truncate(detail, 100)}")
        if args.show_all:
            print("\n  All response headers:")
            for k, v in sorted(d["headers"].items()):
                print(f"    {k}: {truncate(v, 120)}")

    emit(data, args.json, show)


# ========== sanctions ==========

def sanctions_opensanctions(query, limit, timeout, key):
    url = ("https://api.opensanctions.org/search/default"
           f"?q={urllib.parse.quote(query)}&limit={limit}")
    headers = {"Authorization": f"ApiKey {key}"} if key else {}
    raw = fetch_json(url, timeout=timeout, headers=headers, source="api.opensanctions.org")
    total = raw.get("total")
    if isinstance(total, dict):  # API returns {"value": N, "relation": "eq"|"gte"}
        total = total.get("value")
    results = []
    for r in raw.get("results") or []:
        props = r.get("properties") or {}
        results.append({
            "id": r.get("id"), "caption": r.get("caption"), "schema": r.get("schema"),
            "score": round(r.get("score", 0), 3),
            "datasets": r.get("datasets") or [],
            "topics": props.get("topics") or [],
            "countries": props.get("country") or props.get("nationality") or [],
            "birth_date": (props.get("birthDate") or [None])[0],
            "first_seen": r.get("first_seen"), "last_seen": r.get("last_seen"),
            "url": f"https://www.opensanctions.org/entities/{r.get('id')}/" if r.get("id") else None,
        })
    return results, "api.opensanctions.org", (total if isinstance(total, int) else len(results))


def _ofac_cached(name, url, ttl_days=7, timeout=60):
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    path = CACHE_DIR / name
    if path.exists():
        age_days = (time.time() - path.stat().st_mtime) / 86400
        if age_days < ttl_days and path.stat().st_size > 1000:
            return path
    status, _h, body, _u = http_request(url, timeout=timeout, source="ofac.treas.gov")
    if status != 200 or len(body) < 1000:
        if path.exists():
            return path  # stale beats nothing
        raise OsintError(f"OFAC list download failed (HTTP {status}) and no cache available")
    path.write_bytes(body)
    return path


def sanctions_ofac(query, limit, timeout):
    """Free fallback: OFAC SDN list, downloaded once and cached locally."""
    sdn = _ofac_cached("sdn.csv", "https://sanctionslistservice.ofac.treas.gov/api/download/sdn.csv",
                       timeout=timeout)
    alt = _ofac_cached("alt.csv", "https://sanctionslistservice.ofac.treas.gov/api/download/alt.csv",
                       timeout=timeout)
    needle = query.lower()
    results, seen = [], set()

    def clean(v):
        v = (v or "").strip()
        return None if v in ("-0-", "") else v

    with sdn.open(encoding="utf-8", errors="replace", newline="") as fh:
        for row in csv.reader(fh):
            if len(row) < 4:
                continue
            ent, sdn_name, sdn_type, program = row[0], row[1], clean(row[2]), clean(row[3])
            # "-0-" in the SDN_Type column means a legal entity, not an unknown type;
            # multiple programs are encoded as "NPWMD] [RUSSIA-EO14024".
            sdn_type = (sdn_type or "entity").title()
            program = (program or "").replace("] [", ", ") or None
            remarks = clean(row[11]) if len(row) > 11 else None
            if needle in (sdn_name or "").lower():
                key = ("sdn", ent)
                if key in seen:
                    continue
                seen.add(key)
                results.append({"id": f"OFAC-SDN-{ent}", "caption": sdn_name.strip(),
                                "schema": sdn_type or "Unknown", "match": "primary name",
                                "datasets": ["us_ofac_sdn"], "program": program,
                                "topics": ["sanction"], "remarks": truncate(remarks, 200),
                                "url": "https://sanctionssearch.ofac.treas.gov/"})
    if alt.exists():
        with alt.open(encoding="utf-8", errors="replace", newline="") as fh:
            for row in csv.reader(fh):
                if len(row) < 4:
                    continue
                ent, alt_name = row[0], clean(row[3])
                if alt_name and needle in alt_name.lower():
                    key = ("alt", ent, alt_name)
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append({"id": f"OFAC-SDN-{ent}", "caption": alt_name,
                                    "schema": "Alias", "match": f"alias of entity {ent}",
                                    "datasets": ["us_ofac_sdn"], "topics": ["sanction"],
                                    "url": "https://sanctionssearch.ofac.treas.gov/"})

    # Return the FULL match count, not just the page: a screening tool that prints
    # "matches: 10" while 88 entries hit is an undercount a compliance user would act on.
    return results[:limit], "OFAC SDN (cached CSV, US list only)", len(results)


def cmd_sanctions(args):
    query = require_target(args.query, "query")
    args.limit = clamp_positive(args.limit, "--limit")
    if len(query) < 3:
        raise OsintError("Query too short - give at least 3 characters")
    key = os.environ.get("OPENSANCTIONS_API_KEY")
    source_note = None
    try:
        if not key:
            raise OsintError("no OPENSANCTIONS_API_KEY set")
        results, source, total = sanctions_opensanctions(query, args.limit, args.timeout, key)
    except (OsintError, RateLimited) as e:
        source_note = (f"OpenSanctions unavailable ({e}); using free OFAC SDN fallback "
                       "(US list only, exact substring match)")
        print(f"({source_note})", file=sys.stderr)
        results, source, total = sanctions_ofac(query, args.limit, max(args.timeout, 60))

    # The OFAC CSVs are Latin-script only: a Cyrillic query can never match and would
    # otherwise read as a confident "clean" result.
    caveat = None
    if source.startswith("OFAC") and not query.isascii():
        caveat = ("query is not Latin script - the OFAC SDN list stores transliterated "
                  "Latin names only, so a non-Latin query CANNOT match. Retry with the "
                  "transliteration (e.g. 'Ivanov'), or set OPENSANCTIONS_API_KEY.")
        print(f"({BAD} {caveat})", file=sys.stderr)

    hidden = max(0, (total or 0) - len(results))
    data = {"query": query, "source": source, "note": source_note, "caveat": caveat,
            "total_matches": total, "shown": len(results), "truncated": bool(hidden),
            "matches": len(results), "results": results}

    def show(d):
        hr(f"Sanctions / PEP screening: \"{d['query']}\"  ({d['source']})")
        if d.get("caveat"):
            print(f"  {BAD} {d['caveat']}")
        kv("Total matches", d.get("total_matches"), 14)
        if d["truncated"]:
            print(f"  {WARN} showing {d['shown']} of {d['total_matches']} - "
                  f"{hidden} more suppressed by --limit; raise it before concluding anything")
        if not d["results"]:
            print(f"  {OK} No matches in the consulted list(s).")
        for r in d["results"]:
            topics = ", ".join(r.get("topics") or []) or "-"
            print(f"\n  {HIT} {r.get('caption')}   [{r.get('schema')}]")
            kv("id", r.get("id"), 14)
            kv("score", r.get("score"), 14)
            kv("match", r.get("match"), 14)
            kv("topics", topics, 14)
            kv("countries", r.get("countries"), 14)
            kv("birth date", r.get("birth_date"), 14)
            kv("program", r.get("program"), 14)
            kv("datasets", (r.get("datasets") or [])[:6], 14)
            kv("remarks", r.get("remarks"), 14)
            kv("url", r.get("url"), 14)
        if d["truncated"]:
            print(f"\n  ... +{hidden} more matches not shown (--limit {args.limit})")
        print("\n  Name matches are NOT identity confirmation - verify DOB/passport/registry"
              "\n  before acting. This is screening, not a legal determination.")

    emit(data, args.json, show)


# ========== cve ==========

CVE_RE = re.compile(r"^CVE-\d{4}-\d{4,}$", re.I)


def nvd_get(params, timeout):
    url = "https://services.nvd.nist.gov/rest/json/cves/2.0?" + urllib.parse.urlencode(params)
    return fetch_json(url, timeout=timeout, source="services.nvd.nist.gov")


def parse_cve(item):
    cve = item.get("cve") or {}
    desc = next((d.get("value") for d in cve.get("descriptions") or []
                 if d.get("lang") == "en"), None)
    metrics = cve.get("metrics") or {}
    score = severity = vector = None
    for mkey in ("cvssMetricV40", "cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        if metrics.get(mkey):
            cdata = metrics[mkey][0].get("cvssData") or {}
            score = cdata.get("baseScore")
            severity = cdata.get("baseSeverity") or metrics[mkey][0].get("baseSeverity")
            vector = cdata.get("vectorString")
            break
    cwes = []
    for w in cve.get("weaknesses") or []:
        for d in w.get("description") or []:
            if d.get("value", "").startswith("CWE-") and d["value"] not in cwes:
                cwes.append(d["value"])
    return {
        "id": cve.get("id"), "published": (cve.get("published") or "")[:10],
        "last_modified": (cve.get("lastModified") or "")[:10],
        "status": cve.get("vulnStatus"), "cvss": score, "severity": severity,
        "vector": vector, "cwe": cwes,
        "description": desc,
        "references": [r.get("url") for r in (cve.get("references") or [])[:5]],
    }


def cmd_cve(args):
    query = require_target(args.query, "keyword/CVE-ID")
    args.limit = clamp_positive(args.limit, "--limit")
    if args.limit > 100:
        # NVD caps a page at 100. Keeping the raw value here used to skew startIndex
        # (total - limit) while only 100 rows came back, so --limit 150 silently
        # returned a window ending 50 entries BEFORE the newest CVE - and still
        # labelled it "newest first".
        print(f"(--limit {args.limit} exceeds the NVD page cap; using 100)", file=sys.stderr)
        args.limit = 100
    params = {"resultsPerPage": args.limit}
    if CVE_RE.match(query):
        params["cveId"] = query.upper()
        raw = nvd_get(params, args.timeout)
        items = raw.get("vulnerabilities") or []
        total = raw.get("totalResults", len(items))
    else:
        base = {"keywordSearch": query}
        if args.exact:
            base["keywordExactMatch"] = ""
        probe = nvd_get({**base, "resultsPerPage": 1}, args.timeout)
        total = probe.get("totalResults", 0)
        if not total:
            items = []
        else:
            start = 0 if args.oldest else max(0, total - args.limit)
            raw = nvd_get({**base, "resultsPerPage": args.limit, "startIndex": start},
                          args.timeout)
            items = raw.get("vulnerabilities") or []
            if not args.oldest:
                items = list(reversed(items))

    results = [parse_cve(i) for i in items]
    data = {"query": query, "total_results": total, "shown": len(results),
            "order": "oldest first" if args.oldest else "newest first",
            "source": "services.nvd.nist.gov (NVD API 2.0)", "results": results}

    def show(d):
        hr(f"CVE search: \"{d['query']}\"  ({d['source']})")
        kv("Total in NVD", d["total_results"])
        kv("Shown", f"{d['shown']} ({d['order']})")
        if not results:
            print("  No CVEs matched.")
        for r in results:
            sev = (r.get("severity") or "UNKNOWN").upper()
            mark = BAD if sev in ("CRITICAL", "HIGH") else WARN if sev == "MEDIUM" else INFO
            print(f"\n  {mark} {r['id']}  CVSS {r.get('cvss') or '-'} {sev}   "
                  f"published {r.get('published')}")
            if r.get("cwe"):
                print(f"        {', '.join(r['cwe'][:4])}")
            print(f"        {truncate(r.get('description'), 320)}")
            for ref in (r.get("references") or [])[:2]:
                print(f"        ref: {ref}")
        print("\n  NVD without an API key allows ~5 requests / 30s - slow down if you see 429.")

    emit(data, args.json, show)


# ========== recon ==========

def _safe(label, fn):
    try:
        return {"ok": True, "data": fn()}
    except (OsintError, RateLimited) as e:
        return {"ok": False, "error": str(e)}
    except Exception as e:  # keep the summary alive
        return {"ok": False, "error": f"{type(e).__name__}: {e}"}


def cmd_recon(args):
    domain = normalize_domain(args.domain)
    report = {"domain": domain, "generated": datetime.now(timezone.utc).isoformat(timespec="seconds")}

    dns_res = _safe("dns", lambda: collect_dns(domain, timeout=args.timeout))
    records = dns_res["data"][0] if dns_res["ok"] else {}
    report["dns"] = {"ok": dns_res["ok"],
                     "resolver": dns_res["data"][1] if dns_res["ok"] else None,
                     "records": records, "error": dns_res.get("error")}

    a_records = [r for r in (records.get("A") or []) if is_ip(r)]
    primary_ip = a_records[0] if a_records else None

    report["whois"] = _safe("whois", lambda: _recon_whois(domain, args.timeout))
    report["asn"] = _safe("asn", lambda: _recon_asn(primary_ip, args.timeout)) if primary_ip \
        else {"ok": False, "error": "no A record to trace"}
    report["ip"] = _safe("ip", lambda: source_ip_api(guard_ip(primary_ip), args.timeout)) \
        if primary_ip else {"ok": False, "error": "no A record to geolocate"}
    report["certs"] = _safe("certs", lambda: _recon_certs(domain, args.timeout))
    report["ports"] = _safe("ports", lambda: _recon_ports(primary_ip, args.timeout)) if primary_ip \
        else {"ok": False, "error": "no A record to check"}
    report["headers"] = _safe("headers", lambda: _recon_headers(domain, args.timeout))

    verdicts = _recon_verdicts(report, records)
    report["verdicts"] = verdicts

    def show(d):
        print(f"\n{'=' * 62}\n  RECON: {d['domain']}    {d['generated']}\n{'=' * 62}")

        hr("DNS")
        if d["dns"]["ok"]:
            for rt in DNS_TYPES:
                vals = d["dns"]["records"].get(rt) or []
                if vals:
                    print(f"  {rt:<6} {vals[0]}")
                    for v in vals[1:4]:
                        print(f"  {'':<6} {v}")
                    if len(vals) > 4:
                        print(f"  {'':<6} ... +{len(vals) - 4} more")
        else:
            print(f"  {BAD} {d['dns']['error']}")

        hr("Registration (RDAP)")
        if d["whois"]["ok"]:
            w = d["whois"]["data"]
            kv("Registrar", w.get("registrar"))
            kv("Registered", w.get("registered"))
            kv("Expires", w.get("expires"))
            kv("Status", w.get("status"))
        else:
            print(f"  {INFO} {d['whois']['error']}")

        hr("Network")
        if d["ip"]["ok"]:
            i = d["ip"]["data"]
            kv("Primary IP", i.get("ip"))
            kv("Location", " / ".join(x for x in [i.get("country"), i.get("city")] if x))
            kv("ISP / Org", " / ".join(x for x in [i.get("isp"), i.get("org")] if x))
            hosting = (i.get("flags") or {}).get("hosting_datacenter")
            kv("Hosting/DC", "yes" if hosting else "no" if hosting is not None else None)
        else:
            print(f"  {INFO} {d['ip']['error']}")
        if d["asn"]["ok"]:
            a = d["asn"]["data"]
            kv("ASN", f"{a.get('asn')} {a.get('holder') or ''}")
            kv("Prefix", a.get("prefix"))
            kv("Announced pfx", a.get("prefix_count"))
        else:
            print(f"  {INFO} {d['asn']['error']}")

        hr("Exposure (Shodan InternetDB)")
        if d["ports"]["ok"]:
            p = d["ports"]["data"]
            kv("Open ports", ", ".join(str(x) for x in p.get("ports") or []) or "none seen")
            kv("Known CVEs", ", ".join(p.get("vulns") or [])[:400] or "none")
            kv("Tags", p.get("tags"))
        else:
            print(f"  {INFO} {d['ports']['error']}")

        hr("Certificate Transparency")
        if d["certs"]["ok"]:
            c = d["certs"]["data"]
            kv("Unique names", c.get("unique_names"))
            kv("Source", c.get("source"))
            for n in (c.get("sample") or [])[:10]:
                print(f"    {n}")
            if c.get("unique_names", 0) > 10:
                print(f"    ... (osint_client.py subdomains {d['domain']} for the full list)")
        else:
            print(f"  {INFO} {d['certs']['error']}")

        hr("HTTP security headers")
        if d["headers"]["ok"]:
            h = d["headers"]["data"]
            kv("URL", h.get("final_url"))
            kv("Grade", f"{h.get('grade')} ({h.get('score')}, {h.get('percent')}%)")
            for c in h.get("checks") or []:
                print(f"  [{c['verdict']:^4}] {c['header']:<26} {truncate(c['detail'], 60)}")
        else:
            print(f"  {INFO} {d['headers']['error']}")

        hr("VERDICTS")
        for v in d["verdicts"]:
            print(f"  [{v['verdict']:^4}] {v['check']:<26} {v['detail']}")
        print()

    emit(report, args.json, show)


def _recon_whois(domain, timeout):
    raw = fetch_json(f"https://rdap.org/domain/{domain}", timeout=timeout, source="rdap.org")
    events = rdap_events(raw.get("events"))
    entities = rdap_entities(raw.get("entities"))
    return {"registrar": next((e["name"] for e in entities
                               if "registrar" in (e.get("roles") or [])), None),
            "registered": events.get("registration"), "expires": events.get("expiration"),
            "status": raw.get("status") or []}


def _recon_asn(ip, timeout):
    asn, prefix = asn_from_ip(ip)
    ov = ripe("as-overview", f"AS{asn}", timeout=timeout)
    try:
        pfx = ripe("announced-prefixes", f"AS{asn}", timeout=timeout).get("prefixes") or []
    except Exception:
        pfx = []
    return {"asn": f"AS{asn}", "holder": ov.get("holder"), "prefix": prefix,
            "prefix_count": len(pfx)}


def _recon_certs(domain, timeout):
    names, issuers, source, count = collect_ct(domain, timeout)
    return {"unique_names": len(names), "certificates_seen": count,
            "source": source, "sample": names[:20]}


def _recon_ports(ip, timeout):
    guard_ip(ip)
    raw = fetch_json(f"https://internetdb.shodan.io/{ip}", timeout=timeout,
                     source="internetdb.shodan.io")
    return {"ip": ip, "ports": sorted(raw.get("ports") or []),
            "vulns": sorted(raw.get("vulns") or []), "tags": raw.get("tags") or [],
            "hostnames": raw.get("hostnames") or []}


def _recon_headers(domain, timeout):
    url, parsed, ips = guard_url(f"https://{domain}")
    status, rheaders, _body, final_url = http_request(url, timeout=timeout, source=domain)
    final = urllib.parse.urlparse(final_url)
    raw_cookie = rheaders.get("Set-Cookie") or rheaders.get("set-cookie")
    cookies = [raw_cookie] if isinstance(raw_cookie, str) else list(raw_cookie or [])
    findings, extra, score, maxscore, pct, grade = audit_headers(
        rheaders, final.scheme == "https", cookies)
    return {"final_url": final_url, "status": status, "grade": grade,
            "score": f"{score}/{maxscore}", "percent": pct,
            "checks": [{"verdict": v.strip("[] "), "header": h, "detail": d}
                       for v, h, d in findings],
            "notes": [{"verdict": v.strip("[] "), "topic": h, "detail": d} for v, h, d in extra]}


def _recon_verdicts(report, records):
    v = []

    def add(verdict, check, detail):
        v.append({"verdict": verdict.strip("[] "), "check": check, "detail": detail})

    add(OK if records.get("A") or records.get("AAAA") else BAD, "DNS resolves",
        f"{len(records.get('A') or [])} A, {len(records.get('AAAA') or [])} AAAA")
    mx = [m for m in (records.get("MX") or []) if (m or "").strip()]
    # "0 ." is the RFC 7505 null MX. Empty/garbage entries must not crash the summary.
    null_mx = len(mx) == 1 and mx[0].strip().split()[-1].rstrip(".") == ""
    if not mx:
        add(INFO, "Mail (MX)", "no MX - domain does not receive mail")
    elif null_mx:
        add(INFO, "Mail (MX)", "null MX (RFC 7505) - domain explicitly accepts no mail")
    else:
        add(OK, "Mail (MX)", f"{len(mx)} records: {truncate(', '.join(mx), 60)}")

    txt = " ".join(records.get("TXT") or []).lower()
    add(OK if "v=spf1" in txt else WARN, "SPF",
        "present" if "v=spf1" in txt else "missing - spoofing easier")
    dmarc = report.get("_dmarc")
    if dmarc is None:
        try:
            drec, _ = collect_dns(f"_dmarc.{report['domain']}", ["TXT"])
            dmarc_txt = " ".join(drec.get("TXT") or []).lower()
        except Exception:
            dmarc_txt = ""
        add(OK if "v=dmarc1" in dmarc_txt else WARN, "DMARC",
            "present" if "v=dmarc1" in dmarc_txt else "missing at _dmarc record")

    if report["whois"]["ok"]:
        exp = report["whois"]["data"].get("expires")
        detail = f"expires {exp}" if exp else "no expiry in RDAP"
        verdict = OK
        if exp:
            try:
                dt = datetime.fromisoformat(exp.replace("Z", "+00:00"))
                days = (dt - datetime.now(timezone.utc)).days
                detail = f"expires {exp[:10]} ({days} days)"
                verdict = BAD if days < 30 else WARN if days < 90 else OK
            except Exception:
                pass
        add(verdict, "Domain expiry", detail)

    if report["ports"]["ok"]:
        p = report["ports"]["data"]
        risky = [x for x in p.get("ports") or []
                 if x in (21, 22, 23, 25, 445, 1433, 3306, 3389, 5432, 6379, 9200, 27017)]
        add(WARN if risky else OK, "Exposed admin/db ports",
            ", ".join(str(x) for x in risky) if risky else "none of the usual suspects")
        add(BAD if p.get("vulns") else OK, "Known CVEs on host",
            ", ".join(p["vulns"][:8]) if p.get("vulns") else "none listed")

    if report["headers"]["ok"]:
        h = report["headers"]["data"]
        g = h.get("grade")
        add(OK if g in ("A", "B") else WARN if g == "C" else BAD, "HTTP header hygiene",
            f"grade {g} ({h.get('score')})")

    if report["certs"]["ok"]:
        n = report["certs"]["data"].get("unique_names", 0)
        add(INFO if n < 50 else WARN, "Attack surface (CT)",
            f"{n} names in CT logs" + (" - large surface, review subdomains" if n >= 50 else ""))

    return v


# ========== CLI ==========

def build_parser():
    p = argparse.ArgumentParser(
        prog="osint_client.py",
        description="OSINT recon over PUBLIC sources. Request-driven, no daemons. "
                    "Infrastructure and counterparty checks only - not for surveilling people.",
        epilog="Examples:\n"
               "  python osint_client.py recon example.com\n"
               "  python osint_client.py dns example.com --types A,MX,TXT\n"
               "  python osint_client.py ports YOUR_PUBLIC_IP --json\n"
               "  python osint_client.py cve \"openssl\" --limit 5\n"
               "\nOut of scope by design: live flight/vessel/satellite tracking "
               "(needs constant polling).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    p.add_argument("--json", action="store_true", help="machine-readable JSON output")
    p.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT,
                   help=f"per-request timeout in seconds (default {DEFAULT_TIMEOUT})")

    # Same global flags accepted AFTER the subcommand too (SUPPRESS keeps the
    # top-level value when the flag is not repeated).
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--json", action="store_true", default=argparse.SUPPRESS,
                        help="machine-readable JSON output")
    common.add_argument("--timeout", type=int, default=argparse.SUPPRESS,
                        help=f"per-request timeout in seconds (default {DEFAULT_TIMEOUT})")

    sub = p.add_subparsers(dest="command", metavar="<command>")
    _add = sub.add_parser

    def sub_add_parser(name, **kw):
        kw.setdefault("parents", [common])
        return _add(name, **kw)

    sub.add_parser = sub_add_parser

    s = sub.add_parser("ip", help="geolocation + ASN + ISP for an IP (ip-api.com / ipinfo.io)")
    s.add_argument("address", help="IPv4/IPv6 address (or hostname - it will be resolved)")
    s.set_defaults(func=cmd_ip)

    s = sub.add_parser("dns", help="A/AAAA/MX/NS/TXT/CNAME/SOA records")
    s.add_argument("domain")
    s.add_argument("--types", help="comma-separated record types (default: all common)")
    s.add_argument("--doh", action="store_true", help="force DNS-over-HTTPS instead of dnspython")
    s.set_defaults(func=cmd_dns)

    s = sub.add_parser("whois", help="RDAP registration data for a domain or IP (HTTP+JSON, not port 43)")
    s.add_argument("target", help="domain name or IP address")
    s.set_defaults(func=cmd_whois)

    s = sub.add_parser("asn", help="BGP view: prefixes, upstreams, downstreams (RIPEstat)")
    s.add_argument("target", help="AS number (AS15169 or 15169) or an IP to trace")
    s.add_argument("--all-prefixes", action="store_true", help="print every announced prefix")
    s.set_defaults(func=cmd_asn)

    s = sub.add_parser("certs", help="names seen in Certificate Transparency logs (crt.sh)")
    s.add_argument("domain")
    s.add_argument("--limit", type=int, default=60, help="max names to print (default 60)")
    s.set_defaults(func=cmd_certs)

    s = sub.add_parser("ports", help="open ports / CVEs from Shodan InternetDB (free, no key)")
    s.add_argument("ip", help="IP address (or hostname - it will be resolved)")
    s.add_argument("--no-key", action="store_true", help="ignore SHODAN_API_KEY, use free InternetDB")
    s.set_defaults(func=cmd_ports)

    s = sub.add_parser("headers", help="HTTP security header audit with a per-header verdict")
    s.add_argument("url", help="https://example.com (scheme optional)")
    s.add_argument("--show-all", action="store_true", help="dump every response header")
    s.add_argument("--no-redirect", action="store_true", help="do not follow redirects")
    s.set_defaults(func=cmd_headers)

    s = sub.add_parser("sanctions", help="sanctions/PEP screening (OpenSanctions, OFAC SDN fallback)")
    s.add_argument("query", help="person or company name")
    s.add_argument("--limit", type=int, default=10)
    s.set_defaults(func=cmd_sanctions)

    s = sub.add_parser("cve", help="vulnerability lookup by keyword or CVE-ID (NVD)")
    s.add_argument("query", help="keyword (e.g. openssl) or CVE-2024-3094")
    s.add_argument("--limit", type=int, default=10, help="max results (default 10, cap 100)")
    s.add_argument("--oldest", action="store_true", help="oldest CVEs first (default: newest)")
    s.add_argument("--exact", action="store_true", help="exact keyword match")
    s.set_defaults(func=cmd_cve)

    s = sub.add_parser("subdomains", help="CT names + live/dead DNS check")
    s.add_argument("domain")
    s.add_argument("--limit", type=int, default=80, help="max names to check (default 80)")
    s.add_argument("--workers", type=int, default=20, help="parallel resolvers (default 20)")
    s.add_argument("--no-resolve", action="store_true", help="skip the liveness check")
    s.add_argument("--exclude-apex", action="store_true", help="drop the apex domain from results")
    s.set_defaults(func=cmd_subdomains)

    s = sub.add_parser("recon", help="one-shot summary: dns + whois + asn + certs + ports + headers")
    s.add_argument("domain")
    s.set_defaults(func=cmd_recon)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    if not getattr(args, "command", None):
        parser.print_help()
        return 1
    try:
        # requests/urllib turn a non-positive timeout into an internal ValueError that
        # then gets retried and printed twice - reject it up front instead.
        if getattr(args, "timeout", 1) < 1:
            raise OsintError(f"--timeout must be 1 second or greater (got {args.timeout})")
        args.func(args)
        return 0
    except BlockedTarget as e:
        print(f"\n{BAD} {e}\n", file=sys.stderr)
        return 3
    except RateLimited as e:
        print(f"\n{WARN} {e}\n", file=sys.stderr)
        return 4
    except OsintError as e:
        print(f"\n{BAD} {e}\n", file=sys.stderr)
        return 2
    except KeyboardInterrupt:
        print("\nInterrupted.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
