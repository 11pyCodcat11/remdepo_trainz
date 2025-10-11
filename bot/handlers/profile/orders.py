from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, InputMediaPhoto

from ...database.engine import session_scope
from ...database.repository import PurchaseRepo, ProductRepo
from ...utils.helpers import format_price, safe_edit_text


router = Router()


@router.callback_query(lambda c: c.data == "orders:history")
async def show_history(cb: CallbackQuery, db_user):
    async with session_scope() as session:
        all_purchases = await PurchaseRepo(session).list_by_user(db_user.id)
        # Deduplicate by product_id, keep latest by date
        latest_by_product = {}
        for p in all_purchases:
            latest_by_product[p.product_id] = p
        purchases = list(latest_by_product.values())
    # Filter out purchases whose products no longer exist
    if purchases:
        product_ids = [p.product_id for p in purchases]
        async with session_scope() as session:
            from sqlalchemy import select as _select
            from ...database.models import Product as _Product
            res = await session.execute(_select(_Product.id).where(_Product.id.in_(product_ids)))
            valid_ids = {row[0] for row in res.all()}
        purchases = [p for p in purchases if p.product_id in valid_ids]
    if not purchases:
        await cb.answer("🧾 История покупок пуста", show_alert=True)
        return
    idx = 0
    p = purchases[idx]
    async with session_scope() as session:
        product = await ProductRepo(session).get(p.product_id)
    if not product:
        await cb.answer("🧾 История покупок пуста", show_alert=True)
        return
    caption = (
        f"<b>{product.name}</b>\n\n"
        f"💵 {format_price(p.price)}\n"
        f"🗓 Дата: {p.purchased_at:%d.%m.%Y}\n\n"
        f"📦 <b>Товар:</b> 1/{len(purchases)}"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    total = len(purchases)
    rows = []
    if total > 1:
        rows.append([
            InlineKeyboardButton(text="⏪", callback_data=f"orders:nav:prev:{idx}:{total}"),
            InlineKeyboardButton(text="⏩", callback_data=f"orders:nav:next:{idx}:{total}"),
        ])
    # Always include download button if available
    if getattr(product, "download_url", None):
        rows.insert(0, [InlineKeyboardButton(text="⬇️ Скачать", url=product.download_url)])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="profile:open")])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    if product.main_image_file_id:
        try:
            await cb.message.edit_media(InputMediaPhoto(media=product.main_image_file_id, caption=caption), reply_markup=kb)
        except Exception:
            await safe_edit_text(cb.message, caption, reply_markup=kb)
    else:
        await safe_edit_text(cb.message, caption, reply_markup=kb)
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("orders:nav:"))
async def history_nav(cb: CallbackQuery, db_user):
    # orders:nav:direction:idx:total
    parts = cb.data.split(":")
    if len(parts) < 5:
        return await cb.answer("Ошибка навигации", show_alert=True)
    try:
        _, _, direction, idx, _ = parts
        idx = int(idx)
    except (ValueError, IndexError):
        return await cb.answer("Ошибка навигации", show_alert=True)
    async with session_scope() as session:
        all_purchases = await PurchaseRepo(session).list_by_user(db_user.id)
        latest_by_product = {}
        for p in all_purchases:
            latest_by_product[p.product_id] = p
        purchases = list(latest_by_product.values())
        # Filter out purchases whose products no longer exist
        if purchases:
            from sqlalchemy import select as _select
            from ...database.models import Product as _Product
            res = await session.execute(_select(_Product.id).where(_Product.id.in_([pp.product_id for pp in purchases])))
            valid_ids = {row[0] for row in res.all()}
            purchases = [pp for pp in purchases if pp.product_id in valid_ids]
    total = len(purchases)
    if not purchases:
        return await cb.answer("🧾 История покупок пуста", show_alert=True)
    if direction == "next":
        idx = (idx + 1) % total
    else:
        idx = (idx - 1 + total) % total
    p = purchases[idx]
    async with session_scope() as session:
        product = await ProductRepo(session).get(p.product_id)
    if not product:
        return await cb.answer("🧾 История покупок пуста", show_alert=True)
    caption = (
        f"<b>{product.name}</b>\n\n"
        f"💵 {format_price(p.price)}\n"
        f"🗓 Дата: {p.purchased_at:%d.%m.%Y}\n\n"
        f"📦 <b>Товар:</b> {idx+1}/{total}"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    rows = []
    if total > 1:
        rows.append([
            InlineKeyboardButton(text="⏪", callback_data=f"orders:nav:prev:{idx}:{total}"),
            InlineKeyboardButton(text="⏩", callback_data=f"orders:nav:next:{idx}:{total}"),
        ])
    if getattr(product, "download_url", None):
        rows.insert(0, [InlineKeyboardButton(text="⬇️ Скачать", url=product.download_url)])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="profile:open")])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    if product.main_image_file_id:
        try:
            await cb.message.edit_media(InputMediaPhoto(media=product.main_image_file_id, caption=caption), reply_markup=kb)
        except Exception:
            await safe_edit_text(cb.message, caption, reply_markup=kb)
    else:
        await safe_edit_text(cb.message, caption, reply_markup=kb)
    await cb.answer()



