#!/bin/bash

echo "🚀 ПОЛНАЯ ПЕРЕУСТАНОВКА ПРОЕКТА НА СЕРВЕРЕ"
echo "=========================================="
echo ""

echo "📋 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ НА СЕРВЕРЕ:"
echo ""
echo "1️⃣ Остановите приложение:"
echo "   systemctl stop flaskapp"
echo ""
echo "2️⃣ Удалите старый проект:"
echo "   rm -rf /home/flaskapp/app/*"
echo "   rm -rf /home/flaskapp/app/.* 2>/dev/null || true"
echo ""
echo "3️⃣ Скачайте новый архив:"
echo "   cd /home/flaskapp/app"
echo "   wget http://192.168.0.24:8080/deploy_package.tar.gz"
echo ""
echo "4️⃣ Распакуйте архив:"
echo "   tar -xzf deploy_package.tar.gz"
echo ""
echo "5️⃣ Установите зависимости:"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "6️⃣ Создайте папки:"
echo "   mkdir -p uploads instance static templates"
echo "   chmod 755 uploads"
echo ""
echo "7️⃣ Примените миграции:"
echo "   python migrate_add_puzzles.py"
echo "   python migrate_surprise_payment.py"
echo "   python migrate_add_sent_jokes.py"
echo ""
echo "8️⃣ Создайте правильную systemd конфигурацию:"
echo "   sudo nano /etc/systemd/system/flaskapp.service"
echo ""
echo "9️⃣ Содержимое systemd файла:"
echo "   [Unit]"
echo "   Description=Flask Dating App"
echo "   After=network.target"
echo ""
echo "   [Service]"
echo "   Type=simple"
echo "   User=flaskapp"
echo "   WorkingDirectory=/home/flaskapp/app"
echo "   Environment=PATH=/home/flaskapp/app/venv/bin"
echo "   ExecStart=/home/flaskapp/app/venv/bin/python app.py"
echo "   Restart=always"
echo "   RestartSec=3"
echo ""
echo "   [Install]"
echo "   WantedBy=multi-user.target"
echo ""
echo "🔟 Примените изменения:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl start flaskapp"
echo "   sudo systemctl status flaskapp"
echo ""
echo "🌐 Проверьте: https://192.168.255.137"
echo ""
echo "✅ РЕЗУЛЬТАТ:"
echo "  - Чистая установка без старых проблем"
echo "  - Правильная конфигурация Socket.IO"
echo "  - Исправленные лайки и сообщения"
echo "  - Стабильная работа чата"













