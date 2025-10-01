# 🚀 Руководство по деплою на ятутаю.рф

## 📋 Подготовка к деплою

### 1. Требования к серверу
- Ubuntu 20.04+ или Debian 10+
- Python 3.8+
- Git
- Nginx (рекомендуется)
- SSL сертификат (Let's Encrypt)

### 2. Подготовка локального проекта
Убедитесь, что все изменения закоммичены и запушены:
```bash
git add .
git commit -m "Подготовка к деплою"
git push origin master
```

## 🔧 Деплой на сервер

### Шаг 1: Подключение к серверу
```bash
ssh user@your-server-ip
```

### Шаг 2: Клонирование репозитория
```bash
cd /home/$USER
git clone https://github.com/your-username/flask_server.git
cd flask_server
```

### Шаг 3: Запуск скрипта деплоя
```bash
chmod +x deploy_yatutayu.sh
./deploy_yatutayu.sh
```

Скрипт автоматически:
- ✅ Остановит старое приложение
- ✅ Обновит код из git
- ✅ Создаст виртуальное окружение
- ✅ Установит зависимости
- ✅ Инициализирует базу данных
- ✅ Создаст systemd сервис
- ✅ Настроит nginx
- ✅ Настроит файрвол
- ✅ Запустит приложение

## ⚙️ Настройка переменных окружения

### 1. Создайте файл .env на сервере:
```bash
cp env_production.txt .env
nano .env
```

### 2. Настройте переменные:
```bash
# Измените секретный ключ
SECRET_KEY=your-unique-secret-key-here

# Настройте YooKassa (если нужно)
YOOKASSA_SHOP_ID=your-shop-id
YOOKASSA_SECRET_KEY=your-secret-key

# Убедитесь, что webhook URL правильный
YOOKASSA_WEBHOOK_URL=https://ятутаю.рф/yookassa/webhook
```

## 🔒 Настройка SSL сертификата

### 1. Установите Certbot:
```bash
sudo apt update
sudo apt install certbot python3-certbot-nginx
```

### 2. Получите SSL сертификат:
```bash
sudo certbot --nginx -d ятутаю.рф -d www.ятутаю.рф
```

### 3. Настройте автообновление:
```bash
sudo crontab -e
# Добавьте строку:
0 12 * * * /usr/bin/certbot renew --quiet
```

## 🌐 Настройка DNS

Убедитесь, что DNS записи настроены правильно:
- **A запись**: `@` → IP вашего сервера
- **A запись**: `www` → IP вашего сервера

## 📊 Мониторинг и управление

### Полезные команды:
```bash
# Статус приложения
sudo systemctl status dating-app

# Перезапуск
sudo systemctl restart dating-app

# Логи в реальном времени
sudo journalctl -u dating-app -f

# Остановка
sudo systemctl stop dating-app

# Проверка портов
netstat -tlnp | grep :5000
```

### Проверка работы:
```bash
# Проверить доступность
curl -I http://ятутаю.рф

# Проверить SSL
curl -I https://ятутаю.рф
```

## 🔄 Обновление приложения

### Автоматическое обновление:
```bash
cd /home/$USER/flask_server
git pull origin master
sudo systemctl restart dating-app
```

### Или используйте скрипт деплоя снова:
```bash
./deploy_yatutayu.sh
```

## 🛠️ Устранение неполадок

### Проблема: Приложение не запускается
```bash
# Проверьте логи
sudo journalctl -u dating-app -n 50

# Проверьте зависимости
source venv/bin/activate
pip install -r requirements.txt
```

### Проблема: Nginx не работает
```bash
# Проверьте конфигурацию
sudo nginx -t

# Перезапустите nginx
sudo systemctl restart nginx
```

### Проблема: База данных
```bash
# Пересоздайте базу данных
cd /home/$USER/flask_server
source venv/bin/activate
python3 -c "
from app import app, db
with app.app_context():
    db.drop_all()
    db.create_all()
    print('База данных пересоздана')
"
```

## 📱 Настройка YooKassa

### 1. В личном кабинете YooKassa:
- Настройте webhook URL: `https://ятутаю.рф/yookassa/webhook`
- Убедитесь, что тестовый режим отключен
- Проверьте настройки уведомлений

### 2. Проверьте платежи:
- Откройте админ-панель: `https://ятутаю.рф/admin/payments`
- Проверьте логи платежей

## 🔐 Безопасность

### 1. Настройте файрвол:
```bash
sudo ufw status
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
```

### 2. Регулярные бэкапы:
```bash
# Создайте скрипт бэкапа
cat > backup.sh << 'EOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
cp /home/$USER/flask_server/instance/dating_app.db /home/$USER/backup_$DATE.db
find /home/$USER/backup_*.db -mtime +7 -delete
EOF

chmod +x backup.sh

# Добавьте в cron
crontab -e
# Добавьте: 0 2 * * * /home/$USER/flask_server/backup.sh
```

## ✅ Финальная проверка

После деплоя проверьте:
- [ ] Приложение доступно по https://ятутаю.рф
- [ ] SSL сертификат работает
- [ ] Создание профилей работает
- [ ] Платежи YooKassa работают
- [ ] WebSocket соединения работают
- [ ] Загрузка файлов работает
- [ ] Админ-панель доступна

## 📞 Поддержка

Если возникли проблемы:
1. Проверьте логи: `sudo journalctl -u dating-app -f`
2. Проверьте статус сервисов: `sudo systemctl status dating-app nginx`
3. Проверьте доступность портов: `netstat -tlnp`

---

**🎉 Поздравляем! Ваше приложение знакомств успешно развернуто на ятутаю.рф!**