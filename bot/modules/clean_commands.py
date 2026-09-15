from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..config import get_config
from ..database import crud


async def clean_commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto-deletion of command invocation messages in group chat."""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if not chat or chat.type not in ("group", "supergroup"):
        await msg.reply_html("[!] This command can only be used in group chats.")
        return

    cfg = get_config()
    is_admin = False
    if user.id == cfg.owner_id or user.id in cfg.sudo_users:
        is_admin = True
    else:
        try:
            member = await chat.get_member(user.id)
            is_admin = member.status in ("administrator", "creator")
        except Exception:
            is_admin = False

    if not is_admin:
        await msg.reply_html("[!] Only group administrators can configure clean commands mode.")
        return

    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    args = context.args

    if not args:
        current_status = getattr(settings, "clean_commands", False)
        status_str = "ENABLED" if current_status else "DISABLED"
        await msg.reply_html(
            f"<b>:: CLEAN COMMANDS MODE ::</b>\n\n"
            f"• Current Status: <b>{status_str}</b>\n\n"
            f"<i>Usage: <code>/cleancommands on|off</code> to toggle.</i>"
        )
        return

    val = args[0].lower()
    if val in ("on", "yes", "true", "enable", "1"):
        new_val = True
    elif val in ("off", "no", "false", "disable", "0"):
        new_val = False
    else:
        await msg.reply_html("<b>Usage:</b> <code>/cleancommands on|off</code>")
        return

    await crud.update_chat(chat.id, clean_commands=new_val)
    status_str = "ENABLED" if new_val else "DISABLED"
    await msg.reply_html(
        f"<b>:: CLEAN COMMANDS MODE ::</b>\n\n"
        f"• Clean commands mode is now <b>{status_str}</b> for <b>{chat.title}</b>."
    )


def register(application):
    application.add_handler(CommandHandler(["cleancommands", "cleancommand", "cmdclean"], clean_commands_cmd))
