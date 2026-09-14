from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..utils.extraction import get_target_user


def _mention(user) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


async def info_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target_user(update, context) or update.effective_user

    try:
        photos = await context.bot.get_user_profile_photos(target.id)
        photo_count = photos.total if photos else 0
    except Exception:
        photo_count = 0

    lines = [
        f"<b>:: USER INFO — {_mention(target)} ::</b>",
        f"» <b>ID:</b> <code>{target.id}</code>",
        f"» <b>First Name:</b> {target.first_name}",
        f"» <b>Last Name:</b> {target.last_name or 'N/A'}",
        f"» <b>Username:</b> @{target.username}" if target.username else "» <b>Username:</b> None",
        f"» <b>Is Bot:</b> {'Yes' if target.is_bot else 'No'}",
        f"» <b>Profile Photos Count:</b> {photo_count}",
        f"» <b>User Link:</b> <a href=\"tg://user?id={target.id}\">link</a>",
    ]
    await msg.reply_html("\n".join(lines))


async def id_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    lines = [
        f"» <b>Your ID:</b> <code>{user.id}</code>",
        f"» <b>Chat ID:</b> <code>{chat.id}</code>",
    ]

    if msg.reply_to_message:
        reply = msg.reply_to_message
        lines.append(f"» <b>Replied Message ID:</b> <code>{reply.message_id}</code>")
        if reply.from_user:
            lines.append(f"» <b>Replied User ID:</b> <code>{reply.from_user.id}</code>")
        if reply.forward_from:
            lines.append(f"» <b>Forwarded User ID:</b> <code>{reply.forward_from.id}</code>")
        if reply.forward_from_chat:
            lines.append(f"» <b>Forwarded Chat ID:</b> <code>{reply.forward_from_chat.id}</code>")

    await msg.reply_html("\n".join(lines))


def register(application):
    application.add_handler(CommandHandler("info", info_cmd))
    application.add_handler(CommandHandler("id", id_cmd))
