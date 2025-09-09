#!/bin/bash

# Автоматическая настройка Nginx для больших файлов
# Использование: ./setup_nginx_upload_limits.sh

SERVER_IP="212.67.11.50"
SERVER_USER="root"

echo "🔧 Настройка Nginx для загрузки больших файлов..."
echo "Сервер: $SERVER_IP"
echo ""

# Создаем конфигурацию Nginx
echo "📝 Создаем конфигурацию Nginx..."
cat > nginx_upload_limits.conf << 'EOF'
# Настройки для загрузки больших файлов
client_max_body_size 100M;
client_body_timeout 300s;
client_header_timeout 300s;
proxy_read_timeout 300s;
proxy_connect_timeout 300s;
proxy_send_timeout 300s;

# Дополнительные настройки для стабильности
client_body_buffer_size 128k;
client_header_buffer_size 1k;
large_client_header_buffers 4 4k;
EOF

# Копируем конфигурацию на сервер
echo "📤 Копируем конфигурацию на сервер..."
scp nginx_upload_limits.conf $SERVER_USER@$SERVER_IP:/etc/nginx/conf.d/

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация скопирована!"
else
    echo "❌ Ошибка при копировании конфигурации"
    exit 1
fi

# Создаем скрипт для применения настроек на сервере
echo "📝 Создаем скрипт применения настроек..."
cat > apply_nginx_settings.sh << 'EOF'
#!/bin/bash

echo "🔧 Применение настроек Nginx..."

# Проверяем конфигурацию
echo "📋 Проверяем конфигурацию Nginx..."
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация корректна!"
    
    # Перезагружаем Nginx
    echo "🔄 Перезагружаем Nginx..."
    systemctl reload nginx
    
    if [ $? -eq 0 ]; then
        echo "✅ Nginx успешно перезагружен!"
    else
        echo "❌ Ошибка при перезагрузке Nginx"
        exit 1
    fi
else
    echo "❌ Ошибка в конфигурации Nginx"
    exit 1
fi

# Настраиваем системные лимиты
echo "🔧 Настраиваем системные лимиты..."
cat > /etc/security/limits.d/flaskapp.conf << 'LIMITS_EOF'
flaskapp soft nofile 65536
flaskapp hard nofile 65536
root soft nofile 65536
root hard nofile 65536
LIMITS_EOF

echo "✅ Системные лимиты настроены!"

# Перезапускаем приложение
echo "🔄 Перезапускаем Flask приложение..."
systemctl restart flaskapp

if [ $? -eq 0 ]; then
    echo "✅ Flask приложение перезапущено!"
else
    echo "❌ Ошибка при перезапуске Flask"
    exit 1
fi

echo ""
echo "📊 Проверяем статус сервисов..."
echo "=== Статус Nginx ==="
systemctl status nginx --no-pager -l
echo ""
echo "=== Статус Flask ==="
systemctl status flaskapp --no-pager -l
echo ""
echo "✅ Все настройки применены успешно!"
echo "🌐 Теперь можно загружать файлы до 100MB"
EOF

# Копируем скрипт на сервер
echo "📤 Копируем скрипт применения на сервер..."
scp apply_nginx_settings.sh $SERVER_USER@$SERVER_IP:/tmp/

if [ $? -eq 0 ]; then
    echo "✅ Скрипт скопирован!"
else
    echo "❌ Ошибка при копировании скрипта"
    exit 1
fi

echo ""
echo "🚀 Запускаем применение настроек на сервере..."
ssh $SERVER_USER@$SERVER_IP "chmod +x /tmp/apply_nginx_settings.sh && /tmp/apply_nginx_settings.sh"

if [ $? -eq 0 ]; then
    echo "✅ Все настройки применены успешно!"
else
    echo "❌ Ошибка при применении настроек"
    exit 1
fi

# Очищаем временные файлы
rm -f nginx_upload_limits.conf apply_nginx_settings.sh

echo ""
echo "📋 Проверьте работу загрузки файлов:"
echo "1. Откройте сайт"
echo "2. Попробуйте загрузить фото 11MB+"
echo "3. Убедитесь, что ошибка 413 исчезла"
echo ""
echo "✅ Настройка Nginx завершена!" 