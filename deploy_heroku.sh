#!/bin/bash

# 🚀 Автоматический деплой на Heroku
# Использование: ./deploy_heroku.sh [app-name]

set -e  # Остановка при ошибке

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Функции для вывода
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
APP_NAME=${1:-""}

if [ -z "$APP_NAME" ]; then
    print_warning "Имя приложения не указано. Будет создано случайное имя."
fi

print_info "🚀 Начинаем деплой на Heroku..."

# Проверка установки Heroku CLI
if ! command -v heroku &> /dev/null; then
    print_error "Heroku CLI не установлен!"
    print_info "Установите Heroku CLI:"
    print_info "curl https://cli-assets.heroku.com/install.sh | sh"
    exit 1
fi

print_success "Heroku CLI установлен: $(heroku --version)"

# Проверка авторизации
print_info "Проверяем авторизацию в Heroku..."
if ! heroku auth:whoami &> /dev/null; then
    print_warning "Не авторизованы в Heroku. Выполняем вход..."
    heroku login
else
    print_success "Авторизованы как: $(heroku auth:whoami)"
fi

# Проверка необходимых файлов
print_info "Проверяем необходимые файлы..."

REQUIRED_FILES=("app.py" "requirements.txt" "Procfile" "runtime.txt")
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

# Инициализация git если нужно
if [ ! -d ".git" ]; then
    print_info "Инициализируем git репозиторий..."
    git init
    print_success "Git репозиторий инициализирован"
fi

# Создание или подключение к приложению Heroku
if [ -z "$APP_NAME" ]; then
    print_info "Создаем новое приложение Heroku..."
    heroku create
    APP_NAME=$(heroku info -s | grep git_url | sed 's/.*git@heroku.com:\(.*\)\.git.*/\1/')
    print_success "Создано приложение: $APP_NAME"
else
    print_info "Проверяем существование приложения: $APP_NAME"
    if heroku apps:info --app "$APP_NAME" &> /dev/null; then
        print_success "Приложение $APP_NAME существует"
        heroku git:remote -a "$APP_NAME"
    else
        print_info "Создаем приложение: $APP_NAME"
        heroku create "$APP_NAME"
    fi
fi

# Проверка базы данных
print_info "Проверяем базу данных..."
if ! heroku addons --app "$APP_NAME" | grep -q "heroku-postgresql"; then
    print_info "Добавляем PostgreSQL..."
    heroku addons:create heroku-postgresql:mini --app "$APP_NAME"
    print_success "PostgreSQL добавлен"
else
    print_success "PostgreSQL уже подключен"
fi

# Генерация секретного ключа
print_info "Генерируем секретный ключ..."
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
print_success "Секретный ключ сгенерирован"

# Настройка переменных окружения
print_info "Настраиваем переменные окружения..."
heroku config:set SECRET_KEY="$SECRET_KEY" --app "$APP_NAME"
heroku config:set FLASK_ENV=production --app "$APP_NAME"
heroku config:set MAX_REGISTRATION_DISTANCE=3000 --app "$APP_NAME"
heroku config:set PROFILE_LIFETIME_HOURS=24 --app "$APP_NAME"
print_success "Переменные окружения настроены"

# Коммит изменений
print_info "Коммитим изменения..."
git add .
if git diff --cached --quiet; then
    print_warning "Нет изменений для коммита"
else
    git commit -m "Deploy to Heroku - $(date)"
    print_success "Изменения закоммичены"
fi

# Деплой
print_info "Отправляем код на Heroku..."
git push heroku main || git push heroku master
print_success "Код отправлен на Heroku"

# Создание таблиц базы данных
print_info "Создаем таблицы базы данных..."
heroku run python -c "from app import db; db.create_all()" --app "$APP_NAME"
print_success "Таблицы базы данных созданы"

# Проверка процессов
print_info "Проверяем процессы..."
heroku ps:scale web=1 --app "$APP_NAME"
print_success "Веб-процесс запущен"

# Получение URL приложения
APP_URL=$(heroku info -s --app "$APP_NAME" | grep web_url | cut -d= -f2)
print_success "Приложение доступно по адресу: $APP_URL"

# Создание резервной копии
print_info "Создаем резервную копию базы данных..."
heroku pg:backups:capture --app "$APP_NAME"
print_success "Резервная копия создана"

# Финальная проверка
print_info "Выполняем финальную проверку..."
sleep 5

if curl -s -o /dev/null -w "%{http_code}" "$APP_URL" | grep -q "200\|302"; then
    print_success "Приложение успешно запущено!"
else
    print_warning "Приложение может быть еще запускается. Проверьте логи:"
    print_info "heroku logs --tail --app $APP_NAME"
fi

# Вывод информации
echo ""
print_success "🎉 Деплой завершен успешно!"
echo ""
echo "📋 Информация о приложении:"
echo "   Имя: $APP_NAME"
echo "   URL: $APP_URL"
echo "   База данных: $(heroku config:get DATABASE_URL --app "$APP_NAME" | cut -d@ -f2 | cut -d/ -f1)"
echo ""
echo "🔧 Полезные команды:"
echo "   Логи: heroku logs --tail --app $APP_NAME"
echo "   Открыть: heroku open --app $APP_NAME"
echo "   Консоль: heroku run python --app $APP_NAME"
echo "   База данных: heroku pg:psql --app $APP_NAME"
echo ""
echo "📊 Мониторинг:"
echo "   Статус: heroku ps --app $APP_NAME"
echo "   Конфигурация: heroku config --app $APP_NAME"
echo "   Аддоны: heroku addons --app $APP_NAME"
echo ""

print_info "🚀 Ваше приложение готово к использованию!" 