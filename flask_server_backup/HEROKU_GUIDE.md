# 🚀 Полное руководство по Heroku

## 📋 Что такое Heroku?

**Heroku** - это облачная платформа как услуга (PaaS), которая позволяет легко развертывать, управлять и масштабировать веб-приложения. Она поддерживает множество языков программирования, включая Python.

### ✅ Преимущества Heroku:
- **Простота деплоя** - один клик или команда
- **Автоматическое масштабирование**
- **Встроенные аддоны** (базы данных, кэш, мониторинг)
- **SSL сертификаты** включены
- **Git интеграция** - деплой через git push
- **Мониторинг и логи** встроены

### ❌ Недостатки:
- **Стоимость** - от $7/месяц
- **Ограничения** на бесплатном плане
- **Vendor lock-in** - привязка к платформе

## 🛠️ Установка и настройка

### 1. Установка Heroku CLI

**Ubuntu/Debian:**
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

**macOS:**
```bash
brew tap heroku/brew && brew install heroku
```

**Windows:**
Скачайте установщик с [devcenter.heroku.com](https://devcenter.heroku.com/articles/heroku-cli)

### 2. Регистрация и авторизация
```bash
# Регистрация (откроется браузер)
heroku login

# Проверка авторизации
heroku auth:whoami
```

## 🚀 Первый деплой

### Шаг 1: Подготовка проекта
```bash
# Убедитесь, что у вас есть все необходимые файлы
ls -la
# Должны быть: app.py, requirements.txt, Procfile, runtime.txt
```

### Шаг 2: Создание приложения
```bash
# Создание нового приложения
heroku create your-app-name

# Или создание с случайным именем
heroku create
```

### Шаг 3: Настройка базы данных
```bash
# Добавление PostgreSQL (бесплатный план)
heroku addons:create heroku-postgresql:mini

# Проверка URL базы данных
heroku config:get DATABASE_URL
```

### Шаг 4: Настройка переменных окружения
```bash
# Основные настройки
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-super-secret-key-here

# Настройки приложения
heroku config:set MAX_REGISTRATION_DISTANCE=3000
heroku config:set PROFILE_LIFETIME_HOURS=24

# Просмотр всех переменных
heroku config
```

### Шаг 5: Деплой
```bash
# Добавление файлов в git
git add .

# Коммит изменений
git commit -m "Deploy to Heroku"

# Отправка на Heroku
git push heroku main
```

### Шаг 6: Запуск приложения
```bash
# Открытие приложения в браузере
heroku open

# Или получение URL
heroku info -s | grep web_url
```

## 📊 Управление приложением

### Просмотр логов
```bash
# Просмотр логов в реальном времени
heroku logs --tail

# Просмотр последних 1000 строк
heroku logs -n 1000

# Просмотр логов за определенный период
heroku logs --since 1h
```

### Мониторинг производительности
```bash
# Просмотр метрик
heroku ps

# Просмотр использования ресурсов
heroku ps:scale web=1

# Просмотр аддонов
heroku addons
```

### Управление базой данных
```bash
# Подключение к базе данных
heroku pg:psql

# Резервная копия
heroku pg:backups:capture

# Список резервных копий
heroku pg:backups

# Восстановление из резервной копии
heroku pg:backups:restore b001 DATABASE_URL
```

## 🔧 Продвинутые настройки

### Настройка домена
```bash
# Добавление кастомного домена
heroku domains:add www.yourdomain.com

# Проверка DNS записей
heroku domains
```

### Настройка SSL
```bash
# Автоматические SSL сертификаты (включены по умолчанию)
heroku certs:auto:enable

# Проверка статуса SSL
heroku certs
```

### Настройка переменных окружения
```bash
# Установка переменной
heroku config:set VARIABLE_NAME=value

# Удаление переменной
heroku config:unset VARIABLE_NAME

# Экспорт переменных в файл
heroku config --shell > .env
```

## 🗄️ Работа с базой данных

### Миграции
```bash
# Запуск миграций
heroku run python -c "from app import db; db.create_all()"

# Или через Flask-Migrate
heroku run flask db upgrade
```

### Резервные копии
```bash
# Создание резервной копии
heroku pg:backups:capture

# Скачивание резервной копии
heroku pg:backups:download

# Восстановление
heroku pg:backups:restore b001 DATABASE_URL
```

### Мониторинг базы данных
```bash
# Просмотр статистики
heroku pg:stats

# Просмотр активных соединений
heroku pg:ps
```

## 🔍 Отладка и решение проблем

### Частые ошибки и решения

#### 1. "H10 - App crashed"
```bash
# Просмотр логов для диагностики
heroku logs --tail

# Проверка переменных окружения
heroku config

# Перезапуск приложения
heroku restart
```

#### 2. "H14 - No web processes running"
```bash
# Проверка процессов
heroku ps

# Запуск веб-процесса
heroku ps:scale web=1
```

#### 3. "H12 - Request timeout"
```bash
# Увеличение таймаута в Procfile
web: gunicorn app:app --timeout 30

# Перезапуск
git add . && git commit -m "Fix timeout" && git push heroku main
```

#### 4. Проблемы с базой данных
```bash
# Проверка подключения к БД
heroku pg:psql -c "SELECT version();"

# Проверка таблиц
heroku pg:psql -c "\dt"
```

### Отладка локально
```bash
# Запуск локально с настройками Heroku
heroku local web

# Или с переменными окружения
heroku local:run python app.py
```

## 💰 Планы и стоимость

### Планы Heroku:

#### **Hobby (Бывший Free) - $7/месяц**
- 512MB RAM
- 1 процесс
- 30 минут сна в день
- 10,000 строк логов

#### **Basic - $7/месяц**
- 512MB RAM
- 1 процесс
- Всегда работает
- 10,000 строк логов

#### **Standard - $25/месяц**
- 512MB RAM
- 1-10 процессов
- Автоматическое масштабирование
- 50,000 строк логов

#### **Performance - $250/месяц**
- 2.5GB RAM
- 1-100 процессов
- Автоматическое масштабирование
- Неограниченные логи

### Аддоны:
- **PostgreSQL Mini**: $5/месяц
- **PostgreSQL Basic**: $9/месяц
- **Redis Mini**: $15/месяц
- **Papertrail**: $7/месяц (логи)

## 🚀 Автоматический деплой

### GitHub Integration
```bash
# Подключение к GitHub
heroku pipelines:create your-app-name

# Настройка автоматического деплоя
heroku pipelines:add your-app-name --app your-app-name --stage production
```

### GitHub Actions
```yaml
# .github/workflows/deploy.yml
name: Deploy to Heroku

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to Heroku
      uses: akhileshns/heroku-deploy@v3.12.12
      with:
        heroku_api_key: ${{ secrets.HEROKU_API_KEY }}
        heroku_app_name: ${{ secrets.HEROKU_APP_NAME }}
        heroku_email: ${{ secrets.HEROKU_EMAIL }}
```

## 📱 Мобильное приложение

### Heroku CLI для мобильных устройств
- **iOS**: Heroku Dashboard в App Store
- **Android**: Heroku Dashboard в Google Play

## 🔐 Безопасность

### Переменные окружения
```bash
# Никогда не коммитьте секреты в git
echo ".env" >> .gitignore

# Используйте переменные окружения Heroku
heroku config:set SECRET_KEY=your-secret-key
```

### SSL/HTTPS
```bash
# Проверка SSL
heroku certs

# Принудительное перенаправление на HTTPS
# Добавьте в код:
if request.headers.get('X-Forwarded-Proto') == 'http':
    url = request.url.replace('http://', 'https://', 1)
    return redirect(url, code=301)
```

## 📊 Мониторинг и аналитика

### Встроенные метрики
```bash
# Просмотр метрик
heroku addons:open librato

# Настройка алертов
heroku addons:open papertrail
```

### Сторонние сервисы
- **New Relic**: `heroku addons:create newrelic:wayne`
- **Logentries**: `heroku addons:create logentries:le_tryit`
- **Sentry**: `heroku addons:create sentry:f1`

## 🎯 Лучшие практики

### 1. Структура проекта
```
your-app/
├── app.py
├── requirements.txt
├── Procfile
├── runtime.txt
├── .gitignore
├── static/
├── templates/
└── instance/
```

### 2. Procfile
```procfile
web: gunicorn app:app --log-file -
```

### 3. requirements.txt
```txt
Flask==2.3.3
gunicorn==21.2.0
psycopg2-binary==2.9.7
python-dotenv==1.0.0
```

### 4. Переменные окружения
```bash
# Обязательные
SECRET_KEY=your-secret-key
FLASK_ENV=production
DATABASE_URL=postgresql://...

# Опциональные
DEBUG=False
LOG_LEVEL=INFO
```

## 🆘 Поддержка

### Полезные команды
```bash
# Справка
heroku help

# Справка по команде
heroku help logs

# Статус приложения
heroku status
```

### Документация
- [Heroku Dev Center](https://devcenter.heroku.com/)
- [Python на Heroku](https://devcenter.heroku.com/articles/python-support)
- [PostgreSQL на Heroku](https://devcenter.heroku.com/articles/heroku-postgresql)

### Сообщество
- [Heroku Support](https://help.heroku.com/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/heroku)
- [Reddit r/Heroku](https://www.reddit.com/r/Heroku/)

## 🎉 Заключение

Heroku - отличный выбор для быстрого деплоя и масштабирования веб-приложений. Следуя этому руководству, вы сможете легко развернуть ваше Flask-приложение и управлять им в продакшене.

**Удачи с деплоем!** 🚀 