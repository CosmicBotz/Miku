"""Simple in-memory antiflood: if a user sends too many messages within a
time window, act on them (mute/kick/ban, per chat settings). Activity is
kept in memory only - it resets on restart, which is fine for a flood guard.
"""
import time
from collections import defaultdict, deque

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only
from ..utils.flavor import random_phrase
from .moderation import MUTED_PERMISSIONS, _mention

_activity = defaultdict(deque)  # (chat_id, user_id) -> deque[timestamp]


async def flood_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    user = update.effective_user
    chat = update.effective_chat
    if not message or not user or not chat or chat.type not in ("group", "supergroup"):
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    if settings.flood_limit <= 0:
        return

    try:
        member = await chat.get_member(user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    if await crud.is_approved_user(chat.id, user.id):
        return


    key = (chat.id, user.id)
    now = time.time()
    timestamps = _activity[key]
    timestamps.append(now)
    while timestamps and now - timestamps[0] > settings.flood_window:
        timestamps.popleft()

    if len(timestamps) < settings.flood_limit:
        return

    timestamps.clear()
    mode = settings.flood_mode
    try:
        if mode == "ban":
            await context.bot.ban_chat_member(chat.id, user.id)
        elif mode == "kick":
            await context.bot.ban_chat_member(chat.id, user.id)
            await context.bot.unban_chat_member(chat.id, user.id, only_if_banned=True)
        else:
            await context.bot.restrict_chat_member(chat.id, user.id, permissions=MUTED_PERMISSIONS)
    except Exception:
        return

    await message.reply_html(random_phrase("flood_triggered", user=_mention(user)))


@group_only
@admin_only
async def set_flood_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text(
            "Usage: /setflood <n>  (messages allowed within the flood window; 0 disables antiflood)"
        )
        return
    limit = int(context.args[0])
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, flood_limit=limit)
    await update.effective_message.reply_text(
        "Antiflood disabled." if limit <= 0 else f"Antiflood set to {limit} messages."
    )


@group_only
@admin_only
async def set_flood_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0].lower() not in ("mute", "kick", "ban"):
        await update.effective_message.reply_text("Usage: /setfloodmode mute|kick|ban")
        return
    mode = context.args[0].lower()
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, flood_mode=mode)
    await update.effective_message.reply_text(f"Flood mode set to {mode}.")


def register(application):
    # group=1 so this runs alongside command handlers (group=0) on every group message
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL, flood_check),
        group=1,
    )
    application.add_handler(CommandHandler("setflood", set_flood_cmd))
    application.add_handler(CommandHandler("setfloodmode", set_flood_mode_cmd))
