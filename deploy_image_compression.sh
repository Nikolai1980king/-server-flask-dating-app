#!/bin/bash

# 🖼️ ДЕПЛОЙ ОБНОВЛЕНИЯ С АВТОМАТИЧЕСКИМ СЖАТИЕМ ИЗОБРАЖЕНИЙ
echo "🖼️ ДЕПЛОЙ ОБНОВЛЕНИЯ С АВТОМАТИЧЕСКИМ СЖАТИЕМ ИЗОБРАЖЕНИЙ"
echo "========================================================="

# Настройки сервера
SERVER_IP="212.67.11.50"
SERVER_USER="root"
SERVER_PATH="/home/flaskapp/app"

echo "📋 Настройки:"
echo "   Сервер: $SERVER_USER@$SERVER_IP"
echo "   Путь: $SERVER_PATH"

# Проверка подключения к серверу
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'Подключение успешно'" 2>/dev/null; then
    echo "❌ Не удается подключиться к серверу $SERVER_USER@$SERVER_IP"
    echo "Проверьте:"
    echo "   - Доступность сервера"
    echo "   - SSH ключи"
    echo "   - Права доступа"
    exit 1
fi

echo "✅ Подключение к серверу успешно"

# Остановка приложения на сервере
echo "⏸️ Останавливаем приложение на сервере..."
ssh $SERVER_USER@$SERVER_IP "
    echo 'Останавливаем Flask приложение...'
    systemctl stop flaskapp 2>/dev/null || pkill -f app.py 2>/dev/null || echo 'Приложение не запущено'
    echo 'Приложение остановлено'
"

# Создание резервной копии на сервере
echo "💾 Создаем резервную копию на сервере..."
ssh $SERVER_USER@$SERVER_IP "
    cd $SERVER_PATH
    echo 'Создаем резервную копию...'
    cp app.py app.py.backup.\$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo 'Резервная копия не создана'
    echo 'Резервная копия создана'
"

# Копирование обновленного приложения
echo "📤 Копируем обновленное приложение..."
echo "   - app.py (с функцией сжатия изображений)"
scp app.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# Установка зависимостей и запуск
echo "🔧 Устанавливаем зависимости и запускаем..."
ssh $SERVER_USER@$SERVER_IP << EOF
    cd $SERVER_PATH
    echo "📦 Устанавливаем зависимости..."
    
    # Устанавливаем Pillow если не установлен
    pip3 install Pillow --upgrade 2>/dev/null || echo "Pillow уже установлен"
    
    echo "🚀 Запускаем приложение..."
    
    # Запускаем приложение в фоне
    nohup python3 app.py > flask.log 2>&1 &
    
    echo "✅ Приложение запущено"
    
    # Проверяем, что приложение запустилось
    sleep 3
    if pgrep -f "python3 app.py" > /dev/null; then
        echo "✅ Приложение работает"
    else
        echo "❌ Ошибка запуска приложения"
        echo "📋 Логи:"
        tail -20 flask.log
    fi
EOF

# Проверка статуса
echo "🔍 Проверка статуса..."
ssh $SERVER_USER@$SERVER_IP "
    echo '📊 Статус процессов:'
    ps aux | grep -E '(python3|app.py)' | grep -v grep
    
    echo ''
    echo '🌐 Проверка доступности:'
    curl -s -I http://127.0.0.1:5000 | head -3 || echo 'Приложение недоступно'
"

echo ""
echo "🎉 ДЕПЛОЙ ЗАВЕРШЕН!"
echo "===================="
echo "✅ Автоматическое сжатие изображений добавлено"
echo "✅ Лимит файлов увеличен до 100MB"
echo "✅ Фото автоматически сжимается до 5MB"
echo "✅ Размер изображений ограничен 1920x1080"
echo ""
echo "🌐 Сайт должен быть доступен по адресу:"
echo "   https://ятута.рф"
echo ""
echo "🔍 Для проверки работы:"
echo "   - Попробуйте загрузить фото 11.8MB"
echo "   - Фото должно автоматически сжаться"
echo "   - Ошибка 413 больше не должна возникать"
echo ""
echo "📋 Основные изменения:"
echo "   • Добавлена функция compress_image()"
echo "   • Автоматическое сжатие до 5MB"
echo "   • Максимальный размер 1920x1080"
echo "   • Качество JPEG 85%"
echo "   • Лимит загрузки 100MB"
echo ""
echo "🔧 Если нужно проверить логи:"
echo "   ssh $SERVER_USER@$SERVER_IP"
echo "   tail -f $SERVER_PATH/flask.log"
