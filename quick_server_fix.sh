#!/bin/bash

echo "🔧 Быстрое исправление сервера..."

# Подключаемся к серверу и исправляем проблему
ssh -o StrictHostKeyChecking=no root@212.67.11.50 << 'EOF'
    echo "📋 Останавливаем приложение..."
    systemctl stop flaskapp
    
    echo "📋 Убиваем все процессы Python..."
    pkill -f python || true
    pkill -f gunicorn || true
    
    echo "📋 Ждем 3 секунды..."
    sleep 3
    
    echo "📋 Проверяем права доступа..."
    chown -R flaskapp:flaskapp /home/flaskapp/app/
    chmod -R 755 /home/flaskapp/app/
    
    echo "📋 Проверяем базу данных..."
    if [ ! -f /home/flaskapp/app/instance/dating_app.db ]; then
        echo "Создаем новую базу данных..."
        cd /home/flaskapp/app
        python3 -c "from app import db; db.create_all(); print('✅ БД создана')"
    fi
    
    echo "📋 Запускаем приложение..."
    systemctl start flaskapp
    
    echo "📋 Ждем 5 секунд..."
    sleep 5
    
    echo "📋 Проверяем статус..."
    systemctl status flaskapp --no-pager
    
    echo "📋 Проверяем логи..."
    journalctl -u flaskapp -n 5 --no-pager
    
    echo "📋 Тестируем локально..."
    curl -s http://localhost:5000/ | head -3
    
    echo "📋 Проверяем Nginx..."
    systemctl status nginx --no-pager
    
    echo "📋 Проверяем логи Nginx..."
    tail -5 /var/log/nginx/error.log
EOF

echo ""
echo "✅ Исправление завершено!"
echo "🧪 Проверьте сайт в браузере" 