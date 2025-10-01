# Инструкции по развертыванию на сервер

## 1. Подготовка приложения для продакшена

### Изменения в app.py для продакшена:
- Убрать `debug=True` 
- Убрать `allow_unsafe_werkzeug=True`
- Установить порт 80 или 443 для HTTP/HTTPS

### Пример запуска для продакшена:
```python
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=80, debug=False)
```

## 2. Загрузка на сервер

### Вариант 1: Git (рекомендуется)
```bash
# На сервере
cd /path/to/your/app
git pull origin main
```

### Вариант 2: SCP/SFTP
```bash
scp -r /path/to/local/app user@server:/path/to/server/app
```

## 3. Установка зависимостей на сервере
```bash
pip install -r requirements.txt
# или
pip install flask flask-socketio flask-sqlalchemy pillow
```

## 4. Запуск приложения

### Вариант 1: Прямой запуск
```bash
python app.py
```

### Вариант 2: Через systemd (рекомендуется)
Создать файл `/etc/systemd/system/dating-app.service`:
```ini
[Unit]
Description=Dating App
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/path/to/your/app
ExecStart=/usr/bin/python3 app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Затем:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dating-app
sudo systemctl start dating-app
```

### Вариант 3: Через screen/tmux
```bash
screen -S dating-app
python app.py
# Ctrl+A, D для отключения
```

## 5. Настройка домена ятута.рф

### DNS записи:
- A запись: `@` → IP вашего сервера
- A запись: `www` → IP вашего сервера

### Nginx (опционально, для проксирования):
```nginx
server {
    listen 80;
    server_name ятута.рф www.ятута.рф;
    
    location / {
        proxy_pass http://127.0.0.1:80;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    location /socket.io/ {
        proxy_pass http://127.0.0.1:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

## 6. Проверка работы
```bash
# Проверить статус
sudo systemctl status dating-app

# Посмотреть логи
sudo journalctl -u dating-app -f

# Проверить порт
netstat -tlnp | grep :80
```

## 7. Автоматический перезапуск при сбоях
Добавить в systemd сервис:
```ini
Restart=always
RestartSec=10
```

## 8. Мониторинг
```bash
# Проверить использование памяти
ps aux | grep python

# Проверить логи приложения
tail -f /path/to/your/app/app.log
```

## Важные моменты:
- Убедитесь, что порт 80 открыт в файрволе
- Проверьте права доступа к папке с приложением
- Настройте SSL сертификат для HTTPS (Let's Encrypt)
- Регулярно делайте бэкапы базы данных 