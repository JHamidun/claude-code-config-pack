---
name: placeholders
description: Стандартные плейсхолдеры для изображений и иконок — полосатый SVG с подписью monospace. Лучше, чем плохо нарисованный кастом-SVG.
when_to_use: Когда в дизайне нужна картинка / иконка / иллюстрация, а реального ассета нет.
---

# Placeholders

Принцип: **хороший плейсхолдер лучше плохой попытки нарисовать настоящее.**

## Image placeholder

```html
<div class="placeholder" style="aspect-ratio: 16/9;">
  <span>product hero · 1920×1080</span>
</div>
```

```css
.placeholder {
  background: repeating-linear-gradient(
    45deg, #1a1a1a, #1a1a1a 8px, #222 8px, #222 16px
  );
  display: grid; place-items: center;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  color: #888; font-size: 14px;
  border-radius: 8px;
  text-align: center; padding: 16px;
}
```

Светлый вариант:

```css
.placeholder.light {
  background: repeating-linear-gradient(
    45deg, #ececec, #ececec 8px, #f4f4f4 8px, #f4f4f4 16px
  );
  color: #888;
}
```

## Icon placeholder

```html
<span class="icon-ph" data-name="settings"></span>
```

```css
.icon-ph {
  display: inline-block; width: 24px; height: 24px;
  background: currentColor; mask: linear-gradient(#000, #000);
  border: 1.5px solid currentColor; border-radius: 4px;
  background: transparent;
  position: relative;
}
.icon-ph::after {
  content: attr(data-name);
  position: absolute; top: 100%; left: 50%; transform: translateX(-50%);
  font-family: ui-monospace, monospace; font-size: 9px;
  white-space: nowrap; color: #888;
  margin-top: 2px;
}
```

## Avatar placeholder

```html
<div class="avatar-ph">JD</div>
```

```css
.avatar-ph {
  width: 40px; height: 40px;
  background: #d4d4d4; color: #555;
  display: grid; place-items: center;
  border-radius: 50%;
  font-family: ui-monospace, monospace;
  font-size: 13px; font-weight: 500;
}
```

## Что писать в подписи

Конкретное:
- `product hero · 1920×1080`
- `screenshot · settings page`
- `team photo · 6 people`
- `chart · revenue Q1-Q4`

Не «image», не «placeholder», не «coming soon».

## Когда плейсхолдер НЕ подходит

- В финальном артефакте, который пойдёт клиенту, — попроси у пользователя реальные изображения.
- Для логотипа — он критичен; либо проси настоящий, либо ставь `[brand mark]` текстом, не рисуй.
- В презентации с фотографиями людей — без реальных фото секция не работает; не имитируй.

## Антипаттерны

- ❌ Серый прямоугольник с текстом «Image».
- ❌ SVG с попыткой нарисовать «иконку лупы / шестерёнки» от руки. Ты не угадаешь стиль системы.
- ❌ Текст «Coming soon», «WIP», «Lorem».
- ❌ Картинки с unsplash.com, если не сказали — могут быть лицензионные сюрпризы.

## Legacy reference

Прежняя расширенная версия скилла (дерево @2026-04-30) сохранена целиком в `references/legacy-placeholders.md`. Секции там: Базовый image placeholder, Аватары, Logo placeholder, Charts placeholder, Иконки, User-uploaded references, Антипаттерны.
