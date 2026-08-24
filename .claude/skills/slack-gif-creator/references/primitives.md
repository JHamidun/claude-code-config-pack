# Каталог примитивов и хелперов

Полные сигнатуры вызовов. Открывай, когда нужен точный набор аргументов у
конкретного примитива. Исходники рядом — `templates/*.py` и `core/*.py`; если
здесь чего-то нет, читай сам файл, он не соврёт.

## Animation Primitives (`templates/`)

### Shake
```python
from templates.shake import create_shake_animation

frames = create_shake_animation(
    object_type='emoji',
    object_data={'emoji': '😱', 'size': 80},
    num_frames=20,
    shake_intensity=15,
    direction='both'  # or 'horizontal', 'vertical'
)
```

### Bounce
```python
from templates.bounce import create_bounce_animation

frames = create_bounce_animation(
    object_type='circle',
    object_data={'radius': 40, 'color': (255, 100, 100)},
    num_frames=30,
    bounce_height=150
)
```

### Spin / Rotate
```python
from templates.spin import create_spin_animation, create_loading_spinner

frames = create_spin_animation(
    object_type='emoji',
    object_data={'emoji': '🔄', 'size': 100},
    rotation_type='clockwise',   # or 'wobble'
    full_rotations=2
)
frames = create_loading_spinner(spinner_type='dots')
```

### Pulse / Heartbeat
```python
from templates.pulse import create_pulse_animation, create_attention_pulse

frames = create_pulse_animation(
    object_data={'emoji': '❤️', 'size': 100},
    pulse_type='smooth',         # or 'heartbeat' (double-pump)
    scale_range=(0.8, 1.2)
)
frames = create_attention_pulse(emoji='⚠️', num_frames=20)
```

### Fade
```python
from templates.fade import create_fade_animation, create_crossfade

frames = create_fade_animation(fade_type='in')   # or 'out'
frames = create_crossfade(
    object1_data={'emoji': '😊', 'size': 100},
    object2_data={'emoji': '😂', 'size': 100}
)
```

### Zoom
```python
from templates.zoom import create_zoom_animation, create_explosion_zoom

frames = create_zoom_animation(
    zoom_type='in',              # or 'out'
    scale_range=(0.1, 2.0),
    add_motion_blur=True
)
frames = create_explosion_zoom(emoji='💥')
```

### Explode / Shatter
```python
from templates.explode import create_explode_animation, create_particle_burst

frames = create_explode_animation(explode_type='burst', num_pieces=25)
frames = create_explode_animation(explode_type='shatter')
frames = create_explode_animation(explode_type='dissolve')
frames = create_particle_burst(particle_count=30)
```

### Wiggle / Jiggle
```python
from templates.wiggle import create_wiggle_animation, create_excited_wiggle

frames = create_wiggle_animation(wiggle_type='jello', intensity=1.0, cycles=2)
frames = create_wiggle_animation(wiggle_type='wave')
frames = create_excited_wiggle(emoji='🎉')
```

### Slide
```python
from templates.slide import create_slide_animation, create_multi_slide

frames = create_slide_animation(direction='left', slide_type='in', overshoot=True)
frames = create_slide_animation(direction='left', slide_type='across')

objects = [
    {'data': {'emoji': '🎯', 'size': 60}, 'direction': 'left', 'final_pos': (120, 240)},
    {'data': {'emoji': '🎪', 'size': 60}, 'direction': 'right', 'final_pos': (240, 240)}
]
frames = create_multi_slide(objects, stagger_delay=5)
```

### Flip
```python
from templates.flip import create_flip_animation, create_quick_flip

frames = create_flip_animation(
    object1_data={'emoji': '😊', 'size': 120},
    object2_data={'emoji': '😂', 'size': 120},
    flip_axis='horizontal'       # or 'vertical'
)
frames = create_quick_flip('👍', '👎')
```

