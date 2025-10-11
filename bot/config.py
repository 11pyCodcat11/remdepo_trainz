import os

# Prefer env var; default to container data dir
DB_DSN = os.getenv("DATABASE_URL") or os.getenv("DB_DSN") or "sqlite+aiosqlite:////app/data/bot.db"

# Токен бота (по просьбе пользователя захардкожен)
BOT_TOKEN = "8229036508:AAFh1St-NaUVIcnFRrSPJp7mtzo02zoomIA"

# Список админов через запятую (оставьте пустым или добавьте ID)
from typing import Tuple
BOT_ADMINS: Tuple[int, ...] = (1313001001, 5032033459)
# Платежные реквизиты YooKassa
from typing import Optional
YOOKASSA_SHOP_ID: Optional[str] = "506751"
YOOKASSA_SECRET_KEY: Optional[str] = "live_o7a-4--NHd0qle0V9Mws8mPiOjjPbWihfwN6V5Gaq-I"

# Telegram Payments provider token (BotFather — YooKassa via Telegram)
TELEGRAM_PROVIDER_TOKEN: Optional[str] = "390540012:LIVE:79658"

# Profile photo file_id to send in profile
PROFILE_PHOTO_FILE_ID: Optional[str] = "AgACAgIAAxkBAAIBiGjlQOtmHXmSSYojosivnTNW8_-AAAJw_TEbQk8oS3p7I8FLgetiAQADAgADeAADNgQ"

