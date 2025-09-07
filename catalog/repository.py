from typing import List, Optional
from sqlalchemy import select
from .models import Product, Category, User
from .sqlalchemy_base import engine, Base, AsyncSessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from .utils import make_password, check_password, hash_password, verify_password

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_if_empty():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).limit(1))
        if result.scalar_one_or_none() is None:
            demo = [
                Product(slug="vagony-tavriya", title="Вагоны Таврия", price_rub=0, is_free=True,
                        category=Category.ROLLING_STOCK, badge="Бесплатно", popularity=50),
                Product(slug="ed4m-0142", title="ЭД4м 0142", price_rub=0, is_free=True,
                        category=Category.ROLLING_STOCK, badge="Бесплатно", popularity=70),
                Product(slug="volhovstroi-pikalevo", title="Волховстрой–Пикалево", price_rub=0, is_free=True,
                        category=Category.MAPS, badge="Бесплатно", popularity=40),
                Product(slug="paveleckoe", title="Павелецкое направление", price_rub=2500, is_free=False,
                        category=Category.SCENARIOS, popularity=120),
                Product(slug="ed4-0010-original", title="ЭД4-0010 (с оригинальной кабиной)", price_rub=2500,
                        is_free=False, category=Category.ROLLING_STOCK, popularity=90),
            ]
            session.add_all(demo)
            await session.commit()


async def list_products(limit: int = 24, order_by: str = None):
    async with AsyncSessionLocal() as session:
        stmt = select(Product).options(joinedload(Product.photos))
        if order_by == "popularity":
            stmt = stmt.order_by(Product.popularity.desc())
        if limit:
            stmt = stmt.limit(limit)
        res = await session.execute(stmt)
        return res.unique().scalars().all()


async def list_products_by_category(category: Category):
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Product)
            .options(joinedload(Product.photos))
            .where(Product.category == category)
        )
        res = await session.execute(stmt)
        return res.unique().scalars().all()



async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, username: str, email: str, password: str) -> User:
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, username: str, password: str) -> Optional[User]:
    user = await get_user_by_username(session, username)
    if user and verify_password(password, user.password_hash):
        return user
    return None