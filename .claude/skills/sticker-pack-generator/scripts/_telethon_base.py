"""Shared Telethon helpers."""
import os, json

from _config import telegram_api_id, telegram_api_hash, telegram_session


def load_credentials():
    """Returns (api_id, api_hash, session_path)."""
    return telegram_api_id(), telegram_api_hash(), telegram_session()


def load_mapping(path):
    """JSON: [{"name":"01-fire","emoji":"🔥"}, ...]"""
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def norm_emoji(e):
    """Strip VS16 for comparison."""
    return e.replace('️', '')


def load_progress(path):
    if not os.path.exists(path): return set()
    return set(open(path, encoding='utf-8').read().splitlines())


def mark_done(path, name):
    with open(path, 'a', encoding='utf-8') as f:
        f.write(name + '\n')
