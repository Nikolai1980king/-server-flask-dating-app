#!/bin/bash

# 🚀 Скрипт для копирования файлов на сервер 192.168.255.137

echo "🚀 Копирование файлов на сервер 192.168.255.137..."

# Проверяем наличие файлов
REQUIRED_FILES=("app.py" "dating_app.db" "migrate_add_grayscale_mode.py")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        echo "❌ Ошибка: Файл $file не найден!"
        exit 1
    fi
done

echo "✅ Все необходимые файлы найдены"

# Пробуем разные варианты подключения
echo ""
echo "📤 Копируем файлы на сервер..."

# Вариант 1: root пользователь
echo "Попытка 1: root@192.168.255.137"
if scp app.py root@192.168.255.137:/var/www/html/ 2>/dev/null; then
    echo "✅ app.py скопирован как root"
    scp dating_app.db root@192.168.255.137:/var/www/html/
    echo "✅ dating_app.db скопирован как root"
    scp migrate_add_grayscale_mode.py root@192.168.255.137:/var/www/html/
    echo "✅ migrate_add_grayscale_mode.py скопирован как root"
    echo ""
    echo "🔧 Теперь подключитесь к серверу:"
    echo "ssh root@192.168.255.137"
    echo "cd /var/www/html/"
    echo "sudo systemctl stop your-flask-app"
    echo "cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db"
    echo "python migrate_add_grayscale_mode.py"
    echo "python app.py"
    exit 0
fi

# Вариант 2: user пользователь
echo "Попытка 2: user@192.168.255.137"
if scp app.py user@192.168.255.137:/home/user/ 2>/dev/null; then
    echo "✅ app.py скопирован как user"
    scp dating_app.db user@192.168.255.137:/home/user/
    echo "✅ dating_app.db скопирован как user"
    scp migrate_add_grayscale_mode.py user@192.168.255.137:/home/user/
    echo "✅ migrate_add_grayscale_mode.py скопирован как user"
    echo ""
    echo "🔧 Теперь подключитесь к серверу:"
    echo "ssh user@192.168.255.137"
    echo "cd /home/user/"
    echo "sudo systemctl stop your-flask-app"
    echo "cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db"
    echo "python migrate_add_grayscale_mode.py"
    echo "python app.py"
    exit 0
fi

# Вариант 3: ubuntu пользователь
echo "Попытка 3: ubuntu@192.168.255.137"
if scp app.py ubuntu@192.168.255.137:/home/ubuntu/ 2>/dev/null; then
    echo "✅ app.py скопирован как ubuntu"
    scp dating_app.db ubuntu@192.168.255.137:/home/ubuntu/
    echo "✅ dating_app.db скопирован как ubuntu"
    scp migrate_add_grayscale_mode.py ubuntu@192.168.255.137:/home/ubuntu/
    echo "✅ migrate_add_grayscale_mode.py скопирован как ubuntu"
    echo ""
    echo "🔧 Теперь подключитесь к серверу:"
    echo "ssh ubuntu@192.168.255.137"
    echo "cd /home/ubuntu/"
    echo "sudo systemctl stop your-flask-app"
    echo "cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db"
    echo "python migrate_add_grayscale_mode.py"
    echo "python app.py"
    exit 0
fi

echo "❌ Не удалось скопировать файлы автоматически"
echo ""
echo "🔧 Попробуйте вручную:"
echo "scp app.py user@192.168.255.137:/path/to/project/"
echo "scp dating_app.db user@192.168.255.137:/path/to/project/"
echo "scp migrate_add_grayscale_mode.py user@192.168.255.137:/path/to/project/"
echo ""
echo "📋 Затем на сервере выполните:"
echo "ssh user@192.168.255.137"
echo "cd /path/to/project/"
echo "sudo systemctl stop your-flask-app"
echo "cp dating_app.db dating_app_backup_\$(date +%Y%m%d_%H%M%S).db"
echo "python migrate_add_grayscale_mode.py"
echo "python app.py"