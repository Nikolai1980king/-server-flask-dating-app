#!/bin/bash

echo "🛑 Остановка Flask сервера..."

# Остановить все процессы Python app.py
echo "🛑 Остановка процессов python app.py..."
pkill -f "python app.py" 2>/dev/null || true

# Подождать 2 секунды
sleep 2

# Принудительно освободить порт 5000
echo "🔓 Освобождение порта 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || true

# Проверить, что все остановлено
if pgrep -f "python app.py" >/dev/null; then
    echo "❌ Не удалось остановить все процессы"
else
    echo "✅ Все процессы остановлены"
fi

if lsof -i:5000 >/dev/null 2>&1; then
    echo "❌ Порт 5000 все еще занят"
else
    echo "✅ Порт 5000 свободен"
fi

echo "🏁 Готово!" 