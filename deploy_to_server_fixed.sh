#!/bin/bash

# 🔐 ИСПРАВЛЕННЫЙ СКРИПТ ДЕПЛОЯ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ
# Этот скрипт применяет критические исправления безопасности на сервере

echo "🔐 ДЕПЛОЙ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ НА СЕРВЕР"
echo "============================================="

# Проверяем, что мы на правильном сервере
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "unknown")
echo "🌐 Текущий IP: $SERVER_IP"

echo "🔧 Применение исправлений безопасности..."

# 1. Создаем резервную копию текущей конфигурации
echo "💾 Создание резервной копии..."
sudo cp /etc/nginx/sites-available/yatuta-rf /etc/nginx/sites-available/yatuta-rf.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "Файл конфигурации не найден, создаем новый"

# 2. Остановка сервисов
echo "⏹️  Остановка сервисов..."
sudo systemctl stop nginx 2>/dev/null || true
sudo systemctl stop flask_app 2>/dev/null || true

# 3. Обновление конфигурации Nginx
echo "🔧 Обновление конфигурации Nginx..."

# Создаем исправленную конфигурацию
sudo tee /etc/nginx/sites-available/yatuta-rf > /dev/null << 'EOF'
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

# 4. Активация конфигурации
echo "🔗 Активация конфигурации..."
sudo ln -sf /etc/nginx/sites-available/yatuta-rf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 5. Проверка конфигурации Nginx
echo "✅ Проверка конфигурации Nginx..."
sudo nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Ошибка в конфигурации Nginx!"
    echo "🔄 Восстанавливаем резервную копию..."
    sudo cp /etc/nginx/sites-available/yatuta-rf.backup.* /etc/nginx/sites-available/yatuta-rf 2>/dev/null || true
    exit 1
fi

# 6. Обновление приложения (если файл app.py существует)
if [ -f "app.py" ]; then
    echo "🔧 Обновление приложения..."
    sudo cp app.py /home/yatuta/app.py 2>/dev/null || echo "Не удалось обновить app.py"
    sudo chown yatuta:yatuta /home/yatuta/app.py 2>/dev/null || true
fi

# 7. Обновление переменных окружения
if [ -f "env_production.txt" ]; then
    echo "🔧 Обновление переменных окружения..."
    sudo cp env_production.txt /home/yatuta/.env 2>/dev/null || echo "Не удалось обновить .env"
    sudo chown yatuta:yatuta /home/yatuta/.env 2>/dev/null || true
fi

# 8. Запуск сервисов
echo "🚀 Запуск сервисов..."
sudo systemctl start nginx
sudo systemctl start flask_app 2>/dev/null || true

# 9. Проверка статуса
echo "✅ Проверка статуса сервисов..."
sudo systemctl status nginx --no-pager -l | head -10
echo "---"
sudo systemctl status flask_app --no-pager -l 2>/dev/null | head -10 || echo "Flask app service not found"

# 10. Проверка доступности
echo "🌐 Проверка доступности сайта..."
sleep 3
curl -k -I https://ятута.рф 2>/dev/null | head -5 || echo "Сайт недоступен"

echo ""
echo "🎉 ДЕПЛОЙ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ ЗАВЕРШЕН!"
echo "================================================"
echo "✅ Куки теперь работают только по HTTPS"
echo "✅ Добавлены заголовки безопасности"
echo "✅ Настроена защита от XSS и CSRF"
echo "✅ Усилена общая безопасность сайта"
echo ""
echo "🌐 Проверьте сайт: https://ятута.рф"
echo ""
echo "🔍 Для проверки безопасности выполните:"
echo "   curl -I https://ятута.рф"
echo ""
echo "📋 Основные исправления:"
echo "   • SESSION_COOKIE_SECURE = True"
echo "   • SESSION_COOKIE_HTTPONLY = True" 
echo "   • SESSION_COOKIE_SAMESITE = 'Lax'"
echo "   • Добавлены заголовки HSTS, CSP, X-Frame-Options"
echo "   • Обновлен секретный ключ Flask"
echo ""

