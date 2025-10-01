#!/bin/bash

# 🚀 Упрощенный деплой на Beget VPS
# Использование: ./deploy_beget_simple.sh [server-ip]

set -e

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверка аргументов
SERVER_IP=${1:-""}

if [ -z "$SERVER_IP" ]; then
    print_error "Не указан IP адрес сервера!"
    print_info "Использование: ./deploy_beget_simple.sh [server-ip]"
    print_info "Пример: ./deploy_beget_simple.sh 212.67.11.50"
    exit 1
fi

print_info "🚀 Начинаем упрощенный деплой на Beget VPS..."
print_info "Сервер: $SERVER_IP"

# Проверка необходимых файлов
print_info "Проверяем необходимые файлы..."

REQUIRED_FILES=("app.py" "requirements.txt")
MISSING_FILES=()

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        MISSING_FILES+=("$file")
    fi
done

if [ ${#MISSING_FILES[@]} -ne 0 ]; then
    print_error "Отсутствуют необходимые файлы:"
    for file in "${MISSING_FILES[@]}"; do
        print_error "  - $file"
    done
    exit 1
fi

print_success "Все необходимые файлы найдены"

# Создание папки для загрузок
if [ ! -d "static/uploads" ]; then
    print_info "Создаем папку для загрузок..."
    mkdir -p static/uploads
    print_success "Папка static/uploads создана"
fi

# Генерация секретного ключа
print_info "Генерируем секретный ключ..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
print_success "Секретный ключ сгенерирован"

# Создание файла конфигурации
print_info "Создаем файл конфигурации..."
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$SECRET_KEY
DATABASE_URL=postgresql://flaskapp:password@localhost:5432/flaskapp
MAX_REGISTRATION_DISTANCE=3000
PROFILE_LIFETIME_HOURS=24
EOF
print_success "Файл .env создан"

print_info "🔧 Начинаем настройку сервера..."
print_warning "Вам нужно будет ввести пароль от сервера несколько раз"

# Обновление системы
print_info "Обновляем систему..."
ssh root@$SERVER_IP "apt update && apt upgrade -y"

# Установка пакетов
print_info "Устанавливаем необходимые пакеты..."
ssh root@$SERVER_IP "apt install python3 python3-pip python3-venv nginx supervisor git curl postgresql postgresql-contrib -y"

# Создание пользователя
print_info "Создаем пользователя для приложения..."
ssh root@$SERVER_IP "adduser --disabled-password --gecos '' flaskapp || true"
ssh root@$SERVER_IP "usermod -aG sudo flaskapp"

# Создание папки для логов
print_info "Создаем папки для логов..."
ssh root@$SERVER_IP "mkdir -p /var/log/flaskapp"
ssh root@$SERVER_IP "chown flaskapp:flaskapp /var/log/flaskapp"

# Создание директории приложения
print_info "Создаем директорию приложения..."
ssh root@$SERVER_IP "mkdir -p /home/flaskapp/app"

# Копирование файлов
print_info "Копируем файлы приложения..."
scp app.py root@$SERVER_IP:/home/flaskapp/app/
scp requirements.txt root@$SERVER_IP:/home/flaskapp/app/
scp .env root@$SERVER_IP:/home/flaskapp/app/

# Настройка прав доступа
print_info "Настраиваем права доступа..."
ssh root@$SERVER_IP "chown -R flaskapp:flaskapp /home/flaskapp/app"

# Настройка виртуального окружения
print_info "Настраиваем виртуальное окружение..."
ssh root@$SERVER_IP "cd /home/flaskapp/app && sudo -u flaskapp python3 -m venv venv"
ssh root@$SERVER_IP "cd /home/flaskapp/app && sudo -u flaskapp /home/flaskapp/app/venv/bin/pip install -r requirements.txt"
ssh root@$SERVER_IP "cd /home/flaskapp/app && sudo -u flaskapp /home/flaskapp/app/venv/bin/pip install gunicorn psycopg2-binary"

# Создание папки для загрузок
print_info "Создаем папку для загрузок..."
ssh root@$SERVER_IP "sudo -u flaskapp mkdir -p /home/flaskapp/app/static/uploads"
ssh root@$SERVER_IP "chmod 755 /home/flaskapp/app/static/uploads"

# Настройка PostgreSQL
print_info "Настраиваем PostgreSQL..."
ssh root@$SERVER_IP "systemctl start postgresql"
ssh root@$SERVER_IP "systemctl enable postgresql"
ssh root@$SERVER_IP "sudo -u postgres createdb flaskapp || true"
ssh root@$SERVER_IP "sudo -u postgres psql -c \"CREATE USER flaskapp WITH PASSWORD 'password';\" || true"
ssh root@$SERVER_IP "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE flaskapp TO flaskapp;\""

# Создание конфигурации supervisor
print_info "Создаем конфигурацию supervisor..."
ssh root@$SERVER_IP "tee /etc/supervisor/conf.d/flaskapp.conf > /dev/null" << 'EOF'
[program:flaskapp]
directory=/home/flaskapp/app
command=/home/flaskapp/app/venv/bin/gunicorn --workers 2 --bind unix:flaskapp.sock -m 007 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/flaskapp/flaskapp.err.log
stdout_logfile=/var/log/flaskapp/flaskapp.out.log
user=flaskapp
environment=FLASK_ENV="production"
EOF

# Создание конфигурации nginx
print_info "Создаем конфигурацию nginx..."
ssh root@$SERVER_IP "tee /etc/nginx/sites-available/flaskapp > /dev/null" << EOF
server {
    listen 80;
    server_name $SERVER_IP;

    client_max_body_size 16M;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskapp/app/flaskapp.sock;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    location /static {
        alias /home/flaskapp/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /socket.io {
        proxy_pass http://unix:/home/flaskapp/app/flaskapp.sock;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Активация nginx конфигурации
print_info "Активируем nginx конфигурацию..."
ssh root@$SERVER_IP "ln -sf /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/"
ssh root@$SERVER_IP "rm -f /etc/nginx/sites-enabled/default"
ssh root@$SERVER_IP "nginx -t"

# Создание таблиц базы данных
print_info "Создаем таблицы базы данных..."
ssh root@$SERVER_IP "cd /home/flaskapp/app && sudo -u flaskapp /home/flaskapp/app/venv/bin/python -c 'from app import db; db.create_all()'"

# Запуск сервисов
print_info "Запускаем сервисы..."
ssh root@$SERVER_IP "supervisorctl reread"
ssh root@$SERVER_IP "supervisorctl update"
ssh root@$SERVER_IP "supervisorctl start flaskapp"
ssh root@$SERVER_IP "systemctl restart nginx"

# Проверка статуса
print_info "Проверяем статус сервисов..."
ssh root@$SERVER_IP "supervisorctl status flaskapp"
ssh root@$SERVER_IP "systemctl status nginx --no-pager"

# Финальная проверка
print_info "Выполняем финальную проверку..."
sleep 5

if ssh root@$SERVER_IP "curl -s -o /dev/null -w '%{http_code}' http://localhost" | grep -q "200\|302"; then
    print_success "Приложение успешно запущено!"
else
    print_warning "Приложение может быть еще запускается. Проверьте логи:"
    print_info "ssh root@$SERVER_IP 'tail -f /var/log/flaskapp/flaskapp.err.log'"
fi

# Вывод информации
echo ""
print_success "🎉 Деплой на Beget VPS завершен успешно!"
echo ""
echo "📋 Информация о приложении:"
echo "   Сервер: $SERVER_IP"
echo "   URL: http://$SERVER_IP"
echo ""
echo "🔧 Полезные команды:"
echo "   Логи приложения: ssh root@$SERVER_IP 'tail -f /var/log/flaskapp/flaskapp.out.log'"
echo "   Логи ошибок: ssh root@$SERVER_IP 'tail -f /var/log/flaskapp/flaskapp.err.log'"
echo "   Статус: ssh root@$SERVER_IP 'supervisorctl status flaskapp'"
echo "   Перезапуск: ssh root@$SERVER_IP 'supervisorctl restart flaskapp'"
echo ""
echo "📊 Мониторинг:"
echo "   Nginx логи: ssh root@$SERVER_IP 'tail -f /var/log/nginx/access.log'"
echo "   Системные ресурсы: ssh root@$SERVER_IP 'htop'"
echo "   База данных: ssh root@$SERVER_IP 'sudo -u postgres psql -d flaskapp'"
echo ""

print_info "🚀 Ваше приложение готово к использованию!"
print_info "🌐 Откройте в браузере: http://$SERVER_IP" 