# UGC-flow — 11 sub-agents (полная экосистема ugc-*)

Общий конвейер: product-analyzer → ugc-character (text2image_soul_v2) → *-board (gpt_image_2, слот-стрип) → *-clip
(seedance_2_0, @Image-привязки) → montage. Слот-борд = горизонтальный стрип, делённый на вертикальные 9:16 слоты
(последовательные моменты одного 15с клипа). Lip-sync на «говорящих» кадрах, VO на close-up/macro.

1. **ugc-character** → промпт для `text2image_soul_v2`. Матрица «категория товара→гардероб» (премиум-косметика=шёлк-блуза, фитнес=спорт-топ). Нейтрал фон, мягкий оконный свет, UGC-vlog skin texture. Без продукта в руках.
   `A close-up portrait photo of a [age-band] [gender], [ethnicity], [hair]. Wearing [outfit by category/tier]. Neutral warm blurred apartment bg, soft window light. Shot on high-end smartphone, realistic UGC vlog, authentic skin.`
2. **ugc-board** (3-слот 16:9→3×9:16: Hook→Demo→Conclusion). Лицо/одежда стабильны (из @Image2), продукт = @Image1. `gpt_image_2` промпт с Panel 1/2/3.
3. **ugc-clip** → Seedance. @Image1=board, @Image2=аватар, @Image3=продукт. Cut1/3 = lip-sync, Cut2 (close-up рук) = VO mouth closed. Hard cuts.
4. **ugc-unboxing-board** (4-слот 21:9: Packed→Reveal→Focus→Satisfaction). Slot1 коробка запечатана; дальше убрана. @Image3=коробка.
5. **ugc-unboxing-clip** → Seedance (@Image4=box). Физика веса коробки + шуршание бумаги. Cut1 lip-sync→Cut2 reveal gasp→Cut3 VO macro→Cut4 pose lip-sync.
6. **ugc-tutorial-boards** (4-слот 21:9, рендер текста `Step N — Heading` на каждом слоте, идентичный стиль/позиция).
7. **ugc-tutorial-clip** → Seedance с on-screen `Step N` оверлеями по таймкодам; физика пальцев под тип дозатора.
8. **ugc-try-board** (4-слот: Pre-wear[нейтрал+крафт-пакет]→Wearing[full-body]→Texture Macro[hands-free]→Styled Pose[др. комната]).
9. **ugc-try-clip** → Seedance: Cut2 = graceful 360° twirl (посадка со спины), Cut3 = hands-off macro VO, остальные lip-sync.
10. **ugc-product-boards** (4-слот 21:9 без лица, руки на периферии: Intro→Demo A→Demo B→Hero).
11. **ugc-product-clip** → Seedance @Image2=продукт. Без lip-sync/рта; камера-движение вокруг; VO `[voice_gender]` синхрон с гендером рук. Cut1 approach→Cut2 hands-only→Cut3 macro→Cut4 static hero+light-bloom.

→ Забрать: слот-борд паттерн (1 кадр = N моментов), lip-sync↔VO распределение по типам кадров, @Image-привязки, UGC канон-арки.
