"""Phoneme recognizer (facebook/wav2vec2-xlsr-53-espeak-cv-ft) — hears vowel reduction, so it shows Russian stress:
a stressed «о» stays [o], an unstressed one reduces to [a]/[ʌ]/[ə]. Used to audit TTS stress (01.10.2026).
    from phones import phones; phones('voice.mp3', 4.6, 6.4)
"""
import json
import librosa
import torch
from huggingface_hub import hf_hub_download
from transformers import Wav2Vec2FeatureExtractor, Wav2Vec2ForCTC

M = 'facebook/wav2vec2-xlsr-53-espeak-cv-ft'
_model = _fe = _inv = None


def _load():
    global _model, _fe, _inv
    if _model is None:
        _model = Wav2Vec2ForCTC.from_pretrained(M).to('cuda' if torch.cuda.is_available() else 'cpu').eval()
        _fe = Wav2Vec2FeatureExtractor.from_pretrained(M)
        _inv = {v: k for k, v in json.load(open(hf_hub_download(M, 'vocab.json'), encoding='utf-8')).items()}


def phones(path, t0=None, t1=None, with_times=False):
    _load()
    y, sr = librosa.load(path, sr=16000, mono=True)
    off = 0.0
    if t0 is not None:
        a, b = int(max(0, t0) * sr), int(t1 * sr)
        y, off = y[a:b], max(0, t0)
    x = _fe(y, sampling_rate=16000, return_tensors='pt').input_values.to(_model.device)
    with torch.no_grad():
        ids = _model(x).logits.argmax(-1)[0].cpu().numpy()
    out, prev = [], None
    for k, i in enumerate(ids):
        tok = _inv.get(int(i))
        if i != prev and tok not in ('<pad>', '<s>', '</s>', '<unk>', '|', None):
            out.append((tok, round(off + k * 0.02, 2)))
        prev = i
    return out if with_times else ' '.join(t for t, _ in out)
