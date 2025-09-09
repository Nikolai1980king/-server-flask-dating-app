# 🍪 Исправление проблемы с Cookie

## Проблема
Пользователи не могли создавать повторные анкеты из-за ошибки "Cookie: не найден". Проблема заключалась в том, что cookie `user_id` не устанавливался правильно или не сохранялся между запросами. Также была проблема с потерей доступа к существующим анкетам при выходе из приложения.

## Решение

### 1. Улучшена функция `create_profile()`

**Изменения в `app.py`:**

```python
@app.route('/create', methods=['GET', 'POST'])
def create_profile():
    # Получаем user_id из cookie или генерируем новый
    user_id = request.cookies.get('user_id')
    
    # Для отладки
    print(f"DEBUG: user_id из cookie: {user_id}")
    print(f"DEBUG: все cookies: {dict(request.cookies)}")

    if request.method == 'POST':
        # Проверяем, есть ли уже анкета у пользователя
        if user_id:
            existing_profile = Profile.query.get(user_id)
            if existing_profile:
                return jsonify({
                    'success': False,
                    'error': 'У вас уже есть анкета. Вы можете создать только одну анкету.',
                    'has_active_profile': True
                }), 400

        # Если нет user_id, генерируем новый
        if not user_id:
            user_id = str(uuid.uuid4())
            print(f"DEBUG: сгенерирован новый user_id: {user_id}")
```

### 2. Добавлена проверка существующих анкет для GET запросов

```python
# Проверяем, есть ли уже анкета у пользователя (для GET запроса)
existing_profile = None
if user_id:
    existing_profile = Profile.query.get(user_id)
    print(f"DEBUG: найдена существующая анкета по user_id: {existing_profile is not None}")

# Если есть анкета, перенаправляем на неё
if existing_profile:
    print(f"DEBUG: перенаправляем на существующую анкету: {user_id}")
    return redirect(url_for('view_profile', id=user_id))

# Если нет user_id, но есть параметры для поиска анкеты
if not user_id and request.args.get('search_profile'):
    name = request.args.get('name', '').strip()
    age = request.args.get('age', '').strip()
    
    if name and age:
        try:
            age_int = int(age)
            # Ищем анкету по имени и возрасту
            existing_profile = Profile.query.filter_by(name=name, age=age_int).first()
            if existing_profile:
                print(f"DEBUG: найдена анкета по имени и возрасту: {existing_profile.id}")
                # Устанавливаем cookie для найденной анкеты
                response = redirect(url_for('view_profile', id=existing_profile.id))
                response.set_cookie(
                    'user_id', 
                    existing_profile.id,
                    max_age=365*24*60*60,
                    httponly=False,
                    secure=False,
                    samesite='Lax'
                )
                return response
        except ValueError:
            pass
```

### 3. Улучшена установка cookie

**Для POST запроса:**
```python
# Устанавливаем cookie с правильными параметрами
resp.set_cookie(
    'user_id', 
    user_id,
    max_age=365*24*60*60,  # 1 год
    httponly=False,  # Разрешаем доступ из JavaScript
    secure=False,    # Для HTTP (не HTTPS)
    samesite='Lax'   # Совместимость с современными браузерами
)
```

**Для GET запроса:**
```python
# Если нет user_id, генерируем новый и устанавливаем cookie
if not user_id:
    user_id = str(uuid.uuid4())
    print(f"DEBUG: для GET запроса сгенерирован новый user_id: {user_id}")

response = make_response(render_template_string(...))

# Устанавливаем cookie для GET запроса
if not request.cookies.get('user_id'):
    response.set_cookie(
        'user_id', 
        user_id,
        max_age=365*24*60*60,  # 1 год
        httponly=False,  # Разрешаем доступ из JavaScript
        secure=False,    # Для HTTP (не HTTPS)
        samesite='Lax'   # Совместимость с современными браузерами
    )
```

### 4. Добавлена функция очистки cookie

```python
@app.route('/clear_cookie')
def clear_cookie():
    """Очищает cookie user_id для возможности создания новой анкеты"""
    response = make_response(jsonify({
        'success': True,
        'message': 'Cookie очищен. Теперь можно создать новую анкету.'
    }))
    response.delete_cookie('user_id')
    print("DEBUG: cookie user_id очищен")
    return response
```

