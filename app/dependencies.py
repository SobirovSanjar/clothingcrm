"""Shared FastAPI dependencies (current user lookup)."""
from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from .database import get_db
from .models import User


async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
) -> User | None:
    """Return the logged-in User based on the session cookie, or None."""
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return await db.get(User, user_id)
