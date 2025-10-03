#!/bin/bash

echo "⚙️ Настройка .env файла на сервере..."
echo "Сервер: 212.67.11.50"
echo "=" * 50

# Проверяем, что у нас есть шаблон
if [ ! -f "env_production_template.txt" ]; then
    echo "❌ Файл env_production_template.txt не найден!"
    exit 1
fi

echo "📤 Копируем шаблон .env файла на сервер..."
scp env_production_template.txt root@212.67.11.50:/home/flaskapp/app/.env

if [ $? -eq 0 ]; then
    echo "✅ Шаблон .env скопирован на сервер"
else
    echo "❌ Ошибка копирования шаблона .env"
    exit 1
fi

echo "🔄 Подключаемся к серверу для настройки..."
ssh root@212.67.11.50 << 'EOF'
    echo "📂 Переходим в папку приложения..."
    cd /home/flaskapp/app
    
    echo "📝 Текущий .env файл:"
    cat .env
    
    echo ""
    echo "⚠️ ВАЖНО: Отредактируйте .env файл с вашими настройками ЮKassa!"
    echo "Для редактирования используйте: nano .env"
    echo ""
    echo "Обязательно замените:"
    echo "  - YOOKASSA_SHOP_ID=your_shop_id_here"
    echo "  - YOOKASSA_SECRET_KEY=your_secret_key_here"
    echo ""
    echo "DEPLOY_DOMAIN уже настроен: https://192.168.255.137"
    
    echo "🔄 Перезапускаем приложение..."
    systemctl restart flaskapp
    
    echo "📊 Проверяем статус..."
    systemctl status flaskapp --no-pager
    
    echo "✅ Настройка завершена!"
EOF

echo ""
echo "🎉 Настройка .env файла завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Подключитесь к серверу: ssh root@212.67.11.50"
echo "2. Отредактируйте .env: nano /home/flaskapp/app/.env"
echo "3. Замените настройки ЮKassa на ваши"
echo "4. Перезапустите: systemctl restart flaskapp"
echo ""
echo "📖 Подробная инструкция: ENV_SETUP_GUIDE.md"
