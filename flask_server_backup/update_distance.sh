#!/bin/bash

echo "🚀 Обновление расстояния регистрации..."
echo "📏 Старое расстояние: 100 метров"
echo "📏 Новое расстояние: 1000 метров (1 км)"
echo ""

echo "📁 Копирование обновленного app.py на сервер..."
scp app.py root@212.67.11.50:/home/flaskapp/app/

if [ $? -eq 0 ]; then
    echo "✅ Файл успешно скопирован!"
    echo ""
    echo "🔄 Теперь нужно перезапустить приложение на сервере:"
    echo "   ssh root@212.67.11.50"
    echo "   systemctl restart flaskapp"
    echo "   systemctl status flaskapp"
    echo ""
    echo "🎯 Теперь вы сможете регистрироваться на расстоянии до 1 км от кафе!"
else
    echo "❌ Ошибка при копировании файла"
fi 