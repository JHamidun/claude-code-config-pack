"""Step 1: Analyze RAW SRT cuts via a cheap GPT model.

For each short, produce:
- topic: short topic in Russian (3-5 words)
- gist: 1-sentence summary
- hook_formula: one of [Curiosity Gap, Mistake Callout, Fast Result, Direct Question, Mid-Action, Contradiction, Visual Surprise]
- hook_3s: rewritten first 3 seconds (Russian, hook formula applied)
- title: ≤50 chars curiosity-gap title
- description: 2-3 lines for YT description
- on_screen_text: 3-5 words for big overlay text at hook
- loop_close: rewritten last 2 seconds that loops back to hook
- tags: comma-sep 5 tags
- keep: bool (false if content is too disjointed/incoherent for a short)
- skip_reason: if keep=false, why

Output: $SHORTS_HOME/analysis.json (инкрементально — повторный запуск пропускает
уже проанализированное). Настройки путей и ключей — config.py.
"""
import sys, json, os, time
from pathlib import Path
try: sys.stdout.reconfigure(encoding='utf-8')
except: pass

sys.path.insert(0, str(Path(__file__).parent))
import config

# Ключ и клиент — лениво, при первом вызове. На верхнем уровне ничего не делаем:
# импорт модуля не должен ни требовать ключа, ни строить клиента (см. main()).
_client = None


def get_client():
    """OpenAI-клиент по требованию. Ключ: окружение → .credentials.master.env → внятный отказ."""
    global _client
    if _client is None:
        config.key('OPENAI_API_KEY')
        from openai import OpenAI
        _client = OpenAI()
    return _client


FACTORY = config.SOURCE_DIR
OUT = config.ANALYSIS

SYS_PROMPT = """Ты — viral content strategist для YT Shorts. Получаешь сырой SRT-фрагмент из обучающего вебинара на русском.

Твоя задача — преобразовать его в формат YT Shorts ≤60 сек с учётом «The 30% Rule» (хук в 3 секунды или зритель свайпает).

Hook formulas:
1. Curiosity Gap — «Никто не говорит об этом...»
2. Mistake Callout — «Вы делаете это неправильно»
3. Fast Result — «Этот один приём удвоил...»
4. Direct Question — вопрос с completion bias
5. Mid-Action Open — начать с самой интересной точки
6. Contradiction Hook — «Я отключил X — и стало лучше»
7. Visual Surprise — kpitch break

Loop technique: последняя фраза = первая фраза, чтобы re-watch >100%.

Анализируя SRT, верни СТРОГИЙ JSON (без markdown):
{
  "topic": "тема 3-5 слов",
  "gist": "одно предложение что внутри",
  "keep": true/false,
  "skip_reason": "если keep=false — почему (бессвязно/середина фразы без контекста/etc)",
  "hook_formula": "название формулы",
  "hook_3s": "переписанные первые 3 сек (1-2 фразы, мощный заход)",
  "title": "≤50 символов curiosity-gap",
  "description": "2-3 строки описания для YT",
  "on_screen_text": "3-5 слов крупным шрифтом на hook кадре",
  "loop_close": "финальная фраза 2 сек, замыкающая на hook",
  "tags": "тег1,тег2,тег3,тег4,тег5"
}

Только JSON, никакого markdown."""

def analyze_short(srt_text):
    """Call GPT for one short."""
    r = get_client().chat.completions.create(
        model='gpt-4.1-mini',
        messages=[
            {'role': 'system', 'content': SYS_PROMPT},
            {'role': 'user', 'content': f'SRT субтитры шортса:\n\n{srt_text[:3000]}'},
        ],
        temperature=0.7,
        response_format={'type': 'json_object'},
    )
    return json.loads(r.choices[0].message.content)


def main():
    # Existing analysis
    existing = {}
    if OUT.exists():
        existing = json.load(open(OUT, encoding='utf-8'))

    if not FACTORY.is_dir():
        raise SystemExit('\n'.join([
            f'Нет каталога с нарезкой: {FACTORY}',
            '  Ожидается раскладка <SHORTS_SOURCE>/<video_id>/short_NN.srt (рядом short_NN.mp4).',
            '  Задай путь: export SHORTS_SOURCE=/path/to/cuts (или SHORTS_HOME, см. config.py).',
        ]))

    todo = []
    for d in sorted(x.name for x in FACTORY.iterdir() if x.is_dir()):
        for f in sorted(os.listdir(FACTORY/d)):
            if f.endswith('.srt'):
                key = f'{d}/{f[:-4]}'  # напр. 'AbCdEf12345/short_01'
                if key in existing:
                    continue
                todo.append((key, FACTORY/d/f))

    total = len(existing) + len(todo)
    if not total:
        raise SystemExit(f'В {FACTORY} не найдено ни одного .srt — проверь раскладку каталогов.')
    print(f'Total shorts: {total}, already analyzed: {len(existing)}, todo: {len(todo)}')

    for i, (key, srt_path) in enumerate(todo, 1):
        srt = srt_path.read_text(encoding='utf-8', errors='replace')
        try:
            result = analyze_short(srt)
            result['_key'] = key
            result['_srt_path'] = str(srt_path)
            result['_mp4_path'] = str(srt_path.with_suffix('.mp4'))
            existing[key] = result
            # Save incremental
            OUT.write_text(json.dumps(existing, ensure_ascii=False, indent=2), encoding='utf-8')

            keep = '✓' if result.get('keep') else '✗'
            print(f'  [{i}/{len(todo)}] {keep} {key:<32} | {result.get("topic","")[:30]:<30} | {result.get("title","")[:50]}')
            time.sleep(0.3)
        except Exception as e:
            print(f'  [{i}/{len(todo)}] FAIL {key}: {str(e)[:120]}')
            time.sleep(2)

    # Summary
    keep_n = sum(1 for v in existing.values() if v.get('keep'))
    print()
    print(f'=== DONE: {len(existing)} analyzed, {keep_n} viable, {len(existing)-keep_n} to skip ===')


if __name__ == '__main__':
    main()
