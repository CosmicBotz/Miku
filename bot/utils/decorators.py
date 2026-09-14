import functools

from telegram import Update
from telegram.ext import ContextTypes

from .flavor import random_phrase
from .permissions import is_admin_or_owner


def admin_only(func):
    """Require the sender to be a chat admin, the bot owner, or a sudo user."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if not await is_admin_or_owner(update, context):
            await update.effective_message.reply_text(random_phrase("no_permission"))
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


def group_only(func):
    """Require the command to be used inside a group/supergroup, not DMs."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        if update.effective_chat.type not in ("group", "supergroup"):
            await update.effective_message.reply_text("This command only works inside a group, not here~")
            return
        return await func(update, context, *args, **kwargs)

    return wrapper


def bot_admin_required(func):
    """Require the bot itself to be an admin before attempting a moderation action."""

    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        chat = update.effective_chat
        try:
            bot_member = await chat.get_member(context.bot.id)
        except Exception:
            bot_member = None
        if bot_member is None or bot_member.status != "administrator":
            await update.effective_message.reply_text(
                "I need to be an admin here first! Promote me so I can use my powers~ ⚔️"
            )
            return
        return await func(update, context, *args, **kwargs)

    return wrapper
