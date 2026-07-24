# Open-source engines (GitHub) — what to reuse

Curated from research. All listed tools query public endpoints / official data — safe to install and drive from this skill.

## 🟢 Person / footprint (Mode A person-leg)

| Tool | What | Use it for |
|------|------|-----------|
| [holehe](https://github.com/megadose/holehe) | email → registered on 120+ sites (password-reset/registration flows) | confirm an email is real + which platforms → handles to feed `social-intel` |
| [Maigret](https://github.com/soxoj/maigret) | username → presence on 3000+ sites + dossier | expand a `@handle` into a profile map |
| [PhoneInfoga](https://github.com/sundowndev/phoneinfoga) | phone → country/carrier/line-type + footprint search (Numverify/Google/OVH, no cellular touch) | phone leg; ⚠️ stable but unmaintained |
| [ignorant](https://github.com/megadose/ignorant) | phone → registered on Instagram/Amazon/etc (public flows) | reverse phone footprint (holehe family) |
| [theHarvester](https://github.com/laramies/theHarvester) | domain → emails, subdomains, hosts (public) | company-leg: harvest corporate emails/patterns |
| [SpiderFoot](https://github.com/smicallef/spiderfoot) | domain/email/IP → 100+ public sources, modular, self-hosted | deep automated company/domain recon |

Install pattern (optional, on demand): `pipx install holehe maigret ignorant` ; PhoneInfoga/SpiderFoot via their releases. Drive as subprocess and feed JSON into the dossier. These query **public** endpoints — keep to public targets, respect rate limits.

## 🟢 Phone enrichment — the "waterfall" pattern

There is no legitimate OSS that returns a private individual's mobile from a name. Commercial "waterfall" providers (e.g. [FullEnrich](https://fullenrich.com/)) chain many data partnerships. The **legitimate waterfall is already implemented** in `scripts/phone_discovery.py`: company site → 2GIS/Yandex Business (`maps-places`) → hh employer (`headhunter`) → LinkedIn (`linkedin`) → EGRUL/DaData → our Bitrix. For a number the lead gave you, `scripts/phone_identify.py` does the consented Telegram resolve.

### Audited phone/IG OSINT tools (source-reviewed 2026-06-09, not executed)

Cloned and read source (no run). All free, no breach data, no installer/binary red flags except where noted. Use as optional subprocess connectors; respect ToS and rate limits.

| Tool | Verified data source | Free | Caveat |
|------|----------------------|------|--------|
| [PhoneInfoga](https://github.com/sundowndev/phoneinfoga) | Numverify (apilayer) + Google CSE + OVH + dork search | yes | needs Numverify/Google API keys for full; unmaintained; `.so` in repo is a test fixture |
| [phoneintel](https://github.com/phoneintel/phoneintel) | tellows/spamcalls (spam-reputation) + neutrinoapi + IG + OSM + dorks | yes | neutrinoapi key optional |
| [toutatis](https://github.com/megadose/toutatis) | Instagram private API `users/lookup` → obfuscated email/phone-last-digits | yes | IG ToS-grey; needs an IG sessionid |
| [email2phonenumber](https://github.com/martinvigo/email2phonenumber) | Amazon/Twitter/PayPal password-reset flows → masked digits | yes | ToS-adversarial, fragile (breaks when sites change), risk of account flags |
| [Mr.Holmes](https://github.com/Lucksi/Mr.Holmes) | public APIs (GitHub/Twitter/IG/Gravatar/Spotify/LinkedIn) + dorks | yes | ⚠️ ships `Launchers/Win_Launcher.exe` — run the `.py` only, do NOT execute the bundled exe |

Scope: only tools that compute from public/official sources. Anything that returns a private individual's documents/address is out of scope by design.

## 🟢 Lead / firmographic enrichment

| Tool | What | Note |
|------|------|------|
| [firecrawl/fire-enrich](https://github.com/firecrawl/fire-enrich) | email → company via 5 sequential agents (discovery→profile→financial→tech→custom), MIT | **architectural model for our Mode A**; needs Firecrawl+OpenAI; we have the Firecrawl plugin |
| [brightdata/company-data-enrichment](https://github.com/brightdata/company-data-enrichment) | CSV companies → CEO/funding/products | paid Bright Data backend |
| [dominicwhyte/email-enricher](https://github.com/dominicwhyte/email-enricher) | offline email → Fortune-1000 membership | narrow, zero-dep |

## 🟢 RU firmographics (our market)

| Tool | What | Note |
|------|------|------|
| [roma8ok/egrul](https://github.com/roma8ok/egrul) | Go: unofficial egrul.nalog.ru web API | flow reference for our `egrul_lookup.py` |
| [NKaty/dadata.ru-and-nalog.ru-Request-Managers](https://github.com/NKaty/dadata.ru-and-nalog.ru-Request-Managers) | Python: DaData + nalog.ru managers + ЕГРЮЛ/ЕГРИП PDF parser + SQLite queue | closest to our pipeline — borrow PDF-extract parser if needed |
| [atomno-labs/mcp-egrul](https://github.com/atomno-labs/mcp-egrul) | MCP server: ЕГРЮЛ/ЕГРИП scraping + DaData fallback, MIT self-host | could mount as an MCP instead of our script |
| [antonshell/egrul-nalog-parser](https://github.com/antonshell/egrul-nalog-parser) | PHP: ЕГРЮЛ PDF extract parser | parse downloaded выписки |

