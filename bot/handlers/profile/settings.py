from __future__ import annotations

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton

from ...utils.states import ChangeLoginState, ChangePasswordState


router = Router()


@router.callback_query(lambda c: c.data == "profile:login")
async def change_login_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(ChangeLoginState.waiting_for_login)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="profile:open")]])
    await cb.message.edit_text("🧑‍💻 Введите новый логин:", reply_markup=kb)
    await cb.answer()


@router.message(ChangeLoginState.waiting_for_login)
async def change_login_finish(message: Message, state: FSMContext, db_user, db_session):
    db_user.login = message.text.strip()[:50]
    await db_session.flush()
    await message.answer("✅ Логин обновлён. Откройте профиль заново: /start")
    await state.clear()


@router.callback_query(lambda c: c.data == "profile:pwd")
async def change_pwd_start(cb: CallbackQuery, state: FSMContext):
    await state.set_state(ChangePasswordState.waiting_for_new)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="⬅️ Назад", callback_data="profile:open")]])
    await cb.message.edit_text("🔑 Введите новый пароль:", reply_markup=kb)
    await cb.answer()


@router.message(ChangePasswordState.waiting_for_new)
async def change_pwd_finish(message: Message, state: FSMContext, db_user, db_session):
    db_user.password_hash = message.text.strip()  # For demo; hash in real life
    await db_session.flush()
    await message.answer("✅ Пароль обновлён. Откройте профиль заново: /start")
    await state.clear()


