"""Configuration loading for the bot.

Values come from a YAML file (config.yaml by default). Every value also has
an environment variable override, so the bot can be fully configured from a
PaaS dashboard (Render/Koyeb/Heroku, etc.) without committing secrets to
config.yaml. Env vars always win when both are set.
"""
import os
from dataclasses import dataclass, field
from typing import Any, Dict, List

import yaml

_CONFIG: "Config | None" = None


@dataclass
class Config:
    bot_token: str
    owner_id: int
    sudo_users: List[int]
    mongo_uri: str
    mongo_db_name: str
    port: int
    log_level: str
    start_pics: List[str]
    defaults: Dict[str, Any]
    raw: Dict[str, Any] = field(default_factory=dict)


def _env(*names: str) -> "str | None":
    """Return the first set, non-empty environment variable among names."""
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _load_yaml(path: str) -> Dict[str, Any]:
    if not os.path.exists(path):
        # A config file isn't strictly required if every value is supplied
        # via environment variables (common on Render/Koyeb/Heroku), but we
        # still need *a* bot token from somewhere, so only hard-fail if we
        # find neither a file nor the token env var.
        if _env("ANIME_BOT_TOKEN"):
            return {}
        raise FileNotFoundError(
            f"Config file not found at '{path}' and ANIME_BOT_TOKEN is not set. "
            f"Copy config.sample.yaml to config.yaml and fill it in, pass a path "
            f"with --config, or set config entirely via environment variables."
        )
    with open(path, "r", encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def _parse_sudo_users(raw: "str | list | None") -> List[int]:
    if not raw:
        return []
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",")]
        return [int(p) for p in parts if p]
    return [int(u) for u in raw]


def load_config(path: str = "config.yaml") -> Config:
    """Load config.yaml (or the given path), apply env var overrides, and
    cache the result as the active config."""
    global _CONFIG
    data = _load_yaml(path)

    telegram = data.get("telegram", {}) or {}
    owner = data.get("owner", {}) or {}
    mongodb = data.get("mongodb", {}) or {}
    server = data.get("server", {}) or {}
    logging_cfg = data.get("logging", {}) or {}
    defaults = data.get("defaults", {}) or {}

    bot_token = _env("ANIME_BOT_TOKEN") or telegram.get("bot_token")
    if not bot_token or "YOUR-TELEGRAM-BOT-TOKEN" in bot_token:
        raise ValueError(
            "No bot token found. Set telegram.bot_token in config.yaml, or "
            "the ANIME_BOT_TOKEN environment variable, to a real token from @BotFather."
        )

    owner_id = int(_env("ANIME_BOT_OWNER_ID") or owner.get("owner_id") or 0)

    sudo_env = _env("ANIME_BOT_SUDO_USERS")
    sudo_users = _parse_sudo_users(sudo_env) if sudo_env else _parse_sudo_users(owner.get("sudo_users"))

    mongo_uri = (
        _env("ANIME_BOT_MONGO_URI", "MONGODB_URI", "MONGO_URL")
        or mongodb.get("uri", "mongodb://localhost:27017")
    )
    mongo_db_name = _env("ANIME_BOT_MONGO_DB_NAME") or mongodb.get("db_name", "anime_mod_bot")

    # PORT is the de-facto standard env var Render/Koyeb/Heroku all set
    # automatically - it always wins over config.yaml / ANIME_BOT_PORT.
    port = int(_env("PORT", "ANIME_BOT_PORT") or server.get("port", 8080))

    log_level = _env("ANIME_BOT_LOG_LEVEL") or logging_cfg.get("level", "INFO")

    start_pics_env = _env("ANIME_BOT_START_PICS")
    if start_pics_env:
        start_pics = [p.strip() for p in start_pics_env.split(",") if p.strip()]
    else:
        start_pics_raw = telegram.get("start_pics") or data.get("start_pics") or []
        if isinstance(start_pics_raw, str):
            start_pics = [p.strip() for p in start_pics_raw.split(",") if p.strip()]
        elif isinstance(start_pics_raw, list):
            start_pics = [str(p).strip() for p in start_pics_raw if p]
        else:
            start_pics = []

    _CONFIG = Config(
        bot_token=bot_token,
        owner_id=owner_id,
        sudo_users=sudo_users,
        mongo_uri=mongo_uri,
        mongo_db_name=mongo_db_name,
        port=port,
        log_level=log_level,
        start_pics=start_pics,
        defaults=defaults,
        raw=data,
    )
    return _CONFIG


def get_config() -> Config:
    """Return the already-loaded config. Call load_config() once at startup first."""
    if _CONFIG is None:
        raise RuntimeError("Config not loaded yet. Call load_config() before get_config().")
    return _CONFIG
