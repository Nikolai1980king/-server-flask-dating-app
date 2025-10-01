#!/bin/bash

echo "📤 Копирование проекта на сервер ятутаю.рф"
echo "=========================================="

# Настройки
SERVER_USER="root"  # Замените на вашего пользователя
SERVER_IP="your-server-ip"  # Замените на IP вашего сервера
SERVER_PATH="/home/$SERVER_USER/flask_server"

# Цвета
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Проверяем параметры
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Использование: $0 [SERVER_IP] [USER]"
    echo ""
    echo "Примеры:"
    echo "  $0 192.168.1.100 root"
    echo "  $0 your-server.com ubuntu"
    echo ""
    echo "Или отредактируйте переменные в начале скрипта:"
    echo "  SERVER_IP=\"your-server-ip\""
    echo "  SERVER_USER=\"your-username\""
    exit 0
fi

# Переопределяем параметры если переданы
if [ ! -z "$1" ]; then
    SERVER_IP="$1"
fi

if [ ! -z "$2" ]; then
    SERVER_USER="$2"
fi

# Проверяем, что IP задан
if [ "$SERVER_IP" = "your-server-ip" ]; then
    log_error "Не задан IP сервера!"
    echo "Используйте: $0 YOUR_SERVER_IP [USERNAME]"
    echo "Или отредактируйте переменную SERVER_IP в скрипте"
    exit 1
fi

log_info "Копируем проект на сервер $SERVER_USER@$SERVER_IP:$SERVER_PATH"

# Создаем директорию на сервере
log_info "Создаем директорию на сервере..."
ssh $SERVER_USER@$SERVER_IP "mkdir -p $SERVER_PATH"

# Копируем файлы (исключая ненужные)
log_info "Копируем файлы проекта..."
rsync -avz --progress \
    --exclude='.git/' \
    --exclude='__pycache__/' \
    --exclude='*.pyc' \
    --exclude='.env' \
    --exclude='instance/' \
    --exclude='venv/' \
    --exclude='*.log' \
    --exclude='.DS_Store' \
    --exclude='Thumbs.db' \
    ./ $SERVER_USER@$SERVER_IP:$SERVER_PATH/

log_success "Файлы скопированы!"

# Копируем переменные окружения
log_info "Копируем файл переменных окружения..."
scp env_production.txt $SERVER_USER@$SERVER_IP:$SERVER_PATH/.env

log_success "Переменные окружения скопированы!"

# Делаем скрипт деплоя исполняемым
log_info "Настраиваем права доступа..."
ssh $SERVER_USER@$SERVER_IP "chmod +x $SERVER_PATH/deploy_yatutayu.sh"

log_success "Права доступа настроены!"

echo ""
echo "=========================================="
log_success "🎉 Копирование завершено!"
echo ""
echo "Теперь подключитесь к серверу и запустите деплой:"
echo "  ssh $SERVER_USER@$SERVER_IP"
echo "  cd $SERVER_PATH"
echo "  ./deploy_yatutayu.sh"
echo ""
echo "Или запустите деплой удаленно:"
echo "  ssh $SERVER_USER@$SERVER_IP 'cd $SERVER_PATH && ./deploy_yatutayu.sh'"