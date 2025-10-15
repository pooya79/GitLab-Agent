from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from db.models import User


async def get_user_by_identifier(
    session: AsyncSession,
    identifier: str,
) -> Optional[User]:
    """
    Return the User matching the given identifier, which may be either
    a username or an email address, or None if not found.
    """
    stmt = select(User).where(
        or_(
            User.username == identifier,
            User.email == identifier,
        )
    )
    result = await session.execute(stmt)
    return result.scalars().first()
