#!/bin/bash
echo "🔧 Исправляем настройки Nginx..."

# Подключаемся к серверу и изменяем настройки
ssh root@212.67.11.50 << 'EOF'
echo "📋 Текущие настройки:"
grep -n 'client_max_body_size' /etc/nginx/sites-available/flaskapp

echo ""
echo "🔧 Изменяем настройки..."
sed -i 's/client_max_body_size [0-9]*M;/client_max_body_size 10M;/g' /etc/nginx/sites-available/flaskapp

echo ""
echo "📋 Новые настройки:"
grep -n 'client_max_body_size' /etc/nginx/sites-available/flaskapp

echo ""
echo "🔄 Перезапускаем Nginx..."
systemctl reload nginx

echo ""
echo "✅ Готово!"
EOF

echo "🎯 Лимит размера файла увеличен до 10MB!" 