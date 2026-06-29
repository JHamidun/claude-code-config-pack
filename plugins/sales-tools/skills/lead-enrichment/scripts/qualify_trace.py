# -*- coding: utf-8 -*-
"""Mode A orchestrator: a fragment -> a dossier skeleton + a routing plan.

Usage:  python qualify_trace.py "<fragment>"
Output: JSON {input, normalized, company, plan:[steps for Claude]}

What it does deterministically:
  - normalize the fragment (normalize_input.py)
  - if it resolves to a company (corporate email / domain / inn) -> pull firmographics
  - emit a `plan` of remaining PUBLIC research steps for Claude to execute via skills
    (social-intel, linkedin, headhunter, WebSearch) + the Bitrix cross-check.

It intentionally does NOT do the person/social web research itself — that is high-freedom
and belongs to Claude driving the social-intel / linkedin / headhunter skills.
"""
import sys, io, json, subprocess, os
from typing import Any
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

SK = os.path.dirname(os.path.abspath(__file__))

def run(script, *args) -> Any:
    try:
        r = subprocess.run(['python', os.path.join(SK, script), *args],
                           capture_output=True, text=True, timeout=60, encoding='utf-8')
        return json.loads(r.stdout or 'null')
    except Exception as e:
        return {'error': str(e)}

def plan_for(t, v, d):
    steps = []
    if t == 'email':
        if d.get('corporate'):
            steps.append(f"Компания определена по домену {d['domain']}. Найти ФИО владельца ящика: WebSearch '{v}' + сайт компании раздел Команда/Контакты.")
        else:
            steps.append(f"Свободный ящик ({d['domain']}) — это физлицо. Идти по имени/нику: WebSearch '{v}', Skill social-intel по email.")
        steps.append(f"Skill social-intel: forward-досье по '{v}' (linktree/komi, соцсети).")
    elif t == 'phone':
        steps.append("Оператор/регион уже в normalized. Проверить телефон в НАШЕЙ Bitrix (bitrix24 skill, поиск контакта по телефону).")
        steps.append("Публичный след: WebSearch номера в кавычках (сайт/подпись/2ГИС/публичный профиль). Если номер оставил лид — phone_identify.py.")
    elif t in ('name',):
        for var in d.get('variants', [])[:1]:
            steps.append(f"WebSearch '{var} site:linkedin.com/in' и '{v}' + предполагаемая компания.")
        steps.append("Skill headhunter: открытый поиск резюме по ФИО (если роль/город известны).")
        steps.append("Skill social-intel: кросс-платформенное досье по ФИО.")
    elif t in ('username', 'url'):
        steps.append(f"Skill social-intel: forward-досье по '{v}' (это и есть его профиль).")
        if t == 'username':
            steps.append(f"Публичный Telegram (legit): python ~/.claude/tools/tg_client.py user-info {v} — публичный профиль/имя.")
    if t in ('name', 'username', 'phone'):
        steps.append("Публичный Telegram через свой Telethon: tg_client.py search/mentions — найти публичный @username, канал, упоминания.")
    elif t in ('domain', 'inn', 'ogrn'):
        steps.append("Компания-leg готов. ЛПР: Skill linkedin (компания + фильтр должностей) + сайт раздел Руководство.")
    steps.append("Bitrix cross-check: есть ли уже в CRM (email/phone/ИНН) — сделки, касания, менеджер, дубль/реанимация.")
    steps.append("Сигналы: последние интервью/посты/выступления (social-intel / perplexity) — о чём пишет, на что реагирует.")
    steps.append("Скоринг по references/scoring.md: confidence + fit + reachability. Затем оформить досье по шаблону из SKILL.md.")
    return steps

def main(fragment):
    norm = run('normalize_input.py', fragment)
    t, v, d = norm.get('type'), norm.get('value'), norm.get('derived', {})
    company = None
    if t == 'email' and d.get('corporate'):
        company = run('domain_to_company.py', d['domain'])
    elif t == 'domain':
        company = run('domain_to_company.py', v)
    elif t in ('inn', 'ogrn'):
        company = run('dadata_lookup.py', v)
        if not company or (isinstance(company, dict) and company.get('error')):
            company = run('egrul_lookup.py', v)
    elif t == 'phone':
        norm['phone_lookup'] = run('phone_lookup.py', v)
    return {'input': fragment, 'normalized': norm, 'company': company,
            'plan': plan_for(t, v, d)}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: qualify_trace.py "<fragment>"'}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(main(' '.join(sys.argv[1:])), ensure_ascii=False, indent=2))
