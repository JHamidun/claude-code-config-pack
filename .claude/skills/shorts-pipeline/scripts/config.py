"""Единая точка настройки конвейера: пути, ключи, идентификаторы аватара, бренд.

Раньше всё это было захардкожено в каждом скрипте абсолютными путями одной машины.
Теперь — переменные окружения с разумными умолчаниями относительно рабочего каталога,
чтобы конвейер запускался у любого без правки кода.

Переменные (все необязательные, кроме отмеченных):

    SHORTS_HOME       рабочий каталог конвейера. Умолчание: ./shorts-pipeline
                      Внутри: analysis.json, state.json, снимки канала, обложки.
    SHORTS_SOURCE     где лежат нарезанные .srt/.mp4: <SHORTS_SOURCE>/<video_id>/short_NN.srt
                      Умолчание: $SHORTS_HOME/source
    SHORTS_BRAND      подпись на обложке. Умолчание: пусто (подписи не будет)
    SHORTS_HASHTAGS   хвост хэштегов для описаний. Умолчание: пусто (ничего не дописывается)

    HEYGEN_API_KEY        ОБЯЗАТЕЛЕН для генерации (платно, ~$0.0667/сек)
    HEYGEN_AVATAR_ID      ОБЯЗАТЕЛЕН — id ТВОЕГО аватара, кабинет HeyGen → Avatars
    HEYGEN_VOICE_ID       ОБЯЗАТЕЛЕН — id ТВОЕГО голоса, кабинет HeyGen → Voices
    SUBMAGIC_API_KEY      ОБЯЗАТЕЛЕН для субтитров (платный план)
    OPENAI_API_KEY        ОБЯЗАТЕЛЕН для анализа SRT (~$0.0005 за короткий ролик)
    YOUTUBE_TOKEN_FILE    OAuth-токен канала. Умолчание: ~/.claude/.youtube-oauth-token.json

Ключи читаются из окружения; если рядом есть ~/.claude/.credentials.master.env —
подхватываются и оттуда (шаблон: ~/.claude/templates/.credentials.master.env.example).
"""
import os
import sys
from pathlib import Path

_ENV_FILE = Path.home() / ".claude" / ".credentials.master.env"
_dotenv_cache = None


def _dotenv() -> dict:
    """Ленивое чтение .credentials.master.env. Нет файла — пустой словарь, не ошибка."""
    global _dotenv_cache
    if _dotenv_cache is None:
        _dotenv_cache = {}
        if _ENV_FILE.exists():
            for line in _ENV_FILE.read_text(encoding="utf-8", errors="replace").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                _dotenv_cache[k.strip()] = v.strip().strip('"').strip("'")
    return _dotenv_cache


def key(name: str, required: bool = True) -> str:
    """Значение ключа: окружение → .credentials.master.env → внятный отказ.

    Отказ громкий и с адресом, где ключ взять: молча продолжать с пустым ключом
    хуже всего — HeyGen спишет деньги, а результат принять будет нечем.
    """
    val = os.environ.get(name) or _dotenv().get(name, "")
    if val:
        os.environ[name] = val  # чтобы SDK, читающие окружение сами, тоже увидели
        return val
    if not required:
        return ""
    where = {
        "HEYGEN_API_KEY": "app.heygen.com → Settings → API (платно, ~$0.0667/сек видео)",
        "HEYGEN_AVATAR_ID": "app.heygen.com → Avatars → твой аватар → Copy ID",
        "HEYGEN_VOICE_ID": "app.heygen.com → Voices → твой голос → Copy ID",
        "SUBMAGIC_API_KEY": "submagic.co → аккаунт с платным планом → API",
        "OPENAI_API_KEY": "platform.openai.com/api-keys (анализ SRT ~$0.0005 за ролик)",
    }.get(name, "документация соответствующего сервиса")
    raise SystemExit(
        f"ОТКАЗ: не задан {name}.\n"
        f"  Где взять: {where}\n"
        f"  Как задать: export {name}=... (или строка {name}=... "
        f"в ~/.claude/.credentials.master.env)"
    )


HOME = Path(os.environ.get("SHORTS_HOME") or (Path.cwd() / "shorts-pipeline")).expanduser()
SOURCE_DIR = Path(os.environ.get("SHORTS_SOURCE") or (HOME / "source")).expanduser()
BRAND = os.environ.get("SHORTS_BRAND", "")
HASHTAGS = os.environ.get("SHORTS_HASHTAGS", "")

YT_TOKEN = Path(
    os.environ.get("YOUTUBE_TOKEN_FILE")
    or (Path.home() / ".claude" / ".youtube-oauth-token.json")
).expanduser()

# Имена файлов состояния. Лежат в HOME, а не в домашнем каталоге пользователя:
# конвейеров может быть несколько (разные каналы, разные вебинары).
ANALYSIS = HOME / "analysis.json"
CHANNEL_SNAPSHOT = HOME / "channel_shorts.json"
CLEANUP_CANDIDATES = HOME / "cleanup_candidates.json"
CLEANUP_PROGRESS = HOME / "cleanup_progress.json"
THUMBS_DONE = HOME / "thumbs_done.json"
STATS_OUT = HOME / "shorts_stats.json"
COVERS_DIR = HOME / "covers"
OUT_DIR = HOME / "out"


def ensure_home() -> Path:
    HOME.mkdir(parents=True, exist_ok=True)
    return HOME


def require_yt_token() -> Path:
    if not YT_TOKEN.exists():
        raise SystemExit(
            f"нет токена YouTube: {YT_TOKEN}\n"
            "  Заведи OAuth-клиент в Google Cloud Console (YouTube Data API v3),\n"
            "  пройди авторизацию и сохрани токен по этому пути,\n"
            "  либо укажи свой файл: export YOUTUBE_TOKEN_FILE=/path/to/token.json"
        )
    return YT_TOKEN


def add_self_to_path() -> None:
    """Чтобы `import config` работал при запуске скрипта из любого каталога."""
    here = str(Path(__file__).parent)
    if here not in sys.path:
        sys.path.insert(0, here)
