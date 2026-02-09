"""
Firebase Authentication Middleware

Validates Firebase ID tokens and extracts user UID for authenticated endpoints.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from common.config import settings
from common.logging import get_logger

logger = get_logger(__name__)

# HTTP Bearer token security scheme
security = HTTPBearer(auto_error=True)


async def get_current_uid(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Verify Firebase ID token and extract UID.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        str: Firebase user UID
        
    Raises:
        HTTPException: 401 if token is invalid or expired
    """
    try:
        token = credentials.credentials
        
        # Import firebase_admin only when needed (lazy loading)
        from firebase_admin import auth, credentials as fb_credentials, initialize_app
        import firebase_admin
        
        # Initialize Firebase Admin SDK if not already done
        if not firebase_admin._apps:
            if settings.FIREBASE_PROJECT_ID:
                # Use Application Default Credentials (for production)
                # Requires GOOGLE_APPLICATION_CREDENTIALS env var
                try:
                    cred = fb_credentials.ApplicationDefault()
                    initialize_app(cred, {
                        'projectId': settings.FIREBASE_PROJECT_ID
                    })
                    logger.info("Firebase Admin SDK initialized with project credentials")
                except Exception as init_error:
                    logger.warning(f"Firebase init with ADC failed: {init_error}, using project ID only")
                    initialize_app(options={'projectId': settings.FIREBASE_PROJECT_ID})
            else:
                # Development mode: no Firebase project configured
                logger.warning("FIREBASE_PROJECT_ID not set - authentication disabled in dev mode")
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Authentication service not configured"
                )
        
        # Verify the ID token
        decoded_token = auth.verify_id_token(token)
        uid = decoded_token.get("uid")
        
        if not uid:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing UID",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Authenticated user: {uid}")
        return uid
        
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Authentication failed: {type(e).__name__}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Optional: Dependency for routes that should work with or without auth
async def get_optional_uid(
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False))
) -> str | None:
    """
    Optional authentication - returns UID if valid token provided, None otherwise.
    Useful for endpoints that behave differently for authenticated vs anonymous users.
    """
    if credentials is None:
        return None
    
    try:
        return await get_current_uid(credentials)
    except HTTPException:
        return None
