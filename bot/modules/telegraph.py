"""Upload replied media to telegra.ph and return a permanent link."""
import io
import json

import aiohttp
from PIL import Image
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..utils.telethon_client import get_telethon_client

TELEGRAPH_UPLOAD_URL = "https://telegra.ph/upload"

# telegra.ph's upload endpoint only accepts these - anything else (webp
# stickers, tgs animations, etc.) gets converted to PNG before upload.
_TELEGRAPH_OK_MIME = {"image/jpeg", "image/png", "image/gif", "video/mp4"}


def _guess_name_and_mime(reply) -> tuple[str, str]:
    """Best-effort filename + mime type based on the message's media kind."""
    if reply.photo:
        return "photo.jpg", "image/jpeg"
    if reply.sticker:
        st = reply.sticker
        if st.is_animated:
            return "sticker.tgs", "application/octet-stream"
        if st.is_video:
            return "sticker.webm", "video/webm"
        return "sticker.webp", "image/webp"
    if reply.animation:
        return "animation.mp4", reply.animation.mime_type or "video/mp4"
    if reply.video:
        return "video.mp4", reply.video.mime_type or "video/mp4"
    if reply.video_note:
        return "video_note.mp4", "video/mp4"
    if reply.audio:
        return reply.audio.file_name or "audio.mp3", reply.audio.mime_type or "audio/mpeg"
    if reply.voice:
        return "voice.ogg", "audio/ogg"
    if reply.document:
        return reply.document.file_name or "document", reply.document.mime_type or "application/octet-stream"
    return "upload.bin", "application/octet-stream"


def _get_media(reply):
    return (
        (reply.photo[-1] if reply.photo else None)
        or reply.video
        or reply.animation
        or reply.document
        or reply.sticker
        or reply.audio
        or reply.voice
        or reply.video_note
    )


async def _download_via_telethon(chat_id: int, message_id: int) -> "bytes | None":
    """Try the bot's own Telethon client first - handles files >20MB.
    Returns None (never raises) so the caller can fall back to the Bot API."""
    client = get_telethon_client()
    if client is None or not client.is_connected():
        return None
    try:
        tmsg = await client.get_messages(chat_id, ids=message_id)
        if not tmsg or not tmsg.media:
            return None
        return await client.download_media(tmsg, file=bytes)
    except Exception:
        return None


async def _download_via_bot_api(context: ContextTypes.DEFAULT_TYPE, file_id: str) -> bytes:
    """Fallback: plain Bot API download. Telegram caps this at 20MB."""
    tg_file = await context.bot.get_file(file_id)
    buf = io.BytesIO()
    await tg_file.download_to_memory(buf)
    return buf.getvalue()


async def _upload_to_telegraph(file_bytes: bytes, filename: str, mime_type: str) -> str:
    if mime_type not in _TELEGRAPH_OK_MIME:
        try:
            im = Image.open(io.BytesIO(file_bytes)).convert("RGBA")
            out = io.BytesIO()
            im.save(out, format="PNG")
            file_bytes = out.getvalue()
            filename, mime_type = "upload.png", "image/png"
        except Exception:
            pass  # not something Pillow can convert - try uploading as-is

    form = aiohttp.FormData()
    form.add_field("file", file_bytes, filename=filename, content_type=mime_type)
    async with aiohttp.ClientSession() as session:
        async with session.post(TELEGRAPH_UPLOAD_URL, data=form) as resp:
            status = resp.status
            raw = await resp.text()

    try:
        data = json.loads(raw)
    except ValueError:
        raise RuntimeError(f"telegra.ph returned a non-JSON response (HTTP {status}): {raw[:200]!r}")

    # Expected success shape: [{"src": "/file/xxxx.jpg"}]. telegra.ph can also
    # reply with {"error": "..."} , or - on things like rate limiting - a bare
    # string inside the list, e.g. ["Too Many Requests"]. Validate the shape
    # instead of indexing straight into it, so any of those surface as a
    # readable message instead of "string indices must be integers".
    if isinstance(data, dict):
        raise RuntimeError(data.get("error") or f"Unexpected response (HTTP {status}): {raw[:200]!r}")

    if not isinstance(data, list) or not data or not isinstance(data[0], dict) or "src" not in data[0]:
        detail = data[0] if isinstance(data, list) and data else raw[:200]
        raise RuntimeError(f"telegra.ph rejected the upload (HTTP {status}): {detail!r}")

    return "https://telegra.ph" + data[0]["src"]


async def telegraph_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    reply = msg.reply_to_message
    if not reply:
        await msg.reply_text("Reply to a photo, video, document, or sticker to get a permanent telegra.ph link.")
        return

    media = _get_media(reply)
    if not media:
        await msg.reply_text("That message doesn't contain any media I can upload.")
        return

    status = await msg.reply_text("Uploading to telegra.ph, please wait...")
    filename, mime_type = _guess_name_and_mime(reply)

    try:
        file_bytes = await _download_via_telethon(reply.chat_id, reply.message_id)
        if file_bytes is None:
            file_bytes = await _download_via_bot_api(context, media.file_id)

        link = await _upload_to_telegraph(file_bytes, filename, mime_type)
        await status.edit_text(f"Uploaded! Permanent link:\n{link}", disable_web_page_preview=False)
    except Exception as e:
        err = str(e).lower()
        if "too big" in err or "too large" in err:
            await status.edit_text(
                "Failed to upload: this file is too big for the Bot API, and the bot's "
                "Telethon client (api_id/api_hash) either isn't configured or couldn't "
                "fetch it another way."
            )
        else:
            await status.edit_text(f"Failed to upload to telegra.ph: {e}")


def register(application):
    application.add_handler(CommandHandler(["tgm", "tmg", "telegraph"], telegraph_cmd))