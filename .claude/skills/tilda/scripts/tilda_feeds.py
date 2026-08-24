# -*- coding: utf-8 -*-
"""Tilda Feeds API client — direct fetch to /submit/ urlencoded.

Использование:
    client = TildaFeedsClient(cookies_dict)  # или from_browser_export()
    posts = client.list_posts('100000000001')
    new = client.add_post('100000000001', 'Заголовок')
    client.edit_post(new['data']['uid'], title='...', descr='...', date='...',
                     url='...', image='...', mediadata='...', tags='...')
    client.activate_post(new['data']['uid'])

Для получения cookies — открой tilda.cc после логина в браузере, скопируй из
DevTools → Application → Cookies. Или используй Playwright и грабни через
context.cookies().
"""
from __future__ import annotations
import os
import requests
from typing import Optional, Any
from urllib.parse import urlencode


class TildaFeedsClient:
    BASE = 'https://feeds.tilda.ru/submit/'

    def __init__(self, cookies: dict[str, str]):
        self.s = requests.Session()
        self.s.cookies.update(cookies)
        self.s.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'
        self.s.headers['Origin'] = 'https://feeds.tilda.ru'

    def _post(self, action: str, **params) -> dict[str, Any]:
        body = urlencode({**params, 'action': action})
        r = self.s.post(self.BASE, data=body, timeout=30)
        r.raise_for_status()
        try:
            return r.json()
        except ValueError:
            return {'data': None, 'error': f'non-json response: {r.text[:200]}'}

    # ===== Posts CRUD =====

    def list_posts(self, feeduid: str, partuid: str = '', page: int = 1, items: int = 50) -> dict:
        """List posts in feed. Returns dict: {data: {posts: {<uid>: {...}}, total, page, ...}, error}.

        IMPORTANT: posts is OBJECT keyed by uid, not array.
        """
        return self._post('posts_GetList', feeduid=feeduid, partuid=partuid,
                          page=str(page), items=str(items))

    def get_post(self, postuid: str) -> dict:
        """Get full post data including descr, image, url, tags, body."""
        return self._post('posts_Get', postuid=postuid)

    def add_post(self, feeduid: str, title: str, partuid: str = '') -> dict:
        """Create new post. Returns {data: {uid, title}, error}.

        WARNING: Only title, feeduid, partuid are accepted. Use edit_post() for other fields.
        """
        return self._post('posts_Add', feeduid=feeduid, title=title, partuid=partuid)

    def edit_post(
        self,
        postuid: str,
        *,
        title: Optional[str] = None,
        descr: Optional[str] = None,
        date: Optional[str] = None,        # YYYY-MM-DD HH:MM
        url: Optional[str] = None,
        tags: Optional[str] = None,        # comma-separated
        image: Optional[str] = None,       # CDN url
        mediadata: Optional[str] = None,   # same CDN url
        text: Optional[str] = None,        # HTML body
        textoriginal: Optional[str] = None,
        alias: Optional[str] = None,
        feeduid_for_title_lookup: Optional[str] = None,
    ) -> dict:
        """Update post fields. Tilda silently ignores unknown fields.

        For cover image to render in feed cards: SET BOTH image AND mediadata to same URL.

        IMPORTANT: posts_Edit is PUT (full replace), not PATCH. If you don't pass `title`,
        Tilda treats it as empty string → returns "Post title is empty" error.
        Pass `feeduid_for_title_lookup` to auto-fetch and preserve existing title.
        """
        params = {'postuid': postuid}
        for k, v in {
            'title': title, 'descr': descr, 'date': date, 'url': url, 'tags': tags,
            'image': image, 'mediadata': mediadata, 'text': text,
            'textoriginal': textoriginal, 'alias': alias,
        }.items():
            if v is not None:
                params[k] = v
        # Auto-fetch title if not passed and feeduid given (avoid title nullification)
        if 'title' not in params and feeduid_for_title_lookup:
            lst = self.list_posts(feeduid_for_title_lookup, items=500)
            posts = (lst.get('data') or {}).get('posts', {})
            existing_title = posts.get(postuid, {}).get('title', '')
            if existing_title:
                params['title'] = existing_title
        return self._post('posts_Edit', **params)

    def activate_post(self, postuid: str) -> dict:
        """TOGGLE post visibility. Check current active state first if you want a setter."""
        return self._post('posts_Active', postuid=postuid)

    def ensure_active(self, postuid: str, feeduid: str) -> dict:
        """Idempotent activate — toggle only if currently inactive."""
        lst = self.list_posts(feeduid, items=500)
        post = (lst.get('data') or {}).get('posts', {}).get(postuid)
        if post and post.get('active') == 'y':
            return {'data': {'active': 'y'}, 'error': '', 'noop': True}
        return self.activate_post(postuid)

    def delete_post(self, postuid: str) -> dict:
        """Move post to trash. Use trash_empty() to delete permanently."""
        return self._post('posts_Delete', postuid=postuid)

    def restore_post(self, postuid: str) -> dict:
        return self._post('posts_Restore', postuid=postuid)

    def pin_post(self, postuid: str) -> dict:
        return self._post('posts_Pin', postuid=postuid)

    def reorder(self, feeduid: str, postuids_in_order: list[str]) -> dict:
        return self._post('posts_Reorder', feeduid=feeduid,
                          postuids=','.join(postuids_in_order))

    def duplicate_post(self, postuid: str) -> dict:
        return self._post('posts_Duplicate', postuid=postuid)

    # ===== Feeds =====

    def list_feeds(self, projectid: str) -> dict:
        return self._post('feeds_GetList', projectid=projectid)

    def get_feed(self, feeduid: str) -> dict:
        return self._post('feeds_Get', feeduid=feeduid)

    def list_parts(self, feeduid: str) -> dict:
        """List categories (parts) of the feed."""
        return self._post('parts_GetList', feeduid=feeduid)

    # ===== Helpers =====

    def find_posts_by_title(self, feeduid: str, title_substr: str) -> list[dict]:
        """Convenience: find posts whose title contains substring (case-insensitive)."""
        lst = self.list_posts(feeduid, items=500)
        posts = (lst.get('data') or {}).get('posts', {})
        out = []
        s = title_substr.lower()
        for uid, p in posts.items():
            if s in (p.get('title') or '').lower():
                out.append({'uid': uid, **p})
        return out

    def safe_edit_post(self, postuid: str, **updates) -> dict:
        """SAFE update: fetch existing fields via posts_Get, merge updates, send full PUT.

        Use this instead of edit_post() for any partial update. posts_Edit is PUT —
        any field not passed gets nullified (active, parts, descr, url, tags, text).
        This wrapper preserves all existing fields and only overrides what you specify.

        Example:
            client.safe_edit_post(uid, image=cdn, mediadata=cdn)
            # Preserves title, descr, date, url, tags, active, parts, etc.
        """
        existing = self.get_post(postuid).get('data') or {}
        # Build full payload from existing + updates
        merged = {}
        for k in ['title', 'descr', 'date', 'url', 'tags', 'image', 'mediadata',
                  'text', 'textoriginal', 'alias', 'active', 'mediatype']:
            if k in existing and existing[k] is not None:
                merged[k] = existing[k]
        merged.update(updates)
        merged['postuid'] = postuid
        return self._post('posts_Edit', **merged)

    def bulk_set_cover(self, feeduid: str, title_to_cover_url: dict[str, str],
                       normalize_fn=None) -> list[dict]:
        """For each post, find by normalized title and set image+mediadata.

        Uses safe_edit_post() under the hood — preserves all other fields including active.

        Args:
            title_to_cover_url: map normalized_title → CDN url
            normalize_fn: optional callable str→str. Default: lower + strip punct.
        """
        if normalize_fn is None:
            import re
            def norm(s: str) -> str:
                s = (s or '').lower()
                s = re.sub(r'[«»"\'()\[\].,:;\—\-!?]', '', s)
                return re.sub(r'\s+', ' ', s).strip()
            normalize_fn = norm

        lst = self.list_posts(feeduid, items=500)
        posts = (lst.get('data') or {}).get('posts', {})
        results = []
        for uid, p in posts.items():
            key = normalize_fn(p.get('title') or '')
            cover = title_to_cover_url.get(key)
            if not cover:
                results.append({'uid': uid, 'title': p.get('title'),
                                'matched': False, 'reason': 'no cover for this title'})
                continue
            # Pass title explicitly to avoid title nullification (posts_Edit is PUT, not PATCH)
            r = self.edit_post(uid, title=p.get('title') or '', image=cover, mediadata=cover)
            results.append({'uid': uid, 'title': p.get('title'),
                            'matched': True, 'cover': cover, 'error': r.get('error')})
        return results


