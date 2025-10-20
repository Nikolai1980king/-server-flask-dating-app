#!/bin/bash

# 🔐 СКРИПТ ДЕПЛОЯ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ ДЛЯ ятута.рф
# Этот скрипт применяет критические исправления безопасности

echo "🔐 ДЕПЛОЙ ИСПРАВЛЕНИЙ БЕЗОПАСНОСТИ ДЛЯ ятута.рф"
echo "================================================"

# Проверяем, что мы на сервере
if [[ "$(hostname)" != *"212.67.11.50"* ]] && [[ "$(hostname)" != *"yatuta"* ]]; then
    echo "⚠️  Внимание: Этот скрипт предназначен для сервера ятута.рф"
    read -p "Продолжить? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🔧 Применение исправлений безопасности..."

# 1. Остановка сервисов
echo "⏹️  Остановка сервисов..."
sudo systemctl stop nginx
sudo systemctl stop flask_app 2>/dev/null || true

# 2. Обновление конфигурации Nginx
echo "🔧 Обновление конфигурации Nginx..."
sudo cp nginx_https.conf /etc/nginx/sites-available/yatuta-rf
sudo ln -sf /etc/nginx/sites-available/yatuta-rf /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default

# 3. Проверка конфигурации Nginx
echo "✅ Проверка конфигурации Nginx..."
sudo nginx -t
if [ $? -ne 0 ]; then
    echo "❌ Ошибка в конфигурации Nginx!"
    exit 1
fi

# 4. Обновление переменных окружения
echo "🔧 Обновление переменных окружения..."
if [ -f /home/yatuta/.env ]; then
    cp env_production.txt /home/yatuta/.env
    echo "✅ Переменные окружения обновлены"
else
    echo "⚠️  Файл .env не найден, создаем новый..."
    cp env_production.txt /home/yatuta/.env
fi

# 5. Обновление приложения
echo "🔧 Обновление приложения..."
cp app.py /home/yatuta/app.py

# 6. Установка прав доступа
echo "🔧 Установка прав доступа..."
sudo chown -R yatuta:yatuta /home/yatuta/
sudo chmod 644 /home/yatuta/app.py
sudo chmod 644 /home/yatuta/.env

# 7. Запуск сервисов
echo "🚀 Запуск сервисов..."
sudo systemctl start nginx
sudo systemctl start flask_app 2>/dev/null || true

# 8. Проверка статуса
echo "✅ Проверка статуса сервисов..."
sudo systemctl status nginx --no-pager -l
echo "---"
sudo systemctl status flask_app --no-pager -l 2>/dev/null || echo "Flask app service not found"

# 9. Проверка доступности
echo "🌐 Проверка доступности сайта..."
sleep 5
curl -k -I https://ятута.рф 2>/dev/null | head -5

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

