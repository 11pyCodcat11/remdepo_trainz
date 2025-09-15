from typing import List, Optional
from sqlalchemy import select
from .models import Product, Category, User, Cart, CartItem, ProductPhoto, Purchase
from .sqlalchemy_base import engine, Base, AsyncSessionLocal
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
# Импорты из utils теперь делаются локально в функциях

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def seed_if_empty():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(Product).limit(1))
        if result.scalar_one_or_none() is None:
            # Создаем демо товары
            products = [
                Product(
                    slug="vagony-tavriya", 
                    title="Вагоны Таврия", 
                    subtitle="Качественные пассажирские вагоны",
                    price_rub=0, 
                    is_free=True,
                    category=Category.ROLLING_STOCK, 
                    badge="Бесплатно", 
                    popularity=50,
                    blurb="Высокодетализированные пассажирские вагоны Таврия для Train Simulator. Включает в себя полный набор текстур и звуков."
                ),
                Product(
                    slug="ed4m-0142", 
                    title="ЭД4м 0142", 
                    subtitle="Электричка с оригинальными текстурами",
                    price_rub=0, 
                    is_free=True,
                    category=Category.ROLLING_STOCK, 
                    badge="Бесплатно", 
                    popularity=70,
                    blurb="ЭД4м 0142 скрипт реал - Своя кабина с оригинальными текстурами - В кабине расставлены вещи бригады - На лобовом стекле есть грязь и трещены - Свой скрипт."
                ),
                Product(
                    slug="volhovstroi-pikalevo", 
                    title="Волховстрой–Пикалево", 
                    subtitle="Реалистичный маршрут по России",
                    price_rub=0, 
                    is_free=True,
                    category=Category.MAPS, 
                    badge="Бесплатно", 
                    popularity=40,
                    blurb="Детализированный маршрут Волховстрой-Пикалево с реалистичными пейзажами российской природы."
                ),
                Product(
                    slug="paveleckoe", 
                    title="Павелецкое направление", 
                    subtitle="Сценарии для Павелецкого направления",
                    price_rub=2500, 
                    is_free=False,
                    category=Category.SCENARIOS, 
                    popularity=120,
                    blurb="Набор реалистичных сценариев для Павелецкого направления с подробными инструкциями и заданиями."
                ),
                Product(
                    slug="ed4-0010-original", 
                    title="ЭД4-0010 (с оригинальной кабиной)", 
                    subtitle="Премиум модель электрички",
                    price_rub=2500,
                    is_free=False, 
                    category=Category.ROLLING_STOCK, 
                    popularity=90,
                    blurb="Высококачественная модель ЭД4-0010 с полностью оригинальной кабиной, реалистичными звуками и анимацией."
                ),
            ]
            
            session.add_all(products)
            await session.flush()  # Чтобы получить ID товаров
            
            # Добавляем фотографии к товарам
            photos = [
                # Для Вагонов Таврия
                ProductPhoto(product_id=products[0].id, file_path="/static/images/tavria_vahons.jpg", is_main=True, order=0),
                
                # Для ЭД4м 0142 - добавим несколько фото для демонстрации галереи
                ProductPhoto(product_id=products[1].id, file_path="/static/images/ed4m0142.jpg", is_main=True, order=0),
                ProductPhoto(product_id=products[1].id, file_path="/static/images/cabina.jpg", is_main=False, order=1),
                ProductPhoto(product_id=products[1].id, file_path="/static/images/poejd.jpg", is_main=False, order=2),
                ProductPhoto(product_id=products[1].id, file_path="/static/images/poejd2.jpg", is_main=False, order=3),
                
                # Для Волховстрой-Пикалево
                ProductPhoto(product_id=products[2].id, file_path="/static/images/oblojka.jpg", is_main=True, order=0),
                
                # Для Павелецкого направления
                ProductPhoto(product_id=products[3].id, file_path="/static/images/pavel.jpg", is_main=True, order=0),
                
                # Для ЭД4-0010 - тоже несколько фото
                ProductPhoto(product_id=products[4].id, file_path="/static/images/poejd.jpg", is_main=True, order=0),
                ProductPhoto(product_id=products[4].id, file_path="/static/images/cabina.jpg", is_main=False, order=1),
                ProductPhoto(product_id=products[4].id, file_path="/static/images/ed4m0142.jpg", is_main=False, order=2),
            ]
            
            session.add_all(photos)
            await session.commit()


