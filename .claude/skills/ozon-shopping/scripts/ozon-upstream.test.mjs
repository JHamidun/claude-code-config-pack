// node --test ozon-upstream.test.mjs
// Слой ввода-вывода проверяется на выдуманной «сборке upstream» во временной папке: настоящего Ozon и браузера нет.
import test from 'node:test'
import assert from 'node:assert/strict'
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { loadUpstream, reviewSamples, loadReviews, ORDERS } from './ozon-upstream.mjs'

const made = []
function stubDir({ session = true } = {}) {
  const dir = mkdtempSync(join(tmpdir(), 'ozon-up-'))
  made.push(dir)
  mkdirSync(join(dir, 'dist'))
  writeFileSync(join(dir, 'package.json'), '{"type":"module"}')
  writeFileSync(join(dir, 'dist', 'config.js'), 'export function loadConfig() { return { cfg: true } }\n')
  writeFileSync(join(dir, 'dist', 'parsers.js'), 'export function parseReviews(json, limit) { return { parsed: json, limit } }\n')
  writeFileSync(join(dir, 'dist', 'ozon-client.js'), `
export function normalizeProductPath(v) {
  if (String(v).includes('evil')) { const e = new Error('The URL is not an Ozon product page.'); e.code = 'INVALID_PRODUCT'; throw e }
  return '/product/' + String(v).replace(/[^a-z0-9]/gi, '') + '/'
}
export class OzonClient {
  constructor(cfg) { this.cfg = cfg; this.requests = []; ${session ? "this.session = { requestJson: async (path) => { this.requests.push(path); return { path } } }" : 'this.session = {}'} }
  async reviews() { return { main: true } }
}
`)
  return dir
}
test.after(() => { for (const d of made) rmSync(d, { recursive: true, force: true }) })

const code = (c) => (e) => e && e.code === c

test('порядки отзывов: только два, оба проверены на живом Ozon; список заморожен', () => {
  assert.deepEqual(ORDERS, { lowest: 'score_asc', highest: 'score_desc' })
  assert.ok(Object.isFrozen(ORDERS))
})

test('reviewsSorted: тот же транспорт и разбор, порядок только из белого списка', async () => {
  const client = await loadUpstream(stubDir())
  const low = await client.reviewsSorted('m-1', 'lowest', 5)
  const high = await client.reviewsSorted('m-1', 'highest')
  assert.deepEqual(client.requests, ['/product/m1/reviews/?sort=score_asc', '/product/m1/reviews/?sort=score_desc'])
  assert.equal(low.limit, 5)
  assert.equal(high.limit, 30)
})

test('reviewsSorted: чужой порядок и чужой адрес отвергаются до запроса', async () => {
  const client = await loadUpstream(stubDir())
  await assert.rejects(client.reviewsSorted('m-1', 'rating_desc; drop'), code('INVALID_PRODUCT'))
  await assert.rejects(client.reviewsSorted('https://evil.example/x', 'lowest'), code('INVALID_PRODUCT'))
  assert.deepEqual(client.requests, [])
})

test('reviewsSorted: если внутренности upstream поменялись, ошибка понятная, а не TypeError', async () => {
  const client = await loadUpstream(stubDir({ session: false }))
  await assert.rejects(client.reviewsSorted('m-1', 'lowest'), code('OZON_RESPONSE_INVALID'))
})

test('нет сборки upstream: сообщение называет OZON_MCP_DIR', async () => {
  await assert.rejects(loadUpstream(join(tmpdir(), 'no-such-ozon-dir-xyz')), /OZON_MCP_DIR/)
})

test('reviewSamples: все три выборки по порядку; отключённые не запрашиваются', async () => {
  const calls = []
  const client = { reviews: async () => (calls.push('main'), { n: 1 }), reviewsSorted: async (p, o) => (calls.push(o), { n: 2 }) }
  const all = await reviewSamples(client, 'x', { limit: 7 })
  assert.deepEqual(calls, ['main', 'lowest', 'highest'])
  assert.deepEqual(Object.keys(all).sort(), ['highest', 'lowest', 'main', 'notes'])
  calls.length = 0
  await reviewSamples(client, 'x', { lowest: false, highest: false })
  assert.deepEqual(calls, ['main'])
})

test('reviewSamples: отказ в дополнительной выборке не роняет ответ и не раскрывает детали ошибки', async () => {
  const client = {
    reviews: async () => ({ n: 1 }),
    reviewsSorted: async (p, o) => { if (o === 'lowest') throw new Error('socket hang up at /home/example/secret'); return { n: 2 } },
  }
  const s = await reviewSamples(client, 'x')
  assert.equal(s.main.n, 1)
  assert.equal(s.highest.n, 2)
  assert.equal(s.lowest, undefined)
  assert.equal(s.notes.length, 1)
  assert.match(s.notes[0], /«lowest» не получена/)
  assert.ok(!/example|socket/.test(s.notes[0]))
})

test('reviewSamples: ошибка обычной выборки идёт наверх, а клиент без reviewsSorted даёт честную пометку', async () => {
  await assert.rejects(reviewSamples({ reviews: async () => { throw Object.assign(new Error('x'), { code: 'SESSION_EXPIRED' }) } }, 'x'), code('SESSION_EXPIRED'))
  const s = await reviewSamples({ reviews: async () => ({ n: 1 }) }, 'x')
  assert.match(s.notes[0], /дополнительные выборки отзывов недоступны/)
  const none = await reviewSamples({ reviews: async () => ({ n: 1 }) }, 'x', { lowest: false, highest: false })
  assert.deepEqual(none.notes, [])
})

test('loadReviews: quick это один запрос без глубокого разбора, deep это три выборки', async () => {
  const calls = []
  const rev = (o) => ({ rating: 4.5, totalReviews: 10, count: 0, reviews: [], ...o })
  const client = { reviews: async () => (calls.push('main'), rev()), reviewsSorted: async (p, o) => (calls.push(o), rev()) }
  const quick = await loadReviews(client, 'x', { depth: 'quick' })
  assert.deepEqual(calls, ['main'])
  assert.equal(quick.deep, undefined)
  calls.length = 0
  const deep = await loadReviews(client, 'x')
  assert.deepEqual(calls, ['main', 'lowest', 'highest'])
  assert.ok(deep.deep)
})
