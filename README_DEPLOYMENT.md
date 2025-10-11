# 🚀 CI/CD Deployment Setup

## Настройка автоматического деплоя

### 1. **GitHub Secrets**

Добавьте в настройки репозитория (Settings → Secrets and variables → Actions) следующие секреты:

```
SERVER_HOST=your-server-ip
SERVER_USER=your-username
SERVER_SSH_KEY=your-private-ssh-key
SERVER_PORT=22
```

### 2. **Настройка сервера**

#### Создайте systemd service для бота:

```bash
sudo nano /etc/systemd/system/remdepo-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=RemDepo Telegram Bot
After=network.target

[Service]
Type=simple
User=your-username
WorkingDirectory=/path/to/your/remdepo_bot
Environment=PATH=/path/to/your/remdepo_bot/venv/bin
ExecStart=/path/to/your/remdepo_bot/venv/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Активируйте сервис:
```bash
sudo systemctl daemon-reload
sudo systemctl enable remdepo-bot
sudo systemctl start remdepo-bot
```

### 3. **Workflows**

#### **Автоматический деплой** (`deploy.yml`):
- Срабатывает при push в `main` ветку
- Автоматически деплоит на сервер
- Останавливает бота → обновляет код → запускает бота

#### **Ручной деплой** (`manual-deploy.yml`):
- Запускается вручную через GitHub Actions
- Можно выбрать окружение (production/staging)
- Можно пропустить тесты

### 4. **Использование**

#### Автоматический деплой:
```bash
git add .
git commit -m "Update bot features"
git push origin main
# Автоматически запустится деплой
```

#### Ручной деплой:
1. Перейдите в GitHub → Actions
2. Выберите "Manual Deploy"
3. Нажмите "Run workflow"
4. Выберите параметры и запустите

### 5. **Мониторинг**

#### Проверка статуса бота:
```bash
sudo systemctl status remdepo-bot
sudo journalctl -u remdepo-bot -f
```

#### Проверка логов:
```bash
tail -f /var/log/remdepo-bot.log
```

### 6. **Безопасность**

- SSH ключи должны быть без пароля
- Используйте отдельного пользователя для бота
- Регулярно обновляйте зависимости
- Мониторьте логи на предмет ошибок

### 7. **Откат изменений**

Если что-то пошло не так:
```bash
# Остановить бота
sudo systemctl stop remdepo-bot

# Откатить к предыдущему коммиту
git reset --hard HEAD~1

# Запустить бота
sudo systemctl start remdepo-bot
```

## 🎯 **Результат**

Теперь вы можете:
- ✅ **Push в main** → автоматический деплой
- ✅ **Ручной деплой** через GitHub Actions
- ✅ **Бэкап БД** перед каждым деплоем
- ✅ **Автоматические тесты** перед деплоем
- ✅ **Мониторинг статуса** бота

**Настройка займет 10-15 минут!** 🚀
