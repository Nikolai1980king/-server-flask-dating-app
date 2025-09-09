# 🚀 Деплой на Beget VPS

## 📋 Подготовка к деплою

### 1. Регистрация на Beget
1. Перейдите на [beget.com](https://beget.com)
2. Нажмите "Регистрация"
3. Заполните форму регистрации
4. Подтвердите email

### 2. Выбор тарифа VPS
1. Войдите в панель управления
2. Выберите "VPS хостинг"
3. Выберите подходящий тариф:

```
Стартовый тариф (рекомендуется для начала):
├── CPU: 1 ядро
├── RAM: 1 GB
├── Диск: 10 GB SSD
├── Стоимость: от 100₽/месяц
└── Подходит для: тестирования, MVP

Средний тариф:
├── CPU: 2 ядра
├── RAM: 2 GB
├── Диск: 20 GB SSD
├── Стоимость: от 200₽/месяц
└── Подходит для: продакшена

Продвинутый тариф:
├── CPU: 4 ядра
├── RAM: 4 GB
├── Диск: 40 GB SSD
├── Стоимость: от 400₽/месяц
└── Подходит для: высоконагруженных приложений
```

## 🖥️ Создание VPS

### Шаг 1: Создание сервера
1. В панели управления выберите "VPS хостинг"
2. Нажмите "Заказать VPS"
3. Выберите тариф (рекомендую "Стартовый")
4. Выберите операционную систему: **Ubuntu 20.04 LTS**
5. Нажмите "Заказать"

### Шаг 2: Получение данных для подключения
После создания VPS вы получите:
- **IP адрес сервера**
- **Логин**: `root`
- **Пароль** (будет отправлен на email)

## 🔧 Настройка сервера

### Подключение к серверу
```bash
ssh root@YOUR_SERVER_IP
```

### Обновление системы
```bash
apt update && apt upgrade -y
```

### Установка необходимых пакетов
```bash
apt install python3 python3-pip python3-venv nginx supervisor git curl -y
```

### Создание пользователя для приложения
```bash
adduser flaskapp
usermod -aG sudo flaskapp
```

## 📦 Деплой приложения

### Клонирование репозитория
```bash
su - flaskapp
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

### Установка PostgreSQL
```bash
# Вернуться к root пользователю
exit

# Установка PostgreSQL
apt install postgresql postgresql-contrib -y

# Запуск PostgreSQL
systemctl start postgresql
systemctl enable postgresql
```

### Создание базы данных
```bash
# Переключение на пользователя postgres
su - postgres

# Создание базы данных и пользователя
createdb flaskapp
psql -c "CREATE USER flaskapp WITH PASSWORD 'your-password';"
psql -c "GRANT ALL PRIVILEGES ON DATABASE flaskapp TO flaskapp;"

# Выход
exit
```

## ⚙️ Настройка переменных окружения

### Создание файла конфигурации
```bash
su - flaskapp
cd your-repo
nano .env
```

Содержимое файла:
```env
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://flaskapp:your-password@localhost:5432/flaskapp
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
# Вернуться к root пользователю
exit

nano /etc/supervisor/conf.d/flaskapp.conf
```

Содержимое файла:
```ini
[program:flaskapp]
directory=/home/flaskapp/your-repo
command=/home/flaskapp/your-repo/venv/bin/gunicorn --workers 2 --bind unix:flaskapp.sock -m 007 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/flaskapp/flaskapp.err.log
stdout_logfile=/var/log/flaskapp/flaskapp.out.log
user=flaskapp
environment=FLASK_ENV="production"
```

### Создание папки для логов
```bash
mkdir -p /var/log/flaskapp
chown flaskapp:flaskapp /var/log/flaskapp
```

## 🌐 Настройка Nginx

### Создание конфигурации
```bash
nano /etc/nginx/sites-available/flaskapp
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name YOUR_SERVER_IP;

    client_max_body_size 16M;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskapp/your-repo/flaskapp.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /home/flaskapp/your-repo/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

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
ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/
rm /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
```

## 🚀 Запуск приложения

### Создание таблиц базы данных
```bash
su - flaskapp
cd your-repo
source venv/bin/activate
python3 -c "from app import db; db.create_all()"
```

### Запуск supervisor
```bash
# Вернуться к root пользователю
exit

supervisorctl reread
supervisorctl update
supervisorctl start flaskapp
```

### Проверка статуса
```bash
supervisorctl status flaskapp
systemctl status nginx
```

## 🔐 Настройка SSL (опционально)

### Установка Certbot
```bash
apt install certbot python3-certbot-nginx -y
```

### Получение SSL сертификата (если есть домен)
```bash
certbot --nginx -d your-domain.com
```

## 📊 Мониторинг и логи

### Просмотр логов приложения
```bash
tail -f /var/log/flaskapp/flaskapp.out.log
tail -f /var/log/flaskapp/flaskapp.err.log
```

### Просмотр логов Nginx
```bash
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Проверка процессов
```bash
supervisorctl status
systemctl status nginx
systemctl status postgresql
```

## 🔄 Обновление приложения

### Процесс обновления
```bash
# Подключение к серверу
ssh root@YOUR_SERVER_IP

# Переключение на пользователя приложения
su - flaskapp
cd your-repo

# Обновление кода
git pull origin main

# Обновление зависимостей
source venv/bin/activate
pip install -r requirements.txt

# Перезапуск приложения
exit
supervisorctl restart flaskapp
```

## 🗄️ Резервное копирование

### Резервная копия базы данных
```bash
# Создание резервной копии
su - postgres
pg_dump flaskapp > /tmp/flaskapp_backup.sql

# Скачивание резервной копии
exit
scp root@YOUR_SERVER_IP:/tmp/flaskapp_backup.sql ./
```

### Резервная копия файлов
```bash
# Создание архива
tar -czf backup-$(date +%Y%m%d).tar.gz /home/flaskapp/your-repo/static/uploads

# Скачивание архива
scp root@YOUR_SERVER_IP:backup-*.tar.gz ./
```

## 💰 Стоимость Beget VPS

### Тарифы:
- **Стартовый**: от 100₽/месяц (1 CPU, 1 GB RAM, 10 GB SSD)
- **Средний**: от 200₽/месяц (2 CPU, 2 GB RAM, 20 GB SSD)
- **Продвинутый**: от 400₽/месяц (4 CPU, 4 GB RAM, 40 GB SSD)

### Рекомендации:
- **Для тестирования**: Стартовый тариф (100₽/месяц)
- **Для продакшена**: Средний тариф (200₽/месяц)
- **Для высоконагруженных приложений**: Продвинутый тариф (400₽/месяц)

## 🎯 Преимущества Beget VPS

### ✅ Совместимость:
- Python 3.8+ поддерживается
- Flask работает без проблем
- PostgreSQL для базы данных
- WebSocket для Socket.IO
- SSL сертификаты поддерживаются

### ✅ Российский хостинг:
- Данные хранятся в России
- Быстрая скорость в России
- Техподдержка на русском языке
- Соответствие 152-ФЗ

### ✅ Простота:
- Простая панель управления
- Быстрая настройка
- Хорошая техподдержка
- Низкая стоимость

## 🆘 Решение проблем

### Приложение не запускается:
```bash
# Проверка логов
tail -f /var/log/flaskapp/flaskapp.err.log

# Проверка переменных окружения
su - flaskapp
cd your-repo
source venv/bin/activate
python3 -c "import os; print(os.environ.get('DATABASE_URL'))"
```

### Проблемы с базой данных:
```bash
# Проверка подключения
su - postgres
psql -d flaskapp -c "SELECT version();"

# Проверка пользователей
psql -c "\du"
```

### Проблемы с загрузкой файлов:
```bash
# Проверка прав доступа
ls -la /home/flaskapp/your-repo/static/uploads

# Исправление прав
chown -R flaskapp:flaskapp /home/flaskapp/your-repo/static
chmod -R 755 /home/flaskapp/your-repo/static
```

## 🎉 Заключение

**Beget VPS - отличный выбор для вашего приложения!**

### ✅ Что будет работать:
- Все функции Flask приложения
- Чат с Socket.IO
- Загрузка фотографий
- Геолокация
- База данных PostgreSQL

### 🚀 Следующие шаги:
1. Зарегистрируйтесь на Beget
2. Выберите VPS тариф
3. Следуйте этому руководству
4. Настройте домен и SSL (опционально)

**Удачи с деплоем!** 🚀 