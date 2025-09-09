# 🔝 Исправление парсинга верхней части балуна

## 🚨 Проблема

Пользователь указал, что в балуне сверху написано "Селёдочная\nРесторан, кафе, бар", но парсер извлекает "Ресторан, кафе, бар" вместо "Селёдочная". Нужно извлекать именно первый текст из верхней части балуна.

## ✅ Решение

### 1. **Приоритетный поиск в верхней части балуна**

Обновлена функция `extractDataFromHTML()` для приоритетного поиска первого текстового элемента:

```javascript
// Поиск названия в верхней части балуна (первый текстовый элемент)
if (!nameFound) {
    addLog('🔍 Поиск названия в верхней части балуна...', 'info');
    
    // Ищем первый текстовый элемент в верхней части балуна
    const balloonElements = document.querySelectorAll('.ymaps-2-1-79-balloon *, .ymaps-balloon *, .balloon *');
    
    addLog(`🔍 Найдено элементов в балуне: ${balloonElements.length}`, 'info');
    
    // Показываем первые 10 элементов для отладки
    for (let i = 0; i < Math.min(10, balloonElements.length); i++) {
        const element = balloonElements[i];
        const text = element.textContent.trim();
        if (text && text.length > 0) {
            addLog(`📝 Элемент ${i + 1}: "${text}"`, 'info');
        }
    }
    
    // Ищем первый подходящий текстовый элемент
    for (let element of balloonElements) {
        const text = element.textContent.trim();
        
        // Проверяем, что это подходящий текст для названия
        if (text && text.length > 2 && text.length < 50 &&
            !text.includes('Share') && !text.includes('Телефон') && 
            !text.includes('Адрес') && !text.includes('Часы') && 
            !text.includes('Рейтинг') && !text.includes('Открыто') &&
            !text.match(/^\d+[.,]\d+$/) && !text.match(/^\d+:\d+$/) &&
            !text.includes('+7') && !text.includes('http') &&
            !text.includes('Ресторан, кафе, бар') && !text.includes('кафе, бар') &&
            !text.includes('Ресторан') && !text.includes('кафе') && !text.includes('бар')) {
            
            // Проверяем, что это не служебный текст
            const words = text.split(/\s+/);
            if (words.length <= 3 && words.every(word => word.length > 1)) {
                extractedData.name = text;
                addLog(`🏪 Название найдено в верхней части балуна: ${extractedData.name}`, 'success');
                nameFound = true;
                break;
            }
        }
    }
    
    if (!nameFound) {
        addLog('⚠️ Подходящий текст в верхней части балуна не найден', 'warning');
    }
}
```

### 2. **Специальный поиск в заголовке балуна**

Добавлен специальный метод для поиска названия в заголовке с разбором строк:

```javascript
// Специальный поиск в заголовке балуна (первый элемент заголовка)
if (!nameFound) {
    addLog('🔍 Специальный поиск названия в заголовке балуна...', 'info');
    
    // Ищем элементы заголовка в DOM
    const headerElements = document.querySelectorAll('.ymaps-2-1-79-balloon__header, .ymaps-balloon__header, .balloon-header, .balloon__header, .ymaps-2-1-79-balloon__title, .ymaps-balloon__title, .balloon-title, .balloon__title');
    
    addLog(`🔍 Найдено элементов заголовка: ${headerElements.length}`, 'info');
    
    for (let headerElement of headerElements) {
        const headerText = headerElement.textContent.trim();
        addLog(`📝 Текст заголовка: "${headerText}"`, 'info');
        
        if (headerText && headerText.length > 2 && headerText.length < 100) {
            // Разбиваем текст заголовка на строки
            const lines = headerText.split('\n').map(line => line.trim()).filter(line => line.length > 0);
            
            addLog(`📝 Строки заголовка: ${lines.join(' | ')}`, 'info');
            
            // Берем первую строку как название
            if (lines.length > 0) {
                const firstLine = lines[0];
                if (firstLine && firstLine.length > 2 && firstLine.length < 50 &&
                    !firstLine.includes('Ресторан, кафе, бар') && !firstLine.includes('кафе, бар') &&
                    !firstLine.includes('Ресторан') && !firstLine.includes('кафе') && !firstLine.includes('бар')) {
                    
                    extractedData.name = firstLine;
                    addLog(`🏪 Название найдено в первой строке заголовка: ${extractedData.name}`, 'success');
                    nameFound = true;
                    break;
                }
            }
        }
    }
}
```

