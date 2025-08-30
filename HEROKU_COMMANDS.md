# 📚 Справочник команд Heroku

## 🚀 Основные команды

### Приложения
```bash
# Создание приложения
heroku create [app-name]

# Список приложений
heroku apps

# Информация о приложении
heroku info [app-name]

# Открыть приложение в браузере
heroku open [app-name]

# Удаление приложения
heroku apps:destroy [app-name] --confirm [app-name]
```

### Деплой
```bash
# Отправка кода
git push heroku main
git push heroku master

# Принудительный деплой
git push heroku main --force

# Откат к предыдущей версии
heroku rollback [app-name]
```

### Процессы
```bash
# Просмотр процессов
heroku ps [app-name]

# Масштабирование
heroku ps:scale web=1 [app-name]
heroku ps:scale web=2 [app-name]

# Перезапуск
heroku restart [app-name]

# Остановка
heroku ps:stop web [app-name]
```

## 📊 Логи и мониторинг

### Логи
```bash
# Просмотр логов в реальном времени
heroku logs --tail [app-name]

# Последние 1000 строк
heroku logs -n 1000 [app-name]

# Логи за последний час
heroku logs --since 1h [app-name]

# Логи за определенную дату
heroku logs --since "2024-01-01" [app-name]

# Скачивание логов
heroku logs --num 1000 > logs.txt
```

### Мониторинг
```bash
# Статус приложения
heroku status

# Использование ресурсов
heroku ps:type [app-name]

# Метрики
heroku addons:open librato [app-name]
```

## ⚙️ Конфигурация

### Переменные окружения
```bash
# Просмотр всех переменных
heroku config [app-name]

# Установка переменной
heroku config:set KEY=value [app-name]

# Удаление переменной
heroku config:unset KEY [app-name]

# Экспорт в файл
heroku config --shell > .env

# Импорт из файла
heroku config:set $(cat .env | xargs) [app-name]
```

### Домены
```bash
# Список доменов
heroku domains [app-name]

# Добавление домена
heroku domains:add www.example.com [app-name]

# Удаление домена
heroku domains:remove www.example.com [app-name]

# Проверка DNS
heroku domains:wait www.example.com [app-name]
```

### SSL сертификаты
```bash
# Просмотр сертификатов
heroku certs [app-name]

# Автоматические сертификаты
heroku certs:auto:enable [app-name]
heroku certs:auto:disable [app-name]

# Ручные сертификаты
heroku certs:add cert.pem key.pem [app-name]
```

## 🗄️ База данных

### PostgreSQL
```bash
# Подключение к базе
heroku pg:psql [app-name]

# URL базы данных
heroku config:get DATABASE_URL [app-name]

# Статистика
heroku pg:stats [app-name]

# Активные соединения
heroku pg:ps [app-name]

# Информация о базе
heroku pg:info [app-name]
```

### Резервные копии
```bash
# Создание резервной копии
heroku pg:backups:capture [app-name]

# Список резервных копий
heroku pg:backups [app-name]

# Скачивание резервной копии
heroku pg:backups:download b001 [app-name]

# Восстановление
heroku pg:backups:restore b001 DATABASE_URL [app-name]

# Удаление резервной копии
heroku pg:backups:destroy b001 [app-name]
```

### Миграции
```bash
# Запуск Python скрипта
heroku run python script.py [app-name]

# Создание таблиц
heroku run python -c "from app import db; db.create_all()" [app-name]

# Flask миграции
heroku run flask db upgrade [app-name]
```

## 🔌 Аддоны

### Управление аддонами
```bash
# Список аддонов
heroku addons [app-name]

# Добавление аддона
heroku addons:create heroku-postgresql:mini [app-name]

# Удаление аддона
heroku addons:destroy heroku-postgresql [app-name]

# Обновление аддона
heroku addons:upgrade heroku-postgresql:basic [app-name]
```

### Популярные аддоны
```bash
# PostgreSQL
heroku addons:create heroku-postgresql:mini [app-name]

# Redis
heroku addons:create heroku-redis:mini [app-name]

# Papertrail (логи)
heroku addons:create papertrail:choklad [app-name]

# New Relic (мониторинг)
heroku addons:create newrelic:wayne [app-name]

# SendGrid (email)
heroku addons:create sendgrid:starter [app-name]
```

