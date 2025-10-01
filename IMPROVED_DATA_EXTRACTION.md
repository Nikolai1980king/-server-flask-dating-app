# 🔧 Улучшение извлечения данных из балунов

## 🚨 Проблема

Файл сохраняется, но информация не извлекается корректно:
```
НАЗВАНИЕ: Неизвестное заведение
АДРЕС: Адрес не указан
ТЕЛЕФОН: Телефон не указан
ВЕБ-САЙТ: https://yandex.ru/maps/?orgpage%5Bid%5D=58207879702&amp;utm_source=api-maps&amp;from=api-maps
ЧАСЫ РАБОТЫ: Часы работы не указаны
РЕЙТИНГ: Рейтинг не указан
КОЛИЧЕСТВО ОТЗЫВОВ: Отзывы не указаны
ТИП: venue
ОПИСАНИЕ: Описание не указано

КООРДИНАТЫ:
Широта: None
Долгота: None
```

## ✅ Улучшения внесены

### 1. **Улучшенное извлечение geoObject данных**

Обновлена функция `extractGeoObjectData()`:

```javascript
function extractGeoObjectData() {
    const balloonData = myMap.balloon.getData();
    const geoObject = balloonData.geoObject;
    
    if (!geoObject) {
        addLog('⚠️ geoObject не найден в данных балуна', 'warning');
        return {};
    }

    try {
        // Безопасное извлечение свойств с логированием
        const safeProperties = {};
        try {
            const properties = geoObject.properties.getAll();
            addLog(`📋 Найдено ${Object.keys(properties).length} свойств geoObject`, 'info');
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
        } catch (e) {
            console.warn('Не удалось получить свойства geoObject:', e);
            addLog('⚠️ Не удалось получить свойства geoObject', 'warning');
        }

        // Безопасное извлечение координат
        let lat = null, lng = null;
        try {
            const geometry = geoObject.geometry.getCoordinates();
            if (geometry && Array.isArray(geometry) && geometry.length >= 2) {
                lat = geometry[0];
                lng = geometry[1];
                addLog(`📍 Координаты: ${lat}, ${lng}`, 'info');
            }
        } catch (e) {
            console.warn('Не удалось получить координаты:', e);
            addLog('⚠️ Не удалось получить координаты', 'warning');
        }

        // Безопасное извлечение адреса
        let address = 'Адрес не указан';
        try {
            const addressLine = geoObject.getAddressLine();
            if (addressLine && typeof addressLine === 'string') {
                address = addressLine;
                addLog(`🏠 Адрес: ${address}`, 'info');
            }
        } catch (e) {
            console.warn('Не удалось получить адрес:', e);
            addLog('⚠️ Не удалось получить адрес', 'warning');
        }

        // Попытка получить название из разных источников
        let name = 'Неизвестное заведение';
        try {
            // Сначала пробуем получить из свойств
            if (safeProperties.name) {
                name = safeProperties.name;
            } else if (safeProperties.hint) {
                name = safeProperties.hint;
            } else if (safeProperties.title) {
                name = safeProperties.title;
            } else if (safeProperties.text) {
                name = safeProperties.text;
            } else {
                // Пробуем получить из самого geoObject
                const geoObjectName = geoObject.get('name') || geoObject.get('hint') || geoObject.get('title');
                if (geoObjectName) {
                    name = geoObjectName;
                }
            }
            addLog(`🏪 Название: ${name}`, 'info');
        } catch (e) {
            console.warn('Не удалось получить название:', e);
        }
        
        return {
            name: name,
            address: address,
            phone: safeProperties.phone || safeProperties.Phones || 'Телефон не указан',
            website: safeProperties.website || safeProperties.url || 'Сайт не указан',
            hours: safeProperties.hours || safeProperties.working_hours || 'Часы работы не указаны',
            rating: safeProperties.rating || safeProperties.rating_value || 'Рейтинг не указан',
            reviews_count: safeProperties.reviews_count || safeProperties.reviews || 'Отзывы не указаны',
            description: safeProperties.description || safeProperties.comment || 'Описание не указано',
            type: safeProperties.kind || safeProperties.type || 'venue',
            lat: lat,
            lng: lng,
            full_properties: safeProperties
        };
    } catch (error) {
        console.error('Ошибка при извлечении данных geoObject:', error);
        addLog(`❌ Ошибка при извлечении данных geoObject: ${error.message}`, 'error');
        return {
            name: 'Ошибка извлечения данных',
            address: 'Не удалось получить адрес',
            phone: 'Не указан',
            website: 'Не указан',
            hours: 'Не указаны',
            rating: 'Не указан',
            reviews_count: 'Не указаны',
            description: 'Ошибка при извлечении данных',
            type: 'venue',
            lat: null,
            lng: null,
            full_properties: {}
        };
    }
}
```

