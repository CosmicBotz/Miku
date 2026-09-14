from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only

IMMUTABLE_COMMANDS = {"disable", "enable", "disabled", "enableall", "help", "start"}


@group_only
@admin_only
async def disable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /disable <command_name>")
        return

    cmd_name = context.args[0].lower().lstrip("/")
    if cmd_name in IMMUTABLE_COMMANDS:
        await msg.reply_text(f"The <code>/{cmd_name}</code> command cannot be disabled.", parse_mode="HTML")
        return

    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.disable_command(update.effective_chat.id, cmd_name)
    await msg.reply_text(f"Disabled <code>/{cmd_name}</code> for regular members in this chat.", parse_mode="HTML")


@group_only
@admin_only
async def enable_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /enable <command_name>")
        return

    cmd_name = context.args[0].lower().lstrip("/")
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.enable_command(update.effective_chat.id, cmd_name)
    await msg.reply_text(f"Re-enabled <code>/{cmd_name}</code> in this chat.", parse_mode="HTML")


@group_only
async def disabled_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    disabled = await crud.get_disabled_commands(update.effective_chat.id)
    if not disabled:
        await msg.reply_text("No commands are currently disabled in this chat.")
        return

    cmd_list = [f"• <code>/{c}</code>" for c in sorted(disabled)]
    await msg.reply_html("<b>Disabled commands in this chat:</b>\n" + "\n".join(cmd_list))


@group_only
@admin_only
async def enableall_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    await crud.enable_all_commands(update.effective_chat.id)
    await msg.reply_text("Re-enabled all disabled commands in this chat.")


def register(application):
    application.add_handler(CommandHandler("disable", disable_cmd))
    application.add_handler(CommandHandler("enable", enable_cmd))
    application.add_handler(CommandHandler("disabled", disabled_list_cmd))
    application.add_handler(CommandHandler("enableall", enableall_cmd))
