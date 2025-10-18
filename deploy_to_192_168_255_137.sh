#!/bin/bash

# 🚀 Скрипт для развертывания на сервер 192.168.255.137

echo "🚀 Развертывание черно-белого режима на сервер 192.168.255.137..."

# Проверяем наличие архива
if [ ! -f "grayscale_deployment.tar.gz" ]; then
    echo "❌ Архив grayscale_deployment.tar.gz не найден!"
    echo "Сначала запустите: ./deploy_grayscale.sh"
    exit 1
fi

echo "📤 Копируем файлы на сервер..."

# Пробуем разные варианты подключения
echo "Попытка 1: root@192.168.255.137"
if scp grayscale_deployment.tar.gz root@192.168.255.137:/var/www/html/ 2>/dev/null; then
    echo "✅ Файлы скопированы как root"
    SERVER_USER="root"
    SERVER_PATH="/var/www/html"
elif scp grayscale_deployment.tar.gz user@192.168.255.137:/home/user/ 2>/dev/null; then
    echo "✅ Файлы скопированы как user"
    SERVER_USER="user"
    SERVER_PATH="/home/user"
elif scp grayscale_deployment.tar.gz ubuntu@192.168.255.137:/home/ubuntu/ 2>/dev/null; then
    echo "✅ Файлы скопированы как ubuntu"
    SERVER_USER="ubuntu"
    SERVER_PATH="/home/ubuntu"
else
    echo "❌ Не удалось скопировать файлы. Проверьте:"
    echo "1. Доступен ли сервер 192.168.255.137?"
    echo "2. Есть ли SSH доступ?"
    echo "3. Правильный ли пользователь?"
    echo ""
    echo "Попробуйте вручную:"
    echo "scp grayscale_deployment.tar.gz user@192.168.255.137:/path/to/project/"
    exit 1
fi

echo ""
echo "🔧 Теперь подключитесь к серверу и выполните команды:"
echo ""
echo "ssh $SERVER_USER@192.168.255.137"
echo "cd $SERVER_PATH"
echo ""
echo "# Остановите сервер"
echo "sudo systemctl stop your-flask-app"
echo "# или найдите процесс: ps aux | grep python"
echo "# и остановите: kill -9 <PID>"
echo ""
echo "# Создайте резервную копию"
echo "cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db"
echo ""
echo "# Распакуйте архив"
echo "tar -xzf grayscale_deployment.tar.gz"
echo ""
echo "# Запустите миграцию"
echo "python migrate_add_grayscale_mode.py"
echo ""
echo "# Запустите сервер"
echo "python app.py"
echo "# или"
echo "sudo systemctl start your-flask-app"
echo ""
echo "🧪 После этого протестируйте:"
echo "1. Откройте https://192.168.255.137"
echo "2. Войдите в систему"
echo "3. Перейдите в настройки (⚙️)"
echo "4. Найдите кнопку черно-белого режима (⚫)"
echo "5. Переключите режим и проверьте работу"
echo ""
echo "✅ Развертывание готово!"

