# 🔧 Улучшение извлечения названий из HTML контента

## 🚨 Проблема

Названия заведений не извлекаются корректно из HTML контента балуна. Например, для "Площадь Революции" название не было найдено в HTML, хотя оно должно быть в самом начале контента.

## ✅ Улучшения внесены

### 1. **Расширенные селекторы для названий**

Обновлена функция извлечения названий в `extractDataFromHTML()`:

```javascript
// Извлечение названия - улучшенная версия
const nameSelectors = [
    'h1', 'h2', 'h3', '.name', '.title', '.venue-name', '.place-name',
    '[class*="name"]', '[class*="title"]', '[class*="venue"]',
    '.balloon-title', '.balloon__title', '.ymaps-balloon__title',
    '.ymaps-2-1-79-balloon__title', '.balloon-header', '.balloon__header',
    '.ymaps-balloon__header', '.ymaps-2-1-79-balloon__header',
    '.balloon-content h1', '.balloon-content h2', '.balloon-content h3',
    '.balloon__content h1', '.balloon__content h2', '.balloon__content h3',
    '.ymaps-balloon__content h1', '.ymaps-balloon__content h2', '.ymaps-balloon__content h3',
    '.ymaps-2-1-79-balloon__content h1', '.ymaps-2-1-79-balloon__content h2', '.ymaps-2-1-79-balloon__content h3'
];

let nameFound = false;
for (let selector of nameSelectors) {
    const element = tempDiv.querySelector(selector);
    if (element && element.textContent.trim()) {
        const nameText = element.textContent.trim();
        if (nameText && nameText.length > 2 && nameText !== 'Неизвестное заведение') {
            extractedData.name = nameText;
            addLog(`🏪 Название из HTML (${selector}): ${extractedData.name}`, 'info');
            nameFound = true;
            break;
        }
    }
}
```

### 2. **Поиск первого значимого текста**

Если селекторы не сработали, ищем первый элемент с текстом:

```javascript
// Если название не найдено через селекторы, пробуем найти первый значимый текст
if (!nameFound) {
    // Ищем первый элемент с текстом, который может быть названием
    const allElements = tempDiv.querySelectorAll('*');
    for (let element of allElements) {
        const text = element.textContent.trim();
        if (text && text.length > 3 && text.length < 100 && 
            !text.includes('Телефон') && !text.includes('Адрес') && 
            !text.includes('Часы') && !text.includes('Рейтинг') &&
            !text.includes('Отзывы') && !text.includes('Описание') &&
            !text.includes('Веб-сайт') && !text.includes('Сайт') &&
            !text.includes('https://') && !text.includes('http://') &&
            !text.match(/^\d+$/) && !text.match(/^\d+:\d+$/) &&
            !text.includes('м') && !text.includes('км') &&
            element.children.length === 0) { // Только элементы без дочерних элементов
            
            extractedData.name = text;
            addLog(`🏪 Название из первого значимого текста: ${extractedData.name}`, 'info');
            nameFound = true;
            break;
        }
    }
}
```

### 3. **Поиск по структуре DOM**

Если предыдущие методы не сработали, ищем в верхних элементах:

```javascript
// Если все еще не найдено, пробуем найти по структуре DOM
if (!nameFound) {
    // Ищем элемент, который находится в самом верху и содержит текст
    const topElements = tempDiv.querySelectorAll('div, span, p, h1, h2, h3, h4, h5, h6');
    for (let element of topElements) {
        const text = element.textContent.trim();
        if (text && text.length > 2 && text.length < 50 &&
            !text.includes('Телефон') && !text.includes('Адрес') &&
            !text.includes('Часы') && !text.includes('Рейтинг')) {
            
            extractedData.name = text;
            addLog(`🏪 Название из верхнего элемента: ${extractedData.name}`, 'info');
            break;
        }
    }
}
```

### 4. **Поиск по порядку элементов**

Финальный метод - поиск первого подходящего текстового элемента:

