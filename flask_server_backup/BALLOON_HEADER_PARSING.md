# 🔧 Исправление парсинга заголовков балуна

## 🚨 Проблема

Названия заведений не извлекаются, потому что они находятся в верхней шапке/заголовке балуна, которую мы не парсили. Мы парсили только основной контент балуна, но не его заголовок.

## ✅ Решение

### 1. **Парсинг заголовка балуна**

Обновлена функция `extractHTMLContent()` для извлечения как заголовка, так и контента:

```javascript
function extractHTMLContent() {
    try {
        let fullHTML = '';
        
        // 1. Сначала ищем заголовок/шапку балуна
        const headerSelectors = [
            '.ymaps-2-1-79-balloon__header',
            '.ymaps-balloon__header',
            '.balloon-header',
            '.balloon__header',
            '.ymaps-2-1-79-balloon__title',
            '.ymaps-balloon__title',
            '.balloon-title',
            '.balloon__title',
            '.ymaps-2-1-79-balloon__header-content',
            '.ymaps-balloon__header-content',
            '.balloon-header-content',
            '.balloon__header-content'
        ];
        
        for (let selector of headerSelectors) {
            try {
                const header = document.querySelector(selector);
                if (header && header.innerHTML) {
                    addLog(`🎯 Заголовок балуна найден через селектор: ${selector}`, 'info');
                    addLog(`📏 Размер заголовка: ${header.innerHTML.length} символов`, 'info');
                    fullHTML += `<div class="balloon-header">${header.innerHTML}</div>`;
                    break;
                }
            } catch (e) {
                console.warn(`Ошибка при поиске заголовка ${selector}:`, e);
                continue;
            }
        }
        
        // 2. Затем ищем основной контент балуна
        const contentSelectors = [
            '.ymaps-2-1-79-balloon__content',
            '.ymaps-balloon__content',
            '.balloon-content',
            '.balloon__content',
            '.ymaps-2-1-79-balloon__content-body',
            '.ymaps-2-1-79-balloon__content-body__content',
            '.ymaps-2-1-79-balloon__content-body__content__content',
            '.ymaps-2-1-79-balloon__content-body__content__content__content'
        ];
        
        for (let selector of contentSelectors) {
            try {
                const content = document.querySelector(selector);
                if (content && content.innerHTML) {
                    addLog(`🌐 HTML контент найден через селектор: ${selector}`, 'info');
                    addLog(`📏 Размер контента: ${content.innerHTML.length} символов`, 'info');
                    fullHTML += `<div class="balloon-content">${content.innerHTML}</div>`;
                    break;
                }
            } catch (e) {
                console.warn(`Ошибка при поиске селектора ${selector}:`, e);
                continue;
            }
        }
        
        // 3. Если не нашли через селекторы, пробуем найти весь балун целиком
        if (!fullHTML) {
            const balloonSelectors = [
                '.ymaps-2-1-79-balloon',
                '.ymaps-balloon',
                '.balloon',
                '.ymaps-2-1-79-balloon__layout',
                '.ymaps-balloon__layout',
                '.balloon-layout',
                '.balloon__layout'
            ];
            
            for (let selector of balloonSelectors) {
                try {
                    const balloon = document.querySelector(selector);
                    if (balloon && balloon.innerHTML) {
                        addLog(`🎈 Весь балун найден через селектор: ${selector}`, 'info');
                        addLog(`📏 Размер всего балуна: ${balloon.innerHTML.length} символов`, 'info');
                        fullHTML = balloon.innerHTML;
                        break;
                    }
                } catch (e) {
                    console.warn(`Ошибка при поиске балуна ${selector}:`, e);
                    continue;
                }
            }
        }
        
        if (fullHTML) {
            addLog(`📏 Общий размер HTML: ${fullHTML.length} символов`, 'info');
            return fullHTML;
        } else {
            addLog('⚠️ HTML контент не найден', 'warning');
            return '';
        }
    } catch (error) {
        console.error('Ошибка при извлечении HTML контента:', error);
        addLog(`❌ Ошибка при извлечении HTML контента: ${error.message}`, 'error');
        return '';
    }
}
```

### 2. **Приоритетный поиск названий в заголовках**

Обновлены селекторы для поиска названий с приоритетом заголовков:

```javascript
// Извлечение названия - улучшенная версия с приоритетом заголовков
const nameSelectors = [
    // Приоритет 1: Заголовки балуна
    '.balloon-header', '.balloon__header', '.ymaps-balloon__header', '.ymaps-2-1-79-balloon__header',
    '.balloon-title', '.balloon__title', '.ymaps-balloon__title', '.ymaps-2-1-79-balloon__title',
    '.balloon-header-content', '.balloon__header-content', '.ymaps-balloon__header-content', '.ymaps-2-1-79-balloon__header-content',
    // Приоритет 2: Общие заголовки
    'h1', 'h2', 'h3', '.name', '.title', '.venue-name', '.place-name',
    '[class*="name"]', '[class*="title"]', '[class*="venue"]',
    // Приоритет 3: Заголовки в контенте
    '.balloon-content h1', '.balloon-content h2', '.balloon-content h3',
    '.balloon__content h1', '.balloon__content h2', '.balloon__content h3',
    '.ymaps-balloon__content h1', '.ymaps-balloon__content h2', '.ymaps-balloon__content h3',
    '.ymaps-2-1-79-balloon__content h1', '.ymaps-2-1-79-balloon__content h2', '.ymaps-2-1-79-balloon__content h3'
];
```

