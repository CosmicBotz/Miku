import uuid
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..database import crud
from ..utils.decorators import admin_only, group_only
from ..utils.extraction import get_reason, get_target_user


def _mention(user) -> str:
    return f'<a href="tg://user?id={user.id}">{user.first_name}</a>'


async def newfed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /newfed <federation_name>")
        return

    fed_name = " ".join(context.args)
    fed_id = str(uuid.uuid4())[:8]
    created = await crud.create_fed(fed_id, fed_name, update.effective_user.id)

    if created:
        await msg.reply_html(
            f"[+] Created new federation <b>{fed_name}</b>!\n"
            f"» <b>Fed ID:</b> <code>{fed_id}</code>\n"
            f"Use <code>/joinfed {fed_id}</code> in your group to join it."
        )
    else:
        await msg.reply_text("Failed to create federation. Try again.")


async def delfed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /delfed <fed_id>")
        return

    fed_id = context.args[0]
    fed = await crud.get_fed(fed_id)

    if not fed:
        await msg.reply_text("Federation not found.")
        return

    if fed["owner_id"] != update.effective_user.id:
        await msg.reply_text("[!] Only the federation owner can delete this federation.")
        return

    await crud.delete_fed(fed_id)
    await msg.reply_html(f"[-] Deleted federation <b>{fed['fed_name']}</b> (<code>{fed_id}</code>).")


@group_only
@admin_only
async def joinfed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /joinfed <fed_id>")
        return

    fed_id = context.args[0]
    fed = await crud.get_fed(fed_id)
    if not fed:
        await msg.reply_text("Invalid Fed ID. Federation not found.")
        return

    joined = await crud.join_fed(update.effective_chat.id, fed_id)
    if joined:
        await msg.reply_html(f"[+] Joined chat to federation <b>{fed['fed_name']}</b>.")
    else:
        await msg.reply_text("Failed to join federation.")


@group_only
@admin_only
async def leavefed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    left = await crud.leave_fed(update.effective_chat.id)
    if left:
        await msg.reply_text("[-] Left federation.")
    else:
        await msg.reply_text("This chat is not in any federation.")


async def fban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Usage: /fban <user> [reason]")
        return

    fed = await crud.get_fed_by_chat(chat.id) if chat.type in ("group", "supergroup") else None
    if not fed:
        await msg.reply_text("This chat is not connected to a federation.")
        return

    if user.id != fed["owner_id"] and user.id not in fed.get("admins", []):
        await msg.reply_text("[!] You are not an admin of this chat's federation.")
        return

    reason = get_reason(context, offset=1 if msg.reply_to_message else 2)
    banned = await crud.fban_user(fed["_id"], target.id, reason=reason, admin_id=user.id)

    if not banned:
        await msg.reply_html(f"{_mention(target)} is already fbanned in <b>{fed['fed_name']}</b>.")
        return

    await msg.reply_html(
        f"<b>[FBAN LOG]</b>\n"
        f"» <b>User:</b> {_mention(target)} (<code>{target.id}</code>)\n"
        f"» <b>Federation:</b> {fed['fed_name']}\n"
        + (f"» <b>Reason:</b> {reason}" if reason else "")
    )

    fed_chats = await crud.list_fed_chats(fed["_id"])
    for cid in fed_chats:
        try:
            await context.bot.ban_chat_member(cid, target.id)
        except Exception:
            pass


async def unfban_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    chat = update.effective_chat

    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Usage: /unfban <user>")
        return

    fed = await crud.get_fed_by_chat(chat.id) if chat.type in ("group", "supergroup") else None
    if not fed:
        await msg.reply_text("This chat is not connected to a federation.")
        return

    if user.id != fed["owner_id"] and user.id not in fed.get("admins", []):
        await msg.reply_text("[!] You are not an admin of this chat's federation.")
        return

    removed = await crud.unfban_user(fed["_id"], target.id)
    if removed:
        await msg.reply_html(f"[UNFBAN] Un-fbanned {_mention(target)} from <b>{fed['fed_name']}</b>.")
    else:
        await msg.reply_html(f"{_mention(target)} is not fbanned in <b>{fed['fed_name']}</b>.")


