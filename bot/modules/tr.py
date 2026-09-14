import io
import urllib.parse
import aiohttp
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

# Common 2 or 3 letter language codes
LANG_CODES = {
    "af", "sq", "am", "ar", "hy", "az", "eu", "be", "bn", "bs", "bg", "ca", "ceb", "ny", "zh", "zh-cn", "zh-tw",
    "co", "hr", "cs", "da", "nl", "en", "eo", "et", "tl", "fi", "fr", "fy", "gl", "ka", "de", "el", "gu", "ht",
    "ha", "haw", "he", "iw", "hi", "hmn", "hu", "is", "ig", "id", "ga", "it", "ja", "jw", "kn", "kk", "km", "ko",
    "ku", "ky", "lo", "la", "lv", "lt", "lb", "mk", "mg", "ms", "ml", "mt", "mi", "mr", "mn", "my", "ne", "no",
    "ps", "fa", "pl", "pt", "pa", "ro", "ru", "sm", "gd", "sr", "st", "sn", "sd", "si", "sk", "sl", "so", "es",
    "su", "sw", "sv", "tg", "ta", "te", "th", "tr", "uk", "ur", "uz", "vi", "cy", "xh", "yi", "yo", "zu"
}


async def tr_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    args = context.args

    text_to_translate = ""
    target_lang = "en"  # Default translation target is English

    if msg.reply_to_message and (msg.reply_to_message.text or msg.reply_to_message.caption):
        text_to_translate = msg.reply_to_message.text or msg.reply_to_message.caption
        if args:
            target_lang = args[0].lower()
    else:
        if not args:
            await msg.reply_html(
                "<b>Usage:</b> Reply to a message with <code>/tr</code> (defaults to English) or <code>/tr &lt;lang&gt;</code>.\n"
                "Or send <code>/tr &lt;lang&gt; &lt;text&gt;</code> / <code>/tr &lt;text&gt;</code>."
            )
            return

        if len(args) == 1:
            if args[0].lower() in LANG_CODES:
                await msg.reply_html("Please provide text to translate or reply to a message!")
                return
            else:
                target_lang = "en"
                text_to_translate = args[0]
        else:
            if args[0].lower() in LANG_CODES:
                target_lang = args[0].lower()
                text_to_translate = " ".join(args[1:])
            else:
                target_lang = "en"
                text_to_translate = " ".join(args)

    # Translate using deep_translator if installed, else fallback to gratis API endpoint
    try:
        from deep_translator import GoogleTranslator
        translated = GoogleTranslator(source="auto", target=target_lang).translate(text_to_translate)
        await msg.reply_html(
            f"<b>Translated to ({target_lang.upper()}):</b>\n\n<code>{translated}</code>"
        )
        return
    except Exception:
        pass

    # Fallback gratis Google Translate endpoint
    async with aiohttp.ClientSession() as session:
        try:
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_lang}&dt=t&q={urllib.parse.quote(text_to_translate)}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    translated = "".join([item[0] for item in data[0] if item[0]])
                    await msg.reply_html(
                        f"<b>Translated to ({target_lang.upper()}):</b>\n\n<code>{translated}</code>"
                    )
                    return
        except Exception as e:
            await msg.reply_html(f"Error translating text: <code>{e}</code>")


async def tts_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    args = context.args

    text = ""
    lang = "en"

    if msg.reply_to_message and (msg.reply_to_message.text or msg.reply_to_message.caption):
        text = msg.reply_to_message.text or msg.reply_to_message.caption
        if args:
            lang = args[0].lower()
    else:
        if not args:
            await msg.reply_html("<b>Usage:</b> <code>/tts [lang] &lt;text&gt;</code> or reply to a message with <code>/tts</code>.")
            return
        if len(args) > 1 and len(args[0]) <= 5:
            lang = args[0].lower()
            text = " ".join(args[1:])
        else:
            text = " ".join(args)

    # Try gTTS library
    try:
        from gtts import gTTS
        tts = gTTS(text=text, lang=lang)
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        fp.seek(0)
        fp.name = "tts.mp3"
        await msg.reply_audio(audio=fp, caption=f"🗣️ TTS ({lang})")
        return
    except Exception:
        pass

    # Fallback Google TTS URL
    async with aiohttp.ClientSession() as session:
        try:
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&q={urllib.parse.quote(text[:200])}&tl={lang}&client=tw-ob"
            async with session.get(tts_url) as resp:
                if resp.status == 200:
                    audio_data = await resp.read()
                    fp = io.BytesIO(audio_data)
                    fp.name = "tts.mp3"
                    await msg.reply_audio(audio=fp, caption=f"🗣️ TTS ({lang})")
                    return
                else:
                    await msg.reply_html("Failed to generate TTS audio.")
        except Exception as e:
            await msg.reply_html(f"Error producing TTS: <code>{e}</code>")


def register(application):
    application.add_handler(CommandHandler("tr", tr_cmd))
    application.add_handler(CommandHandler("translate", tr_cmd))
    application.add_handler(CommandHandler("tts", tts_cmd))