## 🔧 Разработка

### Локальный запуск
```bash
# Запуск с настройками Heroku
heroku local web

# Запуск команды
heroku local:run python script.py

# Просмотр переменных
heroku local:run env
```

### Отладка
```bash
# Запуск консоли
heroku run python [app-name]

# Запуск bash
heroku run bash [app-name]

# Выполнение команды
heroku run "ls -la" [app-name]
```

### Git интеграция
```bash
# Добавление remote
heroku git:remote -a [app-name]

# Просмотр remote
git remote -v

# Удаление remote
git remote remove heroku
```

## 📱 Мобильное приложение

### Heroku CLI для мобильных
```bash
# iOS: Heroku Dashboard в App Store
# Android: Heroku Dashboard в Google Play

# Команды через мобильное приложение:
# - Просмотр логов
# - Масштабирование
# - Перезапуск
# - Просмотр метрик
```

## 🔐 Безопасность

### API ключи
```bash
# Создание API ключа
heroku authorizations:create

# Список ключей
heroku authorizations

# Удаление ключа
heroku authorizations:destroy [key-id]
```

### SSH ключи
```bash
# Добавление SSH ключа
heroku keys:add ~/.ssh/id_rsa.pub

# Список ключей
heroku keys

# Удаление ключа
heroku keys:remove [email]
```

## 🚀 Автоматизация

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

### Pipelines
```bash
# Создание pipeline
heroku pipelines:create [pipeline-name]

# Добавление приложения в pipeline
heroku pipelines:add [pipeline-name] --app [app-name] --stage production

# Просмотр pipeline
heroku pipelines:info [pipeline-name]

# Продвижение между стадиями
heroku pipelines:promote --app [app-name]
```

## 📊 Аналитика

### Метрики
```bash
# Открытие метрик
heroku addons:open librato [app-name]

# Настройка алертов
heroku addons:open papertrail [app-name]

# Просмотр использования
heroku addons:open newrelic [app-name]
```

### Логи
```bash
# Papertrail
heroku addons:open papertrail [app-name]

# Logentries
heroku addons:open logentries [app-name]

# Loggly
heroku addons:open loggly [app-name]
```

## 🆘 Поддержка

### Справка
```bash
# Общая справка
heroku help

# Справка по команде
heroku help logs
heroku help config
heroku help ps

# Справка по аддону
heroku help addons
```

### Статус
```bash
# Статус Heroku
heroku status

# Статус приложения
heroku status [app-name]

# Статус аддонов
heroku addons:info [addon-name] [app-name]
```

### Поддержка
```bash
# Создание тикета
heroku support:create

# Просмотр тикетов
heroku support:tickets
```

## 💡 Полезные советы

### Алиасы
```bash
# Добавьте в ~/.bashrc или ~/.zshrc
alias hlogs='heroku logs --tail'
alias hps='heroku ps'
alias hconfig='heroku config'
alias hrun='heroku run'
alias hopen='heroku open'
```

### Скрипты
```bash
# deploy.sh
#!/bin/bash
git add .
git commit -m "$1"
git push heroku main
heroku open

# logs.sh
#!/bin/bash
heroku logs --tail --app $1
```

### Переменные окружения
```bash
# .env файл
FLASK_ENV=production
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://...

# Загрузка в Heroku
heroku config:set $(cat .env | xargs)
```

## 🎯 Лучшие практики

### Безопасность
- Никогда не коммитьте секреты в git
- Используйте переменные окружения
- Регулярно обновляйте зависимости
- Настройте SSL сертификаты

### Производительность
- Используйте кэширование
- Оптимизируйте запросы к БД
- Настройте CDN для статических файлов
- Мониторьте производительность

### Мониторинг
- Настройте алерты
- Регулярно проверяйте логи
- Делайте резервные копии
- Отслеживайте метрики

### Разработка
- Используйте staging окружение
- Тестируйте перед деплоем
- Используйте CI/CD
- Документируйте изменения 