# -*- coding: utf-8 -*-
"""Переименование формы в Яндекс.Формах — без ручного браузера.

Работает через выделенный залогиненный профиль:
    ~/.claude/skills/playwright-automation/profiles/yandex-forms

ТОЧНЫЙ КОНТРАКТ (вытащен перехватом запроса живого интерфейса 11.08.2026):
    POST https://forms.yandex.ru/admin/gateway/root/form/updateSurveyInfo
    {"surveyId": "<id>", "surveyInfo": {"name": "<новое имя>"}}

ГРАБЛИ, на которые я потратил час:
  * Конструктор живёт по /admin/<id>/edit — НЕ /constructor (тот отдаёт «Страница не найдена»).
  * Чтение формы — getSurveyInfo (не getSurveyData: тот отвечает UNKNOWN_SERVICE_ACTION).
  * Имя обязано лежать во вложенном surveyInfo. Плоское {surveyId, name} даёт
    400 value_error.missing, а {id, name} — 400 «invalid format, loc: path».
  * Публичный h1 берётся из того же name: отдельного поля заголовка нет.

Использование:
    python fix_form_title.py <survey_id> "<новый заголовок>"
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PROFILE = Path.home() / ".claude/skills/playwright-automation/profiles/yandex-forms"
GATEWAY = "/admin/gateway/root/form/"

JS_RENAME = """
async ([sid, title]) => {
  const csrf = (window.__DATA__ || {}).csrfToken;
  if (!csrf) return { err: 'нет csrfToken — профиль разлогинен' };
  const r = await fetch('https://forms.yandex.ru' + '%s' + 'updateSurveyInfo', {
    method: 'POST', credentials: 'include',
    headers: { 'content-type': 'application/json', 'x-csrf-token': csrf,
               'x-sdk': '1', 'x-use-collab': '1' },
    body: JSON.stringify({ surveyId: sid, surveyInfo: { name: title } })
  });
  const t = await r.text(); let j; try { j = JSON.parse(t); } catch (e) { j = t; }
  return { status: r.status, body: j };
}
""" % GATEWAY


def rename(survey_id: str, title: str) -> bool:
    with sync_playwright() as pw:
        ctx = pw.chromium.launch_persistent_context(
            str(PROFILE), headless=True, viewport={"width": 1440, "height": 900})
        page = ctx.pages[0] if ctx.pages else ctx.new_page()
        page.goto(f"https://forms.yandex.ru/admin/{survey_id}/edit",
                  wait_until="networkidle", timeout=90000)
        page.wait_for_timeout(2500)

        res = page.evaluate(JS_RENAME, [survey_id, title])
        print("updateSurveyInfo:", res)

        page.goto(f"https://forms.yandex.ru/u/{survey_id}/",
                  wait_until="networkidle", timeout=60000)
        page.wait_for_timeout(2000)
        h1 = page.evaluate(
            "() => { const h = document.querySelector('h1'); return h ? h.textContent.trim() : null; }")
        print("заголовок публичной страницы:", h1)
        ctx.close()
        return h1 == title


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    sys.exit(0 if rename(sys.argv[1], sys.argv[2]) else 1)
