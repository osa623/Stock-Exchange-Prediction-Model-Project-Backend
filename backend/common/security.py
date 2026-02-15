"""
PIN Security Utilities

Provides bcrypt-based hashing and verification for 6-digit PINs,
with strict input validation.
"""

import re
import bcrypt

_PIN_PATTERN = re.compile(r"^\d{6}$")


def _validate_pin(pin: str) -> None:
    """Raise ValueError if *pin* is not exactly 6 digits."""
    if not isinstance(pin, str) or not _PIN_PATTERN.match(pin):
        raise ValueError("PIN must be exactly 6 digits")


def hash_pin(pin: str) -> str:
    """
    Hash a 6-digit PIN using bcrypt.

    Returns the bcrypt hash string (UTF-8).
    Raises ValueError for invalid PINs.
    """
    _validate_pin(pin)
    hashed = bcrypt.hashpw(pin.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_pin(pin: str, pin_hash: str) -> bool:
    """
    Verify a PIN against its bcrypt hash using constant-time comparison.

    Returns True if the PIN matches, False otherwise.
    Raises ValueError for invalid PIN format.
    """
    _validate_pin(pin)
    return bcrypt.checkpw(pin.encode("utf-8"), pin_hash.encode("utf-8"))