### Morph / Transform
```python
from templates.morph import create_morph_animation, create_reaction_morph

frames = create_morph_animation(
    object1_data={'emoji': '😊', 'size': 100},
    object2_data={'emoji': '😂', 'size': 100},
    morph_type='crossfade'       # or 'scale', 'spin_morph'
)
```

### Move
```python
from templates.move import create_move_animation

# Linear
frames = create_move_animation(
    object_type='emoji', object_data={'emoji': '🚀', 'size': 60},
    start_pos=(50, 240), end_pos=(430, 240),
    motion_type='linear', easing='ease_out'
)

# Arc (parabolic)
frames = create_move_animation(
    object_type='emoji', object_data={'emoji': '⚽', 'size': 60},
    start_pos=(50, 350), end_pos=(430, 350),
    motion_type='arc', motion_params={'arc_height': 150}
)

# Circle
frames = create_move_animation(
    object_type='emoji', object_data={'emoji': '🌍', 'size': 50},
    motion_type='circle',
    motion_params={'center': (240, 240), 'radius': 120, 'angle_range': 360}
)

# Wave
frames = create_move_animation(
    motion_type='wave',
    motion_params={'wave_amplitude': 50, 'wave_frequency': 2}
)

# Низкоуровневый путь
from core.easing import interpolate, calculate_arc_motion
for i in range(num_frames):
    t = i / (num_frames - 1)
    x = interpolate(start_x, end_x, t, easing='ease_out')
    # или: x, y = calculate_arc_motion(start, end, height, t)
```

### Kaleidoscope
```python
from templates.kaleidoscope import (apply_kaleidoscope, create_kaleidoscope_animation,
                                    apply_simple_mirror)

kaleido_frame = apply_kaleidoscope(frame, segments=8)
frames = create_kaleidoscope_animation(base_frame=my_frame, num_frames=30,
                                       segments=8, rotation_speed=1.0)
mirrored = apply_simple_mirror(frame, mode='quad')  # 'horizontal','vertical','quad','radial'
```

## Helpers (`core/`)

### GIFBuilder — сборка и оптимизация
```python
from core.gif_builder import GIFBuilder

builder = GIFBuilder(width=480, height=480, fps=20)
for frame in my_frames:
    builder.add_frame(frame)
info = builder.save('output.gif', num_colors=128, optimize_for_emoji=False)
# info: size_kb, size_mb, frame_count, duration_seconds; save сам предупреждает о лимитах
```
Внутри: квантование палитры, выбрасывание дублирующихся кадров, предупреждения о
размере, агрессивный emoji-режим.

### Валидаторы
```python
from core.validators import check_slack_size, validate_dimensions, validate_gif, is_slack_ready

passes, info = check_slack_size('emoji.gif', is_emoji=True)
passes, info = validate_dimensions(128, 128, is_emoji=True)
all_pass, results = validate_gif('emoji.gif', is_emoji=True)
if is_slack_ready('emoji.gif', is_emoji=True): ...
```

### Текст
```python
from core.typography import draw_text_with_outline, TYPOGRAPHY_SCALE

draw_text_with_outline(frame, "BONK!", position=(240, 100),
                       font_size=TYPOGRAPHY_SCALE['h1'],  # 60px
                       text_color=(255, 68, 68), outline_color=(0, 0, 0),
                       outline_width=4, centered=True)
```

### Палитры
```python
from core.color_palettes import get_palette

palette = get_palette('vibrant')  # 'pastel', 'dark', 'neon', 'professional'
bg, text, accent = palette['background'], palette['primary'], palette['accent']
```

### Эффекты
```python
from core.visual_effects import ParticleSystem, create_impact_flash, create_shockwave_rings

particles = ParticleSystem()
particles.emit_sparkles(x=240, y=200, count=15)
particles.emit_confetti(x=240, y=200, count=20)
particles.update(); particles.render(frame)

frame = create_impact_flash(frame, position=(240, 200), radius=100)
frame = create_shockwave_rings(frame, position=(240, 200), radii=[30, 60, 90])
```

