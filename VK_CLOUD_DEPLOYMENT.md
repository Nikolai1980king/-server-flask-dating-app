# 🚀 Деплой на VK Cloud (Mail.ru Cloud)

## 📋 Подготовка к деплою

### 1. Регистрация на VK Cloud
1. Перейдите на [mcs.mail.ru](https://mcs.mail.ru)
2. Нажмите "Начать бесплатно"
3. Зарегистрируйтесь через VK ID или email
4. Подтвердите email
5. Добавьте способ оплаты (для верификации)

### 2. Создание проекта
1. Войдите в панель управления
2. Создайте новый проект
3. Выберите регион (Москва)
4. Настройте сеть

## 🖥️ Создание виртуальной машины

### Шаг 1: Создание VM
1. В панели управления выберите "Виртуальные машины"
2. Нажмите "Создать виртуальную машину"
3. Настройте параметры:

```
Имя: flask-dating-app
Операционная система: Ubuntu 20.04 LTS
Конфигурация: 
  - CPU: 2 ядра
  - RAM: 4 GB
  - Диск: 20 GB (SSD)
Сеть: default
Публичный IP: Да
```

### Шаг 2: Настройка безопасности
1. Создайте SSH ключ или используйте существующий
2. Настройте firewall (откройте порты 22, 80, 443)
3. Запишите IP адрес сервера

## 🔧 Настройка сервера

### Подключение к серверу
```bash
ssh ubuntu@your-server-ip
```

### Обновление системы
```bash
sudo apt update && sudo apt upgrade -y
```

### Установка необходимых пакетов
```bash
sudo apt install python3 python3-pip python3-venv nginx supervisor git curl -y
```

### Создание пользователя для приложения
```bash
sudo adduser flaskapp
sudo usermod -aG sudo flaskapp
```

## 📦 Деплой приложения

### Клонирование репозитория
```bash
sudo su - flaskapp
git clone https://github.com/your-username/your-repo.git
cd your-repo
```

### Создание виртуального окружения
```bash
python3 -m venv venv
source venv/bin/activate
```

### Установка зависимостей
```bash
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

### Создание папки для загрузок
```bash
mkdir -p static/uploads
chmod 755 static/uploads
```

## 🗄️ Настройка базы данных

### Создание PostgreSQL в VK Cloud
1. В панели управления выберите "Базы данных"
2. Нажмите "Создать кластер"
3. Выберите PostgreSQL
4. Настройте параметры:

```
Имя: flask-db
Версия: PostgreSQL 13
Конфигурация: s2.micro (1 CPU, 4 GB RAM)
Диск: 10 GB SSD
```

### Получение строки подключения
1. В настройках кластера найдите "Строка подключения"
2. Скопируйте строку вида:
```
postgresql://username:password@host:port/database
```

## ⚙️ Настройка переменных окружения

### Создание файла конфигурации
```bash
nano .env
```

Содержимое файла:
```env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://username:password@host:port/database
MAX_REGISTRATION_DISTANCE=3000
PROFILE_LIFETIME_HOURS=24
```

### Генерация секретного ключа
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

## 🔧 Настройка Gunicorn

### Создание конфигурации supervisor
```bash
sudo nano /etc/supervisor/conf.d/flaskapp.conf
```

Содержимое файла:
```ini
[program:flaskapp]
directory=/home/flaskapp/your-repo
command=/home/flaskapp/your-repo/venv/bin/gunicorn --workers 3 --bind unix:flaskapp.sock -m 007 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/flaskapp/flaskapp.err.log
stdout_logfile=/var/log/flaskapp/flaskapp.out.log
user=flaskapp
environment=FLASK_ENV="production"
```

### Создание папки для логов
```bash
sudo mkdir -p /var/log/flaskapp
sudo chown flaskapp:flaskapp /var/log/flaskapp
```

## 🌐 Настройка Nginx

### Создание конфигурации
```bash
sudo nano /etc/nginx/sites-available/flaskapp
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Увеличиваем лимит загрузки файлов
    client_max_body_size 16M;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskapp/your-repo/flaskapp.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support для Socket.IO
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /home/flaskapp/your-repo/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # WebSocket для Socket.IO
    location /socket.io {
        proxy_pass http://unix:/home/flaskapp/your-repo/flaskapp.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Активация сайта
```bash
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 🚀 Запуск приложения

### Создание таблиц базы данных
```bash
sudo su - flaskapp
cd your-repo
source venv/bin/activate
python3 -c "from app import db; db.create_all()"
```

### Запуск supervisor
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flaskapp
```

### Проверка статуса
```bash
sudo supervisorctl status flaskapp
sudo systemctl status nginx
```

## 🔐 Настройка SSL

### Установка Certbot
```bash
sudo apt install certbot python3-certbot-nginx -y
```

### Получение SSL сертификата
```bash
sudo certbot --nginx -d your-domain.com
```

### Автоматическое обновление
```bash
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Мониторинг и логи

### Просмотр логов приложения
```bash
sudo tail -f /var/log/flaskapp/flaskapp.out.log
sudo tail -f /var/log/flaskapp/flaskapp.err.log
```

### Просмотр логов Nginx
```bash
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Проверка процессов
```bash
sudo supervisorctl status
sudo systemctl status nginx
```

## 🔄 Обновление приложения

### Процесс обновления
```bash
# Подключение к серверу
ssh ubuntu@your-server-ip

# Переключение на пользователя приложения
sudo su - flaskapp
cd your-repo

# Обновление кода
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Перезапуск приложения
sudo supervisorctl restart flaskapp
```

## 🗄️ Резервное копирование

### Резервная копия базы данных
```bash
# В VK Cloud панели управления
1. Выберите ваш PostgreSQL кластер
2. Перейдите в "Резервные копии"
3. Нажмите "Создать резервную копию"
```

### Резервная копия файлов
```bash
# Создание архива
sudo tar -czf backup-$(date +%Y%m%d).tar.gz /home/flaskapp/your-repo/static/uploads

# Скачивание архива
scp ubuntu@your-server-ip:backup-*.tar.gz ./
```

## 💰 Стоимость VK Cloud

### Бесплатный период:
- **30 дней** бесплатного использования
- Полный доступ ко всем сервисам

### После бесплатного периода:
- **VM (2 CPU, 4 GB RAM)**: ~300₽/месяц
- **PostgreSQL (1 CPU, 4 GB RAM)**: ~400₽/месяц
- **Облачное хранилище**: ~50₽/месяц за 100 GB

**Итого**: ~750₽/месяц

## 🎯 Преимущества VK Cloud для вашего приложения

### ✅ Полная совместимость:
- Python 3.8+ поддерживается
- Flask работает без проблем
- PostgreSQL для базы данных
- WebSocket для Socket.IO
- SSL сертификаты включены

### ✅ Российская инфраструктура:
- Соответствие 152-ФЗ
- Данные хранятся в России
- Быстрая скорость в России
- Техподдержка на русском

### ✅ Масштабирование:
- Автоматическое масштабирование
- Load Balancer
- CDN для статических файлов
- Мониторинг и алерты

## 🆘 Решение проблем

### Приложение не запускается:
```bash
# Проверка логов
sudo tail -f /var/log/flaskapp/flaskapp.err.log

# Проверка переменных окружения
sudo su - flaskapp
cd your-repo
source venv/bin/activate
python3 -c "import os; print(os.environ.get('DATABASE_URL'))"
```

### Проблемы с базой данных:
```bash
# Проверка подключения
sudo su - flaskapp
cd your-repo
source venv/bin/activate
python3 -c "from app import db; print(db.engine.url)"
```

### Проблемы с загрузкой файлов:
```bash
# Проверка прав доступа
ls -la /home/flaskapp/your-repo/static/uploads

# Исправление прав
sudo chown -R flaskapp:flaskapp /home/flaskapp/your-repo/static
sudo chmod -R 755 /home/flaskapp/your-repo/static
```

## 🎉 Заключение

**VK Cloud - отличный выбор для вашего приложения!**

### ✅ Что будет работать:
- Все функции Flask приложения
- Чат с Socket.IO
- Загрузка фотографий
- Геолокация
- Яндекс.Карты
- База данных PostgreSQL

### 🚀 Следующие шаги:
1. Зарегистрируйтесь на VK Cloud
2. Создайте виртуальную машину
3. Следуйте этому руководству
4. Настройте домен и SSL
5. Запустите приложение

**Удачи с деплоем!** 🚀 