#!/bin/bash

# 🧹 ЧИСТОЕ ИСПРАВЛЕНИЕ ОШИБКИ 413
echo "🧹 ЧИСТОЕ ИСПРАВЛЕНИЕ ОШИБКИ 413"
echo "================================="

echo "💾 Создаем резервную копию..."
sudo cp /etc/nginx/sites-available/yatuta-rf /etc/nginx/sites-available/yatuta-rf.backup.$(date +%Y%m%d_%H%M%S)

echo "🔧 Создаем чистую конфигурацию..."

# Создаем полностью новую конфигурацию без дублирования
sudo tee /etc/nginx/sites-available/yatuta-rf > /dev/null << 'EOF'
server {
    listen 443 ssl;
    server_name ятута.рф www.ятута.рф;

    # Лимит для загрузки больших фото
    client_max_body_size 200M;

    # SSL сертификаты
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

    # SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Заголовки безопасности
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://api-maps.yandex.ru https://cdn.socket.io https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https://api-maps.yandex.ru https://api.yookassa.ru https://ipapi.co wss: ws:; font-src 'self';" always;

    # Основное проксирование
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # КРИТИЧЕСКИЕ НАСТРОЙКИ ДЛЯ ЗАГРУЗКИ ФАЙЛОВ
        proxy_request_buffering off;
        proxy_buffering off;
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_max_temp_file_size 0;
        proxy_buffer_size 32k;
        proxy_buffers 64 32k;
        proxy_busy_buffers_size 64k;
    }

    # Статические файлы
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

echo "✅ Чистая конфигурация создана"

# Проверяем конфигурацию
echo "🔍 Проверяем конфигурацию..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация корректна"
    echo "🔄 Перезапускаем Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx перезапущен"
    
    echo ""
    echo "🎉 ЧИСТОЕ ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
    echo "================================="
    echo "✅ Лимит файлов: 200MB"
    echo "✅ Буферизация отключена"
    echo "✅ Таймауты: 300s"
    echo "✅ Нет дублирующихся директив"
    echo ""
    echo "🌐 Теперь загрузка фото 11.8MB должна работать!"
else
    echo "❌ Ошибка в конфигурации!"
    echo "🔄 Восстанавливаем резервную копию..."
    sudo cp /etc/nginx/sites-available/yatuta-rf.backup.* /etc/nginx/sites-available/yatuta-rf 2>/dev/null || true
fi

