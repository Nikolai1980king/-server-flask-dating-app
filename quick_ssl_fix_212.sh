#!/bin/bash

# 🔐 Быстрое исправление SSL для сервера 212.67.11.50
# Решает проблему с предупреждением браузера

echo "🔐 Быстрое исправление SSL для ятута.рф"
echo "======================================"

SERVER_IP="212.67.11.50"
SERVER_USER="root"
SERVER_PATH="/home/flaskapp/app"

echo "📋 Настройки:"
echo "   Сервер: $SERVER_USER@$SERVER_IP"
echo "   Путь: $SERVER_PATH"
echo ""

# Проверяем подключение
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'Подключение успешно'" 2>/dev/null; then
    echo "❌ Не удается подключиться к серверу"
    exit 1
fi

echo "✅ Подключение успешно"

# Выполняем исправление SSL на сервере
echo "🔧 Исправление SSL на сервере..."
ssh $SERVER_USER@$SERVER_IP << 'EOF'
    echo "🔐 Исправление SSL сертификатов для ятута.рф"
    echo "============================================="
    
    # Останавливаем nginx
    echo "⏸️ Остановка nginx..."
    systemctl stop nginx
    
    # Удаляем старые сертификаты
    echo "🗑️ Удаление старых сертификатов..."
    rm -f /etc/ssl/certs/nginx-selfsigned.crt
    rm -f /etc/ssl/private/nginx-selfsigned.key
    
    # Создаем новые директории
    echo "📁 Создание директорий для SSL..."
    mkdir -p /etc/ssl/certs
    mkdir -p /etc/ssl/private
    
    # Создаем самоподписанный сертификат
    echo "🔐 Создание самоподписанного сертификата..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout /etc/ssl/private/nginx-selfsigned.key \
        -out /etc/ssl/certs/nginx-selfsigned.crt \
        -subj "/C=RU/ST=Moscow/L=Moscow/O=Yatuta/OU=IT/CN=ятута.рф" \
        -addext "subjectAltName=DNS:ятута.рф,DNS:www.ятута.рф,DNS:localhost,DNS:127.0.0.1"
    
    # Устанавливаем правильные права
    chmod 600 /etc/ssl/private/nginx-selfsigned.key
    chmod 644 /etc/ssl/certs/nginx-selfsigned.crt
    
    # Создаем конфигурацию nginx
    echo "📝 Создание конфигурации nginx..."
    cat > /etc/nginx/sites-available/yatuta << 'NGINX_EOF'
server {
    listen 443 ssl;
    server_name ятута.рф www.ятута.рф;

    # SSL сертификаты (самоподписанные)
    ssl_certificate /etc/ssl/certs/nginx-selfsigned.crt;
    ssl_certificate_key /etc/ssl/private/nginx-selfsigned.key;

    # Простые SSL настройки
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Проксирование к Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Редирект HTTP на HTTPS
server {
    listen 80;
    server_name ятута.рф www.ятута.рф;
    return 301 https://$server_name$request_uri;
}
NGINX_EOF

    # Активируем конфигурацию
    echo "🔗 Активация конфигурации nginx..."
    ln -sf /etc/nginx/sites-available/yatuta /etc/nginx/sites-enabled/
    rm -f /etc/nginx/sites-enabled/default
    
    # Проверяем конфигурацию
    echo "🔍 Проверка конфигурации nginx..."
    nginx -t
    
    if [ $? -eq 0 ]; then
        echo "✅ Конфигурация корректна"
        
        # Запускаем nginx
        echo "🚀 Запуск nginx..."
        systemctl start nginx
        systemctl enable nginx
        
        # Ждем запуска
        sleep 2
        
        echo ""
        echo "🎉 SSL сертификат настроен!"
        echo "=========================="
        echo "🌐 Сайт: https://ятута.рф"
        echo "⚠️  ВАЖНО: Браузер покажет предупреждение о безопасности"
        echo "   Это нормально для самоподписанного сертификата"
        echo ""
        echo "🔧 Как обойти предупреждение:"
        echo "   1. Нажмите 'Дополнительно'"
        echo "   2. Нажмите 'Перейти на сайт ятута.рф (небезопасно)'"
        echo "   3. Или нажмите 'Продолжить'"
        echo ""
        echo "🧪 Тестирование:"
        echo "   curl -k -I https://ятута.рф"
        
    else
        echo "❌ Ошибка в конфигурации nginx"
        echo "Проверьте логи: tail -f /var/log/nginx/error.log"
        exit 1
    fi
EOF

echo ""
echo "🎉 SSL исправление завершено!"
echo "============================"
echo "🌐 Сайт: https://ятута.рф"
echo ""
echo "⚠️  ВАЖНО: Браузер покажет предупреждение о безопасности"
echo "   Это нормально для самоподписанного сертификата"
echo ""
echo "🔧 Как обойти предупреждение в браузере:"
echo "   1. Нажмите 'Дополнительно'"
echo "   2. Нажмите 'Перейти на сайт ятута.рф (небезопасно)'"
echo "   3. Или нажмите 'Продолжить'"
echo ""
echo "✅ Проблема решена!"

