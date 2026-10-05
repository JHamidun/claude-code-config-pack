"""Audit Russian word stress in a voiced story: what the voice actually said vs the correct stress in context.

    python stress_audit.py <story dir> [<story dir> ...]      -> prints suspicious words, writes <dir>/stress_audit.json

Correct stress: RUAccent (context-aware, homographs) on the spoken text. What was said: the phoneme recognizer
(tools/phones.py) — Russian reduces an unstressed «о» to [a]/[ʌ]/[ə], a stressed one stays [o]. So for every word with
«о» (or «ё») we check: stress on «о» → a full [o] must be heard; «о» unstressed → no full [o]. Checked 01.10.2026 on the
«стоит» case the owner heard wrong (story 2: [s t oː j t] = стОит). Words without «о» are not checked by this rule.
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from phones import phones  # noqa: E402

FULL_O = {'o', 'oː', 'ɔ', 'ɔː'}
VOWELS = 'аеёиоуыэюя'
_acc = None


def accentizer():
    global _acc
    if _acc is None:
        from ruaccent import RUAccent
        _acc = RUAccent()
        _acc.load(omograph_model_size='turbo3.1', use_dictionary=True, tiny_mode=False)
    return _acc


def spoken_words(al):
    chars, st, en = al['characters'], al['character_start_times_seconds'], al['character_end_times_seconds']
    out, cur = [], None
    for c, s, e in zip(chars, st, en):
        if c.isspace():
            if cur:
                out.append(cur)
            cur = None
            continue
        if cur is None:
            cur = {'w': c, 's': s, 'e': e}
        else:
            cur['w'] += c
            cur['e'] = e
    if cur:
        out.append(cur)
    return out


def stress_info(token):
    """token with RUAccent '+' before the stressed vowel -> (letters, stressed vowel index or None)."""
    if '́' in token:                      # an explicit mark from the script wins over RUAccent
        clean = token.replace('+', '')
        i = clean.index('́')
        return clean.replace('́', ''), i - 1
    letters, idx = '', None
    plus = False
    for ch in token:
        if ch == '+':
            plus = True
            continue
        if ch.lower() in VOWELS + 'abcdefghijklmnopqrstuvwxyz' or ch.isalpha():
            if plus and ch.lower() in VOWELS:
                idx = len(letters)
            plus = False
            letters += ch
        else:
            letters += ch
    return letters, idx


STRONG_O = {'oː', 'ɔː'}
LOOSE_O = FULL_O | {'oɪ', 'oʊ'}


def audit_take(mp3, al):
    """-> (score, flags). Strong evidence only: a LONG [oː] on an unstressed «о» (stress moved, the стОит case) counts 1;
    no [o]-like sound at all in a word whose stress is on «о» (window widened by 0.12 s) counts 0.5."""
    spoken = ''.join(al['characters'])
    words = spoken_words(al)
    marks = [w['w'] for w in words]
    acc = accentizer().process_all(spoken.replace('́', ''))
    toks = acc.split()
    if len(toks) != len(words):
        toks = [accentizer().process_all(w.replace('́', '')) for w in marks]
    toks = [m if '́' in m else t for m, t in zip(marks, toks)]
    ph = phones(str(mp3), with_times=True)
    flags, score = [], 0.0
    for w, tok in zip(words, toks):
        letters, si = stress_info(tok)
        low = letters.lower()
        if sum(1 for c in low if c in VOWELS) < 2 or not any(c in 'оё' for c in low) or si is None:
            continue
        stressed_o = low[si] in 'оё'
        near = [p for p, t in ph if w['s'] - 0.03 <= t <= w['e'] + 0.03]
        wide = [p for p, t in ph if w['s'] - 0.12 <= t <= w['e'] + 0.12]
        if not stressed_o and any(p in STRONG_O for p in near):
            flags.append({'word': w['w'], 'heard': ' '.join(near), 'why': 'долгое [oː] на безударном «о»'}); score += 1
        elif stressed_o and not any(p in LOOSE_O for p in wide):
            flags.append({'word': w['w'], 'heard': ' '.join(wide), 'why': 'не слышно ударного «о»'}); score += 0.5
    return score, flags


def audit(d):
    d = Path(d)
    meta = json.loads((d / 'alignment.json').read_text(encoding='utf-8'))
    al = meta['alignment']
    spoken = ''.join(al['characters'])
    words = spoken_words(al)
    acc = accentizer().process_all(spoken.replace('́', ''))
    toks = acc.split()
    if len(toks) != len(words):
        print(f'  ! token mismatch {len(toks)} vs {len(words)} — falling back to word-by-word accenting')
        toks = [accentizer().process_all(w['w'].replace('́', '')) for w in words]
    ph = phones(str(d / 'voice.mp3'), with_times=True)
    flags = []
    for w, tok in zip(words, toks):
        letters, si = stress_info(tok)
        low = letters.lower()
        nv = sum(1 for c in low if c in VOWELS)
        if nv < 2 or not any(c in 'оё' for c in low):
            continue
        heard = [p for p, t in ph if w['s'] - 0.03 <= t <= w['e'] + 0.03]
        has_full_o = any(p in FULL_O for p in heard)
        stressed_o = si is not None and low[si] in 'оё'
        if stressed_o and not has_full_o:
            flags.append({'word': w['w'], 'correct': tok, 'heard': ' '.join(heard), 'problem': 'ударное «о» не прозвучало', 's': round(w['s'], 2)})
        elif not stressed_o and si is not None and has_full_o:
            flags.append({'word': w['w'], 'correct': tok, 'heard': ' '.join(heard), 'problem': 'безударное «о» прозвучало полным — похоже на сдвиг ударения', 's': round(w['s'], 2)})
    (d / 'stress_audit.json').write_text(json.dumps({'accented': acc, 'flags': flags}, ensure_ascii=False, indent=1), encoding='utf-8')
    return acc, flags


if __name__ == '__main__':
    for arg in sys.argv[1:]:
        acc, flags = audit(arg)
        print(f'== {Path(arg).name}: подозрительных слов {len(flags)}')
        for f in flags:
            print(f"  {f['s']:6.2f}  {f['word']:<16} правильно: {f['correct']:<18} слышно: {f['heard']:<24} {f['problem']}")
