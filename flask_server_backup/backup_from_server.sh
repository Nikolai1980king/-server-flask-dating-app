#!/bin/bash

# Скрипт для создания бэкапа с сервера
# Использование: ./backup_from_server.sh

SERVER_IP="212.67.11.50"
SERVER_USER="root"
APP_DIR="/home/flaskapp/app"
BACKUP_DIR="./server_backup_$(date +%Y%m%d_%H%M%S)"

echo "🔄 Создание бэкапа с сервера..."
echo "Сервер: $SERVER_IP"
echo "Папка приложения: $APP_DIR"
echo "Бэкап будет сохранен в: $BACKUP_DIR"
echo ""

# Создаем папку для бэкапа
mkdir -p "$BACKUP_DIR"
if [ $? -ne 0 ]; then
    echo "❌ Не удалось создать папку для бэкапа"
    exit 1
fi

echo "📁 Создана папка: $BACKUP_DIR"

# Копируем основные файлы приложения
echo ""
echo "📤 Копируем файлы приложения..."

# Основные файлы
scp -r $SERVER_USER@$SERVER_IP:$APP_DIR/app.py "$BACKUP_DIR/"
scp -r $SERVER_USER@$SERVER_IP:$APP_DIR/requirements.txt "$BACKUP_DIR/" 2>/dev/null
scp -r $SERVER_USER@$SERVER_IP:$APP_DIR/.env "$BACKUP_DIR/" 2>/dev/null

# Статические файлы
echo "📁 Копируем статические файлы..."
scp -r $SERVER_USER@$SERVER_IP:$APP_DIR/static "$BACKUP_DIR/" 2>/dev/null

# База данных
echo "🗄️ Копируем базу данных..."
scp -r $SERVER_USER@$SERVER_IP:$APP_DIR/instance "$BACKUP_DIR/" 2>/dev/null

# Загруженные файлы
echo "📸 Копируем загруженные файлы..."
scp -r $SERVER_USER@$SERVER_IP:$APP_DIR/static/uploads "$BACKUP_DIR/" 2>/dev/null

# Конфигурационные файлы сервера
echo "⚙️ Копируем конфигурационные файлы..."
scp $SERVER_USER@$SERVER_IP:/etc/systemd/system/flaskapp.service "$BACKUP_DIR/" 2>/dev/null
scp $SERVER_USER@$SERVER_IP:/etc/nginx/sites-available/flaskapp "$BACKUP_DIR/" 2>/dev/null

# Получаем информацию о системе
echo "💻 Получаем информацию о системе..."
ssh $SERVER_USER@$SERVER_IP "uname -a && df -h && free -h" > "$BACKUP_DIR/system_info.txt" 2>/dev/null

# Получаем логи приложения
echo "📋 Копируем логи приложения..."
ssh $SERVER_USER@$SERVER_IP "journalctl -u flaskapp --no-pager -n 100" > "$BACKUP_DIR/app_logs.txt" 2>/dev/null

# Создаем файл с информацией о бэкапе
cat > "$BACKUP_DIR/backup_info.txt" << EOF
Бэкап создан: $(date)
Сервер: $SERVER_IP
Папка приложения: $APP_DIR
Пользователь: $SERVER_USER

Содержимое бэкапа:
- app.py - основной файл приложения
- requirements.txt - зависимости Python
- .env - переменные окружения (если есть)
- static/ - статические файлы
- instance/ - база данных SQLite
- static/uploads/ - загруженные файлы
- flaskapp.service - конфигурация systemd
- flaskapp (nginx) - конфигурация nginx
- system_info.txt - информация о системе
- app_logs.txt - логи приложения

Для восстановления:
1. Скопируйте файлы обратно на сервер
2. Перезапустите сервисы: systemctl restart flaskapp nginx
3. Проверьте статус: systemctl status flaskapp nginx
EOF

echo ""
echo "✅ Бэкап успешно создан!"
echo "📁 Папка бэкапа: $BACKUP_DIR"
echo ""

# Показываем содержимое бэкапа
echo "📋 Содержимое бэкапа:"
ls -la "$BACKUP_DIR"

echo ""
echo "📊 Размер бэкапа:"
du -sh "$BACKUP_DIR"

echo ""
echo "🔍 Информация о бэкапе сохранена в: $BACKUP_DIR/backup_info.txt"
echo "📋 Логи приложения в: $BACKUP_DIR/app_logs.txt"
echo "💻 Информация о системе в: $BACKUP_DIR/system_info.txt"

echo ""
echo "🎯 Бэкап готов! Все файлы сохранены локально." 