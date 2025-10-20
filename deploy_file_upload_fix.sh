#!/bin/bash

# 🔧 СКРИПТ ИСПРАВЛЕНИЯ ОШИБКИ 413 ДЛЯ ЗАГРУЗКИ ФАЙЛОВ
# Этот скрипт исправляет проблему с загрузкой больших файлов (ошибка 413)

echo "🔧 ИСПРАВЛЕНИЕ ОШИБКИ 413 ДЛЯ ЗАГРУЗКИ ФАЙЛОВ"
echo "=============================================="

echo "🔧 Применение исправлений для загрузки файлов..."

# 1. Создаем резервную копию текущей конфигурации
echo "💾 Создание резервной копии..."
sudo cp /etc/nginx/sites-available/yatuta-rf /etc/nginx/sites-available/yatuta-rf.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "Файл конфигурации не найден, создаем новый"

# 2. Остановка сервисов
echo "⏹️  Остановка сервисов..."
sudo systemctl stop nginx 2>/dev/null || true

# 3. Обновление конфигурации Nginx с исправлениями для загрузки файлов
echo "🔧 Обновление конфигурации Nginx..."

# Создаем исправленную конфигурацию
sudo tee /etc/nginx/sites-available/yatuta-rf > /dev/null << 'EOF'
server {
    listen 443 ssl;
    server_name ятута.рф www.ятута.рф;

    # 🔧 ЛИМИТ РАЗМЕРА ФАЙЛОВ ДЛЯ ЗАГРУЗКИ ФОТО
    client_max_body_size 100M;  # Достаточно для фото до 100MB

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
        
        # 🔧 ОПТИМИЗАЦИЯ ДЛЯ ЗАГРУЗКИ БОЛЬШИХ ФАЙЛОВ (до 100MB)
        # Увеличиваем таймауты для больших файлов
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        proxy_max_temp_file_size 0;
        
        # Отключаем буферизацию для загрузки файлов (исправляет ошибку 413)
        proxy_request_buffering off;
        proxy_buffering off;
        
        # Увеличиваем размер буферов для лучшей производительности
        proxy_buffer_size 16k;
        proxy_buffers 32 16k;
        proxy_busy_buffers_size 32k;
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

# 6. Запуск сервисов
echo "🚀 Запуск сервисов..."
sudo systemctl start nginx

# 7. Проверка статуса
echo "✅ Проверка статуса сервисов..."
sudo systemctl status nginx --no-pager -l | head -10

# 8. Проверка доступности
echo "🌐 Проверка доступности сайта..."
sleep 3
curl -k -I https://ятута.рф 2>/dev/null | head -5 || echo "Сайт недоступен"

echo ""
echo "🎉 ИСПРАВЛЕНИЕ ОШИБКИ 413 ЗАВЕРШЕНО!"
echo "================================================"
echo "✅ Лимит размера файлов увеличен до 100MB"
echo "✅ Отключена буферизация запросов"
echo "✅ Увеличены таймауты для загрузки"
echo "✅ Оптимизированы размеры буферов"
echo ""
echo "📋 ИСПРАВЛЕНИЯ:"
echo "   • client_max_body_size: 100M"
echo "   • proxy_request_buffering: off"
echo "   • proxy_buffering: off"
echo "   • proxy_*_timeout: 300s"
echo "   • Увеличены размеры буферов"
echo ""
echo "🌐 Теперь можно загружать фото до 100MB!"
echo "🔧 Проверьте загрузку фото размером 11.8MB"

