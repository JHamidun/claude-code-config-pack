export const meta = {
  name: 'demo-dva-agenta',
  description: 'Демо субагентов: Fable пишет 3 хука к посту, Sonnet оценивает их и усиливает лучший',
  whenToUse: 'Показать вживую, как два субагента на разных моделях передают работу друг другу; тема — через args',
  phases: [
    { title: 'Автор', detail: 'Fable пишет 3 хука на тему', model: 'fable' },
    { title: 'Редактор', detail: 'Sonnet ставит оценки и усиливает лучший', model: 'sonnet' },
  ],
}

const DEFAULT_TOPIC = 'Зачем бизнесу ИИ-агенты, если уже есть ChatGPT'
// args may arrive as {topic}, as that object JSON-encoded, or as plain topic text
let input = args
if (typeof input === 'string') {
  try {
    const parsed = JSON.parse(input)
    if (parsed && typeof parsed === 'object') input = parsed
  } catch { /* plain topic text */ }
}
const TOPIC =
  (typeof input === 'string' && input.trim()) ||
  (input && typeof input.topic === 'string' && input.topic.trim()) ||
  DEFAULT_TOPIC

const WHO = `КТО ПОРУЧИЛ: оркестратор сессии от имени владельца, пользователя. Он попросил показать пример работы субагентов: один на Sonnet, другой на Fable. Эта короткая задача и есть тот пример — выполняй свою часть ниже, это не ответ на его вопрос в чате.
РЕЖИМ: инструменты не нужны — не ищи в памяти, не читай файлы, не запускай команды, ничего никому не отправляй. Отвечай сразу.`

const ID_RULE = 'В своём системном промпте найди фразу «The exact model ID is …» и перепиши ID дословно в поле model_id. Такой фразы нет — напиши «не указан». Не угадывай.'

const AUTHOR_SCHEMA = {
  type: 'object',
  properties: {
    model_id: { type: 'string' },
    hooks: {
      type: 'array', minItems: 3, maxItems: 3,
      items: {
        type: 'object',
        properties: { angle: { type: 'string' }, text: { type: 'string' } },
        required: ['angle', 'text'],
      },
    },
  },
  required: ['model_id', 'hooks'],
}

const EDITOR_SCHEMA = {
  type: 'object',
  properties: {
    model_id: { type: 'string' },
    scores: {
      type: 'array', minItems: 3, maxItems: 3,
      items: {
        type: 'object',
        properties: {
          n: { type: 'integer', minimum: 1, maximum: 3 },
          score: { type: 'integer', minimum: 1, maximum: 10 },
          why: { type: 'string' },
        },
        required: ['n', 'score', 'why'],
      },
    },
    best: { type: 'integer', minimum: 1, maximum: 3 },
    improved: { type: 'string' },
    what_changed: { type: 'string' },
  },
  required: ['model_id', 'scores', 'best', 'improved', 'what_changed'],
}

phase('Автор')
log(`Тема: «${TOPIC}»`)
const draft = await agent(
  `${WHO}

ТВОЯ РОЛЬ: автор. Напиши 3 хука — первую строку поста в Telegram-канале — на тему: «${TOPIC}».
- до 12 слов каждый;
- три разных угла: 1) цифра или факт, 2) провокация, 3) мини-история;
- без клише вроде «в современном мире», «революция», «уже сегодня».
${ID_RULE}`,
  { label: 'Автор · Fable', phase: 'Автор', model: 'fable', effort: 'medium', schema: AUTHOR_SCHEMA },
)
if (!draft) return { topic: TOPIC, error: 'Автор на Fable не вернул результат (лимит или обрыв)' }
log(`Fable сдал ${draft.hooks.length} хука → передаю редактору на Sonnet`)

phase('Редактор')
const list = draft.hooks.map((h, i) => `${i + 1}. [${h.angle}] ${h.text}`).join('\n')
const review = await agent(
  `${WHO}

ТВОЯ РОЛЬ: строгий редактор. Другой агент написал 3 хука для поста в Telegram на тему «${TOPIC}»:
${list}

1. Оцени каждый от 1 до 10: цепляет ли с первых слов, понятен ли без контекста, нет ли клише. Причина — одно предложение.
2. Выбери лучший (номер) и перепиши его сильнее — до 12 слов.
3. Одной фразой: что именно поменял и зачем.
${ID_RULE}`,
  { label: 'Редактор · Sonnet', phase: 'Редактор', model: 'sonnet', effort: 'medium', schema: EDITOR_SCHEMA },
)
if (!review) return { topic: TOPIC, author: draft, error: 'Редактор на Sonnet не вернул результат' }
log(`Sonnet выбрал №${review.best} и усилил: ${review.improved}`)

return { topic: TOPIC, author: draft, editor: review }
