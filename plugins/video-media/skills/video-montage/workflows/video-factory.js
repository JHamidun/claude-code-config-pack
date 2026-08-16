export const meta = {
  name: 'video-factory',
  description: 'Конвейер производства ролика: бриф → сценарий и музыка → раскадровка → кадры → сборка → контроль',
  whenToUse: 'Владелец просит сделать ролик, а не отдельную операцию монтажа. Одна задача — весь конвейер ролями, без ручного выбора инструментов.',
  phases: [
    { title: 'Бриф',       detail: 'задача → задание и маршрут сборки' },
    { title: 'Замысел',    detail: 'сценарий и музыка параллельно' },
    { title: 'Раскадровка', detail: 'план кадров по сетке событий' },
    { title: 'Кадры',      detail: 'промпт → генерация → приёмка, волнами по четыре' },
    { title: 'Сборка',     detail: 'монтаж, переходы, титры, сведение' },
    { title: 'Контроль',   detail: 'вердикт без усреднения' },
  ],
};

// --- пути и параметры -----------------------------------------------------------------
// В скрипте нет доступа к диску, времени и случайности: всё, что нужно знать о файловой
// системе, приходит сюда константами и через args, а читают и пишут только агенты.

const HOME = (typeof process !== 'undefined' && process.env && (process.env.USERPROFILE || process.env.HOME)) || '~';
const SK = HOME + '/.claude/skills';
const WORK = String((args && args.workdir) || HOME + '/Videos/video-factory/run');
const ENVELOPE = WORK + '/production.json';
const BRIEF = String((args && args.brief) || 'ролик без описания — восстанови задачу из контекста');
const SECONDS = Number((args && args.seconds) || 35);
const PLATFORM = String((args && args.platform) || 'reels');
const GOAL = String((args && args.goal) || 'watch');
const ROUTE_HINT = (args && args.route) || null;

// Волна агентов. Больше шести одновременно упирается в ограничение сервера: у parallel
// нет параметра параллелизма, поэтому размер волны держим сами.
const WAVE = 4;

// Роли лежат файлами, а не подключаются типом агента. Тип резолвится реестром при
// запуске, и на свежей машине или после перезагрузки окна его может не оказаться —
// тогда падает весь конвейер. Файл на диске есть всегда, поэтому роль вручается
// первой строкой промпта.
const ROLE = (n) => `Твоя роль описана в ${HOME}/.claude/agents/vf-${n}.md — `
  + `прочитай этот файл ПЕРВЫМ ДЕЙСТВИЕМ и работай строго по нему.
`;

const COMMON = `
Ты роль в конвейере производства видео. Работаешь по производственному конверту —
одному JSON-документу, через который роли передают работу друг другу.

КОНВЕРТ: ${ENVELOPE}
РАБОЧАЯ ПАПКА: ${WORK}
СХЕМА КОНВЕРТА: ${SK}/video-montage/schemas/production.schema.json
АРХИТЕКТУРА КОНВЕЙЕРА: ${SK}/video-montage/references/pipeline-architecture.md
КАТАЛОГ ПРИЁМОВ: python ${SK}/video-montage/scripts/techniques.py list --cat <раздел>

ЖЕЛЕЗНЫЕ ПРАВИЛА
1. Пишешь ТОЛЬКО свой раздел конверта. Чужие разделы не трогаешь: над ними параллельно
   работают другие роли, и правка чужого раздела затрёт их работу.
2. Конверт читаешь перед работой и пишешь сразу после — он и есть память конвейера.
   Всё, что не на диске, теряется при обрыве.
3. Идемпотентность: если твой раздел уже заполнен и данные валидны — не переделывай,
   верни skipped: true. Перезапуск не должен платить дважды, особенно за генерацию.
4. Тяжёлое (видео, звук, картинки, длинные тексты) — только на диск. В ответ возвращай
   квитанцию: что сделал, куда положил, сколько получилось.
5. Пустой результат — честный результат. Не смог — скажи прямо, что и почему, не
   подставляй правдоподобное.
6. Числа без первоисточника в работу не берём. Пороги вроде «80% досмотра» — выдумка,
   в каталоге приёмов они отмечены как отвергнутые.

СТЕК (локальный, без демонов и облачных посредников)
  структура ролика   ${SK}/video-montage/scripts/reel_structure.py
  каталог приёмов    ${SK}/video-montage/scripts/techniques.py
  карта трека        ${SK}/video-editor/scripts/music_map.py
  переходы           ${SK}/video-editor/scripts/transitions.py и transitions_pro.py
  шрифты             ${SK}/video-editor/scripts/font_catalog.py
  промпт кадра       ${SK}/manus-slides/scripts/build_visual_prompt.py
  генерация          ${SK}/video-generation/scripts/direct_video.py  (Veo 3.1, Sora 2 напрямую)
`;

