"""
MongoDB Connection Module

Provides async MongoDB client for report data storage and retrieval.
Uses motor (async driver) for non-blocking operations within FastAPI.
Supports both native MongoDB and Azure CosmosDB MongoDB API.
"""

import time

from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
from common.config import settings
from common.logging import get_logger

logger = get_logger(__name__)

_client: AsyncIOMotorClient | None = None
_db = None
_available: bool | None = None  # None = not tested yet
_last_health_check: float = 0.0  # timestamp of last health check
_HEALTH_RETRY_INTERVAL = 30  # seconds between retry attempts when unavailable
_HEALTH_CHECK_INTERVAL = 120  # seconds between periodic health checks when available

DATABASE_NAME = "stock_reports"


class MongoUnavailableError(Exception):
    """Raised when MongoDB is not reachable or credentials are invalid."""
    pass


async def get_mongo_client() -> AsyncIOMotorClient:
    """Lazy-initialize and return the Motor async client."""
    global _client
    if _client is None:
        if not settings.MONGO_DB_URL:
            raise MongoUnavailableError("MONGO_DB_URL is not configured")
        _client = AsyncIOMotorClient(
            settings.MONGO_DB_URL,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=5000,
            maxPoolSize=20,
            minPoolSize=2,
        )
        logger.info("MongoDB async client created")
    return _client


async def check_mongo_health() -> bool:
    """Ping MongoDB and return True if reachable + authenticated."""
    global _available, _last_health_check
    try:
        client = await get_mongo_client()
        await client.admin.command("ping")
        _available = True
        _last_health_check = time.time()
        return True
    except Exception as e:
        _available = False
        _last_health_check = time.time()
        logger.warning("MongoDB health check failed: %s", e)
        return False


async def is_mongo_available() -> bool:
    """Return cached availability. Re-checks periodically on failure."""
    global _available, _last_health_check
    if _available is None:
        return await check_mongo_health()
    # If previously unavailable, retry after the retry interval
    if not _available and (time.time() - _last_health_check) >= _HEALTH_RETRY_INTERVAL:
        logger.info("Retrying MongoDB health check after previous failure")
        return await check_mongo_health()
    return _available


async def get_mongo_db():
    """
    Return the default database handle.
    Raises MongoUnavailableError if the connection can't be established.
    Periodically verifies the connection is still alive.
    """
    global _db, _last_health_check
    if _db is None:
        if not await is_mongo_available():
            raise MongoUnavailableError(
                "MongoDB is not available. Check MONGO_DB_URL credentials."
            )
        client = await get_mongo_client()
        _db = client[DATABASE_NAME]
        # Best-effort index creation (may fail on CosmosDB)
        await _ensure_indexes(_db)
        logger.info("MongoDB database '%s' ready", DATABASE_NAME)
    elif (time.time() - _last_health_check) >= _HEALTH_CHECK_INTERVAL:
        # Periodic liveness check — not on every request
        try:
            client = await get_mongo_client()
            await client.admin.command("ping")
            _last_health_check = time.time()
        except Exception:
            logger.warning("MongoDB connection lost — attempting reconnect")
            await _reset_connection()
            if not await check_mongo_health():
                raise MongoUnavailableError(
                    "MongoDB reconnection failed. Check MONGO_DB_URL credentials."
                )
            client = await get_mongo_client()
            _db = client[DATABASE_NAME]
            await _ensure_indexes(_db)
            logger.info("MongoDB reconnected to '%s'", DATABASE_NAME)
    return _db


async def _reset_connection():
    """Reset cached client and db references for reconnection."""
    global _client, _db, _available
    if _client:
        try:
            _client.close()
        except Exception:
            pass
    _client = None
    _db = None
    _available = None


async def _ensure_indexes(db):
    """
    Create indexes for the reports collection.
    Wrapped in try/except per-index because CosmosDB may not support
    all index types (e.g. text indexes).
    """
    coll = db["reports"]
    indexes = [
        ([("category", ASCENDING)], "idx_category"),
        ([("subcategory", ASCENDING)], "idx_subcategory"),
        ([("symbol", ASCENDING)], "idx_symbol"),
        ([("access_level", ASCENDING)], "idx_access_level"),
        ([("created_at", DESCENDING)], "idx_created_at"),
        (
            [("category", ASCENDING), ("subcategory", ASCENDING), ("symbol", ASCENDING)],
            "category_sub_symbol",
        ),
    ]
    for keys, name in indexes:
        try:
            await coll.create_index(keys, name=name)
        except Exception as e:
            logger.warning("Index '%s' creation skipped: %s", name, e)

    # Text index — not supported on CosmosDB
    try:
        await coll.create_index(
            [("title", "text"), ("symbol", "text"), ("tags", "text")],
            name="text_search",
        )
    except Exception as e:
        logger.warning(f"Text index not available (CosmosDB?): {e}")

    logger.info("MongoDB indexes ensured on 'reports' collection")


async def close_mongo():
    """Close the MongoDB connection on shutdown."""
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None
        logger.info("MongoDB connection closed")
