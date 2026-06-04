---
name: pwa-shell
description: PWA-обёртка для прототипа — manifest.json, service worker (offline), install prompt, app icon. Чтобы прототип на mobile добавлялся «на главный экран» как app, работал offline.
when_to_use: Юзер просит «как app», «можно установить», «работает офлайн», «на главный экран iPhone». Для interactive-prototype который демонстрируется на mobile.
---

# PWA shell

Превращает HTML-прототип в installable mobile app. iOS / Android / desktop browsers поддерживают PWA install через `manifest.json` и service worker.

## Обязательный минимум

```
<project>/
├── index.html
├── manifest.webmanifest
├── service-worker.js
├── icons/
│   ├── icon-192.png       (192×192)
│   ├── icon-512.png       (512×512)
│   ├── icon-180-apple.png (180×180 для iOS)
│   └── splash-screens/    (для iOS launch screens)
```

## manifest.webmanifest

```json
{
  "name": "ExampleProduct",
  "short_name": "HAcademy",
  "description": "Learn AI — practical courses",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "theme_color": "#YOUR_PRIMARY",
  "background_color": "#YOUR_INK",
  "lang": "ru",

  "icons": [
    { "src": "/icons/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any" },
    { "src": "/icons/icon-512-mask.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],

  "screenshots": [
    { "src": "/screenshots/home.png", "sizes": "1080x1920", "type": "image/png", "form_factor": "narrow" }
  ],

  "shortcuts": [
    { "name": "Track Map", "url": "/tracks", "icons": [{ "src": "/icons/track.png", "sizes": "96x96" }] }
  ],

  "categories": ["education", "productivity"]
}
```

В HTML:
```html
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#YOUR_PRIMARY">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent">
<meta name="apple-mobile-web-app-title" content="HAcademy">
<link rel="apple-touch-icon" href="/icons/icon-180-apple.png">
```

## display modes

| Value | Что |
|---|---|
| `browser` | обычная вкладка (не PWA) |
| `minimal-ui` | минимальный chrome (URL + кнопки) |
| `standalone` | как нативный app, без browser UI ✅ |
| `fullscreen` | весь экран, без status bar (для games) |

`standalone` — sweet spot для большинства apps.

## service-worker.js (offline)

Базовый cache-first SW:
```js
const CACHE = 'app-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/styles/tokens.css',
  '/components/shared.jsx',
  '/icons/icon-192.png',
  // ... ключевые ассеты
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(
      keys.filter(k => k !== CACHE).map(k => caches.delete(k))
    ))
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(cached => {
      if (cached) return cached;
      return fetch(e.request).then(resp => {
        // Кэшировать успешные responses
        if (resp.status === 200 && resp.type === 'basic') {
          const copy = resp.clone();
          caches.open(CACHE).then(c => c.put(e.request, copy));
        }
        return resp;
      });
    }).catch(() => {
      // Offline fallback
      if (e.request.destination === 'document') return caches.match('/');
    })
  );
});
```

В `index.html`:
```html
<script>
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/service-worker.js')
      .then(r => console.log('SW registered'))
      .catch(e => console.log('SW failed', e));
  }
</script>
```

## Install prompt

Кастомный install button:
```js
let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
  e.preventDefault();
  deferredPrompt = e;
  document.querySelector('#install-btn').style.display = 'block';
});

document.querySelector('#install-btn').addEventListener('click', async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  const { outcome } = await deferredPrompt.userChoice;
  console.log(outcome);  // 'accepted' or 'dismissed'
  deferredPrompt = null;
});
```

iOS не поддерживает `beforeinstallprompt` — там install через Safari Share menu → «Добавить на главный экран». Прототип может показывать инструкцию.

## Icons — генерация

Из одного 1024×10N PNG:
```bash
npx pwa-asset-generator source-icon-1024.png ./icons \
  --background "#YOUR_INK" \
  --opaque false \
  --padding "0" \
  --manifest manifest.webmanifest \
  --index index.html
```

Сгенерит все размеры + iOS splash screens + автомат добавит в manifest и HTML.

## Maskable icon

iOS / Android делают «adaptive icons» — обрезают round/squircle. Maskable icon должен иметь safe zone:

```
[Иконка 512×512]
[--- 80% inner safe zone ---]
[--- 20% padding (mask-cropable) ---]
```

В manifest помечается `"purpose": "maskable"`.

## Тестирование

- **Chrome DevTools** → Application tab → Manifest, Service Workers, Storage
- **Lighthouse** → PWA category → score 100/100 если всё ОК
- **iOS Safari** → Share → Add to Home Screen
- **Android Chrome** → меню → Install app

## Когда PWA НЕ нужен

- Прототип one-time для презентации → mobile-overlays + device-frames достаточно
- Артефакт desktop only → PWA не даёт ценности
- Юзер не на mobile → просто HTML

## Stack

- `interactive-prototype` — главный артефакт внутри PWA
- `device-frames` — preview как выглядит на iPhone (но это в браузере, не реальный install)
- `standalone-html` — анти-PWA (offline, но не installable)

## Антипаттерны

- Пропустить maskable icon → на Android adaptive icon обрезает важное содержимое
- Не cache'ить main HTML в SW → offline ничего не работает
- Cache 50MB ассетов → quota exceeded на старых устройствах
- Не обновлять CACHE version → юзер залип на старой версии после deploy
- HTTP без HTTPS → SW не работает (на localhost OK)
- Пропустить screenshots в manifest → нет богатого install prompt
- Делать PWA на early-stage прототипе → 80% работы впустую
