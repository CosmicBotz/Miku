from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..utils.decorators import admin_only, bot_admin_required, group_only
from .log_channel import send_log


@group_only
@admin_only
@bot_admin_required
async def purge_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message:
        await message.reply_text("Reply to the message you want to purge from, then send /purge.")
        return

    start_id = message.reply_to_message.message_id
    end_id = message.message_id
    chat_id = update.effective_chat.id

    deleted = 0
    for msg_id in range(start_id, end_id + 1):
        try:
            await context.bot.delete_message(chat_id, msg_id)
            deleted += 1
        except Exception:
            continue

    await context.bot.send_message(chat_id, f"[PURGE] Purged {deleted} messages.")
    await send_log(
        context.bot,
        chat_id,
        f"<b>[PURGE LOG]</b>\n» <b>Count:</b> {deleted} messages\n» <b>Admin:</b> <a href=\"tg://user?id={update.effective_user.id}\">{update.effective_user.first_name}</a>",
    )


@group_only
@admin_only
@bot_admin_required
async def del_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message:
        await message.reply_text("Reply to the message you want deleted, then send /del.")
        return
    try:
        await message.reply_to_message.delete()
        await message.delete()
        await send_log(
            context.bot,
            update.effective_chat.id,
            f"<b>[DELETE LOG]</b>\n» Single message deleted\n» <b>Admin:</b> <a href=\"tg://user?id={update.effective_user.id}\">{update.effective_user.first_name}</a>",
        )
    except Exception as e:
        await message.reply_text(f"Couldn't delete: {e}")


def register(application):
    application.add_handler(CommandHandler("purge", purge_cmd))
    application.add_handler(CommandHandler("del", del_cmd))
