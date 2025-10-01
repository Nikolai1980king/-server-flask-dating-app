#!/bin/bash

echo "📤 Копирование исправленного кода на удаленный сервер"
echo "=================================================="

# Настройки сервера
SERVER_USER="root"
SERVER_HOST="212.67.11.50"
SERVER_PATH="/root/flask_server"

# Цвета для вывода
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
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

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

# Проверяем подключение к серверу
log_info "Проверяем подключение к серверу $SERVER_HOST..."
if ! ssh -o ConnectTimeout=15 -o StrictHostKeyChecking=no $SERVER_USER@$SERVER_HOST "echo 'Подключение успешно'" 2>/dev/null; then
    log_error "Не удается подключиться к серверу $SERVER_HOST"
    log_info "Попробуйте подключиться вручную:"
    log_info "  ssh $SERVER_USER@$SERVER_HOST"
    log_info "Или проверьте настройки SSH ключей"
    exit 1
fi

log_success "Подключение к серверу установлено"

# Создаем директорию на сервере
log_info "Создаем директорию на сервере..."
ssh $SERVER_USER@$SERVER_HOST "mkdir -p $SERVER_PATH"

# Создаем резервную копию
log_info "Создаем резервную копию текущего app.py..."
ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'Резервная копия не создана (файл не существует)'"

# Копируем основные файлы
log_info "Копируем исправленный app.py..."
scp app.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

log_info "Копируем файл миграции..."
scp migrate_add_creation_ip.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

log_info "Копируем requirements.txt..."
scp requirements.txt $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Применяем миграцию на сервере
log_info "Применяем миграцию базы данных на сервере..."
ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && python3 migrate_add_creation_ip.py"

# Перезапускаем сервер
log_info "Перезапускаем Flask приложение..."
ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && pkill -f 'python.*app.py' || echo 'Процесс не найден'"
ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && nohup python3 app.py > app.log 2>&1 &"

# Проверяем статус
log_info "Проверяем статус приложения..."
sleep 3
if ssh $SERVER_USER@$SERVER_HOST "ps aux | grep -v grep | grep 'python.*app.py'"; then
    log_success "Приложение успешно запущено!"
else
    log_warning "Приложение может быть еще запускается"
fi

echo ""
log_success "🎉 Копирование и обновление завершено!"
echo ""
echo "📋 Информация:"
echo "   Сервер: $SERVER_HOST"
echo "   Путь: $SERVER_PATH"
echo "   URL: http://$SERVER_HOST"
echo ""
echo "🔧 Полезные команды:"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo "   cd $SERVER_PATH"
echo "   tail -f app.log  # Логи приложения"
echo "   ps aux | grep python  # Проверить процессы"
echo ""
