import re
import aiohttp
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes, MessageHandler, filters

from bot.database.crud import get_neko_mode, set_neko_mode
from bot.modules.admin_tools import is_admin

WAIFU_PICS_ACTIONS = [
    "waifu", "neko", "shinobu", "megumin", "bully", "cuddle", "cry", "hug",
    "awoo", "kiss", "lick", "pat", "smug", "bonk", "yeet", "blush", "smile",
    "spank", "wave", "highfive", "handhold", "nom", "bite", "glomp", "slap",
    "wink", "poke", "dance", "cringe", "tickle"
]

ACTION_VERBS = {
    "hug": ("hugs everyone!", "hugged"),
    "pat": ("pats everyone!", "patted"),
    "slap": ("slaps everyone around!", "slapped"),
    "kiss": ("blows kisses to everyone!", "kissed"),
    "cuddle": ("wants cuddles!", "cuddled"),
    "bonk": ("bonks everyone!", "bonked"),
    "bite": ("bites everyone!", "bit"),
    "spank": ("spanks everyone!", "spanked"),
    "tickle": ("tickles everyone!", "tickled"),
    "handhold": ("wants to hold hands!", "held hands with"),
    "wave": ("waves at everyone!", "waved at"),
    "highfive": ("highfives everyone!", "highfived"),
    "poke": ("pokes everyone!", "poked"),
    "nom": ("noms!", "nommed on"),
    "lick": ("licks everyone!", "licked"),
    "glomp": ("glomps everyone!", "glomped"),
    "bully": ("bullies everyone!", "bullied"),
    "smile": ("smiles warmly!", "smiled at"),
}


def _uwuify(text: str) -> str:
    if not text:
        return text
    # Replace r and l with w
    text = re.sub(r"[rl]", "w", text)
    text = re.sub(r"[RL]", "W", text)
    # Neko sounds
    text = re.sub(r"na", "nya", text)
    text = re.sub(r"ne", "nye", text)
    text = re.sub(r"ni", "nyi", text)
    text = re.sub(r"no", "nyo", text)
    text = re.sub(r"nu", "nyu", text)
    text = re.sub(r"Na", "Nya", text)
    text = re.sub(r"Ne", "Nye", text)
    text = re.sub(r"Ni", "Nyi", text)
    text = re.sub(r"No", "Nyo", text)
    text = re.sub(r"Nu", "Nyu", text)
    # Add cute suffixes
    text = text.rstrip() + " nya~ 🐾"
    return text


async def nekomode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    msg = update.effective_message
    args = context.args

    if chat.type != "private":
        if not await is_admin(update, user.id):
            await msg.reply_html("You must be an admin to toggle Neko Mode!")
            return

    current = await get_neko_mode(chat.id)

    if not args:
        status_str = "ENABLED 🐾" if current else "DISABLED ❌"
        await msg.reply_html(
            f"<b>Neko Mode is currently:</b> {status_str}\n\n"
            "Use <code>/nekomode on</code> or <code>/nekomode off</code> to toggle."
        )
        return

    arg = args[0].lower()
    if arg in ("on", "yes", "enable", "true"):
        await set_neko_mode(chat.id, True)
        await msg.reply_html("<b>Neko Mode has been ENABLED!</b> 🐾 All text will now sound extra cute nya~")
    elif arg in ("off", "no", "disable", "false"):
        await set_neko_mode(chat.id, False)
        await msg.reply_html("<b>Neko Mode has been DISABLED!</b> ❌ Chat back to normal.")
    else:
        await msg.reply_html("Usage: <code>/nekomode on|off</code>")


async def wallpaper_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get("https://nekos.best/api/v2/wallpaper") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        img_url = results[0].get("url")
                        await msg.reply_photo(photo=img_url, caption="✨ Here is your random anime wallpaper!")
                        return
        except Exception:
            pass

        try:
            async with session.get("https://api.waifu.pics/sfw/waifu") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_url = data.get("url")
                    await msg.reply_photo(photo=img_url, caption="✨ Here is your random anime wallpaper!")
                    return
        except Exception as e:
            await msg.reply_html(f"Error fetching wallpaper: <code>{e}</code>")


async def neko_action_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    user = update.effective_user
    cmd = msg.text.split()[0].lstrip("/").split("@")[0].lower()

    target_name = None
    if msg.reply_to_message and msg.reply_to_message.from_user:
        target_name = msg.reply_to_message.from_user.mention_html()

    solo_verb, target_verb = ACTION_VERBS.get(cmd, (f"is feeling {cmd}!", f"{cmd}'d"))

    if target_name:
        caption = f"<b>{user.mention_html()}</b> {target_verb} <b>{target_name}</b>!"
    else:
        caption = f"<b>{user.mention_html()}</b> {solo_verb}"

    # Fetch animation/photo from waifu.pics sfw API
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"https://api.waifu.pics/sfw/{cmd}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    media_url = data.get("url")
                    if media_url:
                        if media_url.endswith((".gif", ".mp4", ".webm")):
                            await msg.reply_animation(animation=media_url, caption=caption, parse_mode="HTML")
                        else:
                            await msg.reply_photo(photo=media_url, caption=caption, parse_mode="HTML")
                        return
        except Exception:
            pass

        # Fallback to nekos.best API if available
        try:
            async with session.get(f"https://nekos.best/api/v2/{cmd}") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        media_url = results[0].get("url")
                        await msg.reply_animation(animation=media_url, caption=caption, parse_mode="HTML")
                        return
        except Exception as e:
            await msg.reply_html(f"Error performing anime action: <code>{e}</code>")


async def neko_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if not msg or not msg.text or not chat or user.is_bot:
        return

    if await get_neko_mode(chat.id):
        neko_text = _uwuify(msg.text)
        await msg.reply_text(neko_text)


def register(application):
    application.add_handler(CommandHandler("nekomode", nekomode_cmd))
    application.add_handler(CommandHandler("neko", nekomode_cmd))
    application.add_handler(CommandHandler("wallpaper", wallpaper_cmd))

    # Register all anime reaction action commands
    for action in WAIFU_PICS_ACTIONS:
        application.add_handler(CommandHandler(action, neko_action_handler))

    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, neko_message_handler),
        group=2,
    )
