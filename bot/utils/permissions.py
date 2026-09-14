from telegram import Update
from telegram.ext import ContextTypes

from ..config import get_config


async def is_admin_or_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    """True if the sender is the bot owner/sudo, or a real admin/creator of the chat."""
    user = update.effective_user
    chat = update.effective_chat
    if user is None or chat is None:
        return False

    cfg = get_config()
    if user.id == cfg.owner_id or user.id in cfg.sudo_users:
        return True

    try:
        member = await chat.get_member(user.id)
    except Exception:
        return False
    return member.status in ("administrator", "creator")


async def is_bot_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    chat = update.effective_chat
    try:
        member = await chat.get_member(context.bot.id)
    except Exception:
        return False
    return member.status == "administrator"


async def is_approved(chat_id: int, user_id: int) -> bool:
    """True if the user is explicitly approved in the given chat."""
    from ..database import crud
    return await crud.is_approved_user(chat_id, user_id)

