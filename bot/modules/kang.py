import io
from PIL import Image
from telegram import InputSticker, Update
from telegram.ext import CommandHandler, ContextTypes


async def kang_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    bot = context.bot
    args = context.args

    if not msg.reply_to_message:
        await msg.reply_html("Reply to a sticker or photo with <code>/kang [emoji]</code> to steal it!")
        return

    reply = msg.reply_to_message
    sticker_emoji = args[0] if args else "✨"

    file_obj = None
    is_animated = False
    is_video = False

    if reply.sticker:
        file_obj = await reply.sticker.get_file()
        sticker_emoji = reply.sticker.emoji or sticker_emoji
        is_animated = reply.sticker.is_animated
        is_video = reply.sticker.is_video
    elif reply.photo:
        file_obj = await reply.photo[-1].get_file()
    elif reply.document and reply.document.mime_type and "image" in reply.document.mime_type:
        file_obj = await reply.document.get_file()
    else:
        await msg.reply_html("Please reply to a valid sticker or image.")
        return

    # Download file content
    image_bytes = await file_obj.download_as_bytearray()

    # Process photo to 512x512 PNG/WEBP
    if not reply.sticker or (reply.sticker and not is_animated and not is_video):
        try:
            im = Image.open(io.BytesIO(image_bytes))
            im.thumbnail((512, 512))
            out = io.BytesIO()
            im.save(out, format="PNG")
            image_bytes = out.getvalue()
        except Exception as e:
            await msg.reply_html(f"Failed to process sticker image: <code>{e}</code>")
            return

    bot_user = await bot.get_me()
    pack_name = f"frieren_{user.id}_by_{bot_user.username}"
    pack_title = f"@{user.first_name}'s Kang Pack by @{bot_user.username}"

    input_sticker = InputSticker(
        sticker=io.BytesIO(image_bytes),
        emoji_list=[sticker_emoji],
        format="static" if not (is_animated or is_video) else ("animated" if is_animated else "video"),
    )

    try:
        # Try adding sticker to existing set
        await bot.add_sticker_to_set(
            user_id=user.id,
            name=pack_name,
            sticker=input_sticker,
        )
        await msg.reply_html(
            f"Sticker kanged into your pack!\n"
            f"<b>Pack Link:</b> <a href=\"https://t.me/addstickers/{pack_name}\">View Sticker Pack</a>"
        )
    except Exception as e:
        err_msg = str(e).lower()
        if "stickerset_invalid" in err_msg or "does not exist" in err_msg or "invalid sticker set" in err_msg:
            try:
                # Create new sticker set
                await bot.create_new_sticker_set(
                    user_id=user.id,
                    name=pack_name,
                    title=pack_title,
                    stickers=[input_sticker],
                    sticker_format="static" if not (is_animated or is_video) else ("animated" if is_animated else "video"),
                )
                await msg.reply_html(
                    f"Created your new sticker pack and kanged sticker!\n"
                    f"<b>Pack Link:</b> <a href=\"https://t.me/addstickers/{pack_name}\">View Sticker Pack</a>"
                )
            except Exception as create_err:
                await msg.reply_html(f"Could not create sticker pack: <code>{create_err}</code>")
        else:
            await msg.reply_html(f"Error kanging sticker: <code>{e}</code>")


def register(application):
    application.add_handler(CommandHandler("kang", kang_cmd))
    application.add_handler(CommandHandler("pkang", kang_cmd))
