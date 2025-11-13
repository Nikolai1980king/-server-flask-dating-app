#!/bin/bash

# 🚀 Универсальный скрипт для копирования любого файла на сервер

# Проверяем аргументы
if [ $# -eq 0 ]; then
    echo "📖 Использование: $0 <имя_файла> [путь_на_сервере]"
    echo ""
    echo "Примеры:"
    echo "  $0 main.py                    # Скопирует main.py в /home/flaskapp/app/"
    echo "  $0 main.py /custom/path/      # Скопирует main.py в /custom/path/"
    echo "  $0 bot/config.py              # Скопирует bot/config.py"
    exit 1
fi

FILE_TO_COPY="$1"
SERVER_PATH="${2:-/home/flaskapp/app}"

# Настройки сервера (измените под ваш сервер)
SERVER_USER="root"
SERVER_IP="212.67.11.50"
SERVICE_NAME="flaskapp"

echo "🚀 Копирование файла на сервер..."
echo "========================================"
echo "📁 Файл: $FILE_TO_COPY"
echo "📍 Сервер: ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/"
echo ""

# Проверяем наличие файла
if [ ! -f "$FILE_TO_COPY" ]; then
    echo "❌ Ошибка: Файл $FILE_TO_COPY не найден!"
    exit 1
fi

echo "✅ Файл найден"
echo "📤 Копируем..."

# Копируем файл на сервер
scp "$FILE_TO_COPY" ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/

if [ $? -eq 0 ]; then
    echo "✅ Файл успешно скопирован на сервер!"
    echo ""
    
    # Определяем имя файла для перезапуска
    FILENAME=$(basename "$FILE_TO_COPY")
    
    # Если это Python файл с именем main.py, app.py или бот-файл, спрашиваем про перезапуск
    if [[ "$FILENAME" == *.py ]] && [[ "$FILENAME" == main.py ]] || [[ "$FILENAME" == app.py ]] || [[ "$FILENAME" == *bot*.py ]]; then
        read -p "🔄 Перезапустить сервис ${SERVICE_NAME}? (y/n): " restart
        
        if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
            echo "🔄 Перезапускаем сервис..."
            ssh ${SERVER_USER}@${SERVER_IP} << EOF
                cd ${SERVER_PATH}
                systemctl restart ${SERVICE_NAME}
                sleep 2
                systemctl status ${SERVICE_NAME} --no-pager -l
EOF
            echo "✅ Сервис перезапущен!"
        fi
    fi
    
    echo ""
    echo "🎉 Готово!"
else
    echo "❌ Ошибка при копировании файла"
    exit 1
fi



