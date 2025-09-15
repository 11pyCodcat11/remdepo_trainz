from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

DATABASE_URL = "sqlite+aiosqlite:///{}".format("db_catalog.sqlite3")

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)
Base = declarative_base()