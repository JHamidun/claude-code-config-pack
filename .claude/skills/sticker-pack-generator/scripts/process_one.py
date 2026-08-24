"""Process single MP4 → 512x512 VP9-alpha WebM sticker (≤256KB).

Pipeline: rembg+chromakey seed (frame 0) → SAM2 propagate → per-frame chromakey UNION
        → RGBA PNG → yuva420p → alpha_encoder → WebM.

Кодировщик VP9-alpha: на Windows он живёт внутри WSL (родной сборки под Windows нет),
на macOS и Linux это обычный бинарь в PATH — прослойка WSL там не нужна и её нет.

Usage:
    python process_one.py --mp4 input.mp4 --out output.webm
    python process_one.py --mp4 input.mp4 --out output.webm --no-chromakey  # disable per-frame ck
    python process_one.py --mp4 input.mp4 --out output.webm --ck-threshold 200
"""
import sys, io, os, subprocess, tempfile, shutil, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', line_buffering=True)

from _config import (sam2_checkpoint as _sam2_ckpt, sam2_config as _sam2_cfg,
                     wsl_distro, alpha_encoder_path, to_wsl_path)

DEFAULT_CHECKPOINT = _sam2_ckpt()
DEFAULT_CONFIG = _sam2_cfg()

IS_WINDOWS = sys.platform == 'win32'

# --------------------------------------------------------------------------- #
# Тяжёлые зависимости
# --------------------------------------------------------------------------- #
# Раньше `from sam2.build_sam import …` стоял на верхнем уровне модуля. Человек,
# поставивший всё строго по requirements.txt, получал голый
# `ModuleNotFoundError: No module named 'sam2'` — и шёл в pip, где sam2 нет вовсе
# (requirements-optional.txt честно помечает его «no installable PyPI distribution»).
# Ошибка не называла ни причину, ни то, что делать. Заодно из-за импорта на верхнем
# уровне не работал даже `--help`: узнать аргументы скрипта было нельзя.
#
# Теперь импорт отложен до реальной работы, а отказ называет пакет, причину и команду.
_INSTALL_HINTS = {
    'sam2': ('на PyPI его НЕТ — только из git:\n'
             '       pip install "git+https://github.com/facebookresearch/sam2.git"\n'
             '       (нужен torch ≥2.3; веса .pt — по инструкции в SKILL.md)'),
    'torch': ('pip install torch  — сборку под свою CUDA брать на pytorch.org/get-started;\n'
              '       строка есть в requirements-optional.txt'),
    'cv2': 'pip install opencv-python   (строка есть в requirements-optional.txt)',
    'rembg': 'pip install rembg         (строка есть в requirements-optional.txt)',
    'numpy': 'pip install numpy         (строка есть в requirements.txt)',
    'PIL': 'pip install pillow          (строка есть в requirements.txt)',
    'cuda_init': 'файл лежит рядом со скриптом — запускай из каталога scripts/',
}

_DEPS_LOADED = False


def _load_deps():
    """Импортировать тяжёлый стек или отказать по-человечески.

    Ставит в globals: np, Image, cv2, torch, build_sam2_video_predictor, remove, new_session.
    """
    global _DEPS_LOADED, np, Image, cv2, torch
    global build_sam2_video_predictor, remove, new_session
    if _DEPS_LOADED:
        return
    import importlib
    missing = []

    def _imp(module, attr=None):
        root = module.split('.')[0]
        try:
            m = importlib.import_module(module)
        except ImportError as exc:
            missing.append((root, _INSTALL_HINTS.get(root, f'pip install {root}'), str(exc)))
            return None
        except Exception as exc:  # noqa: BLE001
            # Пакет установлен, но его собственная цепочка зависимостей несовместима
            # (реальный случай: sam2 → hydra → omegaconf → antlr4 несовпадающей версии,
            # «Could not deserialize ATN with version 3 (expected 4)»). Такое НЕ ловится
            # как ImportError, и раньше вылезало сорокастрочным чужим трейсбеком, из
            # которого не видно ни виновника, ни того, что делать.
            missing.append((root,
                            f'пакет установлен, но ломается при импорте — конфликт версий '
                            f'внутри его зависимостей.\n'
                            f'       Лечится переустановкой ветки: pip install --force-reinstall {root}\n'
                            f'       (частый виновник у sam2 — antlr4-python3-runtime; версию '
                            f'диктует omegaconf)',
                            f'{type(exc).__name__}: {exc}'))
            return None
        try:
            return getattr(m, attr) if attr else m
        except AttributeError as exc:
            missing.append((root, _INSTALL_HINTS.get(root, f'pip install -U {root}'),
                            f'в установленной версии нет {attr}: {exc}'))
            return None

    _imp('cuda_init')  # noqa: F841 — сайд-эффект: настройка CUDA, должен идти первым
    np = _imp('numpy')
    Image = _imp('PIL.Image')
    cv2 = _imp('cv2')
    torch = _imp('torch')
    build_sam2_video_predictor = _imp('sam2.build_sam', 'build_sam2_video_predictor')
    remove = _imp('rembg', 'remove')
    new_session = _imp('rembg', 'new_session')

    if missing:
        lines = ['[sticker-pack-generator] не хватает зависимостей:']
        for name, hint, exc in missing:
            lines.append(f'  • {name}: {exc}')
            lines.append(f'       {hint}')
        lines.append('  Полный список и порядок установки — SKILL.md этого навыка.')
        raise SystemExit('\n'.join(lines))
    _DEPS_LOADED = True


