#!/usr/bin/env python3
"""
Исправление конфигурации Socket.IO для продакшн сервера
"""

# Создаем правильную конфигурацию для systemd
systemd_config = """[Unit]
Description=Flask App with Socket.IO
After=network.target

[Service]
Type=simple
User=flaskapp
WorkingDirectory=/home/flaskapp/app
Environment=PATH=/home/flaskapp/app/venv/bin
ExecStart=/home/flaskapp/app/venv/bin/python app.py
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""

# Создаем nginx конфигурацию для Socket.IO
nginx_config = """server {
    listen 80;
    server_name 192.168.255.137;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Socket.IO поддержка
    location /socket.io/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
"""

print("🔧 Конфигурация для исправления Socket.IO")
print("=" * 50)
print()
print("📋 КОМАНДЫ ДЛЯ ВЫПОЛНЕНИЯ НА СЕРВЕРЕ:")
print()
print("1️⃣ Создайте systemd конфигурацию:")
print("   sudo nano /etc/systemd/system/flaskapp.service")
print("   # Скопируйте содержимое ниже:")
print()
print(systemd_config)
print()
print("2️⃣ Создайте nginx конфигурацию:")
print("   sudo nano /etc/nginx/sites-available/flaskapp")
print("   # Скопируйте содержимое ниже:")
print()
print(nginx_config)
print()
print("3️⃣ Примените изменения:")
print("   sudo systemctl daemon-reload")
print("   sudo systemctl restart flaskapp")
print("   sudo systemctl restart nginx")
print("   sudo systemctl status flaskapp")
print()
print("4️⃣ Проверьте логи:")
print("   journalctl -u flaskapp -f")
print()
print("🌐 После применения проверьте: https://192.168.255.137")