// Квитанция: роли возвращают отчёт о работе, а не саму работу. Иначе состояние прогона
// раздувается до десятков тысяч токенов и тянет за собой контекст при возобновлении.
const RECEIPT = {
  type: 'object',
  additionalProperties: false,
  required: ['ok', 'summary'],
  properties: {
    ok: { type: 'boolean', description: 'раздел заполнен и валиден' },
    skipped: { type: 'boolean', description: 'уже было сделано, работа не переделывалась' },
    summary: { type: 'string', description: 'что сделано, одной-двумя фразами' },
    counts: { type: 'object', additionalProperties: true, description: 'счётчики: кадров, реплик, склеек' },
    files: { type: 'array', items: { type: 'string' }, description: 'что легло на диск' },
    problems: { type: 'array', items: { type: 'string' }, description: 'что помешало или требует решения владельца' },
  },
};

const SHOT_RESULT = {
  type: 'object',
  additionalProperties: false,
  required: ['id', 'status'],
  properties: {
    id: { type: 'string' },
    status: { type: 'string', enum: ['ready', 'rejected', 'failed', 'skipped'] },
    output: { type: 'string', description: 'путь к файлу кадра' },
    attempts: { type: 'integer' },
    reject_reason: { type: 'string', description: 'что именно не так — конкретно, не «плохо»' },
    note: { type: 'string' },
  },
};

const QC_RESULT = {
  type: 'object',
  additionalProperties: false,
  required: ['verdict', 'checks'],
  properties: {
    verdict: { type: 'string', enum: ['pass', 'revise', 'fail'] },
    checks: {
      type: 'array',
      items: {
        type: 'object',
        additionalProperties: false,
        required: ['name', 'verdict'],
        properties: {
          name: { type: 'string' },
          verdict: { type: 'string', enum: ['pass', 'warn', 'fail'] },
          detail: { type: 'string' },
          technique: { type: 'string' },
        },
      },
    },
    revise_targets: { type: 'array', items: { type: 'string' } },
    watched: { type: 'string', description: 'какие кадры смотрел глазами и на чём' },
  },
};

// --- фаза 1: бриф ---------------------------------------------------------------------

phase('Бриф');

const brief = await agent(`${ROLE('brief')}${COMMON}
Ты приёмщик задачи. Заполняешь разделы brief и route конверта.

ЗАДАЧА ВЛАДЕЛЬЦА: ${BRIEF}
Длительность: ${SECONDS} с. Площадка: ${PLATFORM}. Цель: ${GOAL}.
${ROUTE_HINT ? 'Владелец указал маршрут: ' + ROUTE_HINT : 'Маршрут выбираешь сам по признакам из архитектуры.'}

Создай рабочую папку ${WORK}, если её нет, и запиши конверт в ${ENVELOPE}.
Рутинные решения принимай сам и записывай — переспрашивать нечего. Недостающее, без чего
работать можно, вынеси в problems списком.`,
  { label: 'бриф', phase: 'Бриф', schema: RECEIPT }
).catch(() => null);

if (!brief || !brief.ok) {
  return { error: 'бриф не собран', detail: brief && brief.summary, problems: (brief && brief.problems) || [] };
}
log(`бриф готов: ${brief.summary}`);

// --- фаза 2: сценарий и музыка параллельно --------------------------------------------
// Барьер здесь честный: раскадровке нужны И структура, И сетка долей. Но между собой
// сценарий и музыка не зависят, поэтому идут одновременно.

