# 🚀 Быстрый старт: Деплой на Heroku за 10 минут

## ⚡ Пошаговый деплой

### 1. Установка Heroku CLI
```bash
# Ubuntu/Debian
curl https://cli-assets.heroku.com/install.sh | sh

# Проверка установки
heroku --version
```

### 2. Авторизация
```bash
heroku login
# Откроется браузер для входа
```

### 3. Подготовка проекта
```bash
# Проверяем файлы
ls -la app.py requirements.txt Procfile runtime.txt

# Инициализируем git если нужно
git init
git add .
git commit -m "Initial commit"
```

### 4. Создание приложения
```bash
# Создаем приложение (замените на свое имя)
heroku create your-dating-app-name

# Проверяем что приложение создано
heroku apps
```

### 5. Настройка базы данных
```bash
# Добавляем PostgreSQL
heroku addons:create heroku-postgresql:mini

# Проверяем URL базы данных
heroku config:get DATABASE_URL
```

### 6. Настройка переменных окружения
```bash
# Генерируем секретный ключ
python -c "import secrets; print(secrets.token_hex(32))"

# Устанавливаем переменные (замените на свои значения)
heroku config:set SECRET_KEY=your-generated-secret-key
heroku config:set FLASK_ENV=production
heroku config:set MAX_REGISTRATION_DISTANCE=3000
heroku config:set PROFILE_LIFETIME_HOURS=24

# Проверяем настройки
heroku config
```

### 7. Деплой
```bash
# Отправляем код на Heroku
git push heroku main

# Если ветка называется master
git push heroku master
```

### 8. Запуск приложения
```bash
# Открываем приложение
heroku open

# Или получаем URL
heroku info -s | grep web_url
```

### 9. Проверка логов
```bash
# Смотрим логи в реальном времени
heroku logs --tail
```

## 🔧 Настройка базы данных

### Создание таблиц
```bash
# Запускаем создание таблиц
heroku run python -c "from app import db; db.create_all()"

# Проверяем таблицы
heroku pg:psql -c "\dt"
```

### Резервная копия (опционально)
```bash
# Создаем резервную копию
heroku pg:backups:capture

# Список резервных копий
heroku pg:backups
```

## 🚨 Решение проблем

### Если приложение не запускается:
```bash
# Проверяем логи
heroku logs --tail

# Проверяем процессы
heroku ps

# Перезапускаем
heroku restart
```

### Если база данных не работает:
```bash
# Проверяем подключение
heroku pg:psql -c "SELECT version();"

# Проверяем переменные
heroku config:get DATABASE_URL
```

### Если файлы не загружаются:
```bash
# Проверяем права доступа
heroku run ls -la static/uploads

# Создаем папку если нужно
heroku run mkdir -p static/uploads
```

## 📊 Мониторинг

### Просмотр метрик
```bash
# Статус приложения
heroku ps

# Использование ресурсов
heroku addons

# Логи
heroku logs --tail
```

### Настройка алертов
```bash
# Добавляем мониторинг логов
heroku addons:create papertrail:choklad
```

## 🔄 Обновление приложения

### Процесс обновления
```bash
# Вносим изменения в код
# ...

# Коммитим изменения
git add .
git commit -m "Update app"

# Деплоим
git push heroku main

# Проверяем
heroku open
```

## 💰 Стоимость

### Текущие планы:
- **Hobby**: $7/месяц (512MB RAM, 1 процесс)
- **Basic**: $7/месяц (512MB RAM, всегда работает)
- **Standard**: $25/месяц (автоматическое масштабирование)

### Аддоны:
- **PostgreSQL Mini**: $5/месяц
- **Papertrail**: $7/месяц

## 🎯 Следующие шаги

### 1. Настройка домена
```bash
# Добавляем кастомный домен
heroku domains:add www.yourdomain.com
```

### 2. Настройка SSL
```bash
# Проверяем SSL (включен по умолчанию)
heroku certs
```

### 3. Автоматический деплой
```bash
# Подключаем GitHub
heroku pipelines:create your-app-name
```

### 4. Мониторинг
```bash
# Добавляем мониторинг
heroku addons:create newrelic:wayne
```

## 🆘 Полезные команды

```bash
# Справка
heroku help

# Информация о приложении
heroku info

# Статус
heroku status

# Переменные окружения
heroku config

# Логи
heroku logs --tail

# Процессы
heroku ps

# Аддоны
heroku addons

# База данных
heroku pg:psql
```

## 🎉 Готово!

Ваше приложение теперь работает на Heroku! 

**URL**: https://your-app-name.herokuapp.com

**Следующие шаги:**
1. Протестируйте все функции
2. Настройте мониторинг
3. Добавьте кастомный домен
4. Настройте резервные копии

**Удачи!** 🚀 