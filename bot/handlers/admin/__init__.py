from aiogram import Router
from ...config import BOT_ADMINS
from ...keyboards import admin_main_kb

router = Router()


@router.callback_query(lambda c: c.data == "admin:open")
async def open_admin(cb):
    if cb.from_user.id not in BOT_ADMINS:
        return await cb.answer("Недостаточно прав", show_alert=True)
    await cb.message.edit_text("Админ-панель", reply_markup=admin_main_kb())
    await cb.answer()


