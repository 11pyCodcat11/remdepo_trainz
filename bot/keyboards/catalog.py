from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple


def categories_kb(categories: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = []
    for cid, name in categories:
        rows.append([InlineKeyboardButton(text=f"📂 {name}", callback_data=f"catalog:cat:{cid}")])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def products_list_kb(products: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = []
    for pid, name in products:
        rows.append([InlineKeyboardButton(text=f"🧩 {name}", callback_data=f"product:open:{pid}")])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


