from __future__ import annotations

from decimal import Decimal
from typing import Iterable, Optional, Tuple, List, Dict

from sqlalchemy import select, func, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .models import User, Category, Product, CartItem, Order, OrderItem, PurchaseHistory, ProductImage


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    from typing import Optional
    async def get_or_create(self, telegram_id: int, username: Optional[str]) -> User:
        # Try to find existing user first
        res = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
        user = res.scalar_one_or_none()
        if user is not None:
            if username and user.username != username:
                user.username = username
            return user
        # Not found: attempt to create; handle race-condition on unique constraint
        try:
            user = User(telegram_id=telegram_id, username=username)
            self.session.add(user)
            await self.session.flush()
            return user
        except IntegrityError:
            # Another concurrent request inserted the same telegram_id — fetch and return it
            await self.session.rollback()
            res = await self.session.execute(select(User).where(User.telegram_id == telegram_id))
            user = res.scalar_one()
            if username and user.username != username:
                user.username = username
            return user


class CategoryRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_active(self) -> List[Category]:
        res = await self.session.execute(select(Category).where(Category.is_active == True).order_by(Category.name))
        return list(res.scalars().all())

    async def list_with_counts(self) -> List[Tuple[Category, int]]:
        stmt = (
            select(Category, func.count(Product.id))
            .join(Product, Product.category_id == Category.id, isouter=True)
            .where(Category.is_active == True)
            .group_by(Category.id)
            .order_by(Category.name)
        )
        res = await self.session.execute(stmt)
        return [(row[0], int(row[1])) for row in res.all()]


class ProductRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_popular(self, limit: int = 10) -> List[Product]:
        res = await self.session.execute(
            select(Product)
            .where(Product.is_active == True, Product.category_id != None)
            .order_by(Product.popularity_count.desc(), Product.created_at.desc())
            .limit(limit)
        )
        return list(res.scalars().all())

    async def get(self, product_id: int) -> Optional[Product]:
        res = await self.session.execute(select(Product).where(Product.id == product_id))
        return res.scalar_one_or_none()

    async def increment_popularity(self, product_id: int) -> None:
        res = await self.session.execute(select(Product).where(Product.id == product_id))
        p = res.scalar_one_or_none()
        if p:
            p.popularity_count += 1

    async def add_extra_image(self, product_id: int, file_id: str) -> ProductImage:
        image = ProductImage(product_id=product_id, file_id=file_id)
        self.session.add(image)
        await self.session.flush()
        return image

    async def list_images(self, product_id: int) -> List[ProductImage]:
        res = await self.session.execute(select(ProductImage).where(ProductImage.product_id == product_id))
        return list(res.scalars().all())

    async def list_by_category(self, category_id: int) -> List[Product]:
        res = await self.session.execute(
            select(Product).where(Product.category_id == category_id, Product.is_active == True).order_by(Product.created_at.desc())
        )
        return list(res.scalars().all())


class CartRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, user_id: int, product_id: int, qty: int = 1) -> CartItem:
        res = await self.session.execute(
            select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        item = res.scalar_one_or_none()
        if item:
            # already exists; don't increment silently — keep 1 and let UI show message
            pass
        else:
            item = CartItem(user_id=user_id, product_id=product_id, quantity=qty)
            self.session.add(item)
        await self.session.flush()
        return item

    async def remove(self, user_id: int, product_id: int) -> None:
        await self.session.execute(
            delete(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )

    async def list_items(self, user_id: int) -> List[CartItem]:
        res = await self.session.execute(select(CartItem).where(CartItem.user_id == user_id))
        return list(res.scalars().all())

    async def clear(self, user_id: int) -> None:
        await self.session.execute(delete(CartItem).where(CartItem.user_id == user_id))

    async def exists(self, user_id: int, product_id: int) -> bool:
        res = await self.session.execute(
            select(CartItem.id).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        return res.scalar_one_or_none() is not None


class OrderRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self, order_id: int) -> Optional[Order]:
        res = await self.session.execute(select(Order).where(Order.id == order_id))
        return res.scalar_one_or_none()

    async def get_by_payment_id(self, payment_id: str) -> Optional[Order]:
        res = await self.session.execute(select(Order).where(Order.payment_id == payment_id))
        return res.scalar_one_or_none()

    async def get_pending_orders(self) -> List[Order]:
        res = await self.session.execute(select(Order).where(Order.status == "pending"))
        return list(res.scalars().all())

    async def create_from_cart(self, user_id: int, items: Iterable[CartItem]) -> Order:
        total = Decimal("0.00")
        order = Order(user_id=user_id, total_amount=total, status="pending")
        self.session.add(order)
        await self.session.flush()

        product_ids = [item.product_id for item in items]
        if product_ids:
            res = await self.session.execute(select(Product.id, Product.price).where(Product.id.in_(product_ids)))
            id_to_price = {pid: price for pid, price in res.all()}
        else:
            id_to_price = {}

        for item in items:
            price = id_to_price.get(item.product_id, Decimal("0.00"))
            total += price * item.quantity
            self.session.add(
                OrderItem(order_id=order.id, product_id=item.product_id, quantity=item.quantity, price=price)
            )
        order.total_amount = total
        await self.session.flush()
        return order

    async def set_status(self, order_id: int, status: str, payment_id: Optional[str] = None) -> None:
        res = await self.session.execute(select(Order).where(Order.id == order_id))
        order = res.scalar_one()
        order.status = status
        if payment_id:
            order.payment_id = payment_id

    async def list_by_user(self, user_id: int) -> List[Order]:
        res = await self.session.execute(select(Order).where(Order.user_id == user_id).order_by(Order.created_at.desc()))
        return list(res.scalars().all())


class PurchaseRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add_from_order(self, order_or_id: "OrderOrId") -> None:
        # Avoid async lazy loading by fetching order items explicitly
        if isinstance(order_or_id, Order):
            order_id = order_or_id.id
            user_id = order_or_id.user_id
        else:
            order_id = int(order_or_id)
            res = await self.session.execute(select(Order).where(Order.id == order_id))
            order_obj = res.scalar_one()
            user_id = order_obj.user_id
        res_items = await self.session.execute(select(OrderItem).where(OrderItem.order_id == order_id))
        for item in res_items.scalars().all():
            self.session.add(PurchaseHistory(user_id=user_id, product_id=item.product_id, price=item.price))

    async def list_by_user(self, user_id: int) -> List[PurchaseHistory]:
        # Return purchases only for existing products to avoid UI mismatches
        stmt = (
            select(PurchaseHistory)
            .join(Product, PurchaseHistory.product_id == Product.id)
            .where(PurchaseHistory.user_id == user_id)
            .order_by(PurchaseHistory.purchased_at.desc())
        )
        res = await self.session.execute(stmt)
        return list(res.scalars().all())

    async def exists(self, user_id: int, product_id: int) -> bool:
        """Check if user already purchased the given product."""
        res = await self.session.execute(
            select(PurchaseHistory.id).where(
                PurchaseHistory.user_id == user_id, PurchaseHistory.product_id == product_id
            )
        )
        return res.scalar_one_or_none() is not None