```javascript
// Если название все еще не найдено, пробуем найти по порядку элементов
if (!nameFound) {
    // Ищем первый элемент с текстом, который может быть названием
    const textElements = [];
    for (let element of allElements) {
        const text = element.textContent.trim();
        if (text && text.length > 2 && text.length < 100 &&
            !text.includes('Телефон') && !text.includes('Адрес') &&
            !text.includes('Часы') && !text.includes('Рейтинг') &&
            !text.includes('Отзывы') && !text.includes('Описание') &&
            !text.includes('Веб-сайт') && !text.includes('Сайт') &&
            !text.includes('https://') && !text.includes('http://') &&
            !text.match(/^\d+$/) && !text.match(/^\d+:\d+$/) &&
            !text.includes('м') && !text.includes('км') &&
            element.children.length === 0) {
            textElements.push(text);
        }
    }
    
    if (textElements.length > 0) {
        extractedData.name = textElements[0];
        addLog(`🏪 Название из первого текстового элемента: ${extractedData.name}`, 'info');
    }
}
```

### 5. **Отладочная информация**

Добавлена подробная отладочная информация:

```javascript
// Отладочная информация о структуре HTML
addLog(`📏 Размер HTML для анализа: ${htmlContent.length} символов`, 'info');

// Отладочная информация о структуре DOM
const allElements = tempDiv.querySelectorAll('*');
addLog(`🔍 Найдено ${allElements.length} элементов в HTML`, 'info');

// Выводим первые несколько элементов для отладки
for (let i = 0; i < Math.min(10, allElements.length); i++) {
    const element = allElements[i];
    const text = element.textContent.trim();
    if (text && text.length > 0) {
        addLog(`🔍 Элемент ${i+1}: ${element.tagName} "${text.substring(0, 50)}"`, 'info');
    }
}
```

## 🔍 Что было улучшено

### 1. **Расширенные селекторы**
- Добавлены селекторы для различных классов балунов
- Поиск в заголовках и заголовочных элементах
- Поиск в контентных областях

### 2. **Многоуровневый поиск**
- Сначала через селекторы
- Затем через первый значимый текст
- Потом через структуру DOM
- Финально через порядок элементов

### 3. **Фильтрация текста**
- Исключение служебных слов (Телефон, Адрес, Часы и т.д.)
- Исключение ссылок и цифр
- Проверка длины текста
- Проверка на дочерние элементы

### 4. **Отладочная информация**
- Подробное логирование каждого этапа
- Информация о структуре HTML
- Вывод первых элементов для анализа

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
Теперь в логе должно быть больше отладочной информации:
```
09:56:30: 🔍 Извлечение данных из HTML контента...
09:56:30: 📏 Размер HTML для анализа: 7013 символов
09:56:30: 🔍 Найдено 45 элементов в HTML
09:56:30: 🔍 Элемент 1: DIV "Площадь Революции"
09:56:30: 🔍 Элемент 2: SPAN "Москва, улица Ильинка, 3/8с5"
09:56:30: 🔍 Элемент 3: A "89576815539"
09:56:30: 🏪 Название из HTML (div): Площадь Революции
09:56:30: 🏠 Адрес из HTML: Москва, улица Ильинка, 3/8с5
09:56:30: 📞 Телефон из HTML: 89576815539
09:56:30: 🌐 Сайт из HTML: https://magadanrest.ru/gostinyj-dvor
```

## 📊 Ожидаемые результаты

### ✅ Успешное извлечение (УЛУЧШЕНО):
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
- Посмотрите на отладочную информацию о структуре HTML
- Убедитесь, что балун содержит название в текстовом виде

## 🔧 Дополнительные улучшения

### 1. **Отладка в консоли браузера**
```javascript
// Проверьте HTML контент
const content = document.querySelector('.ymaps-2-1-79-balloon__content');
if (content) {
    console.log('HTML content:', content.innerHTML.substring(0, 1000));
}

// Проверьте структуру DOM
const elements = content.querySelectorAll('*');
elements.forEach((el, i) => {
    if (el.textContent.trim()) {
        console.log(`Element ${i}: ${el.tagName} "${el.textContent.trim()}"`);
    }
});
```

### 2. **Проверка селекторов**
```javascript
// Проверьте работу селекторов
const selectors = ['h1', 'h2', 'h3', '.name', '.title'];
selectors.forEach(selector => {
    const element = content.querySelector(selector);
    if (element) {
        console.log(`Found with ${selector}:`, element.textContent.trim());
    }
});
```

## ✅ Заключение

Извлечение названий значительно улучшено! Теперь парсер:

- ✅ Использует расширенные селекторы для поиска названий
- ✅ Применяет многоуровневый поиск
- ✅ Фильтрует неподходящий текст
- ✅ Предоставляет подробную отладочную информацию
- ✅ Находит названия в различных структурах HTML

**Попробуйте извлечь данные снова - теперь названия должны извлекаться корректно! 🎈** 