"""MongoDB connection bootstrap, using PyMongo's native async API.

(Motor is deprecated in favor of this as of PyMongo 4.9+, so we use
`pymongo.AsyncMongoClient` directly instead of adding a Motor dependency.)

One global client + database, created once in the app's post_init hook via
init_db() and closed in post_shutdown via close_db(). Modules pull the
database with get_db() and await operations directly - no session objects
to manage, unlike the old SQLAlchemy version.
"""
import logging

from pymongo import AsyncMongoClient

logger = logging.getLogger(__name__)

_client: "AsyncMongoClient | None" = None
_db = None


async def init_db(uri: str, db_name: str):
    """Connect to MongoDB, verify it's reachable, and ensure indexes exist."""
    global _client, _db

    _client = AsyncMongoClient(uri)
    _db = _client[db_name]

    # Fail fast with a clear error at startup if Mongo isn't reachable,
    # rather than the first command handler mysteriously hanging/erroring.
    await _client.admin.command("ping")

    await _db.warns.create_index([("chat_id", 1), ("user_id", 1)])
    await _db.blacklist_words.create_index([("chat_id", 1), ("word", 1)], unique=True)

    logger.info("Connected to MongoDB database '%s'", db_name)
    return _db


def get_db():
    if _db is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db


async def close_db():
    global _client, _db
    if _client is not None:
        await _client.close()
    _client = None
    _db = None
