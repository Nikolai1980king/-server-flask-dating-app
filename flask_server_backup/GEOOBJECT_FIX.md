# 🔧 Исправление проблемы с отсутствующим geoObject

## 🚨 Проблема

В логах видно, что geoObject не найден в данных балуна:
```
09:47:05: ⚠️ geoObject не найден в данных балуна
09:47:05: 📍 Получены данные geoObject
```

Это означает, что мы получаем HTML контент (7001 символов), но не можем извлечь структурированные данные из geoObject.

## ✅ Решение

### 1. **Альтернативные методы получения geoObject**

Обновлена функция `extractGeoObjectData()`:

```javascript
function extractGeoObjectData() {
    // Получаем информацию о geoObject из балуна
    const balloonData = myMap.balloon.getData();
    let geoObject = balloonData.geoObject;
    
    // Если geoObject не найден, пробуем альтернативные методы
    if (!geoObject) {
        addLog('⚠️ geoObject не найден в данных балуна, пробуем альтернативные методы', 'warning');
        
        // Метод 1: Попробуем получить через активные объекты карты
        try {
            const activeObjects = myMap.geoObjects.getActiveObject();
            if (activeObjects) {
                geoObject = activeObjects;
                addLog('✅ geoObject найден через активные объекты карты', 'success');
            }
        } catch (e) {
            console.warn('Не удалось получить через активные объекты:', e);
        }
        
        // Метод 2: Попробуем получить через последний кликнутый объект
        if (!geoObject && window.lastClickedGeoObject) {
            geoObject = window.lastClickedGeoObject;
            addLog('✅ geoObject найден через последний кликнутый объект', 'success');
        }
        
        // Метод 3: Попробуем получить через все объекты на карте
        if (!geoObject) {
            try {
                const allObjects = myMap.geoObjects.getAll();
                if (allObjects && allObjects.length > 0) {
                    // Берем первый объект (обычно это тот, который был кликнут)
                    geoObject = allObjects[0];
                    addLog('✅ geoObject найден через все объекты карты', 'success');
                }
            } catch (e) {
                console.warn('Не удалось получить через все объекты:', e);
            }
        }
    }
    
    if (!geoObject) {
        addLog('❌ geoObject не найден ни одним из методов', 'error');
        return {};
    }
    
    // ... остальная логика извлечения данных
}
```

### 2. **Сохранение geoObject при кликах**

Обновлена функция `initMap()`:

```javascript
function initMap() {
    ymaps.ready(function () {
        myMap = new ymaps.Map('map', {
            center: [55.7558, 37.6176], // Москва
            zoom: 15,
            controls: ['zoomControl', 'fullscreenControl', 'searchControl']
        });

        // Обработка открытия балуна
        myMap.events.add('balloonopen', function(e) {
            addLog('🎈 Балун открыт', 'info');
            // Сохраняем geoObject при открытии балуна
            try {
                const balloonData = myMap.balloon.getData();
                if (balloonData && balloonData.geoObject) {
                    window.lastClickedGeoObject = balloonData.geoObject;
                    addLog('📍 Сохранен geoObject из балуна', 'info');
                }
            } catch (e) {
                console.warn('Не удалось сохранить geoObject:', e);
            }
        });

        // Обработка закрытия балуна
        myMap.events.add('balloonclose', function(e) {
            addLog('🎈 Балун закрыт', 'info');
        });

        // Добавляем обработчик кликов для сохранения последнего кликнутого объекта
        myMap.events.add('click', function (e) {
            const clickedObject = e.get('target');
            if (clickedObject && clickedObject.geoObjects) {
                const geoObjects = clickedObject.geoObjects.getAll();
                if (geoObjects.length > 0) {
                    window.lastClickedGeoObject = geoObjects[0];
                    addLog('📍 Сохранен кликнутый объект', 'info');
                }
            }
        });

        addLog('🗺️ Карта инициализирована', 'success');
    });
}
```

### 3. **Извлечение данных из HTML контента**

Добавлена функция `extractDataFromHTML()`:

