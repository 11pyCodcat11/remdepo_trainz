from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from ..keyboards import main_menu_kb
from ..config import BOT_ADMINS
from ..database.engine import session_scope
from ..database.repository import ProductRepo


router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message, db_user):
    is_admin = message.from_user and message.from_user.id in BOT_ADMINS
    # Compute popular count for the main menu
    async with session_scope() as session:
        popular_count = len(await ProductRepo(session).list_popular(limit=50))
    # Determine login status via middleware-injected db_user
    is_logged_in = bool(getattr(db_user, "login", None))
    await message.answer("👋 Добро пожаловать в магазин RemDepo!", reply_markup=main_menu_kb(is_admin=is_admin, popular_count=popular_count, is_logged_in=is_logged_in))


@router.callback_query(lambda c: c.data == "home")
async def cb_home(cb: CallbackQuery, db_user):
    is_admin = cb.from_user and cb.from_user.id in BOT_ADMINS
    # Delete the message where the button was pressed and send fresh main menu
    try:
        await cb.message.delete()
    except Exception:
        pass
    async with session_scope() as session:
        popular_count = len(await ProductRepo(session).list_popular(limit=50))
    # Determine login status via middleware-injected db_user
    is_logged_in = bool(getattr(db_user, "login", None))
    await cb.message.answer("🏠 Главное меню", reply_markup=main_menu_kb(is_admin=is_admin, popular_count=popular_count, is_logged_in=is_logged_in))
    await cb.answer()


