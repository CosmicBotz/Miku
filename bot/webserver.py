"""A minimal HTTP server that exists purely to satisfy PaaS platforms.

Render, Koyeb, and Heroku-style hosts generally expect a "web" service to
bind to $PORT and answer HTTP health checks - otherwise they consider the
deploy unhealthy (or, on Heroku, the dyno gets killed for not binding a
port at all). This bot talks to Telegram via long polling, not real
webhooks, so there's no inbound Telegram traffic hitting this server at
all. It's a dummy listener: it does nothing except say "OK" so the
platform's health check passes and the process is left alone.

If you later want an actual Telegram webhook instead of polling, this is
the place to add a POST route and switch bot/app.py from run_polling() to
run_webhook() - they're intentionally kept separate for now.
"""
import logging

from aiohttp import web

logger = logging.getLogger(__name__)


async def _health(request: web.Request) -> web.Response:
    return web.Response(text="OK")


async def _root(request: web.Request) -> web.Response:
    return web.Response(text="Anime Mod Bot is alive and running on long polling. 🎌")


async def start_webserver(port: int) -> web.AppRunner:
    app = web.Application()
    app.router.add_get("/", _root)
    app.router.add_get("/health", _health)
    app.router.add_get("/healthz", _health)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    logger.info("Dummy health-check web server listening on port %s", port)
    return runner


async def stop_webserver(runner: web.AppRunner) -> None:
    await runner.cleanup()
