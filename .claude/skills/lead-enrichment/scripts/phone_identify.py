# -*- coding: utf-8 -*-
"""Identify a person from a phone number THEY gave you (inbound, consented).

Usage:  python phone_identify.py "+79161234567"

Legitimate "number -> who is this" for a number the lead voluntarily left you (form, chat,
business card). Three legitimate channels:
  1. Telegram native resolve via your own Telethon (contacts.ImportContacts) — respects the
     target's OWN privacy setting ("who can find me by phone"). If they hid it, returns nothing.
     The contact is deleted right after, so your contact list is not polluted.
  2. (plan) Public web search of the number in quotes — site/signature/2GIS/public profile.
  3. (plan) your Bitrix24 — maybe already a contact.

Requires: TELEGRAM_API_ID / TELEGRAM_API_HASH in ~/.claude/.credentials.master.env and the
existing session ~/.claude/telegram_session.session (same as tg_client.py).

Ethics: use only for a number a lead gave you. This is consented identification, not surveillance.
"""
import sys, io, os, json, asyncio
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def load_env():
    p = Path.home() / '.claude' / '.credentials.master.env'
    if p.exists():
        for line in p.read_text(encoding='utf-8').splitlines():
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                k, _, v = line.partition('=')
                if k.strip() and not os.environ.get(k.strip()):
                    os.environ[k.strip()] = v.strip()

async def tg_resolve(phone):
    from telethon import TelegramClient, functions
    from telethon.tl.types import InputPhoneContact
    api_id = int(os.environ['TELEGRAM_API_ID'])
    api_hash = os.environ['TELEGRAM_API_HASH']
    session = str(Path.home() / '.claude' / 'telegram_session')
    out = []
    async with TelegramClient(session, api_id, api_hash) as client:
        res = await client(functions.contacts.ImportContactsRequest(
            contacts=[InputPhoneContact(client_id=0, phone=phone, first_name='_lead_tmp', last_name='')]))
        for u in res.users:
            # re-fetch the canonical profile (ImportContacts echoes the imported label, not the real name)
            real = u
            try:
                real = await client.get_entity(u.id)
            except Exception:
                pass
            fn = real.first_name if (real.first_name and real.first_name != '_lead_tmp') else None
            out.append({'id': u.id, 'first_name': fn, 'last_name': real.last_name,
                        'username': ('@' + real.username) if real.username else None,
                        'phone': ('+' + u.phone) if u.phone else None,
                        'premium': getattr(real, 'premium', None), 'verified': getattr(real, 'verified', None)})
        if res.users:  # cleanup — don't pollute the contact list
            try:
                await client(functions.contacts.DeleteContactsRequest(id=res.users))
            except Exception:
                pass
    return out

def main(phone):
    load_env()
    result = {'phone': phone, 'telegram': [], 'plan': [
        f'Публичный веб: WebSearch "{phone}" в кавычках — сайт/подпись/2ГИС/публичный профиль.',
        'Наша Bitrix: Skill bitrix24 — поиск контакта по телефону (может уже быть в базе).',
        'Если найден @username — Skill social-intel для forward-досье.',
    ]}
    if os.environ.get('TELEGRAM_API_ID') and os.environ.get('TELEGRAM_API_HASH'):
        try:
            result['telegram'] = asyncio.run(tg_resolve(phone))
            result['telegram_note'] = ('Пусто = номер не в Telegram ИЛИ человек закрыл поиск по номеру (его право).'
                                       if not result['telegram'] else 'Резолв через родную фичу Telegram, контакт удалён после.')
        except Exception as e:
            result['telegram_error'] = str(e)
    else:
        result['telegram_error'] = 'TELEGRAM_API_ID/HASH не заданы'
    return result

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(json.dumps({'error': 'usage: phone_identify.py "<phone the lead gave you>"'}, ensure_ascii=False))
        sys.exit(1)
    print(json.dumps(main(sys.argv[1]), ensure_ascii=False, indent=2))
