"""Async data-access helpers backed by MongoDB.

Chats live in the `chat_settings` collection keyed by chat_id (as Mongo's
`_id`), so per-chat settings work naturally at public-bot scale across many
groups. Warns and blacklist words get their own collections so we can
query/count them without loading a whole chat document.

Every function here is a coroutine now (Mongo access is async) - callers in
bot/modules/*.py must `await` them. Chat documents are handed back as a
plain SimpleNamespace so call sites can keep using attribute access
(settings.warn_limit) instead of dict lookups.
"""
from datetime import datetime, timezone
from types import SimpleNamespace
from typing import Any, Dict, List, Optional

from pymongo import ReturnDocument

from .base import get_db

_CHAT_DEFAULTS: Dict[str, Any] = {
    "welcome_enabled": True,
    "welcome_message": "Welcome, {mention}!",
    "goodbye_enabled": True,
    "goodbye_message": "{first} left the chat.",
    "clean_welcome": True,
    "clean_service_messages": True,
    "last_welcome_msg_id": None,
    "rules": "",
    "warn_limit": 3,
    "warn_mode": "mute",
    "flood_limit": 7,
    "flood_window": 8,
    "flood_mode": "mute",
    "antispam_enabled": True,
    "max_links_per_message": 3,
    "locks": {
        "text": False,
        "sticker": False,
        "photo": False,
        "video": False,
        "audio": False,
        "voice": False,
        "gif": False,
        "url": False,
        "forward": False,
        "bot": False,
        "inline": False,
    },
    "log_channel": None,
    "reports_enabled": True,
    "antichannelpin": False,
    "disabled_commands": [],
    "captcha_enabled": False,
    "captcha_mode": "button",
    "captcha_time": 300,
    "antiraid_enabled": False,
    "antiraid_action": "kick",
    "raid_time": 3600,
    "blocklist_mode": "delete",
    "blacklist_delete": True,
}





def _to_ns(doc: dict) -> SimpleNamespace:
    data = dict(doc)
    data["chat_id"] = data.pop("_id", None)
    return SimpleNamespace(**data)


# ---------------------------------------------------------------------
# Chat settings
# ---------------------------------------------------------------------
async def get_or_create_chat(
    chat_id: int, chat_title: Optional[str] = None, defaults: Optional[dict] = None
) -> SimpleNamespace:
    defaults = defaults or {}
    db = get_db()
    chat = await db.chat_settings.find_one({"_id": chat_id})

    if chat is None:
        doc = {"_id": chat_id, "chat_title": chat_title}
        for key, hard_default in _CHAT_DEFAULTS.items():
            doc[key] = defaults.get(key, hard_default)
        await db.chat_settings.insert_one(doc)
        chat = doc
    elif chat_title and chat.get("chat_title") != chat_title:
        await db.chat_settings.update_one({"_id": chat_id}, {"$set": {"chat_title": chat_title}})
        chat["chat_title"] = chat_title

    return _to_ns(chat)


async def update_chat(chat_id: int, **fields) -> Optional[SimpleNamespace]:
    db = get_db()
    doc = await db.chat_settings.find_one_and_update(
        {"_id": chat_id}, {"$set": fields}, return_document=ReturnDocument.AFTER
    )
    if doc is None:
        return None
    return _to_ns(doc)


# ---------------------------------------------------------------------
# Warns
# ---------------------------------------------------------------------
async def add_warn(chat_id: int, user_id: int, reason: str = "", admin_id: Optional[int] = None) -> int:
    """Insert a warn and return the user's new total warn count in this chat."""
    db = get_db()
    await db.warns.insert_one(
        {
            "chat_id": chat_id,
            "user_id": user_id,
            "reason": reason,
            "admin_id": admin_id,
            "created_at": datetime.now(timezone.utc),
        }
    )
    return await db.warns.count_documents({"chat_id": chat_id, "user_id": user_id})


async def get_warns(chat_id: int, user_id: int) -> List[dict]:
    db = get_db()
    cursor = db.warns.find({"chat_id": chat_id, "user_id": user_id}).sort("created_at", 1)
    return [doc async for doc in cursor]


async def reset_warns(chat_id: int, user_id: int) -> None:
    db = get_db()
    await db.warns.delete_many({"chat_id": chat_id, "user_id": user_id})


async def remove_last_warn(chat_id: int, user_id: int) -> bool:
    db = get_db()
    doc = await db.warns.find_one_and_delete(
        {"chat_id": chat_id, "user_id": user_id}, sort=[("created_at", -1)]
    )
    return doc is not None


# ---------------------------------------------------------------------
# Blacklist words
# ---------------------------------------------------------------------
async def add_blacklist_word(chat_id: int, word: str) -> bool:
    db = get_db()
    existing = await db.blacklist_words.find_one({"chat_id": chat_id, "word": word})
    if existing:
        return False
    await db.blacklist_words.insert_one({"chat_id": chat_id, "word": word})
    return True


