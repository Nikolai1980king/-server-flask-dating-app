#!/bin/bash
echo "🔍 Проверяем состояние сервера..."

echo "📁 Проверяем файл на сервере:"
ssh root@212.67.11.50 "ls -la /home/flaskapp/app/app.py"

echo ""
echo "📏 Проверяем MAX_REGISTRATION_DISTANCE:"
ssh root@212.67.11.50 "grep -n 'MAX_REGISTRATION_DISTANCE' /home/flaskapp/app/app.py"

echo ""
echo "🔧 Проверяем статус сервиса:"
ssh root@212.67.11.50 "systemctl status flaskapp"

echo ""
echo "📋 Проверяем логи:"
ssh root@212.67.11.50 "journalctl -u flaskapp --no-pager -n 10" 