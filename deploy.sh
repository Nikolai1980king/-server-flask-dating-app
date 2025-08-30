#!/bin/bash

# Скрипт для быстрого деплоя приложения

echo "🚀 Начинаем деплой приложения..."

# Проверяем наличие необходимых файлов
echo "📋 Проверяем файлы..."
if [ ! -f "app.py" ]; then
    echo "❌ Файл app.py не найден!"
    exit 1
fi

if [ ! -f "requirements.txt" ]; then
    echo "❌ Файл requirements.txt не найден!"
    exit 1
fi

if [ ! -f "Procfile" ]; then
    echo "❌ Файл Procfile не найден!"
    exit 1
fi

echo "✅ Все необходимые файлы найдены"

# Создаем папку для загрузок если её нет
if [ ! -d "static/uploads" ]; then
    echo "📁 Создаем папку для загрузок..."
    mkdir -p static/uploads
fi

# Проверяем переменные окружения
if [ -z "$SECRET_KEY" ]; then
    echo "⚠️  Внимание: SECRET_KEY не установлен!"
    echo "   Установите переменную окружения SECRET_KEY"
fi

# Выбор платформы для деплоя
echo ""
echo "🌐 Выберите платформу для деплоя:"
echo "1) Heroku"
echo "2) Render"
echo "3) Railway"
echo "4) Docker"
echo "5) VPS (ручная настройка)"
read -p "Введите номер (1-5): " choice

case $choice in
    1)
        echo "🚀 Деплой на Heroku..."
        if ! command -v heroku &> /dev/null; then
            echo "❌ Heroku CLI не установлен!"
            echo "   Установите: https://devcenter.heroku.com/articles/heroku-cli"
            exit 1
        fi
        
        # Проверяем авторизацию в Heroku
        if ! heroku auth:whoami &> /dev/null; then
            echo "🔐 Авторизуйтесь в Heroku..."
            heroku login
        fi
        
        # Создаем приложение если его нет
        if [ -z "$HEROKU_APP_NAME" ]; then
            echo "📝 Создаем новое приложение Heroku..."
            heroku create
        else
            echo "📝 Используем существующее приложение: $HEROKU_APP_NAME"
            heroku git:remote -a $HEROKU_APP_NAME
        fi
        
        # Добавляем базу данных
        echo "🗄️  Добавляем PostgreSQL..."
        heroku addons:create heroku-postgresql:mini
        
        # Устанавливаем переменные окружения
        echo "⚙️  Настраиваем переменные окружения..."
        heroku config:set FLASK_ENV=production
        heroku config:set MAX_REGISTRATION_DISTANCE=3000
        heroku config:set PROFILE_LIFETIME_HOURS=24
        
        # Деплой
        echo "📤 Отправляем код на Heroku..."
        git add .
        git commit -m "Deploy to production"
        git push heroku main
        
        echo "✅ Деплой завершен!"
        echo "🌐 Ваше приложение доступно по адресу:"
        heroku info -s | grep web_url | cut -d= -f2
        ;;
        
    2)
        echo "🚀 Деплой на Render..."
        echo "📝 Создайте новый Web Service на https://render.com"
        echo "🔗 Подключите ваш GitHub репозиторий"
        echo "⚙️  Настройте переменные окружения:"
        echo "   - FLASK_ENV=production"
        echo "   - SECRET_KEY=your-secret-key"
        echo "   - MAX_REGISTRATION_DISTANCE=3000"
        echo "   - PROFILE_LIFETIME_HOURS=24"
        echo "🔧 Build Command: pip install -r requirements.txt"
        echo "🚀 Start Command: gunicorn app:app"
        ;;
        
    3)
        echo "🚀 Деплой на Railway..."
        echo "📝 Создайте новый проект на https://railway.app"
        echo "🔗 Подключите ваш GitHub репозиторий"
        echo "⚙️  Railway автоматически определит настройки"
        ;;
        
    4)
        echo "🐳 Деплой с Docker..."
        echo "📦 Собираем Docker образ..."
        docker build -t flaskapp .
        
        echo "🚀 Запускаем с Docker Compose..."
        docker-compose up -d
        
        echo "✅ Приложение запущено на http://localhost:5000"
        ;;
        
    5)
        echo "🖥️  Ручная настройка на VPS..."
        echo "📋 Выполните следующие шаги:"
        echo "1) Подключитесь к серверу"
        echo "2) Установите Python, pip, nginx, supervisor"
        echo "3) Клонируйте репозиторий"
        echo "4) Создайте виртуальное окружение"
        echo "5) Установите зависимости: pip install -r requirements.txt"
        echo "6) Настройте nginx и supervisor"
        echo "7) Запустите приложение"
        echo ""
        echo "📖 Подробные инструкции в файле DEPLOYMENT_GUIDE.md"
        ;;
        
    *)
        echo "❌ Неверный выбор!"
        exit 1
        ;;
esac

echo ""
echo "🎉 Деплой завершен!"
echo "📖 Дополнительная информация в DEPLOYMENT_GUIDE.md" 