"""Telethon MTProto client manager for resolving arbitrary usernames/IDs.

Telegram Bot API HTTP endpoints fail to resolve arbitrary user @usernames if the user
has not interacted with the bot. Telethon MTProto client resolves entities directly.
"""
import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Union

logger = logging.getLogger(__name__)

try:
    from telethon import TelegramClient
    from telethon.tl.types import Channel, Chat, User
    TELETHON_AVAILABLE = True
except ImportError:
    TELETHON_AVAILABLE = False
    TelegramClient = None
    Channel = Chat = User = None

_client: Optional[Any] = None


@dataclass
class ResolvedEntity:
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    title: Optional[str] = None
    username: Optional[str] = None
    is_bot: bool = False
    entity_type: str = "Unknown"  # User, Bot, Channel, Supergroup, Group

    @property
    def display_name(self) -> str:
        if self.title:
            return self.title
        names = [n for n in (self.first_name, self.last_name) if n]
        if names:
            return " ".join(names)
        if self.username:
            return f"@{self.username}"
        return str(self.id)


async def init_telethon(
    api_id: Optional[int], api_hash: Optional[str], bot_token: str, session_name: str = "frieren_bot_session"
) -> Optional[Any]:
    global _client

    if not TELETHON_AVAILABLE:
        logger.info("Telethon library is not installed. Username resolution will rely solely on Bot API.")
        return None

    if not api_id or not api_hash:
        logger.info("API_ID / API_HASH not set. Telethon username resolution is disabled.")
        return None

    try:
        logger.info("Initializing Telethon MTProto client...")
        client = TelegramClient(session_name, api_id, api_hash)
        await client.start(bot_token=bot_token)
        _client = client
        logger.info("Telethon client successfully connected and started.")
        return _client
    except Exception as e:
        logger.error(f"Failed to start Telethon client: {e}")
        _client = None
        return None


async def close_telethon() -> None:
    global _client
    if _client is not None:
        try:
            logger.info("Disconnecting Telethon client...")
            await _client.disconnect()
            logger.info("Telethon client disconnected.")
        except Exception as e:
            logger.warning(f"Error while disconnecting Telethon client: {e}")
        finally:
            _client = None


def get_telethon_client() -> Optional[Any]:
    return _client


async def resolve_entity(target: Union[str, int]) -> Optional[ResolvedEntity]:
    """Resolve a user ID or @username to a ResolvedEntity via Telethon.

    Returns None if Telethon is unavailable, not connected, or entity not found.
    """
    if _client is None or not _client.is_connected():
        return None

    # Handle numeric string conversion if passed as a string representation of ID
    if isinstance(target, str) and not target.startswith("@"):
        if target.lstrip("-").isdigit():
            target = int(target)

    try:
        entity = await _client.get_entity(target)
        if not entity:
            return None

        entity_id = entity.id
        username = getattr(entity, "username", None)
        first_name = getattr(entity, "first_name", None)
        last_name = getattr(entity, "last_name", None)
        title = getattr(entity, "title", None)
        is_bot = getattr(entity, "bot", False)

        entity_type = "User"
        if is_bot:
            entity_type = "Bot"
        elif isinstance(entity, Channel):
            if getattr(entity, "megagroup", False):
                entity_type = "Supergroup"
            else:
                entity_type = "Channel"
        elif isinstance(entity, Chat):
            entity_type = "Group"

        return ResolvedEntity(
            id=entity_id,
            first_name=first_name,
            last_name=last_name,
            title=title,
            username=username,
            is_bot=is_bot,
            entity_type=entity_type,
        )
    except Exception as e:
        logger.debug(f"Telethon entity resolution failed for '{target}': {e}")
        return None
