"""
Health check endpoint для мониторинга состояния бота
"""
import asyncio
import logging
from aiohttp import web
from pathlib import Path

logger = logging.getLogger(__name__)

async def health_check(request):
    """Проверка здоровья бота"""
    try:
        # Проверяем наличие базы данных
        db_path = Path("bot.db")
        if not db_path.exists():
            return web.json_response(
                {"status": "unhealthy", "reason": "database_not_found"}, 
                status=503
            )
        
        # Проверяем размер базы данных (должна быть больше 0)
        if db_path.stat().st_size == 0:
            return web.json_response(
                {"status": "unhealthy", "reason": "database_empty"}, 
                status=503
            )
        
        return web.json_response({
            "status": "healthy",
            "database": "ok",
            "bot": "running"
        })
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return web.json_response(
            {"status": "unhealthy", "reason": str(e)}, 
            status=503
        )

async def start_health_server():
    """Запуск HTTP сервера для health check"""
    app = web.Application()
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    
    logger.info("Health check server started on port 8080")
