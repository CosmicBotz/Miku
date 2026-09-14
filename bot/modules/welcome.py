from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only


from .antiraid import check_antiraid_join
from .captcha import send_captcha_challenge
from .federations import check_fed_ban_on_join


def _placeholders(user, chat, count=None) -> dict:
    mention = f'<a href="tg://user?id={user.id}">{user.first_name}</a>'
    return {
        "first": user.first_name or "",
        "last": user.last_name or "",
        "fullname": (user.first_name or "") + ((" " + user.last_name) if user.last_name else ""),
        "username": f"@{user.username}" if user.username else (user.first_name or ""),
        "mention": mention,
        "id": user.id,
        "chat_title": chat.title or "this chat",
        "count": count if count is not None else "",
    }


async def on_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)

    if settings.clean_service_messages:
        try:
            await message.delete()
        except Exception:
            pass

    for member in message.new_chat_members:
        if member.is_bot and member.id == context.bot.id:
            continue  # the bot itself was added to the group

        # 1. Check Federation Ban
        fbanned = await check_fed_ban_on_join(update, context, member)
        if fbanned:
            continue

        # 2. Check Anti-Raid
        raided = await check_antiraid_join(update, context, member)
        if raided:
            continue

        # 3. Check Captcha Challenge
        if getattr(settings, "captcha_enabled", False):
            await send_captcha_challenge(update, context, member)
            continue

        if not settings.welcome_enabled:
            continue

        template = settings.welcome_message or "Welcome, {mention}!"
        try:
            member_count = await context.bot.get_chat_member_count(chat.id)
        except Exception:
            member_count = None


        try:
            text = template.format(**_placeholders(member, chat, member_count))
        except Exception:
            text = f"Welcome, {member.first_name}!"

        if settings.clean_welcome and settings.last_welcome_msg_id:
            try:
                await context.bot.delete_message(chat.id, settings.last_welcome_msg_id)
            except Exception:
                pass

        sent = await context.bot.send_message(chat.id, text, parse_mode="HTML")
        if settings.clean_welcome:
            await crud.update_chat(chat.id, last_welcome_msg_id=sent.message_id)


async def on_left_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    message = update.effective_message
    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)

    if settings.clean_service_messages:
        try:
            await message.delete()
        except Exception:
            pass

    if not settings.goodbye_enabled:
        return

    member = message.left_chat_member
    if member is None or (member.is_bot and member.id == context.bot.id):
        return

    template = settings.goodbye_message or "{first} left the chat."
    try:
        text = template.format(**_placeholders(member, chat))
    except Exception:
        text = f"{member.first_name} left the chat."

    await context.bot.send_message(chat.id, text, parse_mode="HTML")


@group_only
@admin_only
async def set_welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.effective_message.text.split(None, 1)
    if len(parts) < 2:
        await update.effective_message.reply_text(
            "Usage: /setwelcome <text>\n"
            "Placeholders: {first} {last} {fullname} {username} {mention} {chat_title} {count}"
        )
        return
    await crud.update_chat(update.effective_chat.id, welcome_message=parts[1])
    await update.effective_message.reply_text("Welcome message updated! ✨")


@group_only
@admin_only
async def set_goodbye_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.effective_message.text.split(None, 1)
    if len(parts) < 2:
        await update.effective_message.reply_text("Usage: /setgoodbye <text>")
        return
    await crud.update_chat(update.effective_chat.id, goodbye_message=parts[1])
    await update.effective_message.reply_text("Goodbye message updated! 👋")


async def _toggle(update: Update, context: ContextTypes.DEFAULT_TYPE, field: str, label: str, command: str):
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await update.effective_message.reply_text(f"Usage: /{command} on|off")
        return
    value = context.args[0].lower() == "on"
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, **{field: value})
    await update.effective_message.reply_text(f"{label} turned {'ON ✅' if value else 'OFF ❌'}")


@group_only
@admin_only
async def toggle_welcome_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _toggle(update, context, "welcome_enabled", "Welcome messages", "welcome")


@group_only
@admin_only
async def toggle_goodbye_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _toggle(update, context, "goodbye_enabled", "Goodbye messages", "goodbye")


def register(application):
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, on_new_member))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, on_left_member))
    application.add_handler(CommandHandler("setwelcome", set_welcome_cmd))
    application.add_handler(CommandHandler("setgoodbye", set_goodbye_cmd))
    application.add_handler(CommandHandler("welcome", toggle_welcome_cmd))
    application.add_handler(CommandHandler("goodbye", toggle_goodbye_cmd))