phase('Замысел');

const [script, sound] = await parallel([
  () => agent(`${ROLE('screenwriter')}${COMMON}
Ты сценарист. Заполняешь разделы structure и script.
Структуру строй инструментом reel_structure.py, а не на глаз — он знает ограничения
площадок и не подставляет числа без первоисточника. Реплики привязывай ко времени и к
блокам; поле on_screen не пропускай, по нему работает раскадровщик.`,
    { label: 'сценарий', phase: 'Замысел', schema: RECEIPT }
  ).catch(() => null),

  () => agent(`${ROLE('sound')}${COMMON}
Ты звукорежиссёр. Заполняешь раздел audio: музыка, карта трека, сетка склеек, озвучка.
Карта трека нужна раскадровщику раньше, чем кадры, — не тяни.
Чужой трек в публикуемый ролик не кладёшь никогда: площадки распознают и глушат звук.
Реальные тайминги озвучки возвращай в конверт — они задают настоящий хронометраж.`,
    { label: 'звук', phase: 'Замысел', schema: RECEIPT }
  ).catch(() => null),
]);

if (!script || !script.ok) {
  return { error: 'сценарий не собран', detail: script && script.summary };
}
log(`сценарий: ${script.summary}` + (sound && sound.ok ? ` · звук: ${sound.summary}` : ' · звук не готов, идём без сетки долей'));

// --- фаза 3: раскадровка --------------------------------------------------------------

phase('Раскадровка');

const board = await agent(`${ROLE('storyboard')}${COMMON}
Ты раскадровщик. Заполняешь раздел shots.
Каждой точке из structure.event_times должно соответствовать событие. Если задана
музыка — границы кадров ложатся на доли из audio.cut_grid.
Верни в counts число кадров и распределение по блокам.`,
  { label: 'раскадровка', phase: 'Раскадровка', schema: RECEIPT }
).catch(() => null);

if (!board || !board.ok) {
  return { error: 'раскадровка не собрана', detail: board && board.summary };
}
const shotCount = Number((board.counts && (board.counts.shots || board.counts.кадров)) || 0);
log(`раскадровка: ${board.summary} (кадров ${shotCount || '?'})`);

// --- фаза 4: кадры волнами ------------------------------------------------------------
// Кадры независимы, но одновременно больше волны запускать нельзя — упрёмся в
// ограничение сервера. Поэтому цикл по волнам, а внутри волны — parallel.

phase('Кадры');

const total = shotCount > 0 ? shotCount : 8;
const ids = [];
for (let i = 1; i <= total; i++) ids.push('shot_' + String(i).padStart(2, '0'));

const shots = [];
for (let start = 0; start < ids.length; start += WAVE) {
  const slice = ids.slice(start, start + WAVE);

  const wave = await parallel(slice.map((id) => () =>
    agent(`${ROLE('operator')}${COMMON}
Ты промптер и оператор для ОДНОГО кадра: ${id}.

Шаг 1 — промпт. Собери его сборщиком build_visual_prompt.py по полям кадра из конверта.
Постановку задавай измеримо: не «рядом», а «в метре от машины», «ладонь на капоте».
Направление корпуса и направление взгляда — разные поля, заполняй оба.
Сложное действие начинай уже начатым: «уже в середине замаха», а не «замахивается».

Шаг 2 — генерация. direct_video.py, движок из route.engines.video или по задаче:
черновой прогон лёгким движком, финал — тяжёлым.

Шаг 3 — приёмка СРАЗУ. Достань полосу кадров через ffmpeg и посмотри глазами: то ли в
кадре, не сползла ли оптика к концу, на месте ли люди, нет ли текста-абракадабры.
Годен — status ready. Не годен — status rejected и в reject_reason напиши, ЧТО именно
не так, конкретно.

Повторяешь не больше трёх раз, меняя ОДНУ строку промпта за раз. Не вышло — честно
rejected, конвейер решит, что делать; не жги деньги вслепую.

Если кадр уже готов (status ready и файл на месте) — верни status skipped.
Обнови свой элемент shots в конверте.`,
      { label: id, phase: 'Кадры', schema: SHOT_RESULT }
    ).catch(() => null)
  ));

  const ok = wave.filter(Boolean);
  shots.push(...ok);
  const ready = ok.filter((s) => s.status === 'ready' || s.status === 'skipped').length;
  log(`кадры ${start + 1}–${start + slice.length}: готово ${ready}/${slice.length}`);
}

