#!/bin/bash

echo "🚀 Деплой исправления перехода после оплаты"
echo "Сервер: 212.67.11.50"
echo "=" * 50

echo "📤 Копируем исправленный app.py на сервер..."
scp app.py root@212.67.11.50:/home/flaskapp/app/

if [ $? -eq 0 ]; then
    echo "✅ app.py скопирован успешно"
else
    echo "❌ Ошибка копирования app.py"
    exit 1
fi

echo "📤 Копируем объединенный .env файл..."
scp .env.merged root@212.67.11.50:/home/flaskapp/app/.env

if [ $? -eq 0 ]; then
    echo "✅ .env файл скопирован успешно"
else
    echo "❌ Ошибка копирования .env файла"
    exit 1
fi

echo "🔄 Подключаемся к серверу для перезапуска..."
ssh root@212.67.11.50 << 'EOF'
    echo "📂 Переходим в папку приложения..."
    cd /home/flaskapp/app
    
    echo "⚠️ ВАЖНО: Отредактируйте .env файл с настройками ЮKassa!"
    echo "nano .env"
    echo "Замените:"
    echo "  - YOOKASSA_SHOP_ID=your_shop_id_here"
    echo "  - YOOKASSA_SECRET_KEY=your_secret_key_here"
    echo ""
    echo "DEPLOY_DOMAIN уже настроен: https://192.168.255.137"
    
    echo "🔄 Останавливаем приложение..."
    systemctl stop flaskapp
    
    echo "🚀 Запускаем приложение..."
    systemctl start flaskapp
    
    echo "📊 Проверяем статус..."
    systemctl status flaskapp --no-pager
    
    echo "📋 Проверяем логи..."
    journalctl -u flaskapp -n 5 --no-pager
    
    echo "✅ Исправление деплоено!"
EOF

echo ""
echo "🎉 Деплой исправления завершен!"
echo ""
echo "📋 Что исправлено:"
echo "✅ Переходы после оплаты теперь работают на правильном домене"
echo "✅ Убраны все ссылки на localhost"
echo "✅ Автоматическое перенаправление на профиль пользователя"
echo "✅ Правильная установка cookie для сессий"
echo ""
echo "🧪 Для тестирования:"
echo "1. Откройте: https://192.168.255.137"
echo "2. Создайте профиль"
echo "3. Перейдите к оплате"
echo "4. После оплаты проверьте переход на профиль"
echo ""
echo "⚠️ Не забудьте настроить ЮKassa в .env файле на сервере!"