# RU Firmographics — company-leg sources

Resolve a company from INN / OGRN / name / domain → legal card (директор, выручка, численность, ОКВЭД, статус, аффилированность). Order of preference: **DaData (API) → EGRUL (key-free) → Rusprofile/Checko (web)**.

## 1. DaData — primary (programmatic, no captcha)

Free tier 10k req/day. Key in `DADATA_API_KEY`. Use `scripts/dadata_lookup.py`.

```bash
python scripts/dadata_lookup.py 7700000000          # findById/party — exact card by INN/OGRN
python scripts/dadata_lookup.py --suggest "Company"  # suggest/party — search by name (≤10)
```

Returns: name/name_full, inn, kpp, ogrn, type (LEGAL/INDIVIDUAL), status, director (+post), okved, address, employee_count, income/expense (Росстат), founded, branch_count. Docs: dadata.ru/api/find-party, dadata.ru/api/suggest/party.

## 2. EGRUL — official, free, key-free fallback

`egrul.nalog.ru` unofficial web API (flow mirrors `roma8ok/egrul`): POST `/` `query=<q>` → token `t` → GET `/search-result/<t>` → rows. Use `scripts/egrul_lookup.py`.

```bash
python scripts/egrul_lookup.py 7700000000            # by INN
python scripts/egrul_lookup.py "ПАО крупный банк"        # by name
```

Returns: name, inn, ogrn, kpp, address, **director**, status, reg_date, kind (ul/fl=ИП). The single most authoritative source for the current director (ЕГРЮЛ first-source). Rate-limit gently (≤1 req/2s); captcha appears under load → back off or switch to DaData.

> **Why EGRUL matters for qualification:** press-releases and speaker bios lag by 1+ year. ЕГРЮЛ shows the *legally registered* current гендир. Cross-check role here before trusting a web bio (proven case: a person listed as "ректор" in Vedomosti was replaced per ЕГРЮЛ a year earlier).

## 3. Checko / Rusprofile — web, free tier (the checko + nalog combo)

- **Rusprofile** (rusprofile.ru) — free: реквизиты, ОКВЭД, руководитель, финансы (Росстат), связанные лица. Fast manual check.
- **Checko** (checko.ru) — free card: ИНН/ОГРН, выручка, налоги, госконтракты, арбитраж, аффилированность, **связанные лица и их др. компании**. Has a paid API; without a key, fetch the public card via WebFetch and extract.
- **The combo Pavel mentioned (checko.ru + nalog.ru):** checko.ru gives the rich company picture (finances, links, risks); `egrul.nalog.ru` gives the authoritative legal extract (director, status, founders). Use checko for breadth, ЕГРЮЛ to verify the legal facts. Это про **компанию**, не про человека.

## 4. Domain → company

`scripts/domain_to_company.py <domain>` — scrapes homepage + /contacts/about/requisites for ИНН/ОГРН/emails, then resolves the INN via DaData/EGRUL. RU sites put requisites in the footer or /contacts, /rekvizity, /privacy.

## Hygiene (152-ФЗ lineage)

- Record **source + date** for every field. ≥2 independent sources → High confidence.
- B2B firmographics (юрлицо, директор, выручка) = public/official → fine to store.
- A private individual's personal data (личный мобильный, домашний адрес, паспорт, ИНН-физлица) is NOT firmographics and is out of scope here — qualify on company/role/budget, not on a person's private identifiers.

## Errors

| Error | Fix |
|-------|-----|
| DaData 403 | bad/missing key → fall back to `egrul_lookup.py` |
| DaData 429 | rate limit → slow down |
| EGRUL empty/captcha | back off to 1 req/2s, or use DaData |
| Wrong company on name search | INN beats name; verify top candidate's address/OKVED before trusting |
