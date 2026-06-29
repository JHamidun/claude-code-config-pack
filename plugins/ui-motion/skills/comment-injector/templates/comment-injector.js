(function () {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') document.body.removeAttribute('data-cc-on');
  });
  document.addEventListener('click', (e) => {
    if (!e.altKey) return;
    e.preventDefault(); e.stopPropagation();
    const el = e.target;
    const sel = cssPath(el);
    const text = `SELECTOR: ${sel}\nOUTER_HTML: ${el.outerHTML.slice(0, 400)}`;
    navigator.clipboard.writeText(text);
    flash(el);
  }, true);

  function cssPath(el) {
    const parts = [];
    while (el && el.nodeType === 1 && parts.length < 6) {
      let part = el.tagName.toLowerCase();
      if (el.id) { part += '#' + el.id; parts.unshift(part); break; }
      if (el.className) part += '.' + [...el.classList].slice(0, 2).join('.');
      const sib = [...el.parentNode.children].filter(c => c.tagName === el.tagName);
      if (sib.length > 1) part += `:nth-of-type(${sib.indexOf(el) + 1})`;
      parts.unshift(part);
      el = el.parentElement;
    }
    return parts.join(' > ');
  }
  function flash(el) {
    const o = el.style.outline;
    el.style.outline = '2px solid #ff3b30';
    setTimeout(() => { el.style.outline = o; }, 600);
  }
})();
