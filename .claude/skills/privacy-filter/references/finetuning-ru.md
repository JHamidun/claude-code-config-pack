# Fine-tuning Privacy Filter for Russian (and any out-of-distribution data)

OOB Russian recall ≈ 2/3. Names, addresses, and secrets are weak. OpenAI's own number:
fine-tuning on **10% in-domain data raised F1 from 0.545 to 0.962**. So for serious RU use,
collect a few hundred labelled examples and fine-tune. This is cheap and decisive.

## Dataset schema (same for `opf train` and `opf eval`)

JSONL, one object per line. Span keys are `"<label>: <surface text>"` mapping to a list of
`[start, end]` character offsets (end-exclusive, on the raw `text` string).

```json
{"text": "Клиент John Doe, тел +1234567890.", "spans": {"private_person: John Doe": [[7, 17]], "private_phone: +1234567890": [[24, 40]]}, "info": {"id": "ru_001"}}
```

- Offsets are over Python `str` (Unicode codepoints), not bytes. Verify:
  `text[start:end] == surface`.
- `info` is optional (free-form; `id` recommended for traceability).
- Multiple occurrences of one label/surface → multiple `[start,end]` pairs in the list.
- Use the 8 native labels (`account_number`, `private_address`, `private_email`,
  `private_person`, `private_phone`, `private_url`, `private_date`, `secret`) unless
  defining a custom label space (below).

## Build a labelled set fast

1. Run the model on real RU text to get candidate spans:
   `python scripts/privacy_filter.py -f sample.txt --format json`
2. Hand-correct the misses (names/addresses/secrets) into the JSONL schema above.
   A helper to convert wrapper JSON → train JSONL:

```python
import json
spans = {}
for s in doc["detected_spans"]:                      # doc = one --format json object
    spans.setdefault(f'{s["label"]}: {s["text"]}', []).append([s["start"], s["end"]])
print(json.dumps({"text": doc["redacted_text_source"], "spans": spans}, ensure_ascii=False))
# NOTE: feed the ORIGINAL text, not redacted_text — offsets must match the source string.
```

3. Split into `train.jsonl` and `validation.jsonl` (e.g. 80/20).

## Train

```bash
# Set OPF_MOE_TRITON=0 on Windows/CUDA-without-triton
opf train train.jsonl \
  --validation-dataset validation.jsonl \
  --output-dir ./work/opf-ru-ckpt
```

Writes `config.json`, `model.safetensors`, `finetune_summary.json`, `USAGE.txt`.
Use it via the wrapper: `--checkpoint ./work/opf-ru-ckpt`.

## Evaluate (measure before/after)

```bash
opf eval validation.jsonl --eval-mode typed       # labels match OPF taxonomy
opf eval validation.jsonl --eval-mode untyped     # span-level only + ground_truth_label_recall
```

- `typed` = category-level metrics (use when your labels are the 8 native ones).
- `untyped` = ignores category identity, matches spans only. Use when ground-truth labels
  use a different ontology (e.g. "given name", "street"); reports `ground_truth_label_recall`.

## Custom label space

To train a different ontology (e.g. only `O` + `custom_account_id` + `custom_secret`):

```bash
opf train train.jsonl --validation-dataset validation.jsonl \
  --label-space-json custom_label_space.json --output-dir ckpt/
```

```json
{"category_version": "custom_v1", "span_class_names": ["O", "custom_account_id", "custom_secret"]}
```

`O` must be the first entry. `span_class_names` is the preferred key.

## Demo harnesses (in the repo)

`./work/privacy-filter-opf/examples/scripts/finetuning/` (клон из SKILL.md):
- `finetune_secret_demo.sh` — retrain a category boundary (account_number → secret).
- `finetune_custom_label_demo.sh` — teach a brand-new category.

Both take `--checkpoint` (required), optional `--workdir`, `--output-checkpoint-dir`.

## Calibration without retraining (recall/precision knob)

The Viterbi decoder has transition-bias parameters (background persistence, span entry/
continuation/closure). A `viterbi_calibration.json` ships with the checkpoint. To bias
toward **more masking (higher recall)** vs **less (higher precision)** without fine-tuning,
supply a tuned calibration file:

```python
from opf import OPF
opf = OPF(decode_mode="viterbi").set_viterbi_decoder(calibration_path="my_calib.json")
```

Quick recall floor without any tuning: `--decode argmax` tends to over-segment (noisier
boundaries) but can surface spans Viterbi suppressed — useful as a second pass when
recall matters more than tidy boundaries.
