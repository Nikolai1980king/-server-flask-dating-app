#!/bin/bash

echo "📤 Скрипт копирования файлов на сервер с системой IP-контроля"

# Настройки сервера (измените на свои)
SERVER_USER="root"
SERVER_HOST="212.67.11.50"
SERVER_PATH="/root/flask_server"

# Проверяем подключение к серверу
echo "🔍 Проверяем подключение к серверу..."
if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_HOST "echo 'Подключение успешно'" 2>/dev/null; then
    echo "❌ Не удается подключиться к серверу $SERVER_HOST"
    echo "Проверьте:"
    echo "  - Доступность сервера"
    echo "  - SSH ключи"
    echo "  - Настройки в скрипте (SERVER_USER, SERVER_HOST)"
    exit 1
fi

echo "✅ Подключение к серверу установлено"

# Создаем директорию на сервере если её нет
echo "📁 Создаем директорию на сервере..."
ssh $SERVER_USER@$SERVER_HOST "mkdir -p $SERVER_PATH"

# Копируем основные файлы
echo "📋 Копируем основные файлы..."
scp app.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp requirements.txt $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp run_production.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp init_db_simple.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Копируем тестовые файлы
echo "🧪 Копируем тестовые файлы..."
scp test_ip_control.html $SERVER_USER@$SERVER_HOST:$SERVER_PATH/
scp IP_CONTROL_IMPLEMENTATION.md $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Копируем скрипт деплоя
echo "🚀 Копируем скрипт деплоя..."
scp deploy_with_ip_control.sh $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

# Делаем скрипт исполняемым
echo "⚙️ Делаем скрипт исполняемым..."
ssh $SERVER_USER@$SERVER_HOST "chmod +x $SERVER_PATH/deploy_with_ip_control.sh"

echo "✅ Файлы успешно скопированы на сервер"
echo ""
echo "📋 Следующие шаги:"
echo "1. Подключитесь к серверу:"
echo "   ssh $SERVER_USER@$SERVER_HOST"
echo ""
echo "2. Перейдите в директорию:"
echo "   cd $SERVER_PATH"
echo ""
echo "3. Запустите деплой:"
echo "   ./deploy_with_ip_control.sh"
echo ""
echo "4. Проверьте работу:"
echo "   http://$SERVER_HOST/test_ip_control.html"