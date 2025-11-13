#!/bin/bash

# 🔄 Скрипт для перезапуска телеграм-бота на сервере

echo "🔄 Перезапуск телеграм-бота..."
echo "==============================="

# Настройки сервера
SERVER_USER="${BOT_SERVER_USER:-root}"
SERVER_IP="${BOT_SERVER_IP:-212.67.11.50}"
SERVER_PATH="${BOT_SERVER_PATH:-../bot.yatuta.rf/public_html}"
SERVICE_NAME="${BOT_SERVICE_NAME:-telegram_bot}"

echo ""
echo "📋 Настройки сервера:"
echo "   👤 Пользователь: $SERVER_USER"
echo "   🌐 IP адрес: $SERVER_IP"
echo "   📁 Путь: $SERVER_PATH"
echo "   🔧 Сервис: $SERVICE_NAME"
echo ""

# Функция для перезапуска через systemd
restart_systemd() {
    echo "🔄 Пробуем перезапустить через systemd..."
    ssh ${SERVER_USER}@${SERVER_IP} << EOF
        cd ${SERVER_PATH}
        if systemctl list-units --type=service | grep -q "${SERVICE_NAME}"; then
            echo "✅ Сервис найден, перезапускаем..."
            systemctl restart ${SERVICE_NAME}
            sleep 2
            systemctl status ${SERVICE_NAME} --no-pager -l
        else
            echo "❌ Сервис ${SERVICE_NAME} не найден"
            return 1
        fi
EOF
}

# Функция для перезапуска через screen
restart_screen() {
    echo "🔄 Ищем процессы бота и перезапускаем через screen..."
    ssh ${SERVER_USER}@${SERVER_IP} << EOF
        cd ${SERVER_PATH}
        
        # Ищем процесс бота
        BOT_PID=\$(ps aux | grep -E "python.*main.py|python3.*main.py" | grep -v grep | awk '{print \$2}' | head -1)
        
        if [ ! -z "\$BOT_PID" ]; then
            echo "🛑 Останавливаем процесс бота (PID: \$BOT_PID)..."
            kill \$BOT_PID
            sleep 2
        fi
        
        # Проверяем, есть ли screen сессия с ботом
        SCREEN_SESSION=\$(screen -ls | grep -i bot | awk '{print \$1}' | head -1)
        
        if [ ! -z "\$SCREEN_SESSION" ]; then
            echo "📺 Найдена screen сессия: \$SCREEN_SESSION"
            screen -S \$(echo \$SCREEN_SESSION | cut -d. -f2) -X stuff "\$'\003'"
            sleep 1
            screen -S \$(echo \$SCREEN_SESSION | cut -d. -f2) -X stuff "python3 main.py\$'\r'"
            echo "✅ Бот перезапущен в screen сессии"
        else
            echo "📺 Screen сессии не найдено, создаем новую..."
            screen -dmS telegram_bot bash -c "cd ${SERVER_PATH} && python3 main.py"
            echo "✅ Бот запущен в новой screen сессии (telegram_bot)"
        fi
EOF
}

# Функция для перезапуска через pm2
restart_pm2() {
    echo "🔄 Пробуем перезапустить через pm2..."
    ssh ${SERVER_USER}@${SERVER_IP} << EOF
        cd ${SERVER_PATH}
        if command -v pm2 &> /dev/null; then
            pm2 restart main.py 2>/dev/null || pm2 restart all
            pm2 status
        else
            echo "❌ pm2 не установлен"
            return 1
        fi
EOF
}

# Функция для простого перезапуска (остановить и запустить заново)
restart_simple() {
    echo "🔄 Простой перезапуск (останавливаем и запускаем заново)..."
    ssh ${SERVER_USER}@${SERVER_IP} << EOF
        cd ${SERVER_PATH}
        
        # Останавливаем все процессы main.py
        echo "🛑 Останавливаем процессы бота..."
        pkill -f "python.*main.py" 2>/dev/null || pkill -f "python3.*main.py" 2>/dev/null
        sleep 2
        
        # Проверяем, что процесс остановлен
        if ps aux | grep -E "python.*main.py|python3.*main.py" | grep -v grep > /dev/null; then
            echo "⚠️  Процесс все еще работает, принудительно останавливаем..."
            pkill -9 -f "python.*main.py" 2>/dev/null || pkill -9 -f "python3.*main.py" 2>/dev/null
            sleep 1
        fi
        
        # Запускаем бота в фоновом режиме
        echo "🚀 Запускаем бота..."
        nohup python3 main.py > bot.log 2>&1 &
        sleep 2
        
        # Проверяем статус
        if ps aux | grep -E "python.*main.py|python3.*main.py" | grep -v grep > /dev/null; then
            echo "✅ Бот успешно запущен!"
            ps aux | grep -E "python.*main.py|python3.*main.py" | grep -v grep
            echo ""
            echo "📋 Лог бота: tail -f ${SERVER_PATH}/bot.log"
        else
            echo "❌ Не удалось запустить бота"
            echo "📋 Проверьте лог: cat ${SERVER_PATH}/bot.log"
            return 1
        fi
EOF
}

# Меню выбора способа перезапуска
echo "Выберите способ перезапуска:"
echo "1) Через systemd сервис"
echo "2) Через screen/tmux"
echo "3) Через pm2"
echo "4) Простой способ (остановить и запустить заново)"
echo "5) Автоматически (попробует все способы по очереди)"
echo ""
read -p "Ваш выбор [1-5] (по умолчанию 5): " choice
choice=${choice:-5}

case $choice in
    1)
        restart_systemd
        ;;
    2)
        restart_screen
        ;;
    3)
        restart_pm2
        ;;
    4)
        restart_simple
        ;;
    5)
        echo "🔄 Автоматический режим: пробуем все способы..."
        if restart_systemd 2>/dev/null; then
            echo "✅ Перезапущено через systemd"
        elif restart_pm2 2>/dev/null; then
            echo "✅ Перезапущено через pm2"
        elif restart_screen 2>/dev/null; then
            echo "✅ Перезапущено через screen"
        else
            echo "⚠️  Автоматические способы не сработали, используем простой способ..."
            restart_simple
        fi
        ;;
    *)
        echo "❌ Неверный выбор"
        exit 1
        ;;
esac

echo ""
echo "🎉 Готово! Бот должен быть перезапущен"
echo ""
echo "📋 Полезные команды для проверки:"
echo "   ssh ${SERVER_USER}@${SERVER_IP}"
echo "   cd ${SERVER_PATH}"
echo "   ps aux | grep main.py          # Проверить процесс"
echo "   tail -f bot.log                # Посмотреть лог"
echo "   screen -ls                     # Список screen сессий"
echo "   systemctl status ${SERVICE_NAME}  # Статус systemd сервиса"