async def fedinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    fed_id = context.args[0] if context.args else None

    if not fed_id and update.effective_chat.type in ("group", "supergroup"):
        fed = await crud.get_fed_by_chat(update.effective_chat.id)
    elif fed_id:
        fed = await crud.get_fed(fed_id)
    else:
        fed = None

    if not fed:
        await msg.reply_text("Federation not found. Specify a fed_id or use in a federation-connected chat.")
        return

    chats = await crud.list_fed_chats(fed["_id"])
    banned_count = len(fed.get("banned_users", []))
    admin_count = len(fed.get("admins", []))

    lines = [
        f"<b>:: FEDERATION INFO — {fed['fed_name']} ::</b>",
        f"» <b>Fed ID:</b> <code>{fed['_id']}</code>",
        f"» <b>Owner ID:</b> <code>{fed['owner_id']}</code>",
        f"» <b>Admins Count:</b> {admin_count}",
        f"» <b>Fbanned Users Count:</b> {banned_count}",
        f"» <b>Joined Chats:</b> {len(chats)}",
    ]
    await msg.reply_html("\n".join(lines))


async def fedadmins_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    fed_id = context.args[0] if context.args else None

    if not fed_id and update.effective_chat.type in ("group", "supergroup"):
        fed = await crud.get_fed_by_chat(update.effective_chat.id)
    elif fed_id:
        fed = await crud.get_fed(fed_id)
    else:
        fed = None

    if not fed:
        await msg.reply_text("Federation not found.")
        return

    admins = fed.get("admins", [])
    lines = [f"» <code>{aid}</code>" + (" (Owner)" if aid == fed["owner_id"] else "") for aid in admins]
    await msg.reply_html(f"<b>Admins of {fed['fed_name']}:</b>\n" + "\n".join(lines))


async def fedpromote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Usage: /fedpromote <user>")
        return

    fed = await crud.get_fed_by_chat(update.effective_chat.id)
    if not fed:
        await msg.reply_text("This chat is not connected to a federation.")
        return

    if update.effective_user.id != fed["owner_id"]:
        await msg.reply_text("[!] Only the federation owner can promote fed admins.")
        return

    promoted = await crud.promote_fed_admin(fed["_id"], target.id)
    if promoted:
        await msg.reply_html(f"[+] Promoted {_mention(target)} to fed admin in <b>{fed['fed_name']}</b>.")
    else:
        await msg.reply_html(f"{_mention(target)} is already a fed admin.")


async def feddemote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    target = await get_target_user(update, context)
    if not target:
        await msg.reply_text("Usage: /feddemote <user>")
        return

    fed = await crud.get_fed_by_chat(update.effective_chat.id)
    if not fed:
        await msg.reply_text("This chat is not connected to a federation.")
        return

    if update.effective_user.id != fed["owner_id"]:
        await msg.reply_text("[!] Only the federation owner can demote fed admins.")
        return

    demoted = await crud.demote_fed_admin(fed["_id"], target.id)
    if demoted:
        await msg.reply_html(f"[-] Demoted {_mention(target)} from fed admin in <b>{fed['fed_name']}</b>.")
    else:
        await msg.reply_html(f"{_mention(target)} is not a fed admin.")


async def check_fed_ban_on_join(update: Update, context: ContextTypes.DEFAULT_TYPE, user) -> bool:
    chat = update.effective_chat
    fed = await crud.get_fed_by_chat(chat.id)
    if not fed:
        return False

    if await crud.is_fbanned(fed["_id"], user.id):
        try:
            await context.bot.ban_chat_member(chat.id, user.id)
            await update.effective_message.reply_html(
                f"[FBAN] <a href=\"tg://user?id={user.id}\">{user.first_name}</a> is fbanned in <b>{fed['fed_name']}</b> and has been automatically banned."
            )
            return True
        except Exception:
            pass
    return False


def register(application):
    application.add_handler(CommandHandler("newfed", newfed_cmd))
    application.add_handler(CommandHandler("delfed", delfed_cmd))
    application.add_handler(CommandHandler("joinfed", joinfed_cmd))
    application.add_handler(CommandHandler("leavefed", leavefed_cmd))
    application.add_handler(CommandHandler("fban", fban_cmd))
    application.add_handler(CommandHandler("unfban", unfban_cmd))
    application.add_handler(CommandHandler("fedinfo", fedinfo_cmd))
    application.add_handler(CommandHandler("fedadmins", fedadmins_cmd))
    application.add_handler(CommandHandler("fedpromote", fedpromote_cmd))
    application.add_handler(CommandHandler("feddemote", feddemote_cmd))
