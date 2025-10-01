#!/bin/bash
echo "🔧 Увеличиваем лимит размера файла до 10MB..."

echo "📋 Текущие настройки Nginx:"
ssh root@212.67.11.50 "grep -n 'client_max_body_size' /etc/nginx/sites-available/flaskapp"

echo ""
echo "🔧 Изменяем настройки Nginx..."
ssh root@212.67.11.50 "sed -i 's/client_max_body_size [0-9]*M;/client_max_body_size 10M;/g' /etc/nginx/sites-available/flaskapp"

echo ""
echo "📋 Новые настройки Nginx:"
ssh root@212.67.11.50 "grep -n 'client_max_body_size' /etc/nginx/sites-available/flaskapp"

echo ""
echo "🔄 Перезапускаем Nginx..."
ssh root@212.67.11.50 "systemctl reload nginx"

echo ""
echo "✅ Лимит размера файла увеличен до 10MB!"
echo "🎯 Теперь можно загружать фото до 10MB" 