import math
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from bot.config import get_config


def _get_start_pic() -> str | None:
    try:
        cfg = get_config()
        if cfg.start_pics:
            return random.choice(cfg.start_pics)
    except Exception:
        pass
    return None


START_TEXT_PM = (
    "Konnichiwa, {name}! I am your anime-themed group manager.\n\n"
    "I can protect your group from spammers, raids, flooders, and keep your chat organized.\n\n"
    "Select a category below to explore my command grimoire:"
)

START_TEXT_GROUP = (
    "Konnichiwa! I am active and managing <b>{chat_title}</b>.\n"
    "Click the button below to view my full command list in PM."
)

CATEGORIES = {
    "basics": (
        "<b>:: BASICS & CORE COMMANDS ::</b>\n\n"
        "» /start - Initialize bot in PM or active group.\n"
        "» /help - Open interactive command grimoire.\n"
        "» /info [user] - Detailed profile card, IDs, premium status & photo stats.\n"
        "» /id [user|chat] - Identification card for caller, chat, target & forwards.\n"
        "» /rules - View group chat rules.\n"
        "» /adminlist - Retrieve full list of chat admins & owner.\n"
        "» /connect &lt;chat_id&gt; - Connect to group remotely in PM.\n"
        "» /disconnect - Disconnect from active PM chat connection.\n"
        "» /connection - Check currently connected PM chat.\n"
        "» /support - Support channel & community group links.\n"
        "» /donate - Development support links.\n"
    ),
    "moderation": (
        "<b>:: MODERATION COMMANDS ::</b>\n\n"
        "» /ban [user] [reason] - Permanently ban a user from chat.\n"
        "» /unban [user] - Lift ban for a user.\n"
        "» /tban &lt;user&gt; &lt;time&gt; [reason] - Temp ban (e.g. /tban @user 2h Flood).\n"
        "  • Time units: m (mins), h (hours), d (days), w (weeks).\n"
        "» /kick [user] [reason] - Kick user from group (allows rejoining via link).\n"
        "» /mute [user] [reason] - Mute user indefinitely.\n"
        "» /unmute [user] - Restore messaging permissions.\n"
        "» /tmute &lt;user&gt; &lt;time&gt; [reason] - Temp mute (e.g. /tmute @user 1d Spam).\n"
        "» /cleancommands on|off - Auto-delete command trigger messages in group chat.\n"
    ),
    "warnings": (
        "<b>:: WARNINGS SYSTEM ::</b>\n\n"
        "» /warn [user] [reason] - Issue a formal warning to a user.\n"
        "» /warns [user] - Check active warnings for a user.\n"
        "» /unwarn [user] - Remove the last warning from a user.\n"
        "» /resetwarns [user] - Clear all warnings for a user.\n"
        "» /setwarnlimit &lt;n&gt; - Set max warning threshold (default: 3).\n"
        "» /setwarnmode mute|kick|ban - Action executed upon reaching max warnings.\n"
    ),
    "antispam": (
        "<b>:: ANTI-SPAM & BLACKLIST ::</b>\n\n"
        "» /addblacklist &lt;word/phrase&gt; - Add forbidden keyword to blacklist.\n"
        "» /rmblacklist &lt;word/phrase&gt; - Remove keyword from blacklist.\n"
        "» /blacklist - List all blacklisted terms in chat.\n"
        "» /blocklistmode delete|warn|mute|kick|ban - Action on blacklist match.\n"
        "» /blacklistdelete on|off - Toggle auto-deletion of blacklisted messages.\n"
        "» /setflood &lt;n&gt; - Set max message flood limit (e.g. 5 msgs in 5s).\n"
        "» /setfloodmode mute|kick|ban - Punishment when flood limit is breached.\n"
        "» /purge - Delete range of messages (reply to start message).\n"
        "» /del - Instantly delete the replied message.\n"
    ),
    "locks": (
        "<b>:: LOCKS & APPROVALS ::</b>\n\n"
        "» /lock &lt;type&gt; - Lock specific content types in chat.\n"
        "» /unlock &lt;type&gt; - Unlock content type.\n"
        "» /locks - View current active lock status.\n"
        "» /locktypes - List all lockable media types.\n"
        "  • Supported types: sticker, photo, video, audio, voice, document, contact, location, url, forward, game, poll, inline.\n"
        "» /approve [user] - Approve user (bypasses flood limits, locks & antispam).\n"
        "» /unapprove [user] - Revoke approved status.\n"
        "» /approved - List approved users in chat.\n"
    ),
    "notes": (
        "<b>:: NOTES SYSTEM ::</b>\n\n"
        "» /save &lt;name&gt; &lt;text|reply&gt; - Save a note (triggered by #name or /get name).\n"
        "  • Supports formatted text, photos, stickers & inline buttons.\n"
        "» /get &lt;name&gt; - Retrieve a saved note.\n"
        "» /notes - List all saved notes in current chat.\n"
        "» /clear &lt;name&gt; - Delete a saved note.\n"
        "» /clearall - Delete all notes in chat (Admin only).\n"
    ),
    "filters": (
        "<b>:: CUSTOM AUTOMATED FILTERS ::</b>\n\n"
        "» /filter &lt;keyword&gt; &lt;reply&gt; - Add auto-reply filter for keyword.\n"
        "  • Triggers whenever keyword is mentioned in group messages.\n"
        "» /filters - List active chat filters.\n"
        "» /stop &lt;keyword&gt; - Remove an auto-reply filter.\n"
        "» /stopall - Stop all custom filters in chat.\n"
    ),
    "welcome": (
        "<b>:: WELCOME & GOODBYE ::</b>\n\n"
        "» /setwelcome &lt;text&gt; - Set custom greeting for new members.\n"
        "» /setgoodbye &lt;text&gt; - Set custom goodbye message when members leave.\n"
        "» /welcome on|off - Toggle welcome messages.\n"
        "» /goodbye on|off - Toggle goodbye messages.\n"
        "  • Formatting Placeholders:\n"
        "    {first} - First name | {last} - Last name | {fullname} - Full name\n"
        "    {username} - @username | {mention} - Mention link | {chat_title} - Group name | {count} - Total members\n"
    ),
    "federations": (
        "<b>:: FEDERATIONS ::</b>\n\n"
        "» /newfed &lt;name&gt; - Create a ban federation.\n"
        "» /delfed &lt;fed_id&gt; - Delete a federation.\n"
        "» /joinfed &lt;fed_id&gt; - Join chat to federation.\n"
        "» /leavefed - Disconnect chat from federation.\n"
        "» /fban &lt;user&gt; [reason] - Fedban user across all linked chats.\n"
        "» /unfban &lt;user&gt; - Lift federation ban.\n"
        "» /fedinfo [fed_id] - View federation details & ban count.\n"
        "» /fedadmins [fed_id] - List federation admins.\n"
        "» /fedpromote &lt;user&gt; - Promote user to fed admin.\n"
        "» /feddemote &lt;user&gt; - Demote fed admin.\n"
    ),
    "fun": (
        "<b>:: FUN & GAMES ::</b>\n\n"
        "» /roll [sides] - Roll a dice (e.g. /roll 20, default: 6).\n"
        "» /8ball &lt;question&gt; - Magic 8-Ball answer.\n"
        "» /ship - Pair two random chat members with romance score.\n"
        "» /power - Measure user's anime power level & tier rank.\n"
        "» /q / /quote - Generate custom Quotely sticker from replied message.\n"
    ),
    "anime": (
        "<b>:: ANIME & HINDI DUBS ::</b>\n\n"
        "» /anime &lt;query&gt; - Search AniList for anime poster, score & synopsis.\n"
        "» /manga &lt;query&gt; - Search manga details, chapters & volumes.\n"
        "» /character &lt;name&gt; - Search anime character bio & photo.\n"
        "» /hindidub &lt;query&gt; - Search Hindi dubbed anime with merged season cards.\n"
        "» /dubinfo &lt;query&gt; - Detailed per-platform Hindi dub breakdown.\n"
        "» /latestdubs [n] - View recently released Hindi dubbed anime.\n"
        "» /dubplatform - Interactive catalog browser (Netflix, Crunchyroll, etc.).\n"
        "» /multidubs - List anime dubbed across 2+ streaming platforms.\n"
        "» /dubseason &lt;year&gt; &lt;season&gt; - Check season-wise dub availability.\n"
        "» /dubstats - Platform distribution statistics for Hindi dubs.\n"
        "» /quote - Random inspirational anime quote.\n"
        "» /waifu - Random waifu portrait.\n"
    ),
    "tr": (
        "<b>:: TRANSLATOR & SPEECH ::</b>\n\n"
        "» /tr [lang_code] - Translate replied message or inline text (default: en).\n"
        "  • Usage: Reply with /tr hi (translates to Hindi) or /tr es text.\n"
        "» /tts [lang_code] &lt;text&gt; - Convert text to audio speech voice note.\n"
        "  • Usage: /tts ja Konnichiwa or reply with /tts hi.\n"
        "  • Supported Languages: en (English), hi (Hindi), ja (Japanese), es (Spanish),\n"
        "    fr (French), de (German), ru (Russian), ar (Arabic), zh (Chinese),\n"
        "    ko (Korean), pt (Portuguese), it (Italian), bn (Bengali), ur (Urdu) & 80+ codes.\n"
    ),
    "neko": (
        "<b>:: NEKO MODE ::</b>\n\n"
        "» /nekomode on|off - Toggle cute anime speech filter in group chat.\n"
        "  • Transforms group messages with anime expressions & sound effects!\n"
    ),
    "kang": (
        "<b>:: STICKER KANG ::</b>\n\n"
        "» /kang [emoji] - Steal replied sticker/image into your custom pack.\n"
        "» /pkang [emoji] - Steal image into PNG sticker pack.\n"
        "  • Automatically creates & updates bot-hosted sticker packs for you!\n"
    ),
    "afk": (
        "<b>:: AFK & WHISPERS ::</b>\n\n"
        "» /afk [reason] - Set away status (notifies anyone who tags you).\n"
        "» /whisper @user secret - Send encrypted secret whisper in chat.\n"
        "  • Only the specified user can open the whisper via inline button!\n"
    ),
    "cosplay": (
        "<b>:: COSPLAY GALLERY ::</b>\n\n"
        "» /cosplay - Fetch random high-quality anime cosplay picture.\n"
    ),
}

