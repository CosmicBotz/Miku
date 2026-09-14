from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, bot_admin_required, group_only
from ..utils.extraction import get_reason, get_target_user
from ..utils.flavor import random_phrase
from .log_channel import send_log
from .moderation import MUTED_PERMISSIONS, _mention, _reason_offset


async def _apply_warn_punishment(update: Update, context: ContextTypes.DEFAULT_TYPE, target, mode: str):
    chat_id = update.effective_chat.id
    try:
        if mode == "ban":
            await context.bot.ban_chat_member(chat_id, target.id)
            note = "banned"
        elif mode == "kick":
            await context.bot.ban_chat_member(chat_id, target.id)
            await context.bot.unban_chat_member(chat_id, target.id, only_if_banned=True)
            note = "kicked"
        else:
            await context.bot.restrict_chat_member(chat_id, target.id, permissions=MUTED_PERMISSIONS)
            note = "muted"
    except Exception as e:
        await update.effective_message.reply_text(f"Hit the warn limit but couldn't act on it: {e}")
        return
    await crud.reset_warns(chat_id, target.id)
    await update.effective_message.reply_text(
        f"That was the last straw — {target.first_name} has been {note} and their warnings reset."
    )


@group_only
@admin_only
@bot_admin_required
async def warn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /warn.")
        return
    reason = get_reason(context, offset=_reason_offset(update))
    cfg = get_config()
    settings = await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    count = await crud.add_warn(update.effective_chat.id, target.id, reason=reason, admin_id=update.effective_user.id)

    text = random_phrase("warn", user=_mention(target), count=count, limit=settings.warn_limit)
    if reason:
        text += f"\nReason: {reason}"
    await update.effective_message.reply_html(text)
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[WARN LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Warns:</b> {count}/{settings.warn_limit}\n» <b>Admin:</b> {_mention(update.effective_user)}"
        + (f"\n» <b>Reason:</b> {reason}" if reason else ""),
    )

    if count >= settings.warn_limit:
        await _apply_warn_punishment(update, context, target, settings.warn_mode)


@group_only
async def warns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context) or update.effective_user
    warns = await crud.get_warns(update.effective_chat.id, target.id)
    if not warns:
        await update.effective_message.reply_text(f"{target.first_name} has a clean record. No warnings!")
        return
    lines = [f"{i + 1}. {w.get('reason') or 'no reason given'}" for i, w in enumerate(warns)]
    await update.effective_message.reply_text(f"{target.first_name}'s warnings:\n" + "\n".join(lines))


@group_only
@admin_only
async def resetwarns_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /resetwarns.")
        return
    await crud.reset_warns(update.effective_chat.id, target.id)
    await update.effective_message.reply_text(f"{target.first_name}'s warnings have been cleared.")
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[RESET WARNS LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Admin:</b> {_mention(update.effective_user)}",
    )


@group_only
@admin_only
async def unwarn_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /unwarn.")
        return
    removed = await crud.remove_last_warn(update.effective_chat.id, target.id)
    if removed:
        await update.effective_message.reply_text(f"Removed one warning from {target.first_name}.")
        await send_log(
            context.bot,
            update.effective_chat.id,
            f"<b>[UNWARN LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Admin:</b> {_mention(update.effective_user)}",
        )
    else:
        await update.effective_message.reply_text(f"{target.first_name} has no warnings to remove.")


@group_only
@admin_only
async def set_warn_limit_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or not context.args[0].isdigit():
        await update.effective_message.reply_text("Usage: /setwarnlimit <number>")
        return
    limit = max(1, int(context.args[0]))
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, warn_limit=limit)
    await update.effective_message.reply_text(f"Warn limit set to {limit}.")


@group_only
@admin_only
async def set_warn_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or context.args[0].lower() not in ("mute", "kick", "ban"):
        await update.effective_message.reply_text("Usage: /setwarnmode mute|kick|ban")
        return
    mode = context.args[0].lower()
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, warn_mode=mode)
    await update.effective_message.reply_text(f"Warn mode set to {mode}.")


def register(application):
    application.add_handler(CommandHandler("warn", warn_cmd))
    application.add_handler(CommandHandler("warns", warns_cmd))
    application.add_handler(CommandHandler("resetwarns", resetwarns_cmd))
    application.add_handler(CommandHandler("unwarn", unwarn_cmd))
    application.add_handler(CommandHandler("setwarnlimit", set_warn_limit_cmd))
    application.add_handler(CommandHandler("setwarnmode", set_warn_mode_cmd))
