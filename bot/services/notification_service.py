from __future__ import annotations

from aiogram import Bot

from ..config import BOT_ADMINS


async def notify_admins(bot: Bot, text: str) -> None:
    for admin_id in BOT_ADMINS:
        try:
            await bot.send_message(admin_id, text)
        except Exception:
            continue


