"""Asynchronous SQLModel database infrastructure."""

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Provide a request-scoped async database session."""
    async with async_session_maker() as session:
        yield session


async def close_database() -> None:
    """Release pooled connections when the application shuts down."""
    await engine.dispose()
