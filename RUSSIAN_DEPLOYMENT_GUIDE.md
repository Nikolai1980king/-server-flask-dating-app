# 🇷🇺 Руководство по деплою на российские платформы

## 🎯 Рекомендуемые платформы

### 1. **Yandex Cloud** (Рекомендуется для начала)
**Сайт:** [cloud.yandex.ru](https://cloud.yandex.ru)

#### Преимущества:
- ✅ Бесплатный период: 4000₽ на 60 дней
- ✅ Отличная документация на русском
- ✅ Интеграция с Яндекс.Картами
- ✅ Автоматическое масштабирование
- ✅ Соответствие 152-ФЗ

#### Стоимость после бесплатного периода:
- **Compute Instance**: от 200₽/месяц
- **Managed PostgreSQL**: от 300₽/месяц
- **Load Balancer**: от 100₽/месяц

### 2. **VK Cloud** (Бывший Mail.ru Cloud)
**Сайт:** [mcs.mail.ru](https://mcs.mail.ru)

#### Преимущества:
- ✅ Российская инфраструктура
- ✅ Соответствие 152-ФЗ
- ✅ Техподдержка на русском
- ✅ Автоматическое резервное копирование

#### Стоимость:
- **Бесплатный период**: 30 дней
- **После**: от 300₽/месяц

### 3. **Beget**
**Сайт:** [beget.com](https://beget.com)

#### Преимущества:
- ✅ Простая настройка
- ✅ Низкая стоимость
- ✅ Техподдержка 24/7
- ✅ Российский хостинг

#### Стоимость:
- **VPS**: от 100₽/месяц
- **Shared Hosting**: от 50₽/месяц

## 🚀 Деплой на Yandex Cloud

### Шаг 1: Регистрация
1. Перейдите на [cloud.yandex.ru](https://cloud.yandex.ru)
2. Зарегистрируйтесь через Яндекс.Аккаунт
3. Подтвердите номер телефона
4. Добавьте способ оплаты (для верификации)

### Шаг 2: Создание проекта
```bash
# Установка Yandex Cloud CLI
curl -sSL https://storage.yandexcloud.net/yandexcloud-yc/install.sh | bash

# Инициализация
yc init

# Создание проекта
yc config set project-id your-project-id
```

### Шаг 3: Создание виртуальной машины
```bash
# Создание VM
yc compute instance create \
  --name flask-app \
  --hostname flask-app \
  --memory 2 \
  --cores 2 \
  --core-fraction 20 \
  --preemptible \
  --network-interface subnet-name=default-ru-central1-a,ipv4-address=auto \
  --create-boot-disk image-folder-id=standard-images,image-family=ubuntu-2004-lts,size=10 \
  --zone ru-central1-a
```

### Шаг 4: Настройка сервера
```bash
# Подключение к серверу
ssh ubuntu@your-server-ip

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Создание пользователя для приложения
sudo adduser flaskapp
sudo usermod -aG sudo flaskapp
```

### Шаг 5: Деплой приложения
```bash
# Переключение на пользователя приложения
sudo su - flaskapp

# Клонирование репозитория
git clone https://github.com/your-username/your-repo.git
cd your-repo

# Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
pip install gunicorn

# Создание базы данных
python3 -c "from app import db; db.create_all()"
```

### Шаг 6: Настройка Gunicorn
```bash
# Создание конфигурации supervisor
sudo nano /etc/supervisor/conf.d/flaskapp.conf
```

Содержимое файла:
```ini
[program:flaskapp]
directory=/home/flaskapp/your-repo
command=/home/flaskapp/your-repo/venv/bin/gunicorn --workers 3 --bind unix:flaskapp.sock -m 007 app:app
autostart=true
autorestart=true
stderr_logfile=/var/log/flaskapp/flaskapp.err.log
stdout_logfile=/var/log/flaskapp/flaskapp.out.log
user=flaskapp
```

### Шаг 7: Настройка Nginx
```bash
# Создание конфигурации nginx
sudo nano /etc/nginx/sites-available/flaskapp
```

Содержимое файла:
```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    location / {
        include proxy_params;
        proxy_pass http://unix:/home/flaskapp/your-repo/flaskapp.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/flaskapp/your-repo/static;
    }
}
```

```bash
# Активация сайта
sudo ln -s /etc/nginx/sites-available/flaskapp /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx

# Запуск supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start flaskapp
```

## 🚀 Деплой на VK Cloud

### Шаг 1: Регистрация
1. Перейдите на [mcs.mail.ru](https://mcs.mail.ru)
2. Зарегистрируйтесь
3. Подтвердите email
4. Добавьте способ оплаты

### Шаг 2: Создание проекта
1. Создайте новый проект
2. Выберите регион (Москва)
3. Настройте сеть

### Шаг 3: Создание виртуальной машины
1. Выберите "Виртуальные машины"
2. Создайте новую VM:
   - **ОС**: Ubuntu 20.04
   - **CPU**: 2 ядра
   - **RAM**: 4 GB
   - **Диск**: 20 GB

### Шаг 4: Настройка (аналогично Yandex Cloud)
```bash
# Подключение к серверу
ssh ubuntu@your-server-ip

# Установка пакетов
sudo apt update && sudo apt upgrade -y
sudo apt install python3 python3-pip python3-venv nginx supervisor -y

# Настройка приложения (аналогично выше)
```

## 🚀 Деплой на Beget

### Шаг 1: Регистрация
1. Перейдите на [beget.com](https://beget.com)
2. Зарегистрируйтесь
3. Выберите тариф VPS

### Шаг 2: Настройка VPS
1. В панели управления создайте VPS
2. Выберите Ubuntu 20.04
3. Получите данные для подключения

### Шаг 3: Настройка (аналогично выше)
```bash
# Подключение к серверу
ssh root@your-server-ip

# Настройка аналогична Yandex Cloud
```

## 🔧 Настройка базы данных

### Yandex Cloud Managed PostgreSQL
```bash
# Создание базы данных
yc managed-postgresql cluster create \
  --name flask-db \
  --environment production \
  --network-name default \
  --resource-preset s2.micro \
  --disk-size 10 \
  --disk-type network-ssd \
  --zone ru-central1-a

# Получение подключения
yc managed-postgresql cluster get flask-db
```

### VK Cloud Managed PostgreSQL
1. В панели управления выберите "Базы данных"
2. Создайте PostgreSQL кластер
3. Получите строку подключения

## 🔐 Настройка SSL

### Let's Encrypt (бесплатно)
```bash
# Установка Certbot
sudo apt install certbot python3-certbot-nginx

# Получение сертификата
sudo certbot --nginx -d your-domain.com

# Автоматическое обновление
sudo crontab -e
# Добавьте строку:
# 0 12 * * * /usr/bin/certbot renew --quiet
```

## 📊 Мониторинг

### Yandex Cloud Monitoring
```bash
# Установка агента мониторинга
curl -sSL https://storage.yandexcloud.net/monitoring/agent/install.sh | bash

# Настройка
sudo yc monitoring-agent config set --folder-id your-folder-id
```

### Логирование
```bash
# Просмотр логов приложения
sudo tail -f /var/log/flaskapp/flaskapp.out.log

# Просмотр логов nginx
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

## 💰 Стоимость сравнение

| Платформа | Бесплатный период | После | Поддержка |
|-----------|------------------|-------|-----------|
| **Yandex Cloud** | 4000₽ на 60 дней | от 200₽/мес | ✅ |
| **VK Cloud** | 30 дней | от 300₽/мес | ✅ |
| **Beget** | Нет | от 100₽/мес | ✅ |
| **Selectel** | Нет | от 500₽/мес | ✅ |

## 🎯 Рекомендации

### Для MVP (начальная версия):
1. **Yandex Cloud** - лучший выбор
   - Бесплатный период 4000₽
   - Отличная документация
   - Простая настройка

### Для продакшена:
1. **VK Cloud** - надежный выбор
   - Российская инфраструктура
   - Соответствие 152-ФЗ
   - Хорошая техподдержка

### Для экономии:
1. **Beget** - бюджетный выбор
   - Низкая стоимость
   - Простая настройка
   - Российский хостинг

## 🔄 Автоматический деплой

### GitHub Actions для Yandex Cloud
```yaml
# .github/workflows/deploy.yml
name: Deploy to Yandex Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Deploy to server
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: ${{ secrets.HOST }}
        username: ${{ secrets.USERNAME }}
        key: ${{ secrets.KEY }}
        script: |
          cd /home/flaskapp/your-repo
          git pull origin main
          source venv/bin/activate
          pip install -r requirements.txt
          sudo supervisorctl restart flaskapp
```

## 🆘 Поддержка

### Yandex Cloud:
- Документация: [cloud.yandex.ru/docs](https://cloud.yandex.ru/docs)
- Поддержка: [cloud.yandex.ru/support](https://cloud.yandex.ru/support)

### VK Cloud:
- Документация: [mcs.mail.ru/docs](https://mcs.mail.ru/docs)
- Поддержка: через панель управления

### Beget:
- Документация: [beget.com/ru/help](https://beget.com/ru/help)
- Поддержка: 24/7 через тикеты

## 🎉 Заключение

Для вашего приложения рекомендую **Yandex Cloud**:
- Бесплатный период 4000₽ на 60 дней
- Интеграция с Яндекс.Картами
- Отличная документация на русском
- Простая настройка и масштабирование

**Удачи с деплоем!** 🚀 