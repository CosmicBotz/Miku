import aiohttp
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

ANILIST_URL = "https://graphql.anilist.co"

ANIME_QUERY = """
query ($search: String) {
  Media (search: $search, type: ANIME) {
    id
    title {
      romaji
      english
      native
    }
    status
    episodes
    duration
    averageScore
    genres
    description(asHtml: false)
    coverImage {
      extraLarge
    }
    siteUrl
  }
}
"""

MANGA_QUERY = """
query ($search: String) {
  Media (search: $search, type: MANGA) {
    id
    title {
      romaji
      english
      native
    }
    status
    chapters
    volumes
    averageScore
    genres
    description(asHtml: false)
    coverImage {
      extraLarge
    }
    siteUrl
  }
}
"""

CHARACTER_QUERY = """
query ($search: String) {
  Character (search: $search) {
    name {
      full
      native
    }
    description(asHtml: false)
    image {
      large
    }
    siteUrl
  }
}
"""


def _clean_description(desc: str, limit: int = 350) -> str:
    if not desc:
        return "No description available."
    clean = desc.replace("<br>", "\n").replace("<i>", "").replace("</i>", "").replace("<b>", "").replace("</b>", "")
    if len(clean) > limit:
        return clean[:limit] + "..."
    return clean


async def anime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    query = " ".join(context.args)
    if not query:
        await msg.reply_html("<b>Usage:</b> <code>/anime &lt;anime title&gt;</code>")
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                ANILIST_URL, json={"query": ANIME_QUERY, "variables": {"search": query}}
            ) as resp:
                data = await resp.json()
                media = data.get("data", {}).get("Media")
                if not media:
                    await msg.reply_html("No anime found matching your query!")
                    return

                title = media["title"].get("english") or media["title"].get("romaji")
                native = media["title"].get("native", "")
                status = media.get("status", "N/A")
                episodes = media.get("episodes", "N/A")
                score = media.get("averageScore", "N/A")
                genres = ", ".join(media.get("genres", []))
                cover = media.get("coverImage", {}).get("extraLarge")
                site_url = media.get("siteUrl", "https://anilist.co")
                desc = _clean_description(media.get("description"))

                text = (
                    f"<b>{title}</b> ({native})\n\n"
                    f"<b>Status:</b> {status}\n"
                    f"<b>Episodes:</b> {episodes}\n"
                    f"<b>Score:</b> {score}%\n"
                    f"<b>Genres:</b> {genres}\n\n"
                    f"<b>Description:</b>\n{desc}"
                )
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 View on AniList", url=site_url)]])

                if cover:
                    await msg.reply_photo(photo=cover, caption=text, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await msg.reply_html(text, reply_markup=keyboard)
        except Exception as e:
            await msg.reply_html(f"Error fetching anime info: <code>{e}</code>")


async def manga_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    query = " ".join(context.args)
    if not query:
        await msg.reply_html("<b>Usage:</b> <code>/manga &lt;manga title&gt;</code>")
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                ANILIST_URL, json={"query": MANGA_QUERY, "variables": {"search": query}}
            ) as resp:
                data = await resp.json()
                media = data.get("data", {}).get("Media")
                if not media:
                    await msg.reply_html("No manga found matching your query!")
                    return

                title = media["title"].get("english") or media["title"].get("romaji")
                native = media["title"].get("native", "")
                status = media.get("status", "N/A")
                chapters = media.get("chapters", "N/A")
                volumes = media.get("volumes", "N/A")
                score = media.get("averageScore", "N/A")
                genres = ", ".join(media.get("genres", []))
                cover = media.get("coverImage", {}).get("extraLarge")
                site_url = media.get("siteUrl", "https://anilist.co")
                desc = _clean_description(media.get("description"))

                text = (
                    f"<b>{title}</b> ({native})\n\n"
                    f"<b>Status:</b> {status}\n"
                    f"<b>Chapters:</b> {chapters} | <b>Volumes:</b> {volumes}\n"
                    f"<b>Score:</b> {score}%\n"
                    f"<b>Genres:</b> {genres}\n\n"
                    f"<b>Description:</b>\n{desc}"
                )
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 View on AniList", url=site_url)]])

                if cover:
                    await msg.reply_photo(photo=cover, caption=text, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await msg.reply_html(text, reply_markup=keyboard)
        except Exception as e:
            await msg.reply_html(f"Error fetching manga info: <code>{e}</code>")


async def character_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    query = " ".join(context.args)
    if not query:
        await msg.reply_html("<b>Usage:</b> <code>/character &lt;name&gt;</code>")
        return

    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(
                ANILIST_URL, json={"query": CHARACTER_QUERY, "variables": {"search": query}}
            ) as resp:
                data = await resp.json()
                char = data.get("data", {}).get("Character")
                if not char:
                    await msg.reply_html("No character found!")
                    return

                name = char["name"].get("full")
                native = char["name"].get("native", "")
                img = char.get("image", {}).get("large")
                site_url = char.get("siteUrl", "https://anilist.co")
                desc = _clean_description(char.get("description"))

                text = f"<b>{name}</b> ({native})\n\n<b>Bio:</b>\n{desc}"
                keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("🔗 View on AniList", url=site_url)]])

                if img:
                    await msg.reply_photo(photo=img, caption=text, parse_mode="HTML", reply_markup=keyboard)
                else:
                    await msg.reply_html(text, reply_markup=keyboard)
        except Exception as e:
            await msg.reply_html(f"Error fetching character info: <code>{e}</code>")


