"""
Report Service

Business logic layer that enforces tiered access control:
  - Public:      summary fields only, max 10 per page, max 50 total depth
  - Registered:  detail fields, 50 per page
  - Premium:     full data + export
"""

from db.mongo import get_mongo_db, MongoUnavailableError
from modules.reports import repository
from common.cache import (
    report_list_cache,
    report_detail_cache,
    folder_tree_cache,
    make_cache_key,
)
from common.logging import get_logger

logger = get_logger(__name__)

# ── Access-tier constants ────────────────────────────────────────────────

PUBLIC_MAX_PAGE_SIZE = 10
PUBLIC_MAX_DEPTH = 50       # max offset reachable
REGISTERED_MAX_PAGE_SIZE = 50
PREMIUM_MAX_PAGE_SIZE = 100

# Empty result templates for when MongoDB is unavailable
_EMPTY_LIST = {"reports": [], "total": 0, "page": 1, "page_size": 0, "total_pages": 0, "mongo_status": "unavailable"}
_EMPTY_TREE = {"tree": [], "total_reports": 0, "mongo_status": "unavailable"}


# ── Public (no auth) ────────────────────────────────────────────────────

async def list_reports_public(
    *,
    category: str | None = None,
    subcategory: str | None = None,
    symbol: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 10,
):
    """Public endpoint — summary only, strict limits."""
    page_size = min(page_size, PUBLIC_MAX_PAGE_SIZE)
    if (page - 1) * page_size >= PUBLIC_MAX_DEPTH:
        return {"reports": [], "total": 0, "page": page, "page_size": page_size, "total_pages": 0}

    cache_key = make_cache_key(
        "pub_list", category=category, subcategory=subcategory,
        symbol=symbol, search=search, page=page, page_size=page_size,
    )
    cached = await report_list_cache.get(cache_key)
    if cached:
        return cached

    try:
        db = await get_mongo_db()
    except MongoUnavailableError:
        logger.warning("MongoDB unavailable for public report list")
        return {**_EMPTY_LIST, "page": page, "page_size": page_size}

    docs, total = await repository.list_reports(
        db,
        category=category,
        subcategory=subcategory,
        symbol=symbol,
        access_levels=["public"],
        search=search,
        page=page,
        page_size=page_size,
        summary_only=True,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    result = {
        "reports": docs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
    await report_list_cache.set(cache_key, result)
    return result


# ── Registered (auth required) ──────────────────────────────────────────

async def list_reports_registered(
    *,
    category: str | None = None,
    subcategory: str | None = None,
    symbol: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """Registered users — detail fields, higher limits."""
    page_size = min(page_size, REGISTERED_MAX_PAGE_SIZE)

    cache_key = make_cache_key(
        "reg_list", category=category, subcategory=subcategory,
        symbol=symbol, search=search, page=page, page_size=page_size,
    )
    cached = await report_list_cache.get(cache_key)
    if cached:
        return cached

    try:
        db = await get_mongo_db()
    except MongoUnavailableError:
        logger.warning("MongoDB unavailable for registered report list")
        return {**_EMPTY_LIST, "page": page, "page_size": page_size}

    docs, total = await repository.list_reports(
        db,
        category=category,
        subcategory=subcategory,
        symbol=symbol,
        access_levels=["public", "registered"],
        search=search,
        page=page,
        page_size=page_size,
        summary_only=False,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    result = {
        "reports": docs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
    await report_list_cache.set(cache_key, result)
    return result


async def get_report_detail(report_id: str):
    """Registered users — single report with data (no raw_data)."""
    cache_key = make_cache_key("reg_detail", report_id=report_id)
    cached = await report_detail_cache.get(cache_key)
    if cached:
        return cached

    try:
        db = await get_mongo_db()
    except MongoUnavailableError:
        return None

    doc = await repository.get_report_by_id(db, report_id, include_full=False)
    if doc:
        await report_detail_cache.set(cache_key, doc)
    return doc


# ── Premium (auth + subscription) ────────────────────────────────────────

async def list_reports_premium(
    *,
    category: str | None = None,
    subcategory: str | None = None,
    symbol: str | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
):
    """Premium users — all access levels, highest limits."""
    page_size = min(page_size, PREMIUM_MAX_PAGE_SIZE)

    cache_key = make_cache_key(
        "prem_list", category=category, subcategory=subcategory,
        symbol=symbol, search=search, page=page, page_size=page_size,
    )
    cached = await report_list_cache.get(cache_key)
    if cached:
        return cached

    try:
        db = await get_mongo_db()
    except MongoUnavailableError:
        logger.warning("MongoDB unavailable for premium report list")
        return {**_EMPTY_LIST, "page": page, "page_size": page_size}

    docs, total = await repository.list_reports(
        db,
        category=category,
        subcategory=subcategory,
        symbol=symbol,
        access_levels=["public", "registered", "premium"],
        search=search,
        page=page,
        page_size=page_size,
        summary_only=False,
    )
    total_pages = (total + page_size - 1) // page_size if total else 0
    result = {
        "reports": docs,
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": total_pages,
    }
    await report_list_cache.set(cache_key, result)
    return result


async def get_report_full(report_id: str):
    """Premium users — full report including raw_data and metadata."""
    cache_key = make_cache_key("prem_full", report_id=report_id)
    cached = await report_detail_cache.get(cache_key)
    if cached:
        return cached

    try:
        db = await get_mongo_db()
    except MongoUnavailableError:
        return None

    doc = await repository.get_report_by_id(db, report_id, include_full=True)
    if doc:
        await report_detail_cache.set(cache_key, doc)
    return doc


async def export_report(report_id: str):
    """Premium export — returns full doc for CSV/JSON download."""
    try:
        db = await get_mongo_db()
    except MongoUnavailableError:
        return None
    return await repository.export_report(db, report_id)


# ── Shared ───────────────────────────────────────────────────────────────

async def get_folder_tree():
    """Folder tree — cached, available to all tiers."""
    cache_key = "folder_tree_v1"
    cached = await folder_tree_cache.get(cache_key)
    if cached:
        return cached

    try:
        db = await get_mongo_db()
    except MongoUnavailableError:
        logger.warning("MongoDB unavailable for folder tree")
        return _EMPTY_TREE

    tree = await repository.get_folder_tree(db)
    total = await repository.get_report_count(db)
    result = {"tree": tree, "total_reports": total}
    await folder_tree_cache.set(cache_key, result)
    return result
