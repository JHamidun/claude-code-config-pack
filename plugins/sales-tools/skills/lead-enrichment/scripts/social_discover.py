# -*- coding: utf-8 -*-
"""Cross-network social discovery plan (RU + Western). Person-leg of Mode A.

Usage:  python social_discover.py [--name "ФИО"] [--handle "@user"] [--phone "+7..."] [--company "..."] [--city "..."]
Output: JSON {programmatic:[connector commands to run], search:[WebSearch queries], note}

Emits an exact plan — does NOT execute heavy session connectors itself. Run the listed
commands via the corresponding skills (max-messenger, telegram, headhunter, social-intel) and
the WebSearch queries, then WebFetch any public profile URLs found. See references/social-channels-ru.md.
"""
import sys, io, json, argparse
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

TG = 'python ~/.claude/tools/tg_client.py'
MAX = 'python ~/.claude/tools/max_client.py'

def build(name, handle, phone, company, city):
    prog, search = [], []
    nq = f'"{name}"' if name else ''
    cc = ' '.join(x for x in [name, company, city] if x)

    # programmatic connectors (exact, cheap)
    if phone:
        prog.append(f'{MAX} search-phone {phone}            # MAX по номеру (если лид оставил)')
        prog.append(f'phone_identify.py {phone}             # Telegram-резолв номера (consented)')
    if handle:
        h = handle.lstrip('@')
        prog.append(f'{TG} user-info {h}                    # Telegram публичный профиль')
        prog.append(f'{MAX} user-info {h}                   # MAX профиль')
        prog.append(f'Skill social-intel: forward-досье по {handle} (LinkedIn/IG/X/...)')
    if name:
        prog.append(f'vk_lookup.py --q "{name}"{(" --city " + city) if city else ""}{(" --company " + company) if company else ""}   # VK users.search (если VK_ACCESS_TOKEN задан)')
        prog.append(f'{TG} search "{name}"                  # Telegram публичные совпадения')
        prog.append(f'{MAX} public-search "{name}"          # MAX публичные каналы/профили')
        prog.append(f'Skill headhunter: открытый поиск резюме "{name}" {city}'.rstrip())
        prog.append(f'Skill social-intel: кросс-платформенное досье "{name}"')

    # RU no-API networks → WebSearch site: then WebFetch the profile
    if nq:
        search += [
            f'{nq} site:vk.com',
            f'{nq} {company} site:tenchat.ru'.replace('  ', ' ').strip(),
            f'{nq} site:setka.ru OR site:сетка.рф',
            f'{nq} site:ok.ru',
            f'{nq} site:habr.com OR site:vc.ru',
            f'{nq} site:linkedin.com/in',
            cc,  # generic: personal site / press / conferences
        ]
    if company and not name:
        search.append(f'"{company}" site:vk.com OR site:tenchat.ru   # сотрудники/страница компании')

    return {
        'input': {'name': name, 'handle': handle, 'phone': phone, 'company': company, 'city': city},
        'programmatic': prog,
        'search': [s for s in search if s.strip()],
        'note': 'Запусти programmatic через соответствующие скиллы; прогони search через WebSearch; '
                'WebFetch найденные профили. Совпадение ≥2 сетей = High confidence (scoring.md). '
                'VK users.search доступен при VK_ACCESS_TOKEN (см. social-channels-ru.md).',
    }

if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--name', default=''); ap.add_argument('--handle', default='')
    ap.add_argument('--phone', default=''); ap.add_argument('--company', default=''); ap.add_argument('--city', default='')
    a = ap.parse_args()
    if not any([a.name, a.handle, a.phone, a.company]):
        print(json.dumps({'error': 'need at least one of --name/--handle/--phone/--company'}, ensure_ascii=False)); sys.exit(1)
    print(json.dumps(build(a.name, a.handle, a.phone, a.company, a.city), ensure_ascii=False, indent=2))
