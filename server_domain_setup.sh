#!/bin/bash
echo "🌐 Настройка домена: ятута.рф"

# Создаем резервную копию
cp /etc/nginx/sites-available/flaskapp /etc/nginx/sites-available/flaskapp.backup.$(date +%Y%m%d_%H%M%S)

# Обновляем server_name
sed -i 's/server_name 212.67.11.50;/server_name ятута.рф www.ятута.рф;/g' /etc/nginx/sites-available/flaskapp

# Добавляем client_max_body_size если его нет
if ! grep -q "client_max_body_size" /etc/nginx/sites-available/flaskapp; then
    sed -i '/listen 443 ssl;/a\    client_max_body_size 10M;' /etc/nginx/sites-available/flaskapp
fi

echo "📋 Обновленная конфигурация:"
grep -n "server_name\|client_max_body_size" /etc/nginx/sites-available/flaskapp

echo ""
echo "🔍 Проверяем синтаксис Nginx:"
nginx -t

if [ $? -eq 0 ]; then
    echo "✅ Синтаксис корректен"
    echo ""
    echo "🔄 Перезапускаем Nginx:"
    systemctl reload nginx
    
    echo ""
    echo "📊 Статус Nginx:"
    systemctl status nginx --no-pager
    
    echo ""
    echo "🎯 Готово! Ваше приложение теперь доступно по адресу:"
    echo "   https://ятута.рф"
    echo "   https://www.ятута.рф"
else
    echo "❌ Ошибка в конфигурации Nginx!"
fi
