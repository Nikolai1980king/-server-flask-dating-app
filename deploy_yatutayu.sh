#!/bin/bash

echo "🚀 Деплой приложения знакомств на ятутаю.рф"
echo "=============================================="

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функция для вывода сообщений
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверяем, что мы на сервере
if [ "$EUID" -eq 0 ]; then
    log_error "Не запускайте скрипт от root пользователя"
    exit 1
fi

# Переменные
APP_NAME="dating-app"
APP_DIR="/home/$USER/flask_server"
SERVICE_NAME="dating-app"
DOMAIN="ятутаю.рф"

log_info "Начинаем деплой приложения $APP_NAME на домен $DOMAIN"

# 1. Останавливаем старое приложение
log_info "Останавливаем старое приложение..."
sudo systemctl stop $SERVICE_NAME 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*run_production.py" 2>/dev/null || true

# 2. Переходим в директорию приложения
cd $APP_DIR || {
    log_error "Не удалось перейти в директорию $APP_DIR"
    exit 1
}

# 3. Обновляем код из git
if [ -d ".git" ]; then
    log_info "Обновляем код из git..."
    git pull origin master || {
        log_warning "Не удалось обновить код из git, продолжаем с текущей версией"
    }
else
    log_warning "Git репозиторий не найден, используем текущий код"
fi

# 4. Создаем виртуальное окружение (если не существует)
if [ ! -d "venv" ]; then
    log_info "Создаем виртуальное окружение..."
    python3 -m venv venv
fi

# 5. Активируем виртуальное окружение и устанавливаем зависимости
log_info "Устанавливаем зависимости..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 6. Создаем директории если не существуют
log_info "Создаем необходимые директории..."
mkdir -p static/uploads
mkdir -p instance
mkdir -p venue_info

# 7. Инициализируем базу данных
log_info "Инициализируем базу данных..."
python3 -c "
from app import app, db
with app.app_context():
    db.create_all()
    print('База данных инициализирована')
"

# 8. Создаем systemd сервис
log_info "Создаем systemd сервис..."
sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Dating App - Приложение знакомств
After=network.target

[Service]
Type=simple
User=$USER
Group=$USER
WorkingDirectory=$APP_DIR
Environment=PATH=$APP_DIR/venv/bin
Environment=PYTHONPATH=$APP_DIR
Environment=FLASK_ENV=production
Environment=FLASK_APP=run_production.py
ExecStart=$APP_DIR/venv/bin/python $APP_DIR/run_production.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# 9. Перезагружаем systemd
log_info "Перезагружаем systemd..."
sudo systemctl daemon-reload

# 10. Включаем автозапуск
log_info "Включаем автозапуск сервиса..."
sudo systemctl enable $SERVICE_NAME

# 11. Запускаем приложение
log_info "Запускаем приложение..."
sudo systemctl start $SERVICE_NAME

# 12. Ждем запуска
sleep 5

# 13. Проверяем статус
log_info "Проверяем статус приложения..."
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    log_success "Приложение успешно запущено!"
else
    log_error "Ошибка запуска приложения"
    log_info "Логи сервиса:"
    sudo journalctl -u $SERVICE_NAME --no-pager -l -n 20
    exit 1
fi

# 14. Проверяем доступность
log_info "Проверяем доступность приложения..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5000 | grep -q "200\|302"; then
    log_success "Приложение доступно на localhost:5000"
else
    log_warning "Приложение может быть недоступно на localhost:5000"
fi

# 15. Настройка nginx (если установлен)
if command -v nginx &> /dev/null; then
    log_info "Настраиваем nginx..."
    
    # Создаем конфигурацию nginx
    sudo tee /etc/nginx/sites-available/$DOMAIN > /dev/null <<EOF
server {
    listen 80;
    server_name $DOMAIN www.$DOMAIN;
    
    # Увеличиваем лимиты для загрузки файлов
    client_max_body_size 50M;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        
        # Таймауты
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # WebSocket поддержка для SocketIO
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
    
    # Статические файлы
    location /static/ {
        alias $APP_DIR/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

    # Активируем сайт
    sudo ln -sf /etc/nginx/sites-available/$DOMAIN /etc/nginx/sites-enabled/
    sudo nginx -t && sudo systemctl reload nginx
    
    log_success "Nginx настроен для домена $DOMAIN"
else
    log_warning "Nginx не установлен, приложение доступно только на порту 5000"
fi

# 16. Настройка файрвола
log_info "Настраиваем файрвол..."
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 5000/tcp  # Flask app (если nginx не используется)
sudo ufw --force enable

# 17. Финальная проверка
log_info "Финальная проверка..."
echo ""
echo "=============================================="
log_success "🎉 Деплой завершен успешно!"
echo ""
echo "📊 Статус сервиса:"
sudo systemctl status $SERVICE_NAME --no-pager -l
echo ""
echo "🌐 Приложение доступно по адресам:"
echo "   • http://$DOMAIN (через nginx)"
echo "   • http://localhost:5000 (прямой доступ)"
echo ""
echo "📋 Полезные команды:"
echo "   sudo systemctl status $SERVICE_NAME     - статус приложения"
echo "   sudo systemctl restart $SERVICE_NAME    - перезапуск"
echo "   sudo journalctl -u $SERVICE_NAME -f     - логи в реальном времени"
echo "   sudo systemctl stop $SERVICE_NAME       - остановка"
echo ""
echo "🔧 Настройка SSL (Let's Encrypt):"
echo "   sudo apt install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN"
echo ""
log_info "Деплой завершен! 🚀"