#!/bin/bash
echo "🔍 Простая проверка сервера..."

# Проверяем, что файл существует на сервере
echo "📁 Проверяем файл app.py на сервере:"
ssh root@212.67.11.50 "ls -la /home/flaskapp/app/app.py"

echo ""
echo "📏 Проверяем значение MAX_REGISTRATION_DISTANCE:"
ssh root@212.67.11.50 "grep 'MAX_REGISTRATION_DISTANCE' /home/flaskapp/app/app.py"

echo ""
echo "🔧 Проверяем статус сервиса:"
ssh root@212.67.11.50 "systemctl status flaskapp --no-pager" 