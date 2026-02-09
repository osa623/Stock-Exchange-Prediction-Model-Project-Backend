"""
Analysis Router

Provides endpoints for stock analysis with premium/free access control.
"""

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from sqlalchemy.orm import Session
import re

from db.session import get_db
from app.middleware.firebase_auth import get_current_uid
from modules.users.service import get_or_create_user
from modules.entitlements.service import can_access
from common.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()

# Valid stock symbol pattern: 1-5 uppercase letters
SYMBOL_PATTERN = re.compile(r"^[A-Z]{1,5}$")


def validate_stock_symbol(symbol: str) -> str:
    """
    Validate and sanitize stock symbol input.
    
    Args:
        symbol: Raw stock symbol from request
        
    Returns:
        Sanitized uppercase symbol
        
    Raises:
        HTTPException: If symbol format is invalid
    """
    # Normalize: strip whitespace, uppercase
    cleaned = symbol.strip().upper()
    
    # Validate format
    if not SYMBOL_PATTERN.match(cleaned):
        logger.warning(f"Invalid stock symbol attempted: {symbol}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid stock symbol format: '{symbol}'. "
                   f"Symbol must be 1-5 uppercase letters (e.g., AAPL, MSFT, TSLA)"
        )
    
    return cleaned


@router.get("/stocks/{symbol}")
def stock_details(
    symbol: str = Path(
        ...,
        description="Stock ticker symbol (e.g., AAPL, MSFT)",
        min_length=1,
        max_length=5,
        examples=["AAPL", "MSFT", "TSLA"]
    ),
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """
    Get stock details and analysis.
    
    - **Free users**: Access basic stock details
    - **Premium users**: Access full valuations, ratios, and cashflow analysis
    """
    # Validate and sanitize input
    validated_symbol = validate_stock_symbol(symbol)
    
    # Get or create user
    user = get_or_create_user(db, uid)
    
    logger.info(
        f"Stock details requested: {validated_symbol}",
        extra={"user_id": uid, "symbol": validated_symbol}
    )
    
    # Import analysis functions (lazy import to avoid circular deps)
    try:
        from modules.analysis.fundamental.runner import (
            get_basic_stock_data,
            get_full_fundamental_data
        )
    except ImportError as e:
        logger.error(f"Analysis module import failed: {e}")
        raise HTTPException(
            status_code=503,
            detail="Analysis service temporarily unavailable"
        )
    
    # Check access levels
    has_basic_access = can_access(user, "stocks:details")
    has_premium_access = can_access(user, "stocks:valuation")
    
    # Premium access path
    if has_premium_access:
        try:
            data = get_full_fundamental_data(validated_symbol)
            return {
                "symbol": validated_symbol,
                "access_level": "premium",
                **data
            }
        except Exception as e:
            logger.exception(f"Failed to get full data for {validated_symbol}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve data for {validated_symbol}"
            )
    
    # Free access path
    if has_basic_access:
        try:
            basic = get_basic_stock_data(validated_symbol)
            return {
                "symbol": validated_symbol,
                "access_level": "free",
                **basic,
                "upgrade_message": "Upgrade to premium to view full valuations, ratios, and cashflow analysis"
            }
        except Exception as e:
            logger.exception(f"Failed to get basic data for {validated_symbol}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to retrieve data for {validated_symbol}"
            )
    
    # No access
    raise HTTPException(
        status_code=403,
        detail="Access denied. Please upgrade your subscription."
    )


@router.get("/stocks")
def list_stocks(
    limit: int = Query(default=20, ge=1, le=100, description="Number of stocks to return"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
    uid: str = Depends(get_current_uid),
):
    """
    List available stocks for analysis.
    
    Returns a paginated list of stock symbols.
    """
    user = get_or_create_user(db, uid)
    
    # TODO: Implement stock listing from database or external API
    # This is a placeholder response
    return {
        "stocks": [],
        "limit": limit,
        "offset": offset,
        "total": 0,
        "message": "Stock listing not yet implemented"
    }
