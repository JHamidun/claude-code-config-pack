---
name: claude-in-html
description: Дёргать LLM из артефакта (саммари, генерация ответов, классификация). Для прототипов с "магией".
when_to_use: Прототип симулирует работу AI-фичи (чат, ассистент, генератор контента, классификатор).
---

# Claude in HTML

Прототип может вызвать модель напрямую из браузера через Anthropic SDK или fetch к своему бэку. В Claude Code пользователь сам управляет ключом.

## Минимальная реализация

```html
<script type="module">
  import Anthropic from "https://esm.sh/@anthropic-ai/sdk";

  // Один раз — спросить и сохранить ключ.
  let key = localStorage.getItem('anthropic_key');
  if (!key) {
    key = prompt('Anthropic API key (sk-ant-...) — сохранится локально');
    if (key) localStorage.setItem('anthropic_key', key);
  }

  const client = new Anthropic({ apiKey: key, dangerouslyAllowBrowser: true });

  window.askClaude = async function (userText) {
    const r = await client.messages.create({
      model: 'claude-haiku-4-5',
      max_tokens: 512,
      messages: [{ role: 'user', content: userText }],
    });
    return r.content[0].text;
  };
</script>
```

## Стриминг (для чат-прототипа)

```js
const stream = await client.messages.stream({
  model: 'claude-haiku-4-5',
  max_tokens: 1024,
  messages: history,
});
for await (const event of stream) {
  if (event.type === 'content_block_delta') {
    chatBox.append(event.delta.text);
  }
}
```

## Системные промпты для роли

Когда прототип симулирует продуктовую фичу — задай system, объясняющий, что это.

```js
client.messages.create({
  model: 'claude-haiku-4-5',
  max_tokens: 256,
  system: 'Ты — помощник в приложении доставки еды. Отвечай коротко, на русском, без эмодзи.',
  messages: [...]
});
```

## Где взять ключ — UX

Не спрашивай через `prompt()` каждый раз. Сделай нормальный onboarding-экран:

1. При первом запуске — экран «Чтобы попробовать AI-фичу, вставьте API key».
2. Объясни, что ключ хранится **только в браузере** (localStorage), никуда не отправляется.
3. Дай ссылку на console.anthropic.com где взять ключ.
4. Кнопка «Use without AI» — прототип работает со статикой.

## Деградация

**Всегда** имей фолбэк, если ключа нет или запрос упал:

```js
window.askClaude = async function (userText) {
  try {
    if (!localStorage.getItem('anthropic_key')) return mockResponse(userText);
    // ... real call
  } catch (e) {
    console.warn('Claude недоступен, fallback', e);
    return mockResponse(userText);
  }
};

function mockResponse(text) {
  return `[mock] я бы ответил на: "${text.slice(0, 60)}..."`;
}
```

## Безопасность

- `dangerouslyAllowBrowser: true` означает, что ключ светится в браузере. Это **только** для локальных прототипов.
- Никогда не вшивай свой ключ в HTML и не публикуй такой файл.
- Если делишься прототипом — пользователь должен ввести **свой** ключ. Никогда не свой.

## Альтернатива: свой бэк

Если у пользователя есть бэкенд, лучший паттерн — свой endpoint, который проксирует запрос с серверным ключом. Браузер дёргает `/api/claude`, бэк делает реальный вызов. Безопаснее, но требует разворачивания. Для большинства локальных прототипов overkill.
