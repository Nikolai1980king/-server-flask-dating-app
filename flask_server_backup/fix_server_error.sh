#!/bin/bash

echo "🔧 Исправление ошибки сервера..."
echo "Сервер: 212.67.11.50"

# Подключаемся к серверу и исправляем проблему
ssh root@212.67.11.50 << 'EOF'
    echo "📋 Останавливаем все процессы Python..."
    pkill -f python
    pkill -f flask
    
    echo "📋 Останавливаем Flask приложение..."
    systemctl stop flaskapp
    
    echo "📋 Ждем 3 секунды..."
    sleep 3
    
    echo "📋 Проверяем, что порт 5000 свободен..."
    netstat -tlnp | grep :5000 || echo "Порт 5000 свободен"
    
    echo "📋 Проверяем права доступа..."
    chown -R flaskapp:flaskapp /home/flaskapp/app/
    chmod -R 755 /home/flaskapp/app/
    
    echo "📋 Проверяем базу данных..."
    if [ -f /home/flaskapp/app/instance/dating_app.db ]; then
        echo "База данных существует"
        ls -lh /home/flaskapp/app/instance/dating_app.db
    else
        echo "Создаем новую базу данных..."
        cd /home/flaskapp/app
        python3 -c "
from app import db
db.create_all()
print('✅ Новая база данных создана')
"
    fi
    
    echo "📋 Запускаем Flask приложение..."
    systemctl start flaskapp
    
    echo "📋 Ждем 5 секунд для запуска..."
    sleep 5
    
    echo "📋 Проверяем статус..."
    systemctl status flaskapp --no-pager
    
    echo "📋 Проверяем логи..."
    journalctl -u flaskapp -n 10 --no-pager
    
    echo "📋 Проверяем, что приложение отвечает..."
    curl -s http://localhost:5000/ | head -5
EOF

echo ""
echo "✅ Исправление завершено!"
echo ""
echo "🧪 Проверьте сайт в браузере" 