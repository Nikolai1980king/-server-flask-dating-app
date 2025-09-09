#!/bin/bash

echo "🌐 Обновление конфигурации Nginx для домена"
echo ""

# Запрашиваем домен у пользователя
read -p "Введите ваш домен (например: cafe-dating.ru): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Домен не указан!"
    exit 1
fi

echo ""
echo "🔧 Обновляем конфигурацию Nginx для домена: $DOMAIN"
echo ""

# Создаем команды для выполнения на сервере
cat << EOF > nginx_update_commands.sh
#!/bin/bash
echo "🔧 Обновление конфигурации Nginx для домена: $DOMAIN"

# Создаем резервную копию
cp /etc/nginx/sites-available/flaskapp /etc/nginx/sites-available/flaskapp.backup.$(date +%Y%m%d_%H%M%S)

# Обновляем server_name
sed -i 's/server_name 212.67.11.50;/server_name $DOMAIN www.$DOMAIN;/g' /etc/nginx/sites-available/flaskapp

# Проверяем результат
echo "📋 Обновленная конфигурация:"
grep -n "server_name" /etc/nginx/sites-available/flaskapp

# Проверяем синтаксис
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
    echo "Восстанавливаем резервную копию..."
    cp /etc/nginx/sites-available/flaskapp.backup.* /etc/nginx/sites-available/flaskapp
fi
EOF

echo "📋 Команды для выполнения на сервере сохранены в файл: nginx_update_commands.sh"
echo ""
echo "🚀 Для применения изменений выполните на сервере:"
echo "   ssh root@212.67.11.50"
echo "   chmod +x nginx_update_commands.sh"
echo "   ./nginx_update_commands.sh"
echo ""
echo "⚠️  Убедитесь, что DNS-записи настроены в панели Beget!" 