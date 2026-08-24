"""Trigger-word scanner: scan Russian script BEFORE sending to HeyGen TTS.

WHY: HeyGen TTS русским голосом mistranscribes/mispronounces английские термины:
  - 'pivot'  →  слышится как 'пиво' (beer) → SubMagic ставит 🍺 emoji
  - 'roadmap' →  'road-мап' (англицизм неприятный на слух)
  - 'pipeline' →  путаница "пайплайн" vs "пипелайн"
  - 'feature' → 'фичер' vs 'фи-чур'

КРИТИЧНО: dictionary SubMagic с `["pivot","пайвот"]` НЕ ИСПРАВЛЯЕТ TTS.
Dictionary помогает только распознать новые слова в РЕАЛЬНОМ audio — не в TTS-сгенерированном.

Решение: заменить trigger-слова в скрипте ДО TTS, прямо в исходном тексте.

Usage:
    python trigger_word_check.py script.txt          # scan only, exit 1 if found
    python trigger_word_check.py script.txt --fix    # auto-replace + write *.clean.txt
    python trigger_word_check.py - --fix             # stdin → stdout
    echo "pivot к новой модели" | python trigger_word_check.py - --fix
"""
import sys, re, argparse
from pathlib import Path
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

# (word, replacement, reason)
# Order matters: longer phrases first so they match before shorter ones.
TRIGGERS = [
    # The big one — «пиво» bug
    ('pivot', 'разворот концепции', 'TTS слышит как «пиво» → 🍺 emoji в SubMagic'),
    ('пайвот', 'разворот концепции', 'неестественный англицизм'),
    # Other risky English/anglicisms
    ('roadmap', 'дорожная карта', 'TTS читает по буквам "р-о-а-д-м-ап"'),
    ('pipeline', 'пайплайн', 'нормализуем написание (избегаем «пипелайн»)'),
    ('feature', 'фича', 'единообразие'),
    ('launch', 'запуск', 'TTS читает как «лаунч»'),
    ('mindset', 'образ мышления', 'неестественный англицизм'),
    ('insight', 'инсайт', 'нормализуем написание'),
    ('benchmark', 'эталон', 'не все TTS-голоса знают это слово'),
    ('throughput', 'пропускная способность', 'нет в русском словаре TTS'),
    ('latency', 'задержка', 'TTS читает по буквам'),
    ('fine-tuning', 'дообучение', 'смесь английского и русского ломает TTS'),
    ('fine tuning', 'дообучение', 'смесь английского и русского'),
    # Brand names that get mangled
    ('CustDev', 'кастдев', 'TTS читает побуквенно "С-Ц-У-С-Т-Д-Е-В"'),
    ('PMF', 'product-market fit', 'три буквы — TTS их добивает побуквенно'),
    ('ROI', 'РОИ', 'аббревиатура — лучше расшифровать'),
    ('ICP', 'идеальный клиент', 'три буквы плохо звучат'),
]

# Compiled patterns (case-insensitive, word boundary)
COMPILED = [(re.compile(r'\b' + re.escape(t) + r'\b', re.IGNORECASE), r, why)
            for t, r, why in TRIGGERS]


def scan(text):
    """Return list of (line_no, match_text, replacement, reason)."""
    findings = []
    for i, line in enumerate(text.splitlines(), 1):
        for pat, repl, reason in COMPILED:
            for m in pat.finditer(line):
                findings.append((i, m.group(0), repl, reason))
    return findings


def fix(text):
    """Return cleaned text with all triggers replaced."""
    for pat, repl, _ in COMPILED:
        text = pat.sub(repl, text)
    return text


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('path', help='Script file path or "-" for stdin')
    ap.add_argument('--fix', action='store_true', help='Auto-replace, write *.clean.txt (or stdout for stdin)')
    ap.add_argument('--list', action='store_true', help='List all trigger words and exit')
    args = ap.parse_args()

    if args.list:
        print('Trigger-word list:')
        for t, r, why in TRIGGERS:
            print(f'  "{t}" → "{r}"\n    reason: {why}')
        return

    if args.path == '-':
        text = sys.stdin.read()
    else:
        text = Path(args.path).read_text(encoding='utf-8')

    findings = scan(text)

    if not findings:
        print('OK: no trigger words found.', file=sys.stderr)
        if args.fix and args.path == '-':
            sys.stdout.write(text)
        return 0

    print(f'FOUND {len(findings)} trigger(s):', file=sys.stderr)
    for line_no, match, repl, reason in findings:
        print(f'  L{line_no}: "{match}" → "{repl}"  ({reason})', file=sys.stderr)

    if args.fix:
        cleaned = fix(text)
        if args.path == '-':
            sys.stdout.write(cleaned)
        else:
            out = Path(args.path).with_suffix('.clean.txt')
            out.write_text(cleaned, encoding='utf-8')
            print(f'\nWrote: {out}', file=sys.stderr)
        return 0

    # No --fix: exit 1 (so CI/pipeline can block)
    return 1


if __name__ == '__main__':
    sys.exit(main() or 0)
