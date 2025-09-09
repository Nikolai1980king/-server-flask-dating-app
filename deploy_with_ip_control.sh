#!/bin/bash

echo "🚀 Скрипт развертывания приложения с системой IP-контроля"

# Проверяем, что мы на сервере
if [ "$EUID" -eq 0 ]; then
    echo "❌ Не запускайте скрипт от root пользователя"
    exit 1
fi

# Останавливаем старое приложение
echo "🛑 Останавливаем старое приложение..."
sudo systemctl stop dating-app 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true

# Обновляем код (если используете git)
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

# Создаем systemd сервис
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