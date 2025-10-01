#!/bin/bash

# 🚀 Деплой исправления перенаправления после оплаты
# Использование: ./deploy_payment_fix.sh

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

# Настройки сервера
SERVER_IP="212.67.11.50"
SERVER_USER="root"
SERVER_PATH="/root/flask_server"

print_info "🚀 Деплой исправления перенаправления после оплаты..."
print_info "Сервер: $SERVER_IP"

# Проверяем, что файл app.py существует
if [ ! -f "app.py" ]; then
    print_error "Файл app.py не найден!"
    exit 1
fi

print_info "📤 Копируем обновленный app.py на сервер..."

# Копируем обновленный файл на сервер
scp app.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/

if [ $? -eq 0 ]; then
    print_success "Файл app.py успешно скопирован на сервер"
else
    print_error "Ошибка при копировании файла"
    exit 1
fi

print_info "🔄 Перезапускаем приложение на сервере..."

# Подключаемся к серверу и перезапускаем приложение
ssh $SERVER_USER@$SERVER_IP << 'EOF'
cd /root/flask_server

# Останавливаем старое приложение
echo "🛑 Останавливаем старое приложение..."
pkill -f "python.*app.py" 2>/dev/null || true
supervisorctl stop flaskapp 2>/dev/null || true

# Ждем немного
sleep 2

# Запускаем новое приложение
echo "🚀 Запускаем обновленное приложение..."
supervisorctl start flaskapp

# Проверяем статус
echo "📊 Проверяем статус приложения..."
sleep 3
supervisorctl status flaskapp

echo "✅ Приложение обновлено и запущено!"
EOF

if [ $? -eq 0 ]; then
    print_success "🎉 Деплой завершен успешно!"
    print_info "🌐 Приложение доступно по адресу: http://$SERVER_IP"
    print_info "🔧 Для проверки логов: ssh $SERVER_USER@$SERVER_IP 'tail -f /var/log/flaskapp/flaskapp.out.log'"
else
    print_error "Ошибка при деплое на сервер"
    exit 1
fi