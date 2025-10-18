#!/bin/bash

# 🚀 Скрипт для развертывания черно-белого режима на удаленном сервере

echo "🚀 Начинаем развертывание черно-белого режима..."

# Проверяем наличие необходимых файлов
echo "📋 Проверяем наличие файлов..."

if [ ! -f "app.py" ]; then
    echo "❌ Файл app.py не найден!"
    exit 1
fi

if [ ! -f "dating_app.db" ]; then
    echo "❌ Файл dating_app.db не найден!"
    exit 1
fi

if [ ! -f "migrate_add_grayscale_mode.py" ]; then
    echo "❌ Файл migrate_add_grayscale_mode.py не найден!"
    exit 1
fi

echo "✅ Все необходимые файлы найдены"

# Создаем резервную копию
echo "💾 Создаем резервную копию..."
BACKUP_NAME="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p backups
cp dating_app.db "backups/dating_app_${BACKUP_NAME}.db"
echo "✅ Резервная копия создана: backups/dating_app_${BACKUP_NAME}.db"

# Создаем архив для развертывания
echo "📦 Создаем архив для развертывания..."
tar -czf grayscale_deployment.tar.gz app.py dating_app.db migrate_add_grayscale_mode.py
echo "✅ Архив создан: grayscale_deployment.tar.gz"

# Инструкции для развертывания
echo ""
echo "🎯 Следующие шаги для развертывания на удаленном сервере:"
echo ""
echo "1. 📤 Скопируйте файлы на сервер:"
echo "   scp grayscale_deployment.tar.gz user@remote-server:/path/to/project/"
echo ""
echo "2. 🔧 На удаленном сервере выполните:"
echo "   # Остановите сервер"
echo "   sudo systemctl stop your-flask-app"
echo "   # Или: kill -9 \$(ps aux | grep python | grep app.py | awk '{print \$2}')"
echo ""
echo "3. 💾 Создайте резервную копию на сервере:"
echo "   cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db"
echo ""
echo "4. 📦 Распакуйте архив:"
echo "   tar -xzf grayscale_deployment.tar.gz"
echo ""
echo "5. 🔄 Запустите миграцию (если нужно):"
echo "   python migrate_add_grayscale_mode.py"
echo ""
echo "6. 🚀 Запустите сервер:"
echo "   python app.py"
echo "   # Или: sudo systemctl start your-flask-app"
echo ""
echo "7. 🧪 Протестируйте:"
echo "   - Откройте браузер"
echo "   - Войдите в систему"
echo "   - Перейдите в настройки"
echo "   - Найдите кнопку черно-белого режима (⚫)"
echo "   - Переключите режим и проверьте работу"
echo ""
echo "✅ Развертывание готово!"
echo "📋 Подробные инструкции в файле DEPLOYMENT_GUIDE.md"

