from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple


def cart_kb(items: List[Tuple[int, str]], total: str) -> InlineKeyboardMarkup:
    rows = []
    for pid, name in items:
        rows.append([
            InlineKeyboardButton(text=f"{name}", callback_data=f"cart:item:{pid}"),
            InlineKeyboardButton(text=f"🗑️ Удалить", callback_data=f"cart:remove:{pid}"),
        ])
    rows.append([InlineKeyboardButton(text=f"💰 Оплатить все ({total})", callback_data="order:create")])
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="profile:open")])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


