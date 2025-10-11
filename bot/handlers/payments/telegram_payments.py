from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, LabeledPrice, PreCheckoutQuery, Message
from aiogram.filters import Command
from aiogram.utils.markdown import hbold

from ...config import TELEGRAM_PROVIDER_TOKEN
from ...database.engine import session_scope
from ...database.repository import ProductRepo, OrderRepo, PurchaseRepo
from ...utils.helpers import format_price


router = Router()


@router.callback_query(lambda c: c.data.startswith("tgpay:buy:"))
async def tg_send_invoice(cb: CallbackQuery, db_user):
    # tgpay:buy:<product_id>
    pid = int(cb.data.split(":")[-1])
    if not TELEGRAM_PROVIDER_TOKEN:
        return await cb.answer("Платёж через Telegram не настроен", show_alert=True)
    async with session_scope() as session:
        product = await ProductRepo(session).get(pid)
        if not product:
            return await cb.answer("Товар не найден", show_alert=True)
        # Create pending order and add order item for the product
        order = await OrderRepo(session).create_from_cart(db_user.id, [])
        order.total_amount = product.price
        from ...database.models import OrderItem
        session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=1, price=product.price))
        await session.flush()
    amount_kop = int((product.price * 100).to_integral_value())
    title = product.name[:32]
    description = (product.short_description or product.full_description or "")[:255]
    prices = [LabeledPrice(label="К оплате", amount=amount_kop)]
    payload = f"order:{order.id}:product:{product.id}"
    # do not delete product card; only remove its keyboard
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    await cb.message.answer_invoice(
        title=title,
        description=description or "Оплата товара",
        payload=payload,
        provider_token=TELEGRAM_PROVIDER_TOKEN,
        currency="RUB",
        prices=prices,
        start_parameter="remdepo",
        need_name=False,
        need_phone_number=False,
        need_email=False,
        need_shipping_address=False,
        is_flexible=False,
    )
    await cb.answer()


@router.pre_checkout_query()
async def pre_checkout(pre_checkout_query: PreCheckoutQuery):
    await pre_checkout_query.answer(ok=True)


@router.message()
async def successful_payment_handler(message: Message):
    if not message.successful_payment:
        return
    sp = message.successful_payment
    payload = sp.invoice_payload  # like: order:<oid>:product:<pid>
    try:
        parts = payload.split(":")
        if len(parts) != 4 or parts[0] != "order" or parts[2] != "product":
            return
        _, oid_str, _, pid_str = parts
        oid = int(oid_str)
        pid = int(pid_str)
    except (ValueError, IndexError):
        return
    async with session_scope() as session:
        repo = OrderRepo(session)
        await repo.set_status(oid, "paid", payment_id=sp.provider_payment_charge_id)
        await PurchaseRepo(session).add_from_order(oid)
        # Determine order user and items to clean up cart
        order = await repo.get(oid)
        from ...database.models import OrderItem, Product
        res_items = await session.execute(
            __import__("sqlalchemy").select(OrderItem).where(OrderItem.order_id == oid)
        )
        order_items = list(res_items.scalars().all())
        # Load products for buttons/text in one query
        product_id_list = [it.product_id for it in order_items]
        from typing import Dict
        id_to_product: Dict[int, Product] = {}
        if product_id_list:
            res_products = await session.execute(
                __import__("sqlalchemy").select(Product).where(Product.id.in_(product_id_list))
            )
            id_to_product = {p.id: p for p in res_products.scalars().all()}
        # Clean up cart
        from ...database.repository import CartRepo
        cart_repo = CartRepo(session)
        if order and order_items:
            for it in order_items:
                try:
                    await cart_repo.remove(order.user_id, it.product_id)
                except Exception:
                    pass
        # Popularity boost
        product_repo = ProductRepo(session)
        if pid:
            await product_repo.increment_popularity(pid)
            await product_repo.increment_popularity(pid)
    # Build message and buttons
    price_text = format_price(order.total_amount)
    single_product = pid != 0 and len(id_to_product) == 1
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    if single_product:
        prod = next(iter(id_to_product.values()))
        title_line = f"📦 {hbold('Товар:')} {prod.name}\n"
    else:
        title_line = f"🧾 {hbold('Товары:')} {len(id_to_product)} шт.\n"
    text = (
        f"🎉 {hbold('Покупка успешно завершена!')}\n\n"
        f"{title_line}"
        f"💰 {hbold('Сумма:')} {price_text}\n"
        f"🆔 {hbold('Заказ №')}{oid}\n\n"
        f"Все приобретённые товары добавлены в {hbold('Историю покупок')}."
    )
    buttons = []
    # One download button per product, if URL exists
    for p in id_to_product.values():
        if getattr(p, "download_url", None):
            buttons.append([InlineKeyboardButton(text=f"⬇️ Скачать: {p.name}", url=p.download_url)])
    # Navigation buttons
    buttons.append([InlineKeyboardButton(text="🧾 История покупок", callback_data="orders:history")])
    buttons.append([InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")])
    try:
        await message.delete()
    except Exception:
        pass
    await message.answer(text, protect_content=True, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))


