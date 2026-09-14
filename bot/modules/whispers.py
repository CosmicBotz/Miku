import uuid
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from bot.database.crud import get_whisper, save_whisper


async def whisper_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    args = context.args

    if not args or len(args) < 2:
        await msg.reply_html(
            "<b>Usage:</b> <code>/whisper @username secret message</code>\n"
            "Or reply to a user with <code>/whisper secret message</code>."
        )
        return

    target_user = None
    target_id = None
    secret_text = ""

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target_user = msg.reply_to_message.from_user
        target_id = target_user.id
        secret_text = " ".join(args)
    else:
        target_mention = args[0]
        secret_text = " ".join(args[1:])
        if msg.entities:
            for ent in msg.entities:
                if ent.type == "text_mention" and ent.user:
                    target_user = ent.user
                    target_id = target_user.id
                    break

    if not target_id and target_user:
        target_id = target_user.id

    if not target_id:
        # Fallback: if user specified target handle or ID
        if args[0].isdigit():
            target_id = int(args[0])
        else:
            await msg.reply_html(
                "Could not resolve recipient! Please reply to the user's message with <code>/whisper message</code>."
            )
            return

    whisper_id = str(uuid.uuid4())[:8]
    await save_whisper(whisper_id, user.id, target_id, secret_text)

    target_name = target_user.first_name if target_user else f"User {target_id}"
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🤫 Show Secret Whisper", callback_data=f"wspr:{whisper_id}")]]
    )

    await msg.reply_html(
        f"A secret whisper has been sent for <b>{target_name}</b> by <b>{user.first_name}</b>!",
        reply_markup=keyboard,
    )


async def whisper_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    user = query.from_user

    whisper_id = data.split(":")[1]
    whisper_data = await get_whisper(whisper_id)

    if not whisper_data:
        await query.answer("This whisper has expired or does not exist!", show_alert=True)
        return

    sender_id = whisper_data.get("sender_id")
    target_id = whisper_data.get("target_id")
    secret_text = whisper_data.get("secret_text", "")

    if user.id in (sender_id, target_id):
        await query.answer(f"Secret Whisper:\n\n{secret_text}", show_alert=True)
    else:
        await query.answer("Shh! 🤫 This secret whisper is not for you!", show_alert=True)


def register(application):
    application.add_handler(CommandHandler("whisper", whisper_cmd))
    application.add_handler(CallbackQueryHandler(whisper_callback, pattern=r"^wspr:"))
