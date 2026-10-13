"""Security utilities: input sanitization, user context isolation, and password/token hashing."""
import hashlib
import hmac
import html
import re
from typing import Optional
from fastapi import Header, HTTPException, status

from app.core.config import settings


USER_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{3,64}$")


def sanitize_text(value: Optional[str], max_length: int = 500) -> Optional[str]:
    """Escape HTML characters and strip control characters to prevent XSS and log injection."""
    if value is None:
        return None
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", value).strip()
    if len(cleaned) > max_length:
        raise ValueError(f"Input exceeds maximum allowed length of {max_length} characters.")
    return html.escape(cleaned, quote=True)


def hash_auth_secret(secret: str) -> str:
    """Derive a salted HMAC-SHA256 digest for authentication reference storage."""
    return hmac.new(
        settings.secret_key.encode("utf-8"),
        secret.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def get_current_user_id(
    x_user_id: Optional[str] = Header(default="default_chef", alias="X-User-ID"),
    x_access_token: Optional[str] = Header(default=None, alias="X-Access-Token"),
) -> str:
    """
    Resolve and validate the active user scope.
    Enforces strict format validation and prevents cross-user access when a restricted user ID is targeted.
    """
    user_id = (x_user_id or "default_chef").strip()
    if not USER_ID_PATTERN.match(user_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid X-User-ID header format. Use 3-64 alphanumeric, underscore, or hyphen characters.",
        )
    # If accessing a protected private user namespace (e.g. private_*), require matching token
    if user_id.startswith("private_"):
        expected_token = f"token_{user_id}"
        if not x_access_token or not hmac.compare_digest(x_access_token, expected_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: invalid or missing credentials for this private user workspace.",
            )
    return user_id
