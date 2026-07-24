/**
 * <deck-stage>
 *
 * Веб-компонент-оболочка для HTML-презентаций. Каждый прямой ребёнок <section>
 * считается слайдом. Компонент:
 *  - Масштабирует канвас фиксированного размера под любой viewport (letterbox).
 *  - Управляет навигацией: ←/→, Space, PageUp/Down, Home/End, клик по краям, тач-свайпы.
 *  - Хранит позицию в URL hash (#3) — рефреш не теряет место.
 *  - Эмитит {slideIndexChanged: N} в parent через postMessage (для спикер-нот в iframe-хосте).
 *  - Поддерживает печать в PDF: одна страница = один слайд.
 *  - Показывает счётчик "3 / 12" в углу.
 *
 * Использование:
 *   <script src="deck-stage.js"></script>
 *   <deck-stage width="1920" height="1080">
 *     <section>slide 1</section>
 *     <section>slide 2</section>
 *   </deck-stage>
 */

(function () {
  const TEMPLATE = document.createElement('template');
  TEMPLATE.innerHTML = `
    <style>
      :host {
        display: block;
        width: 100vw;
        height: 100vh;
        background: #000;
        overflow: hidden;
        position: relative;
        font-family: inherit;
      }
      .stage {
        position: absolute;
        top: 50%; left: 50%;
        transform-origin: 0 0;
        background: #fff;
        overflow: hidden;
      }
      ::slotted(section) {
        position: absolute;
        inset: 0;
        display: none;
        overflow: hidden;
      }
      ::slotted(section[data-active]) {
        display: block;
      }
      .counter {
        position: fixed;
        bottom: 16px; right: 20px;
        font: 500 13px/1 ui-monospace, SFMono-Regular, Menlo, monospace;
        color: rgba(255,255,255,.55);
        background: rgba(0,0,0,.35);
        padding: 6px 10px;
        border-radius: 999px;
        pointer-events: none;
        z-index: 9999;
      }
      .nav-zone {
        position: fixed; top: 0; bottom: 0;
        width: 18%;
        cursor: pointer;
        z-index: 9998;
      }
      .nav-zone.left  { left: 0; }
      .nav-zone.right { right: 0; }

      :host([noscale]) .stage {
        position: static;
        transform: none !important;
        width: var(--deck-w) !important;
        height: var(--deck-h) !important;
      }

      @media print {
        @page { margin: 0; size: var(--deck-w-pt, 1920px) var(--deck-h-pt, 1080px); }
        :host { width: auto !important; height: auto !important; background: #fff; }
        .stage, ::slotted(section) {
          position: static !important;
          transform: none !important;
          width: var(--deck-w) !important;
          height: var(--deck-h) !important;
          page-break-after: always;
          break-after: page;
          display: block !important;
        }
        .counter, .nav-zone { display: none !important; }
      }
    </style>
    <div class="stage" part="stage">
      <slot></slot>
    </div>
    <div class="nav-zone left"  data-dir="-1"></div>
    <div class="nav-zone right" data-dir="1"></div>
    <div class="counter" part="counter"></div>
  `;

  class DeckStage extends HTMLElement {
    static get observedAttributes() { return ['width', 'height']; }

    constructor() {
      super();
      this.attachShadow({ mode: 'open' }).appendChild(TEMPLATE.content.cloneNode(true));
      this._stage = this.shadowRoot.querySelector('.stage');
      this._counter = this.shadowRoot.querySelector('.counter');
      this._index = 0;
      this._touchStartX = null;
    }

    connectedCallback() {
      this._w = parseInt(this.getAttribute('width')  || '1920', 10);
      this._h = parseInt(this.getAttribute('height') || '1080', 10);
      this.style.setProperty('--deck-w', this._w + 'px');
      this.style.setProperty('--deck-h', this._h + 'px');
      this._stage.style.width  = this._w + 'px';
      this._stage.style.height = this._h + 'px';

      this._slides = Array.from(this.querySelectorAll(':scope > section'));
      this._slides.forEach((s, i) => {
        if (!s.hasAttribute('data-screen-label')) {
          s.setAttribute('data-screen-label', String(i + 1).padStart(2, '0'));
        }
        s.setAttribute('data-om-validate', 'slide');
      });

      this._scale = this._scale.bind(this);
      window.addEventListener('resize', this._scale);
      this._scale();

      this._onKey = this._onKey.bind(this);
      window.addEventListener('keydown', this._onKey);

      this.shadowRoot.querySelectorAll('.nav-zone').forEach(zone => {
        zone.addEventListener('click', () => this.go(this._index + Number(zone.dataset.dir)));
      });

      this.addEventListener('touchstart', e => { this._touchStartX = e.touches[0].clientX; });
      this.addEventListener('touchend', e => {
        if (this._touchStartX == null) return;
        const dx = e.changedTouches[0].clientX - this._touchStartX;
        if (Math.abs(dx) > 40) this.go(this._index + (dx < 0 ? 1 : -1));
        this._touchStartX = null;
      });

      const fromHash = parseInt(location.hash.replace('#', ''), 10);
      const start = Number.isFinite(fromHash) ? fromHash - 1 : 0;
      this.go(start, /*silent*/ true);
    }

    disconnectedCallback() {
      window.removeEventListener('resize', this._scale);
      window.removeEventListener('keydown', this._onKey);
    }

    attributeChangedCallback() {
      if (!this.isConnected) return;
      this._w = parseInt(this.getAttribute('width')  || '1920', 10);
      this._h = parseInt(this.getAttribute('height') || '1080', 10);
      this._stage.style.width  = this._w + 'px';
      this._stage.style.height = this._h + 'px';
      this._scale();
    }

    _scale() {
      if (this.hasAttribute('noscale')) return;
      const sx = window.innerWidth  / this._w;
      const sy = window.innerHeight / this._h;
      const s  = Math.min(sx, sy);
      this._stage.style.transform =
        `translate(-50%, -50%) scale(${s})`;
      this._stage.style.left = '50%';
      this._stage.style.top  = '50%';
    }

    _onKey(e) {
      if (e.target.closest('input, textarea, [contenteditable]')) return;
      switch (e.key) {
        case 'ArrowRight':
        case 'PageDown':
        case ' ':
          this.go(this._index + 1); e.preventDefault(); break;
        case 'ArrowLeft':
        case 'PageUp':
          this.go(this._index - 1); e.preventDefault(); break;
        case 'Home': this.go(0); break;
        case 'End':  this.go(this._slides.length - 1); break;
        default:
          if (/^[0-9]$/.test(e.key)) {
            const n = parseInt(e.key, 10) - 1;
            if (n >= 0 && n < this._slides.length) this.go(n);
          }
      }
    }

    go(i, silent) {
      const total = this._slides.length;
      const next = Math.max(0, Math.min(total - 1, i));
      this._slides.forEach((s, k) => {
        if (k === next) s.setAttribute('data-active', '');
        else s.removeAttribute('data-active');
      });
      this._index = next;
      this._counter.textContent = `${next + 1} / ${total}`;
      if (!silent) {
        history.replaceState(null, '', '#' + (next + 1));
        try {
          window.parent.postMessage({ slideIndexChanged: next }, '*');
        } catch (e) {}
      }
    }

    get currentIndex() { return this._index; }
    get total() { return this._slides.length; }
  }

  customElements.define('deck-stage', DeckStage);
})();
