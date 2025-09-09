# 🔧 Исправление ошибки циклических ссылок в парсере балунов

## 🚨 Проблема

Ошибка: `Converting circular structure to JSON --> starting at object with constructor 'f' | property '_freezer' -> object with constructor 'n' --- property '_context' closes the circle`

Эта ошибка возникает при попытке сериализации объектов Яндекс.Карт в JSON, которые содержат циклические ссылки.

## ✅ Решение

### 1. Безопасная сериализация на сервере

Добавлена функция `safe_json_serialize()` в `app.py`:

```python
def safe_json_serialize(obj):
    """Безопасная сериализация объектов в JSON с обработкой циклических ссылок"""
    def serialize_helper(obj, visited=None):
        if visited is None:
            visited = set()
        
        obj_id = id(obj)
        if obj_id in visited:
            return f"<circular reference to {type(obj).__name__}>"
        
        visited.add(obj_id)
        
        try:
            if isinstance(obj, dict):
                return {k: serialize_helper(v, visited) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_helper(item, visited) for item in obj]
            elif isinstance(obj, (str, int, float, bool, type(None))):
                return obj
            elif hasattr(obj, '__dict__'):
                # Для объектов с атрибутами
                result = {}
                for key, value in obj.__dict__.items():
                    if not key.startswith('_'):  # Исключаем приватные атрибуты
                        result[key] = serialize_helper(value, visited)
                return result
            else:
                return f"<{type(obj).__name__} object>"
        except Exception as e:
            return f"<error serializing {type(obj).__name__}: {str(e)}>"
        finally:
            visited.discard(obj_id)
    
    return serialize_helper(obj)
```

### 2. Безопасная обработка на клиенте

Обновлена функция `extractGeoObjectData()` в `balloon_parser.html`:

```javascript
function extractGeoObjectData() {
    const balloonData = myMap.balloon.getData();
    const geoObject = balloonData.geoObject;
    
    if (!geoObject) {
        return {};
    }

    try {
        const properties = geoObject.properties.getAll();
        const geometry = geoObject.geometry.getCoordinates();
        
        // Безопасное извлечение свойств
        const safeProperties = {};
        for (let key in properties) {
            try {
                const value = properties[key];
                if (typeof value === 'string' || typeof value === 'number' || typeof value === 'boolean') {
                    safeProperties[key] = value;
                } else {
                    safeProperties[key] = String(value);
                }
            } catch (e) {
                safeProperties[key] = '<error reading property>';
            }
        }
        
        return {
            name: safeProperties.name || safeProperties.hint || 'Неизвестное заведение',
            address: geoObject.getAddressLine() || safeProperties.address || 'Адрес не указан',
            // ... остальные поля
        };
    } catch (error) {
        console.error('Ошибка при извлечении данных geoObject:', error);
        return {
            name: 'Ошибка извлечения данных',
            // ... значения по умолчанию
        };
    }
}
```

### 3. Безопасная отправка данных

Обновлена функция `sendDataToServer()`:

```javascript
function sendDataToServer(geoObjectData, balloonData, htmlContent) {
    // Безопасная подготовка данных для отправки
    const safeData = {
        geoObject: geoObjectData,
        balloonData: {
            content: balloonData.content || '',
            properties: balloonData.properties || {}
        },
        htmlContent: htmlContent || ''
    };

    try {
        fetch('/api/extract-balloon-data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(safeData)
        })
        // ... обработка ответа
    } catch (error) {
        console.error('Ошибка при подготовке данных:', error);
        addLog(`❌ Ошибка подготовки данных: ${error.message}`, 'error');
    }
}
```

## 🔍 Что было исправлено

### 1. **Циклические ссылки**
- Добавлена функция для отслеживания уже посещенных объектов
- Циклические ссылки заменяются на описательные сообщения

### 2. **Безопасная сериализация**
- Проверка типов данных перед сериализацией
- Обработка исключений при работе с объектами
- Исключение приватных атрибутов

### 3. **Улучшенная обработка ошибок**
- Try-catch блоки вокруг критических операций
- Логирование ошибок для отладки
- Fallback значения при ошибках

## 🧪 Тестирование исправления

### 1. Запустите приложение:
```bash
python app.py
```

### 2. Откройте парсер:
```
http://localhost:5000/balloon-parser
```

### 3. Протестируйте извлечение:
- Создайте тестовые заведения
- Кликните на метку
- Нажмите "🎯 Извлечь информацию из балуна"

### 4. Проверьте результаты:
- ✅ Информация извлекается без ошибок
- ✅ Данные сохраняются в файл
- ✅ В логе нет ошибок циклических ссылок

## 📊 Ожидаемые результаты

### До исправления:
```
❌ Ошибка извлечения: Converting circular structure to JSON
```

### После исправления:
```
✅ Данные успешно извлечены и обработаны
✅ Файл сохранен: venue_info_20250127_143031.txt
```

## 🔧 Дополнительные улучшения

### 1. **Логирование**
- Добавлено подробное логирование операций
- Отслеживание ошибок в консоли браузера

### 2. **Валидация данных**
- Проверка типов данных перед обработкой
- Безопасное преобразование значений

### 3. **Fallback механизмы**
- Значения по умолчанию при ошибках
- Graceful degradation функциональности

## 🚨 Профилактика

### 1. **Регулярное тестирование**
- Проверяйте парсер после обновлений
- Тестируйте с разными типами заведений

### 2. **Мониторинг ошибок**
- Следите за логами в консоли браузера
- Проверяйте файлы сохранения

### 3. **Обновления API**
- Следите за изменениями в API Яндекс.Карт
- Адаптируйте код при необходимости

## ✅ Заключение

Ошибка циклических ссылок успешно исправлена! Парсер теперь:

- ✅ Безопасно обрабатывает объекты Яндекс.Карт
- ✅ Извлекает данные без ошибок сериализации
- ✅ Сохраняет информацию в файлы
- ✅ Предоставляет подробное логирование

Парсер готов к использованию! 🎈 