async def create_purchase(session: AsyncSession, user_id: int, product_id: int, price_paid: float, payment_id: str = "") -> Purchase:
    """Создать запись о покупке"""
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        price_paid=price_paid,
        payment_id=payment_id,
        is_completed=True
    )
    session.add(purchase)
    await session.commit()
    await session.refresh(purchase)
    return purchase


async def get_user_purchases(session: AsyncSession, user_id: int) -> List[Purchase]:
    """Получить все покупки пользователя"""
    result = await session.execute(
        select(Purchase)
        .options(joinedload(Purchase.product).joinedload(Product.photos))
        .where(Purchase.user_id == user_id)
        .order_by(Purchase.purchase_date.desc())
    )
    return result.scalars().unique().all()


async def get_cart_items(session: AsyncSession, user_id: int) -> List[CartItem]:
    """Получить товары из корзины пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .options(joinedload(CartItem.product).joinedload(Product.photos))
        .where(Cart.user_id == user_id)
        .order_by(CartItem.id.desc())
    )
    return result.scalars().unique().all()


async def remove_from_cart(session: AsyncSession, user_id: int, product_id: int):
    """Удалить товар из корзины"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id, CartItem.product_id == product_id)
    )
    cart_item = result.scalar_one_or_none()
    if cart_item:
        await session.delete(cart_item)
        await session.commit()


async def clear_cart(session: AsyncSession, user_id: int):
    """Очистить всю корзину пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id)
    )
    cart_items = result.scalars().unique().all()
    for item in cart_items:
        await session.delete(item)
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


async def get_product(slug: str) -> Optional[Product]:
    """Получить товар по slug с загруженными фотографиями"""
    async with AsyncSessionLocal() as session:
        stmt = (
            select(Product)
            .options(joinedload(Product.photos))
            .where(Product.slug == slug)
        )
        res = await session.execute(stmt)
        return res.unique().scalar_one_or_none()



async def get_user_by_id(session: AsyncSession, user_id: int) -> Optional[User]:
    """Получить пользователя по ID"""
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(session: AsyncSession, username: str) -> Optional[User]:
    result = await session.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, username: str, email: str, password: str) -> User:
    from .utils import hash_password
    user = User(
        username=username,
        email=email,
        password_hash=hash_password(password),
    )
    session.add(user)
    await session.commit()


async def create_purchase(session: AsyncSession, user_id: int, product_id: int, price_paid: float, payment_id: str = "") -> Purchase:
    """Создать запись о покупке"""
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        price_paid=price_paid,
        payment_id=payment_id,
        is_completed=True
    )
    session.add(purchase)
    await session.commit()
    await session.refresh(purchase)
    return purchase


async def get_user_purchases(session: AsyncSession, user_id: int) -> List[Purchase]:
    """Получить все покупки пользователя"""
    result = await session.execute(
        select(Purchase)
        .options(joinedload(Purchase.product).joinedload(Product.photos))
        .where(Purchase.user_id == user_id)
        .order_by(Purchase.purchase_date.desc())
    )
    return result.scalars().unique().all()


async def get_cart_items(session: AsyncSession, user_id: int) -> List[CartItem]:
    """Получить товары из корзины пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .options(joinedload(CartItem.product).joinedload(Product.photos))
        .where(Cart.user_id == user_id)
        .order_by(CartItem.id.desc())
    )
    return result.scalars().unique().all()


async def remove_from_cart(session: AsyncSession, user_id: int, product_id: int):
    """Удалить товар из корзины"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id, CartItem.product_id == product_id)
    )
    cart_item = result.scalar_one_or_none()
    if cart_item:
        await session.delete(cart_item)
        await session.commit()


async def clear_cart(session: AsyncSession, user_id: int):
    """Очистить всю корзину пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id)
    )
    cart_items = result.scalars().unique().all()
    for item in cart_items:
        await session.delete(item)
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, username: str, password: str) -> Optional[User]:
    from .utils import verify_password
    user = await get_user_by_username(session, username)
    if user and verify_password(password, user.password_hash):
        return user
    return None


async def get_product_by_id(session: AsyncSession, product_id: int) -> Optional[Product]:
    """Получить товар по ID"""
    result = await session.execute(
        select(Product)
        .options(joinedload(Product.photos))
        .where(Product.id == product_id)
    )
    return result.unique().scalar_one_or_none()


