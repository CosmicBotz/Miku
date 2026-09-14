from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..database import crud


async def connect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user

    if not context.args:
        await msg.reply_text("Usage: /connect <chat_id>")
        return

    try:
        target_chat_id = int(context.args[0])
    except ValueError:
        await msg.reply_text("Invalid Chat ID format. Example: /connect -1001234567890")
        return

    try:
        chat = await context.bot.get_chat(target_chat_id)
        member = await chat.get_member(user.id)
        if member.status not in ("administrator", "creator"):
            await msg.reply_text("You must be an admin of the target chat to connect to it! ❌")
            return
    except Exception as e:
        await msg.reply_text(f"Could not connect to target chat: {e}")
        return

    await crud.set_connection(user.id, target_chat_id)
    await msg.reply_html(f"Successfully connected to <b>{chat.title}</b> (<code>{target_chat_id}</code>)! 🔗")


async def disconnect_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    disconnected = await crud.disconnect_user(update.effective_user.id)
    if disconnected:
        await msg.reply_text("Disconnected from chat.")
    else:
        await msg.reply_text("You are not currently connected to any chat.")


async def connection_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    connected_chat_id = await crud.get_connection(update.effective_user.id)

    if not connected_chat_id:
        await msg.reply_text("You are not connected to any chat. Use /connect <chat_id> in PM.")
        return

    try:
        chat = await context.bot.get_chat(connected_chat_id)
        await msg.reply_html(f"Currently connected to <b>{chat.title}</b> (<code>{connected_chat_id}</code>).")
    except Exception:
        await msg.reply_html(f"Currently connected to Chat ID <code>{connected_chat_id}</code>.")


def register(application):
    application.add_handler(CommandHandler("connect", connect_cmd))
    application.add_handler(CommandHandler("disconnect", disconnect_cmd))
    application.add_handler(CommandHandler("connection", connection_cmd))
