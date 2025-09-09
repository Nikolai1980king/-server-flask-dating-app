# 🌐 Система ограничений по IP-адресу

## ✅ Что изменилось

Система ограничений переключена с отпечатков устройств на контроль по IP-адресу для более надежной работы.

## 🎯 Принцип работы

### 1. Определение IP-адреса
- Система автоматически определяет IP-адрес клиента
- Учитывает заголовки прокси (X-Forwarded-For, X-Real-IP)
- Использует request.remote_addr как fallback

### 2. Проверка ограничений
- При попытке создать анкету система проверяет IP-адрес
- Если с этого IP уже создана анкета - блокирует создание
- Перенаправляет пользователя на существующий профиль

### 3. Регистрация IP
- После успешного создания анкеты IP регистрируется в базе данных
- IP привязывается к созданному профилю

## 🗄️ База данных

### Обновленная таблица Device
```sql
CREATE TABLE device (
    id INTEGER PRIMARY KEY,
    device_fingerprint VARCHAR UNIQUE NOT NULL,
    client_ip VARCHAR NOT NULL,  -- НОВОЕ ПОЛЕ
    user_agent VARCHAR,
    screen_resolution VARCHAR,
    timezone VARCHAR,
    language VARCHAR,
    platform VARCHAR,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
    profile_id VARCHAR
);
```

## 🔧 Изменения в коде

### 1. Функция получения IP (строки 216-226)
```python
def get_client_ip(request):
    """Получает IP-адрес клиента с учетом прокси"""
    if request.headers.get('X-Forwarded-For'):
        ip = request.headers.get('X-Forwarded-For').split(',')[0].strip()
    elif request.headers.get('X-Real-IP'):
        ip = request.headers.get('X-Real-IP')
    else:
        ip = request.remote_addr
    return ip
```

### 2. Обновленная проверка ограничений (строки 245-265)
```python
def check_device_restriction(device_fingerprint, client_ip):
    """Проверяет, есть ли уже анкета для данного IP или отпечатка"""
    # Сначала проверяем по IP-адресу (более надежно)
    device_by_ip = Device.query.filter_by(client_ip=client_ip).first()
    
    if device_by_ip and device_by_ip.profile_id:
        profile = Profile.query.get(device_by_ip.profile_id)
        if profile:
            return True, device_by_ip.profile_id
    
    # Если по IP не найдено, проверяем по отпечатку
    device_by_fingerprint = Device.query.filter_by(device_fingerprint=device_fingerprint).first()
    
    if device_by_fingerprint and device_by_fingerprint.profile_id:
        profile = Profile.query.get(device_by_fingerprint.profile_id)
        if profile:
            return True, device_by_fingerprint.profile_id
    
    return False, None
```

### 3. Обновленная логика create_profile() (строки 1221-1239)
```python
# Создаем отпечаток устройства и получаем IP
device_fingerprint, client_ip = create_device_fingerprint(request)

# Проверяем ограничения по устройству (по IP и отпечатку)
has_existing_profile, existing_profile_id = check_device_restriction(device_fingerprint, client_ip)

if has_existing_profile:
    return jsonify({
        'success': False,
        'error': f'С этого IP-адреса ({client_ip}) уже создана анкета. Один пользователь = одна анкета.',
        'has_active_profile': True,
        'redirect_url': url_for('view_profile', id=existing_profile_id)
    }), 400
```

## 🧪 Тестирование

### Сценарии тестирования

1. **Первый вход с IP:**
   - Пользователь заходит на `/create`
   - Создает анкету успешно
   - IP регистрируется в базе

2. **Повторный вход с того же IP:**
   - Пользователь заходит на `/create` снова
   - Система обнаруживает существующую анкету по IP
   - Автоматически перенаправляет на профиль

3. **Вход с другого браузера на том же IP:**
   - Пользователь открывает другой браузер
   - Пытается создать анкету
   - Система блокирует создание (IP тот же)

4. **Вход с другого IP:**
   - Пользователь заходит с другого IP
   - Может создать новую анкету

## 🎉 Преимущества IP-контроля

✅ **Более надежно:** IP-адрес сложнее подделать чем отпечаток браузера
✅ **Работает с любыми браузерами:** Не зависит от User-Agent
✅ **Простота:** Легче отлаживать и мониторить
✅ **Безопасность:** Защищает от создания множественных анкет

## 🚀 Как использовать

1. **Запустите сервер:**
   ```bash
   python app.py
   ```

2. **Откройте тестовую страницу:**
   ```
   http://localhost:5000/test_device_restriction_system.html
   ```

3. **Протестируйте создание анкеты:**
   ```
   http://localhost:5000/create
   ```

4. **Попробуйте создать анкету снова** - система должна перенаправить на существующий профиль

## 📊 Мониторинг

- Используйте `/api/device-stats` для получения статистики
- Проверяйте таблицу `device` в базе данных
- Логи сервера показывают IP-адреса и проверки ограничений

## ⚠️ Важные замечания

- **NAT/Прокси:** Пользователи за одним NAT будут считаться одним IP
- **Динамические IP:** При смене IP пользователь сможет создать новую анкету
- **VPN/Прокси:** Пользователи с VPN будут иметь разные IP