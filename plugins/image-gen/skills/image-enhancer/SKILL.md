---
name: image-enhancer
description: "Улучшение картинок: апскейл, denoise, оптимизация (Pillow/OpenCV). Триггеры: «улучши качество», «увеличь разрешение», «картинка мыльная»."
---

# Image Enhancer Skill

## Overview

Улучшение качества изображений: upscaling, denoising, enhancement, optimization.

## When to Use

- Увеличение разрешения
- Улучшение качества фото
- Удаление шума
- Оптимизация для web
- Реставрация старых фото

## Tools & Libraries

### Pillow (Basic)

```python
from PIL import Image, ImageEnhance, ImageFilter

def enhance_image(input_path: str, output_path: str):
    """Basic image enhancement"""
    img = Image.open(input_path)

    # Resize (upscale 2x)
    new_size = (img.width * 2, img.height * 2)
    img = img.resize(new_size, Image.LANCZOS)

    # Enhance sharpness
    enhancer = ImageEnhance.Sharpness(img)
    img = enhancer.enhance(1.5)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.2)

    # Enhance color
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.1)

    img.save(output_path, quality=95)
    return output_path
```

### OpenCV (Advanced)

```python
import cv2
import numpy as np

def denoise_image(input_path: str, output_path: str):
    """Remove noise from image"""
    img = cv2.imread(input_path)

    # Non-local means denoising
    denoised = cv2.fastNlMeansDenoisingColored(
        img,
        None,
        h=10,          # Filter strength
        hColor=10,     # Color filter strength
        templateWindowSize=7,
        searchWindowSize=21
    )

    cv2.imwrite(output_path, denoised)
    return output_path

def sharpen_image(input_path: str, output_path: str):
    """Sharpen image"""
    img = cv2.imread(input_path)

    # Unsharp mask
    gaussian = cv2.GaussianBlur(img, (0, 0), 3)
    sharpened = cv2.addWeighted(img, 1.5, gaussian, -0.5, 0)

    cv2.imwrite(output_path, sharpened)
    return output_path

def adjust_brightness_contrast(input_path: str, output_path: str,
                                brightness: int = 0, contrast: int = 0):
    """Adjust brightness and contrast"""
    img = cv2.imread(input_path)

    # Brightness: -127 to 127
    # Contrast: -127 to 127
    img = np.int16(img)
    img = img * (contrast / 127 + 1) - contrast + brightness
    img = np.clip(img, 0, 255)
    img = np.uint8(img)

    cv2.imwrite(output_path, img)
    return output_path
```

### Real-ESRGAN (AI Upscaling)

```bash
# Install
pip install realesrgan

# Command line
realesrgan-ncnn-vulkan -i input.jpg -o output.jpg -n realesrgan-x4plus
```

```python
from realesrgan import RealESRGANer
from basicsr.archs.rrdbnet_arch import RRDBNet
import cv2

def upscale_with_realesrgan(input_path: str, output_path: str, scale: int = 4):
    """AI-powered upscaling"""
    # Load model
    model = RRDBNet(num_in_ch=3, num_out_ch=3, num_feat=64,
                    num_block=23, num_grow_ch=32, scale=4)

    upsampler = RealESRGANer(
        scale=scale,
        model_path='weights/RealESRGAN_x4plus.pth',
        model=model,
        tile=0,
        tile_pad=10,
        pre_pad=0,
        half=True  # Use FP16
    )

    img = cv2.imread(input_path, cv2.IMREAD_UNCHANGED)
    output, _ = upsampler.enhance(img, outscale=scale)
    cv2.imwrite(output_path, output)

    return output_path
```

## Image Optimization

### For Web

```python
from PIL import Image
import os

def optimize_for_web(input_path: str, output_path: str,
                     max_width: int = 1920, quality: int = 85):
    """Optimize image for web"""
    img = Image.open(input_path)

    # Convert to RGB if needed
    if img.mode in ('RGBA', 'P'):
        img = img.convert('RGB')

    # Resize if too large
    if img.width > max_width:
        ratio = max_width / img.width
        new_size = (max_width, int(img.height * ratio))
        img = img.resize(new_size, Image.LANCZOS)

    # Save optimized
    img.save(output_path, 'JPEG', quality=quality, optimize=True)

    # Report compression
    original_size = os.path.getsize(input_path)
    new_size = os.path.getsize(output_path)
    reduction = (1 - new_size / original_size) * 100

    return {
        'output': output_path,
        'original_size': original_size,
        'new_size': new_size,
        'reduction_percent': round(reduction, 1)
    }
```

