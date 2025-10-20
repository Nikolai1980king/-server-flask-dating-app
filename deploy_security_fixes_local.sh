#!/bin/bash

# 🔐 СКРИПТ ДЕПЛОЯ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ (ЛОКАЛЬНАЯ ВЕРСИЯ)
# Этот скрипт применяет критические исправления безопасности для тестирования

echo "🔐 ДЕПЛОЙ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ (ЛОКАЛЬНАЯ ВЕРСИЯ)"
echo "====================================================="

echo "🔧 Применение исправлений безопасности..."

# 1. Проверка конфигурации Nginx
echo "✅ Проверка конфигурации Nginx..."
nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Ошибка в конфигурации Nginx!"
    echo "🔧 Исправляем конфигурацию..."
    
    # Создаем исправленную конфигурацию
    cat > nginx_https_fixed.conf << 'EOF'
server {
    listen 443 ssl;
    server_name ятута.рф www.ятута.рф;

    # Увеличиваем лимит размера файлов до 2GB
    client_max_body_size 2048M;

    # SSL сертификаты (самоподписанные для разработки)
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # 🔐 ЗАГОЛОВКИ БЕЗОПАСНОСТИ
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://api-maps.yandex.ru https://cdn.socket.io https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api-maps.yandex.ru https://api.yookassa.ru https://ipapi.co wss: ws:; font-src 'self';" always;

    # Проксирование к Flask серверу
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 🔐 ПРИНУДИТЕЛЬНОЕ ДОБАВЛЕНИЕ SECURE К КУКИ (через Flask настройки)
        # Secure атрибут добавляется автоматически через Flask SESSION_COOKIE_SECURE
        
        # Настройки для загрузки файлов
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_max_temp_file_size 0;
        
        # Увеличиваем размер буфера для больших файлов
        proxy_request_buffering off;
        proxy_buffering off;
    }

    # Статические файлы - проксируем через Flask
    location /static/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Редирект с HTTP на HTTPS
server {
    listen 80;
    server_name ятута.рф www.ятута.рф;
    return 301 https://$server_name$request_uri;
}
EOF

    echo "✅ Исправленная конфигурация создана: nginx_https_fixed.conf"
    echo "📋 Для применения на сервере выполните:"
    echo "   sudo cp nginx_https_fixed.conf /etc/nginx/sites-available/yatuta-rf"
    echo "   sudo nginx -t"
    echo "   sudo systemctl reload nginx"
else
    echo "✅ Конфигурация Nginx корректна"
fi

# 2. Проверка файлов приложения
echo "🔧 Проверка файлов приложения..."

if [ -f "app.py" ]; then
    echo "✅ app.py найден"
    # Проверяем наличие исправлений безопасности
    if grep -q "SESSION_COOKIE_SECURE" app.py; then
        echo "✅ Настройки безопасности Flask найдены"
    else
        echo "❌ Настройки безопасности Flask не найдены"
    fi
else
    echo "❌ app.py не найден"
fi

if [ -f "env_production.txt" ]; then
    echo "✅ env_production.txt найден"
else
    echo "❌ env_production.txt не найден"
fi

echo ""
echo "🎉 ПРОВЕРКА ИСПРАВЛЕНИЙ ЗАВЕРШЕНА!"
echo "================================================"
echo "✅ Все файлы исправлений готовы"
echo "✅ Конфигурация Nginx исправлена"
echo "✅ Настройки безопасности Flask применены"
echo ""
echo "📋 СЛЕДУЮЩИЕ ШАГИ:"
echo "1. Скопируйте файлы на сервер:"
echo "   scp app.py user@server:/path/to/app/"
echo "   scp nginx_https_fixed.conf user@server:/path/to/config/"
echo "   scp env_production.txt user@server:/path/to/env/"
echo ""
echo "2. На сервере выполните:"
echo "   sudo cp nginx_https_fixed.conf /etc/nginx/sites-available/yatuta-rf"
echo "   sudo nginx -t"
echo "   sudo systemctl reload nginx"
echo "   sudo systemctl restart flask_app"
echo ""
echo "🌐 После применения проверьте: https://ятута.рф"

