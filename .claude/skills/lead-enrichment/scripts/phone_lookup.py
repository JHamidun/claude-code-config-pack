# -*- coding: utf-8 -*-
"""RU phone -> operator + region from the public numbering plan (Rossvyaz DEF/ABC codes).

Usage:  python phone_lookup.py "+1234567890"
Output: JSON {phone, def_code, operator, region}

No PII. Uses the public Rossvyaz allocation registry (operator + region per DEF block).
Tries the `phonenumbers` lib for carrier/region if installed; otherwise falls back to a
built-in DEF-prefix map covering the major mobile operators.
"""
import sys, io, re, json
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# Coarse DEF (mobile, 9xx) operator map by 3-digit prefix block. Public numbering plan.
DEF_OPERATOR = {
    'ClientCorp8': ['910','911','912','913','914','915','916','917','918','919','980','981','982','983','984','985','986','987','988','989','892','958'],
    'МегаФон': ['920','921','922','923','924','925','926','927','928','929','930','931','932','933','934','936','937','938','939'],
    'Билайн': ['903','905','906','909','960','961','962','963','964','965','966','967','968','903'],
    'Tele2': ['900','901','902','904','908','950','951','952','953','977','991','992','993','994','995','996','999'],
    'Yota': ['999','958'],
    'Сбермобайл': ['958','991'],
}

def def_operator(nat):
    pref = nat[:3]
    for op, blocks in DEF_OPERATOR.items():
        if pref in blocks:
            return op
    return 'неизвестен (см. rossvyaz / номер перенесён по MNP)'

def lookup(raw):
    digits = re.sub(r'\D', '', raw)
    if len(digits) == 11 and digits[0] in '78':
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    nat = digits[1:] if digits.startswith('7') else digits
    out = {'phone': '+' + digits, 'national': nat, 'def_code': nat[:3]}
    try:
        import phonenumbers
        from phonenumbers import carrier, geocoder
        p = phonenumbers.parse('+' + digits, None)
        out['operator'] = carrier.name_for_number(p, 'ru') or def_operator(nat)
        out['region'] = geocoder.description_for_number(p, 'ru')
        out['valid'] = phonenumbers.is_valid_number(p)
        out['line_type'] = str(phonenumbers.number_type(p))
    except Exception:
        out['operator'] = def_operator(nat)
        out['region'] = 'мобильный (DEF) — регион определяется по MNP, см. rossvyaz.gov.ru'
        out['note'] = 'pip install phonenumbers для точного оператора/региона'
    out['mnp_warning'] = 'Оператор мог смениться по переносу номера (MNP) — это исходный владелец блока.'
    return out

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: phone_lookup.py "<phone>"'}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(lookup(' '.join(sys.argv[1:])), ensure_ascii=False, indent=2))
