"""Helpers for pulling a "target user" and free-text "reason" out of a
command message, the same way most group-management bots do it: reply to
someone, or pass their numeric id / @username as the first argument.
"""
from typing import Optional

from telegram import Update, User
from telegram.ext import ContextTypes


async def get_target_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> Optional[User]:
    message = update.effective_message

    if message.entities:
        for entity in message.entities:
            if entity.type == "text_mention" and entity.user:
                return entity.user

    if context.args:
        arg = context.args[0]
        if arg.startswith("@"):
            try:
                chat = await context.bot.get_chat(arg)
                return User(id=chat.id, first_name=chat.first_name or arg, is_bot=False, username=chat.username)
            except Exception:
                return None
        if arg.lstrip("-").isdigit():
            try:
                member = await update.effective_chat.get_member(int(arg))
                return member.user
            except Exception:
                try:
                    chat = await context.bot.get_chat(int(arg))
                    return User(
                        id=chat.id,
                        first_name=chat.first_name or str(chat.id),
                        is_bot=False,
                        username=chat.username,
                    )
                except Exception:
                    return None

    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user

    return None


def get_reason(context: ContextTypes.DEFAULT_TYPE, offset: int = 1) -> str:
    """Return whatever command args come after the user identifier as the reason.

    offset=0 when the target came from a reply (all args are reason text),
    offset=1 when the first arg was the user id/@username.
    """
    if not context.args:
        return ""
    return " ".join(context.args[offset:]).strip()
