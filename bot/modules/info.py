from telegram import (
    MessageOriginChannel,
    MessageOriginChat,
    MessageOriginHiddenUser,
    MessageOriginUser,
    Update,
)
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

    lines = []

    # If arguments are provided (e.g. /id @username or /id 123456)
    if context.args:
        target = await get_target_user(update, context)
        if target:
            lines.append(f"» <b>Target User:</b> {_mention(target)}")
            lines.append(f"» <b>Target User ID:</b> <code>{target.id}</code>")
            if target.username:
                lines.append(f"» <b>Target Username:</b> @{target.username}")
        else:
            arg = context.args[0]
            try:
                target_chat = await context.bot.get_chat(arg)
                name = target_chat.title or target_chat.first_name or str(target_chat.id)
                lines.append(f"» <b>Target Name:</b> {name}")
                lines.append(f"» <b>Target ID:</b> <code>{target_chat.id}</code>")
                if target_chat.username:
                    lines.append(f"» <b>Target Username:</b> @{target_chat.username}")
            except Exception:
                await msg.reply_text(f"Could not find user or chat: {arg}")
                return

    if not context.args:
        lines.append(f"» <b>Your ID:</b> <code>{user.id}</code>")
        if user.username:
            lines.append(f"» <b>Your Username:</b> @{user.username}")
        lines.append(f"» <b>Chat ID:</b> <code>{chat.id}</code>")

        if msg.reply_to_message:
            reply = msg.reply_to_message
            lines.append(f"» <b>Replied Message ID:</b> <code>{reply.message_id}</code>")
            if reply.from_user:
                lines.append(f"» <b>Replied User ID:</b> <code>{reply.from_user.id}</code>")
                if reply.from_user.username:
                    lines.append(f"» <b>Replied Username:</b> @{reply.from_user.username}")

            # PTB 21+ / Bot API 7.0+ MessageOrigin support
            origin = getattr(reply, "forward_origin", None)
            if origin:
                if isinstance(origin, MessageOriginUser):
                    lines.append(f"» <b>Forwarded User ID:</b> <code>{origin.sender_user.id}</code>")
                    if origin.sender_user.username:
                        lines.append(f"» <b>Forwarded Username:</b> @{origin.sender_user.username}")
                elif isinstance(origin, (MessageOriginChat, MessageOriginChannel)):
                    f_chat = getattr(origin, "sender_chat", None) or getattr(origin, "chat", None)
                    if f_chat:
                        lines.append(f"» <b>Forwarded Chat ID:</b> <code>{f_chat.id}</code>")
                        if f_chat.username:
                            lines.append(f"» <b>Forwarded Chat Username:</b> @{f_chat.username}")
                elif isinstance(origin, MessageOriginHiddenUser):
                    lines.append(f"» <b>Forwarded User:</b> {origin.sender_user_name} (Hidden)")
            else:
                # Safe fallbacks for legacy PTB attributes
                if getattr(reply, "forward_from", None):
                    lines.append(f"» <b>Forwarded User ID:</b> <code>{reply.forward_from.id}</code>")
                if getattr(reply, "forward_from_chat", None):
                    lines.append(f"» <b>Forwarded Chat ID:</b> <code>{reply.forward_from_chat.id}</code>")

    await msg.reply_html("\n".join(lines))


def register(application):
    application.add_handler(CommandHandler("info", info_cmd))
    application.add_handler(CommandHandler("id", id_cmd))

