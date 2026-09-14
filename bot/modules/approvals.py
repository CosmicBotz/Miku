from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..database import crud
from ..utils.decorators import admin_only, group_only
from ..utils.extraction import get_target_user


def _mention(user) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


@group_only
@admin_only
async def approve_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Reply to a user, or pass their user ID/@username, to /approve.")
        return

    added = await crud.add_approval(update.effective_chat.id, target.id)
    if added:
        await msg.reply_html(f"[+] Approved {_mention(target)}. They can now bypass flood, spam, and lock filters.")
    else:
        await msg.reply_html(f"{_mention(target)} is already approved in this chat.")


@group_only
@admin_only
async def unapprove_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Reply to a user, or pass their user ID/@username, to /unapprove.")
        return

    removed = await crud.remove_approval(update.effective_chat.id, target.id)
    if removed:
        await msg.reply_html(f"[-] Unapproved {_mention(target)}. Standard chat rules now apply.")
    else:
        await msg.reply_html(f"{_mention(target)} is not approved in this chat.")


@group_only
async def approved_list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    approved_user_ids = await crud.list_approvals(update.effective_chat.id)
    if not approved_user_ids:
        await msg.reply_text("No approved users in this chat.")
        return

    lines = ["<b>:: APPROVED USERS ::</b>"]
    for uid in approved_user_ids:
        try:
            member = await update.effective_chat.get_member(uid)
            lines.append(f"» {_mention(member.user)} (<code>{uid}</code>)")
        except Exception:
            lines.append(f"» User ID <code>{uid}</code>")

    await msg.reply_html("\n".join(lines))


def register(application):
    application.add_handler(CommandHandler("approve", approve_cmd))
    application.add_handler(CommandHandler("unapprove", unapprove_cmd))
    application.add_handler(CommandHandler("approved", approved_list_cmd))
