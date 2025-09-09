#!/bin/bash

echo "🚀 Универсальный скрипт развертывания с системой IP-контроля"

# Определяем, запускаем ли мы на сервере или локально
if [ "$EUID" -eq 0 ]; then
    echo "❌ Не запускайте скрипт от root пользователя"
    exit 1
fi

# Проверяем, есть ли systemctl (признак сервера)
if command -v systemctl &> /dev/null; then
    IS_SERVER=true
    echo "🖥️ Обнаружен сервер (systemctl доступен)"
else
    IS_SERVER=false
    echo "💻 Локальный запуск"
fi

# Останавливаем старое приложение
echo "🛑 Останавливаем старое приложение..."
if [ "$IS_SERVER" = true ]; then
    sudo systemctl stop dating-app 2>/dev/null || true
fi
pkill -f "python.*app.py" 2>/dev/null || true

# Обновляем код (если используем git)
if [ -d ".git" ]; then
    echo "📥 Обновляем код из git..."
    git pull origin main
fi

# Устанавливаем зависимости
echo "📦 Устанавливаем зависимости..."
pip install -r requirements.txt

# Инициализируем базу данных с новой таблицей IP-контроля
echo "🗄️ Инициализируем базу данных..."
python init_db_simple.py

if [ "$IS_SERVER" = true ]; then
    # Серверный режим - создаем systemd сервис
    echo "⚙️ Создаем systemd сервис..."
    sudo tee /etc/systemd/system/dating-app.service > /dev/null <<EOF
[Unit]
Description=Dating App with IP Control
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
ExecStart=$(which python3) $(pwd)/run_production.py
Restart=always
RestartSec=10
Environment=PORT=80
Environment=HOST=0.0.0.0

[Install]
WantedBy=multi-user.target
EOF

    # Перезагружаем systemd и запускаем сервис
    echo "🔄 Перезагружаем systemd..."
    sudo systemctl daemon-reload

    echo "✅ Включаем автозапуск..."
    sudo systemctl enable dating-app

    echo "🚀 Запускаем приложение..."
    sudo systemctl start dating-app

    # Проверяем статус
    echo "📊 Проверяем статус..."
    sleep 3
    sudo systemctl status dating-app --no-pager -l

    echo "🌐 Приложение должно быть доступно на порту 80"
    echo "📱 Домен: ятута.рф"
    echo "🔒 Система IP-контроля активна: один IP = одна анкета"
    echo ""
    echo "📋 Полезные команды:"
    echo "  sudo systemctl status dating-app    - статус приложения"
    echo "  sudo systemctl restart dating-app   - перезапуск"
    echo "  sudo journalctl -u dating-app -f   - логи в реальном времени"
    echo "  sudo systemctl stop dating-app      - остановка"
    echo ""
    echo "🧪 Тестирование IP-контроля:"
    echo "  http://ятута.рф/test_ip_control.html"
    echo ""
    echo "📊 Мониторинг IP-контроля:"
    echo "  http://ятута.рф/check_ip_control"

else
    # Локальный режим - запускаем напрямую
    echo "🚀 Запускаем приложение локально..."
    echo "🔒 Система IP-контроля активна: один IP = одна анкета"
    echo ""
    echo "🌐 Приложение будет доступно на:"
    echo "  http://localhost:5000"
    echo "  http://127.0.0.1:5000"
    echo ""
    echo "🧪 Тестирование IP-контроля:"
    echo "  http://localhost:5000/test_ip_control.html"
    echo ""
    echo "📊 Мониторинг IP-контроля:"
    echo "  http://localhost:5000/check_ip_control"
    echo ""
    echo "⏹️ Для остановки нажмите Ctrl+C"
    echo ""
    
    # Запускаем приложение
    python run_production.py
fi