from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from ..database import crud
from ..utils.decorators import admin_only, group_only


def _extract_media_or_text(message, args):
    reply = message.reply_to_message
    target_msg = reply if reply else message

    content = ""
    media_type = None
    file_id = None

    if target_msg.photo:
        media_type = "photo"
        file_id = target_msg.photo[-1].file_id
        content = target_msg.caption or ""
    elif target_msg.video:
        media_type = "video"
        file_id = target_msg.video.file_id
        content = target_msg.caption or ""
    elif target_msg.document:
        media_type = "document"
        file_id = target_msg.document.file_id
        content = target_msg.caption or ""
    elif target_msg.sticker:
        media_type = "sticker"
        file_id = target_msg.sticker.file_id
        content = ""
    elif target_msg.audio:
        media_type = "audio"
        file_id = target_msg.audio.file_id
        content = target_msg.caption or ""
    elif target_msg.voice:
        media_type = "voice"
        file_id = target_msg.voice.file_id
        content = target_msg.caption or ""
    else:
        if reply:
            content = reply.text or ""
        elif len(args) > 1:
            content = " ".join(args[1:])

    return content, media_type, file_id


async def _reply_with_note(message, note):
    media_type = note.get("media_type")
    file_id = note.get("file_id")
    content = note.get("content", "")

    try:
        if media_type == "photo":
            await message.reply_photo(file_id, caption=content)
        elif media_type == "video":
            await message.reply_video(file_id, caption=content)
        elif media_type == "document":
            await message.reply_document(file_id, caption=content)
        elif media_type == "sticker":
            await message.reply_sticker(file_id)
        elif media_type == "audio":
            await message.reply_audio(file_id, caption=content)
        elif media_type == "voice":
            await message.reply_voice(file_id, caption=content)
        else:
            if content:
                await message.reply_text(content)
    except Exception as e:
        await message.reply_text(f"Failed to send note: {e}")


@group_only
@admin_only
async def save_note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /save <note_name> <content|reply to message>")
        return

    note_name = context.args[0].lstrip("#")
    content, media_type, file_id = _extract_media_or_text(msg, context.args)

    if not content and not file_id:
        await msg.reply_text("Please provide content or reply to a message to save as note.")
        return

    await crud.save_note(
        chat_id=update.effective_chat.id,
        note_name=note_name,
        content=content,
        media_type=media_type,
        file_id=file_id,
    )
    await msg.reply_text(f"[+] Saved note #{note_name}.")


@group_only
async def get_note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /get <note_name>")
        return

    note_name = context.args[0].lstrip("#")
    note = await crud.get_note(update.effective_chat.id, note_name)
    if not note:
        await msg.reply_text("Note not found.")
        return

    await _reply_with_note(msg, note)


@group_only
async def list_notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    notes = await crud.list_notes(update.effective_chat.id)
    if not notes:
        await msg.reply_text("No notes saved in this chat.")
        return

    note_list = [f"» <code>#{n.get('display_name', n['note_name'])}</code>" for n in notes]
    text = "<b>:: NOTES IN CHAT ::</b>\n" + "\n".join(note_list)
    await msg.reply_html(text)


@group_only
@admin_only
async def clear_note_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args:
        await msg.reply_text("Usage: /clear <note_name>")
        return

    note_name = context.args[0].lstrip("#")
    deleted = await crud.delete_note(update.effective_chat.id, note_name)
    if deleted:
        await msg.reply_text(f"[-] Deleted note #{note_name}.")
    else:
        await msg.reply_text("Note not found.")


@group_only
@admin_only
async def clearall_notes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    count = await crud.delete_all_notes(update.effective_chat.id)
    await msg.reply_text(f"[-] Cleared all {count} notes from this chat.")


async def hashtag_note_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not msg or not msg.text:
        return

    words = msg.text.split()
    for word in words:
        if word.startswith("#") and len(word) > 1:
            note_name = word[1:]
            note = await crud.get_note(update.effective_chat.id, note_name)
            if note:
                await _reply_with_note(msg, note)
                break


def register(application):
    application.add_handler(CommandHandler("save", save_note_cmd))
    application.add_handler(CommandHandler("get", get_note_cmd))
    application.add_handler(CommandHandler("notes", list_notes_cmd))
    application.add_handler(CommandHandler("clear", clear_note_cmd))
    application.add_handler(CommandHandler("clearall", clearall_notes_cmd))
    application.add_handler(
        MessageHandler(filters.TEXT & filters.ChatType.GROUPS, hashtag_note_trigger),
        group=5,
    )
