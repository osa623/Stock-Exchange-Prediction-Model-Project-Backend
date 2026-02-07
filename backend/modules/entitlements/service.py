from db.models import User

def is_premium(user: User) -> bool:
    return bool(user.subscription and user.subscription.status == "premium")

def can_access(user: User, feature: str) -> bool:
    """
    Central access rules for Phase 1.

    feature examples:
      - "stocks:details"
      - "stocks:valuation"
      - "portfolio:full"
      - "sectors:all"
    """

    # Free users can see basic stock details
    if feature == "stocks:details":
        return True

    # Everything else premium-only in Phase 1
    return is_premium(user)