### Easing
```python
from core.easing import interpolate

y = interpolate(start=0, end=400, t=progress, easing='ease_in')      # падает — ускоряется
y = interpolate(start=0, end=400, t=progress, easing='ease_out')     # приземляется — замедляется
y = interpolate(start=0, end=400, t=progress, easing='bounce_out')
scale = interpolate(start=0.5, end=1.0, t=progress, easing='elastic_out')
```
Доступно: `linear`, `ease_in`, `ease_out`, `ease_in_out`, `bounce_out`,
`elastic_out`, `back_out` и другие — полный список в `core/easing.py`.

### Композиция кадра
```python
from core.frame_composer import (create_gradient_background, draw_emoji_enhanced,
                                 draw_circle_with_shadow, draw_star)

frame = create_gradient_background(480, 480, top_color, bottom_color)
draw_emoji_enhanced(frame, '🎉', position=(200, 200), size=80, shadow=True)
```

## Примеры композиции

### Пульсирующая реакция (emoji)
```python
builder = GIFBuilder(128, 128, 10)
for i in range(12):
    frame = Image.new('RGB', (128, 128), (240, 248, 255))
    scale = 1.0 + math.sin(i * 0.5) * 0.15
    size = int(60 * scale)
    draw_emoji_enhanced(frame, '😱', position=(64-size//2, 64-size//2), size=size, shadow=False)
    builder.add_frame(frame)
builder.save('reaction.gif', num_colors=40, optimize_for_emoji=True)
check_slack_size('reaction.gif', is_emoji=True)
```

### Действие с ударом (bounce + flash)
```python
builder = GIFBuilder(480, 480, 20)

for i in range(15):                                    # фаза 1: падение
    frame = create_gradient_background(480, 480, (240, 248, 255), (200, 230, 255))
    y = interpolate(0, 350, i / 14, 'ease_in')
    draw_emoji_enhanced(frame, '⚽', position=(220, int(y)), size=80)
    builder.add_frame(frame)

for i in range(8):                                     # фаза 2: удар + вспышка
    frame = create_gradient_background(480, 480, (240, 248, 255), (200, 230, 255))
    if i < 3:
        frame = create_impact_flash(frame, (240, 350), radius=120, intensity=0.6)
    draw_emoji_enhanced(frame, '⚽', position=(220, 350), size=80)
    if i > 2:
        draw_text_with_outline(frame, "GOAL!", position=(240, 150), font_size=60,
                               text_color=(255, 68, 68), outline_color=(0, 0, 0),
                               outline_width=4, centered=True)
    builder.add_frame(frame)

builder.save('goal.gif', num_colors=128)
```

### Комбинация примитивов (move → shake)
```python
shake_frames = create_shake_animation(
    object_type='emoji', object_data={'emoji': '😰', 'size': 70},
    num_frames=20, shake_intensity=12
)

builder = GIFBuilder(480, 480, 20)
for i in range(40):
    if i < 20:                                  # до триггера — своё движение
        frame = create_blank_frame(480, 480, (255, 255, 255))
        x = interpolate(50, 300, (i / 39) * 2, 'linear')
        draw_emoji_enhanced(frame, '🚗', position=(int(x), 300), size=60)
        draw_emoji_enhanced(frame, '😰', position=(350, 200), size=70)
    else:                                       # после — готовый кадр тряски
        frame = shake_frames[i - 20]
        draw_emoji_enhanced(frame, '🚗', position=(300, 300), size=60)
    builder.add_frame(frame)

builder.save('scare.gif')
```

### Ручная композиция двух движений в одном цикле
```python
for i in range(num_frames):
    frame = create_blank_frame(480, 480, bg_color)
    y = interpolate(start_y, ground_y, i / (num_frames - 1), 'bounce_out')
    x = center_x + (math.sin(i * 2) * 10 if y >= ground_y - 5 else 0)   # тряска только на ударе
    draw_emoji(frame, '⚽', (x, y), size=60)
    builder.add_frame(frame)
```
