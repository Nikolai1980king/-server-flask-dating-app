#!/bin/bash

# 📋 Скрипт для ручного копирования main.py на сервер и перезапуска бота

echo "📋 Ручное копирование main.py на сервер..."
echo "=========================================="

# Настройки
SERVER_USER="${BOT_SERVER_USER:-root}"
SERVER_IP="${BOT_SERVER_IP:-212.67.11.50}"
SERVER_PATH="${BOT_SERVER_PATH:-../bot.yatuta.rf/public_html}"

# Проверяем наличие файла локально
if [ ! -f "main.py" ]; then
    echo "❌ Ошибка: Файл main.py не найден в текущей директории!"
    echo "📁 Текущая директория: $(pwd)"
    echo ""
    read -p "Введите путь к файлу main.py: " main_path
    if [ ! -f "$main_path" ]; then
        echo "❌ Файл не найден: $main_path"
        exit 1
    fi
    MAIN_FILE="$main_path"
else
    MAIN_FILE="main.py"
fi

echo ""
echo "✅ Найден файл: $MAIN_FILE"
echo "📊 Размер файла: $(du -h "$MAIN_FILE" | cut -f1)"
echo "📅 Дата изменения: $(stat -c %y "$MAIN_FILE" | cut -d'.' -f1)"
echo ""

# Показываем первые строки файла для проверки
echo "📝 Первые 5 строк файла (для проверки):"
head -5 "$MAIN_FILE"
echo ""

read -p "✅ Это правильный файл? (y/n): " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "❌ Отменено"
    exit 1
fi

echo ""
echo "📋 Настройки сервера:"
echo "   👤 Пользователь: $SERVER_USER"
echo "   🌐 IP адрес: $SERVER_IP"
echo "   📁 Путь: $SERVER_PATH"
echo ""
read -p "✅ Правильно? (y/n): " confirm_server
if [ "$confirm_server" != "y" ] && [ "$confirm_server" != "Y" ]; then
    read -p "IP адрес [$SERVER_IP]: " input_ip
    SERVER_IP="${input_ip:-$SERVER_IP}"
    read -p "Пользователь [$SERVER_USER]: " input_user
    SERVER_USER="${input_user:-$SERVER_USER}"
    read -p "Путь [$SERVER_PATH]: " input_path
    SERVER_PATH="${input_path:-$SERVER_PATH}"
fi

echo ""
echo "📤 Шаг 1: Копируем файл на сервер..."
scp "$MAIN_FILE" ${SERVER_USER}@${SERVER_IP}:${SERVER_PATH}/main.py

if [ $? -ne 0 ]; then
    echo "❌ Ошибка копирования файла!"
    exit 1
fi

echo "✅ Файл скопирован!"
echo ""

# Проверяем файл на сервере
echo "📊 Шаг 2: Проверяем файл на сервере..."
ssh ${SERVER_USER}@${SERVER_IP} << EOF
    cd ${SERVER_PATH}
    echo "📁 Текущая директория: \$(pwd)"
    echo ""
    
    if [ -f "main.py" ]; then
        echo "✅ Файл main.py найден"
        echo "📊 Размер: \$(du -h main.py | cut -f1)"
        echo "📅 Дата изменения: \$(stat -c %y main.py | cut -d'.' -f1)"
        echo ""
        echo "📝 Первые 5 строк файла на сервере:"
        head -5 main.py
        echo ""
    else
        echo "❌ Файл main.py не найден на сервере!"
        exit 1
    fi
    
    # Проверяем права доступа
    echo "🔐 Права доступа:"
    ls -lh main.py
    echo ""
    
    # Проверяем текущий процесс бота
    echo "🤖 Текущие процессы бота:"
    ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py" || echo "   (процессов не найдено)"
    echo ""
EOF

echo ""
echo "🧹 Шаг 3: Очищаем кеш Python (.pyc файлы)..."
ssh ${SERVER_USER}@${SERVER_IP} << EOF
    cd ${SERVER_PATH}
    echo "Удаляем __pycache__ и .pyc файлы..."
    find . -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true
    find . -name "*.pyc" -delete 2>/dev/null || true
    echo "✅ Кеш очищен"
EOF

echo ""
echo "🔄 Шаг 4: Перезапускаем бота..."
ssh ${SERVER_USER}@${SERVER_IP} << EOF
    cd ${SERVER_PATH}
    
    # Останавливаем все процессы бота
    echo "🛑 Останавливаем процессы бота..."
    pkill -f "python.*main.py" 2>/dev/null || pkill -f "python3.*main.py" 2>/dev/null
    sleep 3
    
    # Убеждаемся, что процесс остановлен
    if ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py" > /dev/null 2>&1; then
        echo "⚠️  Процесс все еще работает, принудительно останавливаем..."
        pkill -9 -f "python.*main.py" 2>/dev/null || pkill -9 -f "python3.*main.py" 2>/dev/null
        sleep 2
    fi
    
    # Запускаем бота заново
    echo "🚀 Запускаем бота..."
    nohup python3 main.py > bot.log 2>&1 &
    sleep 3
    
    # Проверяем, что бот запустился
    if ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py" > /dev/null 2>&1; then
        echo "✅ Бот успешно запущен!"
        echo ""
        echo "📊 Информация о процессе:"
        ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py" | grep -v grep
        echo ""
        echo "📋 Последние 10 строк лога (для проверки):"
        tail -10 bot.log 2>/dev/null || echo "   (лог пока пуст)"
    else
        echo "❌ Ошибка! Бот не запустился"
        echo ""
        echo "📋 Последние 20 строк лога (для диагностики):"
        tail -20 bot.log 2>/dev/null || echo "   (лог не найден)"
        echo ""
        echo "⚠️  Проверьте ошибки выше!"
    fi
EOF

echo ""
echo "=========================================="
echo "🎉 Процесс завершен!"
echo ""
echo "📋 Для проверки выполните:"
echo "   ssh ${SERVER_USER}@${SERVER_IP}"
echo "   cd ${SERVER_PATH}"
echo "   ps aux | grep main.py           # Проверить процесс"
echo "   tail -f bot.log                 # Смотреть лог в реальном времени"
echo ""


