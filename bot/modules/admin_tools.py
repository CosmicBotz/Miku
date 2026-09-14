from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes, MessageHandler, filters

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, bot_admin_required, group_only


@group_only
async def rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cfg = get_config()
    settings = await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    if not settings.rules:
        await update.effective_message.reply_text("No rules have been set for this chat yet.")
        return
    await update.effective_message.reply_text(settings.rules)


@group_only
@admin_only
async def set_rules_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    parts = update.effective_message.text.split(None, 1)
    if len(parts) < 2:
        await update.effective_message.reply_text("Usage: /setrules <text>")
        return
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, rules=parts[1])
    await update.effective_message.reply_text("[+] Rules updated.")


@group_only
async def adminlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    admins = await update.effective_chat.get_administrators()
    lines = [f"» {a.user.full_name}" + (" (owner)" if a.status == "creator" else "") for a in admins]
    await update.effective_message.reply_text("Chat admins:\n" + "\n".join(lines))


@group_only
@admin_only
@bot_admin_required
async def pin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if not message.reply_to_message:
        await message.reply_text("Reply to the message you want to pin, then send /pin.")
        return
    silent = bool(context.args and context.args[0].lower() in ("silent", "quiet"))
    await message.reply_to_message.pin(disable_notification=silent)
    await message.reply_text("[PIN] Message pinned.")


@group_only
@admin_only
@bot_admin_required
async def unpin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat_id = update.effective_chat.id
    try:
        if msg.reply_to_message:
            await context.bot.unpin_chat_message(chat_id, msg.reply_to_message.message_id)
        else:
            await context.bot.unpin_chat_message(chat_id)
        await msg.reply_text("[UNPIN] Message unpinned.")
    except Exception as e:
        await msg.reply_text(f"Could not unpin: {e}")


@group_only
@admin_only
@bot_admin_required
async def unpinall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    try:
        await context.bot.unpin_all_chat_messages(update.effective_chat.id)
        await msg.reply_text("[UNPIN] All messages unpinned.")
    except Exception as e:
        await msg.reply_text(f"Could not unpin all: {e}")


@group_only
@admin_only
@bot_admin_required
async def permapin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /permapin <text to pin>")
        return

    text = " ".join(context.args)
    sent_msg = await msg.reply_text(text)
    try:
        await sent_msg.pin()
    except Exception as e:
        await msg.reply_text(f"Sent message but failed to pin: {e}")


@group_only
@admin_only
async def antichannelpin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await msg.reply_text("Usage: /antichannelpin on|off")
        return

    enable = context.args[0].lower() == "on"
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, antichannelpin=enable)
    await msg.reply_text(f"Anti-channel pin is now {'[ON]' if enable else '[OFF]'}.")


async def _build_settings_panel(chat):
    cfg = get_config()
    s = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    locks_dict = getattr(s, "locks", {}) or {}
    active_locks = [k for k, v in locks_dict.items() if v]

    text = (
        f"<b>:: CHAT SETTINGS — {chat.title} ::</b>\n\n"
        f"» <b>Welcome:</b> {'[ON]' if s.welcome_enabled else '[OFF]'}\n"
        f"» <b>Goodbye:</b> {'[ON]' if s.goodbye_enabled else '[OFF]'}\n"
        f"» <b>Antiflood:</b> {s.flood_limit} msgs / {s.flood_window}s ({s.flood_mode})\n"
        f"» <b>Warn Limit:</b> {s.warn_limit} ({s.warn_mode})\n"
        f"» <b>Antispam:</b> {'[ON]' if s.antispam_enabled else '[OFF]'} ({getattr(s, 'blocklist_mode', 'delete')})\n"
        f"» <b>Active Locks ({len(active_locks)}):</b> {', '.join(active_locks) if active_locks else 'None'}\n"
        f"» <b>Captcha:</b> {'[ON]' if getattr(s, 'captcha_enabled', False) else '[OFF]'} ({getattr(s, 'captcha_mode', 'button')})\n"
        f"» <b>Anti-Raid:</b> {'[ON]' if getattr(s, 'antiraid_enabled', False) else '[OFF]'} ({getattr(s, 'antiraid_action', 'kick')})\n"
        f"» <b>Reports:</b> {'[ON]' if getattr(s, 'reports_enabled', True) else '[OFF]'}\n"
        f"» <b>Log Channel:</b> <code>{getattr(s, 'log_channel', None) or 'None'}</code>\n"
        f"» <b>Anti-Channel Pin:</b> {'[ON]' if getattr(s, 'antichannelpin', False) else '[OFF]'}\n"
    )

    buttons = [
        [
            InlineKeyboardButton(f"Welcome {'[ON]' if s.welcome_enabled else '[OFF]'}", callback_data="stg:welcome"),
            InlineKeyboardButton(f"Goodbye {'[ON]' if s.goodbye_enabled else '[OFF]'}", callback_data="stg:goodbye"),
        ],
        [
            InlineKeyboardButton(f"Antispam {'[ON]' if s.antispam_enabled else '[OFF]'}", callback_data="stg:antispam"),
            InlineKeyboardButton(f"Captcha {'[ON]' if getattr(s, 'captcha_enabled', False) else '[OFF]'}", callback_data="stg:captcha"),
        ],
        [
            InlineKeyboardButton(f"Anti-Raid {'[ON]' if getattr(s, 'antiraid_enabled', False) else '[OFF]'}", callback_data="stg:antiraid"),
            InlineKeyboardButton(f"Reports {'[ON]' if getattr(s, 'reports_enabled', True) else '[OFF]'}", callback_data="stg:reports"),
        ],
        [
            InlineKeyboardButton(f"Anti-Channel Pin {'[ON]' if getattr(s, 'antichannelpin', False) else '[OFF]'}", callback_data="stg:antichannelpin"),
            InlineKeyboardButton("[ Refresh ]", callback_data="stg:refresh"),
        ],
    ]
    return text, InlineKeyboardMarkup(buttons)


