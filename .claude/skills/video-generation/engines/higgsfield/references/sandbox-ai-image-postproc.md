# Higgsfield sandbox — AI image-постобработка (опенсорс-инструменты)

⚠️ Это **стандартные опенсорс-модели** (не HF-секреты) — полезный cookbook. У нас локально на your-GPU = бесплатно,
или через Replicate. Для нашего image-enhancer/nano-banana-pro как набор рецептов.

## 1. Face-restore — GFPGAN v1.4
```python
from gfpgan import GFPGANer; import cv2
restorer = GFPGANer(model_path="GFPGANv1.4.pth", upscale=2, arch='clean', channel_multiplier=2, bg_upsampler=None)
_,_,restored = restorer.enhance(cv2.imread(inp), has_aligned=False, only_center_face=False, paste_back=True)
cv2.imwrite(out, restored)
```
(альтернатива CodeFormer; фон апскейлится отдельно super-res'ом.) Replicate: `tencentarc/gfpgan`.

## 2. Super-res — Real-ESRGAN x4
```bash
# CLI (vulkan, без GPU-зависимостей): RealESRGAN_x4plus (фото) / RealESRGAN_x4plus_anime_6B (иллюстрации)
realesrgan-ncnn-vulkan -i input_lowres.png -o output_upscaled.png -n RealESRGAN_x4plus -s 4 -f png
```
```python
from realesrgan import RealESRGANer; from basicsr.archs.rrdbnet_arch import RRDBNet; import cv2
m=RRDBNet(num_in_ch=3,num_out_ch=3,num_feat=64,num_block=23,num_grow_ch=32,scale=4)
up=RealESRGANer(scale=4, model_path='RealESRGAN_x4plus.pth', model=m, tile=400, tile_pad=10, half=True)  # tile=400 от VRAM-overflow, half=FP16
out,_=up.enhance(cv2.imread(inp), outscale=4); cv2.imwrite(outp, out)
```
Replicate: `nightmareai/real-esrgan`. (Higgsfield Topaz = коммерческий аналог — см. model-provider-map.)

## 3. Inpaint / object-removal — LaMa (FFC, TorchScript)
```python
import torch, cv2, numpy as np
model = torch.jit.load("lama_model.pt", map_location=device).eval()
img = cv2.cvtColor(cv2.imread(image), cv2.COLOR_BGR2RGB); h,w,_=img.shape
pad_h=(8-h%8)%8; pad_w=(8-w%8)%8  # кратность 8 обязательна
img_p=np.pad(img,((0,pad_h),(0,pad_w),(0,0)),mode="edge"); mask_p=np.pad(cv2.imread(mask,0),((0,pad_h),(0,pad_w)),mode="edge")
it=torch.from_numpy(img_p).float().permute(2,0,1).unsqueeze(0).to(device)/255.0
mt=(torch.from_numpy(mask_p).float().unsqueeze(0).unsqueeze(0).to(device)/255.0 > 0.5).float()  # бинаризация
with torch.no_grad(): pred=model(it,mt)
o=np.clip(pred[0].permute(1,2,0).cpu().numpy()*255,0,255).astype(np.uint8)[:h,:w,:]
cv2.imwrite(out, cv2.cvtColor(o, cv2.COLOR_RGB2BGR))
```
Replicate: `cjwbw/lama` / `allenhooo/lama`. (= наш void-video для видео-inpaint.)

## 4. Outpaint — SD Inpaint (Diffusers), canvas expand
Расширить холст (PIL paste на больший canvas + маска новых зон) → `StableDiffusionInpaintPipeline` дорисовывает. Replicate: `black-forest-labs/flux-fill-pro` (лучше) или nano_banana_2 edit с «extend the scene». (FLUX Fill у нас через Replicate — см. model-provider-map.)

## 5. Depth-map → 2.5D parallax / 3D-photo — Depth-Anything / MiDaS
`Depth-Anything-V2` (или MiDaS dpt_large) → grayscale depth → смещение слоёв по глубине для параллакса (см. наш sandbox-camera §параллакс). Replicate: `chenxwh/depth-anything-v2`.

## 6. Colorize ЧБ→цвет — DDColor
`piddnad/ddcolor` (SOTA раскраска). Replicate: `cjwbw/ddcolor`. (старое: deoldify.)

## 7. Style-transfer — Fast Neural Style (VGG) / IP-Adapter
Классика: предобученные VGG fast-neural-style (`pytorch/examples` fast_neural_style). Современнее: IP-Adapter / FLUX Redux на Replicate (перенос стиля по референсу).

→ Вердикт: для нас всё это = **локально на your-GPU бесплатно** (GFPGAN/ESRGAN/LaMa/Depth-Anything/DDColor ставятся pip) ИЛИ Replicate. В наш image-enhancer/void-video как готовые рецепты. Higgsfield тут не уникален.
