#!/bin/bash

# 🚀 Скрипт для копирования main.py на сервер где размещен телеграм бот

echo "🚀 Копирование main.py на сервер где размещен бот..."
echo "===================================================="

# Настройки сервера (измените под ваш сервер)
# Можете также задать через переменные окружения:
# export BOT_SERVER_IP="your_ip"
# export BOT_SERVER_USER="your_user"
# export BOT_SERVER_PATH="/path/to/bot"
# export BOT_SERVICE_NAME="your_service"

SERVER_USER="${BOT_SERVER_USER:-root}"
SERVER_IP="${BOT_SERVER_IP:-212.67.11.50}"
# Путь на сервере (относительно домашней директории пользователя или абсолютный)
# ../bot.yatuta.rf/public_html = относительно домашней директории
# или используйте абсолютный путь: /home/bot.yatuta.rf/public_html
SERVER_PATH="${BOT_SERVER_PATH:-../bot.yatuta.rf/public_html}"
SERVICE_NAME="${BOT_SERVICE_NAME:-none}"

echo ""
echo "📋 Текущие настройки сервера:"
echo "   👤 Пользователь: $SERVER_USER"
echo "   🌐 IP адрес: $SERVER_IP"
echo "   📁 Путь на сервере: $SERVER_PATH"
echo "   🔧 Имя сервиса: $SERVICE_NAME"
echo ""
read -p "✅ Настройки правильные? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo ""
    echo "📝 Укажите параметры сервера:"
    read -p "   IP адрес сервера [$SERVER_IP]: " input_ip
    SERVER_IP="${input_ip:-$SERVER_IP}"
    
    read -p "   Пользователь [$SERVER_USER]: " input_user
    SERVER_USER="${input_user:-$SERVER_USER}"
    
    read -p "   Путь на сервере (где находится main.py) [$SERVER_PATH]: " input_path
    SERVER_PATH="${input_path:-$SERVER_PATH}"
    
    read -p "   Имя systemd сервиса (или 'none' если нет) [$SERVICE_NAME]: " input_service
    SERVICE_NAME="${input_service:-$SERVICE_NAME}"
    
    echo ""
    echo "📋 Обновленные настройки:"
    echo "   👤 Пользователь: $SERVER_USER"
    echo "   🌐 IP адрес: $SERVER_IP"
    echo "   📁 Путь: $SERVER_PATH"
    echo "   🔧 Сервис: $SERVICE_NAME"
    echo ""
fi

# Проверяем наличие файла main.py
if [ ! -f "main.py" ]; then
    echo "❌ Ошибка: Файл main.py не найден в текущей директории!"
    echo "📁 Текущая директория: $(pwd)"
    exit 1
fi

echo "✅ Файл main.py найден"
echo "📤 Копируем на сервер ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/"

# Копируем файл на сервер
scp main.py ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/

if [ $? -eq 0 ]; then
    echo "✅ Файл main.py успешно скопирован на сервер!"
    echo ""
    
    # Спрашиваем, нужно ли перезапустить сервис (если сервис указан)
    if [ "$SERVICE_NAME" != "none" ] && [ "$SERVICE_NAME" != "" ]; then
        read -p "🔄 Перезапустить сервис ${SERVICE_NAME}? (y/n): " restart
        
        if [ "$restart" = "y" ] || [ "$restart" = "Y" ]; then
            echo "🔄 Перезапускаем сервис на сервере..."
            ssh ${SERVER_USER}@${SERVER_IP} << EOF
                cd ${SERVER_PATH}
                echo "🛑 Останавливаем сервис..."
                systemctl stop ${SERVICE_NAME}
                sleep 2
                echo "🚀 Запускаем сервис..."
                systemctl start ${SERVICE_NAME}
                sleep 2
                echo "📊 Статус сервиса:"
                systemctl status ${SERVICE_NAME} --no-pager -l
EOF
            echo ""
            echo "✅ Сервис перезапущен!"
        else
            echo ""
            echo "📋 Для перезапуска вручную выполните на сервере:"
            echo "   ssh ${SERVER_USER}@${SERVER_IP}"
            echo "   cd ${SERVER_PATH}"
            echo "   systemctl restart ${SERVICE_NAME}"
        fi
    else
        echo ""
        echo "ℹ️  Сервис не указан. Для перезапуска бота выполните на сервере:"
        echo "   ssh ${SERVER_USER}@${SERVER_IP}"
        echo "   cd ${SERVER_PATH}"
        echo "   # Перезапустите бот вручную (systemctl, screen, pm2, или другой способ)"
    fi
    
    echo ""
    echo "🎉 Готово! Изменения применены на сервере"
else
    echo "❌ Ошибка при копировании файла"
    echo ""
    echo "🔧 Возможные причины:"
    echo "   1. Неверный IP адрес или путь к серверу"
    echo "   2. Нет SSH доступа к серверу"
    echo "   3. Неверные учетные данные"
    echo ""
    echo "📋 Попробуйте вручную:"
    echo "   scp main.py ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/"
    exit 1
fi