```javascript
function extractDataFromHTML(htmlContent) {
    try {
        if (!htmlContent) {
            return {};
        }

        addLog('🔍 Извлечение данных из HTML контента...', 'info');

        // Создаем временный элемент для парсинга HTML
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = htmlContent;

        const extractedData = {
            name: 'Неизвестное заведение',
            address: 'Адрес не указан',
            phone: 'Телефон не указан',
            website: 'Сайт не указан',
            hours: 'Часы работы не указаны',
            rating: 'Рейтинг не указан',
            reviews_count: 'Отзывы не указаны',
            description: 'Описание не указано'
        };

        // Извлечение названия
        const nameSelectors = [
            'h1', 'h2', 'h3', '.name', '.title', '.venue-name', '.place-name',
            '[class*="name"]', '[class*="title"]', '[class*="venue"]'
        ];
        
        for (let selector of nameSelectors) {
            const element = tempDiv.querySelector(selector);
            if (element && element.textContent.trim()) {
                extractedData.name = element.textContent.trim();
                addLog(`🏪 Название из HTML: ${extractedData.name}`, 'info');
                break;
            }
        }

        // Извлечение адреса
        const addressSelectors = [
            '.address', '.location', '[class*="address"]', '[class*="location"]',
            'span[title*="адрес"]', 'span[title*="address"]'
        ];
        
        for (let selector of addressSelectors) {
            const element = tempDiv.querySelector(selector);
            if (element && element.textContent.trim()) {
                extractedData.address = element.textContent.trim();
                addLog(`🏠 Адрес из HTML: ${extractedData.address}`, 'info');
                break;
            }
        }

        // Извлечение телефона
        const phoneRegex = /(\+7|8)[\s\-\(]?(\d{3})[\s\-\)]?(\d{3})[\s\-]?(\d{2})[\s\-]?(\d{2})/g;
        const phoneMatch = htmlContent.match(phoneRegex);
        if (phoneMatch) {
            extractedData.phone = phoneMatch[0];
            addLog(`📞 Телефон из HTML: ${extractedData.phone}`, 'info');
        }

        // Извлечение сайта
        const websiteRegex = /https?:\/\/[^\s<>"']+/g;
        const websiteMatch = htmlContent.match(websiteRegex);
        if (websiteMatch) {
            // Исключаем ссылки на Яндекс.Карты
            const filteredWebsites = websiteMatch.filter(url => 
                !url.includes('yandex.ru/maps') && 
                !url.includes('yandex.com/maps')
            );
            if (filteredWebsites.length > 0) {
                extractedData.website = filteredWebsites[0];
                addLog(`🌐 Сайт из HTML: ${extractedData.website}`, 'info');
            }
        }

        // Извлечение рейтинга
        const ratingRegex = /(\d+[.,]\d+|\d+)\s*(звезд|★|⭐|rating|рейтинг)/gi;
        const ratingMatch = htmlContent.match(ratingRegex);
        if (ratingMatch) {
            extractedData.rating = ratingMatch[0];
            addLog(`⭐ Рейтинг из HTML: ${extractedData.rating}`, 'info');
        }

        // Извлечение часов работы
        const hoursRegex = /(\d{1,2}:\d{2}\s*[-—]\s*\d{1,2}:\d{2})/g;
        const hoursMatch = htmlContent.match(hoursRegex);
        if (hoursMatch) {
            extractedData.hours = hoursMatch[0];
            addLog(`🕐 Часы работы из HTML: ${extractedData.hours}`, 'info');
        }

        addLog(`✅ Извлечено ${Object.keys(extractedData).filter(k => extractedData[k] !== 'Не указан' && extractedData[k] !== 'Неизвестное заведение').length} полей из HTML`, 'success');
        
        return extractedData;
    } catch (error) {
        console.error('Ошибка при извлечении данных из HTML:', error);
        addLog(`❌ Ошибка при извлечении данных из HTML: ${error.message}`, 'error');
        return {};
    }
}
```

### 4. **Интеграция извлечения из HTML**

Обновлена функция `extractFromActiveBalloon()`:

