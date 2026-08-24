# Higgsfield sandbox — камера-движения · стабилизация · интерполяция · авто-рефрейм · аудио-чистка · визуалайзеры · whisper

## 1. Камера-движения (из видео/статики)
```bash
# Ken Burns / push-in (zoompan, d=250 кадров)
ffmpeg -y -i input.mp4 -vf "scale=8000:-1,zoompan=z='zoom+0.0015':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=250:s=1920x1080" -c:v libx264 -crf 18 ken_burns.mp4
# whip-pan (crop + sin(t)-смещение + motion blur gblur)
ffmpeg -y -i input.mp4 -vf "scale=3840:1080,crop=1920:1080:'(iw-ow)*(sin(t*2)+1)/2':0,gblur=sigma=10:steps=1" -c:v libx264 -crf 18 whip_pan.mp4
# параллакс из 2 слоёв (fg/bg разная скорость zoompan)
ffmpeg -y -loop 1 -i background.png -loop 1 -i foreground.png -filter_complex "[0:v]scale=2560x1440,zoompan=z='zoom+0.0005':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1920x1080[bg];[1:v]scale=2560x1440,zoompan=z='zoom+0.002':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d=125:s=1920x1080[fg];[bg][fg]overlay=0:0:format=rgb" -t 5 -c:v libx264 -crf 18 parallax.mp4
```

## 2. Стабилизация (vid.stab, 2 прохода)
```bash
ffmpeg -y -i shaky.mp4 -vf "vidstabdetect=shakiness=10:accuracy=15:stepsize=6:result=transforms.trf" -f null -
ffmpeg -y -i shaky.mp4 -vf "vidstabtransform=input=transforms.trf:smoothing=30:optzoom=1:zoom=15:interpol=bilinear" -c:v libx264 -crf 18 -pix_fmt yuv420p stabilized.mp4
```

## 3. Интерполяция кадров (minterpolate, оптический поток)
```bash
# 24/30 → 60 fps
ffmpeg -y -i input.mp4 -vf "minterpolate=fps=60:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1" -c:v libx264 -crf 18 out_60fps.mp4
# сверхплавный slow-mo 0.25x (25fps→100 интерпол. → setpts 4x → -r 25)
ffmpeg -y -i input.mp4 -vf "minterpolate=fps=100:mi_mode=mci:mc_mode=aobmc,setpts=4*PTS" -r 25 -c:v libx264 -crf 18 slowmo.mp4
```

## 4. Умный авто-рефрейм 16:9→9:16 (трекинг лица MediaPipe → динамический crop)
Python считает crop_w = height*(target_w/target_h) (для 1920×1080 → 607×1080), детектит лицо (mp.solutions.face_detection) покадрово, строит ffmpeg-выражение `crop=W:H:if(lte(t,T1),x1,if(lte(t,T2),x2,…)):0` (динамическое x по времени) → 
```bash
ffmpeg -y -i input_16_9.mp4 -vf "[FILTER_EXPR],scale=1080:1920" -c:v libx264 -crf 18 output_9_16.mp4
```
(= наш `reframe_9x16.py --method yolo`; их через MediaPipe + динамическое crop-выражение.)

## 5. Голос-чистка (broadcast)
```bash
# шумодав FFT + вырезание пауз >0.5с ниже -40dB
ffmpeg -y -i noisy.wav -af "afftdn=noise_reduction=15:noise_type=w,silenceremove=start_periods=1:start_duration=0.5:start_threshold=-40dB:end_periods=-1:end_duration=0.5:end_threshold=-40dB" clean_silenced.wav
# цепочка голоса: highpass 80 + EQ +3dB@3k + deesser + компрессор compand
ffmpeg -y -i clean_silenced.wav -af "highpass=f=80,anequalizer=c0 f=3000 w=200 g=3 t=1,deesser=i=0.5:m=0.5:f=6000:b=1000,compand=attacks=0.01:decays=0.1:points=-40/-40|-20/-15|0/-10:soft-gasp=0.01" final_broadcast.wav
```

## 6. Аудио-визуализаторы (музыкальные ролики/подкасты)
```bash
# waveform (зеркальные линии, log-scale)
ffmpeg -y -i audio.mp3 -filter_complex "[0:a]showwaves=s=1920x1080:mode=line:colors=0x00ffff|0x008b8b:scale=log[v]" -map "[v]" -map 0:a -c:v libx264 -crf 20 -c:a copy waveform.mp4
# спектр (scroll, rainbow, log)
ffmpeg -y -i audio.mp3 -filter_complex "[0:a]showspectrum=s=1920x1080:slide=scroll:scale=log:color=rainbow:legend=1[v]" -map "[v]" -map 0:a -c:v libx264 -crf 20 -c:a copy spectrum.mp4
```

## 7. Whisper → SRT/ASS-караоке
```bash
ffmpeg -y -i input_video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 mono_speech_16k.wav   # моно 16k для ASR
```
```python
import whisper; from whisper.utils import get_writer
model = whisper.load_model("large-v3")
result = model.transcribe(audio, temperature=0.0, word_timestamps=True, beam_size=5)
get_writer("srt", out)(result, audio, {"max_line_width":42,"max_line_count":2,"highlight_words":True})
get_writer("ass", out)(result, audio, {"max_line_width":42,"max_line_count":1,"highlight_words":True})  # караоке word-highlight
```
→ Забрать в video-editor: minterpolate slow-mo (лучше нашего setpts без интерполяции), vidstab 2-pass, MediaPipe smart-crop (альтернатива нашему YOLO reframe), voice chain afftdn→silenceremove→deesser→compand, showwaves/showspectrum для аудио-роликов, whisper word_timestamps→ASS (= наш karaoke_captions.py через WhisperX).
