from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Tuple


def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📦 Товары", callback_data="admin:products")],
            [InlineKeyboardButton(text="📁 Категории", callback_data="admin:categories")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
        ]
    )


def admin_products_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить товар", callback_data="admin:prod:add")],
            [InlineKeyboardButton(text="📋 Список товаров", callback_data="admin:prod:list")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
        ]
    )


def admin_product_actions_kb(pid: int, has_photo: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton(text="✏️ Редактировать название", callback_data=f"admin:prod:edit:name:{pid}")],
        [InlineKeyboardButton(text="💵 Редактировать цену", callback_data=f"admin:prod:edit:price:{pid}")],
        [InlineKeyboardButton(text="📝 Редактировать описание", callback_data=f"admin:prod:edit:desc:{pid}")],
    ]
    if has_photo:
        rows.append([InlineKeyboardButton(text="🖼 Заменить фото", callback_data=f"admin:prod:edit:photo:{pid}")])
    else:
        rows.append([InlineKeyboardButton(text="🖼 Добавить фото", callback_data=f"admin:prod:edit:photo:{pid}")])
    rows.append([InlineKeyboardButton(text="🗑 Удалить товар", callback_data=f"admin:prod:del:{pid}")])
    rows.append([InlineKeyboardButton(text="⬅️ К списку", callback_data="admin:prod:list")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_products_list_kb(items: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = []
    for i, (pid, name) in enumerate(items, start=1):
        rows.append([InlineKeyboardButton(text=f"{i}", callback_data=f"admin:prod:open:{pid}")])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def admin_categories_pick_kb(items: List[Tuple[int, str]]) -> InlineKeyboardMarkup:
    rows = []
    for cid, name in items:
        rows.append([InlineKeyboardButton(text=name, callback_data=f"admin:cat:pick:{cid}")])
    rows.append([InlineKeyboardButton(text="Отменить", callback_data="admin:products")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def home_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="🏠 Главное меню", callback_data="home")]]
    )


def finish_extra_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Завершить добавление", callback_data="admin:prod:extra:done")]]
    )


