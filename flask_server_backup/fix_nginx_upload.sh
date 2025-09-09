#!/bin/bash

echo "🔧 Настройка Nginx для загрузки больших файлов на сервере..."
echo ""

# Создаем конфигурацию Nginx
echo "📝 Создаем конфигурацию Nginx..."
cat > nginx_upload_fix.conf << 'EOF'
# Настройки для загрузки больших файлов
client_max_body_size 2G;
client_body_timeout 300s;
client_header_timeout 300s;
proxy_read_timeout 300s;
proxy_connect_timeout 300s;
proxy_send_timeout 300s;
EOF

echo "📤 Копируем конфигурацию на сервер..."
scp nginx_upload_fix.conf root@212.67.11.50:/etc/nginx/conf.d/

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация скопирована!"
else
    echo "❌ Ошибка при копировании"
    exit 1
fi

echo ""
echo "🚀 Подключаемся к серверу для применения настроек..."
ssh root@212.67.11.50 << 'SERVER_COMMANDS'
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
echo "📊 Статус сервисов:"
echo "=== Nginx ==="
systemctl status nginx --no-pager -l | head -10
echo ""
echo "=== Flask ==="
systemctl status flaskapp --no-pager -l | head -10
echo ""
echo "✅ Все настройки применены!"
echo "🌐 Теперь можно загружать файлы до 2GB"
SERVER_COMMANDS

# Очищаем временный файл
rm -f nginx_upload_fix.conf

echo ""
echo "📋 Проверьте работу загрузки файлов:"
echo "1. Откройте сайт"
echo "2. Попробуйте загрузить фото 11MB+"
echo "3. Убедитесь, что ошибка 413 исчезла"
echo ""
echo "✅ Настройка завершена!" 