#!/bin/bash

# 🔧 Скрипт для исправления проблем с сервером
# Автор: AI Assistant
# Дата: 30.08.2025

echo "🔧 Исправление проблем с сервером..."

# 1. Исправляем права доступа к базе данных
echo "📊 Исправляем права доступа к базе данных..."
if [ -f "instance/dating_app.db" ]; then
    chmod 664 instance/dating_app.db
    echo "✅ Права доступа к базе данных исправлены"
else
    echo "⚠️ База данных не найдена"
fi

# 2. Создаем placeholder.png если его нет
echo "🖼️ Проверяем placeholder.png..."
if [ ! -f "static/uploads/placeholder.png" ]; then
    echo "📸 Создаем placeholder.png..."
    if command -v convert &> /dev/null; then
        convert -size 200x200 xc:gray -fill white -draw "text 50,100 'No Photo'" static/uploads/placeholder.png
        echo "✅ placeholder.png создан"
    else
        echo "⚠️ ImageMagick не установлен, создаем пустой файл"
        touch static/uploads/placeholder.png
    fi
else
    echo "✅ placeholder.png уже существует"
fi

# 3. Проверяем права доступа к папке uploads
echo "📁 Проверяем права доступа к папке uploads..."
chmod 755 static/uploads/
echo "✅ Права доступа к папке uploads исправлены"

# 4. Останавливаем старые процессы
echo "🛑 Останавливаем старые процессы..."
pkill -f "python.*app.py" 2>/dev/null || echo "Нет запущенных процессов"

# 5. Запускаем сервер
echo "🚀 Запускаем сервер..."
python app.py &
SERVER_PID=$!

# 6. Ждем запуска сервера
echo "⏳ Ждем запуска сервера..."
sleep 5

# 7. Проверяем, что сервер работает
echo "🔍 Проверяем работу сервера..."
if curl -s -f http://localhost:5000/ > /dev/null; then
    echo "✅ Сервер успешно запущен"
    echo "🌐 Адрес: http://localhost:5000"
    echo "📱 Мобильный адрес: https://192.168.0.24"
    echo "📝 Создание анкеты: https://192.168.0.24/create"
else
    echo "❌ Ошибка запуска сервера"
    kill $SERVER_PID 2>/dev/null
    exit 1
fi

echo ""
echo "🎉 Исправление завершено!"
echo "📋 Что было исправлено:"
echo "   - Права доступа к базе данных"
echo "   - Создан placeholder.png"
echo "   - Права доступа к папке uploads"
echo "   - Сервер перезапущен"
echo ""
echo "💡 Для остановки сервера: pkill -f 'python.*app.py'" 