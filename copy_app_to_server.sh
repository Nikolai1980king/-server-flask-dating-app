#!/bin/bash

echo "📤 Копирование файла app.py на удаленный сервер"

# Настройки сервера
SERVER_USER="root"
SERVER_HOST="212.67.11.50"
SERVER_PATH="/root/flask_server"

# Проверяем, что файл app.py существует
if [ ! -f "app.py" ]; then
    echo "❌ Файл app.py не найден в текущей директории"
    exit 1
fi

echo "📁 Файл app.py найден"

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

echo "✅ Подключение к серверу успешно"

# Создаем резервную копию на сервере
echo "💾 Создаем резервную копию текущего app.py на сервере..."
ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && cp app.py app.py.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'Резервная копия не создана (файл не существует)'"

# Копируем файл на сервер
echo "📤 Копируем app.py на сервер..."
scp app.py $SERVER_USER@$SERVER_HOST:$SERVER_PATH/

if [ $? -eq 0 ]; then
    echo "✅ Файл app.py успешно скопирован на сервер"
    
    # Проверяем размер файла на сервере
    echo "📊 Проверяем размер файла на сервере..."
    ssh $SERVER_USER@$SERVER_HOST "cd $SERVER_PATH && ls -lh app.py"
    
    echo ""
    echo "🎉 Копирование завершено успешно!"
    echo "📝 Файл app.py обновлен на сервере $SERVER_HOST"
    echo "💡 Для применения изменений перезапустите сервер"
    
else
    echo "❌ Ошибка при копировании файла"
    exit 1
fi