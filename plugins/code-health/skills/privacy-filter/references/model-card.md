# OpenAI Privacy Filter — condensed model card

Source: https://huggingface.co/openai/privacy-filter · https://github.com/openai/privacy-filter
Upstream: https://github.com/openai/privacy-filter — там же README, FINETUNING, OUTPUT_SCHEMAS, EVAL_AND_OUTPUT_MODES. Клонируется в `./work/privacy-filter-opf` (см. SKILL.md).

## What it is

Bidirectional token-classification model for PII detection + masking. Pretrained
autoregressively (gpt-oss-like), then converted to an encoder-style token classifier and
post-trained with supervised classification. Labels the whole sequence in ONE forward pass,
then decodes coherent spans with a constrained Viterbi procedure (no token-by-token gen).

| Property | Value |
|----------|-------|
| Params | 1.5B total, 50M active (sparse MoE, 128 experts, top-4) |
| Architecture | 8 pre-norm blocks, d_model=640, GQA (14 q-heads, 2 kv-heads), RoPE |
| Attention | banded, band size 128 (effective window 257 tokens incl. self) |
| Context | 128,000 tokens (no chunking needed) |
| Output head | 33 classes = `O` + 8 labels × {B,I,E,S} (BIOES) |
| License | Apache 2.0 |
| Languages | primarily English; multilingual is weaker (see finetuning-ru.md) |

## Output schema (`opf` / wrapper `--format json`)

```json
{"schema_version": 1,
 "summary": {"output_mode": "typed", "span_count": 3, "by_label": {"private_person": 1}, "decoded_mismatch": false},
 "text": "...", 
 "detected_spans": [{"label": "private_person", "start": 0, "end": 5, "text": "Alice", "placeholder": "<PRIVATE_PERSON>"}],
 "redacted_text": "<PRIVATE_PERSON> ..."}
```

- `--label-mode redacted` collapses every label to `redacted` / `<REDACTED>`.
- `warning` appears only when tokenizer decode doesn't exactly round-trip the input.

## Decoding & operating points (precision/recall knob)

Viterbi uses linear-chain transition scoring with six transition-bias parameters
(background persistence, span entry, continuation, closure, boundary handoff). This makes
each token decision depend on sequence structure → better boundary stability in noisy/
mixed-format text than per-token argmax.

- `--decode viterbi` (default): coherent, contiguous spans. Best recall+precision balance.
- `--decode argmax`: per-token argmax, faster, more fragmented — occasionally surfaces
  spans Viterbi suppressed.
- Bias toward broader masking (recall) vs tighter (precision) by supplying a tuned
  `viterbi_calibration.json` (`OPF(...).set_viterbi_decoder(calibration_path=...)`).
  Default calibration ships in the checkpoint.

## Failure modes (design for these)

- Under-detection: uncommon/regional names, initials, honorific-heavy refs, domain-specific IDs.
- Over-redaction: public entities, orgs, locations, common nouns in ambiguous context;
  benign high-entropy strings (hashes, sample creds, placeholders).
- Boundary drift in mixed-format / heavy-punctuation / long docs.
- `secret`: weakest — misses novel credential formats and split secrets. Pair with
  regex/entropy scanners for API keys.

## Three weight formats in the HF repo

Cached at `~/.cache/huggingface/hub/models--openai--privacy-filter/snapshots/<hash>/`:
- root `*.safetensors` + `tokenizer.json` — HuggingFace `transformers` format.
- `onnx/` — ONNX, for browser / `transformers.js` / non-Python runtimes.
- `original/` — the native `opf` checkpoint format (copied to `~/.opf/privacy_filter`).

## Browser / JS deployment (transformers.js, WebGPU)

```js
import { pipeline } from "@huggingface/transformers";
const clf = await pipeline("token-classification", "openai/privacy-filter",
                           { device: "webgpu", dtype: "q4" });
const out = await clf("Harry Potter harry.potter@hogwarts.edu",
                      { aggregation_strategy: "simple" });
// [{entity_group:'private_person', word:' Harry Potter', score:0.99...}, ...]
```

The HuggingFace blog "How to build scalable web apps with OpenAI's Privacy Filter" covers
Gradio `gr.Server` + span-offset output for on-device sanitization pipelines. Note: the JS
`pipeline` path uses the model's built-in aggregation, not the opf Viterbi decoder, so
boundaries are slightly noisier than the `opf` CLI/Python path.

## HuggingFace `transformers` (Python, no opf package)

```python
from transformers import pipeline
clf = pipeline("token-classification", model="openai/privacy-filter")
clf("My name is Alice Smith")
```

Simpler but lacks the constrained Viterbi decoder and the reversible-redaction helpers.
Prefer the `opf` package (and this skill's wrapper) for production-quality span boundaries.
