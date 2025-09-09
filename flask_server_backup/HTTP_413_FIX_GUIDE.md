# 🔧 Решение ошибки 413 "Request Entity Too Large"

## 🚨 Проблема
Ошибка 413 означает, что размер загружаемого файла превышает максимально допустимый размер, установленный в nginx.

## ✅ Быстрое решение (2 минуты)

### Шаг 1: Запустите скрипт исправления nginx
```bash
./restart_nginx_fix_413.sh
```

### Шаг 2: Перезапустите Flask сервер
```bash
# Остановите текущий сервер (Ctrl+C)
# Затем запустите:
python app_https_simple.py
```

### Шаг 3: Проверьте работу
Откройте: `https://192.168.0.24:5000`

## 🔍 Что было исправлено

### 1. Nginx конфигурация
- **Добавлена директива**: `client_max_body_size 2048M;`
- **Лимит увеличен**: с дефолтных 1MB до 2GB
- **Применена к HTTPS**: порт 443

### 2. Flask приложение
- **Добавлена настройка**: `MAX_CONTENT_LENGTH = 2GB`
- **В файле**: `app.py` (строка 20)
- **Совместимость**: с nginx лимитом

## 📁 Измененные файлы

1. **`nginx_https.conf`** - добавлен `client_max_body_size 2048M;`
2. **`app.py`** - добавлен `MAX_CONTENT_LENGTH = 2GB`
3. **`restart_nginx_fix_413.sh`** - скрипт автоматического исправления

## 🛠️ Ручное исправление (если скрипт не работает)

### Для nginx:
```bash
# Отредактируйте файл
sudo nano /etc/nginx/sites-available/flask_server

# Добавьте строку в server блок:
client_max_body_size 2048M;

# Проверьте конфигурацию
sudo nginx -t

# Перезапустите nginx
sudo systemctl restart nginx
```

### Для Flask:
```python
# В app.py добавьте:
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB
```

## 🧪 Тестирование

### Проверка nginx:
```bash
# Проверьте статус
sudo systemctl status nginx

# Проверьте конфигурацию
sudo nginx -t

# Посмотрите логи
sudo tail -f /var/log/nginx/error.log
```

### Проверка Flask:
```bash
# Запустите тестовый сервер
python test_upload.py

# Откройте: http://192.168.255.137:5001/test_upload
```

## 📊 Размеры файлов

| Компонент | Старый лимит | Новый лимит |
|-----------|--------------|-------------|
| Nginx | 1MB | 2GB |
| Flask | Не установлен | 2GB |
| Общий | 1MB | 2GB |

## 🔄 Альтернативные решения

### 1. Использование простого HTTP сервера
```bash
python test_upload.py
# Откройте: http://192.168.255.137:5001
```

### 2. Использование HTTPS без nginx
```bash
python app_https_simple.py
# Откройте: https://192.168.0.24:5000
```

### 3. Уменьшение размера файлов
- Сжатие изображений
- Использование формата WebP
- Ограничение разрешения

## 🚨 Если проблема остается

1. **Проверьте логи nginx**:
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

2. **Проверьте логи Flask**:
   ```bash
   # В терминале где запущен сервер
   ```

3. **Проверьте права доступа**:
   ```bash
   sudo chown -R www-data:www-data /home/nikolai/PycharmProjects/flask_server/static/uploads/
   sudo chmod 755 /home/nikolai/PycharmProjects/flask_server/static/uploads/
   ```

4. **Проверьте свободное место**:
   ```bash
   df -h
   ```

## 📞 Поддержка

Если проблема не решается:
1. Проверьте все логи
2. Убедитесь, что nginx перезапущен
3. Попробуйте другой браузер
4. Проверьте размер загружаемого файла 