# Руководство по деплою в продакшен

## Варианты деплоя

### 1. 🚀 **Heroku (Рекомендуется для начала)**
Самый простой способ для быстрого запуска.

#### Подготовка к Heroku:
```bash
# Создайте файл Procfile (если его нет)
echo "web: gunicorn app:app" > Procfile

# Создайте runtime.txt
echo "python-3.11.0" > runtime.txt

# Обновите requirements.txt
pip freeze > requirements.txt
```

#### Деплой на Heroku:
```bash
# Установите Heroku CLI
# https://devcenter.heroku.com/articles/heroku-cli

# Создайте приложение
heroku create your-app-name

# Добавьте базу данных PostgreSQL
heroku addons:create heroku-postgresql:mini

# Настройте переменные окружения
heroku config:set SECRET_KEY=your-secret-key-here
heroku config:set FLASK_ENV=production

# Деплой
git add .
git commit -m "Deploy to production"
git push heroku main
```

### 2. 🌐 **VPS (DigitalOcean, AWS, Vultr)**
Полный контроль над сервером.

#### Подготовка сервера:
```bash
# Обновите систему
sudo apt update && sudo apt upgrade -y

# Установите необходимые пакеты
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Создайте пользователя для приложения
sudo adduser flaskapp
sudo usermod -aG sudo flaskapp
```

#### Настройка приложения:
```bash
# Переключитесь на пользователя приложения
sudo su - flaskapp

# Клонируйте репозиторий
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Создайте виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
pip install gunicorn

# Создайте базу данных
python3 -c "from app import db; db.create_all()"
```

#### Настройка Gunicorn:
```bash
# Создайте файл конфигурации
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
```

#### Настройка Nginx:
```bash
sudo nano /etc/nginx/sites-available/flaskapp
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskapp/your-repo/flaskapp.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/flaskapp/your-repo/static;
    }
}
```

```bash
# Активируйте сайт
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Запустите supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flaskapp
```

### 3. ☁️ **Docker (Универсальный)**
Контейнеризация для любого хостинга.

#### Создайте Dockerfile:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
```

#### Создайте docker-compose.yml:
```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key
    volumes:
      - ./static:/app/static
    depends_on:
      - db
  
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=flaskapp
      - POSTGRES_USER=flaskapp
      - POSTGRES_PASSWORD=your-password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

#### Запуск с Docker:
```bash
# Сборка и запуск
docker-compose up --build

# В продакшене
docker-compose -f docker-compose.prod.yml up -d
```

## 🔧 Подготовка приложения к продакшену

### 1. Обновите конфигурацию
```python
# config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Настройки для продакшена
    DEBUG = False
    TESTING = False
    
    # Настройки безопасности
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Настройки загрузки файлов
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'static/uploads'
```

### 2. Добавьте обработку ошибок
```python
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('500.html'), 500
```

### 3. Настройте логирование
```python
import logging
from logging.handlers import RotatingFileHandler
import os

if not app.debug:
    if not os.path.exists('logs'):
        os.mkdir('logs')
    file_handler = RotatingFileHandler('logs/flaskapp.log', maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('Flaskapp startup')
```

### 4. Обновите requirements.txt
```txt
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-SocketIO==5.3.6
gunicorn==21.2.0
geopy==2.4.0
python-dotenv==1.0.0
psycopg2-binary==2.9.7
redis==5.0.1
```

## 🔒 Безопасность

### 1. Переменные окружения
```bash
# .env (не добавляйте в git)
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://user:password@localhost/dbname
FLASK_ENV=production
```

### 2. HTTPS/SSL
```bash
# Установите Certbot для Let's Encrypt
sudo apt install certbot python3-certbot-nginx

# Получите SSL сертификат
sudo certbot --nginx -d your-domain.com
```

### 3. Firewall
```bash
# Настройте UFW
sudo ufw allow 22
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable
```

## 📊 Мониторинг

### 1. Логи
```bash
# Просмотр логов приложения
sudo tail -f /var/log/flaskapp/flaskapp.out.log

# Просмотр логов Nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### 2. Мониторинг системы
```bash
# Установите htop для мониторинга
sudo apt install htop

# Проверка использования ресурсов
htop
df -h
free -h
```

## 🚀 Автоматический деплой

### GitHub Actions (для VPS):
```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /home/flaskapp/your-repo
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo supervisorctl restart flaskapp
```

## 💰 Стоимость хостинга

### Heroku:
- **Hobby**: $7/месяц
- **Standard**: $25/месяц

### DigitalOcean:
- **Basic Droplet**: $5-10/месяц
- **Managed Database**: $15/месяц

### AWS:
- **EC2 t3.micro**: $8-10/месяц
- **RDS**: $15-20/месяц

## 🎯 Рекомендации

### Для начала (MVP):
1. **Heroku** - самый простой и быстрый
2. **DigitalOcean App Platform** - хорошая альтернатива

### Для масштабирования:
1. **AWS/GCP** - полный контроль и масштабируемость
2. **Docker + Kubernetes** - для микросервисов

### Для продакшена:
1. Всегда используйте HTTPS
2. Настройте мониторинг и логирование
3. Регулярно обновляйте зависимости
4. Делайте резервные копии базы данных

## 📞 Поддержка

Если у вас возникнут проблемы с деплоем:
1. Проверьте логи приложения
2. Убедитесь, что все переменные окружения настроены
3. Проверьте, что порты открыты
4. Убедитесь, что база данных доступна 