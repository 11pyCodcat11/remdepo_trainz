# Настройка автоматической проверки платежей

## 🚀 Способы автоматизации

### 1. **YooKassa Webhooks (рекомендуемый)**

**Преимущества:**
- ✅ Мгновенное уведомление о платеже
- ✅ Надежность - YooKassa гарантирует доставку
- ✅ Экономия ресурсов

**Настройка:**
1. В личном кабинете YooKassa перейдите в "Настройки" → "Webhooks"
2. Добавьте URL: `https://your-domain.com/webhook/yookassa`
3. Выберите события: `payment.succeeded`
4. Сохраните настройки

**Что происходит:**
- YooKassa отправляет POST запрос на ваш webhook
- Бот автоматически обновляет статус заказа
- Пользователь получает уведомление в Telegram

### 2. **Периодическая проверка (резервный)**

**Преимущества:**
- ✅ Работает без настройки webhook
- ✅ Не требует публичного URL
- ✅ Простота настройки

**Как работает:**
- Каждые 10 секунд проверяет все pending заказы
- Запрашивает статус через YooKassa API
- Обновляет статус при успешной оплате

## 🔧 Настройка сервера

### Для webhook (если используете):

1. **Откройте порт 8080:**
```bash
sudo ufw allow 8080
```

2. **Настройте nginx (опционально):**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location /webhook/yookassa {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

3. **Получите SSL сертификат:**
```bash
sudo certbot --nginx -d your-domain.com
```

## 📊 Мониторинг

### Логи webhook:
```bash
tail -f /var/log/nginx/access.log | grep webhook
```

### Логи бота:
```bash
journalctl -u your-bot-service -f
```

### Проверка webhook:
```bash
curl -X POST https://your-domain.com/webhook/yookassa \
  -H "Content-Type: application/json" \
  -d '{"event":"payment.succeeded","object":{"id":"test","status":"succeeded"}}'
```

## ⚡ Рекомендации

1. **Используйте webhook** для продакшена
2. **Периодическая проверка** как fallback
3. **Мониторьте логи** для отладки
4. **Тестируйте** на тестовых платежах

## 🐛 Отладка

### Webhook не работает:
- Проверьте URL в настройках YooKassa
- Убедитесь что порт 8080 открыт
- Проверьте логи nginx/bota

### Периодическая проверка не работает:
- Проверьте что APScheduler запущен
- Убедитесь что YooKassa API доступен
- Проверьте логи бота

## 📈 Производительность

- **Webhook**: мгновенно, 0 задержка
- **Периодическая**: до 10 секунд задержки
- **Гибридный**: webhook + периодическая как backup