# 8 categories per page (4 rows of 2 buttons)
ITEMS_PER_PAGE = 8

CATEGORY_LABELS = [
    ("basics", "Basics"),
    ("moderation", "Moderation"),
    ("warnings", "Warnings"),
    ("antispam", "Anti-Spam"),
    ("locks", "Locks"),
    ("notes", "Notes"),
    ("filters", "Filters"),
    ("welcome", "Welcome"),
    ("federations", "Federations"),
    ("fun", "Fun"),
    ("anime", "Anime"),
    ("tr", "Translator"),
    ("neko", "Neko Mode"),
    ("kang", "Stickers"),
    ("afk", "AFK & Whisper"),
    ("cosplay", "Cosplay"),
]


def _get_help_grid(page: int = 0) -> InlineKeyboardMarkup:
    total_pages = math.ceil(len(CATEGORY_LABELS) / ITEMS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * ITEMS_PER_PAGE
    end_idx = start_idx + ITEMS_PER_PAGE
    current_items = CATEGORY_LABELS[start_idx:end_idx]

    buttons = []
    # Build 2-column grid
    for i in range(0, len(current_items), 2):
        row = []
        key1, label1 = current_items[i]
        row.append(InlineKeyboardButton(f"[ {label1} ]", callback_data=f"hcat:{key1}"))
        if i + 1 < len(current_items):
            key2, label2 = current_items[i + 1]
            row.append(InlineKeyboardButton(f"[ {label2} ]", callback_data=f"hcat:{key2}"))
        buttons.append(row)

    # Navigation bar
    nav_row = []
    prev_page = (page - 1) % total_pages
    next_page = (page + 1) % total_pages

    nav_row.append(InlineKeyboardButton("« Prev", callback_data=f"hpage:{prev_page}"))
    nav_row.append(InlineKeyboardButton(f"Page {page + 1}/{total_pages}", callback_data="hpage:nop"))
    nav_row.append(InlineKeyboardButton("Next »", callback_data=f"hpage:{next_page}"))
    buttons.append(nav_row)

    return InlineKeyboardMarkup(buttons)


async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == "private":
        start_pic = _get_start_pic()
        caption_text = START_TEXT_PM.format(name=user.first_name)
        if start_pic:
            try:
                await msg.reply_photo(
                    photo=start_pic,
                    caption=caption_text,
                    parse_mode="HTML",
                    reply_markup=_get_help_grid(page=0),
                )
                return
            except Exception:
                pass
        await msg.reply_html(caption_text, reply_markup=_get_help_grid(page=0))
    else:
        bot_username = context.bot.username or "AnimeModBot"
        pm_url = f"https://t.me/{bot_username}?start=help"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("[ PM for Help ]", url=pm_url)]])
        await msg.reply_html(START_TEXT_GROUP.format(chat_title=chat.title), reply_markup=keyboard)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message

    if chat.type == "private":
        start_pic = _get_start_pic()
        text = "<b>:: COMMAND GRIMOIRE ::</b>\nSelect a category below to view commands:"
        if start_pic:
            try:
                await msg.reply_photo(
                    photo=start_pic, caption=text, parse_mode="HTML", reply_markup=_get_help_grid(page=0)
                )
                return
            except Exception:
                pass
        await msg.reply_html(text, reply_markup=_get_help_grid(page=0))
    else:
        bot_username = context.bot.username or "AnimeModBot"
        pm_url = f"https://t.me/{bot_username}?start=help"
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("[ Open Grimoire in PM ]", url=pm_url)]])
        await msg.reply_html("Click below to view the command grimoire in PM.", reply_markup=keyboard)