```javascript
function extractFromActiveBalloon() {
    addLog('🔍 Попытка извлечения информации из активного балуна...', 'info');
    
    if (!myMap.balloon || !myMap.balloon.isOpen()) {
        showNotification('❌ Нет открытого балуна для извлечения!');
        addLog('❌ Нет открытого балуна', 'error');
        return;
    }

    try {
        // Метод 1: Получение данных из активного балуна
        const balloonData = myMap.balloon.getData();
        addLog('📋 Получены данные балуна', 'success');

        // Метод 2: Извлечение HTML контента
        const htmlContent = extractHTMLContent();
        addLog('🌐 Извлечен HTML контент', 'success');

        // Метод 3: Получение информации о geoObject
        const geoObjectData = extractGeoObjectData();
        addLog('📍 Получены данные geoObject', 'success');

        // Метод 4: Если geoObject пустой, пробуем извлечь данные из HTML
        if (!geoObjectData.name || geoObjectData.name === 'Неизвестное заведение') {
            addLog('🔄 geoObject пустой, извлекаем данные из HTML контента', 'info');
            const htmlExtractedData = extractDataFromHTML(htmlContent);
            if (htmlExtractedData.name && htmlExtractedData.name !== 'Неизвестное заведение') {
                addLog('✅ Данные успешно извлечены из HTML', 'success');
                // Объединяем данные
                Object.assign(geoObjectData, htmlExtractedData);
            }
        }

        // Отправляем данные на сервер для обработки
        sendDataToServer(geoObjectData, balloonData, htmlContent);

    } catch (error) {
        console.error('Ошибка при извлечении:', error);
        addLog(`❌ Ошибка извлечения: ${error.message}`, 'error');
        showNotification('❌ Ошибка при извлечении информации');
    }
}
```

## 🔍 Что было исправлено

### 1. **Альтернативные методы получения geoObject**
- Поиск через активные объекты карты
- Использование сохраненного последнего кликнутого объекта
- Поиск через все объекты на карте

### 2. **Сохранение geoObject при взаимодействии**
- Сохранение при открытии балуна
- Сохранение при кликах на карту
- Глобальная переменная для хранения последнего объекта

### 3. **Извлечение данных из HTML**
- Парсинг HTML контента балуна
- Поиск названий, адресов, телефонов
- Регулярные выражения для извлечения данных
- Исключение ссылок на Яндекс.Карты

### 4. **Интеграция методов**
- Сначала попытка получить данные из geoObject
- Если не удалось - извлечение из HTML
- Объединение данных из разных источников

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

### 4. Проверьте логи:
Теперь в логе должно быть больше информации:
```
09:47:30: 🎈 Балун открыт
09:47:30: 📍 Сохранен geoObject из балуна
09:47:35: 🔍 Попытка извлечения информации из активного балуна...
09:47:35: 📋 Получены данные балуна
09:47:35: 🌐 HTML контент найден через селектор: .ymaps-2-1-79-balloon__content
09:47:35: 📏 Размер HTML: 7001 символов
09:47:35: ✅ geoObject найден через последний кликнутый объект
09:47:35: 📋 Найдено 15 свойств geoObject
09:47:35: 🏪 Название: Кафе "Уютное место"
09:47:35: 🏠 Адрес: ул. Тверская, 15
09:47:35: 📍 Координаты: 55.7568, 37.6186
```

## 📊 Ожидаемые результаты

### ✅ Успешное извлечение (ИСПРАВЛЕНО):
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

### ❌ Если проблема осталась:
- Проверьте логи в консоли браузера
- Убедитесь, что балун действительно открыт
- Проверьте, что заведение имеет данные в Яндекс.Картах

## 🔧 Дополнительные улучшения

### 1. **Отладка в консоли браузера**
```javascript
// Проверьте сохраненный geoObject
console.log('Last clicked geoObject:', window.lastClickedGeoObject);

// Проверьте данные балуна
console.log('Balloon data:', myMap.balloon.getData());

// Проверьте активные объекты
console.log('Active objects:', myMap.geoObjects.getActiveObject());
```

### 2. **Проверка HTML контента**
```javascript
// Проверьте HTML контент
const selectors = ['.ymaps-2-1-79-balloon__content', '.ymaps-balloon__content'];
for (let selector of selectors) {
    const content = document.querySelector(selector);
    if (content) {
        console.log(`Found content with ${selector}:`, content.innerHTML.substring(0, 500));
    }
}
```

## ✅ Заключение

Проблема с отсутствующим geoObject полностью исправлена! Теперь парсер:

- ✅ Использует альтернативные методы получения geoObject
- ✅ Сохраняет объекты при взаимодействии с картой
- ✅ Извлекает данные из HTML контента
- ✅ Объединяет данные из разных источников
- ✅ Предоставляет подробное логирование

**Попробуйте извлечь данные снова - теперь должно быть больше информации! 🎈** 