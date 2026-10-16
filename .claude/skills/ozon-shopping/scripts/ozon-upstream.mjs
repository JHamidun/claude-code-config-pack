/**
 * Слой ввода-вывода: подключает проверенную сборку upstream-сервера (OZON_MCP_DIR) и умеет брать отзывы в трёх порядках.
 * Единственное, что мы добавляем к upstream: параметр sort из белого списка в пути отзывов (тот же транспорт, тот же разбор,
 * тот же хост). Опирается на внутреннее поле client.session upstream-класса OzonClient: версия зафиксирована проверкой
 * коммита 2ec1c70; при обновлении upstream это место перепроверять (см. references/audit-and-install.md).
 */
import { join, resolve } from 'node:path'
import { homedir } from 'node:os'
import { pathToFileURL } from 'node:url'
import { existsSync } from 'node:fs'
import { viewReviews, viewDeepReviews } from './ozon-views.mjs'

/** Порядки, которые Ozon реально понимает (проверено 12.10.2026): sort=score_asc и sort=score_desc. Другие имена он молча игнорирует. */
export const ORDERS = Object.freeze({ lowest: 'score_asc', highest: 'score_desc' })

// Node не раскрывает «~» в путях (path.resolve('~/x') даёт <текущая папка>/~/x), поэтому домашняя папка берётся явно.
export const DEFAULT_DIR = join(homedir(), '.claude', 'tools', 'ozon-shopping-mcp')

export async function loadUpstream(dirInput) {
  const dir = resolve(dirInput || process.env.OZON_MCP_DIR || DEFAULT_DIR)
  for (const f of ['dist/ozon-client.js', 'dist/config.js', 'dist/parsers.js']) {
    if (!existsSync(join(dir, f))) throw new Error(`не найдена сборка MCP: ${join(dir, f)} (OZON_MCP_DIR). Установка описана в references/audit-and-install.md навыка ozon-shopping.`)
  }
  const imp = (rel) => import(pathToFileURL(join(dir, rel)).href)
  const [{ OzonClient, normalizeProductPath }, { loadConfig }, { parseReviews }] = await Promise.all([
    imp('dist/ozon-client.js'), imp('dist/config.js'), imp('dist/parsers.js'),
  ])
  const client = new OzonClient(loadConfig())
  client.reviewsSorted = async (product, order, limit = 30) => {
    const sort = ORDERS[order]
    if (!sort) throw Object.assign(new Error('unknown review order'), { code: 'INVALID_PRODUCT' })
    const session = client.session
    if (!session || typeof session.requestJson !== 'function') {
      throw Object.assign(new Error('upstream internals changed'), { code: 'OZON_RESPONSE_INVALID' })
    }
    const path = normalizeProductPath(product)   // та же проверка хоста и формы адреса, что у upstream
    return parseReviews(await session.requestJson(`${path}reviews/?sort=${sort}`), limit)
  }
  return client
}

/**
 * Отзывы товара в нескольких порядках. Обычный порядок обязателен (его ошибка проходит наверх), остальные необязательны:
 * не получилось, значит идём дальше с пометкой, а не роняем весь ответ.
 */
export async function reviewSamples(client, product, { limit = 30, lowest = true, highest = true } = {}) {
  const samples = { main: await client.reviews(product, limit), notes: [] }
  if (!lowest && !highest) return samples
  if (typeof client.reviewsSorted !== 'function') {
    samples.notes.push('дополнительные выборки отзывов недоступны: разбор только по обычному порядку Ozon')
    return samples
  }
  const extra = async (name, order) => {
    try { samples[name] = await client.reviewsSorted(product, order, limit) } catch { samples.notes.push(`выборка «${name}» не получена (Ozon отказал или схема изменилась)`) }
  }
  if (lowest) await extra('lowest', 'lowest')
  if (highest) await extra('highest', 'highest')
  return samples
}

/**
 * Дайджест отзывов одного товара: deep это три выборки (обычная, самые новые пятёрки, самые низкие, три запроса),
 * quick это одна обычная (один запрос). Общий для CLI и MCP-фасада, чтобы оба отвечали одинаково.
 */
export async function loadReviews(client, product, { limit = 30, depth = 'deep' } = {}) {
  if (depth === 'quick') return viewReviews(await client.reviews(product, limit))
  return viewDeepReviews(await reviewSamples(client, product, { limit }))
}
