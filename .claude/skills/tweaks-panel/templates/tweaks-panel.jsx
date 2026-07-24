/**
 * <TweaksPanel> + useTweaks
 * Плавающая панель «крутилок» для прототипа. localStorage-persistent.
 * Подключается через <script type="text/babel" src="tweaks-panel.jsx"></script>.
 */

const { useState, useEffect, useRef } = React;

function useTweaks(defaults) {
  const key = 'tweaks.' + location.pathname;
  const [state, setState] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem(key) || 'null');
      return saved ? { ...defaults, ...saved } : defaults;
    } catch { return defaults; }
  });
  useEffect(() => { localStorage.setItem(key, JSON.stringify(state)); }, [state, key]);

  function setTweak(k, v) {
    if (typeof k === 'object') setState(s => ({ ...s, ...k }));
    else setState(s => ({ ...s, [k]: v }));
  }
  return [state, setTweak, () => setState(defaults)];
}

const tweaksStyles = {
  panel: {
    position: 'fixed', right: 16, bottom: 16,
    width: 260, maxHeight: '80vh', overflow: 'auto',
    background: '#fff', color: '#111',
    border: '1px solid #ddd', borderRadius: 12,
    boxShadow: '0 20px 60px rgba(0,0,0,.2)',
    fontFamily: '-apple-system, system-ui, sans-serif',
    fontSize: 13, zIndex: 9999,
  },
  header: {
    padding: '10px 14px', borderBottom: '1px solid #eee',
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    cursor: 'move', userSelect: 'none',
    fontWeight: 600,
  },
  body: { padding: '8px 14px 14px' },
  section: { marginTop: 12 },
  sectionTitle: {
    fontSize: 11, textTransform: 'uppercase',
    letterSpacing: 0.08, color: '#888', marginBottom: 6,
  },
  row: { display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 10, marginBottom: 8 },
  label: { color: '#444', flex: 1 },
  closeBtn: {
    background: 'none', border: 0, cursor: 'pointer',
    fontSize: 18, color: '#888', lineHeight: 1, padding: 0,
  },
};

function TweaksPanel({ children, title = 'Tweaks' }) {
  const [open, setOpen] = useState(true);
  const [pos, setPos]   = useState(null);
  const dragRef = useRef(null);

  function onPointerDown(e) {
    const rect = dragRef.current.getBoundingClientRect();
    const off = { x: e.clientX - rect.left, y: e.clientY - rect.top };
    function move(ev) { setPos({ x: ev.clientX - off.x, y: ev.clientY - off.y }); }
    function up() {
      window.removeEventListener('pointermove', move);
      window.removeEventListener('pointerup', up);
    }
    window.addEventListener('pointermove', move);
    window.addEventListener('pointerup', up);
  }

  if (!open) {
    return <button onClick={() => setOpen(true)} style={{
      position: 'fixed', right: 16, bottom: 16, padding: '8px 14px',
      background: '#111', color: '#fff', border: 0, borderRadius: 999,
      cursor: 'pointer', zIndex: 9999, fontSize: 13,
    }}>Tweaks</button>;
  }

  const style = pos
    ? { ...tweaksStyles.panel, left: pos.x, top: pos.y, right: 'auto', bottom: 'auto' }
    : tweaksStyles.panel;

  return (
    <div ref={dragRef} style={style}>
      <div style={tweaksStyles.header} onPointerDown={onPointerDown}>
        <span>{title}</span>
        <button style={tweaksStyles.closeBtn} onClick={() => setOpen(false)}>×</button>
      </div>
      <div style={tweaksStyles.body}>{children}</div>
    </div>
  );
}

function TweakSection({ title, children }) {
  return <div style={tweaksStyles.section}>
    {title && <div style={tweaksStyles.sectionTitle}>{title}</div>}
    {children}
  </div>;
}

function TweakSlider({ label, value, onChange, min = 0, max = 100, step = 1 }) {
  return <div style={tweaksStyles.row}>
    <span style={tweaksStyles.label}>{label}</span>
    <input type="range" min={min} max={max} step={step} value={value}
      onChange={e => onChange(+e.target.value)} style={{ width: 100 }} />
    <span style={{ minWidth: 30, textAlign: 'right', fontVariantNumeric: 'tabular-nums' }}>{value}</span>
  </div>;
}

function TweakToggle({ label, value, onChange }) {
  return <div style={tweaksStyles.row}>
    <span style={tweaksStyles.label}>{label}</span>
    <button onClick={() => onChange(!value)} style={{
      width: 36, height: 20, borderRadius: 999,
      background: value ? '#111' : '#ddd',
      border: 0, position: 'relative', cursor: 'pointer',
      transition: 'background 0.15s',
    }}>
      <span style={{
        position: 'absolute', top: 2, left: value ? 18 : 2,
        width: 16, height: 16, borderRadius: '50%', background: '#fff',
        transition: 'left 0.15s',
      }}/>
    </button>
  </div>;
}

function TweakRadio({ value, options, onChange }) {
  return <div style={{ display: 'flex', gap: 4, background: '#f3f3f3', padding: 2, borderRadius: 6 }}>
    {options.map(o => (
      <button key={o} onClick={() => onChange(o)} style={{
        flex: 1, padding: '6px 8px', border: 0, borderRadius: 4,
        background: value === o ? '#fff' : 'transparent',
        boxShadow: value === o ? '0 1px 3px rgba(0,0,0,.1)' : 'none',
        cursor: 'pointer', fontSize: 12,
      }}>{o}</button>
    ))}
  </div>;
}

function TweakSelect({ label, value, options, onChange }) {
  return <div style={tweaksStyles.row}>
    <span style={tweaksStyles.label}>{label}</span>
    <select value={value} onChange={e => onChange(e.target.value)}>
      {options.map(o => <option key={o} value={o}>{o}</option>)}
    </select>
  </div>;
}

function TweakColor({ label, value, onChange }) {
  return <div style={tweaksStyles.row}>
    <span style={tweaksStyles.label}>{label}</span>
    <input type="color" value={value} onChange={e => onChange(e.target.value)}
      style={{ width: 32, height: 24, border: 'none', background: 'none', padding: 0 }}/>
    <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 11 }}>{value}</span>
  </div>;
}

function TweakText({ label, value, onChange }) {
  return <div style={tweaksStyles.row}>
    <span style={tweaksStyles.label}>{label}</span>
    <input type="text" value={value} onChange={e => onChange(e.target.value)}
      style={{ flex: 1, padding: '4px 6px', fontSize: 12 }} />
  </div>;
}

function TweakNumber({ label, value, onChange }) {
  return <div style={tweaksStyles.row}>
    <span style={tweaksStyles.label}>{label}</span>
    <input type="number" value={value} onChange={e => onChange(+e.target.value)}
      style={{ width: 70, padding: '4px 6px', fontSize: 12 }} />
  </div>;
}

Object.assign(window, {
  useTweaks, TweaksPanel, TweakSection,
  TweakSlider, TweakToggle, TweakRadio, TweakSelect,
  TweakColor, TweakText, TweakNumber,
});
