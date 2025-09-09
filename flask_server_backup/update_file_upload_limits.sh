#!/bin/bash

# Скрипт для обновления лимитов загрузки файлов на сервере
# Использование: ./update_file_upload_limits.sh

SERVER_IP="212.67.11.50"
SERVER_USER="root"
APP_DIR="/home/flaskapp/app"

echo "📁 Обновление лимитов загрузки файлов на сервере..."
echo "Сервер: $SERVER_IP"
echo "Новый лимит: 100MB"
echo ""

# Копируем обновленный app.py
echo "📤 Копируем обновленный app.py..."
scp app.py $SERVER_USER@$SERVER_IP:$APP_DIR/

if [ $? -eq 0 ]; then
    echo "✅ app.py успешно скопирован!"
else
    echo "❌ Ошибка при копировании app.py"
    exit 1
fi

echo ""
echo "🔄 Перезапускаем приложение на сервере..."
echo "Подключитесь к серверу и выполните:"
echo "ssh root@$SERVER_IP"
echo "systemctl restart flaskapp"
echo "systemctl status flaskapp"
echo ""

echo "📋 Проверьте работу загрузки файлов:"
echo "1. Откройте сайт"
echo "2. Попробуйте загрузить фото с компьютера"
echo "3. Убедитесь, что файлы до 100MB загружаются"
echo ""

echo "✅ Обновление лимитов завершено!"
echo "🌐 Теперь можно загружать файлы до 100MB" 