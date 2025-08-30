#!/bin/bash

# Скрипт для настройки HTTPS на сервере
# Использование: ./setup_https.sh

SERVER_IP="212.67.11.50"
SERVER_USER="root"
DOMAIN="ятута.рф"

echo "🔒 Настройка HTTPS для домена $DOMAIN"
echo "Сервер: $SERVER_IP"
echo "=" * 50
echo ""

echo "📋 План настройки:"
echo "1. Подключение к серверу"
echo "2. Установка Certbot"
echo "3. Получение SSL сертификата"
echo "4. Настройка nginx"
echo "5. Перезапуск сервисов"
echo ""

echo "🚀 Начинаем настройку HTTPS..."
echo ""

# Подключаемся к серверу и выполняем настройку
ssh $SERVER_USER@$SERVER_IP << 'EOF'

echo "📦 Обновляем пакеты..."
apt update

echo "🔧 Устанавливаем Certbot..."
apt install -y certbot python3-certbot-nginx

echo "📋 Проверяем конфигурацию nginx..."
if [ ! -f "/etc/nginx/sites-available/flaskapp" ]; then
    echo "❌ Конфигурация nginx не найдена!"
    echo "Создаем базовую конфигурацию..."
    
    cat > /etc/nginx/sites-available/flaskapp << 'NGINX_CONFIG'
server {
    listen 80;
    server_name ятута.рф www.ятута.рф;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /static {
        alias /home/flaskapp/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
}
NGINX_CONFIG
    
    # Активируем конфигурацию
    ln -sf /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    echo "✅ Конфигурация nginx создана"
fi

echo "🔒 Получаем SSL сертификат..."
certbot --nginx -d ятута.рф -d www.ятута.рф --non-interactive --agree-tos --email admin@ятута.рф

if [ $? -eq 0 ]; then
    echo "✅ SSL сертификат успешно получен!"
else
    echo "❌ Ошибка получения SSL сертификата"
    echo "Попробуем получить сертификат вручную..."
    certbot certonly --nginx -d ятута.рф -d www.ятута.рф --non-interactive --agree-tos --email admin@ятута.рф
fi

echo "🔄 Перезапускаем nginx..."
systemctl restart nginx

echo "📊 Проверяем статус nginx..."
systemctl status nginx --no-pager

echo "🔍 Проверяем SSL сертификат..."
certbot certificates

echo "📋 Информация о домене:"
echo "HTTP: http://ятута.рф"
echo "HTTPS: https://ятута.рф"
echo ""

echo "✅ Настройка HTTPS завершена!"
echo "🌐 Теперь сайт доступен по HTTPS: https://ятута.рф"

EOF

echo ""
echo "🎯 Настройка HTTPS завершена!"
echo ""
echo "📋 Проверьте результат:"
echo "1. Откройте https://ятута.рф"
echo "2. Попробуйте геолокацию"
echo "3. Убедитесь, что показывается доменное имя"
echo ""
echo "🔧 Если нужна помощь, проверьте логи:"
echo "   ssh root@$SERVER_IP"
echo "   journalctl -u nginx -f"
echo "   certbot certificates" 