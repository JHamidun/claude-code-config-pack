# HeyGen v3 — готовый Python-клиент и рецепты

Открывай, когда пишешь скрипт против **публичного** API (`x-api-key`, кошелёк
API). Это единственный контур, который навык описывает; почему так — см. в
`../SKILL.md` врезку «Чего в паке нет и почему».

```python
import os, time, requests
from pathlib import Path

KEY = os.environ['HEYGEN_API_KEY']
BASE = 'https://api.heygen.com'
H = {'x-api-key': KEY, 'Content-Type': 'application/json'}
ASSET = lambda url=None, asset_id=None: ({'type':'url','url':url} if url else {'type':'asset_id','asset_id':asset_id})


def wallet_balance() -> float:
    r = requests.get(f'{BASE}/v3/users/me', headers={'x-api-key': KEY}, timeout=30); r.raise_for_status()
    return r.json()['data'].get('wallet', {}).get('remaining_balance', 0.0)


def create_video_avatar(*, avatar_id, script=None, audio_asset_id=None, voice_id=None,
                        aspect_ratio='9:16', resolution='1080p', use_avatar_v=False,
                        motion_prompt=None, expressiveness=None,
                        callback_id=None, callback_url=None, idempotency_key=None) -> str:
    body = {'type': 'avatar', 'avatar_id': avatar_id,
            'aspect_ratio': aspect_ratio, 'resolution': resolution}
    if script: body['script'] = script
    if audio_asset_id: body['audio_asset_id'] = audio_asset_id
    if voice_id: body['voice_id'] = voice_id
    if use_avatar_v: body['engine'] = {'type': 'avatar_v'}
    if motion_prompt: body['motion_prompt'] = motion_prompt
    if expressiveness: body['expressiveness'] = expressiveness
    if callback_id: body['callback_id'] = callback_id
    if callback_url: body['callback_url'] = callback_url
    headers = dict(H)
    if idempotency_key: headers['Idempotency-Key'] = idempotency_key
    r = requests.post(f'{BASE}/v3/videos', headers=headers, json=body, timeout=30)
    r.raise_for_status(); return r.json()['data']['video_id']


def create_video_cinematic(*, prompt, avatar_ids, references=None, aspect_ratio='9:16',
                           resolution='1080p', duration=10, auto_duration=False,
                           enhance_prompt=False, title=None) -> str:
    """Seedance prompt+refs. avatar_ids = list of 1–3 look IDs. Flat $7/video."""
    body = {'type': 'cinematic_avatar', 'prompt': prompt, 'avatar_id': avatar_ids,
            'aspect_ratio': aspect_ratio, 'resolution': resolution, 'enhance_prompt': enhance_prompt}
    if references: body['references'] = references          # [{'type':'url','url':...}, ...]
    if auto_duration: body['auto_duration'] = True
    else: body['duration'] = duration
    if title: body['title'] = title
    r = requests.post(f'{BASE}/v3/videos', headers=H, json=body, timeout=30)
    r.raise_for_status(); return r.json()['data']['video_id']


def get_video(video_id: str) -> dict:
    r = requests.get(f'{BASE}/v3/videos/{video_id}', headers={'x-api-key': KEY}, timeout=30)
    r.raise_for_status(); return r.json()['data']


def wait_for_video(video_id: str, max_min=15, poll_s=15) -> dict:
    deadline = time.time() + max_min * 60
    while time.time() < deadline:
        d = get_video(video_id); st = d.get('status')
        if st == 'completed': return d
        if st == 'failed': raise RuntimeError(f'{video_id} failed: {d.get("failure_reason")}')
        time.sleep(poll_s)
    raise TimeoutError(f'{video_id} not done in {max_min} min')


def avatar_v_eligible(look_id: str) -> bool:
    r = requests.get(f'{BASE}/v3/avatars/looks/{look_id}', headers={'x-api-key': KEY}, timeout=30)
    r.raise_for_status()
    return 'avatar_v' in r.json()['data'].get('supported_api_engines', [])


def upload_asset(path: Path) -> str:
    with open(path, 'rb') as f:
        r = requests.post(f'{BASE}/v3/assets', headers={'x-api-key': KEY}, files={'file': f}, timeout=120)
    r.raise_for_status(); return r.json()['data']['asset_id']


def lipsync(*, video_url, audio_url, mode='precision') -> str:
    r = requests.post(f'{BASE}/v3/lipsyncs', headers=H, json={
        'video': ASSET(url=video_url), 'audio': ASSET(url=audio_url), 'mode': mode}, timeout=30)
    r.raise_for_status(); return r.json()['data']['lipsync_id']


def translate(*, video_url, output_languages, mode='precision', title='Translation') -> list:
    """output_languages = language NAMES (e.g. ['Spanish (Spain)','German'])."""
    r = requests.post(f'{BASE}/v3/video-translations', headers=H, json={
        'video': ASSET(url=video_url), 'output_languages': output_languages,
        'mode': mode, 'title': title, 'fps_mode': 'passthrough'}, timeout=30)
    r.raise_for_status(); return r.json()['data']


def tts_starfish(*, voice_id, text, speed=1.0, input_type='text') -> dict:
    r = requests.post(f'{BASE}/v3/voices/speech', headers=H, json={
        'voice_id': voice_id, 'text': text, 'input_type': input_type, 'speed': speed}, timeout=60)
    r.raise_for_status(); return r.json()['data']


def clone_voice(*, audio_url, voice_name, language=None) -> dict:
    body = {'audio': ASSET(url=audio_url), 'voice_name': voice_name}
    if language: body['language'] = language
    r = requests.post(f'{BASE}/v3/voices/clone', headers=H, json=body, timeout=60)
    r.raise_for_status(); return r.json()['data']


def video_agent(*, prompt, mode='generate', style_id=None, brand_kit_id=None, callback_url=None) -> str:
    body = {'prompt': prompt, 'mode': mode}
    if style_id: body['style_id'] = style_id
    if brand_kit_id: body['brand_kit_id'] = brand_kit_id
    if callback_url: body['callback_url'] = callback_url
    r = requests.post(f'{BASE}/v3/video-agents', headers=H, json=body, timeout=30)
    r.raise_for_status(); return r.json()['data']['session_id']


def register_webhook(url: str, events: list) -> dict:
    r = requests.post(f'{BASE}/v3/webhooks/endpoints', headers=H, json={'url': url, 'events': events}, timeout=30)
    r.raise_for_status(); return r.json()['data']   # {endpoint_id, signing_secret} — store secret now
```

