#!/bin/bash

# 🔍 Скрипт для поиска информации о сервере

echo "🔍 Поиск информации о сервере для развертывания..."
echo ""

# Проверяем локальную сеть
echo "📡 Поиск серверов в локальной сети..."
echo "Сканируем 192.168.1.0/24..."
nmap -sn 192.168.1.0/24 2>/dev/null | grep -E "(Nmap scan report|MAC Address)" | head -20

echo ""
echo "Сканируем 192.168.0.0/24..."
nmap -sn 192.168.0.0/24 2>/dev/null | grep -E "(Nmap scan report|MAC Address)" | head -20

echo ""
echo "Сканируем 10.0.0.0/24..."
nmap -sn 10.0.0.0/24 2>/dev/null | grep -E "(Nmap scan report|MAC Address)" | head -20

echo ""
echo "🌐 Проверяем внешние IP адреса..."
echo "Ваш внешний IP:"
curl -s ifconfig.me
echo ""

echo "🔧 Возможные команды для развертывания:"
echo ""
echo "1. Если сервер в локальной сети:"
echo "   scp grayscale_deployment.tar.gz user@192.168.1.XXX:/path/to/project/"
echo ""
echo "2. Если сервер в интернете:"
echo "   scp grayscale_deployment.tar.gz user@YOUR-SERVER-IP:/path/to/project/"
echo ""
echo "3. Если используете доменное имя:"
echo "   scp grayscale_deployment.tar.gz user@your-domain.com:/path/to/project/"
echo ""
echo "4. Если используете SSH ключи:"
echo "   scp -i ~/.ssh/your-key.pem grayscale_deployment.tar.gz user@server:/path/"
echo ""

echo "❓ Вопросы для определения правильной команды:"
echo "1. Какой IP адрес вашего сервера?"
echo "2. Какой пользователь на сервере (root, user, ubuntu)?"
echo "3. В какой папке находится ваш проект на сервере?"
echo "4. Используете ли вы SSH ключи?"
echo ""

echo "📋 Примеры команд:"
echo "scp grayscale_deployment.tar.gz root@192.168.1.100:/var/www/html/"
echo "scp grayscale_deployment.tar.gz ubuntu@your-server.com:/home/ubuntu/project/"
echo "scp -i ~/.ssh/key.pem grayscale_deployment.tar.gz user@server:/path/"
