# 🚀 Быстрое развертывание на сервер

## Если у вас уже есть работающий сервер:

### 1. Загрузите код на сервер:
```bash
# Через git (рекомендуется)
git clone https://github.com/your-username/flask_server.git
cd flask_server

# Или через SCP
scp -r . user@your-server:/path/to/app/
```

### 2. Запустите скрипт развертывания:
```bash
./deploy.sh
```

### 3. Готово! 🎉

## Ручной запуск:

### 1. Установите зависимости:
```bash
pip install -r requirements.txt
```

### 2. Запустите приложение:
```bash
python run_production.py
```

### 3. Или через systemd:
```bash
sudo systemctl start dating-app
sudo systemctl enable dating-app
```

## Проверка работы:
- Приложение будет доступно на порту 80
- Домен: ятута.рф
- Статус: `sudo systemctl status dating-app`

## Управление:
- Перезапуск: `sudo systemctl restart dating-app`
- Остановка: `sudo systemctl stop dating-app`
- Логи: `sudo journalctl -u dating-app -f` 