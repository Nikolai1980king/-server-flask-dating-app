#!/bin/bash

echo "🔍 Диагностика конфигурации Socket.IO на сервере"
echo "================================================"
echo ""

echo "📋 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ НА СЕРВЕРЕ:"
echo ""
echo "1️⃣ Проверьте systemd конфигурацию:"
echo "   cat /etc/systemd/system/flaskapp.service"
echo ""
echo "2️⃣ Проверьте, как запускается приложение:"
echo "   ps aux | grep python"
echo ""
echo "3️⃣ Проверьте логи:"
echo "   journalctl -u flaskapp -n 20"
echo ""
echo "4️⃣ Проверьте порты:"
echo "   netstat -tlnp | grep 5000"
echo ""
echo "5️⃣ Проверьте nginx конфигурацию:"
echo "   cat /etc/nginx/sites-available/flaskapp"
echo ""

echo "🔧 ВОЗМОЖНЫЕ ПРОБЛЕМЫ:"
echo "  ❌ Приложение запускается через gunicorn вместо socketio.run()"
echo "  ❌ Nginx не проксирует Socket.IO запросы"
echo "  ❌ Неправильная конфигурация CORS"
echo "  ❌ Проблемы с WebSocket поддержкой"
echo ""

echo "✅ РЕШЕНИЯ:"
echo "  1. Исправить systemd конфигурацию"
echo "  2. Настроить nginx для Socket.IO"
echo "  3. Добавить поддержку WebSocket"
echo "  4. Использовать fallback на AJAX"