### 2. **Улучшенное извлечение HTML контента**

Обновлена функция `extractHTMLContent()`:

```javascript
function extractHTMLContent() {
    try {
        // Расширенный список селекторов
        const selectors = [
            '.ymaps-2-1-79-balloon__content',
            '.ymaps-balloon__content',
            '.balloon-content',
            '.balloon__content',
            '.ymaps-2-1-79-balloon__content-body',
            '.ymaps-2-1-79-balloon__content-body__content',
            '.ymaps-2-1-79-balloon__content-body__content__content',
            '.ymaps-2-1-79-balloon__content-body__content__content__content'
        ];
        
        for (let selector of selectors) {
            try {
                const content = document.querySelector(selector);
                if (content && content.innerHTML) {
                    addLog(`🌐 HTML контент найден через селектор: ${selector}`, 'info');
                    addLog(`📏 Размер HTML: ${content.innerHTML.length} символов`, 'info');
                    return content.innerHTML;
                }
            } catch (e) {
                console.warn(`Ошибка при поиске селектора ${selector}:`, e);
                continue;
            }
        }
        
        // Альтернативный метод через overlay
        try {
            if (myMap.balloon && myMap.balloon.isOpen()) {
                const balloonElement = myMap.balloon.getData().geoObject;
                if (balloonElement && balloonElement.getOverlay) {
                    const overlay = balloonElement.getOverlay();
                    if (overlay && overlay.getData) {
                        const balloonContent = overlay.getData();
                        if (balloonContent && balloonContent.innerHTML) {
                            addLog('🌐 HTML контент найден через overlay', 'info');
                            return balloonContent.innerHTML;
                        }
                    }
                }
            }
        } catch (e) {
            console.warn('Не удалось получить контент через overlay:', e);
        }
        
        addLog('⚠️ HTML контент не найден', 'warning');
        return '';
    } catch (error) {
        console.error('Ошибка при извлечении HTML контента:', error);
        addLog(`❌ Ошибка при извлечении HTML контента: ${error.message}`, 'error');
        return '';
    }
}
```

### 3. **Улучшенная отправка данных**

Обновлена функция `sendDataToServer()`:

```javascript
function sendDataToServer(geoObjectData, balloonData, htmlContent) {
    addLog('📤 Отправка данных на сервер...', 'info');

    // Увеличенные лимиты
    const limitedHtmlContent = htmlContent ? htmlContent.substring(0, 2000) : '';
    
    // Включаем больше полей
    const safeData = {
        geoObject: {
            name: geoObjectData.name,
            address: geoObjectData.address,
            phone: geoObjectData.phone,
            website: geoObjectData.website,
            hours: geoObjectData.hours,
            rating: geoObjectData.rating,
            reviews_count: geoObjectData.reviews_count,
            description: geoObjectData.description,
            type: geoObjectData.type,
            lat: geoObjectData.lat,
            lng: geoObjectData.lng,
            full_properties: geoObjectData.full_properties || {}
        },
        balloonData: {
            content: balloonData.content ? balloonData.content.substring(0, 1000) : '',
            properties: balloonData.properties || {}
        },
        htmlContent: limitedHtmlContent
    };

    try {
        let jsonData = safeStringify(safeData);
        
        addLog(`📏 Размер данных для отправки: ${jsonData.length} символов`, 'info');
        
        // Увеличенный лимит
        if (jsonData.length > 100000) { // 100KB лимит
            addLog('⚠️ Данные слишком большие, отправляем только основную информацию', 'warning');
            const minimalData = {
                geoObject: {
                    name: geoObjectData.name,
                    address: geoObjectData.address,
                    phone: geoObjectData.phone,
                    website: geoObjectData.website,
                    lat: geoObjectData.lat,
                    lng: geoObjectData.lng
                },
                balloonData: {},
                htmlContent: ''
            };
            jsonData = safeStringify(minimalData);
            addLog(`📏 Размер сокращенных данных: ${jsonData.length} символов`, 'info');
        }
        
        // ... отправка данных
    } catch (error) {
        console.error('Ошибка при подготовке данных:', error);
        addLog(`❌ Ошибка подготовки данных: ${error.message}`, 'error');
        showNotification('❌ Ошибка при подготовке данных');
    }
}
```

