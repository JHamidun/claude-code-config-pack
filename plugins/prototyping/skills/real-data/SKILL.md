---
name: real-data
description: Подключить прототип к настоящим данным — JSON / CSV / API / GraphQL. Заменить hardcoded mock на live source. Делает прототип демо'абельным с реалистичным content.
when_to_use: После interactive-prototype когда нужно показать на реальных данных. Перед demo инвестору / клиенту. Когда mock «John Doe, 100₽» уже не убедителен.
---

# Real data

Подключить prototype к настоящему source. Не доводить до production-grade — это всё ещё прототип. Цель: достоверная демонстрация.

## 4 уровня connection

| Уровень | Что | Когда |
|---|---|---|
| 1. Static JSON | Скопировать API response в `data.json` | для демо, никаких ключей |
| 2. Public API | Fetch с публичного endpoint | для прототипа без auth |
| 3. Read-only proxy | Backend-proxy с захардкоженным auth | если нужен private API |
| 4. Full integration | Real API + auth | стоп, это уже не прототип |

**Правило:** для прототипа ставь max уровень 2. Если нужно 3+ — это уже не прототип.

## Уровень 1: Static JSON

Самый простой и надёжный.

```bash
# Скопировать данные
curl https://api.real-thing.com/items > data/items.json
```

```jsx
// В прототипе
const [items, setItems] = useState([]);
useEffect(() => {
  fetch('data/items.json')
    .then(r => r.json())
    .then(setItems);
}, []);
```

Pro: работает оффлайн, не зависит от availability API, тестабельно.
Con: данные «застывшие» — не свежие.

## Уровень 2: Public API

Если есть public read-only API:

```jsx
useEffect(() => {
  fetch('https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd')
    .then(r => r.json())
    .then(d => setBtcPrice(d.bitcoin.usd));
}, []);
```

Watch out:
- **CORS** — некоторые API не разрешают cross-origin → нужен proxy
- **Rate limits** — для прототипа `?demo=1` не помогает, не злоупотребляй
- **Stability** — public API могут поменять схему

## Уровень 3: Read-only proxy

Когда public API нет, но есть auth-based.

```js
// scripts/proxy.js (Node Express)
const express = require('express');
const cors = require('cors');
const app = express();

app.use(cors());
app.get('/proxy/items', async (req, res) => {
  const r = await fetch('https://api.real.com/items', {
    headers: { Authorization: `Bearer ${process.env.API_TOKEN}` },
  });
  res.json(await r.json());
});
app.listen(3001);
```

Прототип fetch'ит с `localhost:3001/proxy/items`. Auth не светится в browser.

## Smart placeholders (gap)

Если данных нет — генерируй realistic из schema:

```js
const fakeUser = (i) => ({
  id: i,
  name: ['Your Name', 'John Doe', 'User 1', 'User 2'][i % 4],
  email: `user-${i}@example.com`,
  avatar: `data:image/svg+xml;base64,${btoa(generateAvatarSVG(i))}`,
  joinedAt: new Date(2024, i % 12, (i % 28) + 1).toISOString(),
  posts: Math.floor(Math.random() * 200) + 5,
});

const users = Array.from({ length: 20 }, (_, i) => fakeUser(i));
```

Faker.js для более серьёзного:
```bash
npm i @faker-js/faker
```
```js
import { faker } from '@faker-js/faker/locale/ru';
const users = Array.from({ length: 20 }, () => ({
  name: faker.person.fullName(),
  email: faker.internet.email(),
  avatar: faker.image.avatar(),
}));
```

## CSV → JSON

Если данные приходят CSV (Excel, Google Sheets export):

```js
// Простой CSV parser
function parseCSV(text) {
  const [header, ...rows] = text.trim().split('\n').map(r => r.split(','));
  return rows.map(row => Object.fromEntries(header.map((h, i) => [h, row[i]])));
}

fetch('data/users.csv').then(r => r.text()).then(text => setUsers(parseCSV(text)));
```

Для сложных (с запятыми внутри значений, quoted strings) — `papaparse`:
```bash
npm i papaparse
```

## Данные с обновлением

Polling для live-feel:
```jsx
useEffect(() => {
  const fetchData = () => fetch('data/feed.json').then(r => r.json()).then(setFeed);
  fetchData();
  const id = setInterval(fetchData, 5000);
  return () => clearInterval(id);
}, []);
```

WebSocket для true real-time:
```jsx
const ws = useRef(null);
useEffect(() => {
  ws.current = new WebSocket('wss://stream.example.com');
  ws.current.onmessage = (e) => setLatest(JSON.parse(e.data));
  return () => ws.current?.close();
}, []);
```

## Правила для demo

1. **Hardcoded credentials** не клади в HTML — API key светится у любого open-DevTools
2. **Используй scoped token** — read-only, демо-org, лимит на запросы
3. **Кэшируй ответы** — проверь что прототип не делает 100 fetches
4. **Fallback к mock** — если API down, показывай static data, не пустой UI

## Stack

- `interactive-prototype` — куда подключаемся
- `states-checklist` — loading / error states при fetch
- `microinteractions` — skeleton loader пока fetch
- `placeholders` — fallback если real data fail

## Антипаттерны

- Включить production secrets в HTML → leaked при handoff
- Делать write-операции (POST/PUT/DELETE) с прода в прототипе → реальные данные пропадут
- Polling каждые 100ms → DDoS API
- Игнорировать loading state → юзер видит пустой UI секундами
- Делать prototype без fallback к static → demo-fail если интернет упал
- Зависеть от API без `try/catch` → app крашится при network error
- Использовать prod database в demo → можно случайно сломать prod data