async def help_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    is_photo = bool(query.message and query.message.photo)

    if data.startswith("hpage:"):
        page_str = data.split(":")[1]
        if page_str == "nop":
            await query.answer()
            return
        page = int(page_str)
        text = "<b>:: COMMAND GRIMOIRE ::</b>\nSelect a category below to view commands:"
        if is_photo:
            await query.message.edit_caption(
                caption=text, parse_mode="HTML", reply_markup=_get_help_grid(page=page)
            )
        else:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=_get_help_grid(page=page))
        await query.answer()
        return

    if data == "hcat:main":
        text = "<b>:: COMMAND GRIMOIRE ::</b>\nSelect a category below to view commands:"
        if is_photo:
            await query.message.edit_caption(
                caption=text, parse_mode="HTML", reply_markup=_get_help_grid(page=0)
            )
        else:
            await query.message.edit_text(text, parse_mode="HTML", reply_markup=_get_help_grid(page=0))
        await query.answer()
        return

    if data.startswith("hcat:"):
        cat_key = data.split(":")[1]
        cat_text = CATEGORIES.get(cat_key, "No category info found.")
        back_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("[ « Back to Grimoire ]", callback_data="hcat:main")]]
        )
        if is_photo:
            await query.message.edit_caption(caption=cat_text, parse_mode="HTML", reply_markup=back_markup)
        else:
            await query.message.edit_text(cat_text, parse_mode="HTML", reply_markup=back_markup)
        await query.answer()


def register(application):
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CallbackQueryHandler(help_category_callback, pattern=r"^(hcat:|hpage:)"))
