# 🔐 Настройка GitHub Secrets для CI/CD

## 📋 **Данные вашего сервера:**
- **IP:** 193.106.174.56
- **Пользователь:** root  
- **Пароль:** Fr5CN2DlPL5U
- **Домен:** vm-74902.iq-hosting.ru

## 🚀 **Пошаговая настройка:**

### **1. Добавьте публичный ключ на сервер:**

Выполните на вашем компьютере:
```bash
ssh-copy-id -i ~/.ssh/remdepo_server_key.pub root@193.106.174.56
```

Или вручную:
```bash
# Подключитесь к серверу
ssh root@193.106.174.56

# Создайте папку .ssh
mkdir -p ~/.ssh
chmod 700 ~/.ssh

# Добавьте публичный ключ
echo "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAACAQDKfIpuFf8ICHATqAyV33AWDeDL+hTGhtIyEXf66VgAPdFFxNu8YQ5qNqHomBP6rRhv+XXiX1aAnOM7ezmJY41EEYs5X9UOddXbb8rxFCym5TnrYXVHEgzpdDD2OnQZsG0LElMxXCKfMfWkh/C6LNxSA0mKlx7kmxFZ0evovZ354hGV/2gafl6AZVghXKKED8uxk3v5bTY625pQMjo7dRGspchrGcruSZ/Oij8WeG+Po67wDurjAd88Gk2ERNCJR2asa9i5x0/1aZzTW891ZZ0JAXbqjpDAQS3lMF8sH06FZ7oY3mYIKxAsBACLjy41ph4k7mNo13gBwhGbfIGBNna9e/pnQs5t8My+Jyn1cqFwsMHbdh24tmwbr3egBTOsIvwlbZ7MmJ0Zz2PJ4sRgDUaP8oGNXxs2NGqQ9S88zDcIPh/YUYxbqfRl/BWj3ACQd5aUMtmELfsuaZ0BqRPwjmXADOwU7jntevoB5kcgz0tFpKmRqwq8lYvYCqHxnTOVibDMySkEsM3Qy+Q3DaNQEtFZminhG6XShrtggEMk3EObDJvuDptkjhqRkrSVcspqebgGGONQMmX+ck1NrqC6D6MFkghgLDmadFYO7+3ge232tVQalbls7o5yVld2I50qqVYQfzwsy5ip+asmHngSq7xwPvDZkuDM1pU7EZgXx36upw== timofej@MacBook-Air-timofej.local" >> ~/.ssh/authorized_keys

# Установите права
chmod 600 ~/.ssh/authorized_keys
```

### **2. Настройте GitHub Secrets:**

Перейдите: `https://github.com/11pyCodcat11/remdepo_trainz/settings/secrets/actions`

Нажмите **"New repository secret"** и добавьте:

#### **SERVER_HOST:**
```
193.106.174.56
```

#### **SERVER_USER:**
```
root
```

#### **SERVER_SSH_KEY:**
```
-----BEGIN OPENSSH PRIVATE KEY-----
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
-----END OPENSSH PRIVATE KEY-----
```

#### **SERVER_PORT:**
```
22
```

### **3. Обновите пути в workflow:**

В файле `.github/workflows/deploy.yml` замените:
```yaml
cd /path/to/your/remdepo_bot
```
На реальный путь к проекту на сервере (например: `/root/remdepo_bot`)

### **4. Создайте systemd service на сервере:**

```bash
# Подключитесь к серверу
ssh root@193.106.174.56

# Создайте service файл
nano /etc/systemd/system/remdepo-bot.service
```

Содержимое файла:
```ini
[Unit]
Description=RemDepo Telegram Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/remdepo_bot
Environment=PATH=/root/remdepo_bot/venv/bin
ExecStart=/root/remdepo_bot/venv/bin/python -m bot.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Активируйте:
```bash
systemctl daemon-reload
systemctl enable remdepo-bot
systemctl start remdepo-bot
```

## ✅ **Готово!**

Теперь CI/CD будет работать:
- **Push в main** → автоматический деплой
- **Ручной деплой** через GitHub Actions
- **Безопасность БД** гарантирована
