from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional


def main_menu_kb(is_admin: bool = False, popular_count: Optional[int] = None, is_logged_in: bool = True) -> InlineKeyboardMarkup:
    popular_text = "⭐ Популярное" if not popular_count else f"⭐ Популярное({popular_count})"
    profile_text = "👤 Профиль" if is_logged_in else "🔑 Вход/Регистрация"
    profile_cb = "profile:open" if is_logged_in else "auth:login"
    rows = [
        [
            InlineKeyboardButton(text=popular_text, callback_data="popular:open"),
            InlineKeyboardButton(text="🛒 Каталог", callback_data="catalog:open"),
        ],
        [InlineKeyboardButton(text=profile_text, callback_data=profile_cb)],
    ]
    if is_admin:
        rows.append([InlineKeyboardButton(text="🛠 Админ", callback_data="admin:open")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


