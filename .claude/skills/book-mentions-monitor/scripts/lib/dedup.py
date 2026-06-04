# -*- coding: utf-8 -*-
"""Разметка оригинал/перепечатка по сходству текста (лемма-шинглы + Jaccard).
Аналог «Без перепечаток» / «Оригиналы и перепечатки» Медиалогии."""
import re

try:
    from lib.keyword_analyzer_ru import tokens as _tokens
except Exception:
    def _tokens(t): return re.findall(r"[а-яёa-z]+", (t or "").lower())
try:
    from lib.content_scrubber import scrub as _scrub
except Exception:
    def _scrub(t): return re.sub(r"\s+", " ", t or "").strip()


def _shingles(text, k=3):
    toks = [t for t in _tokens(_scrub(text)) if len(t) > 2]
    if len(toks) < k:
        return set(toks)
    return {" ".join(toks[i:i + k]) for i in range(len(toks) - k + 1)}


def _jaccard(a, b):
    if not a or not b:
        return 0.0
    inter = len(a & b)
    return inter / len(a | b)


def mark_reprints(mentions, threshold=0.55):
    """Группирует похожие тексты; в каждой группе оставляет оригинал (ранний/охватный),
    остальным ставит _reprint_of = url оригинала. Возвращает (mentions, n_orig, n_reprint)."""
    sh = [(_shingles(m.get("title", "") + " " + m.get("snippet", "")), m) for m in mentions]
    n = len(sh)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x

    for i in range(n):
        for j in range(i + 1, n):
            if _jaccard(sh[i][0], sh[j][0]) >= threshold:
                parent[find(i)] = find(j)

    groups = {}
    for i in range(n):
        groups.setdefault(find(i), []).append(i)

    n_orig = n_reprint = 0
    for idxs in groups.values():
        # оригинал = самый ранний по дате; при равенстве — макс. охват
        def keyf(i):
            m = sh[i][1]
            return (m.get("date", "9999"), -(m.get("_reach") or 0))
        idxs_sorted = sorted(idxs, key=keyf)
        orig_i = idxs_sorted[0]
        sh[orig_i][1]["_reprint_of"] = None
        n_orig += 1
        for i in idxs_sorted[1:]:
            sh[i][1]["_reprint_of"] = sh[orig_i][1].get("url", "")
            n_reprint += 1
    return mentions, n_orig, n_reprint
