from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_kb(cart_count: int = 0, purchases_count: int = 0) -> InlineKeyboardMarkup:
    cart_text = f"🛒 Корзина ({cart_count})"
    orders_text = f"🧾 История покупок ({purchases_count})"
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔑 Сменить Пароль", callback_data="profile:pwd")],
            [InlineKeyboardButton(text="🧑‍💻 Сменить Логин", callback_data="profile:login")],
            [InlineKeyboardButton(text=cart_text, callback_data="cart:open"), InlineKeyboardButton(text=orders_text, callback_data="orders:history")],
            [InlineKeyboardButton(text="🚪 Выйти", callback_data="profile:logout")],
            [InlineKeyboardButton(text="🏠 Меню", callback_data="home")],
        ]
    )


