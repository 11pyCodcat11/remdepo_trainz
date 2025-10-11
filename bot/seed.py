from __future__ import annotations

import asyncio
from decimal import Decimal

from .database.engine import session_scope, init_db
from .database.models import Category, Product


async def seed():
    await init_db()
    async with session_scope() as session:
        cat = Category(name="Подвижной состав", description="Модели поездов")
        session.add(cat)
        await session.flush()
        session.add_all(
            [
                Product(
                    name="ЭД4м 0142",
                    description="Высококачественная модель электрички",
                    price=Decimal("0.00"),
                    is_popular=True,
                    category_id=cat.id,
                ),
                Product(
                    name="ЭД4-0010 (оригинальная кабина)",
                    description="Премиум модель",
                    price=Decimal("2500"),
                    is_popular=True,
                    category_id=cat.id,
                ),
            ]
        )


if __name__ == "__main__":
    asyncio.run(seed())