# ===== Tilda CDN upload (no auth required) =====

class TildaCDN:
    """Upload images to Tilda CDN. PDF and other docs are forbidden."""
    UPLOAD_URL = 'https://upload.tildacdn.com/api/upload/'

    def __init__(self, publickey: Optional[str] = None, uploadkey: Optional[str] = None):
        # Fallback на переменные окружения TILDA_PUBLIC_KEY / TILDA_UPLOAD_KEY, если не передано явно
        self.publickey = publickey or os.getenv('TILDA_PUBLIC_KEY')
        self.uploadkey = uploadkey or os.getenv('TILDA_UPLOAD_KEY')

    def upload(self, file_path: str, mime: str = 'image/webp') -> str:
        from pathlib import Path
        p = Path(file_path)
        with open(p, 'rb') as f:
            files = {'files': (p.name, f, mime)}
            data = {'publickey': self.publickey, 'uploadkey': self.uploadkey,
                    'acceptedFiles': 'image/*'}
            r = requests.post(
                self.UPLOAD_URL, data=data, files=files,
                headers={'Origin': 'https://feeds.tilda.ru'}, timeout=60,
            )
        resp = r.json()
        if isinstance(resp, dict) and resp.get('result'):
            return resp['result'][0].get('cdnUrl')
        raise RuntimeError(f'CDN upload failed: {resp}')