## 🔍 Что было улучшено

### 1. **Подробное логирование**
- Логирование каждого этапа извлечения данных
- Информация о количестве найденных свойств
- Размер извлеченного HTML контента
- Размер отправляемых данных

### 2. **Расширенный поиск названий**
- Поиск названия в разных полях: `name`, `hint`, `title`, `text`
- Альтернативные методы получения названия
- Fallback значения при ошибках

### 3. **Улучшенное извлечение HTML**
- Расширенный список селекторов
- Альтернативный метод через overlay
- Подробная информация о найденном контенте

### 4. **Больше полей данных**
- Включение `full_properties` в отправляемые данные
- Увеличенные лимиты для HTML контента
- Сохранение свойств балуна

## 🧪 Тестирование улучшений

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

### 4. Проверьте логи:
Теперь в логе должно быть больше информации:
```
09:35:30: 📋 Найдено 15 свойств geoObject
09:35:30: 🏪 Название: Кафе "Уютное место"
09:35:30: 🏠 Адрес: ул. Тверская, 15
09:35:30: 📍 Координаты: 55.7568, 37.6186
09:35:30: 🌐 HTML контент найден через селектор: .ymaps-2-1-79-balloon__content
09:35:30: 📏 Размер HTML: 1250 символов
09:35:30: 📏 Размер данных для отправки: 45678 символов
```

## 📊 Ожидаемые результаты

### ✅ Успешное извлечение (УЛУЧШЕНО):
```
НАЗВАНИЕ: Кафе "Уютное место"
АДРЕС: ул. Тверская, 15, Москва
ТЕЛЕФОН: +7 (495) 123-45-67
ВЕБ-САЙТ: https://cafe-uyut.ru
ЧАСЫ РАБОТЫ: 09:00 - 23:00
РЕЙТИНГ: 4.5
КОЛИЧЕСТВО ОТЗЫВОВ: 127
ТИП: venue
ОПИСАНИЕ: Уютное кафе с домашней кухней

КООРДИНАТЫ:
Широта: 55.7568
Долгота: 37.6186
```

### ❌ Если данные все еще не извлекаются:
- Проверьте логи в консоли браузера
- Убедитесь, что балун действительно открыт
- Проверьте, что заведение имеет данные в Яндекс.Картах

## 🔧 Дополнительные улучшения

### 1. **Отладка в консоли браузера**
```javascript
// Проверьте данные балуна
console.log('Balloon data:', myMap.balloon.getData());

// Проверьте geoObject
const geoObject = myMap.balloon.getData().geoObject;
console.log('GeoObject:', geoObject);

// Проверьте свойства
const properties = geoObject.properties.getAll();
console.log('Properties:', properties);
```

### 2. **Проверка HTML контента**
```javascript
// Проверьте HTML контент
const selectors = ['.ymaps-2-1-79-balloon__content', '.ymaps-balloon__content'];
for (let selector of selectors) {
    const content = document.querySelector(selector);
    if (content) {
        console.log(`Found content with ${selector}:`, content.innerHTML);
    }
}
```

## ✅ Заключение

Извлечение данных значительно улучшено! Теперь парсер:

- ✅ Подробно логирует каждый этап извлечения
- ✅ Ищет названия в разных полях
- ✅ Использует расширенные селекторы для HTML
- ✅ Отправляет больше данных на сервер
- ✅ Предоставляет детальную отладочную информацию

**Попробуйте извлечь данные снова - теперь должно быть больше информации! 🎈** 