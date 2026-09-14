import re

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only

URL_RE = re.compile(r"(https?://|t\.me/|www\.)\S+", re.IGNORECASE)

LOCK_TYPES = [
    "text",
    "sticker",
    "photo",
    "video",
    "audio",
    "voice",
    "gif",
    "url",
    "forward",
    "bot",
    "inline",
]


def _is_locked_content(msg, lock_type: str) -> bool:
    if lock_type == "sticker" and msg.sticker:
        return True
    if lock_type == "photo" and msg.photo:
        return True
    if lock_type == "video" and msg.video:
        return True
    if lock_type == "audio" and msg.audio:
        return True
    if lock_type == "voice" and msg.voice:
        return True
    if lock_type == "gif" and msg.animation:
        return True
    if lock_type == "url" and URL_RE.search(msg.text or msg.caption or ""):
        return True
    if lock_type == "forward" and (msg.forward_date or msg.forward_from or msg.forward_from_chat):
        return True
    if lock_type == "inline" and msg.via_bot:
        return True
    if lock_type == "bot" and msg.new_chat_members:
        if any(m.is_bot for m in msg.new_chat_members):
            return True
    if lock_type == "text" and msg.text and not msg.text.startswith("/"):
        return True
    return False


@group_only
@admin_only
async def lock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /lock <locktype>")
        return

    lock_type = context.args[0].lower()
    if lock_type not in LOCK_TYPES:
        await msg.reply_text(f"Invalid lock type. Send /locktypes to see supported types.")
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    locks = getattr(settings, "locks", {}).copy() if hasattr(settings, "locks") else {}
    locks[lock_type] = True

    await crud.update_chat(update.effective_chat.id, locks=locks)
    await msg.reply_text(f"[+] Locked <code>{lock_type}</code>.", parse_mode="HTML")


@group_only
@admin_only
async def unlock_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /unlock <locktype>")
        return

    lock_type = context.args[0].lower()
    if lock_type not in LOCK_TYPES:
        await msg.reply_text(f"Invalid lock type. Send /locktypes to see supported types.")
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    locks = getattr(settings, "locks", {}).copy() if hasattr(settings, "locks") else {}
    locks[lock_type] = False

    await crud.update_chat(update.effective_chat.id, locks=locks)
    await msg.reply_text(f"[+] Unlocked <code>{lock_type}</code>.", parse_mode="HTML")


@group_only
async def locks_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    cfg = get_config()
    settings = await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    locks = getattr(settings, "locks", {}) or {}

    lines = ["<b>:: CHAT LOCKS ::</b>"]
    for ltype in LOCK_TYPES:
        status = "[LOCKED]" if locks.get(ltype) else "[UNLOCKED]"
        lines.append(f"» <code>{ltype}</code>: {status}")

    await msg.reply_html("\n".join(lines))


@group_only
async def locktypes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    types_str = ", ".join([f"<code>{t}</code>" for t in LOCK_TYPES])
    await update.effective_message.reply_html(f"<b>Supported lock types:</b>\n{types_str}")


async def locks_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if not msg or not user or not chat or chat.type not in ("group", "supergroup"):
        return

    cfg = get_config()
    if user.id == cfg.owner_id or user.id in cfg.sudo_users:
        return

    try:
        member = await chat.get_member(user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    if await crud.is_approved_user(chat.id, user.id):
        return

    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    locks = getattr(settings, "locks", {}) or {}

    for lock_type, is_locked in locks.items():
        if is_locked and _is_locked_content(msg, lock_type):
            try:
                await msg.delete()
            except Exception:
                pass
            break


def register(application):
    application.add_handler(CommandHandler("lock", lock_cmd))
    application.add_handler(CommandHandler("unlock", unlock_cmd))
    application.add_handler(CommandHandler("locks", locks_cmd))
    application.add_handler(CommandHandler("locktypes", locktypes_cmd))
    application.add_handler(
        MessageHandler(filters.ChatType.GROUPS & ~filters.StatusUpdate.ALL, locks_check_handler),
        group=4,
    )
