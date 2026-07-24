# Higgsfield UGC + TV-Ad employee flows (full, debug-disclosure)

Все UGC-флоу = **слот-борд** (горизонтальный стрип, делённый на вертикальные 9:16 слоты = последовательные моменты
одного 15с клипа) → seedance_2_0 (9:16) → montage hard-cut. Общая цепочка: `product-analyzer` (описание, сегмент
luxury/premium/drugstore, категория) → input type auto/guided/director → персонаж (ugc-character → text2image_soul_v2
3:4 2k, либо прикреплённый портрет) → последовательные борды (gpt_image_2, каждый обуславливается предыдущим) →
параллельные ugc-clip промпты → рендер. **Связывание двухканальное:** job_id в `medias[].value` + public url в
`image_refs`; повторный upload запрещён. **First-Word Constraint:** первое слово аудио = хук, без OK/Okay/So/Yeah/Um.

## ugc-flow (talking-head, 3-slot 16:9→3×9:16)
Создатель в кадре держит продукт, эмоционально рассказывает. Один создатель/ролик (внешность+одежда залочены).
Sub-agents: `ugc-character` (портрет на нейтрал фоне) · `ugc-board` (стрип 16:9 / 3 слота 9:16, бесшовное окружение) · `ugc-clip` (динам. Seedance промпт, hard-cut между слотами).

## ugc-unboxing-flow (4-slot 21:9)
Арка: **Slot1 Packed** (запечатанная коробка) → **Slot2 Reveal** (извлечение, пик эмоций) → **Slot3 Product-Focus** (macro, коробки нет) → **Slot4 Satisfaction** (позирует с продуктом). Коробка дефолт крафт; реал-фото → `package_media_id` на slot1. CTA-tail (~0.5-1с, жест вниз). Sub: `ugc-unboxing-board`, `ugc-unboxing-clip` (вскрытие, шуршание, фокус на продукт).

## ugc-tutorial-flow (4-slot, Step N)
4 хронолог. шага/клип. **Сквозная нумерация** (клип2 = Step 5..8). Плашка `Step N — Heading` (Step 2 — Apply Cream), единый стиль. **Product Usage Analysis** до бордов (если <4×N шагов — добавить подготовительные; если > — объединить микрошаги). CTA-tail (селфи-камера + жест вниз + «Link in bio»). Sub: `ugc-tutorial-boards`, `ugc-tutorial-clip-prompt` (+ массив step_captions).

## ugc-try-on-flow (4-slot, OOTD/Fit Check)
**Slot1 Pre-Wear** (нейтрал домашка, крафт-пакет, вещь скрыта) → **Slot2 Wearing** (одет, Tripod POV, twirl 360° reveal → замирает) → **Slot3 Texture Close-up** (экстрим-макро ткани, **hands-free**, руки вне кадра) → **Slot4 Style Pose** (стильная поза в другой комнате того же дома). **No Mirrors** (запрет зеркал/отражений/селфи). Клипы 1/2/4 = lip-sync, клип3 = VO (создатель молчит). Sub: `ugc-try-board`, `ugc-try-clip` (twirl в 2, VO в 3).

## ugc-product-flow (без создателя, VO-only)
Продукт = единственный герой; люди только «вспомогательные руки» по периферии/POV, лица не показывать. 4-slot 21:9: **Intro** (в окружении) → **Demo-A** → **Demo-B** (др. масштаб/функция) → **Result**. `voice_gender` (female/male/random) синхрон с гендером рук. Продукт через upload, залочен во всех 4 слотах. Sub: `ugc-product-boards`, `ugc-product-clip-prompt` (VO + макро-движения камеры вокруг продукта).

## tv-ad (премиум 15с 16:9 1080p)
**3 формата:** Problem-Solution (VO) · Lifestyle (говорит на камеру) · High-Energy (кинетическая камера, абстракт).
**Screen Lock:** продукт с экраном (телефон/часы/консоль) → `is_screen_bearing=true` (блок дрифта интерфейса).
**Стадии:** I Параметры → II `brand-analyzer` (по сайту клиента → бренд-бук: цвета/шрифты/позиционирование) → **III GATE I** `tv-ad-script` (апрув сценария обязателен) → IV-V `tv-ad-character`(soul_v2)+`tv-ad-location`(gpt_image_2) → **VI GATE II** `tv-ad-seedance` → seedance_2_0, апрув видео.
**medias[] строгий порядок: 1.Локация 2.Продукт 3.Герой 4.Бренд-ассет** (для @Image1..4 связывания).
Sub: `tv-ad-script` (7-панельная структура + Packshot финал) · `tv-ad-character` (одежда под фирменные цвета) · `tv-ad-location` (интерьер с бренд-буком) · `tv-ad-seedance` (сценарий + screen-lock + послойная анимация + продукт + Anti-bleed/Sound design).

## Забрать к нам
- **Slot-board паттерн** (1 горизонтальный кадр = N последовательных моментов) — дешёвая раскадровка одним изображением.
- **First-Word Constraint** (хук с 1-го слова, без филлеров) → в наши tts/shorts-скиллы (анти-AI-звучание).
- **UGC канон-арки** (unboxing Packed→Reveal→Focus→Satisfaction; try-on Pre→Wear→Texture→Pose; tutorial Step-N) = готовые шаблоны коротких роликов.
- **tv-ad GATE-driven** + brand-analyzer→бренд-бук + medias порядок-связывание + Screen Lock — для брендовых роликов.
- product-analyzer сегментирование (luxury/premium/drugstore) + voice_gender↔hands sync.
