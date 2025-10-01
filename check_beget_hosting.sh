#!/bin/bash

# 🔍 Проверка возможностей обычного хостинга Beget
# Использование: ./check_beget_hosting.sh [server] [username]

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
SERVER=${1:-"kapita6n.beget.tech"}
USERNAME=${2:-"kapita6n"}

print_info "🔍 Проверяем возможности хостинга Beget..."
print_info "Сервер: $SERVER"
print_info "Пользователь: $USERNAME"

# Проверка подключения
print_info "Проверяем SSH подключение..."
if ssh -o ConnectTimeout=10 -o BatchMode=yes $USERNAME@$SERVER exit 2>/dev/null; then
    print_success "SSH подключение работает!"
else
    print_error "SSH недоступен!"
    print_info "Убедитесь, что SSH включен в панели Beget"
    exit 1
fi

# Проверка Python
print_info "Проверяем Python..."
PYTHON_VERSION=$(ssh $USERNAME@$SERVER "python3 --version 2>/dev/null || python --version 2>/dev/null || echo 'Python не найден'")
print_info "Версия Python: $PYTHON_VERSION"

if echo "$PYTHON_VERSION" | grep -q "Python"; then
    print_success "Python доступен!"
else
    print_error "Python не найден!"
    print_warning "Возможно, нужно использовать Python 2.7"
fi

# Проверка pip
print_info "Проверяем pip..."
PIP_VERSION=$(ssh $USERNAME@$SERVER "pip3 --version 2>/dev/null || pip --version 2>/dev/null || echo 'pip не найден'")
print_info "Версия pip: $PIP_VERSION"

if echo "$PIP_VERSION" | grep -q "pip"; then
    print_success "pip доступен!"
else
    print_warning "pip не найден!"
fi

# Проверка директорий
print_info "Проверяем структуру директорий..."
ssh $USERNAME@$SERVER "ls -la ~/"

# Проверка www директории
print_info "Проверяем www директорию..."
WWW_DIR=$(ssh $USERNAME@$SERVER "find ~/ -name 'www' -type d 2>/dev/null || find ~/ -name 'public_html' -type d 2>/dev/null || echo 'www директория не найдена'")
print_info "WWW директория: $WWW_DIR"

if echo "$WWW_DIR" | grep -q "www\|public_html"; then
    print_success "WWW директория найдена!"
else
    print_warning "WWW директория не найдена!"
fi

# Проверка поддержки CGI
print_info "Проверяем поддержку CGI..."
CGI_DIR=$(ssh $USERNAME@$SERVER "find ~/ -name 'cgi-bin' -type d 2>/dev/null || echo 'cgi-bin не найден'")
print_info "CGI директория: $CGI_DIR"

if echo "$CGI_DIR" | grep -q "cgi-bin"; then
    print_success "CGI поддерживается!"
else
    print_warning "CGI не найден!"
fi

# Проверка базы данных
print_info "Проверяем доступ к MySQL..."
MYSQL_ACCESS=$(ssh $USERNAME@$SERVER "mysql --version 2>/dev/null || echo 'MySQL клиент не найден'")
print_info "MySQL клиент: $MYSQL_ACCESS"

if echo "$MYSQL_ACCESS" | grep -q "mysql"; then
    print_success "MySQL клиент доступен!"
else
    print_warning "MySQL клиент не найден!"
fi

# Проверка поддержки WebSocket
print_info "Проверяем поддержку WebSocket..."
print_warning "WebSocket поддержка зависит от конфигурации сервера"

# Проверка файловых ограничений
print_info "Проверяем файловые ограничения..."
FILE_LIMITS=$(ssh $USERNAME@$SERVER "ulimit -a 2>/dev/null || echo 'Ограничения не найдены'")
print_info "Файловые ограничения: $FILE_LIMITS"

# Вывод результатов
echo ""
print_info "📊 Результаты проверки:"
echo ""

if echo "$PYTHON_VERSION" | grep -q "Python"; then
    print_success "✅ Python: Доступен"
else
    print_error "❌ Python: Не найден"
fi

if echo "$PIP_VERSION" | grep -q "pip"; then
    print_success "✅ pip: Доступен"
else
    print_warning "⚠️  pip: Не найден"
fi

if echo "$WWW_DIR" | grep -q "www\|public_html"; then
    print_success "✅ WWW директория: Найдена"
else
    print_warning "⚠️  WWW директория: Не найдена"
fi

if echo "$CGI_DIR" | grep -q "cgi-bin"; then
    print_success "✅ CGI: Поддерживается"
else
    print_warning "⚠️  CGI: Не найден"
fi

if echo "$MYSQL_ACCESS" | grep -q "mysql"; then
    print_success "✅ MySQL: Доступен"
else
    print_warning "⚠️  MySQL: Не найден"
fi

echo ""
print_info "🎯 Рекомендации:"

if echo "$PYTHON_VERSION" | grep -q "Python"; then
    print_success "Ваш хостинг поддерживает Python!"
    print_info "Можем попробовать адаптировать приложение"
else
    print_error "Python не поддерживается на этом хостинге"
    print_info "Рекомендую перейти на VPS"
fi

echo ""
print_info "🔧 Следующие шаги:"
print_info "1. Если Python доступен - создам адаптированную версию"
print_info "2. Если Python недоступен - рекомендую VPS"
print_info "3. Проверим поддержку WebSocket для чата" 