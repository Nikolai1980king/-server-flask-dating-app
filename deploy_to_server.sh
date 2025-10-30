#!/bin/bash

echo "🚀 Деплой на сервер 212.67.11.50"
echo "📁 Папка: /home/flaskapp/app"
echo "=" * 50

# Проверяем, что архив существует
if [ ! -f "deploy_package.tar.gz" ]; then
    echo "❌ Архив deploy_package.tar.gz не найден!"
    echo "Сначала запустите: ./prepare_for_deploy.sh"
    exit 1
fi

echo "📦 Копируем архив на сервер..."
scp deploy_package.tar.gz root@212.67.11.50:/home/flaskapp/app/

if [ $? -eq 0 ]; then
    echo "✅ Архив скопирован успешно"
else
    echo "❌ Ошибка копирования архива"
    exit 1
fi

echo "🔄 Подключаемся к серверу для установки..."
ssh root@212.67.11.50 << 'EOF'
    echo "📂 Переходим в папку приложения..."
    cd /home/flaskapp/app
    
    echo "📦 Распаковываем архив..."
    tar -xzf deploy_package.tar.gz
    
    echo "📦 Устанавливаем зависимости..."
    pip install -r requirements.txt
    
    echo "📁 Создаем папку для загрузок..."
    mkdir -p uploads
    chmod 755 uploads
    
    echo "⚙️ Настраиваем переменные окружения..."
    if [ ! -f ".env" ]; then
        cp .env.example .env
        echo "📝 Создан файл .env из примера"
        echo "⚠️ ВАЖНО: Отредактируйте .env файл с вашими настройками!"
    fi
    
    echo "🔄 Останавливаем приложение..."
    systemctl stop flaskapp
    
    echo "🚀 Запускаем приложение..."
    systemctl start flaskapp
    
    echo "📊 Проверяем статус..."
    systemctl status flaskapp --no-pager
    
    echo "📋 Проверяем логи..."
    journalctl -u flaskapp -n 5 --no-pager
    
    echo "✅ Деплой завершен!"
EOF

echo ""
echo "🎉 Деплой завершен!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Отредактируйте .env файл на сервере:"
echo "   ssh root@212.67.11.50"
echo "   nano /home/flaskapp/app/.env"
echo ""
echo "2. Обязательно установите:"
echo "   DEPLOY_DOMAIN=https://192.168.255.137"
echo "   YOOKASSA_SHOP_ID=your_shop_id"
echo "   YOOKASSA_SECRET_KEY=your_secret_key"
echo "   YOOKASSA_TEST_MODE=False"
echo ""
echo "3. Перезапустите приложение:"
echo "   systemctl restart flaskapp"
echo ""
echo "4. Проверьте работу:"
echo "   https://192.168.255.137"

















