"""
Your CRM API клиент с retry, throttling, пагинацией.
Общий модуль для всех отчётов sales-manager-audit.

Использование:
    from bx_client import bx, bx_all, WEBHOOK

    data = bx('crm.deal.list', {'filter': {'ASSIGNED_BY_ID': 3956}})
    all_deals = bx_all('crm.deal.list', {'filter': {'ASSIGNED_BY_ID': 3956}})
"""
import os
import sys
import time
import requests
from dotenv import load_dotenv

# Fix Windows encoding
try:
    sys.stdout.reconfigure(encoding='utf-8')  # type: ignore
except Exception:
    pass
os.environ['PYTHONIOENCODING'] = 'utf-8'

# Load credentials
load_dotenv(os.path.expanduser('~/.claude/.credentials.master.env'))

BASE_URL = os.getenv('CRM_PROD_BASE_URL', '')
WEBHOOK_PATH = os.getenv('CRM_PROD_WEBHOOK_PATH', '')

if not BASE_URL or not WEBHOOK_PATH:
    raise RuntimeError('Не найдены CRM_PROD_BASE_URL / CRM_PROD_WEBHOOK_PATH в ~/.claude/.credentials.master.env')

WEBHOOK = BASE_URL + WEBHOOK_PATH

# Alternative envs
ENVS = {
    'prod': BASE_URL + WEBHOOK_PATH,
    'dev1': (os.getenv('CRM_DEV_BASE_URL') or '') + (os.getenv('CRM_DEV_WEBHOOK_PATH') or ''),
    'dev2': (os.getenv('CRM_DEV2_BASE_URL') or '') + (os.getenv('CRM_DEV2_WEBHOOK_PATH') or ''),
}


def bx(method: str, params=None, retries: int = 5, timeout: int = 90, env: str = 'prod'):
    """
    Call Your CRM REST API method with retry and throttling.

    Args:
        method: API method name (e.g. 'crm.deal.list')
        params: request parameters (dict)
        retries: retry count on failure (default 5)
        timeout: request timeout in seconds (default 90)
        env: environment 'prod' | 'dev1' | 'dev2'

    Returns:
        dict with 'result', 'total', 'next' keys (or 'error' on total failure)
    """
    webhook = ENVS.get(env, WEBHOOK)
    if not webhook:
        return {'error': f'No webhook for env={env}', 'result': []}

    url = f'{webhook}/{method}'
    last_error = None

    for attempt in range(retries):
        try:
            r = requests.post(url, json=params or {}, timeout=timeout)
            data = r.json()
            if 'error' in data and 'QUERY_LIMIT_EXCEEDED' in str(data.get('error', '')):
                time.sleep(2)
                continue
            return data
        except (requests.exceptions.RequestException, ValueError) as e:
            last_error = e
            wait = min(2 ** attempt, 30)
            time.sleep(wait)

    return {'error': f'Failed after {retries} retries: {last_error}', 'result': []}


def bx_all(method: str, params=None, limit: int = 20000, throttle: float = 0.4, env: str = 'prod'):
    """
    Fetch all records with pagination.

    Args:
        method: API method
        params: request parameters
        limit: max records to return (default 20000)
        throttle: sleep between pages in seconds (default 0.4)
        env: environment

    Returns:
        list of records
    """
    params = dict(params or {})
    result = []
    start = 0

    while True:
        params['start'] = start
        data = bx(method, params, env=env)
        items = data.get('result', [])

        # Handle nested structure (like tasks.task.list)
        if isinstance(items, dict):
            items = items.get('tasks', items.get('items', []))

        result.extend(items)

        if 'next' not in data or len(result) >= limit:
            break

        start = data['next']
        time.sleep(throttle)

    return result


def bx_batch(commands: dict, env: str = 'prod'):
    """
    Execute up to 50 API calls in single batch request.

    Args:
        commands: dict {label: 'method?param=value'}

    Returns:
        dict with 'result' containing per-label results
    """
    return bx('batch', {'halt': 0, 'cmd': commands}, env=env)


def safe_float(v) -> float:
    """Safe float conversion."""
    try:
        return float(v) if v else 0.0
    except (ValueError, TypeError):
        return 0.0


def safe_int(v) -> int:
    """Safe int conversion."""
    try:
        return int(v) if v else 0
    except (ValueError, TypeError):
        return 0


def parse_dt(s: str):
    """Parse Bitrix ISO datetime string."""
    from datetime import datetime
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace('Z', '+00:00').split('+')[0])
    except (ValueError, AttributeError):
        return None


