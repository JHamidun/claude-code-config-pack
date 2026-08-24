"""SubMagic-этап отдельным запуском: готовое видео по URL → субтитры + зумы → mp4.

В конвейере этот шаг делает full_pipeline.py. Отдельно скрипт полезен, когда ролик
уже есть (снятый, смонтированный, из HeyGen) и нужно только прогнать его через SubMagic.

    python submagic_process.py <video_url> --title "Название" --out final.mp4
    python submagic_process.py <video_url>            # выход: $SHORTS_HOME/out/<project_id>.mp4

Раньше здесь были зашиты чужое название проекта и один и тот же путь выхода — второй
запуск затирал первый, а в SubMagic уезжало название от прошлого ролика. Теперь и то,
и другое — аргументы.

Ключ: SUBMAGIC_API_KEY (платный план submagic.co). Берётся через config.key().
"""
import sys, time, json, argparse
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).parent))
import config

try: sys.stdout.reconfigure(encoding='utf-8')
except Exception: pass

SM_BASE = 'https://api.submagic.co/v1'


def main():
    ap = argparse.ArgumentParser(description='SubMagic: video URL → captions + zooms → mp4')
    ap.add_argument('video_url', help='Прямой URL видео (например signed URL от HeyGen — перезаливать не нужно)')
    ap.add_argument('--title', help='Название проекта в SubMagic (умолчание: по имени файла из URL)')
    ap.add_argument('--out', help='Куда сохранить итоговый mp4 (умолчание: $SHORTS_HOME/out/<project_id>.mp4)')
    ap.add_argument('--language', default='ru', help='Язык дорожки (умолчание ru)')
    ap.add_argument('--template', default='Hormozi 2', help='Шаблон субтитров SubMagic')
    ap.add_argument('--timeout-min', type=int, default=15, help='Сколько ждать рендер')
    args = ap.parse_args()

    sk = config.key('SUBMAGIC_API_KEY')
    headers = {'x-api-key': sk, 'Content-Type': 'application/json'}

    title = args.title or f'short-{time.strftime("%Y%m%d-%H%M%S")}'
    print(f'Video URL: {args.video_url[:80]}...')

    body = {
        'title': title,
        'language': args.language,
        'videoUrl': args.video_url,
        'templateName': args.template,
        'magicZooms': True,
        # magicBrolls MUST stay False on RU audio: auto-B-roll picks emoji/GIF by transcribed
        # keywords, so a mis-transcription lands on screen — «pivot» heard as «пиво» stamped a
        # 🍺 into a finished short. There is no PATCH for caption text, only a full re-render.
        # See references/gotchas.md §1-2.
        'magicBrolls': False,
        'cleanAudio': True,
        # 'dictionary' здесь НЕ передаётся сознательно: словарь помогает распознать НОВЫЕ
        # термины, но уже mistranscribed слово не чинит. Чистить надо скрипт ДО TTS
        # (trigger_word_check.py), а не выход. См. gotchas §1.
    }

    print('Creating SubMagic project...')
    r = requests.post(f'{SM_BASE}/projects', headers=headers, json=body, timeout=60)
    print(f'  HTTP {r.status_code}')
    if r.status_code not in (200, 201):
        print(f'  ERROR: {r.text[:500]}')
        sys.exit(1)
    proj = r.json()
    proj_id = proj.get('id') or proj.get('projectId')
    print(f'  project_id: {proj_id}')
    print(f'  status: {proj.get("status")}')

    out = Path(args.out) if args.out else (config.OUT_DIR / f'{proj_id}.mp4')
    out.parent.mkdir(parents=True, exist_ok=True)
    (out.parent / f'{proj_id}.state.json').write_text(
        json.dumps({'project_id': proj_id, 'video_url': args.video_url, 'initial': proj},
                   ensure_ascii=False, indent=2), encoding='utf-8')

    print('\nPolling for completion...')
    deadline = time.time() + args.timeout_min * 60
    while time.time() < deadline:
        r = requests.get(f'{SM_BASE}/projects/{proj_id}', headers={'x-api-key': sk}, timeout=60)
        if r.status_code != 200:
            print(f'  poll error {r.status_code}'); time.sleep(15); continue
        p = r.json()
        st = p.get('status')
        if st == 'completed':
            durl = p.get('downloadUrl') or p.get('download_url') or p.get('outputUrl')
            print('  ✓ COMPLETED')
            print(f'  previewUrl: https://app.submagic.co/view/{proj_id}')
            if not durl:
                print('  ВНИМАНИЕ: проект готов, но downloadUrl пуст — забери вручную по previewUrl')
                sys.exit(1)
            print(f'  Downloading to {out}...')
            with requests.get(durl, stream=True, timeout=300) as resp:
                resp.raise_for_status()
                with open(out, 'wb') as f:
                    for chunk in resp.iter_content(64 * 1024):
                        f.write(chunk)
            print(f'  ✓ Saved: {out} ({out.stat().st_size/1024:.0f}KB)')
            return
        if st == 'failed':
            print(f'  ✗ FAILED: {p.get("error") or p.get("failureReason")}')
            sys.exit(1)
        print(f'    submagic: {st}...', flush=True)
        time.sleep(20)

    print('  TIMEOUT — проект не досчитался за отведённое время; '
          f'проверь https://app.submagic.co/view/{proj_id}')
    sys.exit(1)


if __name__ == '__main__':
    main()
