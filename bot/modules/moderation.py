from datetime import datetime, timezone

from telegram import ChatPermissions, Update
from telegram.ext import CommandHandler, ContextTypes

from ..utils.decorators import admin_only, bot_admin_required, group_only
from ..utils.extraction import get_reason, get_target_user
from ..utils.flavor import random_phrase
from ..utils.time_parser import parse_time
from .log_channel import send_log

FULL_PERMISSIONS = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
    can_invite_users=True,
)
MUTED_PERMISSIONS = ChatPermissions(can_send_messages=False)


def _mention(user) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


def _reason_offset(update) -> int:
    return 0 if update.effective_message.reply_to_message else 1


@group_only
@admin_only
@bot_admin_required
async def ban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /ban.")
        return
    reason = get_reason(context, offset=_reason_offset(update))
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
    except Exception as e:
        await update.effective_message.reply_text(f"Couldn't ban: {e}")
        return
    text = random_phrase("ban", user=_mention(target))
    if reason:
        text += f"\nReason: {reason}"
    await update.effective_message.reply_html(text)
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[BAN LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Admin:</b> {_mention(update.effective_user)}"
        + (f"\n» <b>Reason:</b> {reason}" if reason else ""),
    )


@group_only
@admin_only
@bot_admin_required
async def unban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /unban.")
        return
    try:
        await context.bot.unban_chat_member(update.effective_chat.id, target.id, only_if_banned=True)
    except Exception as e:
        await update.effective_message.reply_text(f"Couldn't unban: {e}")
        return
    await update.effective_message.reply_html(random_phrase("unban", user=_mention(target)))
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[UNBAN LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Admin:</b> {_mention(update.effective_user)}",
    )


@group_only
@admin_only
@bot_admin_required
async def kick_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /kick.")
        return
    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id)
        await context.bot.unban_chat_member(update.effective_chat.id, target.id, only_if_banned=True)
    except Exception as e:
        await update.effective_message.reply_text(f"Couldn't kick: {e}")
        return
    await update.effective_message.reply_html(random_phrase("kick", user=_mention(target)))
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[KICK LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Admin:</b> {_mention(update.effective_user)}",
    )


@group_only
@admin_only
@bot_admin_required
async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /mute.")
        return
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=MUTED_PERMISSIONS)
    except Exception as e:
        await update.effective_message.reply_text(f"Couldn't mute: {e}")
        return
    await update.effective_message.reply_html(random_phrase("mute", user=_mention(target)))
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[MUTE LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Admin:</b> {_mention(update.effective_user)}",
    )


@group_only
@admin_only
@bot_admin_required
async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context)
    if not target:
        await update.effective_message.reply_text("Reply to a user, or give their user id, to /unmute.")
        return
    try:
        await context.bot.restrict_chat_member(update.effective_chat.id, target.id, permissions=FULL_PERMISSIONS)
    except Exception as e:
        await update.effective_message.reply_text(f"Couldn't unmute: {e}")
        return
    await update.effective_message.reply_html(random_phrase("unmute", user=_mention(target)))
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[UNMUTE LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Admin:</b> {_mention(update.effective_user)}",
    )


@group_only
@admin_only
@bot_admin_required
async def tban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Usage: /tban <user> <duration> [reason]")
        return

    time_arg = None
    if msg.reply_to_message and context.args:
        time_arg = context.args[0]
        reason_offset = 1
    elif len(context.args) > 1:
        time_arg = context.args[1]
        reason_offset = 2
    else:
        await msg.reply_text("Please specify a duration e.g. /tban @user 1h")
        return

    delta = parse_time(time_arg)
    if not delta:
        await msg.reply_text("Invalid duration format. Use e.g. 10m, 1h30m, 2d, 1w.")
        return

    until_date = datetime.now(timezone.utc) + delta
    reason = get_reason(context, offset=reason_offset)

    try:
        await context.bot.ban_chat_member(update.effective_chat.id, target.id, until_date=until_date)
    except Exception as e:
        await msg.reply_text(f"Couldn't temp-ban: {e}")
        return

    text = f"[TBAN] Temporarily banned {_mention(target)} for {time_arg}."
    if reason:
        text += f"\nReason: {reason}"
    await msg.reply_html(text)
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[TEMP-BAN LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Duration:</b> {time_arg}\n» <b>Admin:</b> {_mention(update.effective_user)}"
        + (f"\n» <b>Reason:</b> {reason}" if reason else ""),
    )


@group_only
@admin_only
@bot_admin_required
async def tmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Usage: /tmute <user> <duration> [reason]")
        return

    time_arg = None
    if msg.reply_to_message and context.args:
        time_arg = context.args[0]
        reason_offset = 1
    elif len(context.args) > 1:
        time_arg = context.args[1]
        reason_offset = 2
    else:
        await msg.reply_text("Please specify a duration e.g. /tmute @user 1h")
        return

    delta = parse_time(time_arg)
    if not delta:
        await msg.reply_text("Invalid duration format. Use e.g. 10m, 1h30m, 2d, 1w.")
        return

    until_date = datetime.now(timezone.utc) + delta
    reason = get_reason(context, offset=reason_offset)

    try:
        await context.bot.restrict_chat_member(
            update.effective_chat.id, target.id, permissions=MUTED_PERMISSIONS, until_date=until_date
        )
    except Exception as e:
        await msg.reply_text(f"Couldn't temp-mute: {e}")
        return

    text = f"[TMUTE] Temporarily muted {_mention(target)} for {time_arg}."
    if reason:
        text += f"\nReason: {reason}"
    await msg.reply_html(text)
    await send_log(
        context.bot,
        update.effective_chat.id,
        f"<b>[TEMP-MUTE LOG]</b>\n» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n» <b>Duration:</b> {time_arg}\n» <b>Admin:</b> {_mention(update.effective_user)}"
        + (f"\n» <b>Reason:</b> {reason}" if reason else ""),
    )


def register(application):
    application.add_handler(CommandHandler("ban", ban_cmd))
    application.add_handler(CommandHandler("unban", unban_cmd))
    application.add_handler(CommandHandler("tban", tban_cmd))
    application.add_handler(CommandHandler("kick", kick_cmd))
    application.add_handler(CommandHandler("mute", mute_cmd))
    application.add_handler(CommandHandler("unmute", unmute_cmd))
    application.add_handler(CommandHandler("tmute", tmute_cmd))