# --------------------------------------------------------------------------- #
# VP9-alpha кодировщик: WSL только на Windows
# --------------------------------------------------------------------------- #
def to_wsl(p):
    p = p.replace('\\', '/')
    if len(p) > 1 and p[1] == ':':
        return f'/mnt/{p[0].lower()}{p[2:]}'
    return p


def check_alpha_encoder():
    """(ok, сообщение) — есть ли чем закодировать VP9-alpha.

    Проверять ДО работы: SAM2 по всем кадрам идёт минутами, и упереться в
    отсутствующий кодировщик на последнем шаге — значит выбросить всю эту работу.
    Раньше именно так и было: на macOS/Linux вызывался `wsl`, которого там нет,
    и провал приходил после полного прогона сегментации.
    """
    enc = alpha_encoder_path()
    if IS_WINDOWS:
        if shutil.which('wsl') is None:
            return False, ('VP9-alpha кодируется через WSL, а `wsl` не найден в PATH.\n'
                           '  Установка: wsl --install -d Ubuntu-22.04 (нужен перезапуск),\n'
                           '  затем собрать alpha_encoder внутри дистрибутива — см. SKILL.md.')
        return True, f'wsl -d {wsl_distro()} → {enc}'
    # macOS / Linux: alpha_encoder — родной бинарь, прослойка не нужна.
    resolved = shutil.which(enc) or (enc if os.path.exists(enc) else None)
    if resolved is None:
        return False, (f'не найден бинарь alpha_encoder: {enc}\n'
                       '  На macOS/Linux он запускается напрямую, без WSL.\n'
                       '  Путь переопределяется переменной ALPHA_ENCODER_PATH.\n'
                       '  Сборка — см. SKILL.md этого навыка.')
    return True, resolved


