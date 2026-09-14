import re

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..database import crud
from ..utils.decorators import admin_only, group_only


def _extract_filter_data(message, args):
    reply = message.reply_to_message
    target_msg = reply if reply else message

    reply_text = ""
    media_type = None
    file_id = None

    if target_msg.photo:
        media_type = "photo"
        file_id = target_msg.photo[-1].file_id
        reply_text = target_msg.caption or ""
    elif target_msg.video:
        media_type = "video"
        file_id = target_msg.video.file_id
        reply_text = target_msg.caption or ""
    elif target_msg.document:
        media_type = "document"
        file_id = target_msg.document.file_id
        reply_text = target_msg.caption or ""
    elif target_msg.sticker:
        media_type = "sticker"
        file_id = target_msg.sticker.file_id
        reply_text = ""
    elif target_msg.audio:
        media_type = "audio"
        file_id = target_msg.audio.file_id
        reply_text = target_msg.caption or ""
    elif target_msg.voice:
        media_type = "voice"
        file_id = target_msg.voice.file_id
        reply_text = target_msg.caption or ""
    else:
        if reply:
            reply_text = reply.text or ""
        elif len(args) > 1:
            reply_text = " ".join(args[1:])

    return reply_text, media_type, file_id


async def _reply_with_filter(message, filter_doc):
    media_type = filter_doc.get("media_type")
    file_id = filter_doc.get("file_id")
    reply_text = filter_doc.get("reply_text", "")

    try:
        if media_type == "photo":
            await message.reply_photo(file_id, caption=reply_text)
        elif media_type == "video":
            await message.reply_video(file_id, caption=reply_text)
        elif media_type == "document":
            await message.reply_document(file_id, caption=reply_text)
        elif media_type == "sticker":
            await message.reply_sticker(file_id)
        elif media_type == "audio":
            await message.reply_audio(file_id, caption=reply_text)
        elif media_type == "voice":
            await message.reply_voice(file_id, caption=reply_text)
        else:
            if reply_text:
                await message.reply_text(reply_text)
    except Exception:
        pass


@group_only
@admin_only
async def add_filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /filter <keyword> <reply message|reply to message>")
        return

    keyword = context.args[0].lower()
    reply_text, media_type, file_id = _extract_filter_data(msg, context.args)

    if not reply_text and not file_id:
        await msg.reply_text("Please provide reply content or reply to a message.")
        return

    await crud.add_filter(
        chat_id=update.effective_chat.id,
        keyword=keyword,
        reply_text=reply_text,
        media_type=media_type,
        file_id=file_id,
    )
    await msg.reply_text(f"[+] Added filter for '<code>{keyword}</code>'.", parse_mode="HTML")


@group_only
async def list_filters_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    filter_list = await crud.list_filters(update.effective_chat.id)
    if not filter_list:
        await msg.reply_text("No active filters in this chat.")
        return

    keywords = [f"» <code>{f['keyword']}</code>" for f in filter_list]
    await msg.reply_html("<b>:: ACTIVE FILTERS ::</b>\n" + "\n".join(keywords))


@group_only
@admin_only
async def stop_filter_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /stop <keyword>")
        return

    keyword = context.args[0].lower()
    deleted = await crud.delete_filter(update.effective_chat.id, keyword)
    if deleted:
        await msg.reply_text(f"[-] Stopped filter for '<code>{keyword}</code>'.", parse_mode="HTML")
    else:
        await msg.reply_text("That filter doesn't exist.")


@group_only
@admin_only
async def stopall_filters_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    count = await crud.delete_all_filters(update.effective_chat.id)
    await msg.reply_text(f"[-] Stopped all {count} filters in this chat.")


async def filter_check_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    chat = update.effective_chat
    if not msg or not msg.text or chat.type not in ("group", "supergroup"):
        return

    chat_filters = await crud.list_filters(chat.id)
    if not chat_filters:
        return

    text_lower = msg.text.lower()
    for f in chat_filters:
        kw = f["keyword"].lower()
        pattern = r"\b" + re.escape(kw) + r"\b"
        if re.search(pattern, text_lower):
            await _reply_with_filter(msg, f)
            break


def register(application):
    application.add_handler(CommandHandler("filter", add_filter_cmd))
    application.add_handler(CommandHandler("filters", list_filters_cmd))
    application.add_handler(CommandHandler("stop", stop_filter_cmd))
    application.add_handler(CommandHandler("stopall", stopall_filters_cmd))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS & ~filters.COMMAND, filter_check_handler),
        group=3,
    )
