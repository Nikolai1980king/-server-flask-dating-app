# 🧠 Функция "Напрягись" - Головоломки и задачи на логику

## ✅ Реализовано

Добавлена 4-я опция сюрприза "Напрягись" с головоломками и логическими задачами!

---

## 🎯 Что это?

**"Напрягись"** - это функция отправки логических головоломок и задач на смекалку (в стиле Перельмана) собеседнику в чате.

---

## 📋 Основные возможности

### 1️⃣ **Коллекция головоломок**
- ✅ 25 уникальных головоломок и задач на логику
- ✅ Без ответов - получатель должен подумать сам!
- ✅ Разнообразные типы:
  - Математические загадки
  - Логические парадоксы
  - Загадки с подвохом
  - Задачи на смекалку

### 2️⃣ **Отслеживание повторов**
- ✅ Головоломки не повторяются для одного получателя
- ✅ Таблица `sent_puzzle` в БД хранит историю
- ✅ Случайный выбор из доступных (не отправленных ранее)
- ✅ Уведомление, если все головоломки уже отправлены

### 3️⃣ **Красивое отображение**
- ✅ Синий градиент (голубой → фиолетовый)
- ✅ Большой пульсирующий мозг 🧠 (5em)
- ✅ 4 вращающиеся иконки по углам: 🧩🎲💭
- ✅ Белый блок с текстом (отличная читаемость)
- ✅ Думающий смайлик внизу 🤔 (качается)
- ✅ Остается в истории чата навсегда

---

## 🎨 Визуальный дизайн

### Цветовая схема:
```css
background: linear-gradient(135deg, 
  #00d2ff 0%,    /* Голубой */
  #3a7bd5 35%,   /* Синий */
  #9d50bb 70%,   /* Фиолетовый */
  #6e48aa 100%   /* Темно-фиолетовый */
);
```

### Анимации:
1. **puzzleGlow** - пульсация всего блока с изменением тени
2. **brainPulse** - мозг пульсирует и слегка поворачивается
3. **puzzleRotate1** - вращение по часовой (360°)
4. **puzzleRotate2** - вращение против часовой (360°)
5. **puzzleFloat** - плавающее движение вверх-вниз
6. **thinkingRotate** - качание думающего смайлика

### Структура:
```
┌──────────────────────────────────────┐
│ 🎁 Вам отправили сюрприз!            │
│ ┌────────────────────────────────┐   │
│ │ 🧩 (вращается)  🎲 (вращается) │   │
│ │                                 │   │
│ │        🧠 (5em, пульсирует)     │   │
│ │                                 │   │
│ │      Напрягись! 💪              │   │
│ │                                 │   │
│ │ ┌───────────────────────────┐  │   │
│ │ │  Белый блок с головоломкой│  │   │
│ │ │  (крупный шрифт 1.15em)   │  │   │
│ │ │  (синяя рамка)            │  │   │
│ │ └───────────────────────────┘  │   │
│ │                                 │   │
│ │        🤔 (качается)            │   │
│ │                                 │   │
│ │ 💭 (плавает)    🧩 (вращается)  │   │
│ └────────────────────────────────┘   │
└──────────────────────────────────────┘
```

---

## 💾 База данных

### Таблица `sent_puzzle`
```sql
CREATE TABLE sent_puzzle (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id VARCHAR NOT NULL,        -- Кто отправил
    receiver_id VARCHAR NOT NULL,      -- Кто получил
    puzzle_id INTEGER NOT NULL,        -- ID головоломки из списка
    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (sender_id, receiver_id, puzzle_id)  -- Не повторяем
)
```

### Миграция
Файл: `migrate_add_puzzles.py`
```bash
python migrate_add_puzzles.py
```

---

## 🔧 Техническая реализация

### Backend (app.py)

#### 1. Коллекция головоломок
```python
LOGIC_PUZZLES = [
    "📊 У отца шесть сыновей. Каждый сын имеет сестру.\n\nСколько всего детей у этого отца?",
    "🔢 Двое играли в шахматы 4 часа.\n\nСколько времени играл каждый?",
    # ... еще 23 головоломки
]
```

#### 2. Модель SentPuzzle
```python
class SentPuzzle(db.Model):
    """Модель для хранения отправленных головоломок"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, nullable=False)
    receiver_id = db.Column(db.String, nullable=False)
    puzzle_id = db.Column(db.Integer, nullable=False)
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (
        db.UniqueConstraint('sender_id', 'receiver_id', 'puzzle_id', 
                          name='unique_sent_puzzle'),
    )
```

