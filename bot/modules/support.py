from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CommandHandler, ContextTypes

SUPPORT_TEXT = (
    "<b>:: ANIME GUARDIAN SUPPORT & COMMUNITY ::</b>\n\n"
    "Need help, found a bug, or want to suggest a feature?\n"
    "Join our support community below."
)

DONATE_TEXT = (
    "<b>:: SUPPORT ANIME GUARDIAN BOT ::</b>\n\n"
    "Anime Guardian is free and open-source.\n"
    "If you find this bot useful for your community, consider supporting development costs."
)


async def support_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("[ Updates Channel ]", url="https://t.me/CosmicBotz"),
                InlineKeyboardButton("[ Support Group ]", url="https://t.me/CosmicBotz_support"),
            ]
        ]
    )
    await update.effective_message.reply_html(SUPPORT_TEXT, reply_markup=keyboard)


async def donate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("[ Support Project ]", url="https://github.com"),
            ]
        ]
    )
    await update.effective_message.reply_html(DONATE_TEXT, reply_markup=keyboard)


def register(application):
    application.add_handler(CommandHandler("support", support_cmd))
    application.add_handler(CommandHandler("donate", donate_cmd))
