import html
import logging
import traceback

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes

from .config import get_config
from .database.base import close_db, init_db
from .modules import load_all_modules
from .webserver import start_webserver, stop_webserver

logger = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update", exc_info=context.error)

    tb_list = (
        traceback.format_exception(None, context.error, context.error.__traceback__)
        if context.error
        else []
    )
    tb_string = "".join(tb_list)
    if len(tb_string) > 3000:
        tb_string = tb_string[-3000:]

    escaped_tb = html.escape(tb_string)
    err_name = html.escape(type(context.error).__name__ if context.error else "UnknownError")
    err_msg = html.escape(str(context.error) if context.error else "")

    error_text = (
        f"⚠️ <b>An error occurred:</b> <code>{err_name}: {err_msg}</code>\n\n"
        f"<b>Recent Error Log:</b>\n"
        f"<pre>{escaped_tb}</pre>"
    )

    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_html(error_text)
        except Exception:
            try:
                clean_msg = (
                    f"⚠️ An error occurred: {err_name}: {err_msg}\n\n"
                    f"Recent Error Log:\n{tb_string[-1500:]}"
                )
                await update.effective_message.reply_text(clean_msg[:4000])
            except Exception:
                pass

    try:
        cfg = get_config()
        if cfg.owner_id:
            await context.bot.send_message(
                chat_id=cfg.owner_id,
                text=f"<b>[BOT ERROR ALERT]</b>\n{error_text}",
                parse_mode="HTML",
            )
    except Exception:
        pass


async def _post_init(application: Application) -> None:
    """Runs once, inside PTB's own event loop, before polling starts."""
    cfg = get_config()
    await init_db(cfg.mongo_uri, cfg.mongo_db_name)
    application.bot_data["webserver_runner"] = await start_webserver(cfg.port)
    logger.info("Anime Mod Bot is ready.")


async def _post_shutdown(application: Application) -> None:
    """Runs once as the application is shutting down."""
    runner = application.bot_data.get("webserver_runner")
    if runner is not None:
        await stop_webserver(runner)
    await close_db()


def build_application() -> Application:
    cfg = get_config()
    application = (
        ApplicationBuilder()
        .token(cfg.bot_token)
        .post_init(_post_init)
        .post_shutdown(_post_shutdown)
        .build()
    )
    application.add_error_handler(on_error)
    load_all_modules(application)
    return application


def run() -> None:
    application = build_application()
    logger.info("Starting polling...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
