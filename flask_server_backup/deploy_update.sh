#!/bin/bash

# Скрипт для быстрого обновления приложения на Beget VPS
# Использование: ./deploy_update.sh

SERVER_IP="212.67.11.50"
SERVER_USER="root"
APP_DIR="/home/flaskapp/app"

echo "🚀 Быстрое обновление приложения на сервере..."
echo "Сервер: $SERVER_IP"
echo ""

# Проверяем наличие файлов
echo "📁 Проверяем файлы для копирования..."
if [ ! -f "app.py" ]; then
    echo "❌ Файл app.py не найден!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Файл requirements.txt не найден!"
    exit 1
fi

echo "✅ Файлы найдены"

# Копируем файлы на сервер
echo ""
echo "📤 Копируем файлы на сервер..."
echo "Введите пароль от сервера:"

# Копируем основные файлы
scp app.py $SERVER_USER@$SERVER_IP:$APP_DIR/
scp requirements.txt $SERVER_USER@$SERVER_IP:$APP_DIR/

# Копируем статические файлы если есть
if [ -d "static" ]; then
    echo "📁 Копируем папку static..."
    scp -r static $SERVER_USER@$SERVER_IP:$APP_DIR/
fi

# Копируем .env если есть
if [ -f ".env" ]; then
    echo "🔧 Копируем .env..."
    scp .env $SERVER_USER@$SERVER_IP:$APP_DIR/
fi

echo ""
echo "🔄 Перезапускаем приложение на сервере..."
echo "Подключитесь к серверу и выполните:"
echo "ssh root@$SERVER_IP"
echo "systemctl restart flaskapp"
echo "systemctl status flaskapp"

echo ""
echo "✅ Обновление завершено!"
echo "🌐 Сайт: http://$SERVER_IP"
echo "🔒 HTTPS: https://$SERVER_IP" 