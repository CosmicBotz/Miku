from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only
from ..utils.time_parser import parse_time
from .moderation import MUTED_PERMISSIONS


async def disable_antiraid_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.data["chat_id"]
    await crud.update_chat(chat_id, antiraid_enabled=False)
    try:
        await context.bot.send_message(
            chat_id, "[ANTIRAID] Anti-Raid mode has automatically expired and is now disabled."
        )
    except Exception:
        pass


@group_only
@admin_only
async def antiraid_toggle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await msg.reply_text("Usage: /antiraid on|off")
        return

    enable = context.args[0].lower() == "on"
    chat_id = update.effective_chat.id
    cfg = get_config()
    settings = await crud.get_or_create_chat(chat_id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(chat_id, antiraid_enabled=enable)

    if enable:
        raid_seconds = getattr(settings, "raid_time", 3600)
        if context.job_queue:
            context.job_queue.run_once(
                disable_antiraid_job, raid_seconds, data={"chat_id": chat_id}
            )
        await msg.reply_text(
            f"[ANTIRAID] <b>Anti-Raid ENABLED.</b> All new joining members will be auto-{settings.antiraid_action}ed for the next {raid_seconds // 60} minutes.",
            parse_mode="HTML",
        )
    else:
        await msg.reply_text("[ANTIRAID] Anti-Raid mode disabled.")


@group_only
@admin_only
async def raid_time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /raidtime <duration>  (e.g. 1h, 30m, 2d)")
        return

    delta = parse_time(context.args[0])
    if not delta:
        await msg.reply_text("Invalid duration. Use e.g. 30m, 1h, 2d.")
        return

    seconds = int(delta.total_seconds())
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, raid_time=seconds)
    await msg.reply_text(f"[ANTIRAID] Anti-Raid duration set to {context.args[0]} ({seconds} seconds).")


@group_only
@admin_only
async def raid_action_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("kick", "ban", "mute"):
        await msg.reply_text("Usage: /raidactionmode kick|ban|mute")
        return

    action = context.args[0].lower()
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, antiraid_action=action)
    await msg.reply_text(f"[ANTIRAID] Anti-Raid action set to {action}.")


async def check_antiraid_join(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> bool:
    chat = update.effective_chat
    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)

    if not getattr(settings, "antiraid_enabled", False):
        return False

    action = getattr(settings, "antiraid_action", "kick")
    try:
        if action == "ban":
            await context.bot.ban_chat_member(chat.id, user.id)
        elif action == "kick":
            await context.bot.ban_chat_member(chat.id, user.id)
            await context.bot.unban_chat_member(chat.id, user.id, only_if_banned=True)
        else:
            await context.bot.restrict_chat_member(chat.id, user.id, permissions=MUTED_PERMISSIONS)

        await update.effective_message.reply_html(
            f"[ANTIRAID] Automatically {action}ed new user <a href=\"tg://user?id={user.id}\">{user.first_name}</a>."
        )
        return True
    except Exception:
        return False


def register(application):
    application.add_handler(CommandHandler("antiraid", antiraid_toggle_cmd))
    application.add_handler(CommandHandler("raidtime", raid_time_cmd))
    application.add_handler(CommandHandler("raidactionmode", raid_action_mode_cmd))
