from collections import defaultdict
import math
import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes


def _progress_bar(val: int, max_val: int, length: int = 10) -> str:
    if max_val <= 0:
        return "░" * length
    filled = min(length, int(round((val / max_val) * length)))
    return "█" * filled + "░" * (length - filled)


def _group_and_format_dub_results(results: list[dict]) -> str:
    grouped = defaultdict(list)
    for item in results:
        title = item.get("title", "Unknown Title")
        m = re.search(
            r"^(.*?)\s*\((Season[^)]+|Ep[^)]+|Eps[^)]+|Specials?|Movie|Part[^)]+)\)$",
            title,
            re.IGNORECASE,
        )
        if m:
            base_title = m.group(1).strip()
            season_tag = m.group(2).strip()
        else:
            base_title = title.strip()
            season_tag = None

        grouped[base_title].append((season_tag, item))

    lines = []
    for base_title, items in grouped.items():
        lines.append(f"» <b>{base_title}</b>")
        for season_tag, item in items:
            tag_label = f"• <b>{season_tag}</b>" if season_tag else "• <b>Main Series / Movie</b>"
            lines.append(f"  {tag_label}")

            dubs = item.get("hindi_dubs", [])
            if dubs:
                for dub in dubs:
                    plat = dub.get("platform", "Unknown")
                    rel = dub.get("release_date") or "N/A"
                    stat = dub.get("status") or "N/A"
                    mtype = (dub.get("media_type") or "series").capitalize()
                    lines.append(f"    - Platform: <b>{plat}</b> | Release: <code>{rel}</code> | Status: <b>{stat}</b> ({mtype})")
            else:
                lines.append("    - <i>No platform metadata available.</i>")

            if item.get("notes"):
                lines.append(f"    - Note: <i>{item.get('notes')}</i>")
        lines.append("")

    return "\n".join(lines).strip()


async def hindidub_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Search for Hindi dubbed anime by title and merge seasons under base title."""
    msg = update.effective_message
    query = " ".join(context.args)
    if not query:
        await msg.reply_html(
            "<b>Usage:</b> <code>/hindidub &lt;anime title&gt;</code>\n"
            "<i>Example: /hindidub Naruto</i>"
        )
        return

    try:
        import aninidhi
        results = aninidhi.search(query)
        if not results:
            await msg.reply_html(f"[!] No Hindi-dubbed anime found matching <b>'{query}'</b>.")
            return

        formatted = _group_and_format_dub_results(results[:10])
        text = f"<b>:: HINDI DUB SEARCH RESULTS FOR '{query.upper()}' ::</b>\n\n{formatted}"

        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("View Platform Stats", callback_data="hnd_stats")]]
        )
        await msg.reply_html(text, reply_markup=keyboard)

    except Exception as e:
        await msg.reply_html(f"[!] Error fetching Hindi dub info: <code>{e}</code>")


async def dubinfo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get full per-platform dub breakdown for an anime title with season merging."""
    msg = update.effective_message
    query = " ".join(context.args)
    if not query:
        await msg.reply_html("<b>Usage:</b> <code>/dubinfo &lt;anime title&gt;</code>")
        return

    try:
        import aninidhi
        info = aninidhi.get_dub_info(query)
        if not info:
            await msg.reply_html(f"[!] No dub details found for <b>'{query}'</b>.")
            return

        formatted = _group_and_format_dub_results(info[:10])
        text = f"<b>:: HINDI DUB BREAKDOWN — '{query.upper()}' ::</b>\n\n{formatted}"

        await msg.reply_html(text)
    except Exception as e:
        await msg.reply_html(f"[!] Error: <code>{e}</code>")


async def latestdubs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Retrieve recently released Hindi-dubbed anime."""
    msg = update.effective_message
    limit = 10
    if context.args and context.args[0].isdigit():
        limit = min(20, max(1, int(context.args[0])))

    try:
        import aninidhi
        latest = aninidhi.get_latest(limit=limit, dubbed_only=True)
        if not latest:
            await msg.reply_html("[!] No recent Hindi dub releases found.")
            return

        text = f"<b>:: RECENT HINDI DUB RELEASES (TOP {len(latest)}) ::</b>\n\n"
        for idx, item in enumerate(latest, 1):
            title = item.get("title", "Unknown")
            dubs = item.get("hindi_dubs", [])
            plat_info = ", ".join(f"{d.get('platform')} ({d.get('release_date', 'N/A')})" for d in dubs) if dubs else "Official Dub"
            text += f"<b>{idx}.</b> <b>{title}</b>\n   • <i>{plat_info}</i>\n"

        await msg.reply_html(text)
    except Exception as e:
        await msg.reply_html(f"[!] Error fetching latest dubs: <code>{e}</code>")


async def dubplatform_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Filter Hindi-dubbed anime by streaming platform."""
    msg = update.effective_message
    platform = " ".join(context.args).strip()

    platforms = ["Crunchyroll", "Netflix", "Muse India", "Anime Times (Prime Video)"]

    if not platform:
        buttons = [
            [InlineKeyboardButton(p, callback_data=f"hnd_plat:{p}")]
            for p in platforms
        ]
        keyboard = InlineKeyboardMarkup(buttons)
        await msg.reply_html(
            "<b>:: SELECT DUBBING PLATFORM ::</b>\n\n"
            "Choose a streaming platform below to view its Hindi-dubbed catalog:",
            reply_markup=keyboard,
        )
        return

    await _send_platform_catalog(msg, platform)


