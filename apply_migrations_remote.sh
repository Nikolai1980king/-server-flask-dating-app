#!/bin/bash

echo "🔧 Применение миграций на удаленном сервере"
echo "============================================"
echo ""
echo "🔑 ПОТРЕБУЕТСЯ ВВЕСТИ ПАРОЛЬ ROOT"
echo ""

ssh root@212.67.11.50 << 'ENDSSH'
    echo "📂 Переходим в папку приложения..."
    cd /home/flaskapp/app
    
    echo "🔍 Проверяем текущую структуру БД..."
    sqlite3 instance/dating_app.db ".schema profile" | grep surprise_feature
    
    if [ $? -ne 0 ]; then
        echo "⚠️ Столбцы surprise_feature не найдены, применяем миграцию..."
        
        echo "🔄 Применяем migrate_surprise_payment.py..."
        python migrate_surprise_payment.py
        
        echo "🔄 Применяем migrate_add_sent_jokes.py..."
        python migrate_add_sent_jokes.py
        
        echo "🔄 Применяем migrate_add_puzzles.py..."
        python migrate_add_puzzles.py
        
        echo ""
        echo "✅ Миграции применены!"
        echo ""
        
        echo "📊 Проверяем результат..."
        sqlite3 instance/dating_app.db << 'SQL'
.tables
.schema profile
.schema sent_joke
.schema sent_puzzle
.schema chat_permission
SQL
        
        echo ""
        echo "🔄 Перезапускаем приложение..."
        systemctl restart flaskapp
        
        echo "📋 Проверяем статус..."
        systemctl status flaskapp --no-pager -l
    else
        echo "✅ Миграции уже применены"
    fi
    
    echo ""
    echo "🎉 Готово!"
ENDSSH

echo ""
echo "✅ Миграции применены на сервере"
echo "🌐 Проверьте: https://192.168.255.137"

















