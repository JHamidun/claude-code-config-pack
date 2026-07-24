# Higgsfield sandbox — audio-gen API + прозрачный/стикерный экспорт + sprite + маски/SAM

## 1. Audio-Gen API (озвучка/дубляж) — POST `https://api.higgsfield.ai/v1/audio/generate`
```json
// Voiceover/TTS
{"requests":[{"type":"voiceover","prompt":"Welcome back to the tech frontier.","model":"elevenlabs","voice_id":"c8b09ff2-…"}],"async":true}
// Dubbing/Translate (по job-id исходного видео)
{"requests":[{"type":"translate","target_language":"spa","input_video":{"id":"job_seedance_84b02ac8","type":"seedance_job"}}],"async":true}
```
Поллинг: `POST /v1/jobs/status` `{"job_ids":["job_audio_99bf234a"]}` → results[{status: completed/in_progress/failed, result.url}].

## 2. Suno (музыка) — POST `https://api.higgsfield.ai/v1/music/generate` (skill songwriting-and-ai-music)
```json
{"prompt":"[Intro]\n[Heavy analog synth growl]\nWe build from light...\n[Chorus]\n[Explosive drop]\nUnshackled entropy!",
 "tags":"vintage analog synth, cinematic dark electronic, minor key, 112bpm",
 "title":"Unshackled Entropy","make_instrumental":false,"model":"chirp-v3-5"}
```
Поллинг: `GET /v1/music/tasks?ids=task_suno_1a2b3c` → audio_url при completed. (метатеги [Intro]/[Chorus]/[Explosive drop] = наш elevenlabs/suno pattern.)

## 3. Прозрачный / стикерный экспорт (Telegram-стикеры, веб)
```bash
# WebM с альфой (VP9 yuva420p) из RGBA-кадров
ffmpeg -y -framerate 25 -i frame_%04d.png -c:v libvpx-vp9 -pix_fmt yuva420p -auto-alt-ref 0 -b:v 2M output_alpha.webm
# APNG (анимир. прозрачный PNG, бесконечный цикл)
ffmpeg -y -framerate 15 -i frame_%04d.png -f apng -plays 0 -pix_fmt rgba output.apng
# прозрачный GIF (reserve_transparent + alpha_threshold)
ffmpeg -y -i frame_%04d.png -filter_complex "[0:v]split[a][b];[a]palettegen=reserve_transparent=1[p];[b][p]paletteuse=alpha_threshold=128" output_transparent.gif
```
```python
# вырезание фона у видео покадрово (rembg, единая session = быстрее)
from rembg import remove, new_session; from PIL import Image; import os,sys
def remove_video_bg(ind, outd):
    os.makedirs(outd, exist_ok=True); s = new_session("u2net")
    for f in sorted(os.listdir(ind)):
        if f.endswith(('.png','.jpg','.jpeg')):
            remove(Image.open(os.path.join(ind,f)).convert("RGBA"), session=s).save(os.path.join(outd,f),"PNG")
```
→ прямо для твоих стикер-паков ([[runway-throttled-tasks-recovery-2026-06-06]], [[hailuo-dark-gradient-rembg-only-fix-2026-06-06]]): rembg покадрово → yuva420p webm / apng.

## 4. Sprite-sheet / atlas
```bash
# ffmpeg: 16 кадров 128×128 → 4×4 (512×512)
ffmpeg -y -i frame_%04d.png -filter_complex "tile=4x4" -vframes 1 sprite_sheet.png
```
```python
# PIL: авто-сетка ceil(sqrt(n)), прозрачный холст RGBA, paste по ячейкам
import os,math; from PIL import Image
def build_atlas(d,out):
    imgs=[Image.open(os.path.join(d,f)) for f in sorted(os.listdir(d)) if f.endswith('.png')]
    n=len(imgs); cols=math.ceil(math.sqrt(n)); rows=math.ceil(n/cols); w,h=imgs[0].size
    atlas=Image.new("RGBA",(cols*w,rows*h),(0,0,0,0))
    for i,im in enumerate(imgs): atlas.paste(im,(i%cols*w, i//cols*h))
    atlas.save(out,"PNG")
```

## 5. Ротоскоп / маски
```bash
# RGB + ЧБ-маска → прозрачный WebM (alphamerge)
ffmpeg -y -i rgb_content.mp4 -i alpha_mask.mp4 -filter_complex "[0:v][1:v]alphamerge[out]" -map "[out]" -c:v libvpx-vp9 -pix_fmt yuva420p output_matte.webm
# замена фона по маске (maskedmerge: фон0 + передний1 + маска2)
ffmpeg -y -i background.mp4 -i foreground.mp4 -i mask.mp4 -filter_complex "[0:v][1:v][2:v]maskedmerge[out]" -map "[out]" composited_scene.mp4
```
```python
# SAM-сегментация → alpha PNG (точка-промпт по центру кадра)
from segment_anything import sam_model_registry, SamPredictor; import cv2,numpy as np
sam=sam_model_registry["vit_h"](checkpoint="sam_vit_h_4b8939.pth"); p=SamPredictor(sam)
img=cv2.imread(path); p.set_image(img); h,w,_=img.shape
masks,_,_=p.predict(point_coords=np.array([[w//2,h//2]]), point_labels=np.array([1]), multimask_output=False)
rgba=cv2.cvtColor(img,cv2.COLOR_BGR2BGRA); rgba[:,:,3]=masks[0].astype(np.uint8)*255; cv2.imwrite(out,rgba)
```
→ Забрать: yuva420p webm + apng для стикеров (прямо в наш video-editor/sticker-flow), rembg single-session покадрово, alphamerge/maskedmerge композ, SAM center-point вырезание. Audio-gen/Suno API = их обёртка над ElevenLabs/Suno (у нас прямые ключи — см. elevenlabs skill, дешевле напрямую).
