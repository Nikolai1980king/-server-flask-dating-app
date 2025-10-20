#!/bin/bash

# 🚀 Деплой откаченного проекта на удаленный сервер
# После отката к коммиту 22abcc9

echo "🚀 Деплой откаченного проекта на сервер"
echo "======================================"

# Настройки сервера (измените на ваши)
SERVER_IP="192.168.255.137"  # Замените на IP вашего сервера
SERVER_USER="root"            # Замените на пользователя сервера
SERVER_PATH="/home/flaskapp/app"  # Замените на путь на сервере

echo "📋 Настройки деплоя:"
echo "   Сервер: $SERVER_USER@$SERVER_IP"
echo "   Путь: $SERVER_PATH"
echo ""

# Проверяем подключение к серверу
echo "🔍 Проверка подключения к серверу..."
if ! ssh -o ConnectTimeout=10 $SERVER_USER@$SERVER_IP "echo 'Подключение успешно'" 2>/dev/null; then
    echo "❌ Не удается подключиться к серверу $SERVER_USER@$SERVER_IP"
    echo "Проверьте:"
    echo "1. Доступен ли сервер?"
    echo "2. Правильный ли IP адрес?"
    echo "3. Есть ли SSH доступ?"
    echo "4. Правильный ли пользователь?"
    exit 1
fi

echo "✅ Подключение к серверу успешно"

# Создаем архив проекта
echo "📦 Создание архива проекта..."
tar -czf project_rollback.tar.gz \
    app.py \
    requirements.txt \
    config.py \
    static/ \
    templates/ \
    *.py \
    *.md \
    *.sh \
    --exclude="venv" \
    --exclude="__pycache__" \
    --exclude="*.pyc" \
    --exclude=".git"

if [ $? -eq 0 ]; then
    echo "✅ Архив создан: project_rollback.tar.gz"
else
    echo "❌ Ошибка создания архива"
    exit 1
fi

# Копируем архив на сервер
echo "📤 Копирование архива на сервер..."
scp project_rollback.tar.gz $SERVER_USER@$SERVER_IP:$SERVER_PATH/

if [ $? -eq 0 ]; then
    echo "✅ Архив скопирован на сервер"
else
    echo "❌ Ошибка копирования архива"
    exit 1
fi

# Подключаемся к серверу для установки
echo "🔧 Установка на сервере..."
ssh $SERVER_USER@$SERVER_IP << EOF
    echo "📂 Переходим в папку приложения..."
    cd $SERVER_PATH
    
    echo "🔄 Останавливаем приложение..."
    systemctl stop flaskapp 2>/dev/null || pkill -f app.py 2>/dev/null || echo "Приложение не запущено"
    
    echo "💾 Создаем резервную копию базы данных..."
    if [ -f "dating_app.db" ]; then
        cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db
        echo "✅ Резервная копия создана"
    fi
    
    echo "📦 Распаковываем архив..."
    tar -xzf project_rollback.tar.gz
    
    echo "📦 Устанавливаем зависимости..."
    pip install -r requirements.txt
    
    echo "📁 Создаем необходимые папки..."
    mkdir -p uploads
    mkdir -p static/uploads
    chmod 755 uploads
    chmod 755 static/uploads
    
    echo "⚙️ Настраиваем переменные окружения..."
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            echo "📝 Создан файл .env из примера"
        else
            echo "FLASK_ENV=production" > .env
            echo "SECRET_KEY=your-secret-key-here" >> .env
            echo "📝 Создан базовый файл .env"
        fi
        echo "⚠️ ВАЖНО: Отредактируйте .env файл с вашими настройками!"
    fi
    
    echo "🔄 Запускаем приложение..."
    systemctl start flaskapp 2>/dev/null || {
        echo "Запускаем приложение вручную..."
        nohup python app.py > flask.log 2>&1 &
    }
    
    echo "📊 Проверяем статус..."
    sleep 3
    if systemctl is-active --quiet flaskapp; then
        echo "✅ Приложение запущено через systemctl"
        systemctl status flaskapp --no-pager
    else
        echo "✅ Приложение запущено вручную"
        ps aux | grep app.py | grep -v grep
    fi
    
    echo "📋 Проверяем логи..."
    if [ -f "flask.log" ]; then
        echo "Последние 5 строк лога:"
        tail -5 flask.log
    fi
    
    echo "✅ Установка завершена!"
EOF

if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Деплой завершен успешно!"
    echo "=========================="
    echo "🌐 Сайт должен быть доступен по адресу:"
    echo "   http://$SERVER_IP"
    echo "   https://$SERVER_IP (если настроен SSL)"
    echo ""
    echo "📋 Следующие шаги:"
    echo "1. Проверьте работу сайта"
    echo "2. При необходимости отредактируйте .env файл:"
    echo "   ssh $SERVER_USER@$SERVER_IP"
    echo "   nano $SERVER_PATH/.env"
    echo "3. Перезапустите приложение:"
    echo "   systemctl restart flaskapp"
    echo ""
    echo "🧪 Тестирование:"
    echo "   curl http://$SERVER_IP"
    echo "   curl https://$SERVER_IP"
else
    echo "❌ Ошибка при установке на сервере"
    echo "Проверьте логи на сервере:"
    echo "ssh $SERVER_USER@$SERVER_IP"
    echo "tail -f $SERVER_PATH/flask.log"
fi

# Очищаем временный архив
echo "🧹 Очистка временных файлов..."
rm -f project_rollback.tar.gz

echo "✅ Деплой завершен!"

