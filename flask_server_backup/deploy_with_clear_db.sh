#!/bin/bash
echo "🚀 Копирование файлов на сервер и очистка базы данных..."
echo "=" * 50

# Копируем основной файл приложения
echo "📁 Копируем app.py..."
scp app.py root@212.67.11.50:/home/flaskapp/app/

# Копируем скрипт очистки базы данных
echo "📁 Копируем скрипт очистки..."
scp clear_all_profiles.py root@212.67.11.50:/home/flaskapp/app/

if [ $? -eq 0 ]; then
    echo "✅ Файлы успешно скопированы!"
    echo ""
    echo "🔄 Подключаемся к серверу для очистки и перезапуска..."
    echo ""
    
    # Подключаемся к серверу и выполняем команды
    ssh root@212.67.11.50 << 'EOF'
        echo "🔧 Остановка приложения..."
        systemctl stop flaskapp
        
        echo "🗑️ Очистка базы данных..."
        cd /home/flaskapp/app
        python3 clear_all_profiles.py <<< "YES"
        
        echo "🔄 Запуск приложения..."
        systemctl start flaskapp
        
        echo "📊 Проверка статуса..."
        systemctl status flaskapp
        
        echo "✅ Готово! Сервер перезапущен с чистой базой данных"
EOF

else
    echo "❌ Ошибка при копировании файлов"
fi 