#!/bin/bash

echo "🔧 Исправление ошибки 413 (Request Entity Too Large)"

# Останавливаем nginx
echo "1. Останавливаем nginx..."
sudo systemctl stop nginx

# Копируем исправленную конфигурацию
echo "2. Копируем исправленную конфигурацию..."
sudo cp nginx_https.conf /etc/nginx/sites-available/flask_server
sudo ln -sf /etc/nginx/sites-available/flask_server /etc/nginx/sites-enabled/

# Удаляем дефолтную конфигурацию если она есть
sudo rm -f /etc/nginx/sites-enabled/default

# Проверяем конфигурацию
echo "3. Проверяем конфигурацию nginx..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация корректна"
    
    # Запускаем nginx
    echo "4. Запускаем nginx..."
    sudo systemctl start nginx
    sudo systemctl enable nginx
    
    echo "5. Проверяем статус nginx..."
    sudo systemctl status nginx --no-pager
    
    echo ""
    echo "🎉 Готово! Теперь можно загружать файлы до 2GB"
    echo "📝 Для применения изменений перезапустите Flask сервер"
    echo "🌐 Откройте: https://192.168.0.24"
else
    echo "❌ Ошибка в конфигурации nginx"
    exit 1
fi 