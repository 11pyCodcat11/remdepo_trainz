from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, InputMediaPhoto

from ...database.engine import session_scope
from ...services.cart_service import CartService
from ...keyboards import cart_kb
from ...database.repository import ProductRepo
from ...utils.helpers import format_price, safe_edit_text


router = Router()


@router.callback_query(lambda c: c.data == "cart:open")
async def open_cart(cb: CallbackQuery, db_user):
    async with session_scope() as session:
        items, total = await CartService(session).list_with_total(db_user.id)
    names = [(pid, f"{name} — {format_price(price)} ×{qty}") for pid, name, qty, price in items]
    await safe_edit_text(cb.message, "🛒 Корзина:", reply_markup=cart_kb(names, f"{format_price(total)}"))
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("cart:remove:"))
async def remove_from_cart(cb: CallbackQuery, db_user):
    pid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        await CartService(session).remove(db_user.id, pid)
        items, total = await CartService(session).list_with_total(db_user.id)
    names = [(pid, f"{name} — {format_price(price)} ×{qty}") for pid, name, qty, price in items]
    await safe_edit_text(cb.message, "🛒 Корзина:", reply_markup=cart_kb(names, f"{format_price(total)}"))
    await cb.answer("Удалено")


@router.callback_query(lambda c: c.data.startswith("cart:item:"))
async def open_cart_item(cb: CallbackQuery, db_user):
    pid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        product = await ProductRepo(session).get(pid)
    if not product:
        return await cb.answer("Товар не найден", show_alert=True)
    caption = (
        f"<b>{product.name}</b>\n\n"
        f"💵 {format_price(product.price)}\n\n"
        f"📝 <b>Описание:</b>\n{product.full_description or product.short_description or ''}"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=("✅ Получить" if str(product.price)=="0.00" else "💳 Приобрести"), callback_data=f"buy:{product.id}")],
        [InlineKeyboardButton(text="🗑 Удалить из корзины", callback_data=f"cart:remove:{product.id}")],
        [InlineKeyboardButton(text="⬅️ К корзине", callback_data="cart:open")],
    ])
    if product.main_image_file_id:
        try:
            await cb.message.edit_media(InputMediaPhoto(media=product.main_image_file_id, caption=caption), reply_markup=kb)
        except Exception:
            await cb.message.edit_text(caption, reply_markup=kb)
    else:
        await cb.message.edit_text(caption, reply_markup=kb)
    await cb.answer()


@router.callback_query(lambda c: c.data.startswith("cart:add:"))
async def add_from_cart_duplicate_guard(cb: CallbackQuery, db_user):
    # Guard for duplicate add attempts; service prevents increment, so show info
    if not getattr(db_user, "login", None):
        return
    pid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        items, _ = await CartService(session).list_with_total(db_user.id)
        if any(p == pid for p, *_ in items):
            return await cb.answer("Этот товар уже в вашей корзине", show_alert=True)