# ===== Tilda Page editor (saverecord field) =====

class TildaPageEditor:
    """Edit page block settings (e.g. Feed-block input1 for posts-per-page limit)."""
    EDIT = 'https://tilda.cc/page/edit/'
    SUBMIT = 'https://tilda.cc/page/submit/'
    PUBLISH = 'https://tilda.cc/page/publish/'

    def __init__(self, cookies: dict[str, str]):
        self.s = requests.Session()
        self.s.cookies.update(cookies)
        self.s.headers['Content-Type'] = 'application/x-www-form-urlencoded; charset=UTF-8'

    def get_record_settings(self, pageid: str, recordid: str) -> dict:
        body = urlencode({'comm': 'editrecordsettings', 'pageid': pageid,
                          'recordid': recordid, 'tab': 'settings'})
        r = self.s.post(self.EDIT, data=body, timeout=30)
        return r.json()

    def save_field(self, pageid: str, recordid: str, field: str, value: str) -> str:
        """Save single field of a record. Returns 'OK' on success."""
        body = urlencode({'comm': 'saverecord', 'pageid': pageid, 'recordid': recordid,
                          'onlythisfield': field, field: value})
        r = self.s.post(self.SUBMIT, data=body, timeout=30)
        return r.text

    def publish(self, pageid: str, projectid: str) -> dict:
        body = urlencode({'pageid': pageid, 'projectid': projectid})
        r = self.s.post(self.PUBLISH, data=body, timeout=60)
        return r.json()


# ===== Browser-based session helpers =====

def login_and_handshake(playwright_page, projectid: str, feeduid: str,
                        any_pageid: str, email: str, password: str,
                        timeout_ms: int = 20000) -> bool:
    """Login to tilda.cc and walk the handshake chain so feeds.tilda.ru session is valid.

    Without this chain, feeds.tilda.ru/submit/ returns {"error": "RELOGIN"} and
    feeds.tilda.ru/posts/?feeduid=... redirects back to tilda.ru/projects/.

    Order of URLs is critical — the page-editor step (tilda.cc/page/?pageid=...)
    is what propagates session to feeds.tilda.ru. Verified 2026-04-25.

    Args:
        playwright_page: a Playwright sync page (from launch().new_context().new_page())
        projectid: Tilda project numeric id (e.g. '12345678')
        feeduid: feed numeric id (e.g. '100000000001')
        any_pageid: ANY real pageid in the project (e.g. '70000005') — used as bridge
        email/password: Tilda credentials
        timeout_ms: per-goto timeout

    Returns:
        True if final URL is feeds.tilda.ru/posts/?feeduid=... (handshake succeeded).
    """
    import re as _re
    page = playwright_page

    # 1. login
    page.goto('https://tilda.cc/login/', wait_until='domcontentloaded', timeout=timeout_ms)
    page.wait_for_timeout(800)
    try:
        page.fill('input[name="email"], input[type="email"]', email, timeout=5000)
        page.fill('input[name="password"], input[type="password"]', password, timeout=5000)
        page.click('button[type="submit"], button:has-text("Войти")', timeout=5000)
    except Exception:
        pass
    try:
        page.wait_for_url(_re.compile(r'projects'), timeout=15000)
    except Exception:
        pass
    page.wait_for_timeout(1200)

    # 2. handshake chain — order matters
    chain = [
        f'https://tilda.cc/projects/projectinfo/?projectid={projectid}',
        f'https://tilda.cc/projects/manage/?projectid={projectid}',
        f'https://tilda.cc/page/?pageid={any_pageid}&projectid={projectid}',  # KEY step
        f'https://feeds.tilda.ru/feeds/?projectid={projectid}',
        f'https://feeds.tilda.ru/posts/?feeduid={feeduid}&projectid={projectid}',
    ]
    for url in chain:
        try:
            page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
            page.wait_for_timeout(1500)
        except Exception:
            continue
        if 'feeds.tilda.ru/posts' in page.url and f'feeduid={feeduid}' in page.url:
            return True
    return 'feeds.tilda.ru/posts' in page.url


