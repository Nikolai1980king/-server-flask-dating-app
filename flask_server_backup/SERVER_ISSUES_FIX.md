# 🔧 Решение проблем с сервером

## 🚨 Проблема: База данных только для чтения

### Симптомы:
- Ошибка: `sqlite3.OperationalError: attempt to write a readonly database`
- Не удается создать или удалить анкеты
- Страница создания анкеты не загружается

### Причина:
База данных `instance/dating_app.db` имеет неправильные права доступа (только для чтения).

### Решение:

#### Автоматическое исправление:
```bash
./fix_server_issues.sh
```

#### Ручное исправление:
```bash
# 1. Исправляем права доступа
chmod 664 instance/dating_app.db

# 2. Перезапускаем сервер
pkill -f "python.*app.py"
python app.py
```

## 🚨 Проблема: Отсутствует placeholder.png

### Симптомы:
- Ошибка 404: `GET /static/uploads/placeholder.png`
- Анкеты отображаются без фото
- Проблемы с загрузкой изображений

### Причина:
Файл `static/uploads/placeholder.png` отсутствует или поврежден.

### Решение:

#### Автоматическое исправление:
```bash
./fix_server_issues.sh
```

#### Ручное исправление:
```bash
# 1. Создаем placeholder.png
convert -size 200x200 xc:gray -fill white -draw "text 50,100 'No Photo'" static/uploads/placeholder.png

# 2. Проверяем права доступа
chmod 644 static/uploads/placeholder.png
```

## 🚨 Проблема: Поврежденные записи в базе данных

### Симптомы:
- Анкеты без фото
- Ошибки при удалении анкет
- Несоответствие между файлами и записями в БД

### Решение:

#### Очистка базы данных:
```bash
# 1. Останавливаем сервер
pkill -f "python.*app.py"

# 2. Проверяем количество анкет
sqlite3 instance/dating_app.db "SELECT COUNT(*) FROM profile;"

# 3. Удаляем все анкеты (если нужно)
sqlite3 instance/dating_app.db "DELETE FROM profile;"

# 4. Очищаем связанные таблицы
sqlite3 instance/dating_app.db "DELETE FROM like;"
sqlite3 instance/dating_app.db "DELETE FROM message;"

# 5. Перезапускаем сервер
python app.py
```

#### Очистка файлов:
```bash
# Удаляем все файлы из uploads (кроме placeholder.png)
find static/uploads/ -name "*.jpg" -o -name "*.png" -o -name "*.jpeg" | grep -v placeholder.png | xargs rm -f
```

## 🚨 Проблема: Страница создания анкеты не загружается

### Симптомы:
- HTTP 500 ошибка при заходе на `/create`
- Белый экран
- Ошибки в логах сервера

### Решение:

#### Проверка и исправление:
```bash
# 1. Проверяем логи сервера
tail -f /var/log/syslog | grep python

# 2. Проверяем права доступа
ls -la instance/
ls -la static/uploads/

# 3. Запускаем скрипт исправления
./fix_server_issues.sh

# 4. Проверяем работу сервера
curl -I http://localhost:5000/create
```

## 🔧 Автоматический скрипт исправления

Создан скрипт `fix_server_issues.sh` для автоматического исправления всех проблем:

### Использование:
```bash
# Запуск скрипта
./fix_server_issues.sh
```

### Что делает скрипт:
1. ✅ Исправляет права доступа к базе данных
2. ✅ Создает placeholder.png если его нет
3. ✅ Исправляет права доступа к папкам
4. ✅ Останавливает старые процессы
5. ✅ Запускает сервер заново
6. ✅ Проверяет работу сервера

## 📊 Мониторинг состояния сервера

### Проверка состояния:
```bash
# Проверка процессов
ps aux | grep python

# Проверка портов
netstat -tlnp | grep 5000

# Проверка базы данных
sqlite3 instance/dating_app.db "SELECT COUNT(*) FROM profile;"

# Проверка файлов
ls -la static/uploads/
ls -la instance/
```

### Проверка API endpoints:
```bash
# Главная страница
curl -I http://localhost:5000/

# Страница создания анкеты
curl -I http://localhost:5000/create

# API профилей
curl http://localhost:5000/api/profiles

# Placeholder изображение
curl -I http://localhost:5000/static/uploads/placeholder.png
```

## 🚀 Быстрые команды

### Перезапуск сервера:
```bash
pkill -f "python.*app.py" && python app.py
```

### Полная очистка и перезапуск:
```bash
./fix_server_issues.sh
```

### Проверка всех компонентов:
```bash
echo "🔍 Проверка сервера..."
curl -s -f http://localhost:5000/ > /dev/null && echo "✅ Сервер работает" || echo "❌ Сервер не работает"

echo "🔍 Проверка базы данных..."
ls -la instance/dating_app.db | grep -q "rw" && echo "✅ БД доступна для записи" || echo "❌ БД только для чтения"

echo "🔍 Проверка placeholder.png..."
curl -s -f http://localhost:5000/static/uploads/placeholder.png > /dev/null && echo "✅ Placeholder доступен" || echo "❌ Placeholder отсутствует"
```

## 📞 Поддержка

Если проблемы не решаются:

1. **Проверьте логи сервера** - они покажут точную причину ошибки
2. **Запустите скрипт исправления** - `./fix_server_issues.sh`
3. **Проверьте права доступа** - все файлы должны быть доступны для записи
4. **Перезапустите сервер** - иногда помогает полный перезапуск

## ✅ Статус исправлений

- **Права доступа к БД**: ✅ Исправлено
- **Placeholder.png**: ✅ Создан
- **Скрипт автоматизации**: ✅ Создан
- **Документация**: ✅ Создана
- **Тестирование**: ✅ Проведено

**Сервер должен работать стабильно!** 🎯✨ 