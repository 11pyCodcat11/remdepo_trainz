from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from typing import Optional


def product_kb(product_id: int, can_get_free: bool, idx: int, total: int, source: str, is_purchased: bool = False, download_url: Optional[str] = None, in_cart: bool = False) -> InlineKeyboardMarkup:
    rows = []
    if is_purchased:
        if download_url:
            rows.append([InlineKeyboardButton(text="⬇️ Скачать", url=download_url)])
    else:
        buy_text = "✅ Получить" if can_get_free else "💳 Приобрести"
        rows.append([InlineKeyboardButton(text=buy_text, callback_data=f"buy:{product_id}")])
        if not in_cart:
            rows.append([InlineKeyboardButton(text="🛒 В корзину", callback_data=f"cart:add:{product_id}")])
    rows.append([InlineKeyboardButton(text="ℹ️ О товаре", callback_data=f"product:about:{product_id}:0:{source}:{idx}")])
    if total and total > 1:
        rows.append([
            InlineKeyboardButton(text="⏪", callback_data=f"nav:prev:{source}:{idx}:{total}"),
            InlineKeyboardButton(text="⏩", callback_data=f"nav:next:{source}:{idx}:{total}"),
        ])
    
    # Determine correct back navigation based on source
    if source.startswith("cat:"):
        # From category product → back to catalog categories list
        back_callback = "catalog:open"
    elif source == "popular":
        # From popular product → back to main menu
        back_callback = "home"
    else:
        # Default fallback
        back_callback = "catalog:open"
    
    rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data=back_callback)])
    rows.append([InlineKeyboardButton(text="🏠 Меню", callback_data="home")])
    return InlineKeyboardMarkup(inline_keyboard=rows)


