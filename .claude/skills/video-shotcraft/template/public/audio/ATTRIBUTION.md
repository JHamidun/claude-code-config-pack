# Звук шаблона — происхождение каждого файла

В этом каталоге 11 mp3, и их зовёт по именам код шаблона
(`template/src/aifl/Main.tsx`). Все одиннадцать — **Mixkit Sound Effects Free
License**: использование, в том числе коммерческое, без указания авторства и без
оплаты; запрещено перепродавать сами звуки как звуковую библиотеку.
Условия: <https://mixkit.co/license/#sfxFree>.

## Как этот список получен (23.08.2026)

Раньше по шести файлам из одиннадцати источник считался утраченным: в
`assets/audio/ATTRIBUTION.md` пять из них помечены «无法反查，商用前须确认»
(«не восстанавливается, перед коммерческим использованием подтвердить»), а
шестой, `impact-cine.mp3`, апстрим у себя удалил.

Источник восстановлен сверкой байтов, а не догадкой: каталог Mixkit обойдён по
категориям (388 файлов), каждый скачан, посчитан sha256 и сопоставлен с
файлами этого каталога. **Совпали все 11 — байт в байт.** Пять уже
задокументированных совпали с теми самыми URL, что записаны в
`assets/audio/ATTRIBUTION.md`, — это и есть проверка самого метода: если бы
сверка врала, она бы врала и на них.

Длительность и размер каждого файла сходятся с карточкой Mixkit — ещё одна
независимая сверка (например, `keyboard.mp3` — 513 831 байт и 0:19 у обоих).

## Таблица

| Файл | Байт | Длит. | Название у Mixkit | URL |
|---|---|---|---|---|
| `click-camera.mp3` | 14 406 | 0:01 | Camera shutter click | https://assets.mixkit.co/active_storage/sfx/1133/1133-preview.mp3 |
| `impact-cine.mp3` | 115 904 | 0:04 | Cinematic whoosh deep impact | https://assets.mixkit.co/active_storage/sfx/1143/1143-preview.mp3 |
| `keyboard.mp3` | 513 831 | 0:19 | Typing on a laptop keyboard | https://assets.mixkit.co/active_storage/sfx/2531/2531-preview.mp3 |
| `pop.mp3` | 15 239 | 0:01 | Long pop | https://assets.mixkit.co/active_storage/sfx/2358/2358-preview.mp3 |
| `riser-cine.mp3` | 145 112 | 0:04 | Cinematic laser gun thunder | https://assets.mixkit.co/active_storage/sfx/1287/1287-preview.mp3 |
| `sparkle.mp3` | 143 743 | 0:04 | Fairy sparkle whoosh | https://assets.mixkit.co/active_storage/sfx/869/869-preview.mp3 |
| `swoosh-quick.mp3` | 27 247 | 0:01 | Fast small sweep transition | https://assets.mixkit.co/active_storage/sfx/166/166-preview.mp3 |
| `transition-snap.mp3` | 19 051 | 0:01 | Fast transitions swoosh | https://assets.mixkit.co/active_storage/sfx/3115/3115-preview.mp3 |
| `transition-soft.mp3` | 41 082 | 0:01 | Air zoom vacuum | https://assets.mixkit.co/active_storage/sfx/2608/2608-preview.mp3 |
| `whoosh-big.mp3` | 71 724 | 0:02 | Air woosh | https://assets.mixkit.co/active_storage/sfx/1489/1489-preview.mp3 |
| `whoosh-fast.mp3` | 57 624 | 0:01 | Fast whoosh transition | https://assets.mixkit.co/active_storage/sfx/1490/1490-preview.mp3 |

Проверить любую строку можно за полминуты: скачать URL и сравнить sha256 с
файлом рядом.

## Правило на будущее

Записывать название и URL **в момент скачивания**. Пакетная загрузка стирает
метаданные, и через месяц остаётся файл без роду и племени: восстановление
выше заняло 388 загрузок и удалось только потому, что весь каталог Mixkit
доступен целиком. С площадкой, где такого обхода нет, это не повторить.

---

## Не путать с большой библиотекой

Полная звуковая библиотека навыка (`assets/audio/sfx/`, 149 файлов) в раздачу
**не входит** — она вырезана при сборке (`_build_plugins.py`, `HEAVY_MEDIA_DIRS`)
из-за объёма. В паке остаются только её описи: `assets/audio/ATTRIBUTION.md` и
`AUDITION-2026-07-27.md`, где записаны названия и URL всех 141 звука. Скачать
их себе можно по этим URL.