def resolve_manager_id(query: str) -> str:
    """
    Resolve manager by name or ID.
    Returns user ID as string.
    """
    # If already numeric, return as is
    if str(query).isdigit():
        return str(query)

    # Search by name
    parts = query.strip().split()
    filter_params = {'ACTIVE': True}
    if len(parts) == 1:
        filter_params['LAST_NAME'] = parts[0]
    else:
        filter_params['LAST_NAME'] = parts[0]
        # NAME could also be checked

    users = bx('user.get', {
        'filter': filter_params,
        'select': ['ID', 'NAME', 'LAST_NAME', 'WORK_POSITION']
    })

    result = users.get('result', [])
    if not result:
        # Try by first name
        users = bx('user.get', {
            'filter': {'ACTIVE': True, 'NAME': parts[0]},
            'select': ['ID', 'NAME', 'LAST_NAME', 'WORK_POSITION']
        })
        result = users.get('result', [])

    if not result:
        raise ValueError(f'Не найден менеджер: {query}')

    if len(result) > 1:
        # Try to disambiguate by first name
        if len(parts) >= 2:
            matches = [u for u in result if parts[1].lower() in (u.get('NAME') or '').lower()]
            if matches:
                return matches[0]['ID']
        # Return first match with warning
        print(f'[!] Найдено {len(result)} совпадений для "{query}", беру первого: '
              f'{result[0].get("NAME")} {result[0].get("LAST_NAME")}', file=sys.stderr)

    return result[0]['ID']


def resolve_manager_ids(query: str) -> list:
    """Resolve comma-separated list of manager names/IDs to list of IDs."""
    return [resolve_manager_id(x.strip()) for x in query.split(',') if x.strip()]


def parse_period(period: str) -> tuple:
    """
    Parse period string to (start_iso, end_iso).

    Supported formats:
        '2026-04-07:2026-05-13' — explicit range
        '2026-Q2' — quarter
        '2026-05' — month
        'last-30d' — last 30 days from today
        'all' — no bounds
    """
    from datetime import datetime, timedelta

    if period == 'all':
        return None, None

    if period == 'today':
        today = datetime.now().strftime('%Y-%m-%d')
        return f'{today}T00:00:00', f'{today}T23:59:59'

    if period.startswith('last-') and period.endswith('d'):
        days = int(period[5:-1])
        end = datetime.now()
        start = end - timedelta(days=days)
        return start.strftime('%Y-%m-%dT00:00:00'), end.strftime('%Y-%m-%dT23:59:59')

    if ':' in period:
        s, e = period.split(':', 1)
        return f'{s.strip()}T00:00:00', f'{e.strip()}T23:59:59'

    # Quarter: 2026-Q2
    if '-Q' in period:
        year, q = period.split('-Q')
        q = int(q)
        m_start = (q - 1) * 3 + 1
        m_end = m_start + 2
        import calendar
        last_day = calendar.monthrange(int(year), m_end)[1]
        return f'{year}-{m_start:02d}-01T00:00:00', f'{year}-{m_end:02d}-{last_day:02d}T23:59:59'

    # Month: 2026-05
    if len(period) == 7 and '-' in period:
        year, month = period.split('-')
        import calendar
        last_day = calendar.monthrange(int(year), int(month))[1]
        return f'{period}-01T00:00:00', f'{period}-{last_day:02d}T23:59:59'

    raise ValueError(f'Неизвестный формат периода: {period}')


# Cache for user names
_user_cache = {}

def get_user_name(uid: str) -> str:
    """Get user full name with caching."""
    if not uid or uid == '0':
        return '—'
    if uid in _user_cache:
        return _user_cache[uid]
    u = bx('user.get', {'ID': uid, 'select': ['ID', 'NAME', 'LAST_NAME']})
    r = u.get('result', [])
    if r:
        name = f"{r[0].get('NAME', '')} {r[0].get('LAST_NAME', '')}".strip()
        _user_cache[uid] = name
        return name
    return f'ID:{uid}'


# Cache for funnel stages
_stage_cache = {}

def get_stage_names(category_id: int) -> dict:
    """Get {stage_id: name} map for a funnel with caching."""
    key = int(category_id)
    if key in _stage_cache:
        return _stage_cache[key]

    if category_id == 0:
        result = bx('crm.status.list', {'filter': {'ENTITY_ID': 'DEAL_STAGE'}})
    else:
        result = bx('crm.dealcategory.stage.list', {'id': category_id})

    stages = {s['STATUS_ID']: s['NAME'] for s in result.get('result', [])}
    _stage_cache[key] = stages
    return stages


if __name__ == '__main__':
    # Smoke test
    print(f'Webhook: {WEBHOOK[:50]}...')
    print(f'Testing connection...')
    r = bx('server.time')
    print(f'Server time: {r.get("result")}')
    r = bx('crm.dealcategory.list')
    print(f'Funnels found: {len(r.get("result", []))}')
