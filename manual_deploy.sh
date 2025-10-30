#!/bin/bash

echo "🚀 Ручной деплой на сервер"
echo "=========================="
echo ""
echo "📦 Архив готов: deploy_package.tar.gz"
echo "📁 Размер: $(du -h deploy_package.tar.gz | cut -f1)"
echo ""
echo "🔧 ИНСТРУКЦИИ ДЛЯ РУЧНОГО ДЕПЛОЯ:"
echo ""
echo "1️⃣ Подключитесь к серверу:"
echo "   ssh root@212.67.11.50"
echo ""
echo "2️⃣ Перейдите в папку приложения:"
echo "   cd /home/flaskapp/app"
echo ""
echo "3️⃣ Скачайте архив (выполните на локальной машине):"
echo "   scp /home/nikolai/PycharmProjects/flask_server/deploy_package.tar.gz root@212.67.11.50:/home/flaskapp/app/"
echo ""
echo "4️⃣ На сервере выполните:"
echo "   tar -xzf deploy_package.tar.gz"
echo "   pip install -r requirements.txt"
echo "   mkdir -p uploads instance"
echo "   chmod 755 uploads"
echo ""
echo "5️⃣ Примените миграции:"
echo "   python migrate_add_puzzles.py"
echo "   python migrate_surprise_payment.py"
echo "   python migrate_add_sent_jokes.py"
echo ""
echo "6️⃣ Перезапустите приложение:"
echo "   systemctl stop flaskapp"
echo "   systemctl start flaskapp"
echo "   systemctl status flaskapp"
echo ""
echo "✅ ИСПРАВЛЕНИЯ В ЭТОМ ДЕПЛОЕ:"
echo "  - 🔧 Исправлена проблема с циклическими лайками"
echo "  - 🔧 Исправлено дублирование сообщений в чате"
echo "  - 🔧 Исправлена ошибка в webhook ЮKassa (user_id не определен)"
echo "  - 🔧 Улучшена проверка дубликатов сообщений"
echo ""
echo "🌐 После деплоя проверьте: https://192.168.255.137"
echo ""













