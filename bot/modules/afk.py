from datetime import datetime, timezone
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from bot.database.crud import get_afk, set_afk, unset_afk


def _format_time(delta_seconds: float) -> str:
    hours, remainder = divmod(int(delta_seconds), 3600)
    minutes, seconds = divmod(remainder, 60)
    days, hours = divmod(hours, 24)
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if seconds > 0 or not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts)


async def afk_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = update.effective_message
    reason = " ".join(context.args) if context.args else "AFK"

    await set_afk(user.id, reason)
    await msg.reply_html(f"<b>{user.mention_html()}</b> is now AFK!\n<b>Reason:</b> {reason}")


async def afk_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    if not msg or not user:
        return

    # 1. Check if sender was AFK and turn off AFK
    afk_data = await get_afk(user.id)
    if afk_data:
        await unset_afk(user.id)
        start_time = afk_data.get("time")
        afk_duration = ""
        if start_time:
            if start_time.tzinfo is None:
                start_time = start_time.replace(tzinfo=timezone.utc)
            now = datetime.now(timezone.utc)
            delta = (now - start_time).total_seconds()
            afk_duration = f" (Away for: {_format_time(delta)})"
        await msg.reply_html(f"Welcome back, <b>{user.mention_html()}</b>! I have removed your AFK status{afk_duration}.")

    # 2. Check if replied user is AFK
    if msg.reply_to_message and msg.reply_to_message.from_user:
        replied_user = msg.reply_to_message.from_user
        if replied_user.id != user.id:
            rep_afk = await get_afk(replied_user.id)
            if rep_afk:
                reason = rep_afk.get("reason", "AFK")
                start_time = rep_afk.get("time")
                afk_duration = ""
                if start_time:
                    if start_time.tzinfo is None:
                        start_time = start_time.replace(tzinfo=timezone.utc)
                    now = datetime.now(timezone.utc)
                    delta = (now - start_time).total_seconds()
                    afk_duration = f" ({_format_time(delta)} ago)"
                await msg.reply_html(
                    f"<b>{replied_user.mention_html()}</b> is currently AFK{afk_duration}.\n"
                    f"<b>Reason:</b> {reason}"
                )

    # 3. Check for entity mentions
    if msg.entities:
        for ent in msg.entities:
            target_user_id = None
            if ent.type == "text_mention" and ent.user:
                target_user_id = ent.user.id
            elif ent.type == "mention":
                # Mention by handle username
                username = msg.text[ent.offset : ent.offset + ent.length].lstrip("@")
                # We can't resolve username to ID directly without DB cache, but reply-check handles most
                pass

            if target_user_id and target_user_id != user.id:
                target_afk = await get_afk(target_user_id)
                if target_afk:
                    reason = target_afk.get("reason", "AFK")
                    start_time = target_afk.get("time")
                    afk_duration = ""
                    if start_time:
                        if start_time.tzinfo is None:
                            start_time = start_time.replace(tzinfo=timezone.utc)
                        now = datetime.now(timezone.utc)
                        delta = (now - start_time).total_seconds()
                        afk_duration = f" ({_format_time(delta)} ago)"
                    await msg.reply_html(
                        f"Target user is currently AFK{afk_duration}.\n"
                        f"<b>Reason:</b> {reason}"
                    )


def register(application):
    application.add_handler(CommandHandler("afk", afk_cmd))
    application.add_handler(
        MessageHandler(filters.ALL & ~filters.COMMAND & ~filters.StatusUpdate.ALL, afk_check_handler),
        group=1,
    )
