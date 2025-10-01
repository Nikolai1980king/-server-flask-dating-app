#!/bin/bash
echo "🔄 Перезапуск сервера..."
ssh root@212.67.11.50 "systemctl restart flaskapp && systemctl status flaskapp"
echo "✅ Сервер перезапущен!" 