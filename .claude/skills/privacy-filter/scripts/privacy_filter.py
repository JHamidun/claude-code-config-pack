#!/usr/bin/env python3
"""Local PII detection / redaction via OpenAI Privacy Filter (opf).

Wraps the official `opf` package. Adds reversible redaction (unique placeholders
+ a restore map) so text can be de-identified, sent to a cloud LLM, and then
re-identified from the LLM's answer.

Examples:
    python privacy_filter.py "Alice (alice@acme.com) was born 1990-01-02."
    python privacy_filter.py -f letter.txt --format json
    python privacy_filter.py -f doc.txt --reversible --map map.json --out clean.txt
    python privacy_filter.py --restore --map map.json -f llm_answer.txt --out final.txt
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

# CRITICAL on Windows / any box without Triton: the MoE kernels default to a
# Triton path on CUDA and crash if triton is absent. Force the pure-PyTorch
# fallback unless triton is importable. Must run BEFORE importing opf.
if "OPF_MOE_TRITON" not in os.environ:
    try:
        import triton  # noqa: F401
    except Exception:
        os.environ["OPF_MOE_TRITON"] = "0"

# Always emit UTF-8 regardless of the host console code page (Windows cp1251 etc.)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except Exception:
        pass

LABELS = (
    "account_number", "private_address", "private_email", "private_person",
    "private_phone", "private_url", "private_date", "secret",
)


def resolve_device(name: str) -> str:
    if name != "auto":
        return name
    try:
        import torch
        return "cuda" if torch.cuda.is_available() else "cpu"
    except Exception:
        return "cpu"


def read_inputs(args) -> list[tuple[str, str]]:
    """Return list of (source_label, text)."""
    items: list[tuple[str, str]] = []
    if args.text:
        items.append(("arg", args.text))
    for fp in args.file or []:
        items.append((fp, Path(fp).read_text(encoding="utf-8")))
    if args.stdin or (not items and not sys.stdin.isatty()):
        data = sys.stdin.read()
        if data:
            items.append(("stdin", data))
    return items


def build_redactor(args):
    from opf import OPF
    return OPF(
        model=args.checkpoint,
        device=resolve_device(args.device),
        output_mode=args.label_mode,
        decode_mode=args.decode,
    )


def reversible_redact(text, spans, mapping, counters, placeholder_tmpl):
    """Rebuild text with unique, reversible placeholders.

    Same (label, surface) reuses the same token so the LLM keeps coreference.
    `mapping` (token -> original) and `counters` (label -> int) persist across
    inputs in one run. Returns redacted text.
    """
    ordered = sorted(spans, key=lambda s: s.start)
    out, cursor = [], 0
    surface_to_token: dict[tuple[str, str], str] = {
        (v["label"], v["text"]): tok for tok, v in mapping.items()
    }
    for sp in ordered:
        if sp.start < cursor:  # defensive: skip overlap
            continue
        key = (sp.label, sp.text)
        token = surface_to_token.get(key)
        if token is None:
            counters[sp.label] = counters.get(sp.label, 0) + 1
            token = placeholder_tmpl.format(
                LABEL=sp.label.upper(), n=counters[sp.label]
            )
            surface_to_token[key] = token
            mapping[token] = {"text": sp.text, "label": sp.label}
        out.append(text[cursor:sp.start])
        out.append(token)
        cursor = sp.end
    out.append(text[cursor:])
    return "".join(out)


def do_restore(args):
    mp = json.loads(Path(args.map).read_text(encoding="utf-8"))
    placeholders = mp.get("placeholders", mp)  # accept raw {token: {...}} too
    # token -> original string
    table = {
        tok: (v["text"] if isinstance(v, dict) else v)
        for tok, v in placeholders.items()
    }
    inputs = read_inputs(args)
    if not inputs:
        sys.exit("restore: no input text (pass TEXT, -f FILE, or pipe via stdin)")
    results = []
    for _, text in inputs:
        # Replace longest tokens first so [LBL_1] never clobbers [LBL_10].
        for tok in sorted(table, key=len, reverse=True):
            text = text.replace(tok, table[tok])
        results.append(text)
    emit("\n".join(results), args)


def emit(text: str, args):
    if args.out:
        Path(args.out).write_text(text, encoding="utf-8")
        print(f"wrote {args.out} ({len(text)} chars)", file=sys.stderr)
    else:
        print(text)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("text", nargs="?", help="Inline text to process.")
    p.add_argument("-f", "--file", action="append", help="Input file (repeatable, UTF-8).")
    p.add_argument("--stdin", action="store_true", help="Force read from stdin.")
    p.add_argument("--device", default="auto", choices=("auto", "cpu", "cuda"))
    p.add_argument("--decode", default="viterbi", choices=("viterbi", "argmax"),
                   help="viterbi = coherent spans (default); argmax = faster, noisier.")
    p.add_argument("--label-mode", default="typed", choices=("typed", "redacted"),
                   help="typed keeps <PRIVATE_EMAIL> etc.; redacted collapses to <REDACTED>.")
    p.add_argument("--checkpoint", default=None,
                   help="Checkpoint dir. Default: $OPF_CHECKPOINT or ~/.opf/privacy_filter (auto-download).")
    p.add_argument("--reversible", action="store_true",
                   help="Use unique numbered placeholders and emit a restore map.")
    p.add_argument("--map", default=None,
                   help="Restore-map path: written in --reversible, read in --restore.")
    p.add_argument("--restore", action="store_true",
                   help="Re-identify text using --map (no model load).")
    p.add_argument("--placeholder", default="[{LABEL}_{n}]",
                   help="Reversible token template. Default '[{LABEL}_{n}]'.")
    p.add_argument("--format", default="text", choices=("text", "json"),
                   help="text = redacted text; json = full result with spans.")
    p.add_argument("--out", default=None, help="Write output text to file (UTF-8).")
    args = p.parse_args(argv)

    if args.restore:
        if not args.map:
            sys.exit("--restore requires --map MAP.json")
        return do_restore(args)

    inputs = read_inputs(args)
    if not inputs:
        sys.exit("no input (pass TEXT, -f FILE, or pipe via stdin)")

    redactor = build_redactor(args)
    mapping: dict[str, dict] = {}
    counters: dict[str, int] = {}
    json_docs, text_docs = [], []

    for source, text in inputs:
        result = redactor.redact(text)
        spans = result.detected_spans
        if args.reversible:
            redacted = reversible_redact(text, spans, mapping, counters, args.placeholder)
        else:
            redacted = result.redacted_text
        text_docs.append(redacted)
        json_docs.append({
            "source": source,
            "redacted_text": redacted,
            "detected_spans": [
                {"label": s.label, "start": s.start, "end": s.end, "text": s.text}
                for s in spans
            ],
            "summary": dict(result.summary),
        })

    if args.reversible and args.map:
        Path(args.map).write_text(
            json.dumps({"placeholders": mapping, "by_label": counters},
                       ensure_ascii=False, indent=2),
            encoding="utf-8")
        print(f"wrote restore map {args.map} ({len(mapping)} placeholders)", file=sys.stderr)

    if args.format == "json":
        out = json_docs[0] if len(json_docs) == 1 else {"docs": json_docs}
        if args.reversible:
            out["placeholders"] = mapping
        emit(json.dumps(out, ensure_ascii=False, indent=2), args)
    else:
        emit("\n".join(text_docs), args)


if __name__ == "__main__":
    main()
