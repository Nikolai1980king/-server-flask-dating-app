#!/bin/bash

# Скрипт для генерации SSL сертификатов для nginx

echo "🔐 Генерация SSL сертификатов для nginx..."

# Создаем директории если их нет
sudo mkdir -p /etc/ssl/certs
sudo mkdir -p /etc/ssl/private

# Генерируем самоподписанный сертификат
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/nginx-selfsigned.key \
    -out /etc/ssl/certs/nginx-selfsigned.crt \
    -subj "/C=RU/ST=Moscow/L=Moscow/O=Development/CN=192.168.255.137"

echo "✅ SSL сертификаты созданы!"
echo "📁 Сертификат: /etc/ssl/certs/nginx-selfsigned.crt"
echo "🔑 Ключ: /etc/ssl/private/nginx-selfsigned.key"

# Устанавливаем правильные права
sudo chmod 644 /etc/ssl/certs/nginx-selfsigned.crt
sudo chmod 600 /etc/ssl/private/nginx-selfsigned.key

echo "🔒 Права доступа установлены"
echo ""
echo "📝 Следующие шаги:"
echo "1. Скопируйте nginx_https.conf в /etc/nginx/sites-available/"
echo "2. Создайте символическую ссылку в sites-enabled/"
echo "3. Перезапустите nginx"
echo ""
echo "Команды:"
echo "sudo cp nginx_https.conf /etc/nginx/sites-available/flask_https"
echo "sudo ln -s /etc/nginx/sites-available/flask_https /etc/nginx/sites-enabled/"
echo "sudo nginx -t"
echo "sudo systemctl restart nginx" 