async def get_or_create_cart(session: AsyncSession, user_id: int) -> Cart:
    """Получить или создать корзину для пользователя"""
    result = await session.execute(
        select(Cart)
        .options(joinedload(Cart.items))
        .where(Cart.user_id == user_id)
    )
    cart = result.unique().scalar_one_or_none()
    
    if not cart:
        cart = Cart(user_id=user_id)
        session.add(cart)
        await session.flush()  # Получаем ID без коммита
        await session.refresh(cart)  # Обновляем объект с полученным ID
    
    return cart


async def create_purchase(session: AsyncSession, user_id: int, product_id: int, price_paid: float, payment_id: str = "") -> Purchase:
    """Создать запись о покупке"""
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        price_paid=price_paid,
        payment_id=payment_id,
        is_completed=True
    )
    session.add(purchase)
    await session.commit()
    await session.refresh(purchase)
    return purchase


async def get_user_purchases(session: AsyncSession, user_id: int) -> List[Purchase]:
    """Получить все покупки пользователя"""
    result = await session.execute(
        select(Purchase)
        .options(joinedload(Purchase.product).joinedload(Product.photos))
        .where(Purchase.user_id == user_id)
        .order_by(Purchase.purchase_date.desc())
    )
    return result.scalars().unique().all()


async def get_cart_items(session: AsyncSession, user_id: int) -> List[CartItem]:
    """Получить товары из корзины пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .options(joinedload(CartItem.product).joinedload(Product.photos))
        .where(Cart.user_id == user_id)
        .order_by(CartItem.id.desc())
    )
    return result.scalars().unique().all()


async def remove_from_cart(session: AsyncSession, user_id: int, product_id: int):
    """Удалить товар из корзины"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id, CartItem.product_id == product_id)
    )
    cart_item = result.scalar_one_or_none()
    if cart_item:
        await session.delete(cart_item)
        await session.commit()


async def clear_cart(session: AsyncSession, user_id: int):
    """Очистить всю корзину пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id)
    )
    cart_items = result.scalars().unique().all()
    for item in cart_items:
        await session.delete(item)
    await session.commit()


async def add_to_cart(session: AsyncSession, user_id: int, product_id: int, quantity: int = 1):
    """Добавить товар в корзину"""
    cart = await get_or_create_cart(session, user_id)
    
    # Проверяем, есть ли уже этот товар в корзине
    result = await session.execute(
        select(CartItem).where(
            CartItem.cart_id == cart.id,
            CartItem.product_id == product_id
        )
    )
    existing_item = result.scalar_one_or_none()
    
    if existing_item:
        # Увеличиваем количество
        existing_item.quantity += quantity
    else:
        # Создаем новый элемент корзины
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=product_id,
            quantity=quantity
        )
        session.add(cart_item)
    
    await session.commit()


async def create_purchase(session: AsyncSession, user_id: int, product_id: int, price_paid: float, payment_id: str = "") -> Purchase:
    """Создать запись о покупке"""
    purchase = Purchase(
        user_id=user_id,
        product_id=product_id,
        price_paid=price_paid,
        payment_id=payment_id,
        is_completed=True
    )
    session.add(purchase)
    await session.commit()
    await session.refresh(purchase)
    return purchase


async def get_user_purchases(session: AsyncSession, user_id: int) -> List[Purchase]:
    """Получить все покупки пользователя"""
    result = await session.execute(
        select(Purchase)
        .options(joinedload(Purchase.product).joinedload(Product.photos))
        .where(Purchase.user_id == user_id)
        .order_by(Purchase.purchase_date.desc())
    )
    return result.scalars().unique().all()


async def get_cart_items(session: AsyncSession, user_id: int) -> List[CartItem]:
    """Получить товары из корзины пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .options(joinedload(CartItem.product).joinedload(Product.photos))
        .where(Cart.user_id == user_id)
        .order_by(CartItem.id.desc())
    )
    return result.scalars().unique().all()


async def remove_from_cart(session: AsyncSession, user_id: int, product_id: int):
    """Удалить товар из корзины"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id, CartItem.product_id == product_id)
    )
    cart_item = result.scalar_one_or_none()
    if cart_item:
        await session.delete(cart_item)
        await session.commit()


async def clear_cart(session: AsyncSession, user_id: int):
    """Очистить всю корзину пользователя"""
    result = await session.execute(
        select(CartItem)
        .join(Cart)
        .where(Cart.user_id == user_id)
    )
    cart_items = result.scalars().unique().all()
    for item in cart_items:
        await session.delete(item)
    await session.commit()