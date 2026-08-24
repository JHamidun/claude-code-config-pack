// Tilda Feeds API — JavaScript helper for use in DevTools console or Playwright browser_evaluate
// Direct fetch to /submit/ urlencoded — bypasses sendRequest() callback hell.
//
// Usage in DevTools (on https://feeds.tilda.ru/posts/?feeduid=<feeduid>):
//   const t = new TildaFeed('100000000001');
//   const list = await t.list();
//   await t.edit(uid, {title:'...', image:'...', mediadata:'...'});
//
// In Playwright browser_evaluate — copy-paste class definition into your evaluate block.

class TildaFeed {
  constructor(feeduid) {
    this.feeduid = feeduid;
  }

  async _post(action, params = {}) {
    const body = new URLSearchParams({...params, action}).toString();
    const r = await fetch('/submit/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
      body,
      credentials: 'include',
    });
    return r.json();
  }

  // ===== Posts =====

  /** List posts. Returns Object keyed by uid (NOT array). */
  async list({partuid = '', page = 1, items = 50} = {}) {
    const r = await this._post('posts_GetList', {
      feeduid: this.feeduid, partuid, page: String(page), items: String(items),
    });
    return r.data?.posts || {};
  }

  async listAll() {
    return this.list({items: 500});
  }

  async get(postuid) {
    const r = await this._post('posts_Get', {postuid});
    return r.data;
  }

  /** Add empty post — only title is set. Returns new uid. */
  async add(title, partuid = '') {
    const r = await this._post('posts_Add', {feeduid: this.feeduid, title, partuid});
    return r.data?.uid;
  }

  /** Edit post fields. Pass any of: title, descr, date, url, tags, image, mediadata, text, alias.
   *
   * IMPORTANT: posts_Edit is PUT (full replace), not PATCH. Missing `title` → empty string.
   * Always pass `title` (or use editPreservingTitle()) to avoid "Post title is empty" error.
   */
  async edit(postuid, fields) {
    return this._post('posts_Edit', {postuid, ...fields});
  }

  /** Like edit() but auto-fetches and preserves existing title to prevent nullification. */
  async editPreservingTitle(postuid, fields) {
    if (!fields.title) {
      const list = await this.list({items: 500});
      const existing = list[postuid];
      if (existing && existing.title) fields = {title: existing.title, ...fields};
    }
    return this.edit(postuid, fields);
  }

  /** TOGGLE visibility. Use ensureActive() for setter behavior. */
  async toggleActive(postuid) {
    return this._post('posts_Active', {postuid});
  }

  /** Idempotent activate — toggles only if currently inactive. */
  async ensureActive(postuid) {
    const list = await this.list({items: 500});
    const post = list[postuid];
    if (post && post.active === 'y') return {noop: true};
    return this.toggleActive(postuid);
  }

  async delete(postuid) {
    return this._post('posts_Delete', {postuid});
  }

  async restore(postuid) {
    return this._post('posts_Restore', {postuid});
  }

  async pin(postuid) {
    return this._post('posts_Pin', {postuid});
  }

  async reorder(postuidsInOrder) {
    return this._post('posts_Reorder', {feeduid: this.feeduid, postuids: postuidsInOrder.join(',')});
  }

  async duplicate(postuid) {
    return this._post('posts_Duplicate', {postuid});
  }

  // ===== Helpers =====

  static normalizeTitle(s) {
    return (s || '').toLowerCase()
      .replace(/[«»"'()\[\].,:;\—\-!?]/g, '')
      .replace(/\s+/g, ' ').trim();
  }

  /** Find posts by title substring. */
  async findByTitle(substr) {
    const list = await this.list({items: 500});
    const s = substr.toLowerCase();
    return Object.entries(list)
      .filter(([uid, p]) => (p.title || '').toLowerCase().includes(s))
      .map(([uid, p]) => ({uid, ...p}));
  }

  /** Bulk set covers by normalized title. titleToCover: Object<normTitle, cdnUrl>. */
  async bulkSetCovers(titleToCover) {
    const list = await this.list({items: 500});
    const results = [];
    for (const [uid, p] of Object.entries(list)) {
      const key = TildaFeed.normalizeTitle(p.title || '');
      const cover = titleToCover[key];
      if (!cover) {
        results.push({uid, title: p.title, matched: false});
        continue;
      }
      // Pass title explicitly — posts_Edit nullifies title if not passed
      const r = await this.edit(uid, {title: p.title || '', image: cover, mediadata: cover});
      results.push({uid, title: p.title, matched: true, cover, error: r.error});
    }
    return results;
  }
}

// ===== Tilda Page editor =====

class TildaPage {
  constructor(pageid, projectid) {
    this.pageid = pageid;
    this.projectid = projectid;
  }

  async getRecordSettings(recordid) {
    const body = new URLSearchParams({
      comm: 'editrecordsettings', pageid: this.pageid, recordid, tab: 'settings',
    }).toString();
    const r = await fetch('/page/edit/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
      body, credentials: 'include',
    });
    return r.json();
  }

  /** Save single field. Returns 'OK' string. */
  async saveField(recordid, field, value) {
    const body = new URLSearchParams({
      comm: 'saverecord', pageid: this.pageid, recordid,
      onlythisfield: field, [field]: value,
    }).toString();
    const r = await fetch('/page/submit/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
      body, credentials: 'include',
    });
    return r.text();
  }

  async publish() {
    const body = new URLSearchParams({
      pageid: this.pageid, projectid: this.projectid,
    }).toString();
    const r = await fetch('/page/publish/', {
      method: 'POST',
      headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
      body, credentials: 'include',
    });
    return r.json();
  }
}

// ===== XHR capture for unknown actions =====

function captureSubmits() {
  if (window.__TILDA_XHR_HOOKED) return;
  window.__TILDA_XHR_HOOKED = true;
  window.__TILDA_SUBMITS = [];
  const X = window.XMLHttpRequest;
  const _open = X.prototype.open;
  const _send = X.prototype.send;
  X.prototype.open = function(m, u) { this._u = u; this._m = m; return _open.apply(this, arguments); };
  X.prototype.send = function(body) {
    if (this._u && this._u.includes('/submit/')) {
      window.__TILDA_SUBMITS.push({
        url: this._u,
        method: this._m,
        body: typeof body === 'string' ? body : '(non-string)',
        ts: Date.now(),
      });
    }
    return _send.apply(this, arguments);
  };
  console.log('Capturing /submit/ XHRs into window.__TILDA_SUBMITS');
}

// ===== Fire-and-forget pattern (для долгих циклов в Playwright) =====
//
// Use when MCP browser_evaluate timeouts on long sequential ops.
//
//   window.BG = {step:'init', results:[], errors:[]};
//   (async () => {
//     try {
//       const t = new TildaFeed('100000000001');
//       const posts = await t.list({items:500});
//       window.BG.step = 'editing';
//       for (const [uid, p] of Object.entries(posts)) {
//         const r = await t.edit(uid, {image:'...', mediadata:'...'});
//         window.BG.results.push({uid, error: r.error});
//       }
//       window.BG.step = 'done';
//     } catch(e) { window.BG.errors.push(String(e)); window.BG.step='fatal'; }
//   })();
//
// Then in separate evaluate: read window.BG.step / .results.

// Export for module use (Node.js / Playwright with import)
if (typeof module !== 'undefined') {
  module.exports = {TildaFeed, TildaPage, captureSubmits};
}
