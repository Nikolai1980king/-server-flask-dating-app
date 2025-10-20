#!/bin/bash

# 🚨 МГНОВЕННОЕ ИСПРАВЛЕНИЕ ОШИБКИ 413
echo "🚨 МГНОВЕННОЕ ИСПРАВЛЕНИЕ ОШИБКИ 413"
echo "===================================="

echo "🔧 Исправляем конфигурацию Nginx мгновенно..."

# 1. Увеличиваем лимит размера файлов
echo "📏 Увеличиваем лимит размера файлов до 200MB..."
sudo sed -i 's/client_max_body_size [0-9]*[MG];/client_max_body_size 200M;/' /etc/nginx/sites-available/yatuta-rf

# 2. Добавляем отключение буферизации если его нет
echo "🚫 Отключаем буферизацию запросов..."
if ! grep -q "proxy_request_buffering off" /etc/nginx/sites-available/yatuta-rf; then
    sudo sed -i '/proxy_set_header X-Forwarded-Proto/a\        proxy_request_buffering off;' /etc/nginx/sites-available/yatuta-rf
fi

if ! grep -q "proxy_buffering off" /etc/nginx/sites-available/yatuta-rf; then
    sudo sed -i '/proxy_request_buffering off/a\        proxy_buffering off;' /etc/nginx/sites-available/yatuta-rf
fi

# 3. Увеличиваем таймауты
echo "⏱️  Увеличиваем таймауты..."
sudo sed -i 's/proxy_connect_timeout [0-9]*s;/proxy_connect_timeout 300s;/' /etc/nginx/sites-available/yatuta-rf
sudo sed -i 's/proxy_send_timeout [0-9]*s;/proxy_send_timeout 300s;/' /etc/nginx/sites-available/yatuta-rf
sudo sed -i 's/proxy_read_timeout [0-9]*s;/proxy_read_timeout 300s;/' /etc/nginx/sites-available/yatuta-rf

# 4. Проверяем конфигурацию
echo "🔍 Проверяем конфигурацию..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация корректна"
    echo "🔄 Перезапускаем Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx перезапущен"
    
    echo ""
    echo "🎉 ИСПРАВЛЕНИЕ ПРИМЕНЕНО МГНОВЕННО!"
    echo "===================================="
    echo "✅ Лимит размера файлов: 200MB"
    echo "✅ Буферизация отключена"
    echo "✅ Таймауты: 300s (5 минут)"
    echo ""
    echo "🌐 Теперь попробуйте загрузить фото 11.8MB!"
    echo "📱 Если все еще ошибка 413, попробуйте фото меньшего размера"
else
    echo "❌ Ошибка в конфигурации!"
fi

# 5. Показываем текущие настройки
echo ""
echo "📋 ТЕКУЩИЕ НАСТРОЙКИ:"
grep "client_max_body_size" /etc/nginx/sites-available/yatuta-rf
grep "proxy_request_buffering" /etc/nginx/sites-available/yatuta-rf
grep "proxy_buffering" /etc/nginx/sites-available/yatuta-rf
grep "proxy_.*_timeout" /etc/nginx/sites-available/yatuta-rf

