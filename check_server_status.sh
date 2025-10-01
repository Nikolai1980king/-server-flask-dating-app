#!/bin/bash

echo "🔍 Проверка статуса сервера..."
echo "Сервер: 212.67.11.50"

# Подключаемся к серверу и проверяем статус
ssh root@212.67.11.50 << 'EOF'
    echo "📋 Проверяем статус Flask приложения..."
    systemctl status flaskapp --no-pager
    
    echo ""
    echo "📋 Проверяем логи Flask приложения..."
    journalctl -u flaskapp -n 20 --no-pager
    
    echo ""
    echo "📋 Проверяем процессы Python..."
    ps aux | grep python
    
    echo ""
    echo "📋 Проверяем использование портов..."
    netstat -tlnp | grep :5000
    
    echo ""
    echo "📋 Проверяем права доступа к файлам..."
    ls -la /home/flaskapp/app/
    ls -la /home/flaskapp/app/instance/
    
    echo ""
    echo "📋 Проверяем размер базы данных..."
    ls -lh /home/flaskapp/app/instance/dating_app.db
EOF

echo ""
echo "✅ Проверка завершена!" 