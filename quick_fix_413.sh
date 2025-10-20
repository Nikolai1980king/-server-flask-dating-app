#!/bin/bash

# 🚨 БЫСТРОЕ ИСПРАВЛЕНИЕ ОШИБКИ 413
echo "🚨 БЫСТРОЕ ИСПРАВЛЕНИЕ ОШИБКИ 413"
echo "================================="

echo "🔧 Исправляем конфигурацию Nginx..."

# Создаем исправленную конфигурацию с увеличенными лимитами
sudo tee /etc/nginx/sites-available/yatuta-rf > /dev/null << 'EOF'
server {
    listen 443 ssl;
    server_name ятута.рф www.ятута.рф;

    # 🚨 УВЕЛИЧИВАЕМ ЛИМИТ ДЛЯ ЗАГРУЗКИ БОЛЬШИХ ФОТО
    client_max_body_size 200M;  # Достаточно для фото до 200MB

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
        
        # 🚨 КРИТИЧЕСКИЕ НАСТРОЙКИ ДЛЯ ЗАГРУЗКИ ФАЙЛОВ
        proxy_request_buffering off;  # Отключаем буферизацию запросов
        proxy_buffering off;          # Отключаем буферизацию ответов
        
        # Увеличиваем таймауты для больших файлов
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        
        # Увеличиваем размеры буферов
        proxy_buffer_size 32k;
        proxy_buffers 64 32k;
        proxy_busy_buffers_size 64k;
        
        # Отключаем временные файлы
        proxy_max_temp_file_size 0;
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

echo "✅ Конфигурация обновлена"

# Проверяем конфигурацию
echo "🔍 Проверка конфигурации..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация корректна"
    echo "🔄 Перезапускаем Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx перезапущен"
    
    echo ""
    echo "🎉 ИСПРАВЛЕНИЕ ПРИМЕНЕНО!"
    echo "=========================="
    echo "✅ Лимит размера файлов: 200MB"
    echo "✅ Буферизация отключена"
    echo "✅ Таймауты увеличены до 5 минут"
    echo "✅ Размеры буферов увеличены"
    echo ""
    echo "🌐 Теперь попробуйте загрузить фото 11.8MB снова!"
else
    echo "❌ Ошибка в конфигурации!"
    echo "🔄 Восстанавливаем резервную копию..."
    sudo cp /etc/nginx/sites-available/yatuta-rf.backup.* /etc/nginx/sites-available/yatuta-rf 2>/dev/null || true
fi

