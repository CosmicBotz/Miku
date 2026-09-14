import aiohttp
from telegram import Update
from telegram.ext import CommandHandler, ContextTypes


async def cosplay_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message

    async with aiohttp.ClientSession() as session:
        # Try primary cosplay API
        try:
            async with session.get("https://web-api-cosplay.vercel.app/cosplay") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    img_url = data.get("url") or data.get("image")
                    if img_url:
                        await msg.reply_photo(photo=img_url, caption="📸 Here is your random anime cosplay!")
                        return
        except Exception:
            pass

        # Try anime aesthetic wallpaper / neko fallback API
        try:
            async with session.get("https://nekos.best/api/v2/kitsune") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    results = data.get("results", [])
                    if results:
                        img_url = results[0].get("url")
                        await msg.reply_photo(photo=img_url, caption="📸 Here is your anime gallery image!")
                        return
        except Exception as e:
            await msg.reply_html(f"Error fetching cosplay image: <code>{e}</code>")


def register(application):
    application.add_handler(CommandHandler("cosplay", cosplay_cmd))
