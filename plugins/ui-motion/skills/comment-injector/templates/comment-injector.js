(function () {
  // Alt+Click       — one element to clipboard (selector + outerHTML).
  // Shift+Alt+Click — add/remove element to a batch; clipboard gets the whole numbered list.
  // Escape          — clear the batch.
  const marked = [];
  // Description is captured BEFORE the dashed outline is applied, otherwise the copied
  // outerHTML carries our own style/data attributes and reads as part of the page.
  const described = new Map();

  document.addEventListener('keydown', (e) => {
    if (e.key !== 'Escape') return;
    document.body.removeAttribute('data-cc-on');
    while (marked.length) unmark(marked.pop());
  });

  document.addEventListener('click', (e) => {
    if (!e.altKey) return;
    e.preventDefault(); e.stopPropagation();
    const el = e.target;
    if (e.shiftKey) {
      const i = marked.indexOf(el);
      if (i === -1) { described.set(el, describe(el)); marked.push(el); mark(el); } else { marked.splice(i, 1); unmark(el); }
      copy(marked.length ? `MARKED: ${marked.length}\n` + marked.map((m, k) => `${k + 1}. ${described.get(m).replace(/\n/g, '\n   ')}`).join('\n') : '');
      return;
    }
    copy(describe(el));
    flash(el);
  }, true);

  function describe(el) {
    return `SELECTOR: ${cssPath(el)}\nOUTER_HTML: ${el.outerHTML.slice(0, 400)}`;
  }
  function copy(text) {
    if (navigator.clipboard) navigator.clipboard.writeText(text).catch(() => {});
  }
  function cssPath(el) {
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 6) {
      let part = el.tagName.toLowerCase();
      if (el.id) { part += '#' + el.id; parts.unshift(part); break; }
      if (el.classList && el.classList.length) part += '.' + [...el.classList].slice(0, 2).join('.');
      const sib = el.parentElement ? [...el.parentElement.children].filter(c => c.tagName === el.tagName) : [];
      if (sib.length > 1) part += `:nth-of-type(${sib.indexOf(el) + 1})`;
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  function mark(el) {
    el.dataset.ccOutline = el.style.outline;
    el.style.outline = '2px dashed #ff3b30';
    el.style.outlineOffset = '2px';
  }
  function unmark(el) {
    described.delete(el);
    el.style.outline = el.dataset.ccOutline || '';
    el.style.outlineOffset = '';
    delete el.dataset.ccOutline;
    if (!el.getAttribute('style')) el.removeAttribute('style');
  }
  function flash(el) {
    const o = el.style.outline;
    el.style.outline = '2px solid #ff3b30';
    setTimeout(() => { el.style.outline = o; }, 600);
  }
})();
