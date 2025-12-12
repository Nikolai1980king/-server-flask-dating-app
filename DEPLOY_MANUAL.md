# 🚀 Ручной деплой на сервер 212.67.11.50

## ✅ Подготовка выполнена

Архив создан: **deploy_package.tar.gz** (11M)

---

## 📋 Инструкция по развертыванию

### Шаг 1: Копирование архива на сервер

```bash
scp deploy_package.tar.gz root@212.67.11.50:/home/flaskapp/app/
```

**Введите пароль root при запросе**

---

### Шаг 2: Подключение к серверу

```bash
ssh root@212.67.11.50
```

---

### Шаг 3: Распаковка и установка

```bash
# Переходим в папку приложения
cd /home/flaskapp/app

# Распаковываем архив
tar -xzf deploy_package.tar.gz

# Устанавливаем зависимости
pip install -r requirements.txt

# Создаем папки
mkdir -p uploads instance
chmod 755 uploads

# Применяем миграции для новых таблиц
python migrate_add_puzzles.py
python migrate_surprise_payment.py
python migrate_add_sent_jokes.py
```

---

### Шаг 4: Проверка .env файла

```bash
nano .env
```

**Убедитесь что установлены:**
```
DEPLOY_DOMAIN=https://192.168.255.137
YOOKASSA_SHOP_ID=ваш_shop_id
YOOKASSA_SECRET_KEY=ваш_secret_key
YOOKASSA_TEST_MODE=False
```

---

### Шаг 5: Перезапуск приложения

```bash
# Останавливаем
systemctl stop flaskapp

# Запускаем
systemctl start flaskapp

# Проверяем статус
systemctl status flaskapp

# Смотрим логи
journalctl -u flaskapp -n 20 --no-pager
```

---

### Шаг 6: Проверка работы

Откройте в браузере:
```
https://192.168.255.137
```

---

## 🎁 Что было добавлено

### Новые функции:
- ✅ **Функция "Напрягись"** - 25 головоломок и задач на логику
- ✅ Головоломки не повторяются для одного получателя
- ✅ Красивое отображение с синим градиентом и анимациями
- ✅ Текст "Напишите за какой столик принести" для десерта и шампанского

### Новые таблицы в БД:
- `sent_puzzle` - отслеживание отправленных головоломок
- `sent_joke` - отслеживание отправленных анекдотов
- `chat_permission` - разрешения на общение после сюрприза

### Обновленные поля:
- `profile.surprise_feature_paid` - оплата функции "Удивить"
- `profile.surprise_feature_payment_date` - дата оплаты

---

## 🧪 Тестирование на сервере

### 1. Проверка миграций
```bash
cd /home/flaskapp/app
sqlite3 instance/dating_app.db

# В консоли SQLite:
.tables
# Должны быть: sent_puzzle, sent_joke, chat_permission

.schema sent_puzzle
.schema sent_joke
.schema chat_permission

.exit
```

### 2. Проверка функции "Напрягись"
1. Откройте https://192.168.255.137
2. Войдите в профиль
3. Активируйте функцию "Удивить" (50₽ или вручную в БД)
4. Нажмите кнопку "✨" на карточке посетителя
5. Выберите "🧠 Напрягись"
6. Проверьте что головоломка отправилась без ответа
7. Обновите страницу чата - головоломка должна остаться

### 3. Проверка всех 4 сюрпризов
- 🍰 **Десерт** - должен быть текст про столик
- 🍾 **Шампанское** - должен быть текст про столик
- 😄 **Рассмешить** - анекдот про ресторан
- 🧠 **Напрягись** - головоломка БЕЗ ответа

---

## 🔧 Полезные команды

### Просмотр логов в реальном времени
```bash
journalctl -u flaskapp -f
```

### Перезапуск приложения
```bash
systemctl restart flaskapp
```

### Просмотр ошибок Python
```bash
journalctl -u flaskapp -n 50 | grep -i error
```

### Проверка процесса
```bash
ps aux | grep python
```

### Очистка логов
```bash
journalctl --vacuum-time=1d
```

---

## ⚠️ Важные замечания

1. **Миграции обязательны!** Без них новые функции не будут работать
2. **Проверьте .env** - особенно DEPLOY_DOMAIN
3. **Проверьте права** - папка uploads должна быть доступна для записи
4. **База данных** - находится в `instance/dating_app.db`
5. **Бэкап** - сделайте бэкап БД перед миграциями

---

## 📦 Содержимое архива

```
deploy_package.tar.gz содержит:
├── app.py (обновлен с головоломками)
├── requirements.txt
├── deploy_config.py
├── migrate_add_puzzles.py (НОВАЯ)
├── migrate_surprise_payment.py
├── migrate_add_sent_jokes.py
├── .env.example
└── папки: instance/, uploads/, static/, templates/
```

---

## 🎉 После успешного деплоя

Приложение будет доступно по адресу:
**https://192.168.255.137**

С новыми функциями:
- 🍰 Десерт
- 🍾 Шампанское
- 😄 Рассмешить
- 🧠 Напрягись ← **НОВОЕ!**

---

## 💬 Поддержка

Если возникли проблемы, проверьте:
1. Логи: `journalctl -u flaskapp -n 50`
2. Статус: `systemctl status flaskapp`
3. Миграции применены: `sqlite3 instance/dating_app.db ".tables"`
4. Flask запущен: `ps aux | grep python`































