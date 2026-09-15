import datetime
import io
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

# Render everything at this multiple of the final 512px card width, then
# downscale with LANCZOS at the end. PIL's ImageDraw shapes (circular
# avatars, rounded corners) aren't anti-aliased on their own and come out
# jagged at 1x - this is the same "scale" trick LyoSU/quote-api uses
# (it renders server-side at scale: 2) to get smooth edges cheaply.
SCALE = 2

# Matches LyoSU/quote-api's default quote card background (#1b1429) - the
# color people actually recognize from real quote-bot stickers.
BG_COLOR = (27, 20, 41, 245)
BORDER_COLOR = (60, 50, 82, 255)


def _get_user_accent_color(user_id: int) -> tuple[int, int, int]:
    return ACCENT_COLORS[abs(user_id) % len(ACCENT_COLORS)]


def _make_circular_avatar(avatar_img: Image.Image, size: int) -> Image.Image:
    avatar_img = avatar_img.resize((size, size), Image.Resampling.LANCZOS).convert("RGBA")
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0, size, size), fill=255)
    output = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    output.paste(avatar_img, (0, 0), mask)
    return output


def _generate_fallback_avatar(initial: str, bg_color: tuple[int, int, int], size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=bg_color)
    letter = (initial or "?").upper()
    font = ImageFont.load_default(size=int(size * 0.5))
    bbox = draw.textbbox((0, 0), letter, font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text(((size - w) / 2 - bbox[0], (size - h) / 2 - bbox[1]), letter, font=font, fill=(255, 255, 255))
    return img


def _wrap_text(text: str, font: "ImageFont.FreeTypeFont", max_width: int) -> list[str]:
    """Word-wrap by measuring actual rendered pixel width for this font,
    instead of guessing a fixed character count."""
    words = text.split()
    if not words:
        return [""]
    lines = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if font.getlength(candidate) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def generate_quote_card(
    name: str,
    text: str,
    username: str | None = None,
    user_id: int = 0,
    avatar_bytes: bytes | None = None,
    time_str: str | None = None,
    reply_name: str | None = None,
    reply_text: str | None = None,
) -> bytes:
    """Generate a WebP quote sticker sized to its content - a rectangle like
    a real chat-bubble screenshot.

    reply_name/reply_text (optional): when the quoted message was itself a
    reply, a small "replying to X" block is drawn above the main text -
    mirrors Telegram's own in-bubble reply preview and LyoSU/quote-api's
    replyMessage feature, so the card reads like an actual chat screenshot
    rather than an isolated line of text.
    """
    # ---- logical (1x) layout, in terms of the final 512px-wide sticker ----
    W = 512
    CARD_MARGIN = 15
    TOP, BOTTOM = 30, 30
    AVATAR_SIZE = 76
    TEXT_LEFT = 45
    TEXT_RIGHT_MARGIN = 40
    HEADER_H = 116
    FOOTER_H = 50
    MIN_H, MAX_H = 220, 512

    accent_color = _get_user_accent_color(user_id)

    name_font = ImageFont.load_default(size=26 * SCALE)
    handle_font = ImageFont.load_default(size=18 * SCALE)
    body_font = ImageFont.load_default(size=23 * SCALE)
    time_font = ImageFont.load_default(size=16 * SCALE)
    reply_name_font = ImageFont.load_default(size=17 * SCALE)
    reply_text_font = ImageFont.load_default(size=16 * SCALE)

    text_max_width = (W - TEXT_LEFT - TEXT_RIGHT_MARGIN) * SCALE
    wrapped_lines = _wrap_text(text, body_font, text_max_width)
    max_lines = 10
    display_lines = wrapped_lines[:max_lines]
    if len(wrapped_lines) > max_lines:
        display_lines[-1] = display_lines[-1][:40] + "..."

    ascent, descent = body_font.getmetrics()
    line_h = int((ascent + descent) * 1.35)  # already SCALE-sized

    reply_block_h = 0
    reply_preview_line = None
    if reply_name:
        reply_max_width = text_max_width - 12 * SCALE
        preview_lines = _wrap_text((reply_text or "").strip() or "Media", reply_text_font, reply_max_width)
        reply_preview_line = preview_lines[0]
        if len(preview_lines) > 1:
            reply_preview_line = reply_preview_line.rstrip() + "…"
        reply_block_h = 58 * SCALE

    content_h_scaled = (
        TOP * SCALE + HEADER_H * SCALE + reply_block_h
        + len(display_lines) * line_h + FOOTER_H * SCALE + BOTTOM * SCALE
    )
    H = max(MIN_H, min(MAX_H, round(content_h_scaled / SCALE)))

    RW, RH = W * SCALE, H * SCALE
    img = Image.new("RGBA", (RW, RH), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    def s(v):
        return v * SCALE

    # Card background box
    draw.rounded_rectangle(
        [s(CARD_MARGIN), s(TOP), RW - s(CARD_MARGIN), RH - s(BOTTOM)],
        radius=s(24),
        fill=BG_COLOR,
        outline=BORDER_COLOR,
        width=s(2),
    )

    # Avatar rendering
    avatar_size_px = s(AVATAR_SIZE)
    if avatar_bytes:
        try:
            raw_avatar = Image.open(io.BytesIO(avatar_bytes))
            avatar_icon = _make_circular_avatar(raw_avatar, size=avatar_size_px)
        except Exception:
            avatar_icon = _generate_fallback_avatar(name[0], accent_color, size=avatar_size_px)
    else:
        avatar_icon = _generate_fallback_avatar(name[0], accent_color, size=avatar_size_px)

    img.paste(avatar_icon, (s(TEXT_LEFT - 5), s(TOP + 22)), avatar_icon)

    # Name and Handle
    text_x = s(TEXT_LEFT - 5 + AVATAR_SIZE + 15)
    draw.text((text_x, s(TOP + 22)), name[:24], font=name_font, fill=accent_color)
    draw.text(
        (text_x, s(TOP + 54)),
        f"@{username}" if username else "Telegram Member",
        font=handle_font,
        fill=(150, 155, 175),
    )

    # Divider line
    divider_y = s(TOP + HEADER_H)
    draw.line([(s(TEXT_LEFT - 5), divider_y), (RW - s(TEXT_LEFT - 5), divider_y)], fill=(50, 50, 70, 255), width=s(1))

    y = divider_y + s(18)

    # Nested reply preview (accent bar + name + one truncated line)
    if reply_preview_line:
        bar_x = s(TEXT_LEFT)
        draw.rectangle([bar_x, y, bar_x + s(3), y + reply_block_h - s(10)], fill=accent_color)
        draw.text((bar_x + s(12), y), (reply_name or "")[:24], font=reply_name_font, fill=accent_color)
        draw.text((bar_x + s(12), y + s(22)), reply_preview_line, font=reply_text_font, fill=(150, 155, 175))
        y += reply_block_h

    # Message Text Lines
    for line in display_lines:
        draw.text((s(TEXT_LEFT), y), line, font=body_font, fill=(240, 240, 250))
        y += line_h

    # Timestamp
    if not time_str:
        time_str = datetime.datetime.now(datetime.timezone.utc).strftime("%H:%M")
    time_w = time_font.getlength(time_str)
    draw.text((RW - s(CARD_MARGIN + 25) - time_w, RH - s(BOTTOM + 32)), time_str, font=time_font, fill=(120, 125, 150))

    # Downscale from the supersampled render - this is what actually
    # produces the smooth/anti-aliased edges on circles and corners.
    img = img.resize((W, H), Image.Resampling.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=95)
    return buf.getvalue()


async def quotely_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate a custom quote sticker from a replied message."""
    msg = update.effective_message
    if not msg or not msg.reply_to_message:
        await msg.reply_html(
            "<b>Usage:</b> Reply to a message with <code>/q</code> or <code>/quote</code> to generate a quote sticker.",
            allow_sending_without_reply=True,
        )
        return

    reply = msg.reply_to_message
    text_to_quote = reply.text or reply.caption
    if not text_to_quote:
        await msg.reply_html("[!] The replied message contains no text to quote.", allow_sending_without_reply=True)
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

    # If the quoted message was itself a reply, show who/what it replied to
    # (mirrors Telegram's own in-bubble reply preview).
    reply_name = None
    reply_text_preview = None
    nested = reply.reply_to_message
    if nested:
        if nested.from_user:
            reply_name = nested.from_user.first_name
        elif nested.sender_chat:
            reply_name = nested.sender_chat.title or "Channel"
        else:
            reply_name = "Anonymous"
        reply_text_preview = nested.text or nested.caption or ""

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
            reply_name=reply_name,
            reply_text=reply_text_preview,
        )
        # Reply to the *quoted* message rather than the /q command message -
        # cmdclean mode may already have deleted the command message by the
        # time we get here, which used to make reply_sticker fail outright.
        # allow_sending_without_reply covers the same case if the quoted
        # message itself somehow vanishes too.
        await reply.reply_sticker(sticker=io.BytesIO(sticker_data), allow_sending_without_reply=True)
    except Exception as e:
        await msg.reply_html(f"[!] Error generating quote sticker: <code>{e}</code>", allow_sending_without_reply=True)


def register(application):
    application.add_handler(CommandHandler(["q", "quote", "quotely"], quotely_cmd))