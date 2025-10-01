#!/bin/bash

# Комплексное исправление лимитов загрузки файлов на сервере
# Использование: ./fix_upload_limits_complete.sh

SERVER_IP="212.67.11.50"
SERVER_USER="root"
APP_DIR="/home/flaskapp/app"

echo "🔧 Комплексное исправление лимитов загрузки файлов..."
echo "Сервер: $SERVER_IP"
echo ""

# 1. Копируем обновленный app.py
echo "📤 1. Копируем обновленный app.py..."
scp app.py $SERVER_USER@$SERVER_IP:$APP_DIR/

if [ $? -eq 0 ]; then
    echo "✅ app.py успешно скопирован!"
else
    echo "❌ Ошибка при копировании app.py"
    exit 1
fi

echo ""
echo "🔧 2. Настраиваем системные лимиты на сервере..."
echo "Подключитесь к серверу и выполните следующие команды:"
echo ""
echo "ssh root@$SERVER_IP"
echo ""
echo "=== НА СЕРВЕРЕ ВЫПОЛНИТЕ: ==="
echo ""
echo "# 1. Настройка Nginx для больших файлов"
echo "cat > /etc/nginx/conf.d/upload_limits.conf << 'EOF'"
echo "client_max_body_size 100M;"
echo "client_body_timeout 300s;"
echo "client_header_timeout 300s;"
echo "proxy_read_timeout 300s;"
echo "proxy_connect_timeout 300s;"
echo "proxy_send_timeout 300s;"
echo "EOF"
echo ""
echo "# 2. Проверка и перезапуск Nginx"
echo "nginx -t"
echo "systemctl reload nginx"
echo ""
echo "# 3. Настройка системных лимитов"
echo "cat > /etc/security/limits.d/flaskapp.conf << 'EOF'"
echo "flaskapp soft nofile 65536"
echo "flaskapp hard nofile 65536"
echo "root soft nofile 65536"
echo "root hard nofile 65536"
echo "EOF"
echo ""
echo "# 4. Перезапуск приложения"
echo "systemctl restart flaskapp"
echo "systemctl status flaskapp"
echo ""
echo "# 5. Проверка логов"
echo "journalctl -u flaskapp -f"
echo ""
echo "=== КОМАНДЫ ЗАВЕРШЕНЫ ==="
echo ""
echo "📋 После выполнения проверьте:"
echo "1. Откройте сайт"
echo "2. Попробуйте загрузить фото 11MB+"
echo "3. Убедитесь, что ошибка 413 исчезла"
echo ""
echo "✅ Комплексное исправление подготовлено!" 