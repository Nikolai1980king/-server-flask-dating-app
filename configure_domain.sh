#!/bin/bash

echo "🌐 Настройка домена для приложения"
echo ""

# Запрашиваем домен
read -p "Введите ваш домен (например: cafe-dating.ru): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Домен не указан!"
    exit 1
fi

echo ""
echo "🔧 Создаем команды для настройки домена: $DOMAIN"
echo ""

# Создаем файл с командами для сервера
cat > server_domain_setup.sh << EOF
#!/bin/bash
echo "🌐 Настройка домена: $DOMAIN"

# Создаем резервную копию
cp /etc/nginx/sites-available/flaskapp /etc/nginx/sites-available/flaskapp.backup.\$(date +%Y%m%d_%H%M%S)

# Обновляем server_name
sed -i 's/server_name 212.67.11.50;/server_name $DOMAIN www.$DOMAIN;/g' /etc/nginx/sites-available/flaskapp

# Добавляем client_max_body_size если его нет
if ! grep -q "client_max_body_size" /etc/nginx/sites-available/flaskapp; then
    sed -i '/listen 443 ssl;/a\    client_max_body_size 10M;' /etc/nginx/sites-available/flaskapp
fi

echo "📋 Обновленная конфигурация:"
grep -n "server_name\|client_max_body_size" /etc/nginx/sites-available/flaskapp

echo ""
echo "🔍 Проверяем синтаксис Nginx:"
nginx -t

if [ \$? -eq 0 ]; then
    echo "✅ Синтаксис корректен"
    echo ""
    echo "🔄 Перезапускаем Nginx:"
    systemctl reload nginx
    
    echo ""
    echo "📊 Статус Nginx:"
    systemctl status nginx --no-pager
    
    echo ""
    echo "🎯 Готово! Ваше приложение теперь доступно по адресу:"
    echo "   https://$DOMAIN"
    echo "   https://www.$DOMAIN"
else
    echo "❌ Ошибка в конфигурации Nginx!"
fi
EOF

echo "✅ Файл server_domain_setup.sh создан!"
echo ""
echo "🚀 Для применения изменений выполните на сервере:"
echo "   ssh root@212.67.11.50"
echo "   chmod +x server_domain_setup.sh"
echo "   ./server_domain_setup.sh"
echo ""
echo "⚠️  Убедитесь, что DNS-записи настроены в панели Beget!"
echo "   A-запись: @ → 212.67.11.50" 