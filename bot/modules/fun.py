import hashlib
import random

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from ..utils.extraction import get_target_user

# Original flavor text (not quoting any specific franchise) to keep the
# fun commands fully self-contained and safe to ship as-is.
QUOTES = [
    "Hard work beats talent when talent refuses to train.",
    "Even the smallest spark can light up the darkest night.",
    "A true hero isn't one without fear, but one who moves forward despite it.",
    "Every scar tells a story of a battle you survived.",
    "The future isn't written until you pick up your sword and write it yourself.",
    "Strength isn't about never falling down, it's about how many times you stand back up.",
]

EIGHTBALL = [
    "Without a doubt!",
    "Ask again after the training arc.",
    "The stars say... maybe not this time.",
    "Absolutely, no contest.",
    "Doubtful — try again next episode.",
    "All signs point to yes!",
    "Cloudy right now, ask again later.",
]


async def power_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target = await get_target_user(update, context) or update.effective_user
    seed = int(hashlib.sha256(f"{target.id}-{random.randint(0, 999999)}".encode()).hexdigest(), 16)
    level = (seed % 99999) + 1
    await update.effective_message.reply_text(f"⚡ {target.first_name}'s power level is {level}!")


async def ship_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    names = []
    if message.reply_to_message and message.reply_to_message.from_user:
        names.append(message.reply_to_message.from_user.first_name)
    if context.args:
        names.extend(context.args)
    if len(names) < 2:
        names = [update.effective_user.first_name, "this chat"]

    a, b = names[0], names[1]
    digest = hashlib.sha256((a + b).encode()).hexdigest()
    percent = int(digest, 16) % 101
    filled = round(10 * percent / 100)
    bar = "❤️" * filled + "🤍" * (10 - filled)
    await message.reply_text(f"{a} x {b}\n{bar} {percent}%")


async def eightball_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(random.choice(EIGHTBALL))


async def quote_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.effective_message.reply_text(random.choice(QUOTES))


async def roll_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    sides = 6
    if context.args and context.args[0].isdigit():
        sides = max(2, int(context.args[0]))
    await update.effective_message.reply_text(f"🎲 You rolled a {random.randint(1, sides)} (d{sides})")


def register(application):
    application.add_handler(CommandHandler("power", power_cmd))
    application.add_handler(CommandHandler("ship", ship_cmd))
    application.add_handler(CommandHandler("8ball", eightball_cmd))
    application.add_handler(CommandHandler("quote", quote_cmd))
    application.add_handler(CommandHandler("roll", roll_cmd))
