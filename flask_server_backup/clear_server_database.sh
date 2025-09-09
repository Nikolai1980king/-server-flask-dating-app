#!/bin/bash

echo "🗑️ Очистка базы данных на сервере..."
echo "Сервер: 212.67.11.50"
echo "База данных: /home/flaskapp/app/instance/dating_app.db"

# Подключаемся к серверу и очищаем базу данных
ssh root@212.67.11.50 << 'EOF'
    echo "📋 Останавливаем Flask приложение..."
    systemctl stop flaskapp
    
    echo "🗑️ Создаем резервную копию базы данных..."
    cp /home/flaskapp/app/instance/dating_app.db /home/flaskapp/app/instance/dating_app_backup_$(date +%Y%m%d_%H%M%S).db
    
    echo "🗑️ Удаляем старую базу данных..."
    rm -f /home/flaskapp/app/instance/dating_app.db
    
    echo "🔄 Создаем новую пустую базу данных..."
    cd /home/flaskapp/app
    python3 -c "
from app import db
db.create_all()
print('✅ Новая база данных создана')
"
    
    echo "📋 Запускаем Flask приложение..."
    systemctl start flaskapp
    
    echo "📋 Проверяем статус..."
    systemctl status flaskapp --no-pager
    
    echo "📋 Проверяем логи..."
    journalctl -u flaskapp -n 5 --no-pager
EOF

echo ""
echo "✅ База данных очищена!"
echo ""
echo "📋 Что было сделано:"
echo "1. ✅ Остановлено Flask приложение"
echo "2. ✅ Создана резервная копия старой БД"
echo "3. ✅ Удалена старая база данных"
echo "4. ✅ Создана новая пустая база данных"
echo "5. ✅ Запущено Flask приложение"
echo ""
echo "🧪 Теперь можно тестировать:"
echo "1. Откройте сайт в браузере"
echo "2. Создайте новую анкету"
echo "3. Проверьте ограничение на одну анкету"
echo "4. Проверьте работу карты" 