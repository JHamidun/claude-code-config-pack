---
name: pwa-shell
description: "HTML-артефакт → устанавливаемое PWA: manifest, service worker, иконки. Триггеры: «поставить на телефон», «install prompt», «service worker offline»."
---

# PWA shell

Минимальное PWA — три файла + иконки. Ничего сложного.

## Минимум

```
project/
  index.html
  manifest.webmanifest
  sw.js
  icons/
    icon-192.png
    icon-512.png
    icon-512-maskable.png
```

### manifest.webmanifest

```json
{
  "name": "Project Name",
  "short_name": "Project",
  "description": "Описание для install-prompt",
  "start_url": "/",
  "scope": "/",
  "display": "standalone",
  "orientation": "portrait",
  "background_color": "#FAF9F6",
  "theme_color": "#111111",
  "lang": "ru",
  "icons": [
    { "src": "icons/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icons/icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icons/icon-512-maskable.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ]
}
```

### index.html — head

```html
<link rel="manifest" href="/manifest.webmanifest">
<meta name="theme-color" content="#111111">
<link rel="apple-touch-icon" href="/icons/icon-192.png">
<script>
  if ('serviceWorker' in navigator) {
    addEventListener('load', () => navigator.serviceWorker.register('/sw.js'));
  }
</script>
```

### sw.js — простейший cache-first

```js
const CACHE = 'app-v1';
const ASSETS = [
  '/',
  '/index.html',
  '/style.css',
  '/app.js',
  '/icons/icon-192.png',
];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(ASSETS)));
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys().then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  if (e.request.method !== 'GET') return;
  e.respondWith(
    caches.match(e.request).then(r => r || fetch(e.request).then(resp => {
      if (resp.ok && new URL(e.request.url).origin === location.origin) {
        const copy = resp.clone();
        caches.open(CACHE).then(c => c.put(e.request, copy));
      }
      return resp;
    }).catch(() => caches.match('/')))
  );
});
```

## Иконки

Сгенерируй 192px и 512px из одной 1024px-исходной:

```bash
# С imagemagick
magick icon-1024.png -resize 192x192 icons/icon-192.png
magick icon-1024.png -resize 512x512 icons/icon-512.png
# Maskable: добавь safe area 10%
magick icon-1024.png -resize 410x410 -background "#111" -gravity center -extent 512x512 icons/icon-512-maskable.png
```

## Install prompt

Для Android Chrome / desktop Chrome — кастомный UI:

```js
let deferredPrompt;
window.addEventListener('beforeinstallprompt', e => {
  e.preventDefault();
  deferredPrompt = e;
  document.getElementById('install-btn').hidden = false;
});

document.getElementById('install-btn').onclick = async () => {
  if (!deferredPrompt) return;
  deferredPrompt.prompt();
  await deferredPrompt.userChoice;
  deferredPrompt = null;
  document.getElementById('install-btn').hidden = true;
};
```

iOS Safari install — **только** через "Поделиться → На главный экран". Можно показать инструкцию, если detect iOS.

## Update flow

Когда пользователь открывает старую версию, новый SW активируется в фоне. Чтобы он применился сразу:

```js
self.addEventListener('install', e => self.skipWaiting());
self.addEventListener('activate', e => self.clients.claim());
```

И в основном коде:

```js
navigator.serviceWorker.addEventListener('controllerchange', () => location.reload());
```

## Тестирование

- Chrome DevTools → Application → Manifest и Service Workers.
- Lighthouse → PWA score (стремиться к ≥90).
- Самое надёжное — установить на реальный телефон.

## Что НЕ нужно

- Push-уведомления для прототипа. Это отдельная инфраструктура.
- Background sync — overkill.
- Сложные стратегии кэша. Cache-first для статики достаточно.

## Чек-лист

- ✅ HTTPS (или localhost). Без HTTPS PWA не работает.
- ✅ Manifest подключен.
- ✅ SW зарегистрирован и работает.
- ✅ Иконки 192 и 512 есть.
- ✅ Maskable иконка есть (для Android adaptive icons).
- ✅ Lighthouse PWA-checks зелёные.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-pwa-shell.md`. Секции там: Обязательный минимум, manifest.webmanifest, display modes, service-worker.js (offline), Install prompt, Icons — генерация, Maskable icon, Тестирование, Когда PWA НЕ нужен, Stack, Антипаттерны.
