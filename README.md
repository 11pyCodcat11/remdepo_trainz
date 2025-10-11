# Remdepo Bot - Telegram Shop Bot

Telegram бот для интернет-магазина с поддержкой платежей через YooKassa.

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose
- Telegram Bot Token
- YooKassa API ключи

### Установка и запуск

1. **Клонируйте репозиторий:**
   ```bash
   git clone <repository-url>
   cd remdepo_bot
   ```

2. **Настройте переменные окружения:**
   ```bash
   cp env.example .env
   nano .env
   ```

3. **Заполните необходимые переменные в .env:**
   ```env
   BOT_TOKEN=your_bot_token_here
   TELEGRAM_PROVIDER_TOKEN=your_provider_token_here
   YOOKASSA_SHOP_ID=your_shop_id_here
   YOOKASSA_SECRET_KEY=your_secret_key_here
   ```

4. **Запустите бота:**
   ```bash
   ./deploy.sh
   ```

## 🐳 Docker Deployment

### Основные команды

```bash
# Запуск бота
./deploy.sh

# Мониторинг
./monitor.sh

# Просмотр логов
docker-compose logs -f remdepo-bot

# Перезапуск
docker-compose restart remdepo-bot

# Остановка
docker-compose down
```

### Устойчивость к падениям

Бот настроен для автоматического восстановления:

- **Restart Policy:** `unless-stopped` - автоматический перезапуск при падении
- **Health Check:** проверка состояния каждые 30 секунд
- **Resource Limits:** ограничения памяти и CPU
- **Log Rotation:** автоматическая ротация логов
- **Watchtower:** автоматическое обновление образов

### Мониторинг

```bash
# Проверка статуса
docker-compose ps

# Использование ресурсов
docker stats remdepo-bot

# Логи в реальном времени
docker-compose logs -f remdepo-bot

# Последние ошибки
docker-compose logs --tail=50 remdepo-bot | grep ERROR
```

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | Обязательная |
|------------|----------|--------------|
| `BOT_TOKEN` | Токен Telegram бота | ✅ |
| `TELEGRAM_PROVIDER_TOKEN` | Токен для платежей | ✅ |
| `YOOKASSA_SHOP_ID` | ID магазина YooKassa | ✅ |
| `YOOKASSA_SECRET_KEY` | Секретный ключ YooKassa | ✅ |
| `DATABASE_URL` | URL базы данных | ❌ (по умолчанию SQLite) |
| `LOG_LEVEL` | Уровень логирования | ❌ (по умолчанию INFO) |

### Структура проекта

```
remdepo_bot/
├── bot/                    # Исходный код бота
│   ├── handlers/          # Обработчики команд
│   ├── keyboards/         # Клавиатуры
│   ├── database/          # Модели и репозитории
│   └── services/          # Бизнес-логика
├── docker-compose.yml     # Docker Compose конфигурация
├── Dockerfile            # Docker образ
├── deploy.sh            # Скрипт деплоя
├── monitor.sh           # Скрипт мониторинга
└── env.example          # Пример переменных окружения
```

## 📊 Логирование

Бот использует структурированное логирование с эмодзи для удобства:

- 🔍 **[CATALOG]** - операции с каталогом
- 📂 **[CATEGORY]** - операции с категориями
- 🛍️ **[PRODUCT]** - операции с товарами
- ℹ️ **[ABOUT_PRODUCT]** - информация о товарах
- 🔄 **[NAVIGATION]** - навигация
- 💳 **[PAYMENT]** - платежи
- 🧺 **[CART]** - корзина

## 🛠️ Разработка

### Локальная разработка

```bash
# Установка зависимостей
pip install -r requirements.txt

# Запуск бота
python -m bot.main
```

### Тестирование

```bash
# Запуск тестов
python -m pytest

# Проверка кода
flake8 bot/
black bot/
```

## 🔒 Безопасность

- Контейнер запускается от непривилегированного пользователя
- Ограничения ресурсов предотвращают DoS атаки
- Логи не содержат чувствительных данных
- Переменные окружения изолированы

## 📈 Производительность

- **Memory Limit:** 512MB
- **CPU Limit:** 0.5 cores
- **Log Rotation:** 10MB файлы, 3 файла максимум
- **Health Check:** каждые 30 секунд

## 🆘 Устранение неполадок

### Бот не запускается

```bash
# Проверьте логи
docker-compose logs remdepo-bot

# Проверьте переменные окружения
docker-compose config

# Пересоберите образ
docker-compose build --no-cache
```

### Проблемы с базой данных

```bash
# Проверьте права доступа
ls -la bot.db

# Пересоздайте базу данных
rm bot.db
docker-compose restart remdepo-bot
```

### Высокое использование ресурсов

```bash
# Мониторинг ресурсов
docker stats remdepo-bot

# Ограничение ресурсов в docker-compose.yml
```

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `docker-compose logs remdepo-bot`
2. Проверьте статус: `docker-compose ps`
3. Перезапустите: `docker-compose restart remdepo-bot`

## 📄 Лицензия

MIT License
