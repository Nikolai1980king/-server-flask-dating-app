#!/bin/bash

# 🚀 Скрипт для копирования файлов на сервер 212.67.11.50

echo "🚀 Копирование файлов на сервер 212.67.11.50..."

# Проверяем наличие файлов
REQUIRED_FILES=("app.py" "dating_app.db" "migrate_add_grayscale_mode.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Ошибка: Файл $file не найден!"
        exit 1
    fi
done

echo "✅ Все необходимые файлы найдены"

echo ""
echo "📤 Копируем файлы на сервер 212.67.11.50..."

# Копируем файлы
echo "Копируем app.py..."
scp app.py root@212.67.11.50:/var/www/html/
echo "✅ app.py скопирован"

echo "Копируем dating_app.db..."
scp dating_app.db root@212.67.11.50:/var/www/html/
echo "✅ dating_app.db скопирован"

echo "Копируем migrate_add_grayscale_mode.py..."
scp migrate_add_grayscale_mode.py root@212.67.11.50:/var/www/html/
echo "✅ migrate_add_grayscale_mode.py скопирован"

echo ""
echo "🔧 Теперь подключитесь к серверу и выполните команды:"
echo ""
echo "ssh root@212.67.11.50"
echo "cd /var/www/html/"
echo ""
echo "# Остановите текущий сервер"
echo "sudo systemctl stop your-flask-app"
echo "# или найдите процесс: ps aux | grep python"
echo "# и остановите: kill -9 <PID>"
echo ""
echo "# Создайте резервную копию базы данных"
echo "cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db"
echo ""
echo "# Запустите миграцию (добавит поле grayscale_mode)"
echo "python migrate_add_grayscale_mode.py"
echo ""
echo "# Запустите сервер"
echo "python app.py"
echo "# или"
echo "sudo systemctl start your-flask-app"
echo ""
echo "🧪 После этого протестируйте:"
echo "1. Откройте https://212.67.11.50"
echo "2. Войдите в систему"
echo "3. Перейдите в настройки (⚙️)"
echo "4. Найдите кнопку черно-белого режима (⚫)"
echo "5. Переключите режим и проверьте работу"
echo ""
echo "✅ Развертывание готово!"