async def _send_platform_catalog(target_msg, platform_name: str):
    try:
        import aninidhi
        items = aninidhi.get_by_platform(platform_name)
        if not items:
            await target_msg.reply_html(f"[!] No Hindi-dubbed anime found on <b>{platform_name}</b>.")
            return

        formatted = _group_and_format_dub_results(items[:15])
        text = f"<b>:: HINDI DUBS ON {platform_name.upper()} ::</b>\n\n{formatted}"

        await target_msg.reply_html(text)
    except Exception as e:
        await target_msg.reply_html(f"[!] Error fetching platform catalog: <code>{e}</code>")


async def multidubs_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Find anime dubbed across multiple streaming platforms."""
    msg = update.effective_message
    try:
        import aninidhi
        items = aninidhi.multi_platform_dubs(min_platforms=2)
        if not items:
            await msg.reply_html("[!] No multi-platform dubbed anime found.")
            return

        formatted = _group_and_format_dub_results(items[:10])
        text = f"<b>:: MULTI-PLATFORM HINDI DUBBED ANIME ::</b>\n\n{formatted}"

        await msg.reply_html(text)
    except Exception as e:
        await msg.reply_html(f"[!] Error: <code>{e}</code>")


async def dubseason_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get anime from a specific MAL season and year."""
    msg = update.effective_message
    if len(context.args) < 2 or not context.args[0].isdigit():
        await msg.reply_html("<b>Usage:</b> <code>/dubseason &lt;year&gt; &lt;winter|spring|summer|fall&gt;</code>")
        return

    year = int(context.args[0])
    season = context.args[1].lower()

    try:
        import aninidhi
        results = aninidhi.get_season(year, season)
        if not results:
            await msg.reply_html(f"[!] No dataset records found for <b>{season.capitalize()} {year}</b>.")
            return

        text = f"<b>:: ANIME SEASON: {season.upper()} {year} ::</b>\n\n"
        for item in results[:10]:
            title = item.get("title", "Unknown")
            dubbed = "[+] Hindi Dubbed" if item.get("hindi_available") else "[-] No Hindi Dub"
            text += f"• <b>{title}</b> — {dubbed}\n"

        await msg.reply_html(text)
    except Exception as e:
        await msg.reply_html(f"[!] Error: <code>{e}</code>")


async def dubstats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """View platform distribution statistics for Hindi dubbed anime."""
    msg = update.effective_message
    await _send_dub_stats(msg)


async def _send_dub_stats(target_msg):
    try:
        import aninidhi
        stats = aninidhi.platform_stats()
        if not stats:
            await target_msg.reply_html("[!] No platform statistics available.")
            return

        total = sum(stats.values())
        max_val = max(stats.values()) if stats else 1

        text = "<b>:: HINDI DUBBED ANIME PLATFORM STATS ::</b>\n\n"
        for platform, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
            bar = _progress_bar(count, max_val, length=10)
            pct = (count / total * 100) if total else 0
            text += f"» <b>{platform}</b>\n<code>[{bar}]</code> {count} titles ({pct:.1f}%)\n\n"

        text += f"• <b>Total Dubbed Releases Indexed:</b> <code>{total}</code>\n"
        text += f"• <b>Data Engine:</b> <code>aninidhi {getattr(aninidhi, '__version__', '0.2.0')}</code>"

        await target_msg.reply_html(text)
    except Exception as e:
        await target_msg.reply_html(f"[!] Error fetching stats: <code>{e}</code>")


async def hindi_anime_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle callback buttons for platform selection and stats."""
    query = update.callback_query
    data = query.data or ""
    await query.answer()

    if data.startswith("hnd_plat:"):
        platform = data.split(":", 1)[1]
        await _send_platform_catalog(query.message, platform)
    elif data == "hnd_stats":
        await _send_dub_stats(query.message)


def register(application):
    application.add_handler(CommandHandler(["hindidub", "hindianime"], hindidub_cmd))
    application.add_handler(CommandHandler("dubinfo", dubinfo_cmd))
    application.add_handler(CommandHandler(["latestdubs", "recentdubs"], latestdubs_cmd))
    application.add_handler(CommandHandler(["dubplatform", "dubbyplatform"], dubplatform_cmd))
    application.add_handler(CommandHandler("multidubs", multidubs_cmd))
    application.add_handler(CommandHandler("dubseason", dubseason_cmd))
    application.add_handler(CommandHandler("dubstats", dubstats_cmd))
    application.add_handler(CallbackQueryHandler(hindi_anime_callback, pattern=r"^hnd_"))
