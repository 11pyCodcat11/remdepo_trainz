from __future__ import annotations

import json
import logging
from aiohttp import web
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ...config import BOT_TOKEN
from ...database.engine import session_scope
from ...database.repository import OrderRepo, PurchaseRepo
from ...utils.helpers import safe_edit_text

logger = logging.getLogger(__name__)

# Store bot instance globally
bot_instance = None

def set_bot_instance(bot: Bot):
    """Set bot instance for webhook notifications"""
    global bot_instance
    bot_instance = bot

async def yookassa_webhook_handler(request):
    """Handle YooKassa webhook notifications"""
    try:
        # Get webhook data
        data = await request.json()
        logger.info(f"YooKassa webhook received: {data}")
        
        # Extract payment info
        event_type = data.get('event')
        payment_data = data.get('object', {})
        payment_id = payment_data.get('id')
        status = payment_data.get('status')
        
        if event_type != 'payment.succeeded':
            return web.Response(text='OK')
            
        if status != 'succeeded':
            return web.Response(text='OK')
        
        # Find order by payment_id
        async with session_scope() as session:
            repo = OrderRepo(session)
            order = await repo.get_by_payment_id(payment_id)
            
            if not order:
                logger.warning(f"Order not found for payment_id: {payment_id}")
                return web.Response(text='OK')
            
            if order.status == 'paid':
                logger.info(f"Order {order.id} already paid")
                return web.Response(text='OK')
            
            # Update order status
            await repo.set_status(order.id, "paid", payment_id=payment_id)
            await PurchaseRepo(session).add_from_order(order.id)
            
            # Get updated order
            order = await repo.get(order.id)
            
            # Send notification to user
            if bot_instance and order.user_id:
                try:
                    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                    kb = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="🧾 История покупок", callback_data="orders:history")
                    ]])
                    
                    await bot_instance.send_message(
                        chat_id=order.user_id,
                        text=f"🎉 Оплата успешно завершена!\n\nЗаказ #{order.id}\nСумма: {order.total_amount} ₽\n\nВсе ссылки на скачивание будут доступны в Истории покупок.",
                        reply_markup=kb
                    )
                    logger.info(f"Payment notification sent to user {order.user_id}")
                except Exception as e:
                    logger.error(f"Failed to send payment notification: {e}")
        
        return web.Response(text='OK')
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return web.Response(text='ERROR', status=500)

async def start_webhook_server():
    """Start webhook server for YooKassa notifications"""
    app = web.Application()
    app.router.add_post('/webhook/yookassa', yookassa_webhook_handler)
    
    # Health check endpoint
    async def health_check(request):
        return web.Response(text='OK')
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("Webhook server started on port 8080")
    return runner
