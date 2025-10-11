from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from ..database.repository import CartRepo, ProductRepo


class CartService:
    def __init__(self, session: AsyncSession):
        self.cart_repo = CartRepo(session)
        self.product_repo = ProductRepo(session)

    async def add(self, user_id: int, product_id: int, qty: int = 1):
        return await self.cart_repo.add(user_id, product_id, qty)

    async def remove(self, user_id: int, product_id: int):
        await self.cart_repo.remove(user_id, product_id)

    async def list_with_total(self, user_id: int):
        items = await self.cart_repo.list_items(user_id)
        total = Decimal("0.00")
        result = []
        for it in items:
            # Avoid async lazy loading (MissingGreenlet): fetch product explicitly
            product = await self.product_repo.get(it.product_id)
            if not product:
                continue
            result.append((it.product_id, product.name, it.quantity, product.price))
            total += product.price * it.quantity
        return result, total