### 3. **Специальный поиск в заголовке балуна**

Добавлен специальный метод для поиска названий в заголовке:

```javascript
// Специальный поиск в заголовке балуна
if (!nameFound) {
    addLog('🔍 Специальный поиск названия в заголовке балуна...', 'info');
    
    // Ищем элементы заголовка в DOM
    const headerElements = document.querySelectorAll('.ymaps-2-1-79-balloon__header, .ymaps-balloon__header, .balloon-header, .balloon__header, .ymaps-2-1-79-balloon__title, .ymaps-balloon__title, .balloon-title, .balloon__title');
    
    for (let headerElement of headerElements) {
        const headerText = headerElement.textContent.trim();
        if (headerText && headerText.length > 2 && headerText.length < 100 &&
            !headerText.includes('Телефон') && !headerText.includes('Адрес') &&
            !headerText.includes('Часы') && !headerText.includes('Рейтинг')) {
            
            extractedData.name = headerText;
            addLog(`🏪 Название найдено в заголовке балуна: ${extractedData.name}`, 'info');
            nameFound = true;
            break;
        }
    }
}
```

## 🔍 Что было исправлено

### 1. **Парсинг заголовка балуна**
- Поиск элементов заголовка через различные селекторы
- Извлечение HTML заголовка отдельно от контента
- Объединение заголовка и контента в один HTML

### 2. **Приоритетный поиск названий**
- Приоритет 1: Заголовки балуна
- Приоритет 2: Общие заголовки
- Приоритет 3: Заголовки в контенте

### 3. **Специальный поиск в DOM**
- Прямой поиск элементов заголовка в DOM
- Фильтрация неподходящего текста
- Логирование найденных названий

### 4. **Многоуровневый подход**
- Сначала парсинг заголовка + контента
- Затем поиск названий в заголовках
- Финально поиск в общем HTML

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
Теперь в логе должно быть больше информации о заголовках:
```
10:00:30: 🔍 Извлечение данных из HTML контента...
10:00:30: 📏 Размер HTML для анализа: 8500 символов
10:00:30: 🔍 Найдено 60 элементов в HTML
10:00:30: 🎯 Заголовок балуна найден через селектор: .ymaps-2-1-79-balloon__header
10:00:30: 📏 Размер заголовка: 1500 символов
10:00:30: 🌐 HTML контент найден через селектор: .ymaps-2-1-79-balloon__content
10:00:30: 📏 Размер контента: 7000 символов
10:00:30: 🏪 Название найдено в заголовке балуна: Площадь Революции
10:00:30: 🏠 Адрес из HTML: Москва, улица Ильинка, 3/8с5
10:00:30: 📞 Телефон из HTML: 89576815539
10:00:30: 🌐 Сайт из HTML: https://magadanrest.ru/gostinyj-dvor
```

## 📊 Ожидаемые результаты

### ✅ Успешное извлечение (ИСПРАВЛЕНО):
```
НАЗВАНИЕ: Площадь Революции
АДРЕС: Москва, улица Ильинка, 3/8с5
ТЕЛЕФОН: 89576815539
ВЕБ-САЙТ: https://magadanrest.ru/gostinyj-dvor
ЧАСЫ РАБОТЫ: Часы работы не указаны
РЕЙТИНГ: Рейтинг не указан
КОЛИЧЕСТВО ОТЗЫВОВ: Отзывы не указаны
ТИП: venue
ОПИСАНИЕ: Описание не указано
```

### ❌ Если название все еще не извлекается:
- Проверьте логи в консоли браузера
- Посмотрите на информацию о заголовке балуна
- Убедитесь, что балун содержит заголовок

## 🔧 Дополнительные улучшения

### 1. **Отладка заголовков в консоли браузера**
```javascript
// Проверьте заголовки балуна
const headerSelectors = ['.ymaps-2-1-79-balloon__header', '.ymaps-balloon__header', '.balloon-header'];
headerSelectors.forEach(selector => {
    const header = document.querySelector(selector);
    if (header) {
        console.log(`Header found with ${selector}:`, header.textContent.trim());
    }
});

// Проверьте весь балун
const balloon = document.querySelector('.ymaps-2-1-79-balloon');
if (balloon) {
    console.log('Full balloon HTML:', balloon.innerHTML.substring(0, 2000));
}
```

### 2. **Проверка структуры балуна**
```javascript
// Проверьте структуру балуна
const balloonElements = document.querySelectorAll('.ymaps-2-1-79-balloon *');
balloonElements.forEach((el, i) => {
    if (el.textContent.trim() && i < 20) {
        console.log(`Balloon element ${i}: ${el.tagName} "${el.textContent.trim()}"`);
    }
});
```

## ✅ Заключение

Парсинг заголовков балуна полностью исправлен! Теперь парсер:

- ✅ Извлекает заголовок балуна отдельно от контента
- ✅ Объединяет заголовок и контент в один HTML
- ✅ Приоритетно ищет названия в заголовках
- ✅ Использует специальный поиск в DOM
- ✅ Предоставляет подробную отладочную информацию

**Попробуйте извлечь данные снова - теперь названия должны извлекаться из заголовков балуна! 🎈** 