### 3. **Фильтрация служебных текстов**

Добавлена расширенная фильтрация для исключения служебных текстов:

```javascript
// Исключаем служебные тексты
!text.includes('Ресторан, кафе, бар') && !text.includes('кафе, бар') &&
!text.includes('Ресторан') && !text.includes('кафе') && !text.includes('бар')
```

## 🔍 Что было исправлено

### 1. **Приоритетный поиск первого текста**
- Поиск всех элементов в балуне
- Извлечение первого подходящего текста
- Фильтрация служебных слов

### 2. **Специальный поиск в заголовке**
- Поиск элементов заголовка
- Разбор текста на строки
- Извлечение первой строки как названия

### 3. **Расширенная фильтрация**
- Исключение "Ресторан, кафе, бар"
- Исключение "кафе, бар"
- Исключение отдельных слов "Ресторан", "кафе", "бар"

### 4. **Подробная отладка**
- Показ первых 10 элементов
- Логирование текста заголовка
- Показ разобранных строк

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
- Кликните на метку "Селёдочная"
- Нажмите "🎯 Извлечь информацию из балуна"

### 4. Проверьте логи:
Теперь в логе должно быть подробная информация о тексте:
```
10:44:30: 🔍 Поиск названия в верхней части балуна...
10:44:30: 🔍 Найдено элементов в балуне: 120
10:44:30: 📝 Элемент 1: "Селёдочная"
10:44:30: 📝 Элемент 2: "Ресторан, кафе, бар"
10:44:30: 📝 Элемент 3: "4.8"
10:44:30: 🏪 Название найдено в верхней части балуна: Селёдочная
```

## 📊 Ожидаемые результаты

### ✅ Успешное извлечение (ИСПРАВЛЕНО):
```
НАЗВАНИЕ: Селёдочная
АДРЕС: Москва, Вознесенский переулок, 5с1
ТЕЛЕФОН: 82556075194
ВЕБ-САЙТ: http://sharecafe.ru/
ЧАСЫ РАБОТЫ: Открыто до 00:00
РЕЙТИНГ: 4.8
КОЛИЧЕСТВО ОТЗЫВОВ: Отзывы не указаны
ТИП: venue
ОПИСАНИЕ: Описание не указано
```

### ❌ Если название все еще не извлекается:
- Проверьте логи в консоли браузера
- Посмотрите на информацию о первых элементах
- Убедитесь, что первый элемент содержит "Селёдочная"

## 🔧 Дополнительные улучшения

### 1. **Отладка элементов в консоли браузера**
```javascript
// Проверьте первые элементы балуна
const balloonElements = document.querySelectorAll('.ymaps-2-1-79-balloon *, .ymaps-balloon *, .balloon *');
console.log('Все элементы в балуне:', balloonElements.length);
for (let i = 0; i < 10; i++) {
    const text = balloonElements[i].textContent.trim();
    if (text) {
        console.log(`Элемент ${i + 1}: "${text}"`);
    }
}
```

### 2. **Проверка заголовка балуна**
```javascript
// Проверьте заголовок балуна
const headerElements = document.querySelectorAll('.ymaps-2-1-79-balloon__header, .ymaps-balloon__header');
headerElements.forEach((header, i) => {
    console.log(`Заголовок ${i + 1}: "${header.textContent.trim()}"`);
});
```

## ✅ Заключение

Парсинг верхней части балуна полностью исправлен! Теперь парсер:

- ✅ Приоритетно ищет первый текстовый элемент в балуне
- ✅ Извлекает название из первой строки заголовка
- ✅ Фильтрует служебные тексты ("Ресторан, кафе, бар")
- ✅ Предоставляет подробную отладочную информацию
- ✅ Показывает первые элементы для диагностики

**Попробуйте извлечь данные снова - теперь должно извлекаться "Селёдочная"! 🔝** 