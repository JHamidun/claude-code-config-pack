# MD-board sub-agents — storyboard-sheet generators (highMD/productMD/typographyMD/infographicMD-board)

Генерят лист раскадровки (gpt_image_2) → потом *MD-clip анимирует. Универсальная структура промпта board +
единый JSON `board_specs`. (classicMD-board дословно → motion-designer-classicMD-board-prompt.md.)

## Универсальный board prompt
`GRID LAYOUT & CHROME` (NxM сетка, sheet bg, hairline gutters) → `STYLE & PALETTE LOCK` (register, palette, "ALL PANELS COHERENT WORLD") → `SUBJECT & MATERIAL LOCK` (motif/material/signature element) → `PANEL BREAKDOWN 01..N` (Panel 0X — CONTENT / NARRATIVE BEAT / LIGHT[TYPE/DIRECTION/DOES] / EFFECTS) → `TEXT IN PANEL` (chess-pattern панели) → `BRAND REVEAL` (Panel N, type R1-R8) → `RULE 10 SAFETY` (no metadata-chips внутри панелей, только в chrome-полях).

## Универсальный JSON board_specs
```json
{"case":"motion-design-board","input_tier":"auto|guided|director","board_specs":{
 "project_title","duration":15,"format","style_aesthetic","camera_mode",
 "palette":["#HEX1","#HEX2","#HEX3"],"tone_descriptors":[],"style_descriptors":[],
 "chess_pattern":"A|B|Hybrid","text_panel_ids":[],"brand_panel_id","brand_mode",
 "brand_reveal_type":"R1..R8","font_pairing":{"display","accent"},
 "panel_layouts":{"01":"A".."G"},"punch_lines":{},"brand_tagline"},
 "panels":[{"id","timecode","role":"visual|text","caption"}],"prompt":"<gpt_image_2 промпт>"}
```

## Специфика
- **highMD-board:** 6 пан 3×2, sheet **#000000**, Hyperkinetic, Material Lock (жидкое стекло/лава/хром), text-панели B {02,04,06}, brand_reveal R1 (Material assembly), font Futura Condensed. EFFECTS: motion blur + bloom; NARRATIVE BEAT = пиковая фаза (splash 1.2s, shatter 2.1s).
- **productMD-board:** 9 пан 3×3 16:9, sheet **#DDDDDD** (3px borders/28px gutters/40px margin), **PRODUCT BIBLE @Image1** (engineering identity), Scale Alternation (Wide→Macro→Medium→Special→Medium→Macro→Overhead→Wide→Medium), Shot 04=trick, текст только 01/08/09 белый Helvetica, chrome monospace tech-notes (ACTION/CAMERA/LIGHT). brand_reveal R2.
- **typographyMD-board:** 6 пан, sheet cream **#F5EDDF**, Type-As-Subject (буквы 50-90% кадра), иерархия размеров (L→M→S), **2-Font Lock** (Playfair Display + Inter Mono), text-панели A {01,03,05}, brand_reveal R7, Tier(c) full chrome.
- **infographicMD-board:** 6 пан, sheet cool charcoal, HR-2 цифры 15-40% высоты (мелкие подписи убрать), **HR-5** только `metric_values_from_brief` (["$420","12K","84%"]), пошаговое построение (оси→столбцы→число), Layout C, brand_reveal R5, Tier(b) panel-captions chrome.

→ Забрать: универсальный board_specs JSON + brand_reveal каталог R1-R8 + chess_pattern (позиции текстовых панелей) + per-doctrine sheet-bg/grid.
