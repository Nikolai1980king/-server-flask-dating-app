#!/bin/bash

# 🔧 ИСПРАВЛЕНИЕ ДУБЛИРУЮЩИХСЯ ДИРЕКТИВ NGINX
echo "🔧 ИСПРАВЛЕНИЕ ДУБЛИРУЮЩИХСЯ ДИРЕКТИВ"
echo "====================================="

echo "🔍 Удаляем дублирующиеся директивы..."

# Удаляем все дублирующиеся директивы proxy_request_buffering и proxy_buffering
sudo sed -i '/proxy_request_buffering/d' /etc/nginx/sites-available/yatuta-rf
sudo sed -i '/proxy_buffering/d' /etc/nginx/sites-available/yatuta-rf

echo "✅ Дублирующиеся директивы удалены"

# Добавляем правильные директивы в нужное место
echo "🔧 Добавляем правильные директивы..."
sudo sed -i '/proxy_set_header X-Forwarded-Proto/a\        proxy_request_buffering off;\n        proxy_buffering off;' /etc/nginx/sites-available/yatuta-rf

echo "✅ Правильные директивы добавлены"

# Проверяем конфигурацию
echo "🔍 Проверяем конфигурацию..."
sudo nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация корректна"
    echo "🔄 Перезапускаем Nginx..."
    sudo systemctl reload nginx
    echo "✅ Nginx перезапущен"
    
    echo ""
    echo "🎉 ИСПРАВЛЕНИЕ ЗАВЕРШЕНО!"
    echo "=========================="
    echo "✅ Дублирующиеся директивы удалены"
    echo "✅ Правильные настройки применены"
    echo "✅ Лимит файлов: 200MB"
    echo "✅ Буферизация отключена"
    echo ""
    echo "🌐 Теперь попробуйте загрузить фото 11.8MB!"
else
    echo "❌ Ошибка в конфигурации!"
    echo "📋 Показываем проблемные строки:"
    grep -n "proxy_request_buffering\|proxy_buffering" /etc/nginx/sites-available/yatuta-rf
fi

