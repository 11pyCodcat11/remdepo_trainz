from __future__ import annotations
import logging

from aiogram import Router
from aiogram.types import CallbackQuery, InputMediaPhoto

from ...database.engine import session_scope
from ...database.repository import CategoryRepo, ProductRepo
from ...keyboards import categories_kb, products_list_kb, product_kb
from ...utils.helpers import format_price, safe_edit_text

logger = logging.getLogger(__name__)


router = Router()


@router.callback_query(lambda c: c.data == "catalog:open")
async def open_catalog(cb: CallbackQuery):
    logger.info(f"🔍 [CATALOG] Открытие каталога. User ID: {cb.from_user.id}, Callback: {cb.data}")
    async with session_scope() as session:
        cats = await CategoryRepo(session).list_with_counts()
    data = [(c.id, f"{c.name}({cnt})") for c, cnt in cats]
    logger.info(f"📂 [CATALOG] Найдено категорий: {len(data)}")
    await safe_edit_text(cb.message, "Категории:", reply_markup=categories_kb(data))
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("catalog:cat:"))
async def open_category(cb: CallbackQuery, db_user):
    cat_id = int(cb.data.split(":")[-1])
    # Сохраняем исходный callback_data кнопки категории
    original_callback = cb.data
    logger.info(f"📂 [CATEGORY] Открытие категории. User ID: {cb.from_user.id}, Cat ID: {cat_id}, Original callback: {original_callback}")
    
    async with session_scope() as session:
        products = await ProductRepo(session).list_by_category(cat_id)
    
    logger.info(f"📦 [CATEGORY] Найдено товаров в категории {cat_id}: {len(products)}")
    
    if not products:
        logger.warning(f"⚠️ [CATEGORY] Категория {cat_id} пуста")
        await cb.answer("Пока что этот раздел пуст ☹️", show_alert=True)
        return
    
    p = products[0]
    price_free = str(p.price) == "0.00"
    description = p.short_description or p.full_description or ''
    caption = (
        f"<b>{p.name}</b>\n\n"
        f"💵 {format_price(p.price)}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"📦 <b>Товар:</b> 1/{len(products)}"
    )
    
    logger.info(f"🛍️ [CATEGORY] Показываем товар: {p.name} (ID: {p.id})")
    
    # Determine if purchased to show "Скачать"
    is_purchased = False
    try:
        from ...database.repository import PurchaseRepo as _PR
        async with session_scope() as _s:
            is_purchased = await _PR(_s).exists(db_user.id, p.id)
    except Exception:
        is_purchased = False
    # check if product is already in cart for current user
    in_cart = False
    try:
        from ...database.repository import CartRepo as _CR
        async with session_scope() as _s:
            in_cart = await _CR(_s).exists(db_user.id, p.id)
    except Exception:
        in_cart = False
    
    # Передаем исходный callback_data через source
    source_with_callback = f"cat:{cat_id}:{original_callback}"
    logger.info(f"🔗 [CATEGORY] Формируем source: {source_with_callback}")
    
    kb = product_kb(p.id, price_free, 0, len(products), source_with_callback, is_purchased=is_purchased, download_url=p.download_url, in_cart=in_cart)
    if p.main_image_file_id:
        try:
            await cb.message.edit_media(InputMediaPhoto(media=p.main_image_file_id, caption=caption), reply_markup=kb)
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


@router.callback_query(lambda c: c.data.startswith("nav:") and (":cat:" in c.data or c.data.split(":")[2] == "popular"))
async def navigate(cb: CallbackQuery, db_user):
    logger.info(f"🔄 [NAVIGATION] Навигация. User ID: {cb.from_user.id}, Callback: {cb.data}")
    
    parts = cb.data.split(":")
    # Поддержка формата: nav:<prev|next>:cat:<cat_id>:...:<idx>:<total>
    if len(parts) >= 6 and "cat" in parts:
        try:
            direction = parts[1]
            cat_pos = parts.index("cat")
            cat_id = int(parts[cat_pos + 1])
            # Индексы и total — это последние два элемента
            idx = int(parts[-2])
            total = int(parts[-1])
            # Исходный callback между cat_id и последними двумя элементами (может отсутствовать)
            original_tail = parts[cat_pos + 2:-2]
            original_callback = ":".join(original_tail) if original_tail else f"catalog:cat:{cat_id}"
            source = f"cat:{cat_id}:{original_callback}"
            logger.info(f"📂 [NAVIGATION] Навигация по категории: Direction={direction}, Cat ID={cat_id}, IDX={idx}/{total}, Original callback='{original_callback}'")
        except (ValueError, IndexError) as e:
            logger.error(f"❌ [NAVIGATION] Ошибка парсинга навигации: {e}, Data: {cb.data}")
            return await cb.answer("Ошибка навигации", show_alert=True)
    else:
        logger.warning(f"⚠️ [NAVIGATION] Неизвестный формат навигации: {cb.data}")
        return await cb.answer()
    
    if source.startswith("cat:"):
        cat_id = int(source.split(":")[1])
        logger.info(f"📦 [NAVIGATION] Загружаем товары категории {cat_id}")
        async with session_scope() as session:
            items = await ProductRepo(session).list_by_category(cat_id)
    else:
        logger.warning(f"⚠️ [NAVIGATION] Неизвестный source: {source}")
        return
    
    if not items:
        logger.warning(f"⚠️ [NAVIGATION] Нет товаров в категории {cat_id}")
        return
    
    if direction == "next":
        idx = (idx + 1) % total
        logger.info(f"➡️ [NAVIGATION] Переход к следующему товару: {idx+1}/{total}")
    else:
        idx = (idx - 1 + total) % total
        logger.info(f"⬅️ [NAVIGATION] Переход к предыдущему товару: {idx+1}/{total}")
    
    p = items[idx]
    price_free = str(p.price) == "0.00"
    description = p.short_description or p.full_description or ''
    caption = (
        f"<b>{p.name}</b>\n\n"
        f"💵 {format_price(p.price)}\n\n"
        f"📝 <b>Описание:</b>\n{description}\n\n"
        f"📦 <b>Товар:</b> {idx+1}/{total}"
    )
    
    logger.info(f"🛍️ [NAVIGATION] Показываем товар: {p.name} (ID: {p.id})")
    
    is_purchased = False
    try:
        from ...database.repository import PurchaseRepo as _PR
        async with session_scope() as _s:
            is_purchased = await _PR(_s).exists(db_user.id, p.id)
    except Exception:
        is_purchased = False
    # check if product is already in cart for current user
    in_cart = False
    try:
        from ...database.repository import CartRepo as _CR
        async with session_scope() as _s:
            in_cart = await _CR(_s).exists(db_user.id, p.id)
    except Exception:
        in_cart = False
    
    logger.info(f"🔗 [NAVIGATION] Формируем клавиатуру с source: {source}")
    kb = product_kb(p.id, price_free, idx, total, source, is_purchased=is_purchased, download_url=p.download_url, in_cart=in_cart)
    
    if p.main_image_file_id:
        try:
            await cb.message.edit_media(InputMediaPhoto(media=p.main_image_file_id, caption=caption), reply_markup=kb)
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


