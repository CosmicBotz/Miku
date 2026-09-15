import datetime
import io
import textwrap
from PIL import Image, ImageDraw, ImageFont
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

ACCENT_COLORS = [
    (255, 117, 143),  # Pink
    (76, 201, 240),   # Cyan
    (247, 37, 133),   # Magenta
    (114, 9, 183),    # Purple
    (78, 168, 222),   # Blue
    (255, 183, 3),    # Gold
    (42, 157, 143),   # Teal
    (231, 111, 81),   # Coral
]


def _get_user_accent_color(user_id: int) -> tuple[int, int, int]:
    return ACCENT_COLORS[abs(user_id) % len(ACCENT_COLORS)]


def _make_circular_avatar(avatar_img: Image.Image, size: int = 70) -> Image.Image:
    avatar_img = avatar_img.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(avatar_img, (0, 0), mask)
    return output


def _generate_fallback_avatar(initial: str, bg_color: tuple[int, int, int], size: int = 70) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=bg_color)
    letter = initial.upper() if initial else "?"
    draw.text((size // 2 - 8, size // 2 - 12), letter, fill=(255, 255, 255))
    return img


def generate_quote_card(
    name: str,
    text: str,
    username: str | None = None,
    user_id: int = 0,
    avatar_bytes: bytes | None = None,
    time_str: str | None = None,
) -> bytes:
    """Generate a high-quality WebP quote sticker image using Pillow."""
    W, H = 512, 512
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    accent_color = _get_user_accent_color(user_id)

    # Calculate card bounds & wrapped text
    wrapped_lines = textwrap.wrap(text, width=32)
    max_lines = 10
    display_lines = wrapped_lines[:max_lines]
    if len(wrapped_lines) > max_lines:
        display_lines[-1] = display_lines[-1][:28] + "..."

    # Card background box
    draw.rounded_rectangle(
        [15, 30, 497, 482],
        radius=24,
        fill=(24, 24, 36, 245),
        outline=(55, 55, 75, 255),
        width=2,
    )

    # Avatar rendering
    if avatar_bytes:
        try:
            raw_avatar = Image.open(io.BytesIO(avatar_bytes))
            avatar_icon = _make_circular_avatar(raw_avatar, size=70)
        except Exception:
            avatar_icon = _generate_fallback_avatar(name[0], accent_color, size=70)
    else:
        avatar_icon = _generate_fallback_avatar(name[0], accent_color, size=70)

    img.paste(avatar_icon, (40, 55), avatar_icon)

    # Name and Handle
    draw.text((125, 60), name[:24], fill=accent_color)
    if username:
        draw.text((125, 88), f"@{username}", fill=(140, 145, 165))
    else:
        draw.text((125, 88), "Telegram Member", fill=(140, 145, 165))

    # Divider line
    draw.line([(40, 140), (472, 140)], fill=(45, 45, 65, 255), width=1)

    # Message Text Lines
    y_offset = 160
    for line in display_lines:
        draw.text((45, y_offset), line, fill=(240, 240, 250))
        y_offset += 24

    # Timestamp
    if not time_str:
        time_str = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M")
    draw.text((430, 448), time_str, fill=(110, 115, 140))

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=95)
    return buf.getvalue()


async def quotely_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a custom quote sticker from a replied message."""
    msg = update.effective_message
    if not msg or not msg.reply_to_message:
        await msg.reply_html("<b>Usage:</b> Reply to a message with <code>/q</code> or <code>/quote</code> to generate a quote sticker.")
        return

    reply = msg.reply_to_message
    text_to_quote = reply.text or reply.caption
    if not text_to_quote:
        await msg.reply_html("[!] The replied message contains no text to quote.")
        return

    sender = reply.from_user
    if sender:
        name = f"{sender.first_name} {sender.last_name}" if sender.last_name else sender.first_name
        username = sender.username
        user_id = sender.id
    elif reply.sender_chat:
        name = reply.sender_chat.title or "Channel"
        username = reply.sender_chat.username
        user_id = reply.sender_chat.id
    else:
        name = "Anonymous"
        username = None
        user_id = 0

    # Fetch avatar if available
    avatar_bytes = None
    if sender:
        try:
            photos = await context.bot.get_user_profile_photos(user_id=sender.id, limit=1)
            if photos and photos.photos:
                file_id = photos.photos[0][-1].file_id
                file_obj = await context.bot.get_file(file_id)
                avatar_buf = io.BytesIO()
                await file_obj.download_to_memory(avatar_buf)
                avatar_bytes = avatar_buf.getvalue()
        except Exception:
            avatar_bytes = None

    time_str = reply.date.strftime("%H:%M") if reply.date else None

    try:
        sticker_data = generate_quote_card(
            name=name,
            text=text_to_quote,
            username=username,
            user_id=user_id,
            avatar_bytes=avatar_bytes,
            time_str=time_str,
        )

        await msg.reply_sticker(sticker=io.BytesIO(sticker_data))
    except Exception as e:
        await msg.reply_html(f"[!] Error generating quote sticker: <code>{e}</code>")


def register(application):
    application.add_handler(CommandHandler(["q", "quote", "quotely"], quotely_cmd))
