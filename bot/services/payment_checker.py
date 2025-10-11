from __future__ import annotations

import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from ..config import YOOKASSA_SHOP_ID, YOOKASSA_SECRET_KEY
from ..database.engine import session_scope
from ..database.repository import OrderRepo, PurchaseRepo
from ..utils.helpers import safe_edit_text

logger = logging.getLogger(__name__)

# Store bot instance globally
bot_instance = None

def set_bot_instance(bot):
    """Set bot instance for notifications"""
    global bot_instance
    bot_instance = bot

async def check_pending_payments():
    """Check pending payments and update status"""
    if not YOOKASSA_SHOP_ID or not YOOKASSA_SECRET_KEY:
        return
        
    try:
        from yookassa import Configuration, Payment
        
        Configuration.configure(account_id=YOOKASSA_SHOP_ID, secret_key=YOOKASSA_SECRET_KEY)
        
        async with session_scope() as session:
            repo = OrderRepo(session)
            # Get all pending orders with payment_id
            pending_orders = await repo.get_pending_orders()
            
            for order in pending_orders:
                if not order.payment_id:
                    continue
                    
                try:
                    # Check payment status
                    payment = Payment.find_one(order.payment_id)
                    status = getattr(payment, "status", None)
                    
                    if status in ["succeeded", "paid"]:
                        # Update order status
                        await repo.set_status(order.id, "paid", payment_id=order.payment_id)
                        await PurchaseRepo(session).add_from_order(order.id)
                        
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
                        
                        logger.info(f"Order {order.id} marked as paid")
                        
                except Exception as e:
                    logger.error(f"Error checking payment {order.payment_id}: {e}")
                    
    except Exception as e:
        logger.error(f"Error in payment checker: {e}")

def start_payment_checker():
    """Start periodic payment checking"""
    scheduler = AsyncIOScheduler()
    
    # Check payments every 10 seconds
    scheduler.add_job(
        check_pending_payments,
        trigger=IntervalTrigger(seconds=10),
        id='payment_checker',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info("Payment checker started (10s interval)")
    return scheduler
