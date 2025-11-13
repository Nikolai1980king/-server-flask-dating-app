#!/bin/bash

# 🔍 Скрипт для проверки состояния бота на сервере

echo "🔍 Проверка состояния телеграм-бота на сервере..."
echo "=================================================="

SERVER_USER="${BOT_SERVER_USER:-root}"
SERVER_IP="${BOT_SERVER_IP:-212.67.11.50}"
SERVER_PATH="${BOT_SERVER_PATH:-../bot.yatuta.rf/public_html}"

echo ""
echo "📋 Подключение к серверу..."
echo "   👤 Пользователь: $SERVER_USER"
echo "   🌐 IP адрес: $SERVER_IP"
echo "   📁 Путь: $SERVER_PATH"
echo ""

ssh ${SERVER_USER}@${SERVER_IP} << EOF
    cd ${SERVER_PATH} 2>/dev/null || { echo "❌ Не удалось перейти в ${SERVER_PATH}"; exit 1; }
    
    echo "📁 Текущая директория: \$(pwd)"
    echo ""
    
    echo "📄 Файлы main.py в этой директории:"
    find . -maxdepth 2 -name "main.py" -type f -exec ls -lh {} \; 2>/dev/null || echo "   main.py не найден"
    echo ""
    
    if [ -f "main.py" ]; then
        echo "✅ Файл main.py найден в текущей директории"
        echo "📊 Информация о файле:"
        ls -lh main.py
        echo ""
        echo "📅 Дата изменения: \$(stat -c %y main.py)"
        echo ""
        echo "📝 Первые 10 строк файла:"
        head -10 main.py
        echo ""
        echo "📏 Последние 5 строк файла:"
        tail -5 main.py
        echo ""
    else
        echo "❌ Файл main.py НЕ найден в ${SERVER_PATH}"
        echo ""
        echo "📁 Содержимое директории:"
        ls -lah
        echo ""
    fi
    
    echo "🤖 Процессы бота:"
    BOT_PROCESSES=\$(ps aux | grep -E "[p]ython.*main.py|[p]ython3.*main.py")
    if [ -z "\$BOT_PROCESSES" ]; then
        echo "   ❌ Процессы бота не найдены!"
    else
        echo "   ✅ Найдены процессы:"
        echo "\$BOT_PROCESSES"
        echo ""
        # Показываем рабочую директорию процесса
        BOT_PID=\$(echo "\$BOT_PROCESSES" | awk '{print \$2}' | head -1)
        if [ ! -z "\$BOT_PID" ]; then
            echo "   📁 Рабочая директория процесса (PID \$BOT_PID):"
            pwdx \$BOT_PID 2>/dev/null || ls -l /proc/\$BOT_PID/cwd 2>/dev/null || echo "   (не удалось определить)"
            echo ""
            echo "   📄 Команда запуска:"
            cat /proc/\$BOT_PID/cmdline 2>/dev/null | tr '\0' ' ' || echo "   (не удалось определить)"
            echo ""
        fi
    fi
    
    echo "📋 Логи бота:"
    if [ -f "bot.log" ]; then
        echo "   ✅ Файл bot.log найден"
        echo "   📊 Размер: \$(du -h bot.log | cut -f1)"
        echo ""
        echo "   📝 Последние 15 строк лога:"
        tail -15 bot.log
    else
        echo "   ⚠️  Файл bot.log не найден"
        # Ищем другие логи
        find . -maxdepth 1 -name "*.log" -type f | head -5
    fi
    echo ""
    
    echo "🔐 Права доступа на файлы:"
    ls -lh main.py bot.log 2>/dev/null || echo "   (некоторые файлы отсутствуют)"
    echo ""
    
    echo "🐍 Версия Python:"
    python3 --version 2>/dev/null || python --version 2>/dev/null || echo "   Python не найден"
    echo ""
    
    echo "📦 Установленные пакеты Python (для бота):"
    pip3 list 2>/dev/null | grep -i "telegram\|bot\|aiogram\|pyTelegramBotAPI" || echo "   (пакеты не найдены или pip3 не доступен)"
    echo ""
    
    echo "🗂️  Кеш Python (.pyc файлы):"
    PYCFILES=\$(find . -name "*.pyc" | wc -l)
    echo "   Найдено .pyc файлов: \$PYCFILES"
    if [ \$PYCFILES -gt 0 ]; then
        echo "   ⚠️  Рекомендуется очистить кеш!"
        echo "   Команда: find . -name '*.pyc' -delete && find . -type d -name '__pycache__' -exec rm -r {} +"
    fi
EOF

echo ""
echo "=========================================="
echo "✅ Проверка завершена!"
echo ""