### WebP Conversion

```python
def convert_to_webp(input_path: str, quality: int = 80):
    """Convert to WebP format"""
    img = Image.open(input_path)
    output_path = input_path.rsplit('.', 1)[0] + '.webp'

    img.save(output_path, 'WEBP', quality=quality)
    return output_path
```

### Batch Processing

```python
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

def batch_optimize(input_dir: str, output_dir: str, max_workers: int = 4):
    """Optimize all images in directory"""
    input_path = Path(input_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    images = list(input_path.glob('*.{jpg,jpeg,png,webp}'))

    def process(img_path):
        output_file = output_path / img_path.name
        return optimize_for_web(str(img_path), str(output_file))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(process, images))

    return results
```

## Color Correction

```python
def auto_white_balance(input_path: str, output_path: str):
    """Automatic white balance correction"""
    img = cv2.imread(input_path)

    # Convert to LAB color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)

    # Apply CLAHE to L channel
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)

    # Merge and convert back
    lab = cv2.merge([l, a, b])
    result = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)

    cv2.imwrite(output_path, result)
    return output_path

def adjust_saturation(input_path: str, output_path: str, factor: float = 1.2):
    """Adjust color saturation"""
    img = cv2.imread(input_path)
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)

    hsv[:, :, 1] = hsv[:, :, 1] * factor
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)

    result = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)
    cv2.imwrite(output_path, result)
    return output_path
```

## Photo Restoration

```python
def remove_scratches(input_path: str, output_path: str):
    """Remove scratches from old photos"""
    img = cv2.imread(input_path)

    # Create mask for scratches (bright thin lines)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, mask = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)

    # Dilate mask
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.dilate(mask, kernel, iterations=1)

    # Inpaint
    result = cv2.inpaint(img, mask, 3, cv2.INPAINT_TELEA)

    cv2.imwrite(output_path, result)
    return output_path
```

## Complete Enhancement Pipeline

```python
def full_enhancement_pipeline(input_path: str, output_path: str):
    """Complete image enhancement"""
    img = cv2.imread(input_path)

    # 1. Denoise
    img = cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)

    # 2. White balance
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)

    # 3. Sharpen
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    img = cv2.filter2D(img, -1, kernel)

    # 4. Adjust saturation slightly
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] = hsv[:, :, 1] * 1.1
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    img = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)

    cv2.imwrite(output_path, img, [cv2.IMWRITE_JPEG_QUALITY, 95])
    return output_path
```

## API Services

### With AI APIs

```python
import requests
import base64

def enhance_with_api(input_path: str, api_key: str) -> str:
    """Use external API for enhancement"""
    with open(input_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()

    response = requests.post(
        'https://api.example.com/enhance',
        headers={'Authorization': f'Bearer {api_key}'},
        json={
            'image': image_data,
            'enhancement': 'upscale_4x',
            'denoise': True
        }
    )

    result = response.json()
    return base64.b64decode(result['enhanced_image'])
```

## Quality Metrics

```python
def calculate_image_quality(image_path: str) -> dict:
    """Calculate image quality metrics"""
    img = cv2.imread(image_path)

    # Sharpness (Laplacian variance)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()

    # Brightness
    brightness = np.mean(gray)

    # Contrast
    contrast = np.std(gray)

    # Colorfulness
    b, g, r = cv2.split(img)
    rg = np.absolute(r.astype(int) - g.astype(int))
    yb = np.absolute(0.5 * (r.astype(int) + g.astype(int)) - b.astype(int))
    colorfulness = np.sqrt(np.mean(rg)**2 + np.mean(yb)**2) + 0.3 * np.sqrt(np.std(rg)**2 + np.std(yb)**2)

    return {
        'sharpness': round(sharpness, 2),
        'brightness': round(brightness, 2),
        'contrast': round(contrast, 2),
        'colorfulness': round(colorfulness, 2)
    }
```

## Tips

1. **Always backup** - сохраняй оригинал
2. **Lossless first** - сначала lossless операции
3. **Quality settings** - 80-85% для web достаточно
4. **WebP** - меньше размер при том же качестве
5. **AI upscaling** - лучше чем традиционные методы
6. **Batch processing** - автоматизируй рутину
7. **Monitor size** - следи за размером файлов
