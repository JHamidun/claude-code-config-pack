/*
 * Yandex Forms builder — self-contained для chrome-devtools evaluate_script.
 * Аутентификация: cookie-сессия залогиненного браузера (Яндекс 360) + CSRF из window.__DATA__.
 * Перед запуском: navigate_page -> https://forms.yandex.ru/admin/  (чтобы был свежий csrfToken).
 *
 * Использование: оберни весь файл в async-функцию для evaluate_script и заполни массив items
 * каждой формы по DSL. Вызови build(name, items). Возвращает {surveyId, fill, ok, errs}.
 *
 * DSL (см. SKILL.md):
 *   ['S','заголовок блока / интро']
 *   ['T','вопрос', required?, 'подсказка?']           короткий текст
 *   ['P','вопрос', required?, 'подсказка?']           абзац
 *   ['R','вопрос', [опции], required?]                один вариант (radio)
 *   ['C','вопрос', [опции], required?]                несколько вариантов (checkbox -> view:'checks')
 *   ['SC','вопрос','низ','верх', required?]           шкала 1..5
 *
 * ГРАБЛЯ: несколько вариантов = view:'checks' (НЕ 'checkbox'; иначе сервер делает radio).
 */
async () => {
  const csrf = window.__DATA__.csrfToken;
  async function g(method, body) {
    const r = await fetch('https://forms.yandex.ru/admin/gateway/root/form/' + method, {
      method: 'POST', credentials: 'include',
      headers: { 'content-type': 'application/json', 'x-csrf-token': csrf, 'x-sdk': '1', 'x-use-collab': '1' },
      body: JSON.stringify(body)
    });
    const t = await r.text(); let j; try { j = JSON.parse(t); } catch (e) { j = t; }
    return { status: r.status, j };
  }
  let C = 1;
  const iid = () => 100000000 + (C++) * 7 + Math.floor(Math.random() * 5);
  const kdig = () => '' + (Math.floor(Math.random() * 9e15) + 1e15);
  const opts = arr => arr.map(text => ({ id: iid(), text, key: kdig(), hidden: false }));
  function mkq(it) {
    const k = it[0];
    if (k === 'S')  return { id: iid(), key: 'statement_' + kdig(),        type: 'text', view: 'textinput', title: it[1] };
    if (k === 'T')  return { id: iid(), key: 'answer_short_text_' + kdig(), type: 'text', view: 'textinput', title: it[1] + (it[3] ? '\n' + it[3] : ''), required: !!it[2] };
    if (k === 'P')  return { id: iid(), key: 'answer_long_text_' + kdig(),  type: 'text', view: 'textarea',  title: it[1] + (it[3] ? '\n' + it[3] : ''), required: !!it[2] };
    if (k === 'R')  return { id: iid(), key: 'answer_choices_' + kdig(), type: 'choices', view: 'radio',  widget: 'radio',    title: it[1], required: !!it[3], options: opts(it[2]), sort: 'natural' };
    if (k === 'C')  return { id: iid(), key: 'answer_choices_' + kdig(), type: 'choices', view: 'checks', widget: 'checkbox', title: it[1], required: !!it[3], options: opts(it[2]), sort: 'natural' };
    if (k === 'SC') return { id: iid(), key: 'answer_choices_' + kdig(), type: 'choices', view: 'radio',  widget: 'radio',    title: it[1] + '\n(1 — ' + it[2] + ', 5 — ' + it[3] + ')', required: !!it[4], options: opts(['1','2','3','4','5']), sort: 'natural' };
  }
  async function build(name, items) {
    const cr = await g('createFormFromTemplate', { templateId: 'empty_form_v2' });
    const sid = cr.j && (cr.j.id || cr.j.surveyId);
    if (!sid) return { name, fail: 'create', cr };
    const sd = await g('getSurveyData', { surveyId: sid });
    if (sd.j) { sd.j.name = name; await g('updateSurveyData', { surveyId: sid, survey: sd.j }); }
    const ql = await g('surveyQuestionsLA', { surveyId: sid });
    let pageId = null; const nodes = ql.j && ql.j.nodes;
    if (Array.isArray(nodes)) { const pg = nodes.find(n => n.type === 'page'); if (pg) pageId = pg.id; }
    if (!pageId) { const ap = await g('addPage', { surveyId: sid }); pageId = ap.j && (ap.j.id || ap.j.pageId); }
    let ok = 0; const errs = [];
    for (let i = 0; i < items.length; i++) {
      const res = await g('addSurveyQuestion', { surveyId: sid, page: pageId, position: i, question: mkq(items[i]) });
      if (res.status === 200) ok++; else errs.push({ i, t: (items[i][1] || '').slice(0, 25), status: res.status });
    }
    const pub = await g('publishSurvey', { surveyId: sid });
    return { name, surveyId: sid, total: items.length, ok, errs, pub: pub.status, fill: 'https://forms.yandex.ru/u/' + sid + '/' };
  }

  // ===== ЗАПОЛНИ items СВОИМ ОПРОСОМ И ВЫЗОВИ build(...) =====
  const items = [
    ['S', 'Интро / описание формы — отображается сверху'],
    ['S', 'Блок 1. О себе'],
    ['T', 'ФИО', true],
    ['T', 'Рабочий email', true, 'Подсказка под полем'],
    ['R', 'Один из вариантов', ['Вариант 1', 'Вариант 2', 'Другое'], true],
    ['C', 'Несколько вариантов', ['A', 'B', 'C', 'Другое']],
    ['SC', 'Оцените по шкале', 'плохо', 'отлично'],
    ['P', 'Развёрнутый ответ']
  ];
  return await build('Название новой формы', items);
};
