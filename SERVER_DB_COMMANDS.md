# 🖥️ Команды для проверки БД на удаленном сервере

## 📡 Подключение к серверу

```bash
ssh user@your-server-ip
```

## 📂 Переход в папку проекта

```bash
cd /path/to/flask_server
```

## 🔍 Проверка базы данных

### 1. Быстрая проверка
```bash
python3 check_db.py
```

**Показывает:**
- Количество профилей
- Количество лайков
- Количество метчей
- ⚠️ Предупреждение если есть лишние лайки

### 2. Детальная проверка через Python
```bash
python3 -c "
from app import db, Profile, Like, Match
from app import app

with app.app_context():
    profiles = Profile.query.all()
    likes = Like.query.all()
    matches = Match.query.all()
    
    print('Профили:')
    for p in profiles:
        print(f'  - {p.name} (ID: {p.id[:12]}...)')
    
    print(f'\nЛайки: {len(likes)}')
    for like in likes:
        from_p = Profile.query.get(like.user_id)
        to_p = Profile.query.get(like.liked_id)
        print(f'  {from_p.name if from_p else \"???\"} -> {to_p.name if to_p else \"???\"}')
    
    print(f'\nМетчи: {len(matches)}')
"
```

### 3. Проверка через SQLite напрямую
```bash
sqlite3 dating_app.db "SELECT COUNT(*) FROM profile;"
sqlite3 dating_app.db "SELECT COUNT(*) FROM like;"
sqlite3 dating_app.db "SELECT COUNT(*) FROM match;"
```

## 🧹 Очистка данных

### Интерактивная очистка (Рекомендуется)
```bash
python3 clear_cache.py
```

**Меню:**
1. Проверить состояние БД
2. Удалить только лайки и метчи
3. Удалить только временные профили
4. ПОЛНАЯ ОЧИСТКА (все данные)

### Быстрая очистка лайков (без подтверждения)
```bash
python3 -c "
from app import db, Like, Match
from app import app

with app.app_context():
    likes_count = Like.query.count()
    matches_count = Match.query.count()
    
    Like.query.delete()
    Match.query.delete()
    db.session.commit()
    
    print(f'Удалено: {likes_count} лайков, {matches_count} метчей')
"
```

### Полная очистка БД (ОСТОРОЖНО!)
```bash
python3 -c "
from app import db, Profile, Like, Match, PendingProfile, Message
from app import app

with app.app_context():
    Like.query.delete()
    Match.query.delete()
    Message.query.delete()
    Profile.query.delete()
    PendingProfile.query.delete()
    db.session.commit()
    print('✅ База данных полностью очищена')
"
```

## 🗑️ Очистка кеша браузера

### На компьютере
```
Ctrl + Shift + Delete → Очистить кеш
```
Или:
```
Ctrl + F5 (жесткая перезагрузка)
```

### На телефоне
```
Настройки браузера → Очистить данные → Кеш
```

## 🔄 Перезапуск сервера

### Если используете systemd
```bash
sudo systemctl restart flask-app
sudo systemctl status flask-app
```

### Если запущено вручную
```bash
# Остановить (найти процесс)
ps aux | grep app.py
kill -9 <PID>

# Запустить снова
nohup python3 app.py > server.log 2>&1 &
```

### Если используете screen/tmux
```bash
# Найти сессию
screen -ls
# или
tmux ls

# Подключиться
screen -r flask
# или
tmux attach -t flask

# Остановить (Ctrl+C) и запустить снова
python3 app.py
```

## 📊 Мониторинг в реальном времени

### Следить за логами
```bash
tail -f server.log
```

### Проверять БД каждые 5 секунд
```bash
watch -n 5 'python3 check_db.py'
```

## 🔧 Диагностика проблем с лайками

### 1. Проверить что в БД
```bash
python3 check_db.py
```

### 2. Открыть диагностическую страницу
```
http://your-server-ip:5000/debug/likes-and-matches
```

### 3. Проверить синхронизацию
```bash
# Создать 2 профиля
# Лайкнуть со страницы /visitors
python3 check_db.py
# Должен появиться 1 лайк

# Открыть /profile/<id>
# Сердечко должно быть красным
```

### 4. Если лайки появляются сами
```bash
# Очистить лайки
python3 clear_cache.py
# Выбрать опцию 2

# Обновить код
git pull origin master

# Перезапустить сервер
sudo systemctl restart flask-app

# Проверить снова
python3 check_db.py
```

## 🚨 Экстренная очистка (одна команда)

```bash
cd /path/to/flask_server && python3 -c "from app import db, Like, Match; from app import app; app.app_context().push(); Like.query.delete(); Match.query.delete(); db.session.commit(); print('✅ Очищено')"
```

## 📝 Резервное копирование БД

### Создать бэкап
```bash
cp dating_app.db dating_app.db.backup_$(date +%Y%m%d_%H%M%S)
```

### Восстановить из бэкапа
```bash
cp dating_app.db.backup_20241010_123456 dating_app.db
```

## 🔍 SQL запросы для диагностики

### Показать всех пользователей и их лайки
```bash
sqlite3 dating_app.db << EOF
SELECT 
    p1.name as 'От кого',
    p2.name as 'Кому',
    l.id as 'Like ID'
FROM like l
LEFT JOIN profile p1 ON l.user_id = p1.id
LEFT JOIN profile p2 ON l.liked_id = p2.id;
EOF
```

### Найти дублирующиеся лайки
```bash
sqlite3 dating_app.db << EOF
SELECT user_id, liked_id, COUNT(*) as count
FROM like
GROUP BY user_id, liked_id
HAVING count > 1;
EOF
```

### Показать структуру таблицы
```bash
sqlite3 dating_app.db ".schema like"
sqlite3 dating_app.db ".schema profile"
```

## 📱 Проверка с телефона

1. Откройте браузер на телефоне
2. Зайдите: `http://your-server-ip:5000/debug/likes-and-matches`
3. Проверьте таблицу "Мои лайки"
4. Если есть лайки которых не было → проблема найдена

## ✅ Чеклист диагностики

- [ ] Подключился к серверу
- [ ] Проверил БД: `python3 check_db.py`
- [ ] Открыл диагностику: `/debug/likes-and-matches`
- [ ] Почистил кеш браузера: Ctrl+F5
- [ ] Обновил код: `git pull`
- [ ] Перезапустил сервер
- [ ] Проверил снова: `python3 check_db.py`
- [ ] Протестировал синхронизацию лайков

## 💡 Полезные алиасы

Добавьте в `~/.bashrc`:

```bash
alias db-check='cd /path/to/flask_server && python3 check_db.py'
alias db-clear='cd /path/to/flask_server && python3 clear_cache.py'
alias flask-restart='sudo systemctl restart flask-app && sudo systemctl status flask-app'
alias flask-logs='tail -f /path/to/flask_server/server.log'
```

Применить:
```bash
source ~/.bashrc
```

Теперь можно использовать:
```bash
db-check        # Проверить БД
db-clear        # Очистить БД
flask-restart   # Перезапустить
flask-logs      # Смотреть логи
```


















