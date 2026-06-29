/**
 * Минималистичный таймлайн-движок.
 * Подключается как <script type="text/babel" src="anim-engine.jsx"></script>
 * после React + Babel.
 *
 * Экспортирует на window: Stage, Sprite, useTime, useSprite, Easing, interpolate,
 * entryFade, entryRise, exitFade.
 */

const { useState, useEffect, useRef, useContext, createContext, useMemo } = React;

const TimeCtx   = createContext(0);
const SpriteCtx = createContext(0);

const Easing = {
  linear:    t => t,
  easeIn:    t => t * t,
  easeOut:   t => 1 - (1 - t) * (1 - t),
  easeInOut: t => t < 0.5 ? 2 * t * t : 1 - Math.pow(-2 * t + 2, 2) / 2,
  expo:      t => t === 0 ? 0 : Math.pow(2, 10 * t - 10),
  back:      t => 2.7 * t * t * t - 1.7 * t * t,
  bounce:    t => {
    const n = 7.5625, d = 2.75;
    if (t < 1/d)   return n * t * t;
    if (t < 2/d) { t -= 1.5/d; return n * t * t + 0.75; }
    if (t < 2.5/d){ t -= 2.25/d; return n * t * t + 0.9375; }
    t -= 2.625/d; return n * t * t + 0.984375;
  },
};

function interpolate(t, [from, to], easing = Easing.linear) {
  const e = Math.max(0, Math.min(1, easing(t)));
  if (Array.isArray(from)) return from.map((f, i) => f + (to[i] - f) * e);
  return from + (to - from) * e;
}

function useTime() { return useContext(TimeCtx); }
function useSprite() { return useContext(SpriteCtx); }

function Stage({ duration = 5, width = 1920, height = 1080, children, fps = 60 }) {
  const [time, setTime] = useState(0);
  const [playing, setPlaying] = useState(true);
  const rafRef = useRef(null);
  const lastRef = useRef(performance.now());
  const stageRef = useRef(null);
  const [scale, setScale] = useState(1);

  useEffect(() => {
    function tick(now) {
      const dt = (now - lastRef.current) / 1000;
      lastRef.current = now;
      if (playing) {
        setTime(t => {
          const next = t + dt;
          return next > duration ? 0 : next;
        });
      }
      rafRef.current = requestAnimationFrame(tick);
    }
    rafRef.current = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(rafRef.current);
  }, [playing, duration]);

  useEffect(() => {
    function fit() {
      const sx = window.innerWidth / width;
      const sy = (window.innerHeight - 60) / height;
      setScale(Math.min(sx, sy));
    }
    fit();
    window.addEventListener('resize', fit);
    return () => window.removeEventListener('resize', fit);
  }, [width, height]);

  return (
    <div style={{ width: '100vw', height: '100vh', background: '#000', overflow: 'hidden', position: 'relative' }}>
      <div ref={stageRef} style={{
        position: 'absolute', top: '50%', left: '50%',
        width, height, background: '#fff',
        transform: `translate(-50%, -50%) scale(${scale})`, transformOrigin: 'center',
      }}>
        <TimeCtx.Provider value={time}>{children}</TimeCtx.Provider>
      </div>

      <div style={{
        position: 'fixed', bottom: 0, left: 0, right: 0, height: 60,
        background: 'rgba(0,0,0,.8)', display: 'flex', alignItems: 'center', gap: 16, padding: '0 16px',
        color: '#fff', fontFamily: 'ui-monospace, monospace', fontSize: 13,
      }}>
        <button onClick={() => setPlaying(p => !p)} style={{
          background: 'none', border: '1px solid #555', color: '#fff',
          padding: '6px 12px', borderRadius: 4, cursor: 'pointer',
        }}>{playing ? 'Pause' : 'Play'}</button>
        <span style={{ minWidth: 80 }}>{time.toFixed(2)}s / {duration}s</span>
        <input type="range" min={0} max={duration} step={0.01} value={time}
          onChange={e => { setTime(+e.target.value); setPlaying(false); }}
          style={{ flex: 1 }}
        />
      </div>
    </div>
  );
}

function Sprite({ start = 0, end = Infinity, children }) {
  const t = useTime();
  if (t < start || t > end) return null;
  const local = (t - start) / (end - start);
  return <SpriteCtx.Provider value={Math.max(0, Math.min(1, local))}>
    {typeof children === 'function' ? children() : children}
  </SpriteCtx.Provider>;
}

// Готовые wrappers
function entryFade({ duration = 0.5, easing = Easing.easeOut } = {}) {
  return (p) => ({ opacity: interpolate(Math.min(1, p / (duration / (1 - 0))), [0, 1], easing) });
}
function entryRise({ from = 40, duration = 0.6, easing = Easing.easeOut } = {}) {
  return (p) => {
    const e = Math.min(1, p / duration);
    return {
      opacity: interpolate(e, [0, 1], easing),
      transform: `translateY(${interpolate(e, [from, 0], easing)}px)`,
    };
  };
}
function exitFade({ start = 0.7, easing = Easing.easeIn } = {}) {
  return (p) => p < start ? {} : { opacity: interpolate((p - start) / (1 - start), [1, 0], easing) };
}

Object.assign(window, {
  Stage, Sprite, useTime, useSprite,
  Easing, interpolate,
  entryFade, entryRise, exitFade,
});
