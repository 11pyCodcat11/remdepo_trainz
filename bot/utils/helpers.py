from __future__ import annotations

import re
from typing import Any, Callable, Dict, Awaitable
from decimal import Decimal

from aiogram import BaseMiddleware
from typing import Optional
from aiogram.types import Message, CallbackQuery

from ..database.engine import session_scope
from ..database.repository import UserRepo


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def format_price(price: Decimal) -> str:
    """Format price without trailing zeros"""
    price_str = str(price)
    if price_str.endswith('.00'):
        price_str = price_str[:-3]
    return "Бесплатно" if price_str == "0" else f"{price_str} ₽"


class AuthMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[["MessageOrCallback", Dict[str, Any]], Awaitable[Any]],
        event: "MessageOrCallback",
        data: Dict[str, Any],
    ) -> Any:
        tg_user = event.from_user
        if tg_user is None:
            return await handler(event, data)
        async with session_scope() as session:
            user = await UserRepo(session).get_or_create(tg_user.id, tg_user.username)
            data["db_session"] = session
            data["db_user"] = user
            result = await handler(event, data)
            return result


# Safely edit a message text. If the current message can't be edited as text (e.g., it's a media),
# delete it and send a new text message with the same markup.
async def safe_edit_text(message, text: str, reply_markup=None, disable_web_page_preview: Optional[bool] = None, parse_mode: Optional[str] = None):
    if not message:
        return
    try:
        await message.edit_text(text, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview, parse_mode=parse_mode)
    except Exception:
        try:
            await message.delete()
        except Exception:
            pass
        await message.answer(text, reply_markup=reply_markup, disable_web_page_preview=disable_web_page_preview)

# Define a Protocol-like union alias for Python 3.8 compatibility without PEP 604
try:
    from aiogram.types import Message as _Msg, CallbackQuery as _Cb
    MessageOrCallback = (_Msg, _Cb)  # type: ignore
except Exception:  # pragma: no cover
    MessageOrCallback = tuple  # fallback

