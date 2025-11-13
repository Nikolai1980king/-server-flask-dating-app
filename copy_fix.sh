#!/bin/bash

echo "🔧 Копирование исправлений Socket.IO на сервер"
echo "=============================================="
echo ""

# Проверяем, что файл существует
if [ ! -f "app.py" ]; then
    echo "❌ Файл app.py не найден!"
    exit 1
fi

echo "📋 ИСПРАВЛЕНИЯ В ФАЙЛЕ app.py:"
echo "  ✅ Улучшена конфигурация Socket.IO"
echo "  ✅ Исправлена инициализация Socket.IO в JavaScript"
echo "  ✅ Добавлен fallback на AJAX"
echo "  ✅ Улучшена обработка ошибок"
echo ""

echo "📤 КОМАНДЫ ДЛЯ КОПИРОВАНИЯ:"
echo ""
echo "1️⃣ Скопируйте файл на сервер:"
echo "   scp app.py root@212.67.11.50:/home/flaskapp/app/"
echo ""
echo "2️⃣ Подключитесь к серверу:"
echo "   ssh root@212.67.11.50"
echo ""
echo "3️⃣ Перезапустите приложение:"
echo "   cd /home/flaskapp/app"
echo "   systemctl restart flaskapp"
echo "   systemctl status flaskapp"
echo ""
echo "4️⃣ Проверьте логи:"
echo "   journalctl -u flaskapp -f"
echo ""
echo "🌐 После применения проверьте: https://192.168.255.137"
echo ""

# Показываем размер файла
SIZE=$(du -h app.py | cut -f1)
echo "📦 Размер файла: $SIZE"
echo "📄 Файл: app.py"
echo ""
echo "🚀 Готово к копированию!"
