@group_only
@admin_only
async def settings_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, keyboard = await _build_settings_panel(update.effective_chat)
    await update.effective_message.reply_html(text, reply_markup=keyboard)


async def settings_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat = update.effective_chat
    user = update.effective_user

    try:
        member = await chat.get_member(user.id)
        if member.status not in ("administrator", "creator"):
            await query.answer("[!] You must be an admin to toggle settings.", show_alert=True)
            return
    except Exception:
        await query.answer("Could not verify admin status.", show_alert=True)
        return

    data = query.data
    field_map = {
        "stg:welcome": "welcome_enabled",
        "stg:goodbye": "goodbye_enabled",
        "stg:antispam": "antispam_enabled",
        "stg:captcha": "captcha_enabled",
        "stg:antiraid": "antiraid_enabled",
        "stg:reports": "reports_enabled",
        "stg:antichannelpin": "antichannelpin",
    }

    if data in field_map:
        field = field_map[data]
        cfg = get_config()
        settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
        cur_val = getattr(settings, field, False)
        await crud.update_chat(chat.id, **{field: not cur_val})
        await query.answer(f"Toggled {field.replace('_', ' ')}.")

    text, keyboard = await _build_settings_panel(chat)
    try:
        await query.message.edit_text(text, parse_mode="HTML", reply_markup=keyboard)
    except Exception:
        pass
    await query.answer()


async def antichannelpin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not chat or chat.type not in ("group", "supergroup"):
        return

    is_auto_forward = getattr(msg, "is_automatic_forward", False)
    is_pinned_service = bool(msg.pinned_message)

    if not (is_auto_forward or is_pinned_service):
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    if not getattr(settings, "antichannelpin", False):
        return

    try:
        if is_auto_forward:
            await context.bot.unpin_chat_message(chat.id, msg.message_id)
        elif is_pinned_service and msg.pinned_message and getattr(msg.pinned_message, "is_automatic_forward", False):
            await context.bot.unpin_chat_message(chat.id, msg.pinned_message.message_id)
            await msg.delete()
    except Exception:
        pass


def register(application):
    application.add_handler(CommandHandler("rules", rules_cmd))
    application.add_handler(CommandHandler("setrules", set_rules_cmd))
    application.add_handler(CommandHandler("adminlist", adminlist_cmd))
    application.add_handler(CommandHandler("pin", pin_cmd))
    application.add_handler(CommandHandler("unpin", unpin_cmd))
    application.add_handler(CommandHandler("unpinall", unpinall_cmd))
    application.add_handler(CommandHandler("permapin", permapin_cmd))
    application.add_handler(CommandHandler("antichannelpin", antichannelpin_cmd))
    application.add_handler(CommandHandler("settings", settings_cmd))
    application.add_handler(CallbackQueryHandler(settings_callback_handler, pattern=r"^stg:"))
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS & (filters.StatusUpdate.PINNED_MESSAGE | filters.FORWARDED), antichannelpin_handler),
        group=0,
    )
