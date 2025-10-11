from __future__ import annotations
import logging

from aiogram import Router
from aiogram.types import CallbackQuery, InputMediaPhoto, LabeledPrice

from ...database.engine import session_scope
from ...database.repository import ProductRepo
from ...database.models import Order
from ...keyboards import product_kb
from ...utils.helpers import format_price, safe_edit_text
from ...config import TELEGRAM_PROVIDER_TOKEN

logger = logging.getLogger(__name__)


router = Router()


@router.callback_query(lambda c: c.data.startswith("buy:"))
async def buy_now(cb: CallbackQuery, db_user):
    if not getattr(db_user, "login", None):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Вход/Регистрация", callback_data="auth:login")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog:open")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
            ]
        )
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("🔑 Для покупки товаров необходимо пройти авторизацию.", reply_markup=kb)
        return await cb.answer()
    pid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        product = await ProductRepo(session).get(pid)
    if not product:
        return await cb.answer("Товар не найден", show_alert=True)
    
    # Create order directly for single product
    from ...database.repository import OrderRepo, PurchaseRepo
    from ...services.payment_service import PaymentService
    # Admin notifications removed per request
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    async with session_scope() as session:
        order = Order(user_id=db_user.id, total_amount=product.price, status="pending")
        session.add(order)
        await session.flush()
        from ...database.models import OrderItem
        session.add(OrderItem(order_id=order.id, product_id=product.id, quantity=1, price=product.price))
        await session.flush()

    # Prefer Telegram Payments if configured and product is not free
    if TELEGRAM_PROVIDER_TOKEN and str(product.price) != "0.00" and db_user.email:
        amount_kop = int((product.price * 100).to_integral_value())
        title = product.name[:32]
        description = (product.short_description or product.full_description or "Оплата товара")[:255]
        prices = [LabeledPrice(label="К оплате", amount=amount_kop)]
        payload = f"order:{order.id}:product:{product.id}"
        
        # Provider data for YooKassa receipt
        provider_data = {
            "receipt": {
                "customer": {
                    "email": db_user.email
                },
                "items": [
                    {
                        "description": product.name[:128],
                        "quantity": 1,
                        "amount": {
                            "value": str(product.price),
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
        
        # do not delete card; only remove its keyboard
        try:
            await cb.message.edit_reply_markup(reply_markup=None)
        except Exception:
            pass
        await cb.message.answer_invoice(
            title=title,
            description=description,
            payload=payload,
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
            [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog:open")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
        ])
        await safe_edit_text(cb.message, 
            "📧 <b>Для оплаты через Telegram нужен email!</b>\n\n"
            "Для корректной работы платежей и получения чеков необходимо указать email в профиле.\n\n"
            "Перейдите в настройки профиля и добавьте email.",
            reply_markup=kb
        )
        return await cb.answer("Нужен email для оплаты", show_alert=True)

    # Create YooKassa payment (redirect to browser)
    payment = PaymentService()
    payment_id, url = await payment.create_payment(order.id, str(product.price), f"Order #{order.id}", return_url="https://t.me")
    if url:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💳 Оплатить", url=url)],
            [InlineKeyboardButton(text="🔄 Проверить оплату", callback_data=f"order:check:{order.id}:{payment_id}")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
        ])
        await safe_edit_text(cb.message, f"Счёт на оплату выставлен. Заказ #{order.id}\nСумма: {product.price} ₽", reply_markup=kb)
        return await cb.answer()

    # Fallback test path: mark paid and send confirmation
    async with session_scope() as session:
        repo = OrderRepo(session)
        await repo.set_status(order.id, "paid", payment_id=payment_id)
        await PurchaseRepo(session).add_from_order(order.id)
        # Increase popularity by 2 and remove from cart if present
        from ...database.repository import CartRepo, ProductRepo as PR
        pr = PR(session)
        await pr.increment_popularity(product.id)
        await pr.increment_popularity(product.id)
        await CartRepo(session).remove(db_user.id, product.id)

    price_text = "Бесплатно" if str(product.price) == "0.00" else f"{product.price} ₽"
    confirmation_text = (
        f"🎉 <b>Покупка успешно завершена!</b>\n\n"
        f"📦 <b>Товар:</b> {product.name}\n"
        f"💰 <b>Сумма:</b> {price_text}\n"
        f"🆔 <b>Заказ №{order.id}</b>\n\n"
        f"✅ Товар добавлен в вашу библиотеку.\n"
        f"Спасибо за покупку!"
    )
    # do not delete card; only remove its keyboard
    try:
        await cb.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass
    buttons = []
    if getattr(product, "download_url", None):
        buttons.append([InlineKeyboardButton(text="⬇️ Скачать", url=product.download_url)])
    buttons.append([InlineKeyboardButton(text="🧾 История покупок", callback_data="orders:history")]) 
    await cb.message.answer(confirmation_text + "\n\nВсе ссылки на скачивание будут доступны в Истории покупок.", reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons), protect_content=True, disable_web_page_preview=True)
    await cb.answer("✅ Покупка завершена!", show_alert=True)


@router.callback_query(lambda c: c.data.startswith("product:about:"))
async def about_product(cb: CallbackQuery, db_user):
    # product:about:<pid>:<idx>:<source>:<product_idx>
    logger.info(f"ℹ️ [ABOUT_PRODUCT] Открытие 'О товаре'. User ID: {cb.from_user.id}, Callback: {cb.data}")
    
    parts = cb.data.split(":")
    if len(parts) < 5:
        logger.error(f"❌ [ABOUT_PRODUCT] Недостаточно параметров в callback: {cb.data}")
        return await cb.answer("Ошибка в данных товара", show_alert=True)
    try:
        _, _, pid, idx = parts[:4]
        pid = int(pid)
        idx = int(idx)
        
        # Правильно извлекаем source - все части после 4-й до последней (product_idx)
        if len(parts) > 5:
            # Есть product_idx в конце
            source = ":".join(parts[4:-1])  # Все части кроме последней
            product_idx = int(parts[-1])
        elif len(parts) > 4:
            # Нет product_idx
            source = ":".join(parts[4:])
            product_idx = 0
        else:
            source = "catalog"
            product_idx = 0
        
        logger.info(f"📋 [ABOUT_PRODUCT] Параметры: PID={pid}, IDX={idx}, SOURCE='{source}', PRODUCT_IDX={product_idx}")
    except (ValueError, IndexError) as e:
        logger.error(f"❌ [ABOUT_PRODUCT] Ошибка парсинга callback: {e}, Data: {cb.data}")
        return await cb.answer("Ошибка в данных товара", show_alert=True)
    async with session_scope() as session:
        repo = ProductRepo(session)
        product = await repo.get(pid)
        images = await repo.list_images(pid)
        await repo.increment_popularity(pid)
    
    # Create combined list: main image first, then extra images
    all_images = []
    if product.main_image_file_id:
        all_images.append(product.main_image_file_id)
    for img in images:
        all_images.append(img.file_id)
    
    total = len(all_images)
    if total == 0:
        await cb.answer("У товара нет фотографий", show_alert=True)
        return
    
    # Format price without trailing zeros
    price_text = format_price(product.price)
    
    photo_pos = (idx % total) + 1
    description = product.full_description or product.short_description or ''
    caption = (
        f"<b>ℹ️ О товаре:</b>\n"
        f"<b>{product.name}</b>\n\n"
        f"💵 <b>Цена:</b> {price_text}\n\n"
        f"<b>Описание:</b>\n{description}\n\n"
        f"🖼 <b>Фото:</b> {photo_pos}/{total}"
    )
    
    # Build navigation buttons
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    nav_row = []
    if total > 1:
        nav_row = [
            InlineKeyboardButton(text="⏪ Предыдущее фото", callback_data=f"product:about:{pid}:{(idx-1+total)%total}:{source}:{product_idx}"),
            InlineKeyboardButton(text="Следующее фото ⏩", callback_data=f"product:about:{pid}:{(idx+1)%total}:{source}:{product_idx}"),
        ]
    
    # Buttons depend on purchase status
    from ...database.repository import PurchaseRepo as _PR
    is_purchased = False
    try:
        async with session_scope() as _s:
            is_purchased = await _PR(_s).exists(db_user.id, pid)
    except Exception:
        is_purchased = False
    if is_purchased:
        action_buttons = []
        if getattr(product, "download_url", None):
            action_buttons.append([InlineKeyboardButton(text="⬇️ Скачать", url=product.download_url)])
    else:
        buy_text = "✅ Получить" if str(product.price) == "0.00" else "💳 Приобрести"
        action_buttons = [
            [InlineKeyboardButton(text=buy_text, callback_data=f"buy:{pid}")],
            [InlineKeyboardButton(text="🧺 В корзину", callback_data=f"cart:add:{pid}")],
        ]
    
    # Determine correct back navigation based on source
    logger.info(f"🔙 [ABOUT_PRODUCT] Определяем кнопку 'Назад' для source: '{source}'")
    
    if source.startswith("cat:"):
        # From "About product" → back to the product itself
        # Проверяем, есть ли сохраненный исходный callback_data
        source_parts = source.split(":")
        logger.info(f"🔍 [ABOUT_PRODUCT] Разбираем source на части: {source_parts}")
        
        if len(source_parts) >= 3:
            # Используем сохраненный исходный callback_data (все части после cat:id)
            back_callback = ":".join(source_parts[2:])
            logger.info(f"✅ [ABOUT_PRODUCT] Используем сохраненный callback: '{back_callback}'")
        else:
            # Fallback к стандартному callback_data
            cat_id = source.split(":")[1]
            back_callback = f"catalog:cat:{cat_id}"
            logger.info(f"⚠️ [ABOUT_PRODUCT] Fallback к стандартному callback: '{back_callback}'")
    elif source == "popular":
        # From "About popular product" → back to popular products list
        back_callback = "popular:open"
        logger.info(f"⭐ [ABOUT_PRODUCT] Популярные товары - кнопка 'Назад': '{back_callback}'")
    else:
        # Default fallback
        back_callback = "catalog:open"
        logger.info(f"🏠 [ABOUT_PRODUCT] Default fallback - кнопка 'Назад': '{back_callback}'")
    
    logger.info(f"🎯 [ABOUT_PRODUCT] Итоговая кнопка 'Назад': '{back_callback}'")
    
    
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        nav_row if nav_row else [],
        *action_buttons,
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)],
        [InlineKeyboardButton(text="🏠 Меню", callback_data="home")]
    ])
    
    # Choose image
    file_id = all_images[idx % total]
    
    if file_id:
        try:
            await cb.message.edit_media(InputMediaPhoto(media=file_id, caption=caption), reply_markup=kb)
        except Exception:
            # If edit_media fails, try to edit as text
            try:
                await cb.message.edit_text(caption, reply_markup=kb)
            except Exception:
                # If edit_text also fails, delete and send new message
                try:
                    await cb.message.delete()
                except Exception:
                    pass
                await cb.message.answer(caption, reply_markup=kb)
    else:
        try:
            await cb.message.edit_text(caption, reply_markup=kb)
        except Exception:
            # If edit_text fails, delete and send new message
            try:
                await cb.message.delete()
            except Exception:
                pass
            await cb.message.answer(caption, reply_markup=kb)
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("cart:add:"))
async def add_to_cart(cb: CallbackQuery, db_user):
    pid = int(cb.data.split(":")[-1])
    if not getattr(db_user, "login", None):
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="🔑 Вход/Регистрация", callback_data="auth:login")],
                [InlineKeyboardButton(text="⬅️ Назад", callback_data="catalog:open")],
                [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
            ]
        )
        try:
            await cb.message.delete()
        except Exception:
            pass
        await cb.message.answer("🔑 Для добавления в корзину необходимо пройти авторизацию.", reply_markup=kb)
        return await cb.answer()
    from ...services.cart_service import CartService
    from ...database.repository import ProductRepo
    async with session_scope() as session:
        await CartService(session).add(db_user.id, pid, 1)
        product = await ProductRepo(session).get(pid)
    # Try to update current card keyboard to hide "В корзину"
    try:
        from ...keyboards import product_kb
        can_get_free = str(product.price) == "0.00" if product else False
        await cb.message.edit_reply_markup(
            reply_markup=product_kb(pid, can_get_free, 0, 1, "single", in_cart=True, is_purchased=False, download_url=getattr(product, "download_url", None))
        )
    except Exception:
        pass
    await cb.answer("🧺 Добавлено в корзину", show_alert=True)


