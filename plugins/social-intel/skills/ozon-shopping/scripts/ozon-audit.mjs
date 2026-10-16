#!/usr/bin/env node
/**
 * Командная строка к Ozon: те же данные, что у MCP `ozon-shopping`, но за один вызов и с отсевом подозрительных отзывов.
 * Использует УЖЕ проверенную сборку upstream-сервера (OZON_MCP_DIR, по умолчанию ~/.claude/tools/ozon-shopping-mcp),
 * ничего не скачивает и не ставит. Сессия общая с MCP: %APPDATA%/ozon-shopping-mcp/session.json.
 *
 *   node ozon-audit.mjs search "беспроводная мышь" [--sort rating] [--min 1000] [--max 4000] [--limit 12] [--json]
 *   node ozon-audit.mjs product <ссылка|sku> [--json]
 *   node ozon-audit.mjs reviews <ссылка|sku> [--depth deep|quick] [--limit 30] [--json]   отзывы + отсев накрутки
 *   node ozon-audit.mjs compare <ссылка|sku> <ссылка|sku> ... [--depth deep|quick] [--limit 30] [--keys "вес,подключение"] [--json]
 *   node ozon-audit.mjs health [--live]
 *   node ozon-audit.mjs setup [--timeout 120]                            окно браузера: проверку Ozon проходят руками
 *
 * deep (по умолчанию): три выборки отзывов на товар (обычная, самые новые пятёрки, самые низкие), три запроса; quick: одна.
 * Всё, что приходит с Ozon, чужой недоверенный текст: он чистится, режется, проверяется на «команды ассистенту»
 * (найденное вырезается) и печатается как ДАННЫЕ. Команд, меняющих что-либо на Ozon, нет.
 */
import { resolve } from 'node:path'
import { clean } from './review-audit.mjs'
import {
  makeSanitizer, viewSearch, viewProduct, viewCompareEntry, explainError, redactionNotice,
  renderSearch, renderProduct, renderReviews, renderCompare,
} from './ozon-views.mjs'
import { loadUpstream, loadReviews, DEFAULT_DIR } from './ozon-upstream.mjs'

const DIR = resolve(process.env.OZON_MCP_DIR || DEFAULT_DIR)

function parseArgs(argv) {
  const flags = {}
  const rest = []
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (a.startsWith('--')) {
      const key = a.slice(2)
      if (['json', 'live'].includes(key)) flags[key] = true
      else { flags[key] = argv[i + 1]; i++ }
    } else rest.push(a)
  }
  return { flags, rest }
}

const intFlag = (v, fallback, lo, hi) => {
  if (v === undefined) return fallback
  const n = Number(v)
  if (!Number.isInteger(n) || n < lo || n > hi) throw new Error(`значение «${v}» вне диапазона ${lo}..${hi}`)
  return n
}

const depthFlag = (v) => {
  const d = v === undefined ? 'deep' : v
  if (d !== 'deep' && d !== 'quick') throw new Error('--depth: deep или quick')
  return d
}

const out = (flags, view, render) => console.log(flags.json ? JSON.stringify(view, null, 2) : render(view))

async function cmdSearch(client, { flags, rest }, S) {
  const query = rest.join(' ').trim()
  if (!query) throw new Error('нужен поисковый запрос')
  const input = {
    query,
    sort: flags.sort || 'popular',
    priceMin: flags.min !== undefined ? intFlag(flags.min, 0, 0, 99_999_999) : undefined,
    priceMax: flags.max !== undefined ? intFlag(flags.max, 0, 0, 99_999_999) : undefined,
    limit: intFlag(flags.limit, 12, 1, 36),
  }
  out(flags, viewSearch(await client.search(input), input, S), renderSearch)
}

async function cmdProduct(client, { flags, rest }, S) {
  if (!rest[0]) throw new Error('нужна ссылка или sku товара')
  out(flags, viewProduct(await client.product(rest[0]), S), renderProduct)
}

async function cmdReviews(client, { flags, rest }) {
  if (!rest[0]) throw new Error('нужна ссылка или sku товара')
  const view = await loadReviews(client, rest[0], { limit: intFlag(flags.limit, 30, 1, 30), depth: depthFlag(flags.depth) })
  out(flags, view, renderReviews)
}

async function cmdCompare(client, { flags, rest }, S) {
  if (rest.length < 1) throw new Error('нужна хотя бы одна ссылка или sku')
  if (rest.length > 8) throw new Error('за раз не больше 8 товаров (запросы идут по очереди с паузами)')
  const limit = intFlag(flags.limit, 30, 1, 30)
  const depth = depthFlag(flags.depth)
  const keys = (flags.keys || '').split(',')
  const entries = []
  for (const ref of rest) {
    try {
      const product = viewProduct(await client.product(ref), S)
      const reviews = await loadReviews(client, ref, { limit, depth })
      entries.push(viewCompareEntry(ref, product, reviews))
    } catch (e) {
      entries.push(viewCompareEntry(ref, null, null, explainError(e)))
    }
  }
  out(flags, entries, (v) => renderCompare(v, keys))
}

async function cmdHealth(client, { flags }) {
  const h = await client.health(!!flags.live)
  if (h.live && h.live.error) h.live.error = clean(h.live.error, 300)
  console.log(JSON.stringify(h, null, 2))
}

async function cmdSetup(client, { flags }) {
  const timeout = intFlag(flags.timeout, 120, 30, 300)
  console.error('Открою окно Chrome. Если Ozon показывает проверку, пройдите её в этом окне.')
  console.log(JSON.stringify(await client.setup(timeout * 1000, (m) => console.error(m)), null, 2))
}

const COMMANDS = { search: cmdSearch, product: cmdProduct, reviews: cmdReviews, compare: cmdCompare, health: cmdHealth, setup: cmdSetup }

async function main() {
  const [command, ...argv] = process.argv.slice(2)
  if (!command || !COMMANDS[command]) {
    console.error('Команды: ' + Object.keys(COMMANDS).join(', ') + '\nПодробнее: см. шапку файла.')
    process.exit(command ? 2 : 0)
  }
  const args = parseArgs(argv)
  const S = makeSanitizer()
  let client
  try {
    client = await loadUpstream(DIR)
    await COMMANDS[command](client, args, S)
  } catch (e) {
    const known = e && typeof e === 'object' && typeof e.code === 'string'
    const x = known ? explainError(e) : { code: 'ERROR', message: clean(e && e.message ? e.message : String(e), 400) }
    console.error(`Ошибка: ${x.code}: ${x.message}`)
    process.exitCode = 1
  } finally {
    if (client) await client.shutdown().catch(() => undefined)
    const notice = redactionNotice(S)
    if (notice) console.error(notice)
  }
}

await main()
