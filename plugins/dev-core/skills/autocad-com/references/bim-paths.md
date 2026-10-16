# Путь к BIM: код → IFC → CAD, код внутри Revit, российские аналоги (разведка 09.09.2026, проверена опровергателями)

Контекст: заказчик, который **работает в Revit**, прислал альбом СИП-дома (22 листа: 2 плана, 4 фасада,
2 разреза, 2 спецификации, 12 картинок 3D) и спросил «получится ли так же» и «хочу через Revit/AutoCAD».
Полный разбор — `${WORKSPACE}/interior-ai-demo/research/house_kuznetsovka/analysis/house_album_analysis.md`.
Здесь — то, что переживёт этот проект. Пометки: (П) — подтверждено первоисточником, (Г) — предположение.

**Главное правило выбора пути: инструмент заказчика — вводная, а не предмет обсуждения.** Работает в Revit —
основной путь C (скрипт внутри Revit), A — PDF/DXF без Revit для сверки и показа, B — обмен моделью через IFC.
Лицензии, санкции и «легальность» его софта в тексты заказчику не выносить: 16.09.2026 такой абзац в черновике
для клиента, работающего в Revit, владелец назвал отсебятиной.

## Чем альбом дома отличается от альбома интерьера

Объёмная геометрия: уровни (−219 … +5986), кровля с уклоном и свесами, фронтоны, терраса под скатом, сваи.
Фасады и разрезы — **проекции 3D-модели** (видны дальние столбы и каркас фронтона сквозь чердак), таблицы —
её подсчёты. Сетка осей (наружные — по наружной грани, внутренние — по центру перегородки), система отметок,
типы стен с послойным составом («профили»: ГКЛ 12 + СИП 119 + ГКЛ 12), спецификации проёмов с эскизами
створок и сечений профилей. В нашем холсте нет функций осей и 3D-модели как источника видов — это и есть
работа при переходе на дома; лист, штамп, DXF/PDF/XLSX, реестр, валидатор переносятся как есть.

Признак «альбом сделан из 3D в CAD, а не руками»: «неровные» размеры 2093/2293/2745/2722/2991 — измеренная
геометрия, не проектные номиналы. Одно и то же на разных листах даёт разные числа (2745 vs 2722) — ловится
валидатором «одна отметка на всех листах».

## Три пути (сводка)

| | A. Свой движок (SVG/DXF) | B. Код → IFC → CAD | C. Код внутри Revit |
|---|---|---|---|
| Нужен CAD | нет | да (Revit/ArchiCAD/Renga) | да, Revit 2021+ |
| Что получает заказчик | PDF-альбом, DXF, SVG, XLSX, 3D-html | IFC-модель + виды из CAD; листы руками/скриптом | RVT с листами |
| Фасады/разрезы | считаем сами (сечение тел плоскостью; для прямоугольного дома хватает правил) | режет CAD | режет Revit |
| Штамп ГОСТ | наш | шаблон CAD | ADSK-шаблон |
| Первый альбом дома (Г) | 2–3 недели | 3–5 дней модель + 1–2 недели CAD | 3–4 недели |
| Главное предположение | скорость разрезов из 3D | качество импорта на наших данных | шаблон заказчика: штамп, типы стен, семейства |

Выбор — по инструменту заказчика: работает в Revit → **C основной** (+A для PDF/DXF, +B для обмена); CAD нет или
нужен результат без CAD → **A** (+B как экспорт той же модели в IFC).

## B. IFC из Python — что подтверждено (П)

- `pip install ifcopenshell` — 0.8.5 (13.04.2026), Python 3.10–3.14, CAD не нужен.
- Каркас: `project.create_file` → `root.create_entity(IfcProject/IfcSite/IfcBuilding/IfcBuildingStorey)` →
  `unit.assign_unit` → `context.add_context(Model, Body)` → `aggregate.assign_object` → стены `IfcWall` +
  `geometry.add_wall_representation(length, height, thickness)` → `spatial.assign_container`.
- Проёмы: `feature.add_feature(IfcOpeningElement, element=wall)` (IfcRelVoidsElement) →
  `feature.add_filling(opening, element=door)`; двери/окна — `add_door_representation` /
  `add_window_representation`. Перекрытия — `add_slab_representation(depth, x_angle)` (уклон в радианах).
  **Функции кровли в API нет**: IfcRoof + наклонные IfcSlab через `x_angle` либо `add_profile_representation` /
  `add_mesh_representation`.
- Чтобы CAD поднял стену как нативную Wall: слоистая стена в **два шага** — `IfcMaterialLayerSet` на тип
  (`add_material_set` + `add_layer` + `edit_layer(LayerThickness)` + `assign_material(products=[wall_type],
  type="IfcMaterialLayerSet")`) и обязательный `IfcMaterialLayerSetUsage` на экземпляр + ось стены
  `add_axis_representation`; геометрия SweptSolid (`IfcExtrudedAreaSolid`), лучше `IfcWallStandardCase`.
  Меш/BREP в ArchiCAD 27–29 становится Morph/Object, не Wall.
- Revit «Link IFC» (2026/2027): элементы приходят DirectShape, менять нельзя, в связанную стену дверь не
  вставить; виды/листы/спецификации над связью — обычные. Revit «Open IFC»: нативные стены/плиты там, где
  экструзии (`IfcWallStandardCase`), рекомендован IFC2x3 Coordination View 2.0, маппинг классов —
  `importIFCClassMapping.txt`. ArchiCAD 27–29: пресет «Geometry Conversion for IFC Import» — экструзии →
  параметрические Wall/Slab.