## Recipes

### Short с digital twin — максимальное качество (Avatar V, если look проходит)
```python
import os
# Свои id: HEYGEN_AVATAR_ID / HEYGEN_VOICE_ID в ~/.claude/.credentials.master.env.
# Где взять — app.heygen.com/avatars и /voices, либо GET /v3/avatars/looks и GET /v3/voices.
look_id = os.environ['HEYGEN_AVATAR_ID']   # verify it's a v3 look via GET /v3/avatars/looks
vid = create_video_avatar(avatar_id=look_id, script='Hook... reveal... loop close.',
    voice_id=os.environ['HEYGEN_VOICE_ID'], aspect_ratio='9:16', resolution='1080p',
    use_avatar_v=avatar_v_eligible(look_id), callback_id='shorts-001')
d = wait_for_video(vid)   # d['video_url'] → SubMagic
```

### Cinematic Avatar — prompt + референс (Seedance)
```python
vid = create_video_cinematic(
    prompt='A founder in a sunlit studio, warm cinematic grade, slow push-in, talking to camera about AI.',
    avatar_ids=['<look_id>'], references=[{'type':'url','url':'https://.../user-ref.jpg'}],
    aspect_ratio='9:16', resolution='1080p', duration=12)
d = wait_for_video(vid)
```

### ElevenLabs clone → HeyGen lip-sync
```python
# Option A: pre-recorded audio into /v3/videos
asset_id = upload_asset(elevenlabs_tts(text='...', voice_id=os.environ['ELEVENLABS_VOICE_ID_RU']))
create_video_avatar(avatar_id=os.environ['HEYGEN_AVATAR_ID'], audio_asset_id=asset_id, aspect_ratio='9:16')
# Option B: dub an existing video
lipsync(video_url='https://...your-video.mp4', audio_url='https://...eleven.mp3', mode='precision')
```

### Вебинар на 5 языков
```python
ids = translate(video_url='https://...webinar.mp4',
    output_languages=['English','Spanish (Spain)','French','German','Portuguese (Brazil)'],
    mode='precision', title='webinar')
# poll GET /v3/video-translations/{id} per returned translation
```

### HyperFrames — брендовое интро из HTML
```python
import requests
r = requests.post(f'{BASE}/v3/hyperframes/renders', headers=H, json={
    'project': {'type':'url','url':'https://.../intro-comp.zip'},
    'composition': 'compositions/intro.html',
    'variables': {'title': 'Your Channel Name', 'accent': '#ff6a00'},
    'resolution': '1080p', 'aspect_ratio': '9:16', 'fps': 30}, timeout=30)
render_id = r.json()['data']['render_id']
```
