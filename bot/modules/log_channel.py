import logging
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only

logger = logging.getLogger(__name__)


async def send_log(bot, chat_id: int, text: str):
    """Shared helper to send formatted action logs to the chat's log channel."""
    try:
        cfg = get_config()
        settings = await crud.get_or_create_chat(chat_id, defaults=cfg.defaults)
        log_channel = getattr(settings, "log_channel", None)
        if log_channel:
            await bot.send_message(chat_id=log_channel, text=text, parse_mode="HTML")
    except Exception as e:
        logger.warning(f"Failed to send log for chat {chat_id}: {e}")


@group_only
async def logchannel_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    cfg = get_config()
    settings = await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    log_channel = getattr(settings, "log_channel", None)

    if log_channel:
        await msg.reply_html(f"Current log channel for this chat is <code>{log_channel}</code>.")
    else:
        await msg.reply_text("No log channel configured for this chat. Use /setlog to set one.")


@group_only
@admin_only
async def setlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    target_channel = None

    if context.args:
        try:
            target_channel = int(context.args[0])
        except ValueError:
            target_channel = context.args[0]
    elif msg.forward_from_chat:
        target_channel = msg.forward_from_chat.id
    elif msg.reply_to_message and msg.reply_to_message.forward_from_chat:
        target_channel = msg.reply_to_message.forward_from_chat.id

    if not target_channel:
        await msg.reply_text(
            "Usage: /setlog <channel_id_or_username> or forward a message from the channel and reply /setlog."
        )
        return

    try:
        channel_chat = await context.bot.get_chat(target_channel)
        await crud.update_chat(chat_id, log_channel=channel_chat.id)
        await msg.reply_html(f"[+] Log channel set to <b>{channel_chat.title}</b> (<code>{channel_chat.id}</code>).")
        await send_log(
            context.bot,
            chat_id,
            f"<b>[LOG CHANNEL CONFIG]</b>\nThis channel has been set as the log channel for <b>{update.effective_chat.title}</b>.",
        )
    except Exception as e:
        await msg.reply_text(f"Could not set log channel. Make sure I am an admin in that channel. Error: {e}")


@group_only
@admin_only
async def unsetlog_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    await crud.update_chat(chat_id, log_channel=None)
    await msg.reply_text("Log channel has been unset for this chat.")


def register(application):
    application.add_handler(CommandHandler("logchannel", logchannel_cmd))
    application.add_handler(CommandHandler("setlog", setlog_cmd))
    application.add_handler(CommandHandler("unsetlog", unsetlog_cmd))
