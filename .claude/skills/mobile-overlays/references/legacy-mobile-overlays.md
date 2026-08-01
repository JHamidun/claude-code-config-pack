<!-- LEGACY: полное тело скилла 'mobile-overlays' из старого дерева ~/.claude/tools/claude-code-skills (@2026-04-30).
     Сохранено при консолидации деревьев design-пака 2026-07-18 (lossless-merge, канон deep-read-before-merge).
     Актуальный канон — ../SKILL.md; здесь — расширенный материал прежней версии (таблицы, рецепты, антипаттерны). -->

---
name: mobile-overlays
description: Mobile UI слои — клавиатура (iOS/Android), bottom sheet, action sheet, тосты, нотификации. Поверх interactive-prototype добавляет реалистичные overlay-элементы.
when_to_use: В прототипе есть формы, выборы, дейтствия — нужны те UI-overlay'и которые юзер видит на телефоне. После interactive-prototype, обычно вместе с device-frames.
---

# Mobile overlays

Готовые JSX-компоненты для типовых mobile UI-overlay'ев. Не пытайся сам рисовать клавиатуру — используй pre-built.

## Состав

| Компонент | Что | Когда использовать |
|---|---|---|
| `<IOSKeyboard>` / `<AndroidKeyboard>` | клавиатура снизу | в прототипе есть `<input>` и пользователь вводит |
| `<BottomSheet>` | модалка снизу | мобильный select, фильтры, share |
| `<ActionSheet>` | список действий | удалить / поделиться / отчёт — iOS-стиль |
| `<Toast>` | плашка-уведомление | feedback после действия (saved, error) |
| `<Notification>` | system-style notification | push-нотификация в углу |
| `<Modal>` | full-screen модалка | overlay с подтверждением действия |
| `<StatusBar>` | время + батарея + сигнал | реалистичный mobile chrome |

## iOS Keyboard (упрощённая)

```jsx
function IOSKeyboard({ visible, onKey, onSubmit, mode = 'text' }) {
  if (!visible) return null;
  const rows = mode === 'text' ? [
    'qwertyuiop', 'asdfghjkl', '⇧zxcvbnm⌫'
  ] : [
    '1234567890', '-/:;()$&@"', '.,?!\'⌫'
  ];
  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0,
      background: '#D1D3D9', padding: '8px 4px 28px',
      fontFamily: '-apple-system, BlinkMacSystemFont, sans-serif',
      borderTop: '1px solid rgba(0,0,0,0.1)',
    }}>
      {rows.map((row, i) => (
        <div key={i} style={{ display: 'flex', justifyContent: 'center', gap: 4, padding: '4px 4px' }}>
          {[...row].map((c, j) => (
            <button key={j} onClick={() => onKey(c)} style={{
              width: 32, height: 42, fontSize: 24, background: '#fff',
              border: 'none', borderRadius: 5, boxShadow: '0 1px 0 rgba(0,0,0,0.3)',
            }}>{c}</button>
          ))}
        </div>
      ))}
      <div style={{ display: 'flex', gap: 4, padding: '4px 4px' }}>
        <button style={{ flex: 1, height: 42, background: '#A6ABB6', borderRadius: 5 }}>123</button>
        <button style={{ flex: 4, height: 42, background: '#fff', borderRadius: 5 }}>пробел</button>
        <button onClick={onSubmit} style={{ flex: 1, height: 42, background: '#007AFF', color: '#fff', borderRadius: 5 }}>↵</button>
      </div>
    </div>
  );
}
window.IOSKeyboard = IOSKeyboard;
```

## Bottom sheet

```jsx
function BottomSheet({ open, onClose, children, height = 400 }) {
  return (
    <>
      <div style={{
        position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.4)',
        opacity: open ? 1 : 0, pointerEvents: open ? 'auto' : 'none',
        transition: 'opacity .25s',
      }} onClick={onClose} />
      <div style={{
        position: 'fixed', left: 0, right: 0, bottom: 0,
        background: '#fff', borderRadius: '16px 16px 0 0',
        height, padding: 20, paddingTop: 12,
        transform: open ? 'translateY(0)' : `translateY(${height}px)`,
        transition: 'transform .3s cubic-bezier(.2,.7,.3,1)',
      }}>
        <div style={{ width: 40, height: 4, background: '#ddd', borderRadius: 2, margin: '0 auto 16px' }} />
        {children}
      </div>
    </>
  );
}
window.BottomSheet = BottomSheet;
```

## Toast

```jsx
function Toast({ message, kind = 'info', onClose }) {
  if (!message) return null;
  const colors = {
    info:    { bg: '#1F2937', fg: '#fff' },
    success: { bg: '#16A34A', fg: '#fff' },
    error:   { bg: '#DC2626', fg: '#fff' },
  };
  setTimeout(onClose, 3000);
  return (
    <div style={{
      position: 'fixed', bottom: 80, left: '50%', transform: 'translateX(-50%)',
      background: colors[kind].bg, color: colors[kind].fg,
      padding: '12px 20px', borderRadius: 8, fontSize: 14, fontWeight: 500,
      boxShadow: '0 8px 24px rgba(0,0,0,0.2)', zIndex: 1000,
    }}>{message}</div>
  );
}
window.Toast = Toast;
```

## Стек

Mobile-overlays почти всегда вместе с:
- `device-frames` — рамка телефона снаружи
- `interactive-prototype` — экран внутри
- `microinteractions` — анимации появления (slide-up, fade-in)

## Антипаттерны

- Своя реализация iOS-клавиатуры с нуля → 200 строк впустую, всё уже есть
- Bottom sheet без backdrop → юзер не понимает что нужно закрыть
- Toast без auto-dismiss → застревает на экране
- ActionSheet с 8+ опциями → не помещается на mobile
- Modal full-screen без чёткого CTA «закрыть» → юзер в ловушке
- Использовать `position: absolute` вместо `fixed` для overlay → ломается при скролле
- Z-index без системы (`z-index: 9999999`) → конфликты, всё ломается. Используй каскад: backdrop=900, sheet=1000, toast=1100
