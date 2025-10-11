from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from ...services.payment_service import PaymentService
from ...database.engine import session_scope
from ...database.repository import OrderRepo, CartRepo, PurchaseRepo
from ...utils.helpers import safe_edit_text
# Admin notifications removed per request
from ..start import main_menu_kb  # reuse if needed
from ...config import BOT_TOKEN, TELEGRAM_PROVIDER_TOKEN


router = Router()
@router.callback_query(lambda c: c.data.startswith("order:check:"))
async def check_order(cb: CallbackQuery, db_user):
    # order:check:<order_id>:<payment_id>
    parts = cb.data.split(":")
    if len(parts) != 4:
        return await cb.answer("Ошибка в данных заказа", show_alert=True)
    try:
        _, _, oid, pid = parts
        oid = int(oid)
    except (ValueError, IndexError):
        return await cb.answer("Ошибка в данных заказа", show_alert=True)
    payment = PaymentService()
    status = await payment.check_payment(pid)
    if status == "succeeded" or status == "paid":
        async with session_scope() as session:
            repo = OrderRepo(session)
            await repo.set_status(oid, "paid", payment_id=pid)
            await PurchaseRepo(session).add_from_order(oid)
            order = await repo.get(oid)
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧾 История покупок", callback_data="orders:history")]])
        await safe_edit_text(cb.message, f"🎉 Оплата успешно завершена!\n\nЗаказ #{oid}\nСумма: {order.total_amount} ₽\n\nВсе ссылки на скачивание будут доступны в Истории покупок.", reply_markup=kb)
        return await cb.answer("Оплачено", show_alert=True)
    await cb.answer("Платёж ещё не подтверждён", show_alert=True)

@router.callback_query(lambda c: c.data == "order:create")
async def create_order(cb: CallbackQuery, db_user):
    async with session_scope() as session:
        # Convert cart into order
        items_in_cart = await CartRepo(session).list_items(db_user.id)
        if not items_in_cart:
            return await cb.answer("Корзина пуста", show_alert=True)
        order = await OrderRepo(session).create_from_cart(db_user.id, items_in_cart)
        await CartRepo(session).clear(db_user.id)
    # Prefer Telegram Payments if provider token is set and user has email
    if TELEGRAM_PROVIDER_TOKEN and db_user.email:
        from aiogram.types import LabeledPrice
        amount_kop = int((order.total_amount * 100).to_integral_value())
        title = f"Корзина #{order.id}"
        description = "Оплата товаров из корзины"
        prices = [LabeledPrice(label="К оплате", amount=amount_kop)]
        
        # Provider data for YooKassa receipt
        provider_data = {
            "receipt": {
                "customer": {
                    "email": db_user.email
                },
                "items": [
                    {
                        "description": f"Товары из корзины #{order.id}",
                        "quantity": 1,
                        "amount": {
                            "value": str(order.total_amount),
                            "currency": "RUB"
                        },
                        "vat_code": 1,
                        "payment_mode": "full_payment",
                        "payment_subject": "commodity"
                    }
                ],
                "tax_system_code": 1
            }
        }
        
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await cb.message.answer_invoice(
            title=title,
            description=description,
            payload=f"order:{order.id}:product:0",
            provider_token=TELEGRAM_PROVIDER_TOKEN,
            currency="RUB",
            prices=prices,
            start_parameter="remdepo",
            provider_data=provider_data
        )
        return await cb.answer()
    
    # Check if user has email for Telegram Payments
    if not db_user.email:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📧 Настроить email", callback_data="profile:settings")],
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="cart:open")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
        ])
        await safe_edit_text(cb.message, 
            "📧 <b>Для оплаты через Telegram нужен email!</b>\n\n"
            "Для корректной работы платежей и получения чеков необходимо указать email в профиле.\n\n"
            "Перейдите в настройки профиля и добавьте email.",
            reply_markup=kb
        )
        return await cb.answer("Нужен email для оплаты", show_alert=True)
    
    # Otherwise create external payment
    payment = PaymentService()
    pid, url = await payment.create_payment(order.id, str(order.total_amount), f"Order #{order.id}", return_url="https://t.me")
    if url:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="💳 Оплатить", url=url)], [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"order:check:{order.id}:{pid}")]])
        await safe_edit_text(cb.message, f"Счёт на оплату выставлен. Заказ #{order.id}\nСумма: {order.total_amount} ₽", reply_markup=kb)
        return await cb.answer()
    # Fallback test: mark as paid
    async with session_scope() as session:
        repo = OrderRepo(session)
        await repo.set_status(order.id, "paid", payment_id=pid)
        await PurchaseRepo(session).add_from_order(order.id)
        order = await repo.get(order.id)
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🧾 История покупок", callback_data="orders:history")]])
    await safe_edit_text(cb.message, f"🎉 Оплата успешно завершена (тест)!\n\nЗаказ #{order.id}\nСумма: {order.total_amount} ₽\n\nВсе ссылки на скачивание будут доступны в Истории покупок.", reply_markup=kb)
    await cb.answer()


