"""
Database session management and async engine configuration.

Single source of truth for the DB connection — imported by the FastAPI app,
dependencies, and alembic/env.py for migrations.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

is_sqlite = settings.database_url.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Async Engine Configuration
engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True,
    pool_pre_ping=not is_sqlite,
    connect_args=connect_args,
)

# Async Session Factory
async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency — yields a request-scoped AsyncSession with rollback on error."""
    async with async_session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
