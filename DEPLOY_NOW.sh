#!/bin/bash

echo "🚀 Быстрый деплой на сервер 212.67.11.50"
echo "========================================"
echo ""
echo "📦 Архив готов: deploy_package.tar.gz (11M)"
echo ""
echo "🔑 ПОТРЕБУЕТСЯ ВВЕСТИ ПАРОЛЬ ROOT 2 РАЗА"
echo ""

# Шаг 1: Копирование
echo "📤 Шаг 1/2: Копируем архив на сервер..."
scp deploy_package.tar.gz root@212.67.11.50:/home/flaskapp/app/

if [ $? -ne 0 ]; then
    echo "❌ Ошибка копирования"
    exit 1
fi

echo "✅ Архив скопирован"
echo ""

# Шаг 2: Установка
echo "⚙️ Шаг 2/2: Устанавливаем на сервере..."
ssh root@212.67.11.50 << 'ENDSSH'
    cd /home/flaskapp/app
    
    echo "📦 Распаковываем..."
    tar -xzf deploy_package.tar.gz
    
    echo "📋 Устанавливаем зависимости..."
    pip install -r requirements.txt -q
    
    echo "📁 Создаем папки..."
    mkdir -p uploads instance
    chmod 755 uploads
    
    echo "🔄 Применяем миграции..."
    python migrate_add_puzzles.py
    python migrate_surprise_payment.py
    python migrate_add_sent_jokes.py
    
    echo "🔄 Перезапускаем приложение..."
    systemctl stop flaskapp
    systemctl start flaskapp
    
    echo "✅ Готово!"
    echo ""
    systemctl status flaskapp --no-pager -l
ENDSSH

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "🌐 Проверьте: https://192.168.255.137"
echo ""
echo "📋 Что добавлено:"
echo "  - 🧠 Функция 'Напрягись' (25 головоломок)"
echo "  - 🍰 Текст про столик для десерта"
echo "  - 🍾 Текст про столик для шампанского"
echo ""













