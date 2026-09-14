import logging

from telegram import Update
from telegram.ext import Application, ApplicationBuilder, ContextTypes

from .config import get_config
from .database.base import close_db, init_db
from .modules import load_all_modules
from .webserver import start_webserver, stop_webserver

logger = logging.getLogger(__name__)


async def on_error(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("Exception while handling an update", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        try:
            await update.effective_message.reply_text(
                "Ara ara, something went wrong on my end. The error has been logged~ 🛠️"
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