async def remove_blacklist_word(chat_id: int, word: str) -> bool:
    db = get_db()
    result = await db.blacklist_words.delete_one({"chat_id": chat_id, "word": word})
    return result.deleted_count > 0


async def list_blacklist_words(chat_id: int) -> List[str]:
    db = get_db()
    cursor = db.blacklist_words.find({"chat_id": chat_id})
    return [doc["word"] async for doc in cursor]


# ---------------------------------------------------------------------
# Notes
# ---------------------------------------------------------------------
async def save_note(
    chat_id: int,
    note_name: str,
    content: str = "",
    media_type: Optional[str] = None,
    file_id: Optional[str] = None,
) -> None:
    db = get_db()
    key = note_name.lower()
    await db.notes.update_one(
        {"chat_id": chat_id, "note_name": key},
        {
            "$set": {
                "chat_id": chat_id,
                "note_name": key,
                "display_name": note_name,
                "content": content,
                "media_type": media_type,
                "file_id": file_id,
            }
        },
        upsert=True,
    )


async def get_note(chat_id: int, note_name: str) -> Optional[dict]:
    db = get_db()
    return await db.notes.find_one({"chat_id": chat_id, "note_name": note_name.lower()})


async def list_notes(chat_id: int) -> List[dict]:
    db = get_db()
    cursor = db.notes.find({"chat_id": chat_id}).sort("note_name", 1)
    return [doc async for doc in cursor]


async def delete_note(chat_id: int, note_name: str) -> bool:
    db = get_db()
    result = await db.notes.delete_one({"chat_id": chat_id, "note_name": note_name.lower()})
    return result.deleted_count > 0


async def delete_all_notes(chat_id: int) -> int:
    db = get_db()
    result = await db.notes.delete_many({"chat_id": chat_id})
    return result.deleted_count


# ---------------------------------------------------------------------
# Filters
# ---------------------------------------------------------------------
async def add_filter(
    chat_id: int,
    keyword: str,
    reply_text: str = "",
    media_type: Optional[str] = None,
    file_id: Optional[str] = None,
) -> None:
    db = get_db()
    key = keyword.lower()
    await db.filters.update_one(
        {"chat_id": chat_id, "keyword": key},
        {
            "$set": {
                "chat_id": chat_id,
                "keyword": key,
                "reply_text": reply_text,
                "media_type": media_type,
                "file_id": file_id,
            }
        },
        upsert=True,
    )


async def get_filter(chat_id: int, keyword: str) -> Optional[dict]:
    db = get_db()
    return await db.filters.find_one({"chat_id": chat_id, "keyword": keyword.lower()})


async def list_filters(chat_id: int) -> List[dict]:
    db = get_db()
    cursor = db.filters.find({"chat_id": chat_id}).sort("keyword", 1)
    return [doc async for doc in cursor]


async def delete_filter(chat_id: int, keyword: str) -> bool:
    db = get_db()
    result = await db.filters.delete_one({"chat_id": chat_id, "keyword": keyword.lower()})
    return result.deleted_count > 0


async def delete_all_filters(chat_id: int) -> int:
    db = get_db()
    result = await db.filters.delete_many({"chat_id": chat_id})
    return result.deleted_count


# ---------------------------------------------------------------------
# Approvals
# ---------------------------------------------------------------------
async def add_approval(chat_id: int, user_id: int) -> bool:
    db = get_db()
    existing = await db.approvals.find_one({"chat_id": chat_id, "user_id": user_id})
    if existing:
        return False
    await db.approvals.insert_one({"chat_id": chat_id, "user_id": user_id})
    return True


async def remove_approval(chat_id: int, user_id: int) -> bool:
    db = get_db()
    result = await db.approvals.delete_one({"chat_id": chat_id, "user_id": user_id})
    return result.deleted_count > 0


async def list_approvals(chat_id: int) -> List[int]:
    db = get_db()
    cursor = db.approvals.find({"chat_id": chat_id})
    return [doc["user_id"] async for doc in cursor]


async def is_approved_user(chat_id: int, user_id: int) -> bool:
    db = get_db()
    doc = await db.approvals.find_one({"chat_id": chat_id, "user_id": user_id})
    return doc is not None


# ---------------------------------------------------------------------
# Disabled Commands
# ---------------------------------------------------------------------
async def disable_command(chat_id: int, command: str) -> bool:
    db = get_db()
    cmd = command.lower().lstrip("/")
    await db.chat_settings.update_one(
        {"_id": chat_id}, {"$addToSet": {"disabled_commands": cmd}}, upsert=True
    )
    return True


