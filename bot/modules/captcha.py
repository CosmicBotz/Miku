import random
from telegram import ChatPermissions, InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from ..config import get_config
from ..database import crud
from ..utils.decorators import admin_only, group_only
from .moderation import FULL_PERMISSIONS, MUTED_PERMISSIONS


async def captcha_timeout_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    data = job.data
    chat_id = data["chat_id"]
    user_id = data["user_id"]
    message_id = data.get("message_id")

    try:
        await context.bot.ban_chat_member(chat_id, user_id)
        await context.bot.unban_chat_member(chat_id, user_id, only_if_banned=True)
    except Exception:
        pass

    if message_id:
        try:
            await context.bot.delete_message(chat_id, message_id)
        except Exception:
            pass


@group_only
@admin_only
async def captcha_toggle_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("on", "off"):
        await msg.reply_text("Usage: /captcha on|off")
        return

    enable = context.args[0].lower() == "on"
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, captcha_enabled=enable)
    await msg.reply_text(f"Captcha verification is now {'[ON]' if enable else '[OFF]'}.")


@group_only
@admin_only
async def captcha_mode_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or context.args[0].lower() not in ("button", "text", "math"):
        await msg.reply_text("Usage: /captchamode button|text|math")
        return

    mode = context.args[0].lower()
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, captcha_mode=mode)
    await msg.reply_text(f"Captcha mode set to {mode}.")


@group_only
@admin_only
async def set_captcha_time_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.effective_message
    if not context.args or not context.args[0].isdigit():
        await msg.reply_text("Usage: /setcaptchatime <seconds>")
        return

    seconds = max(30, int(context.args[0]))
    cfg = get_config()
    await crud.get_or_create_chat(update.effective_chat.id, update.effective_chat.title, cfg.defaults)
    await crud.update_chat(update.effective_chat.id, captcha_time=seconds)
    await msg.reply_text(f"Captcha timeout set to {seconds} seconds.")


async def send_captcha_challenge(update: Update, context: ContextTypes.DEFAULT_TYPE, user):
    chat = update.effective_chat
    cfg = get_config()
    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)

    if not getattr(settings, "captcha_enabled", False):
        return

    try:
        await context.bot.restrict_chat_member(chat.id, user.id, permissions=MUTED_PERMISSIONS)
    except Exception:
        return

    mode = getattr(settings, "captcha_mode", "button")
    captcha_time = getattr(settings, "captcha_time", 300)

    if mode in ("math", "text"):
        a, b = random.randint(1, 10), random.randint(1, 10)
        correct_ans = a + b
        distractors = set()
        while len(distractors) < 3:
            val = random.randint(2, 20)
            if val != correct_ans:
                distractors.add(val)
        options = list(distractors) + [correct_ans]
        random.shuffle(options)

        buttons = [
            InlineKeyboardButton(
                str(opt),
                callback_data=f"cpt:{user.id}:{'correct' if opt == correct_ans else 'wrong'}",
            )
            for opt in options
        ]
        keyboard = InlineKeyboardMarkup([buttons])
        text = f"[CAPTCHA] Welcome <a href=\"tg://user?id={user.id}\">{user.first_name}</a>! Please solve this math captcha: <b>{a} + {b} = ?</b>"
    else:
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("[ Confirm Human ]", callback_data=f"cpt:{user.id}:correct")]]
        )
        text = f"[CAPTCHA] Welcome <a href=\"tg://user?id={user.id}\">{user.first_name}</a>! Click the button below to prove you are human."

    sent_msg = await update.effective_message.reply_html(text, reply_markup=keyboard)

    if context.job_queue:
        context.job_queue.run_once(
            captcha_timeout_job,
            captcha_time,
            data={"chat_id": chat.id, "user_id": user.id, "message_id": sent_msg.message_id},
        )


async def captcha_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query.data.startswith("cpt:"):
        return

    parts = query.data.split(":")
    target_user_id = int(parts[1])
    result = parts[2]

    if query.from_user.id != target_user_id:
        await query.answer("[!] This captcha is not for you.", show_alert=True)
        return

    if result == "correct":
        try:
            await context.bot.restrict_chat_member(
                query.message.chat_id, target_user_id, permissions=FULL_PERMISSIONS
            )
            await query.answer("[PASS] Captcha passed! Welcome.", show_alert=True)
            await query.message.delete()
        except Exception as e:
            await query.answer(f"Failed to unrestrict: {e}", show_alert=True)
    else:
        await query.answer("[x] Wrong answer! Try again.", show_alert=True)


def register(application):
    application.add_handler(CommandHandler("captcha", captcha_toggle_cmd))
    application.add_handler(CommandHandler("captchamode", captcha_mode_cmd))
    application.add_handler(CommandHandler("setcaptchatime", set_captcha_time_cmd))
    application.add_handler(CallbackQueryHandler(captcha_callback_handler, pattern=r"^cpt:"))
