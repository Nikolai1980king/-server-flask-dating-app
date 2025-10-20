#!/bin/bash

# 🚀 Быстрое копирование откаченного проекта на сервер
# Без архивации, прямое копирование файлов

echo "🚀 Быстрое копирование проекта на сервер"
echo "======================================="

# Настройки сервера (измените на ваши)
SERVER_IP="192.168.255.137"  # Замените на IP вашего сервера
SERVER_USER="root"            # Замените на пользователя сервера
SERVER_PATH="/home/flaskapp/app"  # Замените на путь на сервере

echo "📋 Настройки:"
echo "   Сервер: $SERVER_USER@$SERVER_IP"
echo "   Путь: $SERVER_PATH"
echo ""

# Проверяем подключение
echo "🔍 Проверка подключения..."
if ! ssh -o ConnectTimeout=5 $SERVER_USER@$SERVER_IP "echo 'OK'" 2>/dev/null; then
    echo "❌ Не удается подключиться к серверу"
    echo "Проверьте IP адрес и SSH доступ"
    exit 1
fi

echo "✅ Подключение успешно"

# Останавливаем приложение на сервере
echo "⏸️ Останавливаем приложение на сервере..."
ssh $SERVER_USER@$SERVER_IP "
    systemctl stop flaskapp 2>/dev/null || pkill -f app.py 2>/dev/null || echo 'Приложение не запущено'
    echo '✅ Приложение остановлено'
"

# Создаем резервную копию на сервере
echo "💾 Создаем резервную копию на сервере..."
ssh $SERVER_USER@$SERVER_IP "
    cd $SERVER_PATH
    if [ -f 'dating_app.db' ]; then
        cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db
        echo '✅ Резервная копия базы данных создана'
    fi
    if [ -d 'app_backup' ]; then
        rm -rf app_backup
    fi
    mkdir -p app_backup
    cp -r app.py requirements.txt config.py static templates *.py *.md *.sh app_backup/ 2>/dev/null || echo 'Копирование файлов в резерв'
    echo '✅ Резервная копия проекта создана'
"

# Копируем основные файлы
echo "📤 Копируем основные файлы..."
scp app.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp requirements.txt $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp config.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# Копируем папки
echo "📁 Копируем папки..."
scp -r static/ $SERVER_USER@$SERVER_IP:$SERVER_PATH/
scp -r templates/ $SERVER_USER@$SERVER_IP:$SERVER_PATH/

# Копируем Python файлы
echo "🐍 Копируем Python файлы..."
scp *.py $SERVER_USER@$SERVER_IP:$SERVER_PATH/ 2>/dev/null || echo "Некоторые .py файлы не найдены"

# Копируем скрипты
echo "📜 Копируем скрипты..."
scp *.sh $SERVER_USER@$SERVER_IP:$SERVER_PATH/ 2>/dev/null || echo "Некоторые .sh файлы не найдены"

# Копируем документацию
echo "📚 Копируем документацию..."
scp *.md $SERVER_USER@$SERVER_IP:$SERVER_PATH/ 2>/dev/null || echo "Некоторые .md файлы не найдены"

# Устанавливаем зависимости и запускаем
echo "🔧 Устанавливаем зависимости и запускаем..."
ssh $SERVER_USER@$SERVER_IP << EOF
    cd $SERVER_PATH
    
    echo "📦 Устанавливаем зависимости..."
    pip install -r requirements.txt
    
    echo "📁 Создаем необходимые папки..."
    mkdir -p uploads
    mkdir -p static/uploads
    chmod 755 uploads
    chmod 755 static/uploads
    
    echo "⚙️ Проверяем переменные окружения..."
    if [ ! -f ".env" ]; then
        echo "FLASK_ENV=production" > .env
        echo "SECRET_KEY=your-secret-key-here" >> .env
        echo "📝 Создан базовый файл .env"
        echo "⚠️ ВАЖНО: Отредактируйте .env файл с вашими настройками!"
    fi
    
    echo "🚀 Запускаем приложение..."
    systemctl start flaskapp 2>/dev/null || {
        echo "Запускаем приложение вручную..."
        nohup python app.py > flask.log 2>&1 &
        echo "PID: \$!"
    }
    
    echo "📊 Проверяем статус..."
    sleep 3
    if systemctl is-active --quiet flaskapp; then
        echo "✅ Приложение запущено через systemctl"
    else
        echo "✅ Приложение запущено вручную"
        ps aux | grep app.py | grep -v grep
    fi
    
    echo "📋 Проверяем логи..."
    if [ -f "flask.log" ]; then
        echo "Последние 3 строки лога:"
        tail -3 flask.log
    fi
    
    echo "✅ Установка завершена!"
EOF

echo ""
echo "🎉 Быстрое копирование завершено!"
echo "================================"
echo "🌐 Сайт должен быть доступен по адресу:"
echo "   http://$SERVER_IP"
echo "   https://$SERVER_IP (если настроен SSL)"
echo ""
echo "📋 Для проверки:"
echo "   curl http://$SERVER_IP"
echo "   ssh $SERVER_USER@$SERVER_IP 'tail -f $SERVER_PATH/flask.log'"
echo ""
echo "✅ Деплой завершен!"

