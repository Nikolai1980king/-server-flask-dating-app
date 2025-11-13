#!/bin/bash

echo "📤 Копирование миграций на сервер"
echo "=================================="
echo ""
echo "🔑 ПОТРЕБУЕТСЯ ВВЕСТИ ПАРОЛЬ ROOT"
echo ""

# Копируем все файлы миграций
echo "📋 Копируем migrate_surprise_payment.py..."
scp migrate_surprise_payment.py root@212.67.11.50:/home/flaskapp/app/

echo "📋 Копируем migrate_add_sent_jokes.py..."
scp migrate_add_sent_jokes.py root@212.67.11.50:/home/flaskapp/app/

echo "📋 Копируем migrate_add_puzzles.py..."
scp migrate_add_puzzles.py root@212.67.11.50:/home/flaskapp/app/

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Все миграции скопированы!"
    echo ""
    echo "🚀 Теперь запустите:"
    echo "   ./apply_migrations_remote.sh"
else
    echo ""
    echo "❌ Ошибка копирования"
    exit 1
fi




















