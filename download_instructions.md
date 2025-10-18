# 📥 Инструкции для скачивания архива

## 🌐 HTTP сервер запущен

Архив доступен по адресу: http://192.168.0.24:8080/deploy_package.tar.gz

## 📋 Команды для выполнения на сервере:

```bash
# 1. Перейдите в папку приложения
cd /home/flaskapp/app

# 2. Скачайте архив
wget http://192.168.0.24:8080/deploy_package.tar.gz

# 3. Распакуйте архив
tar -xzf deploy_package.tar.gz

# 4. Установите зависимости
pip install -r requirements.txt

# 5. Создайте необходимые папки
mkdir -p uploads instance
chmod 755 uploads

# 6. Примените миграции
python migrate_add_puzzles.py
python migrate_surprise_payment.py
python migrate_add_sent_jokes.py

# 7. Перезапустите приложение
systemctl stop flaskapp
systemctl start flaskapp

# 8. Проверьте статус
systemctl status flaskapp
```

## 🔧 Альтернативный способ (если wget не работает):

```bash
# Скачайте через curl
curl -O http://192.168.0.24:8080/deploy_package.tar.gz
```

## 📊 Проверка после деплоя:

1. **Лайки**: Попробуйте лайкнуть пользователя - не должно быть циклического поведения
2. **Сообщения**: Отправьте сообщение в чате - не должно дублироваться
3. **Платежи**: Проверьте обработку платежей ЮKassa

## 🌐 URL для проверки:
https://192.168.255.137