def encode_alpha_webm(yuva, out, size):
    """yuva420p → VP9-alpha WebM. Windows — через WSL, остальные ОС — напрямую."""
    ok, info = check_alpha_encoder()
    if not ok:
        raise SystemExit(f'[sticker-pack-generator] {info}')
    if IS_WINDOWS:
        subprocess.run(['wsl', '-d', wsl_distro(), '-u', 'root', 'bash', '-c',
                        f'cd /tmp && wd=$(mktemp -d) && cd $wd && '
                        f'{alpha_encoder_path()} '
                        f'-w {size} -h {size} -i {to_wsl(yuva)} -o {to_wsl(out)} '
                        f'-c vp9 > /dev/null 2>&1'], check=True)
    else:
        subprocess.run([info, '-w', str(size), '-h', str(size),
                        '-i', yuva, '-o', out, '-c', 'vp9'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def chromakey_inv_white(rgb, t=215):
    """Returns uint8 0/255 mask. 255 = non-white (foreground)."""
    return ((rgb.min(axis=-1) < t).astype(np.uint8) * 255)


def process(mp4, out, ck_threshold=215, per_frame_chromakey=True,
            duration=3, fps=30, size=512,
            rembg_model='isnet-general-use',
            sam2_config=DEFAULT_CONFIG, sam2_checkpoint=DEFAULT_CHECKPOINT,
            work_parent=None):
    _load_deps()
    # Preflight: упереться в отсутствующий кодировщик ПОСЛЕ прогона SAM2 по всем
    # кадрам — значит выбросить минуты работы. Проверяем до первого кадра.
    ok, info = check_alpha_encoder()
    if not ok:
        raise SystemExit(f'[sticker-pack-generator] {info}')
    print(f'alpha_encoder: {info}')
    work = tempfile.mkdtemp(prefix='spg_', dir=work_parent or os.path.dirname(out))
    print(f'work: {work}')
    try:
        raw_dir = f'{work}/raw'; os.makedirs(raw_dir)
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', mp4,
                        '-t', str(duration),
                        '-vf', f"crop='min(iw,ih)':'min(iw,ih)',scale={size}:{size},fps={fps}",
                        '-qmin', '1', '-q:v', '1',
                        f'{raw_dir}/%05d.jpg'], check=True)
        files = sorted(os.listdir(raw_dir))
        print(f'frames: {len(files)}')

        # Seed: rembg ∪ chromakey on frame 0
        rgb0 = np.array(Image.open(f'{raw_dir}/{files[0]}').convert('RGB'))
        sess = new_session(rembg_model,
                           providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        with open(f'{raw_dir}/{files[0]}', 'rb') as f:
            rem0 = np.array(Image.open(io.BytesIO(remove(f.read(), session=sess))).convert('RGBA'))
        rembg_mask = (rem0[..., 3] > 128).astype(np.uint8) * 255
        ck0 = chromakey_inv_white(rgb0, t=ck_threshold)
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        seed = cv2.morphologyEx(np.maximum(rembg_mask, ck0), cv2.MORPH_CLOSE, kernel)
        seed_bool = (seed > 0).astype(np.uint8)
        print(f'seed coverage: {seed_bool.sum()} px')

        # SAM2 propagate
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        predictor = build_sam2_video_predictor(sam2_config, sam2_checkpoint, device=device)
        with torch.inference_mode(), torch.autocast(device.type, dtype=torch.bfloat16):
            state = predictor.init_state(video_path=raw_dir)
            predictor.add_new_mask(inference_state=state, frame_idx=0, obj_id=1,
                                   mask=torch.from_numpy(seed_bool).to(device))
            sam2_masks = {}
            for fi, _, ml in predictor.propagate_in_video(state):
                sam2_masks[fi] = (ml[0] > 0.0).cpu().numpy().squeeze(0)

        # Compose RGBA frames
        smooth = f'{work}/smooth'; os.makedirs(smooth)
        for i, fn in enumerate(files):
            rgb = np.array(Image.open(f'{raw_dir}/{fn}').convert('RGB'))
            sam_m = sam2_masks.get(i, np.zeros((size, size), dtype=bool)).astype(np.uint8) * 255
            if per_frame_chromakey:
                ck_m = chromakey_inv_white(rgb, t=ck_threshold)
                union = np.maximum(sam_m, ck_m)
            else:
                union = sam_m
            closed = cv2.morphologyEx(union, cv2.MORPH_CLOSE, kernel)
            a = closed.astype(np.int16)
            a = np.where(a < 60, 0, a)
            a = np.where(a > 180, 255, a).astype(np.uint8)
            Image.fromarray(np.dstack([rgb, a]), 'RGBA').save(f'{smooth}/{i+1:05d}.png')

        # Raw yuva420p
        yuva = f'{work}/raw.yuva'
        subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps),
                        '-i', f'{smooth}/%05d.png', '-pix_fmt', 'yuva420p',
                        '-f', 'rawvideo', yuva], check=True)

        # alpha_encoder (Windows → WSL, macOS/Linux → напрямую)
        encode_alpha_webm(yuva, out, size)
        sz = os.path.getsize(out)
        print(f'OUT: {out} ({sz}b)')
        if sz > 256_000:
            print(f'WARNING: file >{256_000}b, Telegram may reject')
        return out
    finally:
        shutil.rmtree(work, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--mp4', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--ck-threshold', type=int, default=215)
    ap.add_argument('--no-chromakey', action='store_true',
                    help='disable per-frame chromakey UNION (SAM2 alone)')
    ap.add_argument('--rembg-model', default='isnet-general-use')
    ap.add_argument('--checkpoint', default=DEFAULT_CHECKPOINT)
    ap.add_argument('--config', default=DEFAULT_CONFIG)
    args = ap.parse_args()
    process(args.mp4, args.out,
            ck_threshold=args.ck_threshold,
            per_frame_chromakey=not args.no_chromakey,
            rembg_model=args.rembg_model,
            sam2_config=args.config, sam2_checkpoint=args.checkpoint)


if __name__ == '__main__':
    main()
