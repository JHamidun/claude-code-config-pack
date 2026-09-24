"""Optional local ASR adapter. Explicit existing model; no automatic downloads."""
import argparse
from pathlib import Path
from common import writable, write_json, stop_check


def stamp(value):
    ms = round(value * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def main():
    p = argparse.ArgumentParser()
    p.add_argument('audio'); p.add_argument('--model-dir', required=True); p.add_argument('--output-dir', required=True)
    p.add_argument('--language', default='ru'); p.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    p.add_argument('--compute-type', default='int8'); p.add_argument('--start', action='store_true')
    a = p.parse_args(); source = Path(a.audio).resolve(); model = Path(a.model_dir).resolve(); out = writable(a.output_dir)
    if not source.is_file() or not (model / 'model.bin').is_file():
        raise ValueError('Supply an existing media file and local CTranslate2 model directory')
    if out in source.parents or out == model or model in out.parents:
        raise ValueError('ASR output needs a separate directory from media/model sources')
    if not a.start:
        print('Plan: local transcription to draft.srt and draft-words.json. Review all timings/text before use.'); return
    from faster_whisper import WhisperModel
    stop_check(out.parent)
    engine = WhisperModel(str(model), device=a.device, compute_type=a.compute_type, cpu_threads=2, num_workers=1, local_files_only=True)
    segments, info = engine.transcribe(str(source), language=a.language, word_timestamps=True, vad_filter=True, beam_size=5)
    words, rows = [], []
    for i, s in enumerate(segments, 1):
        stop_check(out.parent)
        rows.append(f'{i}\n{stamp(s.start)} --> {stamp(s.end)}\n{s.text.strip()}\n')
        words.extend({'start': w.start, 'end': w.end, 'word': w.word.strip(), 'probability': w.probability} for w in s.words or [])
    out.mkdir(parents=True, exist_ok=True)
    (out / 'draft.srt').write_text('\n'.join(rows), encoding='utf-8-sig')
    write_json(out / 'draft-words.json', {'language': info.language, 'reviewed': False, 'words': words})
    print(out)


if __name__ == '__main__':
    main()
