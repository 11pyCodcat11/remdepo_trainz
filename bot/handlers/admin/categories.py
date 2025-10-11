from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from ...config import BOT_ADMINS
from ...keyboards import admin_main_kb
from ...database.engine import session_scope
from ...database.models import Category
from sqlalchemy import select
from ...utils.states import AdminCategoryState
from aiogram.fsm.context import FSMContext
from aiogram.types import Message


router = Router()


def _is_admin(uid: int) -> bool:
    return uid in BOT_ADMINS


@router.callback_query(lambda c: c.data == "admin:categories")
async def admin_categories(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Недостаточно прав", show_alert=True)
    # Автосоздадим базовые категории, если пусто
    async with session_scope() as session:
        # Создаём базовые категории только если в таблице совсем пусто,
        # чтобы переименованные категории не пересоздавались заново.
        res = await session.execute(select(Category))
        all_cats = res.scalars().all()
        if not all_cats:
            session.add_all([
                Category(name="Подвижной состав"),
                Category(name="Карты"),
                Category(name="Сценарии"),
                Category(name="Полезные ссылки"),
            ])
    # Показать список категорий инлайн-кнопками для редактирования
    async with session_scope() as session:
        res = await session.execute(select(Category).order_by(Category.id))
        cats = res.scalars().all()
    rows = [[InlineKeyboardButton(text=f"{c.name}", callback_data=f"admin:cat:edit:{c.id}")]
            for c in cats]
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    await cb.message.edit_text("Категории (нажмите для переименования):", reply_markup=kb)
    await cb.answer()

@router.callback_query(lambda c: c.data.startswith("admin:cat:edit:"))
async def cat_edit_start(cb: CallbackQuery, state: FSMContext):
    cid = int(cb.data.split(":")[-1])
    async with session_scope() as session:
        res = await session.execute(select(Category).where(Category.id == cid))
        c = res.scalar_one_or_none()
    if not c:
        return await cb.answer("Категория не найдена", show_alert=True)
    await state.update_data(cid=cid, old_name=c.name)
    await state.set_state(AdminCategoryState.waiting_for_name)
    await cb.message.edit_text(
        f"Текущая: {c.name}\nВведите новое название:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="↩️ Отмена", callback_data="admin:categories")]]),
    )
    await cb.answer()


@router.message(AdminCategoryState.waiting_for_name)
async def cat_edit_enter_new(message: Message, state: FSMContext):
    new_name = message.text.strip()
    data = await state.get_data()
    cid = data.get("cid")
    old_name = data.get("old_name")
    await state.update_data(new_name=new_name)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"admin:cat:confirm:{cid}")],
            [InlineKeyboardButton(text="↩️ Отмена", callback_data="admin:categories")],
        ]
    )
    await message.answer(f"Переименовать ‘{old_name}’ → ‘{new_name}’ ?", reply_markup=kb)


@router.callback_query(lambda c: c.data.startswith("admin:cat:confirm:"))
async def cat_edit_confirm(cb: CallbackQuery, state: FSMContext):
    cid = int(cb.data.split(":")[-1])
    data = await state.get_data()
    new_name = data.get("new_name")
    if not new_name:
        return await cb.answer("Нет нового названия", show_alert=True)
    async with session_scope() as session:
        res = await session.execute(select(Category).where(Category.id == cid))
        c = res.scalar_one_or_none()
        if not c:
            await state.clear()
            return await cb.answer("Категория не найдена", show_alert=True)
        c.name = new_name
        await session.flush()
    await state.clear()
    await admin_categories(cb)


