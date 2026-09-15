from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..config import get_config
from ..database import crud


async def clean_commands_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Toggle auto-deletion of command invocation messages in group chat."""
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message

    if not chat or chat.type not in ("group", "supergroup"):
        await msg.reply_html("[!] This command can only be used in group chats.", quote=False)
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
        await msg.reply_html("[!] Only group administrators can configure clean commands mode.", quote=False)
        return

    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    args = context.args

    if not args:
        current_status = getattr(settings, "clean_commands", False)
        status_str = "ENABLED" if current_status else "DISABLED"
        await msg.reply_html(
            f"<b>:: CLEAN COMMANDS MODE ::</b>\n\n"
            f"• Current Status: <b>{status_str}</b>\n\n"
            f"<i>Usage: <code>/cleancommands on|off</code> to toggle.</i>",
            quote=False,
        )
        return

    val = args[0].lower()
    if val in ("on", "yes", "true", "enable", "1"):
        new_val = True
    elif val in ("off", "no", "false", "disable", "0"):
        new_val = False
    else:
        await msg.reply_html("<b>Usage:</b> <code>/cleancommands on|off</code>", quote=False)
        return

    await crud.update_chat(chat.id, clean_commands=new_val)
    status_str = "ENABLED" if new_val else "DISABLED"
    await msg.reply_html(
        f"<b>:: CLEAN COMMANDS MODE ::</b>\n\n"
        f"• Clean commands mode is now <b>{status_str}</b> for <b>{chat.title}</b>.",
        quote=False,
    )


async def clean_any_command_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Delete ANY command message (any user, any bot's command - not just ours)
    when clean_commands mode is on for this chat.

    Runs in its own group *before* command dispatch (group 0), so it deletes
    the trigger message without depending on whether this bot even has a
    handler for that command.
    """
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not chat or chat.type not in ("group", "supergroup"):
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    if not getattr(settings, "clean_commands", False):
        return

    try:
        await msg.delete()
    except Exception:
        pass


def register(application):
    application.add_handler(CommandHandler(["cleancommands", "cleancommand", "cmdclean"], clean_commands_cmd))
    # group=-1: runs before the real CommandHandlers in group 0. PTB only
    # runs the first matching handler *within* a group, so this has to live
    # in its own group - sharing group 0 would let it race the actual
    # command handlers and sometimes swallow them instead of just deleting
    # the trigger message.
    application.add_handler(
        MessageHandler(filters.COMMAND & filters.ChatType.GROUPS, clean_any_command_handler),
        group=-1,
    )
