import re

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only
from .moderation import MUTED_PERMISSIONS

URL_RE = re.compile(r"(https?://|t\.me/|www\.)\S+", re.IGNORECASE)


async def antispam_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not message or not message.text or chat.type not in ("group", "supergroup") or not user:
        return

    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
    if not settings.antispam_enabled:
        return

    try:
        member = await chat.get_member(user.id)
        if member.status in ("administrator", "creator"):
            return
    except Exception:
        pass

    if await crud.is_approved_user(chat.id, user.id):
        return

    text_lower = message.text.lower()
    blacklisted_words = await crud.list_blacklist_words(chat.id)

    for word in blacklisted_words:
        if word.lower() in text_lower:
            if getattr(settings, "blacklist_delete", True):
                try:
                    await message.delete()
                except Exception:
                    pass

            mode = getattr(settings, "blocklist_mode", "delete")
            try:
                if mode == "warn":
                    count = await crud.add_warn(chat.id, user.id, reason="Blacklisted word", admin_id=context.bot.id)
                    await message.reply_html(
                        f"[!] User <a href=\"tg://user?id={user.id}\">{user.first_name}</a> used blacklisted word! ({count}/{settings.warn_limit} warnings)"
                    )
                elif mode == "mute":
                    await context.bot.restrict_chat_member(chat.id, user.id, permissions=MUTED_PERMISSIONS)
                elif mode == "kick":
                    await context.bot.ban_chat_member(chat.id, user.id)
                    await context.bot.unban_chat_member(chat.id, user.id, only_if_banned=True)
                elif mode == "ban":
                    await context.bot.ban_chat_member(chat.id, user.id)
            except Exception:
                pass
            return

    if settings.max_links_per_message and len(URL_RE.findall(message.text)) > settings.max_links_per_message:
        try:
            await message.delete()
        except Exception:
            pass


@group_only
@admin_only
async def add_blacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /addblacklist <word or phrase>")
        return
    word = " ".join(context.args).lower()
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    added = await crud.add_blacklist_word(update.effective_chat.id, word)
    await update.effective_message.reply_text("[+] Added to blacklist." if added else "[!] That is already blacklisted.")


@group_only
@admin_only
async def rm_blacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.effective_message.reply_text("Usage: /rmblacklist <word or phrase>")
        return
    word = " ".join(context.args).lower()
    removed = await crud.remove_blacklist_word(update.effective_chat.id, word)
    await update.effective_message.reply_text("[-] Removed from blacklist." if removed else "[!] That was not blacklisted.")


@group_only
async def list_blacklist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    words = await crud.list_blacklist_words(update.effective_chat.id)
    if not words:
        await update.effective_message.reply_text("No blacklisted words yet.")
        return
    await update.effective_message.reply_text("Blacklisted words:\n" + ", ".join(words))


@group_only
@admin_only
async def blocklist_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("delete", "warn", "mute", "kick", "ban"):
        await msg.reply_text("Usage: /blocklistmode delete|warn|mute|kick|ban")
        return

    mode = context.args[0].lower()
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, blocklist_mode=mode)
    await msg.reply_text(f"[+] Blacklist trigger action set to {mode}.")


@group_only
@admin_only
async def blacklist_delete_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await msg.reply_text("Usage: /blacklistdelete on|off")
        return

    enable = context.args[0].lower() == "on"
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, blacklist_delete=enable)
    await msg.reply_text(f"[+] Auto-deletion of blacklisted messages is now {'[ON]' if enable else '[OFF]'}.")


def register(application):
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, antispam_check),
        group=2,
    )
    application.add_handler(CommandHandler("addblacklist", add_blacklist_cmd))
    application.add_handler(CommandHandler("rmblacklist", rm_blacklist_cmd))
    application.add_handler(CommandHandler("blacklist", list_blacklist_cmd))
    application.add_handler(CommandHandler("blocklistmode", blocklist_mode_cmd))
    application.add_handler(CommandHandler("blacklistdelete", blacklist_delete_cmd))
