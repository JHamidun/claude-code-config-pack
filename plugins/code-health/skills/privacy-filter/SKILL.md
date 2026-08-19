---
name: privacy-filter
description: "Local PII detection and redaction (OpenAI opf, on-device): de-identify text before cloud LLMs, reversible, RU support. Triggers: «strip PII», «anonymize text»."
metadata:
  version: 1.0.0
  updated: 2026-05-31
  model: openai/privacy-filter
  license: Apache-2.0
---

# Privacy Filter (OpenAI `opf`)

Local, on-device PII filter. A 1.5B-param bidirectional token classifier (50M active,
sparse MoE) that labels and redacts personal data in one forward pass. Runs on the
your GPU (or CPU). Everything stays on the machine — nothing leaves for the cloud.

**Primary use:** de-identify text locally, then safely send the obezlichenny version to
a cloud LLM (Claude/GPT). Optionally re-identify the LLM's answer afterwards.

## 8 detected categories

`account_number` · `private_address` · `private_email` · `private_person` ·
`private_phone` · `private_url` · `private_date` · `secret`

## Setup state (this machine)

Already installed and verified:
- Package `opf` installed editable from `${WORKSPACE}/privacy-filter-opf` (official repo).
- Checkpoint at `~/.opf/privacy_filter` (2.7 GB). transformers + ONNX formats also cached
  under `~/.cache/huggingface/hub/models--openai--privacy-filter`.
- Wrapper: `scripts/privacy_filter.py`.

Fresh machine: `pip install -e ${WORKSPACE}/privacy-filter-opf` then first run auto-downloads
the checkpoint from `openai/privacy-filter` to `~/.opf/privacy_filter`.

> CRITICAL (Windows / no-Triton): the MoE kernels default to a Triton path on CUDA and
> crash with `ModuleNotFoundError: triton`. The wrapper sets `OPF_MOE_TRITON=0`
> automatically (pure-PyTorch fallback, still GPU). If calling `opf`/`from opf import OPF`
> directly, export `OPF_MOE_TRITON=0` first.

## Quick start (wrapper)

```bash
cd ~/.claude/skills/privacy-filter

# Detect + see labelled spans as JSON
python scripts/privacy_filter.py "John Doe, john@example.com, +1234567890" --format json

# Redact a file to text (default placeholders <PRIVATE_EMAIL> etc.)
python scripts/privacy_filter.py -f letter.txt --out letter.clean.txt

# Pipe usage
type doc.txt | python scripts/privacy_filter.py
```

Always use real Windows paths (`C:/Users/...`), never `/tmp` — Git Bash mangles
POSIX paths into MSYS paths. Output files are always written UTF-8.

## Reversible redaction — the cloud-LLM round-trip

The model's default placeholders are not unique (`<PRIVATE_PERSON>` repeats), so they
can't be restored. `--reversible` assigns unique tokens (`[PRIVATE_PERSON_1]`, …),
reuses the same token for repeated values (keeps coreference), and writes a restore map.
Round-trip is byte-exact (verified).

```bash
# 1. De-identify locally, keep the map private
python scripts/privacy_filter.py -f contract.txt --reversible \
    --map map.json --out contract.clean.txt

# 2. Send contract.clean.txt to the cloud LLM. Instruct it to KEEP placeholders verbatim.

# 3. Re-identify the LLM's answer locally (no model load needed)
python scripts/privacy_filter.py --restore --map map.json -f llm_answer.txt --out final.txt
```

`map.json` contains real PII → keep it local, never send it anywhere.

## Key options

| Flag | Default | Notes |
|------|---------|-------|
| `--device auto\|cpu\|cuda` | auto | cuda if available |
| `--decode viterbi\|argmax` | viterbi | viterbi = coherent spans; argmax = faster, noisier |
| `--label-mode typed\|redacted` | typed | redacted collapses all to `<REDACTED>` |
| `--reversible` + `--map FILE` | off | unique tokens + restore map |
| `--restore` + `--map FILE` | off | re-identify, no model load |
| `--checkpoint DIR` | `~/.opf/privacy_filter` | or set `$OPF_CHECKPOINT` |
| `--format text\|json` | text | json includes spans + summary |
| `-f FILE` (repeatable), `--out FILE` | — | model loads once for all `-f` files |

## Python API (when scripting beyond the CLI)

```python
import os; os.environ.setdefault("OPF_MOE_TRITON", "0")  # before importing opf
from opf import OPF
opf = OPF(device="cuda", output_mode="typed", decode_mode="viterbi")
r = opf.redact("Alice alice@acme.com")
r.redacted_text                  # "<PRIVATE_PERSON> <PRIVATE_EMAIL>"
[(s.label, s.text, s.start, s.end) for s in r.detected_spans]
```

## Official CLI (`opf`) — eval & fine-tune

```bash
opf "Alice was born on 1990-01-02."        # one-shot (uses GPU; set OPF_MOE_TRITON=0)
opf redact -f file.txt --format json
opf eval dataset.jsonl                       # metrics vs ground truth
opf train train.jsonl --output-dir ckpt/     # fine-tune
```

## Russian-language reality (READ before production on RU text)

Out-of-the-box recall on Russian is roughly two-thirds. Strong: emails, URLs, dates,
phones, account numbers. Weak: **person names** (patronymics/diminutives split or
missed — e.g. "Парамонов | Сергей Викторович" detected as two spans), **addresses**
(partial spans), **secrets** (novel formats missed). OpenAI reports fine-tuning on just
10% in-domain data lifts F1 0.545 → 0.962.

For any RU production use: evaluate on your own data and fine-tune. See
`references/finetuning-ru.md` for the dataset schema, `opf train`/`opf eval` recipes,
and calibration tips.

## Limitations & safety

- **Not anonymization / not a compliance guarantee** — one layer in privacy-by-design.
  Keep human review for medical/legal/financial/HR text.
- Static label policy (8 categories); change it only via fine-tuning, not at runtime.
- `secret` is the weakest category — do not rely on it alone for credentials. Combine
  with regex/entropy scanners for API keys.
- For high recall, prefer `--decode viterbi` (default) over `argmax`.

## Supply-chain note

Use ONLY `openai/privacy-filter` (HuggingFace) and `github.com/openai/privacy-filter`.
A typosquat double (`Open-OSS/privacy-filter`) shipped an infostealer and got 244k
downloads in 18h. Never `pip install` or download a "privacy-filter" from any other org.

## References

- `references/model-card.md` — architecture, decoding/operating points, output schema,
  browser/ONNX + transformers.js usage. Read when tuning precision/recall or deploying
  in a browser/JS app.
- `references/finetuning-ru.md` — Russian fine-tuning: JSONL schema, `opf train`/`eval`,
  custom label spaces, calibration. Read before fine-tuning or evaluating on RU data.
