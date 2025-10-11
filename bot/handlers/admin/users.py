from __future__ import annotations

from aiogram import Router
from aiogram.types import CallbackQuery

from ...config import BOT_ADMINS
from ...keyboards import admin_main_kb


router = Router()


def _is_admin(uid: int) -> bool:
    return uid in BOT_ADMINS


@router.callback_query(lambda c: c.data == "admin:users")
async def admin_users(cb: CallbackQuery):
    if not _is_admin(cb.from_user.id):
        return await cb.answer("Недостаточно прав", show_alert=True)
    await cb.message.edit_text("Админ: Пользователи (заглушка)", reply_markup=admin_main_kb())
    await cb.answer()


