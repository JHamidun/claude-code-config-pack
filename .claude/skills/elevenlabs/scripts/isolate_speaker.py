#!/usr/bin/env python3
"""Оставить в записи только основного говорящего.

В записи вебинара кроме ведущего звучат вопросы участников, реплики помощника,
иногда рекламная вставка. Для клонирования голоса это яд: модель усредняет всё, что
слышит, и клон получается ни на кого не похожим. Резать вручную двухчасовую запись
невозможно, а на слух чужую реплику в середине никто не заметит.

Как отделяется. Голос человека узнаётся по спектральной окраске — она устойчива в
пределах записи и заметно различается между людьми. Запись режется на короткие окна,
для каждого считаются мел-кепстральные коэффициенты, окна группируются по сходству.
Ведущий вебинара говорит больше всех, поэтому самая крупная группа — он.

Метод не требует ни отдельной модели, ни видеокарты, ни токена: только спектральный
анализ. Он не различит двух похожих мужских голосов так же уверенно, как специальная
модель, поэтому результат обязательно слушают — скрипт сам готовит выборку для этого.

    python isolate_speaker.py webinar.mp4 -o only_host.mp3
    python isolate_speaker.py webinar.mp4 -o only_host.mp3 --speakers 3 --check check/
"""
from __future__ import annotations

import argparse
import pathlib
import subprocess
import sys
import tempfile


def decode(src: pathlib.Path, rate: int = 16000):
    """Аудио в массив отсчётов. Видео и любые контейнеры — через ffmpeg."""
    import numpy as np
    with tempfile.TemporaryDirectory() as td:
        wav = pathlib.Path(td) / "a.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
                        "-ac", "1", "-ar", str(rate), str(wav)], check=True)
        import soundfile as sf
        data, sr = sf.read(str(wav), dtype="float32")
    return np.asarray(data), sr


def features(y, sr: int, win: float, hop: float):
    """Признаки голоса по окнам.

    Кроме кепстральных коэффициентов берётся их разброс внутри окна: у говорящего
    он устойчив, а на стыке двух голосов подскакивает — это помогает не склеивать
    соседние реплики разных людей в одно окно.
    """
    import librosa
    import numpy as np

    n_win, n_hop = int(win * sr), int(hop * sr)
    starts = range(0, max(len(y) - n_win, 1), n_hop)
    feats, times = [], []
    for s in starts:
        chunk = y[s:s + n_win]
        if len(chunk) < n_win // 2:
            continue
        # Тишину пропускаем: у неё нет окраски, и она стянет к себе отдельный кластер.
        rms = float(np.sqrt(np.mean(chunk ** 2)))
        if rms < 0.004:
            continue
        m = librosa.feature.mfcc(y=chunk, sr=sr, n_mfcc=20)
        feats.append(np.concatenate([m.mean(axis=1), m.std(axis=1)]))
        times.append(s / sr)
    return np.array(feats), np.array(times)


def cluster(feats, n_max: int, min_quality: float = 0.22):
    """Разделить окна по говорящим, определив их число самостоятельно.

    Заданное число кластеров — ловушка: метод честно поделит на столько частей,
    сколько попросили, даже если человек в записи один. Тогда речь одного голоса
    рвётся надвое по громкости или интонации, и половина материала выбрасывается
    как «чужая». Так и произошло на первой же записи: из 96 минут монолога
    отброшено 48, и обе половины оказались одним и тем же человеком.

    Поэтому число говорящих подбирается по качеству разделения. Силуэтный
    коэффициент показывает, насколько кластеры действительно обособлены: у разных
    людей граница чёткая, у одного человека — размытая. Ниже порога считаем, что
    голос один, и берём запись целиком.
    """
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    x = StandardScaler().fit_transform(feats)
    # Силуэт на десятках тысяч окон считается долго; выборки хватает для оценки.
    idx = np.random.RandomState(0).permutation(len(x))[:4000]

    best = (None, -1.0, 1)
    for n in range(2, n_max + 1):
        labels = KMeans(n_clusters=n, n_init=10, random_state=0).fit_predict(x)
        try:
            q = silhouette_score(x[idx], labels[idx])
        except ValueError:
            continue
        print(f"    разделение на {n}: качество {q:.3f}"
              f"{'  ← слабое, похоже на один голос' if q < min_quality else ''}")
        if q > best[1]:
            best = (labels, q, n)

    if best[0] is None or best[1] < min_quality:
        print(f"  разделение неубедительное — считаю, что говорящий один, беру всё")
        return np.zeros(len(x), dtype=int), 1
    return best[0], best[2]


