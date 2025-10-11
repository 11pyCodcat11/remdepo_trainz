from __future__ import annotations

from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from ..config import DB_DSN


class Base(DeclarativeBase):
    pass


engine = create_async_engine(DB_DSN, future=True, echo=False)
async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    # Import models inside to avoid circular imports
    from . import models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Auto-add missing columns for backward compatibility
        try:
            # Only works for SQLite
            await conn.exec_driver_sql(
                "ALTER TABLE products ADD COLUMN download_url TEXT"
            )
        except Exception:
            # Column may already exist; ignore errors
            pass


@asynccontextmanager
async def session_scope():
    session: AsyncSession = async_session_maker()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


