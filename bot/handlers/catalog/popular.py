from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, InputMediaPhoto

from ...database.engine import session_scope
from ...database.repository import ProductRepo
from ...keyboards import product_kb
from ...database.repository import CartRepo, PurchaseRepo
from ...utils.helpers import format_price


router = Router()


def _product_caption(product) -> str:
    price = format_price(product.price)
    description = product.short_description or getattr(product, 'full_description', None) or ''
    return f"<b>{product.name}</b>\n\n💵 {price}\n\n📝 <b>Описание:</b>\n{description}"


@router.callback_query(lambda c: c.data == "popular:open")
async def open_popular(cb: CallbackQuery, db_user):
    async with session_scope() as session:
        popular = await ProductRepo(session).list_popular(limit=5)
    if not popular:
        # Alert with emoji and do not alter current message content
        return await cb.answer("⚠️ Популярных товаров пока нет", show_alert=True)

    product = popular[0]
    caption = _product_caption(product) + f"\n\n📦 <b>Товар:</b> 1/{len(popular)}"
    # check if in cart
    in_cart = False
    try:
        async with session_scope() as _s:
            in_cart = await CartRepo(_s).exists(db_user.id, product.id)
    except Exception:
        in_cart = False
    # purchased?
    is_purchased = False
    try:
        async with session_scope() as _s:
            is_purchased = await PurchaseRepo(_s).exists(db_user.id, product.id)
    except Exception:
        is_purchased = False
    kb = product_kb(
        product.id,
        str(product.price) == "0.00",
        0,
        len(popular),
        "popular",
        in_cart=in_cart,
        is_purchased=is_purchased,
        download_url=product.download_url,
    )
    if product.main_image_file_id:
        try:
            await cb.message.edit_media(InputMediaPhoto(media=product.main_image_file_id, caption=caption), reply_markup=kb)
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


@router.callback_query(lambda c: c.data.startswith("product:open:"))
async def open_product(cb: CallbackQuery):
    pid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        repo = ProductRepo(session)
        product = await repo.get(pid)
        if product:
            await repo.increment_popularity(pid)
    if not product:
        await cb.answer("Товар не найден", show_alert=True)
        return
    caption = _product_caption(product) + "\n\n📦 <b>Товар:</b> 1/1"
    if product.main_image_file_id:
        try:
            await cb.message.edit_media(
                media=InputMediaPhoto(media=product.main_image_file_id, caption=caption),
                reply_markup=product_kb(product.id, str(product.price) == "0.00", 0, 1, "single"),
            )
        except Exception:
            await cb.message.edit_text(caption, reply_markup=product_kb(product.id, str(product.price) == "0.00", 0, 1, "single"))
    else:
        await cb.message.edit_text(caption, reply_markup=product_kb(product.id, str(product.price) == "0.00", 0, 1, "single"))
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("nav:") and c.data.split(":")[2] == "popular")
async def navigate(cb: CallbackQuery, db_user):
    # nav:prev:popular:idx:total
    parts = cb.data.split(":")
    if len(parts) < 5:
        return await cb.answer("Ошибка навигации", show_alert=True)
    try:
        _, direction, _, idx, total = parts[:5]
        idx = int(idx)
        total = int(total)
    except (ValueError, IndexError):
        return await cb.answer("Ошибка навигации", show_alert=True)
    async with session_scope() as session:
        items = await ProductRepo(session).list_popular(limit=total)

    if not items:
        return await cb.answer()

    if direction == "next":
        idx = (idx + 1) % total
    else:
        idx = (idx - 1 + total) % total

    product = items[idx]
    caption = _product_caption(product) + f"\n\n📦 <b>Товар:</b> {idx+1}/{total}"
    in_cart = False
    try:
        async with session_scope() as _s:
            in_cart = await CartRepo(_s).exists(db_user.id, product.id)
    except Exception:
        in_cart = False
    is_purchased = False
    try:
        async with session_scope() as _s:
            is_purchased = await PurchaseRepo(_s).exists(db_user.id, product.id)
    except Exception:
        is_purchased = False
    kb = product_kb(
        product.id,
        str(product.price) == "0.00",
        idx,
        total,
        "popular",
        in_cart=in_cart,
        is_purchased=is_purchased,
        download_url=product.download_url,
    )
    if product.main_image_file_id:
        try:
            await cb.message.edit_media(
                InputMediaPhoto(media=product.main_image_file_id, caption=caption),
                reply_markup=kb,
            )
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