#### 3. Endpoint обработки
```python
@app.route('/api/send-surprise', methods=['POST'])
def api_send_surprise():
    # ...
    elif surprise_type == 'puzzle':
        # Получаем отправленные головоломки
        sent_puzzles = SentPuzzle.query.filter_by(
            sender_id=user_id, 
            receiver_id=receiver_id
        ).all()
        sent_puzzle_ids = [sp.puzzle_id for sp in sent_puzzles]
        
        # Находим доступные
        available_puzzle_ids = [
            i for i in range(len(LOGIC_PUZZLES)) 
            if i not in sent_puzzle_ids
        ]
        
        if not available_puzzle_ids:
            return jsonify({
                "error": "Все головоломки уже отправлены",
                "all_puzzles_sent": True
            }), 400
        
        # Выбираем случайную
        selected_puzzle_id = random.choice(available_puzzle_ids)
        selected_puzzle = LOGIC_PUZZLES[selected_puzzle_id]
        
        # Сохраняем
        new_sent_puzzle = SentPuzzle(
            sender_id=user_id,
            receiver_id=receiver_id,
            puzzle_id=selected_puzzle_id
        )
        db.session.add(new_sent_puzzle)
        
        message_text = f"🧠 SURPRISE_PUZZLE\n\n{selected_puzzle}"
```

### Frontend (JavaScript)

#### 1. Модальное окно
```html
<div class="surprise-option" onclick="sendSurprise('puzzle')">
    <div class="surprise-icon">🧠</div>
    <div class="surprise-text">
        <h3>Напрягись</h3>
        <p>Отправить головоломку или задачку на логику</p>
    </div>
</div>
```

#### 2. Функция отправки
```javascript
function sendSurprise(type) {
    fetch('/api/send-surprise', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            receiver_id: currentReceiverId,
            type: type  // 'puzzle'
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            if (type === 'puzzle') {
                message = `🧠 Головоломка отправлена ${currentReceiverName}!`;
            }
            showNotification(message, 'success');
        } else if (data.all_puzzles_sent) {
            showNotification(`Все головоломки уже отправлены`, 'info');
        }
    });
}
```

#### 3. Отображение в чате
```javascript
if (msg.includes('SURPRISE_PUZZLE')) {
    const puzzleText = msg.replace('🧠 SURPRISE_PUZZLE', '').trim();
    div.innerHTML = `
        <!-- Красивый блок с головоломкой -->
        <div style="background: linear-gradient(...); animation: puzzleGlow 4s...">
            <div style="font-size: 5em; animation: brainPulse 2s...">🧠</div>
            <div>Напрягись! 💪</div>
            <div style="background: rgba(255,255,255,0.95)...">
                ${puzzleText}
            </div>
            <div style="animation: thinkingRotate 4s...">🤔</div>
        </div>
    `;
}
```

---

## 📊 Примеры головоломок

1. **📊 Математическая**: "У отца шесть сыновей. Каждый сын имеет сестру. Сколько всего детей у этого отца?"

2. **🚗 Логическая**: "Человек ехал в город. По дороге он встретил 3 машины. Сколько машин ехало в город?"

3. **⚖️ Задача на смекалку**: "На одной чаше весов кирпич, на другой - полкирпича и гиря 1 кг. Весы в равновесии. Сколько весит кирпич?"

4. **🎨 Креативная**: "Назовите пять дней недели, не называя их по названиям и числам."

5. **🏃 С подвохом**: "Вы участвуете в забеге и обогнали бегуна, который бежал вторым. На каком месте вы теперь?"

---

## 🎁 Все 4 сюрприза в одном месте

| Тип | Эмодзи | Цвет | Особенность |
|-----|--------|------|-------------|
| **Десерт** | 🍰 | Розово-персиковый | Пульсирует, текст про столик |
| **Шампанское** | 🍾 | Золотой | 4 искры, текст про столик |
| **Анекдот** | 😄 | Фиолетово-розовый | 2 смайлика, блики |
| **Головоломка** | 🧠 | Синий | 4 вращающиеся иконки |

---

## ✅ Что работает

1. ✅ **Отправка головоломок** через кнопку "Удивить"
2. ✅ **Случайный выбор** из доступных
3. ✅ **Отслеживание повторов** на уровне БД
4. ✅ **Красивое отображение** с анимациями
5. ✅ **Сохранение в истории чата** навсегда
6. ✅ **Загрузка при перезагрузке** страницы
7. ✅ **Уведомления** об успехе/ошибках
8. ✅ **Разрешение на чат** после отправки

---

## 🚀 Как использовать

### Для пользователя:
1. Оплатить функцию "Удивить" (50₽)
2. Открыть карточку посетителя
3. Нажать кнопку "✨" (Удивить)
4. Выбрать "🧠 Напрягись"
5. Головоломка будет отправлена получателю

### Для получателя:
1. Зайти в чат
2. Увидеть красивый блок с головоломкой
3. Подумать над ответом
4. Ответить отправителю (чат теперь открыт)

---

## 📝 Итого

**Добавлено:**
- ✅ 25 головоломок без ответов
- ✅ Модель SentPuzzle
- ✅ Endpoint для puzzle
- ✅ Опция "Напрягись" в UI
- ✅ Красивое отображение
- ✅ Миграция БД
- ✅ Полная интеграция с системой сюрпризов

**Улучшено:**
- ✅ Десерт и шампанское - добавлен текст про столик
- ✅ Все сюрпризы остаются в истории чата

**Результат:** Полностью функциональная система головоломок! 🎉




