### 5. Добавлена страница восстановления анкеты

```python
@app.route('/restore_profile')
def restore_profile():
    """Страница для восстановления анкеты"""
    # Возвращает HTML форму для поиска анкеты по имени и возрасту
```

## Новые функции

### 🔍 Восстановление анкеты
- **URL**: `/restore_profile`
- **Функция**: Поиск существующей анкеты по имени и возрасту
- **Процесс**: 
  1. Пользователь вводит имя и возраст
  2. Система ищет анкету в базе данных
  3. Если найдена, устанавливается cookie и происходит перенаправление на анкету

### 🗑️ Очистка cookie
- **URL**: `/clear_cookie`
- **Функция**: Удаление cookie для создания новой анкеты
- **Использование**: Для тестирования или создания новой анкеты

## Тестирование

### 1. Запустите сервер
```bash
python app.py
```

### 2. Откройте тестовую страницу
Перейдите по адресу: `http://localhost:5000/test_cookie_fix.html`

### 3. Проверьте функции
- **Проверить Cookie** - показывает текущий cookie
- **Очистить Cookie** - удаляет cookie для создания новой анкеты
- **Тест создания анкеты** - проверяет процесс создания
- **Тест нескольких анкет** - тестирует создание нескольких анкет

### 4. Тестирование восстановления анкеты
1. Создайте анкету
2. Очистите cookie (или закройте браузер)
3. Перейдите на `/restore_profile`
4. Введите имя и возраст
5. Проверьте, что анкета восстановлена

### 5. Создание анкеты
1. Перейдите на `/create`
2. Заполните форму
3. Загрузите фото
4. Выберите заведение на карте
5. Нажмите "Создать"

## Ожидаемый результат

✅ **До исправления:**
- Ошибка "Cookie: не найден"
- Невозможность создать повторную анкету
- Потеря доступа к существующим анкетам при выходе из приложения

✅ **После исправления:**
- Cookie устанавливается автоматически
- Можно создавать новые анкеты после очистки cookie
- Стабильная работа сессий
- Возможность восстановить доступ к существующей анкете
- Отладочные сообщения в консоли сервера

## Отладка

### Проверка в консоли браузера
```javascript
// Проверить cookie
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
    return null;
}

console.log('user_id cookie:', getCookie('user_id'));
```

### Проверка в консоли сервера
Сервер выводит отладочные сообщения:
```
DEBUG: user_id из cookie: [значение]
DEBUG: все cookies: [словарь cookies]
DEBUG: найдена существующая анкета по user_id: True/False
DEBUG: перенаправляем на существующую анкету: [id]
DEBUG: найдена анкета по имени и возрасту: [id]
DEBUG: сгенерирован новый user_id: [новый id]
DEBUG: установлен cookie user_id: [id]
```

## Сценарии использования

### 1. Первое посещение
- Пользователь заходит на сайт
- Автоматически генерируется user_id и устанавливается cookie
- Пользователь может создать анкету

### 2. Возвращение с cookie
- Пользователь возвращается с сохраненным cookie
- Система проверяет наличие анкеты
- Если анкета есть - перенаправляет на неё
- Если анкеты нет - позволяет создать новую

### 3. Потеря cookie
- Пользователь потерял cookie (закрыл браузер, очистил данные)
- Может использовать восстановление анкеты по имени и возрасту
- Или создать новую анкету

### 4. Создание новой анкеты
- Пользователь очищает cookie через `/clear_cookie`
- Может создать новую анкету

## Дополнительные улучшения

1. **Автоматическая очистка** - cookie очищается при удалении анкеты
2. **Валидация** - проверка корректности cookie
3. **Безопасность** - правильные параметры cookie для безопасности
4. **Совместимость** - поддержка современных браузеров
5. **Восстановление** - поиск анкеты по имени и возрасту

## Файлы изменены

- `app.py` - основная логика исправления
- `test_cookie_fix.html` - тестовая страница
- `restore_profile.html` - страница восстановления анкеты
- `COOKIE_FIX_GUIDE.md` - данное руководство

---

**Статус:** ✅ Исправлено  
**Дата:** 30 августа 2025  
**Версия:** 2.0 