# JS helpers for in-page fetch from feeds.tilda.ru origin (avoids CORS/RELOGIN)
SUB_FETCH_JS = r"""
async ({action, params}) => {
  const body = new URLSearchParams(Object.assign({}, params, {action})).toString();
  const r = await fetch('/submit/', {
    method: 'POST',
    credentials: 'include',
    headers: {'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8'},
    body,
  });
  const text = await r.text();
  try { return JSON.parse(text); } catch (e) { return {raw: text.slice(0, 500)}; }
}
"""


def in_page_call(page, action: str, params: Optional[dict] = None) -> dict:
    """Call feeds.tilda.ru/submit/ via in-page fetch. Page must be on feeds.tilda.ru/posts/.

    This is the only reliable way to call the feeds API after Playwright login —
    Python requests with extracted cookies returns RELOGIN. Same-origin fetch works.
    """
    return page.evaluate(SUB_FETCH_JS, {'action': action, 'params': params or {}})


def safe_in_page_edit(page, feeduid: str, postuid: str, **updates) -> dict:
    """Safe partial update: PRESERVES active/parts/title/etc.

    ⚠️ posts_Get does NOT return `active` field — only posts_GetList does.
    Without this helper, doing posts_Edit with image+mediadata silently sets
    active='' on the post and it disappears from the site.

    Strategy: fetch full state from posts_GetList (has `active` + `parts`),
    merge with posts_Get (has `descr`/`text`/`mediatype` etc.), then send PUT.

    Args:
        page: Playwright page on feeds.tilda.ru/posts/
        feeduid: feed numeric id (needed to read `active` field)
        postuid: post id to update
        **updates: fields to override (e.g. image='https://...', mediadata='https://...')

    Returns:
        Tilda response dict with `error`/`data`.
    """
    # 1. Get full post via posts_Get (has descr, text, etc but NOT active)
    got = in_page_call(page, 'posts_Get', {'postuid': postuid})
    full = (got.get('data') or {}) if isinstance(got, dict) else {}

    # 2. Get list to read `active` and `parts` (NOT in posts_Get response)
    lst = in_page_call(page, 'posts_GetList',
                       {'feeduid': feeduid, 'partuid': '', 'page': '1', 'items': '500'})
    list_post = (lst.get('data') or {}).get('posts', {}).get(postuid, {})

    payload = {'postuid': postuid}
    # Copy from posts_Get (rich fields)
    for k in ['title', 'descr', 'date', 'url', 'tags', 'text',
              'textoriginal', 'alias', 'mediatype', 'image', 'mediadata']:
        if full.get(k) is not None:
            payload[k] = full[k]
    # Override active+parts from posts_GetList (authoritative for these)
    if list_post.get('active') is not None:
        payload['active'] = list_post['active'] or 'y'
    else:
        payload['active'] = 'y'  # default to visible
    if list_post.get('parts') is not None:
        payload['parts'] = list_post['parts']

    # Apply user updates last (they win)
    payload.update(updates)

    return in_page_call(page, 'posts_Edit', payload)


if __name__ == '__main__':
    print('TildaFeedsClient — see SKILL.md for usage examples')
    print(f'Importable from: {__file__}')
