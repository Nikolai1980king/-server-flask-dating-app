#!/bin/bash
echo "🚀 Копирование обновленного app.py на сервер..."
echo "📏 Расстояние регистрации: 100 метров"
scp app.py root@212.67.11.50:/home/flaskapp/app/
if [ $? -eq 0 ]; then
    echo "✅ Файл успешно скопирован!"
    echo "🔄 Теперь нужно перезапустить приложение на сервере:"
    echo "   ssh root@212.67.11.50"
    echo "   systemctl restart flaskapp"
    echo "   systemctl status flaskapp"
    echo "🎯 Теперь регистрация работает на расстоянии до 100 метров от кафе!"
else
    echo "❌ Ошибка при копировании файла"
fi 