const ready = shots.filter((s) => s.status === 'ready' || s.status === 'skipped');
const bad = shots.filter((s) => s.status === 'rejected' || s.status === 'failed');
log(`кадры всего: готово ${ready.length}, брак ${bad.length}, потеряно ${ids.length - shots.length}`);

if (ready.length === 0) {
  return {
    error: 'ни один кадр не получился',
    rejected: bad.map((s) => ({ id: s.id, reason: String(s.reject_reason || '').slice(0, 200) })),
  };
}

// --- фаза 5: сборка -------------------------------------------------------------------

phase('Сборка');

const cut = await agent(`${ROLE('editor')}${COMMON}
Ты монтажёр. Заполняешь раздел edit и собираешь ролик.
Готовых кадров: ${ready.length}${bad.length ? `, брака ${bad.length} — эти места закрывай перекрытием или удлинением соседнего кадра` : ''}.
Склейки — по сетке audio.cut_grid, на дропах склейка обязательна.
Переходов два-три вида на весь ролик, длительность либо 0,15–0,25 с, либо 0,6–1,0 с.
Шрифт титров подбирай font_catalog.py под роль и с проверкой кириллицы.
Перед сдачей посмотри полосы кадров вокруг стыков глазами.
Путь готового ролика запиши в edit.output и верни в files.`,
  { label: 'монтаж', phase: 'Сборка', schema: RECEIPT }
).catch(() => null);

if (!cut || !cut.ok) {
  return { error: 'ролик не собран', detail: cut && cut.summary, ready: ready.length, rejected: bad.length };
}
log(`смонтировано: ${cut.summary}`);

// --- фаза 6: контроль -----------------------------------------------------------------
// Проверяющий смотрит свежим взглядом и не является тем, кто собирал: роль, которая
// проверяет свою работу, подтверждает её.

phase('Контроль');

const qc = await agent(`${ROLE('qc')}${COMMON}
Ты контроль качества. Заполняешь раздел qa.
Проверь готовый ролик по каталогу приёмов: крючок, перехват, темп, однообразие, стыки,
переходы, выдача, титры, длина, звук.
Оценки НЕ усредняешь: любой fail делает общий вердикт fail. Провал по одному измерению
не должен маскироваться хорошими остальными.
Смотри глазами: доставай полосы кадров вокруг крючка и каждого стыка. Заключение без
просмотра кадров недействительно.
Если вердикт revise — перечисли в revise_targets ТОЧНО те кадры или блоки, что надо
переделать: лишний помеченный кадр стоит настоящих денег.`,
  { label: 'контроль', phase: 'Контроль', schema: QC_RESULT, effort: 'high' }
).catch(() => null);

const fails = qc && Array.isArray(qc.checks) ? qc.checks.filter((c) => c.verdict === 'fail') : [];
log(`контроль: ${qc ? qc.verdict : 'не отработал'}${fails.length ? `, провалов ${fails.length}` : ''}`);

return {
  envelope: ENVELOPE,
  workdir: WORK,
  video: (cut.files || []).slice(0, 3),
  shots: { total: ids.length, ready: ready.length, rejected: bad.length },
  rejected: bad.map((s) => ({ id: s.id, reason: String(s.reject_reason || '').slice(0, 200) })).slice(0, 20),
  qc: qc ? {
    verdict: qc.verdict,
    fails: fails.map((c) => `${c.name}: ${String(c.detail || '').slice(0, 160)}`),
    revise: qc.revise_targets || [],
    watched: String(qc.watched || '').slice(0, 200),
  } : { verdict: 'не проверено' },
  problems: []
    .concat((brief.problems || []), (script.problems || []), ((sound && sound.problems) || []),
            (board.problems || []), (cut.problems || []))
    .slice(0, 20),
};
