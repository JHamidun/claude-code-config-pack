<!-- LEGACY: полное тело скилла 'standalone-html' из старого дерева ${WORKSPACE}/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: standalone-html
description: Самодостаточный single-file HTML — все скрипты, стили, картинки inline. Можно отправить как один файл по email, открыть без сервера, сохранить в Notion. Финальный output для слайдов / лендингов / прототипов когда нужна 100% portability.
when_to_use: Юзер просит «один файл», «без зависимостей», «отправить по email», «открывается на любой машине», «standalone». После slides / interactive-prototype если внешние файлы тяжёлые.
---

# Standalone HTML

Один `.html` файл, который работает в браузере без файлового сервера, без интернета, без других файлов рядом. Все картинки → base64, шрифты → embedded, JS/CSS → inline.

## Какие inline'ятся

| Тип | Метод | Размер |
|---|---|---|
| Изображения | `data:image/png;base64,...` | × 1.33 |
| SVG | inline `<svg>` | стандартный |
| Шрифты | `data:font/woff2;base64,...` в `@font-face` | × 1.33 |
| CSS | `<style>` в `<head>` | стандартный |
| JS | `<script>` в `<head>` или `<body>` | стандартный |
| Видео | `data:video/mp4;base64,...` | × 1.33 (NOT recommended for >2MB) |

`× 1.33` — оверхед base64 кодирования.

## Каркас inliner script

`scripts/inline.js`:
```js
const fs = require('fs');
const path = require('path');
const mime = require('mime-types');

function inlineFile(filePath, baseDir) {
  const abs = path.resolve(baseDir, filePath);
  const buf = fs.readFileSync(abs);
  const m = mime.lookup(abs) || 'application/octet-stream';
  return `data:${m};base64,${buf.toString('base64')}`;
}

function inlineHTML(htmlPath) {
  const baseDir = path.dirname(htmlPath);
  let html = fs.readFileSync(htmlPath, 'utf-8');

  // 1. Replace <link rel="stylesheet" href="X"> → <style>...content...</style>
  html = html.replace(/<link\s+rel="stylesheet"\s+href="([^"]+)"\s*\/?>/g, (_, href) => {
    if (href.startsWith('http')) return _;  // CDN — не трогаем
    let css = fs.readFileSync(path.resolve(baseDir, href), 'utf-8');
    // Inline url() в CSS
    css = css.replace(/url\((['"]?)([^)'"]+)\1\)/g, (m, q, url) => {
      if (url.startsWith('http') || url.startsWith('data:')) return m;
      return `url("${inlineFile(url, path.dirname(path.resolve(baseDir, href)))}")`;
    });
    return `<style>\n${css}\n</style>`;
  });

  // 2. Replace <script src="X"> → <script>...content...</script>
  html = html.replace(/<script\s+([^>]*?)src="([^"]+)"([^>]*?)\s*><\/script>/g,
    (_, before, src, after) => {
      if (src.startsWith('http')) return _;  // CDN
      const js = fs.readFileSync(path.resolve(baseDir, src), 'utf-8');
      return `<script ${before} ${after}>\n${js}\n</script>`;
    });

  // 3. Replace <img src="X"> → <img src="data:...">
  html = html.replace(/<img\s+([^>]*?)src="([^"]+)"([^>]*?)\s*\/?>/g,
    (_, before, src, after) => {
      if (src.startsWith('http') || src.startsWith('data:')) return _;
      return `<img ${before}src="${inlineFile(src, baseDir)}"${after}>`;
    });

  return html;
}

if (require.main === module) {
  const out = inlineHTML(process.argv[2]);
  fs.writeFileSync(process.argv[3] || 'standalone.html', out);
  console.log(`✓ ${process.argv[3] || 'standalone.html'} (${(out.length / 1024).toFixed(1)} KB)`);
}

module.exports = { inlineHTML };
```

```bash
npm i mime-types
node scripts/inline.js artifact.html artifact.standalone.html
```

## CDN scripts — оставлять или embedd'ить?

В artifact из Claude Design используются:
- `react.development.js`, `react-dom.development.js`, `babel-standalone`

| Решение | Pro | Con |
|---|---|---|
| Оставить CDN-ссылки | размер file 50KB | нужен интернет для запуска |
| Embedd'ить React+Babel | работает offline | размер file +1.5MB |

Для real standalone (offline ready) — embedd'ить. Но 1.5MB — большой email-attachment.

**Compromise:** standalone-html + `react.production.min.js` + `react-dom.production.min.js` (без Babel, заранее compiled JSX через online tool):

```bash
# Pre-compile JSX в JS
npx babel src/animation.jsx --presets=@babel/preset-react -o dist/animation.js
# Теперь embedd'ить animation.js, не animation.jsx
# И не нужен @babel/standalone — экономим 1MB
```

## Размеры — что разумно

| Размер | Применение |
|---|---|
| < 100KB | Эмейл-attachment, Slack |
| 100KB - 500KB | Telegram, Discord |
| 500KB - 2MB | Notion-embed, GitHub gist |
| 2MB - 10MB | Local file, Drive |
| > 10MB | Не standalone — лучше hosting |

Если получился >10MB — что-то пошло не так (большие images / видео).

## Verifier для standalone

После inline — открыть в браузере и проверить что всё работает:
```bash
node scripts/verify.js standalone.html
# Через `verifier` skill: file:// без сети, всё должно рендериться
```

## Когда НЕ делать standalone

- Артефакт идёт в production project — там сборщик сделает свою оптимизацию
- Используется heavy data (CSV, JSON) на много MB — лучше hosting
- Есть интерактив с back-end API — standalone не починит API

## Stacking

- `verifier` — проверить standalone после inline
- `dev-handoff` — иногда нужен standalone-html ВНУТРИ handoff bundle для preview
- `export-pdf` — после standalone проще export'ить (всё в одном файле)

## Антипаттерны

- Inline'ить видео >5MB → файл становится unusable
- Использовать blob: URLs внутри standalone (исчезают при reload)
- Оставить относительные ссылки которые не inline'ятся → broken images
- Не сохранять source отдельно — после inline'a JS-код становится unreadable, debug сложно
- Inline'ить шрифты для языков, которые не используются (полный CJK набор) → +2MB на ничего
- Делать standalone каждое изменение → теряется dev-loop (live-preview не работает)
