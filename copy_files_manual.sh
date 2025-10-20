#!/bin/bash

echo "📋 РУЧНОЕ КОПИРОВАНИЕ ФАЙЛОВ"
echo "============================="
echo ""

echo "🔧 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ НА УДАЛЕННОМ СЕРВЕРЕ:"
echo ""
echo "1️⃣ СОЗДАЙТЕ ФАЙЛ app.py:"
echo "   nano /home/flaskapp/app/app.py"
echo "   # Скопируйте содержимое файла app.py с локального сервера"
echo ""
echo "2️⃣ СОЗДАЙТЕ ФАЙЛ requirements.txt:"
echo "   nano /home/flaskapp/app/requirements.txt"
echo "   # Скопируйте содержимое файла requirements.txt с локального сервера"
echo ""
echo "3️⃣ СОЗДАЙТЕ ФАЙЛЫ МИГРАЦИЙ:"
echo "   nano /home/flaskapp/app/migrate_add_puzzles.py"
echo "   nano /home/flaskapp/app/migrate_surprise_payment.py"
echo "   nano /home/flaskapp/app/migrate_add_sent_jokes.py"
echo "   # Скопируйте содержимое файлов миграций"
echo ""
echo "4️⃣ УСТАНОВИТЕ ЗАВИСИМОСТИ:"
echo "   cd /home/flaskapp/app"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo ""
echo "5️⃣ СОЗДАЙТЕ ПАПКИ:"
echo "   mkdir -p uploads instance static templates"
echo "   chmod 755 uploads static templates"
echo ""
echo "6️⃣ ПРИМЕНИТЕ МИГРАЦИИ:"
echo "   python migrate_add_puzzles.py"
echo "   python migrate_surprise_payment.py"
echo "   python migrate_add_sent_jokes.py"
echo ""
echo "7️⃣ СОЗДАЙТЕ SYSTEMD КОНФИГУРАЦИЮ:"
echo "   sudo nano /etc/systemd/system/flaskapp.service"
echo ""
echo "8️⃣ ЗАПУСТИТЕ ПРИЛОЖЕНИЕ:"
echo "   sudo systemctl daemon-reload"
echo "   sudo systemctl start flaskapp"
echo "   sudo systemctl status flaskapp"
echo ""
echo "🌐 ПРОВЕРЬТЕ: https://192.168.255.137"
echo ""
echo "✅ РЕЗУЛЬТАТ:"
echo "  - Файлы скопированы вручную"
echo "  - Все исправления применены"
echo "  - Стабильная работа чата и лайков"









