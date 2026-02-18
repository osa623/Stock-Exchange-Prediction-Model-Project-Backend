"""
Test pymongo SCRAM-SHA-256 with CosmosDB — debug handshake + workarounds.
"""
import asyncio
import hashlib
import hmac
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from common.config import settings

# Enable full pymongo debug logging to see SCRAM conversation
logging.basicConfig(level=logging.DEBUG)
logging.getLogger("pymongo").setLevel(logging.DEBUG)


async def try_standard():
    """Standard connection — expect failure (baseline)."""
    print("\n=== Standard pymongo ===")
    try:
        c = AsyncIOMotorClient(settings.MONGO_DB_URL, serverSelectionTimeoutMS=10000)
        db = c["stock_reports"]
        names = await db.list_collection_names()
        print(f"✓ {names}")
        c.close()
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {str(e)[:100]}")
        return False


async def try_patched():
    """
    Monkey-patch pymongo SCRAM to use password_digest (md5) for SHA-256.
    Some CosmosDB implementations store the key this way.
    """
    print("\n=== Patched: md5 digest for SCRAM-SHA-256 ===")
    try:
        import pymongo.auth as auth_mod

        # Save original
        orig_scram = auth_mod._authenticate_scram

        def _password_digest(username, password):
            """md5(username:mongo:password) — the SHA-1 style digest."""
            if not isinstance(password, str):
                raise TypeError("password must be a string")
            md5hash = hashlib.md5()
            data = f"{username}:mongo:{password}"
            md5hash.update(data.encode("utf-8"))
            return md5hash.hexdigest()

        def patched_scram(credentials, conn, mechanism="SCRAM-SHA-256"):
            """Override: use md5 digest even for SHA-256."""
            # Intercept and replace password with md5 digest
            source = credentials.source
            username = credentials.username
            password = credentials.password

            # Create modified credentials with md5-digested password
            digest = _password_digest(username, password)
            from pymongo.auth import _build_credentials_tuple
            new_creds = _build_credentials_tuple(
                mechanism, source, username, digest, None, None
            )
            return orig_scram(new_creds, conn, mechanism)

        # This likely won't work as-is, but let's see
        # auth_mod._authenticate_scram = patched_scram

        # Instead, try direct approach: connect with the md5-digested password in URL
        import urllib.parse
        parsed = urllib.parse.urlparse(settings.MONGO_DB_URL)
        username = urllib.parse.unquote(parsed.username)
        password = urllib.parse.unquote(parsed.password)

        # Compute md5 digest
        digest = _password_digest(username, password)
        print(f"  md5 digest: {digest}")

        # Build URL with digest as password
        encoded_digest = urllib.parse.quote_plus(digest)
        new_url = settings.MONGO_DB_URL.replace(
            f":{urllib.parse.quote_plus(password)}@",
            f":{encoded_digest}@"
        )

        c = AsyncIOMotorClient(new_url, serverSelectionTimeoutMS=10000)
        db = c["stock_reports"]
        names = await db.list_collection_names()
        print(f"✓ {names}")
        c.close()
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {str(e)[:100]}")
        return False


async def try_no_saslprep():
    """
    Disable saslprep by monkey-patching, in case Python's stringprep
    behaves differently from Node.js saslprep.
    """
    print("\n=== No saslprep ===")
    try:
        import pymongo.auth as auth_mod
        # Monkey-patch saslprep to be a no-op
        if hasattr(auth_mod, '_saslprep'):
            orig = auth_mod._saslprep
            auth_mod._saslprep = lambda s: s
            print("  saslprep disabled")

        c = AsyncIOMotorClient(settings.MONGO_DB_URL, serverSelectionTimeoutMS=10000)
        db = c["stock_reports"]
        names = await db.list_collection_names()
        print(f"✓ {names}")
        c.close()

        if hasattr(auth_mod, '_saslprep'):
            auth_mod._saslprep = orig
        return True
    except Exception as e:
        print(f"✗ {type(e).__name__}: {str(e)[:100]}")
        if hasattr(auth_mod, '_saslprep'):
            auth_mod._saslprep = orig
        return False


async def main():
    # Try each approach
    if await try_standard():
        return
    if await try_no_saslprep():
        return
    if await try_patched():
        return

    print("\n❌ All approaches failed.")
    print("The CosmosDB SCRAM-SHA-256 implementation differs from pymongo.")


if __name__ == "__main__":
    asyncio.run(main())
