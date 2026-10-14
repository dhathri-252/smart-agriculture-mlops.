"""Shared FastAPI dependencies."""

from typing import Optional

from fastapi import Header

from api import db
from api.security import decode_token, extract_bearer_token


async def optional_user(
    authorization: Optional[str] = Header(None),
) -> Optional[dict]:
    """Resolve the logged-in user from the Authorization header.

    Returns ``None`` for anonymous or invalid tokens — endpoints decide
    whether anonymous access is allowed.
    """
    token = extract_bearer_token(authorization)
    if not token:
        return None
    claims = decode_token(token)
    if not claims:
        return None
    user_id = claims.get("sub")
    if not isinstance(user_id, int):
        return None
    user = db.get_user_by_id(user_id)
    if user is None:
        return None
    user.pop("password_hash", None)
    return user


async def required_user(
    authorization: Optional[str] = Header(None),
) -> dict:
    user = await optional_user(authorization)
    if user is None:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Provide a valid Authorization: Bearer <token>.",
        )
    return user