async def enable_command(chat_id: int, command: str) -> bool:
    db = get_db()
    cmd = command.lower().lstrip("/")
    result = await db.chat_settings.update_one(
        {"_id": chat_id}, {"$pull": {"disabled_commands": cmd}}
    )
    return result.modified_count > 0


async def enable_all_commands(chat_id: int) -> bool:
    db = get_db()
    await db.chat_settings.update_one({"_id": chat_id}, {"$set": {"disabled_commands": []}})
    return True


async def get_disabled_commands(chat_id: int) -> List[str]:
    db = get_db()
    chat = await db.chat_settings.find_one({"_id": chat_id})
    if not chat:
        return []
    return chat.get("disabled_commands", [])


# ---------------------------------------------------------------------
# Connections
# ---------------------------------------------------------------------
async def set_connection(user_id: int, chat_id: int) -> None:
    db = get_db()
    await db.connections.update_one(
        {"_id": user_id}, {"$set": {"_id": user_id, "chat_id": chat_id}}, upsert=True
    )


async def disconnect_user(user_id: int) -> bool:
    db = get_db()
    result = await db.connections.delete_one({"_id": user_id})
    return result.deleted_count > 0


async def get_connection(user_id: int) -> Optional[int]:
    db = get_db()
    doc = await db.connections.find_one({"_id": user_id})
    return doc["chat_id"] if doc else None


# ---------------------------------------------------------------------
# Federations
# ---------------------------------------------------------------------
async def create_fed(fed_id: str, fed_name: str, owner_id: int) -> bool:
    db = get_db()
    existing = await db.federations.find_one({"_id": fed_id})
    if existing:
        return False
    await db.federations.insert_one(
        {
            "_id": fed_id,
            "fed_name": fed_name,
            "owner_id": owner_id,
            "admins": [owner_id],
            "banned_users": [],
            "created_at": datetime.now(timezone.utc),
        }
    )
    return True


async def delete_fed(fed_id: str) -> bool:
    db = get_db()
    result = await db.federations.delete_one({"_id": fed_id})
    await db.fed_chats.delete_many({"fed_id": fed_id})
    return result.deleted_count > 0


async def get_fed(fed_id: str) -> Optional[dict]:
    db = get_db()
    return await db.federations.find_one({"_id": fed_id})


async def join_fed(chat_id: int, fed_id: str) -> bool:
    db = get_db()
    fed = await db.federations.find_one({"_id": fed_id})
    if not fed:
        return False
    await db.fed_chats.update_one(
        {"_id": chat_id}, {"$set": {"_id": chat_id, "fed_id": fed_id}}, upsert=True
    )
    return True


async def leave_fed(chat_id: int) -> bool:
    db = get_db()
    result = await db.fed_chats.delete_one({"_id": chat_id})
    return result.deleted_count > 0


async def get_fed_by_chat(chat_id: int) -> Optional[dict]:
    db = get_db()
    link = await db.fed_chats.find_one({"_id": chat_id})
    if not link:
        return None
    return await get_fed(link["fed_id"])


async def list_fed_chats(fed_id: str) -> List[int]:
    db = get_db()
    cursor = db.fed_chats.find({"fed_id": fed_id})
    return [doc["_id"] async for doc in cursor]


async def fban_user(fed_id: str, user_id: int, reason: str = "", admin_id: Optional[int] = None) -> bool:
    db = get_db()
    fed = await get_fed(fed_id)
    if not fed:
        return False

    banned = fed.get("banned_users", [])
    if any(b["user_id"] == user_id for b in banned):
        return False

    entry = {
        "user_id": user_id,
        "reason": reason,
        "admin_id": admin_id,
        "created_at": datetime.now(timezone.utc),
    }
    await db.federations.update_one({"_id": fed_id}, {"$push": {"banned_users": entry}})
    return True


async def unfban_user(fed_id: str, user_id: int) -> bool:
    db = get_db()
    result = await db.federations.update_one(
        {"_id": fed_id}, {"$pull": {"banned_users": {"user_id": user_id}}}
    )
    return result.modified_count > 0


async def is_fbanned(fed_id: str, user_id: int) -> bool:
    db = get_db()
    doc = await db.federations.find_one({"_id": fed_id, "banned_users.user_id": user_id})
    return doc is not None


async def promote_fed_admin(fed_id: str, user_id: int) -> bool:
    db = get_db()
    result = await db.federations.update_one(
        {"_id": fed_id}, {"$addToSet": {"admins": user_id}}
    )
    return result.modified_count > 0


async def demote_fed_admin(fed_id: str, user_id: int) -> bool:
    db = get_db()
    result = await db.federations.update_one(
        {"_id": fed_id}, {"$pull": {"admins": user_id}}
    )
    return result.modified_count > 0



