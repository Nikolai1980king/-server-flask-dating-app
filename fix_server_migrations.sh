#!/bin/bash

echo "🔧 ИСПРАВЛЕНИЕ МИГРАЦИЙ НА СЕРВЕРЕ"
echo "===================================="
echo ""
echo "Проблема: sqlalchemy.exc.OperationalError"
echo "          столбец profile.surprise_feature_paid не существует"
echo ""
echo "Решение: Скопируем и применим миграции"
echo ""
echo "🔑 ПОТРЕБУЕТСЯ ВВЕСТИ ПАРОЛЬ ROOT 2 РАЗА"
echo ""
read -p "Нажмите Enter для продолжения..."

# ШАГ 1: Копирование миграций
echo ""
echo "📤 ШАГ 1/2: Копируем миграции на сервер..."
echo "==========================================="

scp migrate_surprise_payment.py root@212.67.11.50:/home/flaskapp/app/
scp migrate_add_sent_jokes.py root@212.67.11.50:/home/flaskapp/app/
scp migrate_add_puzzles.py root@212.67.11.50:/home/flaskapp/app/

if [ $? -ne 0 ]; then
    echo "❌ Ошибка копирования миграций"
    exit 1
fi

echo "✅ Миграции скопированы"

# ШАГ 2: Применение миграций
echo ""
echo "🔄 ШАГ 2/2: Применяем миграции на сервере..."
echo "============================================="

ssh root@212.67.11.50 << 'ENDSSH'
    cd /home/flaskapp/app
    
    echo ""
    echo "📊 Текущее состояние БД:"
    echo "------------------------"
    sqlite3 instance/dating_app.db ".tables"
    
    echo ""
    echo "🔄 Применяем миграции..."
    echo ""
    
    echo "1️⃣ migrate_surprise_payment.py (добавляет surprise_feature_paid)..."
    python migrate_surprise_payment.py
    
    echo ""
    echo "2️⃣ migrate_add_sent_jokes.py (добавляет sent_joke)..."
    python migrate_add_sent_jokes.py
    
    echo ""
    echo "3️⃣ migrate_add_puzzles.py (добавляет sent_puzzle)..."
    python migrate_add_puzzles.py
    
    echo ""
    echo "📊 Проверяем результат:"
    echo "-----------------------"
    sqlite3 instance/dating_app.db << 'SQL'
-- Показываем все таблицы
.tables

-- Проверяем структуру profile
SELECT sql FROM sqlite_master WHERE type='table' AND name='profile';

-- Проверяем наличие новых таблиц
SELECT name FROM sqlite_master WHERE type='table' AND name IN ('sent_joke', 'sent_puzzle', 'chat_permission');
SQL
    
    echo ""
    echo "🔄 Останавливаем приложение..."
    systemctl stop flaskapp
    
    echo "🚀 Запускаем приложение..."
    systemctl start flaskapp
    
    sleep 2
    
    echo ""
    echo "📋 Статус приложения:"
    systemctl status flaskapp --no-pager -l | head -20
    
    echo ""
    echo "📋 Последние логи:"
    journalctl -u flaskapp -n 10 --no-pager
ENDSSH

echo ""
echo "=========================================="
echo "🎉 ГОТОВО!"
echo "=========================================="
echo ""
echo "✅ Миграции применены"
echo "✅ Приложение перезапущено"
echo ""
echo "🌐 Проверьте работу:"
echo "   https://192.168.255.137"
echo ""
echo "📊 Что изменилось в БД:"
echo "   + profile.surprise_feature_paid"
echo "   + profile.surprise_feature_payment_date"
echo "   + таблица chat_permission"
echo "   + таблица sent_joke"
echo "   + таблица sent_puzzle"
echo ""

















