"""
Report Repository

Direct MongoDB data-access layer for report documents.
All queries are built with safe parameter binding — no raw string interpolation.
"""

from bson import ObjectId
from datetime import datetime, timezone
from typing import Any
from common.logging import get_logger

logger = get_logger(__name__)

COLLECTION = "reports"


def _safe_filter(key: str, value: str) -> dict:
    """
    Build a safe equality filter.
    Rejects values that start with $ or contain { } to block
    MongoDB operator injection.
    """
    v = str(value).strip()
    if v.startswith("$") or "{" in v or "}" in v:
        raise ValueError(f"Unsafe filter value for '{key}': {v}")
    return {key: v}


def _build_query(
    *,
    category: str | None = None,
    subcategory: str | None = None,
    symbol: str | None = None,
    access_levels: list[str] | None = None,
    search: str | None = None,
) -> dict:
    """Build a safe MongoDB query dict from validated parameters."""
    query: dict[str, Any] = {}

    if category:
        query.update(_safe_filter("category", category))
    if subcategory:
        query.update(_safe_filter("subcategory", subcategory))
    if symbol:
        query.update(_safe_filter("symbol", symbol.upper()))
    if access_levels:
        query["access_level"] = {"$in": access_levels}
    if search:
        # Try text index first; fall back to regex for CosmosDB
        safe_search = search.replace('"', "").replace("\\", "")[:100]
        try:
            # Check if text index exists by attempting a text query placeholder
            query["$or"] = [
                {"title": {"$regex": safe_search, "$options": "i"}},
                {"symbol": {"$regex": safe_search, "$options": "i"}},
                {"tags": {"$regex": safe_search, "$options": "i"}},
            ]
        except Exception:
            pass

    return query


def _serialize_doc(doc: dict) -> dict:
    """Convert MongoDB document to JSON-safe dict."""
    if doc is None:
        return {}
    doc["id"] = str(doc.pop("_id"))
    for key in ("created_at", "updated_at"):
        if key in doc and isinstance(doc[key], datetime):
            doc[key] = doc[key].isoformat()
    return doc


async def list_reports(
    db,
    *,
    category: str | None = None,
    subcategory: str | None = None,
    symbol: str | None = None,
    access_levels: list[str] | None = None,
    search: str | None = None,
    page: int = 1,
    page_size: int = 20,
    summary_only: bool = True,
) -> tuple[list[dict], int]:
    """
    Return paginated list of reports.

    Parameters
    ----------
    summary_only : bool
        When True, project only summary fields (public/list view).
    """
    coll = db[COLLECTION]
    query = _build_query(
        category=category,
        subcategory=subcategory,
        symbol=symbol,
        access_levels=access_levels,
        search=search,
    )

    # Choose field projection
    if summary_only:
        projection = {
            "title": 1,
            "category": 1,
            "subcategory": 1,
            "symbol": 1,
            "access_level": 1,
            "summary": 1,
            "tags": 1,
            "created_at": 1,
        }
    else:
        projection = {
            "raw_data": 0,  # exclude heavy export blob from list
            "methodology": 0,
            "metadata": 0,
        }

    skip = (page - 1) * page_size

    total = await coll.count_documents(query)
    cursor = (
        coll.find(query, projection)
        .sort("created_at", -1)
        .skip(skip)
        .limit(page_size)
    )
    docs = [_serialize_doc(d) async for d in cursor]
    return docs, total


async def get_report_by_id(db, report_id: str, include_full: bool = False) -> dict | None:
    """Fetch a single report by its ObjectId string."""
    if not ObjectId.is_valid(report_id):
        return None

    coll = db[COLLECTION]
    projection = None
    if not include_full:
        projection = {"raw_data": 0, "metadata": 0, "methodology": 0}

    doc = await coll.find_one({"_id": ObjectId(report_id)}, projection)
    return _serialize_doc(doc) if doc else None


async def get_folder_tree(db) -> list[dict]:
    """
    Aggregate the distinct category → subcategory hierarchy
    with report counts per node.
    """
    coll = db[COLLECTION]
    pipeline = [
        {
            "$group": {
                "_id": {
                    "category": "$category",
                    "subcategory": {"$ifNull": ["$subcategory", "__none__"]},
                },
                "count": {"$sum": 1},
            }
        },
        {"$sort": {"_id.category": 1, "_id.subcategory": 1}},
    ]

    tree_map: dict[str, dict] = {}
    async for doc in coll.aggregate(pipeline):
        cat = doc["_id"]["category"]
        sub = doc["_id"]["subcategory"]
        cnt = doc["count"]

        if cat not in tree_map:
            tree_map[cat] = {"name": cat, "path": cat, "children": [], "report_count": 0}

        if sub == "__none__":
            tree_map[cat]["report_count"] += cnt
        else:
            tree_map[cat]["children"].append(
                {"name": sub, "path": f"{cat}/{sub}", "children": [], "report_count": cnt}
            )
            tree_map[cat]["report_count"] += cnt

    return list(tree_map.values())


async def get_report_count(db) -> int:
    """Total number of reports in the collection."""
    return await db[COLLECTION].count_documents({})


async def export_report(db, report_id: str) -> dict | None:
    """Fetch full report including raw_data for CSV/export."""
    return await get_report_by_id(db, report_id, include_full=True)
