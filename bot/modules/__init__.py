"""Module auto-loader.

Every .py file in this package that defines a top-level
`register(application)` function is treated as a bot module and is loaded
automatically at startup - no need to hand-edit a big list of imports.
"""
import importlib
import logging
import pkgutil

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

logger = logging.getLogger(__name__)


class ApplicationProxy:
    """Proxy around Application to intercept add_handler for command disabling."""

    def __init__(self, application: Application):
        self._app = application

    def add_handler(self, handler, group=0):
        if isinstance(handler, CommandHandler):
            orig_callback = handler.callback
            command_list = [c.lower() for c in handler.commands] if hasattr(handler, "commands") else []

            async def check_disabled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
                chat = update.effective_chat
                user = update.effective_user
                if chat and chat.type in ("group", "supergroup") and user:
                    from ..config import get_config
                    from ..database import crud

                    cfg = get_config()
                    settings = await crud.get_or_create_chat(chat.id, chat.title, cfg.defaults)
                    disabled_cmds = getattr(settings, "disabled_commands", []) or []

                    if disabled_cmds:
                        if user.id == cfg.owner_id or user.id in cfg.sudo_users:
                            is_admin = True
                        else:
                            try:
                                member = await chat.get_member(user.id)
                                is_admin = member.status in ("administrator", "creator")
                            except Exception:
                                is_admin = False

                        if not is_admin:
                            msg_text = update.effective_message.text if update.effective_message else ""
                            cmd_used = (
                                msg_text.split()[0].lstrip("/").split("@")[0].lower()
                                if msg_text and msg_text.startswith("/")
                                else ""
                            )
                            if cmd_used in disabled_cmds or any(c in disabled_cmds for c in command_list):
                                return

                return await orig_callback(update, context)

            handler.callback = check_disabled_callback

        return self._app.add_handler(handler, group=group)

    def __getattr__(self, name):
        return getattr(self._app, name)


def load_all_modules(application: Application) -> list[str]:
    proxy = ApplicationProxy(application)
    loaded = []
    for _finder, module_name, is_pkg in pkgutil.iter_modules(__path__):
        if is_pkg or module_name.startswith("_") or module_name == "filters":
            continue
        full_name = f"{__name__}.{module_name}"
        module = importlib.import_module(full_name)
        register = getattr(module, "register", None)
        if register is None:
            logger.warning("Module '%s' has no register(application) function, skipping.", module_name)
            continue
        register(proxy)
        loaded.append(module_name)

    logger.info("Loaded modules: %s", ", ".join(sorted(loaded)) or "(none)")
    return loaded