async def quote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://api.waifu.pics/sfw/waifu") as resp:
                pass
            # Fetch random quote from animechan API or fallback
            async with session.get("https://animechan.xyz/api/random") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    quote = data.get("quote")
                    character = data.get("character")
                    anime = data.get("anime")
                    await msg.reply_html(
                        f"<i>\"{quote}\"</i>\n\n— <b>{character}</b> ({anime})"
                    )
                    return
        except Exception:
            pass

    # High quality fallback anime quote
    quotes = [
        ("Fear is not evil. It tells you what your weakness is. And once you know your weakness, you can become stronger as well as kinder.", "Gildarts Clive", "Fairy Tail"),
        ("It's not the face that makes someone a monster, it's the choices they make with their lives.", "Naruto Uzumaki", "Naruto"),
        ("If you don't take risks, you can't create a future.", "Monkey D. Luffy", "One Piece"),
        ("A lesson without pain is meaningless.", "Edward Elric", "Fullmetal Alchemist"),
        ("Words are magic.", "Frieren", "Frieren: Beyond Journey's End"),
    ]
    import random
    q, c, a = random.choice(quotes)
    await msg.reply_html(f"<i>\"{q}\"</i>\n\n— <b>{c}</b> ({a})")


async def waifu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://nekos.best/api/v2/waifu") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        img_url = results[0].get("url")
                        artist_name = results[0].get("artist_name", "Unknown Artist")
                        await msg.reply_photo(
                            photo=img_url,
                            caption=f"Here is your waifu! ✨\n<b>Artist:</b> {artist_name}",
                            parse_mode="HTML",
                        )
                        return
        except Exception:
            pass

        # Fallback to waifu.pics
        try:
            async with session.get("https://api.waifu.pics/sfw/waifu") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_url = data.get("url")
                    await msg.reply_photo(photo=img_url, caption="Here is your waifu! ✨")
                    return
        except Exception as e:
            await msg.reply_html(f"Error fetching waifu: <code>{e}</code>")


def register(application):
    application.add_handler(CommandHandler("anime", anime_cmd))
    application.add_handler(CommandHandler("manga", manga_cmd))
    application.add_handler(CommandHandler("character", character_cmd))
    application.add_handler(CommandHandler("quote", quote_cmd))
    application.add_handler(CommandHandler("waifu", waifu_cmd))