- Без CAD: `IfcConvert in.ifc -yv out.svg --section-height-from-storeys --auto-section --auto-elevation
  --scale 1:100 --door-arcs --print-space-areas --svg-poly` — планы/разрезы/фасады в SVG без штампа и таблиц;
  Bonsai 0.8.5 (Blender) умеет листы с титульными блоками, документация чертежей — «Work in Progress».

## C. Revit из кода — что подтверждено (П)

- pyRevit v6.5.5 (25.08.2026, GPL-3.0), Revit 2025/2026 (.NET 8) и 2027 (.NET 10). Движок по умолчанию —
  **IronPython 2.7.12** («99.9% инструментов только на нём»); CPython 3.12 через шебанг `#! python3`, но
  `pyrevit.forms` под ним не работает и после Reload скрипты падают до перезапуска. RevitPythonShell 2.2.0
  (04.2025) мёртв, 2027 не поддержан. Dynamo 4.0 (Revit 2027) — PythonNet3/CPython 3.11 по умолчанию.
- API: `Wall.Create(doc, curve, wallTypeId, levelId, height, offset, flip, structural)`;
  `Floor.Create(doc, IList<CurveLoop>, floorTypeId, levelId, …)`; кровля —
  `doc.Create.NewFootPrintRoof(footPrint, level, roofType, out mapping)` + `set_DefinesSlope/set_SlopeAngle`
  (значение = rise/run, 0,5 ≈ 26,6°); **длины в футах, углы в радианах**. Виды: `ViewPlan.Create`,
  `ViewSection.CreateSection(doc, vftId, bbox)`, `View3D.CreateIsometric`, `ViewSheet.Create(doc,
  titleBlockTypeId)` (без штампа — `ElementId.InvalidElementId`), `Viewport.Create(doc, sheetId, viewId,
  XYZ)` — координаты листа **в футах**, `ScheduleSheetInstance.Create`.
- Штамп ГОСТ: ADSK-шаблоны (BIM2B), АР `ADSK_RU_ШаблонПроекта_АР_r2021_v2.2.1.rte` открывается в 2021+,
  сборок под 2025/2026 нет, макросы работают только в 2019; семейство `ADSK_ОсновнаяНадпись` (формы 3/5/6);
  бесплатные основные надписи ф.3/5/6 у В. Муратова (2017/2019).
- **Headless у десктопного Revit нет** (с 2022 UI-less инициализация — нарушение ToS): скрипт работает в
  открытом Revit, запускается кнопкой pyRevit или из Dynamo. Единственный официальный headless — облачный
  APS Automation API: только .NET-аддины (pyRevit не запускается),
  $3 за 12 минут = $15/час, 300 минут в месяц бесплатно. RevitBatchProcessor v1.13.0-beta (2015–2027,
  IronPython 2.7) — нужен установленный Revit, автор проект не поддерживает.
- Фон для НАШИХ решений (заказчику не выносить): Autodesk запретил использование российскими компаниями с 20.03.2024 (12-й пакет ЕС,
  ст. 5n(2b)), с июля 2024 блокирует аккаунты купивших через третьи страны/VPN. Требования РФ: ПП 331
  (обязательная ТИМ для жилья по 214-ФЗ с 01.07.2024, малоэтажка с 01.01.2025), Указ 166 (иностранное ПО на
  значимых объектах КИИ с 01.01.2025), ПП 1875 (нацрежим госзаказа).
- Российские аналоги с API: **Renga** — COM API v2.50, плагины C#/C++, Python — внешняя автоматизация через
  pywin32 (`help.rengabim.com/api`, `github.com/RengaSoftware/SampleScripts`); **nanoCAD BIM Конструкции** —
  SDK на C# с 23.1; **Model Studio CS** — CADLib API .NET. Умеют ли их API листы со штампом и виды из
  скрипта — не проверено (Г).

## Курс «РАМ-Проект» (ramproject.ru/kurs) — что это, для сравнения

Только Revit, ручное моделирование: каркасный дом (70 уроков, 28 ч, 14 000 ₽), газобетон (71 урок, 32 ч),
силовой каркас, фундамент; марки АР+КР; Dynamo/API/скриптов нет, «автоматизация» = готовый шаблон Revit; ИИ —
только для визуализации. Учебный альбом каркасника: АР 17 листов + КР 26 листов. Чем отличается скриптовый
путь: та же модель и листы в Revit строятся из файла с параметрами, следующий дом — новый файл, а не модель с
нуля. Курс, который заказчик прислал как ориентир, в клиентском тексте не критиковать.

## Что спросить у заказчика, прежде чем обещать дом

1. В какой программе сделан исходный альбом и есть ли исходник (не PDF): по листам софт не определяется —
   признаки K3-Коттедж / SketchUp + плагин / Renga.
2. В чём работает и что нужно на выходе; если Revit — версия и шаблон проекта (штамп, типы стен, семейства
   окон и дверей).
3. Один дом или поток — генератор окупается со второго-третьего объекта.
4. Типы домов дальше (СИП / каркас / брус) — от этого справочник стен.
5. ТЗ по тому, чего на листах нет: уклон кровли, тип фундамента, число ступеней.

Источники — раздел «Источники» в `house_album_analysis.md` (pyRevit releases, revitapidocs 2026/2027,
blog.autodesk.io, bim2b.ru, aps.autodesk.com, docs.ifcopenshell.org, help.graphisoft.com, help.rengabim.com,
adsknews.autodesk.com, publication.pravo.gov.ru).
