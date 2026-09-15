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
        "» /start - Start the bot\n"
        "» /help - View command grimoire\n"
        "» /info [user] - Show user details & profile pic count\n"
        "» /id - Show user & chat IDs\n"
        "» /rules - View chat rules\n"
        "» /adminlist - List chat admins\n"
        "» /connect &lt;chat_id&gt; - Connect to chat in PM\n"
        "» /disconnect - Disconnect active PM chat\n"
        "» /connection - Check active PM connection\n"
        "» /support - Support channel & group links\n"
        "» /donate - Support bot development\n"
    ),
    "moderation": (
        "<b>:: MODERATION COMMANDS ::</b>\n\n"
        "» /ban [reason] - Ban a user\n"
        "» /unban - Unban a user\n"
        "» /tban &lt;user&gt; &lt;time&gt; [reason] - Temp ban (e.g. 1h30m, 2d)\n"
        "» /kick - Kick a user from chat\n"
        "» /mute - Mute a user\n"
        "» /unmute - Unmute a user\n"
        "» /tmute &lt;user&gt; &lt;time&gt; [reason] - Temp mute (e.g. 1h30m, 2d)\n"
    ),
    "warnings": (
        "<b>:: WARNINGS SYSTEM ::</b>\n\n"
        "» /warn [reason] - Warn a user\n"
        "» /warns [user] - Check user's warnings\n"
        "» /unwarn - Remove last warning from user\n"
        "» /resetwarns - Clear all user warnings\n"
        "» /setwarnlimit &lt;n&gt; - Set max warn limit\n"
        "» /setwarnmode mute|kick|ban - Action on max warns\n"
    ),
    "antispam": (
        "<b>:: ANTI-SPAM & BLACKLIST ::</b>\n\n"
        "» /addblacklist &lt;word&gt; - Add word to blacklist\n"
        "» /rmblacklist &lt;word&gt; - Remove word from blacklist\n"
        "» /blacklist - List blacklisted words\n"
        "» /blocklistmode delete|warn|mute|kick|ban - Action on blacklist match\n"
        "» /blacklistdelete on|off - Delete blacklisted messages\n"
        "» /setflood &lt;n&gt; - Messages allowed in flood window\n"
        "» /setfloodmode mute|kick|ban - Action on flood limit\n"
        "» /purge - Delete range of messages (reply to start)\n"
        "» /del - Delete replied message\n"
    ),
    "locks": (
        "<b>:: LOCKS & APPROVALS ::</b>\n\n"
        "» /lock &lt;type&gt; - Lock media/content type\n"
        "» /unlock &lt;type&gt; - Unlock content type\n"
        "» /locks - Show active lock status\n"
        "» /locktypes - List supported lock types\n"
        "» /approve - Approve user (bypass flood, spam, locks)\n"
        "» /unapprove - Remove approval\n"
        "» /approved - List approved users in chat\n"
    ),
    "notes": (
        "<b>:: NOTES ::</b>\n\n"
        "» /save &lt;name&gt; &lt;content|reply&gt; - Save a note (#name trigger)\n"
        "» /get &lt;name&gt; - Get a saved note\n"
        "» /notes - List all saved notes in chat\n"
        "» /clear &lt;name&gt; - Delete a saved note\n"
        "» /clearall - Delete all notes in chat\n"
    ),
    "filters": (
        "<b>:: CUSTOM FILTERS ::</b>\n\n"
        "» /filter &lt;keyword&gt; &lt;reply&gt; - Add auto-reply filter\n"
        "» /filters - List active chat filters\n"
        "» /stop &lt;keyword&gt; - Stop/remove a filter\n"
        "» /stopall - Stop all chat filters\n"
    ),
    "welcome": (
        "<b>:: WELCOME & GOODBYE ::</b>\n\n"
        "» /setwelcome &lt;text&gt; - Set custom welcome message\n"
        "» /setgoodbye &lt;text&gt; - Set custom leave message\n"
        "» /welcome on|off - Toggle welcome messages\n"
        "» /goodbye on|off - Toggle goodbye messages\n"
        "Placeholders: {first} {last} {fullname} {username} {mention} {chat_title} {count}\n"
    ),
    "federations": (
        "<b>:: FEDERATIONS ::</b>\n\n"
        "» /newfed &lt;name&gt; - Create a federation\n"
        "» /delfed &lt;fed_id&gt; - Delete a federation\n"
        "» /joinfed &lt;fed_id&gt; - Join chat to federation\n"
        "» /leavefed - Leave federation\n"
        "» /fban &lt;user&gt; [reason] - Fedban user across all fed chats\n"
        "» /unfban &lt;user&gt; - Un-fedban user\n"
        "» /fedinfo [fed_id] - View federation details\n"
        "» /fedadmins [fed_id] - List federation admins\n"
        "» /fedpromote &lt;user&gt; - Add fed admin\n"
        "» /feddemote &lt;user&gt; - Remove fed admin\n"
    ),
    "fun": (
        "<b>:: FUN & GAMES ::</b>\n\n"
        "» /roll [sides] - Roll a dice (default 6)\n"
        "» /8ball &lt;question&gt; - Magic 8-Ball answer\n"
        "» /ship - Ship two users in the chat\n"
        "» /power - Measure user's anime power level\n"
    ),
    "anime": (
        "<b>:: ANIME & MANGA ::</b>\n\n"
        "» /anime &lt;query&gt; - Search anime info & poster\n"
        "» /manga &lt;query&gt; - Search manga details\n"
        "» /character &lt;name&gt; - Search anime character bio\n"
        "» /hindidub &lt;query&gt; - Search Hindi dubbed anime platforms & release info\n"
        "» /dubinfo &lt;query&gt; - Detailed per-platform Hindi dub breakdown\n"
        "» /latestdubs [n] - View recently released Hindi dubbed anime\n"
        "» /dubplatform - Browse Hindi dubbed anime by platform (Netflix, CR, etc.)\n"
        "» /multidubs - List anime dubbed across 2+ platforms\n"
        "» /dubseason &lt;year&gt; &lt;season&gt; - Season-wise dub availability\n"
        "» /dubstats - Platform distribution statistics for Hindi dubs\n"
        "» /quote - Random anime quote\n"
        "» /waifu - Random waifu picture\n"
    ),
    "tr": (
        "<b>:: TRANSLATOR & SPEECH ::</b>\n\n"
        "» /tr [lang_code] - Translate replied message\n"
        "» /tts [lang_code] &lt;text&gt; - Text-to-speech audio generator\n"
    ),
    "neko": (
        "<b>:: NEKO MODE ::</b>\n\n"
        "» /nekomode on|off - Toggle cute anime speech filter in group\n"
    ),
    "kang": (
        "<b>:: STICKER KANG ::</b>\n\n"
        "» /kang / /pkang - Steal replied sticker into your sticker pack\n"
    ),
    "afk": (
        "<b>:: AFK & WHISPERS ::</b>\n\n"
        "» /afk [reason] - Set your away status\n"
        "» /whisper @user secret - Send secret whisper message\n"
    ),
    "cosplay": (
        "<b>:: COSPLAY & GALLERY ::</b>\n\n"
        "» /cosplay - Get random anime cosplay picture\n"
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
