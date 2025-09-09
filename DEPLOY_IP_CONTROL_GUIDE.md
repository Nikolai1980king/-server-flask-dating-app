# 🚀 Руководство по развертыванию с системой IP-контроля

## 📋 Обзор

Это руководство поможет вам развернуть приложение с новой системой IP-контроля на сервере.

## 🎯 Что нового

- ✅ Система IP-контроля: **один IP = одна анкета**
- ✅ Автоматическое перенаправление на существующий профиль
- ✅ Защита от создания множественных анкет
- ✅ Тестовые эндпоинты для мониторинга

## 🚀 Способы развертывания

### 1. Автоматический деплой (рекомендуется)

#### Для сервера:
```bash
# Копируем файлы на сервер
./copy_to_server_ip_control.sh

# Подключаемся к серверу
ssh root@212.67.11.50

# Переходим в директорию
cd /root/flask_server

# Запускаем деплой
./deploy_with_ip_control.sh
```

#### Для локального тестирования:
```bash
# Запускаем универсальный скрипт
./universal_deploy.sh
```

### 2. Ручной деплой

#### Шаг 1: Подготовка файлов
```bash
# Основные файлы
app.py                    # Обновленное приложение
requirements.txt          # Зависимости
run_production.py         # Скрипт запуска
init_db_simple.py         # Инициализация БД

# Тестовые файлы
test_ip_control.html      # Тестовый интерфейс
IP_CONTROL_IMPLEMENTATION.md  # Документация

# Скрипты деплоя
deploy_with_ip_control.sh # Деплой на сервер
universal_deploy.sh       # Универсальный деплой
```

#### Шаг 2: Копирование на сервер
```bash
# Через SCP
scp app.py root@212.67.11.50:/root/flask_server/
scp requirements.txt root@212.67.11.50:/root/flask_server/
scp run_production.py root@212.67.11.50:/root/flask_server/
scp init_db_simple.py root@212.67.11.50:/root/flask_server/
scp test_ip_control.html root@212.67.11.50:/root/flask_server/

# Через rsync (если есть)
rsync -avz --exclude='.git' . root@212.67.11.50:/root/flask_server/
```

#### Шаг 3: Установка на сервере
```bash
# Подключаемся к серверу
ssh root@212.67.11.50

# Переходим в директорию
cd /root/flask_server

# Устанавливаем зависимости
pip install -r requirements.txt

# Инициализируем базу данных
python init_db_simple.py

# Останавливаем старое приложение
sudo systemctl stop dating-app

# Запускаем новое приложение
python run_production.py
```

## 🔧 Настройка systemd сервиса

### Создание сервиса:
```bash
sudo tee /etc/systemd/system/dating-app.service > /dev/null <<EOF
[Unit]
Description=Dating App with IP Control
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/flask_server
ExecStart=/usr/bin/python3 /root/flask_server/run_production.py
Restart=always
RestartSec=10
Environment=PORT=80
Environment=HOST=0.0.0.0

[Install]
WantedBy=multi-user.target
EOF
```

### Управление сервисом:
```bash
# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем автозапуск
sudo systemctl enable dating-app

# Запускаем сервис
sudo systemctl start dating-app

# Проверяем статус
sudo systemctl status dating-app

# Перезапускаем
sudo systemctl restart dating-app

# Останавливаем
sudo systemctl stop dating-app
```

## 🧪 Тестирование

### 1. Проверка работы приложения
```bash
# Статус сервиса
sudo systemctl status dating-app

# Логи
sudo journalctl -u dating-app -f

# Проверка порта
netstat -tlnp | grep :80
```

### 2. Тестирование IP-контроля
- Откройте: `http://ятута.рф/test_ip_control.html`
- Создайте анкету
- Попробуйте создать анкету снова
- Должно произойти перенаправление

### 3. Мониторинг
- Проверка IP: `http://ятута.рф/check_ip`
- Проверка БД: `http://ятута.рф/check_ip_control`
- Очистка БД: `http://ятута.рф/clear_ip_control` (POST)

## 📊 Мониторинг системы

### Логи приложения:
```bash
# Логи в реальном времени
sudo journalctl -u dating-app -f

# Последние 100 строк
sudo journalctl -u dating-app -n 100

# Логи за сегодня
sudo journalctl -u dating-app --since today
```

### Проверка базы данных:
```bash
# Подключение к SQLite
sqlite3 instance/dating_app.db

# Просмотр таблицы IP-контроля
SELECT * FROM ip_control;

# Количество записей
SELECT COUNT(*) FROM ip_control;

# Выход
.quit
```

### Проверка процессов:
```bash
# Процессы Python
ps aux | grep python

# Использование портов
netstat -tlnp | grep python
```

## 🔧 Устранение неполадок

### Проблема: Приложение не запускается
```bash
# Проверяем логи
sudo journalctl -u dating-app -n 50

# Проверяем зависимости
pip list | grep -E "(flask|sqlalchemy|socketio)"

# Проверяем базу данных
python init_db_simple.py
```

### Проблема: Ошибка базы данных
```bash
# Пересоздаем базу данных
rm instance/dating_app.db
python init_db_simple.py

# Проверяем права доступа
ls -la instance/
```

### Проблема: Порт занят
```bash
# Находим процесс
sudo lsof -i :80

# Убиваем процесс
sudo kill -9 PID

# Перезапускаем сервис
sudo systemctl restart dating-app
```

## 📁 Структура файлов на сервере

```
/root/flask_server/
├── app.py                          # Основное приложение
├── requirements.txt                # Зависимости
├── run_production.py              # Скрипт запуска
├── init_db_simple.py              # Инициализация БД
├── test_ip_control.html           # Тестовый интерфейс
├── IP_CONTROL_IMPLEMENTATION.md   # Документация
├── deploy_with_ip_control.sh      # Скрипт деплоя
├── universal_deploy.sh            # Универсальный деплой
├── instance/
│   └── dating_app.db              # База данных
└── static/
    └── uploads/                   # Загруженные фото
```

## 🎯 Результат

После успешного развертывания:

✅ **Приложение работает** на порту 80
✅ **Система IP-контроля активна** - один IP = одна анкета
✅ **Автоматическое перенаправление** на существующие профили
✅ **Тестовые эндпоинты** для мониторинга
✅ **Systemd сервис** для автозапуска

## 📞 Поддержка

При возникновении проблем:

1. Проверьте логи: `sudo journalctl -u dating-app -f`
2. Проверьте статус: `sudo systemctl status dating-app`
3. Проверьте тестовую страницу: `http://ятута.рф/test_ip_control.html`
4. Проверьте мониторинг: `http://ятута.рф/check_ip_control`

## 🔄 Обновление

Для обновления приложения:

```bash
# Останавливаем сервис
sudo systemctl stop dating-app

# Обновляем код
git pull origin main  # или копируем новые файлы

# Перезапускаем
sudo systemctl start dating-app
```