def merge(times, labels, target: int, win: float, gap: float = 0.6):
    """Слить соседние окна одного говорящего в непрерывные отрезки."""
    segs = []
    cur = None
    for t, l in zip(times, labels):
        if l != target:
            continue
        if cur and t - cur[1] <= gap:
            cur[1] = t + win
        else:
            if cur:
                segs.append(cur)
            cur = [t, t + win]
    if cur:
        segs.append(cur)
    return segs


def cut(src: pathlib.Path, segs, out: pathlib.Path, pad: float = 0.12) -> None:
    """Вырезать отрезки и склеить. Отбор идёт одним фильтром, без временных файлов."""
    parts = []
    for i, (a, b) in enumerate(segs):
        a = max(0.0, a - pad)
        # Фейд по краям каждого отрезка: склейка десятков кусков без него
        # превращается в дорожку из щелчков (приём из video-use).
        dur = (b + pad) - a
        parts.append(
            f"[0:a]atrim=start={a:.3f}:end={b + pad:.3f},asetpts=PTS-STARTPTS,"
            f"afade=t=in:st=0:d=0.03,"
            f"afade=t=out:st={max(dur - 0.03, 0):.3f}:d=0.03[s{i}]")
    graph = ";".join(parts) + ";" + "".join(f"[s{i}]" for i in range(len(segs))) \
            + f"concat=n={len(segs)}:v=0:a=1[out]"
    # Ограничитель на выходе. Сам сигнал не перегружен, но при сжатии в mp3 между
    # отсчётами возникают выбросы выше нуля, и следующий инструмент видит «перегруз»
    # там, где его нет. Дешевле подрезать здесь, чем разбираться потом.
    graph += ";[out]alimiter=limit=0.92:level=disabled[lim]"
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src),
                    "-filter_complex", graph, "-map", "[lim]",
                    "-ac", "1", "-ar", "44100", "-b:a", "192k", str(out)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("-o", "--out", required=True)
    ap.add_argument("--speakers", type=int, default=4,
                    help="верхняя граница числа голосов; точное число подбирается само")
    ap.add_argument("--window", type=float, default=1.5, help="длина окна, с")
    ap.add_argument("--min-seg", type=float, default=1.2,
                    help="отрезки короче отбрасываются: обрывки слов портят датасет")
    ap.add_argument("--check", help="папка для выборок каждого голоса — послушать")
    a = ap.parse_args()

    src = pathlib.Path(a.source)
    if not src.exists():
        raise SystemExit(f"нет файла: {src}")

    print(f"  читаю {src.name}…")
    y, sr = decode(src)
    print(f"  длительность: {len(y) / sr / 60:.1f} мин")

    feats, times = features(y, sr, a.window, a.window / 2)
    if len(feats) < 40:
        raise SystemExit("слишком мало речи для разделения голосов")
    print(f"  окон с речью: {len(feats)}")

    labels, n_found = cluster(feats, a.speakers)
    import numpy as np
    sizes = [(int(np.sum(labels == i)), i) for i in range(n_found)]
    sizes.sort(reverse=True)
    for n, i in sizes:
        print(f"    голос {i}: {n} окон ({n * 100 // len(labels)}% речи)")
    main_speaker = sizes[0][1]

    # Выборки по каждому голосу: разделение проверяется на слух, а не на веру —
    # спектральный метод может свести два похожих голоса в один кластер.
    if a.check:
        chk = pathlib.Path(a.check)
        chk.mkdir(parents=True, exist_ok=True)
        for _, i in sizes:
            segs = [s for s in merge(times, labels, i, a.window)
                    if s[1] - s[0] >= a.min_seg][:8]
            if segs:
                cut(src, segs, chk / f"voice_{i}.mp3")
        print(f"  выборки голосов: {chk}  ← послушать, какой из них нужный")

    if n_found == 1:
        print("  голос один — запись берётся целиком, вырезать нечего")
    segs = [s for s in merge(times, labels, main_speaker, a.window)
            if s[1] - s[0] >= a.min_seg]
    kept = sum(b - a_ for a_, b in segs)
    print(f"  отрезков основного голоса: {len(segs)}, суммарно {kept / 60:.1f} мин "
          f"({kept / (len(y) / sr) * 100:.0f}% записи)")

    cut(src, segs, pathlib.Path(a.out))
    print(f"  только основной голос: {a.out}")
    print("  проверь выборки на слух перед тем, как отдавать в обучение")
    return 0


if __name__ == "__main__":
    sys.exit(main())
