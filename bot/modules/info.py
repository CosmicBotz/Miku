from telegram import (
    MessageOriginChannel,
    MessageOriginChat,
    MessageOriginHiddenUser,
    MessageOriginUser,
    Update,
)
from telegram.ext import CommandHandler, ContextTypes

from ..utils.extraction import get_target_user
from ..utils.telethon_client import resolve_entity


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

    lines = ["<b>:: IDENTIFICATION CARD ::</b>\n"]

    # 1. COMMAND USER
    if user:
        lines.append("» <b>USER WHO USED COMMAND</b>")
        lines.append(f"• <b>Name:</b> {_mention(user)}")
        lines.append(f"• <b>User ID:</b> <code>{user.id}</code>")
        if user.username:
            lines.append(f"• <b>Username:</b> @{user.username}")
        lines.append("")

    # 2. CURRENT CHAT
    if chat:
        chat_title = chat.title or chat.first_name or "Private Chat"
        chat_type = chat.type.capitalize()
        lines.append("» <b>CHAT WHERE USED</b>")
        lines.append(f"• <b>Title:</b> {chat_title}")
        lines.append(f"• <b>Chat ID:</b> <code>{chat.id}</code>")
        lines.append(f"• <b>Type:</b> {chat_type}")
        if chat.username:
            lines.append(f"• <b>Chat Username:</b> @{chat.username}")
        linked_id = getattr(chat, "linked_chat_id", None)
        if linked_id:
            lines.append(f"• <b>Linked Discussion Chat ID:</b> <code>{linked_id}</code>")
        lines.append("")

    # 3. SPECIFIED TARGET
    if context.args:
        lines.append("» <b>SPECIFIED TARGET ENTITY</b>")
        target = await get_target_user(update, context)
        if target:
            lines.append(f"• <b>Target User:</b> {_mention(target)}")
            lines.append(f"• <b>User ID:</b> <code>{target.id}</code>")
            if target.username:
                lines.append(f"• <b>Username:</b> @{target.username}")
        else:
            arg = context.args[0]
            try:
                target_chat = await context.bot.get_chat(arg)
                name = target_chat.title or target_chat.first_name or str(target_chat.id)
                lines.append(f"• <b>Target Name:</b> {name}")
                lines.append(f"• <b>Target ID:</b> <code>{target_chat.id}</code>")
                lines.append(f"• <b>Target Type:</b> {target_chat.type.capitalize()}")
                if target_chat.username:
                    lines.append(f"• <b>Target Username:</b> @{target_chat.username}")
            except Exception:
                resolved = await resolve_entity(arg)
                if resolved:
                    lines.append(f"• <b>Target Name:</b> {resolved.display_name}")
                    lines.append(f"• <b>Target ID:</b> <code>{resolved.id}</code>")
                    lines.append(f"• <b>Target Type:</b> {resolved.entity_type}")
                    if resolved.username:
                        lines.append(f"• <b>Target Username:</b> @{resolved.username}")
                else:
                    await msg.reply_text(f"Could not find user or chat: {arg}")
                    return
        lines.append("")

    # 4. REPLIED MESSAGE & TARGET USER / CHANNEL
    if msg.reply_to_message:
        reply = msg.reply_to_message
        lines.append("» <b>REPLIED MESSAGE & TARGET USER</b>")
        lines.append(f"• <b>Replied Message ID:</b> <code>{reply.message_id}</code>")

        if reply.from_user:
            lines.append(f"• <b>Replied User:</b> {_mention(reply.from_user)}")
            lines.append(f"• <b>Replied User ID:</b> <code>{reply.from_user.id}</code>")
            if reply.from_user.username:
                lines.append(f"• <b>Replied Username:</b> @{reply.from_user.username}")

        if getattr(reply, "sender_chat", None):
            s_chat = reply.sender_chat
            lines.append(f"• <b>Sent On Behalf Of Channel:</b> {s_chat.title or 'Channel'}")
            lines.append(f"• <b>Sender Channel ID:</b> <code>{s_chat.id}</code>")
            if s_chat.username:
                lines.append(f"• <b>Sender Channel Username:</b> @{s_chat.username}")

        origin = getattr(reply, "forward_origin", None)
        if origin:
            lines.append("")
            lines.append("» <b>FORWARDED ORIGIN / CHANNEL</b>")
            if isinstance(origin, MessageOriginUser):
                f_u = origin.sender_user
                lines.append(f"• <b>Forwarded User:</b> {_mention(f_u)}")
                lines.append(f"• <b>Forwarded User ID:</b> <code>{f_u.id}</code>")
                if f_u.username:
                    lines.append(f"• <b>Forwarded Username:</b> @{f_u.username}")
            elif isinstance(origin, (MessageOriginChat, MessageOriginChannel)):
                f_chat = getattr(origin, "sender_chat", None) or getattr(origin, "chat", None)
                if f_chat:
                    f_name = f_chat.title or f_chat.first_name or str(f_chat.id)
                    lines.append(f"• <b>Forwarded Channel/Chat:</b> {f_name}")
                    lines.append(f"• <b>Forwarded Channel/Chat ID:</b> <code>{f_chat.id}</code>")
                    if f_chat.username:
                        lines.append(f"• <b>Forwarded Username:</b> @{f_chat.username}")
            elif isinstance(origin, MessageOriginHiddenUser):
                lines.append(f"• <b>Forwarded User:</b> {origin.sender_user_name} <i>(Hidden Profile)</i>")
        else:
            f_u = getattr(reply, "forward_from", None)
            if f_u:
                lines.append("")
                lines.append("» <b>FORWARDED ORIGIN / USER</b>")
                lines.append(f"• <b>Forwarded User:</b> {_mention(f_u)}")
                lines.append(f"• <b>Forwarded User ID:</b> <code>{f_u.id}</code>")
                if f_u.username:
                    lines.append(f"• <b>Forwarded Username:</b> @{f_u.username}")

            f_c = getattr(reply, "forward_from_chat", None)
            if f_c:
                lines.append("")
                lines.append("» <b>FORWARDED ORIGIN / CHANNEL</b>")
                lines.append(f"• <b>Forwarded Channel/Chat:</b> {f_c.title or 'Channel'}")
                lines.append(f"• <b>Forwarded Channel/Chat ID:</b> <code>{f_c.id}</code>")
                if f_c.username:
                    lines.append(f"• <b>Forwarded Username:</b> @{f_c.username}")

    clean_text = "\n".join(lines).strip()
    await msg.reply_html(clean_text)


def register(application):
    application.add_handler(CommandHandler("info", info_cmd))
    application.add_handler(CommandHandler("id", id_cmd))

