"""Config loader — reads from environment variables (loaded from .env if present)."""
import os


def _load_env():
    """Load .env file if present (simple parser, no external deps)."""
    paths = [
        os.path.join(os.getcwd(), '.env'),
        os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env'),
    ]
    for p in paths:
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                for ln in f:
                    ln = ln.strip()
                    if not ln or ln.startswith('#') or '=' not in ln:
                        continue
                    k, v = ln.split('=', 1)
                    k = k.strip()
                    v = v.strip().strip('"').strip("'")
                    if k and v and k not in os.environ:
                        os.environ[k] = v
            return p
    return None


_load_env()


def get(key, default=None):
    v = os.environ.get(key, default)
    if v is None:
        raise SystemExit(f'Missing env: {key}. Copy .env.example to .env and fill in.')
    return v


# ---- Telegram (Telethon) ----
def telegram_api_id() -> int:
    return int(get('TELEGRAM_API_ID'))


def telegram_api_hash() -> str:
    return get('TELEGRAM_API_HASH')


def telegram_session() -> str:
    return os.path.expanduser(os.environ.get('TELEGRAM_SESSION', './telegram_session'))


# ---- OpenAI (gpt-image-2 for static) ----
def openai_key() -> str:
    return get('OPENAI_API_KEY')


def openai_image_model() -> str:
    return os.environ.get('OPENAI_IMAGE_MODEL', 'gpt-image-1')


# ---- SAM2 (animated) ----
def sam2_checkpoint() -> str:
    return os.environ.get('SAM2_CHECKPOINT',
                          './sam2_checkpoints/sam2.1_hiera_small.pt')


def sam2_config() -> str:
    return os.environ.get('SAM2_CONFIG', 'configs/sam2.1/sam2.1_hiera_s.yaml')


# ---- WSL alpha_encoder ----
def wsl_distro() -> str:
    return os.environ.get('WSL_DISTRO', 'Ubuntu-22.04')


def alpha_encoder_path() -> str:
    return os.environ.get('ALPHA_ENCODER_PATH',
                          '/opt/webm-tools/alpha_encoder/alpha_encoder')


def to_wsl_path(p: str) -> str:
    """Convert Windows path to WSL path."""
    p = p.replace('\\', '/')
    if len(p) > 1 and p[1] == ':':
        return f'/mnt/{p[0].lower()}{p[2:]}'
    return p
