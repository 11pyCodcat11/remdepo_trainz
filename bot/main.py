from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums.parse_mode import ParseMode

from .config import BOT_TOKEN
from .database.engine import init_db
from .health import start_health_server
from .handlers.start import router as start_router
from .handlers.catalog.categories import router as catalog_categories_router
from .handlers.catalog.products import router as catalog_products_router
from .handlers.catalog.popular import router as popular_router
from .handlers.profile.auth import router as auth_router
from .handlers.profile.cart import router as cart_router
from .handlers.profile.orders import router as orders_router
from .handlers.profile.settings import router as settings_router
from .handlers.admin.products import router as admin_products_router
from .handlers.admin.categories import router as admin_categories_router
from .handlers.admin.orders import router as admin_orders_router
from .handlers.admin.users import router as admin_users_router
from .handlers.admin import router as admin_root_router
from .handlers.payments.telegram_payments import router as tg_payments_router
from .handlers.payments.yookassa import router as yookassa_router
from .handlers.payments.webhook import start_webhook_server, set_bot_instance
from .services.payment_checker import start_payment_checker, set_bot_instance as set_checker_bot
from .utils.helpers import AuthMiddleware


async def main() -> None:
    logging.basicConfig(level=logging.INFO)

    await init_db()

    # Запускаем health check сервер
    await start_health_server()

    # Запускаем webhook сервер для YooKassa
    webhook_runner = await start_webhook_server()

    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    
    # Устанавливаем bot instance для webhook уведомлений
    set_bot_instance(bot)
    set_checker_bot(bot)
    
    # Запускаем периодическую проверку платежей
    payment_scheduler = start_payment_checker()
    
    dp = Dispatcher()

    # Middleware: ensure user exists in DB and add user to event context
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Routers
    dp.include_router(start_router)
    dp.include_router(popular_router)
    dp.include_router(catalog_categories_router)
    dp.include_router(catalog_products_router)
    dp.include_router(auth_router)
    dp.include_router(cart_router)
    dp.include_router(orders_router)
    dp.include_router(settings_router)

    # Admin
    dp.include_router(admin_products_router)
    dp.include_router(admin_categories_router)
    dp.include_router(admin_orders_router)
    dp.include_router(admin_users_router)
    dp.include_router(admin_root_router)

    # Payments
    dp.include_router(tg_payments_router)
    dp.include_router(yookassa_router)

    logging.info("Bot is starting in polling mode...")
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass


