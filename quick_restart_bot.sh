#!/bin/bash

# ⚡ Быстрый перезапуск бота (автоматический выбор способа)

echo "⚡ Быстрый перезапуск телеграм-бота..."

SERVER_USER="${BOT_SERVER_USER:-root}"
SERVER_IP="${BOT_SERVER_IP:-212.67.11.50}"
SERVER_PATH="${BOT_SERVER_PATH:-../bot.yatuta.rf/public_html}"

ssh ${SERVER_USER}@${SERVER_IP} << EOF
    cd ${SERVER_PATH}
    
    echo "🛑 Останавливаем бота..."
    pkill -f "python.*main.py" 2>/dev/null || pkill -f "python3.*main.py" 2>/dev/null
    sleep 2
    
    # Если process все еще работает, принудительно останавливаем
    if ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py" > /dev/null; then
        pkill -9 -f "python.*main.py" 2>/dev/null || pkill -9 -f "python3.*main.py" 2>/dev/null
        sleep 1
    fi
    
    echo "🚀 Запускаем бота..."
    nohup python3 main.py > bot.log 2>&1 &
    sleep 2
    
    if ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py" > /dev/null; then
        echo "✅ Бот успешно перезапущен!"
        echo ""
        echo "📊 Текущий процесс:"
        ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py" | grep -v grep
    else
        echo "❌ Ошибка запуска бота"
        echo "📋 Последние строки лога:"
        tail -10 bot.log
    fi
EOF

echo ""
echo "✅ Готово! Для просмотра лога: ssh ${SERVER_USER}@${SERVER_IP} 'tail -f ${SERVER_PATH}/bot.log'"



