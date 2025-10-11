# 🛡️ БЕЗОПАСНЫЙ ДЕПЛОЙ - Защита базы данных

## ⚠️ ВАЖНО: Ваша база данных будет в безопасности!

### 🔒 **Многоуровневая защита БД:**

1. **Автоматический бэкап** перед каждым деплоем
2. **Проверка целостности** БД после обновления
3. **Автоматический откат** при проблемах
4. **Множественные копии** в разных местах

### 📋 **Пошаговая настройка (БЕЗОПАСНО):**

#### **Шаг 1: Создайте бэкап СЕЙЧАС (перед настройкой CI/CD)**
```bash
# На сервере выполните:
cd /path/to/your/remdepo_bot
cp bot.db bot.db.SAFE_BACKUP.$(date +%Y%m%d_%H%M%S)
echo "✅ Бэкап создан: bot.db.SAFE_BACKUP.$(date +%Y%m%d_%H%M%S)"
```

#### **Шаг 2: Настройте .gitignore для БД**
```bash
# В корне проекта создайте/обновите .gitignore:
echo "bot.db" >> .gitignore
echo "bot.db.backup.*" >> .gitignore
echo "*.db" >> .gitignore
```

#### **Шаг 3: Настройте GitHub Secrets**
В GitHub → Settings → Secrets and variables → Actions:
```
SERVER_HOST=your-server-ip
SERVER_USER=your-username  
SERVER_SSH_KEY=your-private-ssh-key
SERVER_PORT=22
```

#### **Шаг 4: Обновите пути в workflow**
Замените `/path/to/your/remdepo_bot` на реальный путь к проекту

### 🛡️ **Что происходит при деплое:**

1. **Остановка бота** (graceful)
2. **Создание бэкапа** БД с timestamp
3. **Сохранение копии** в `/tmp/remdepo_backups/`
4. **Обновление кода** (БД НЕ трогается!)
5. **Проверка целостности** БД
6. **Запуск бота** только если БД OK
7. **Откат** при любых проблемах

### 🔄 **Процедура отката (если что-то пойдет не так):**

```bash
# На сервере:
sudo systemctl stop remdepo-bot
cp bot.db.backup.YYYYMMDD_HHMMSS bot.db
sudo systemctl start remdepo-bot
```

### 📊 **Мониторинг безопасности:**

#### **Проверка бэкапов:**
```bash
ls -la bot.db.backup.*
ls -la /tmp/remdepo_backups/
```

#### **Проверка БД:**
```bash
sqlite3 bot.db "SELECT COUNT(*) FROM users;"
sqlite3 bot.db "SELECT COUNT(*) FROM orders;"
```

#### **Проверка бота:**
```bash
sudo systemctl status remdepo-bot
sudo journalctl -u remdepo-bot -f
```

### 🚨 **Экстренные процедуры:**

#### **Если деплой сломал БД:**
```bash
# 1. Остановить бота
sudo systemctl stop remdepo-bot

# 2. Найти последний бэкап
ls -la bot.db.backup.* | tail -1

# 3. Восстановить БД
cp bot.db.backup.YYYYMMDD_HHMMSS bot.db

# 4. Запустить бота
sudo systemctl start remdepo-bot
```

#### **Если бот не запускается:**
```bash
# Проверить логи
sudo journalctl -u remdepo-bot -n 50

# Проверить БД
sqlite3 bot.db ".tables"

# Восстановить из бэкапа
cp /tmp/remdepo_backups/bot.db.backup.YYYYMMDD_HHMMSS bot.db
```

### ✅ **Гарантии безопасности:**

- ✅ **БД НЕ перезаписывается** при деплое
- ✅ **Множественные бэкапы** создаются автоматически
- ✅ **Проверка целостности** перед запуском
- ✅ **Автоматический откат** при проблемах
- ✅ **Сохранение в /tmp/** как дополнительная защита

### 🎯 **Результат:**

Ваша база данных будет **ПОЛНОСТЬЮ ЗАЩИЩЕНА**:
- При каждом деплое создается бэкап
- БД проверяется на целостность
- При любых проблемах - автоматический откат
- Множественные копии в разных местах

**Можете смело настраивать CI/CD - ваши данные в безопасности!** 🛡️
