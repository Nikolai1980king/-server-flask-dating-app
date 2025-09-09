# 🚀 Быстрый деплой с системой IP-контроля

## ⚡ Самый быстрый способ

### 1. Копируем файлы на сервер:
```bash
./copy_to_server_ip_control.sh
```

### 2. Подключаемся к серверу и деплоим:
```bash
ssh root@212.67.11.50
cd /root/flask_server
./deploy_with_ip_control.sh
```

### 3. Готово! 🎉

## 🧪 Тестирование

Откройте: `http://ятута.рф/test_ip_control.html`

## 📊 Мониторинг

- Статус: `sudo systemctl status dating-app`
- Логи: `sudo journalctl -u dating-app -f`
- IP-контроль: `http://ятута.рф/check_ip_control`

## 🔄 Управление

- Перезапуск: `sudo systemctl restart dating-app`
- Остановка: `sudo systemctl stop dating-app`
- Запуск: `sudo systemctl start dating-app`

## 🎯 Что нового

✅ **Система IP-контроля** - один IP = одна анкета
✅ **Автоматическое перенаправление** на существующие профили
✅ **Защита от множественных анкет** с одного устройства
✅ **Тестовые эндпоинты** для мониторинга

## 📁 Файлы для деплоя

- `app.py` - обновленное приложение
- `init_db_simple.py` - инициализация БД
- `test_ip_control.html` - тестовый интерфейс
- `deploy_with_ip_control.sh` - скрипт деплоя
- `copy_to_server_ip_control.sh` - копирование на сервер

## ⚠️ Важно

- Убедитесь, что SSH ключи настроены
- Проверьте настройки сервера в скриптах
- После деплоя протестируйте систему IP-контроля