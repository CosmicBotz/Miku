import re
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only

ADMIN_RE = re.compile(r"@admins?\b", re.IGNORECASE)


@group_only
async def report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg.reply_to_message:
        await msg.reply_text("Reply to the message you want to report to admins, then send /report.")
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    if not getattr(settings, "reports_enabled", True):
        await msg.reply_text("Reports are currently disabled in this chat.")
        return

    reported_msg = msg.reply_to_message
    reported_user = reported_msg.from_user

    admins = await chat.get_administrators()
    admin_mentions = []
    for admin in admins:
        if not admin.user.is_bot:
            admin_mentions.append(f'<a href="tg://user?id={admin.user.id}">\u200b</a>')

    hidden_tags = "".join(admin_mentions)
    text = (
        f"<b>[REPORT] Message Reported</b>\n"
        f"» <b>Reported by:</b> <a href=\"tg://user?id={user.id}\">{user.first_name}</a>\n"
        f"» <b>Reported user:</b> <a href=\"tg://user?id={reported_user.id}\">{reported_user.first_name}</a>\n"
        f"Admins have been notified. {hidden_tags}"
    )
    await msg.reply_html(text)


@group_only
@admin_only
async def reports_toggle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await msg.reply_text("Usage: /reports on|off")
        return

    enable = context.args[0].lower() == "on"
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, reports_enabled=enable)
    await msg.reply_text(f"User reports are now {'[ON]' if enable else '[OFF]'}.")


async def admin_mention_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not msg.text or chat.type not in ("group", "supergroup"):
        return

    if not ADMIN_RE.search(msg.text):
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    if not getattr(settings, "reports_enabled", True):
        return

    admins = await chat.get_administrators()
    admin_mentions = [
        f'<a href="tg://user?id={a.user.id}">\u200b</a>' for a in admins if not a.user.is_bot
    ]
    hidden_tags = "".join(admin_mentions)

    await msg.reply_html(
        f"<b>[REPORT] Admin Summoned</b> by <a href=\"tg://user?id={user.id}\">{user.first_name}</a>. {hidden_tags}"
    )


def register(application):
    application.add_handler(CommandHandler("report", report_cmd))
    application.add_handler(CommandHandler("reports", reports_toggle_cmd))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND, admin_mention_handler),
        group=0,
    )
