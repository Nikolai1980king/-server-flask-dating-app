# Автоматический сброс счетчика непрочитанных сообщений

## Проблема
Когда пользователь находился в открытом чате с собеседником и получал новое сообщение, он видел:
1. Индикатор "печатает..."
2. Само сообщение появлялось на экране
3. Но счетчик непрочитанных сообщений в конвертике (✉️) продолжал показывать цифру

Это создавало путаницу, так как пользователь уже видел сообщение, но счетчик не обновлялся.

## Решение
Добавлена автоматическая отметка сообщений как прочитанные при получении новых сообщений в открытом чате.

### 1. Новый API endpoint для отметки сообщений как прочитанные
```python
@app.route('/api/mark_messages_read/<string:other_user_id>', methods=['POST'])
def api_mark_messages_read(other_user_id):
    """API для отметки сообщений от конкретного пользователя как прочитанные"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({"error": "Пользователь не авторизован"}), 401
    
    try:
        # Находим все сообщения от other_user_id к user_id, которые еще не прочитаны
        chat_key = '_'.join(sorted([user_id, other_user_id]))
        unread_messages = Message.query.filter_by(chat_key=chat_key).filter(
            Message.sender == other_user_id,
            (Message.read_by.is_(None)) | (Message.read_by != user_id)
        ).all()
        
        # Отмечаем их как прочитанные
        for msg in unread_messages:
            msg.read_by = user_id
        
        db.session.commit()
        
        return jsonify({
            "success": True,
            "marked_read": len(unread_messages),
            "unread_messages": get_unread_messages_count(user_id)
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка при отметке сообщений: {str(e)}"}), 500
```

### 2. Функция отметки сообщений как прочитанные
```javascript
function markMessagesAsRead(otherUserId) {
    fetch(`/api/mark_messages_read/${otherUserId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Обновляем счетчик в навбаре
            updateNavbarBadges();
        }
    })
    .catch(error => {
        console.error('Ошибка при отметке сообщений как прочитанных:', error);
    });
}
```

### 3. Автоматическое обновление счетчика в навбаре
```javascript
function updateNavbarBadges() {
    fetch('/api/unread')
        .then(response => response.json())
        .then(data => {
            let msgBadge = document.getElementById('msg-badge');
            if (msgBadge) {
                if (data.unread_messages > 0) {
                    msgBadge.innerText = data.unread_messages;
                    msgBadge.style.display = '';
                } else {
                    msgBadge.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Ошибка при обновлении счетчиков:', error);
        });
}
```

### 4. Интеграция с получением сообщений
```javascript
// При получении сообщения через Socket.IO
socket.on('message', function(data) {
    addMessage(data.text, data.sender);
    if (data.sender !== user_id) {
        lastMessageCount++;
        // Автоматически отмечаем сообщение как прочитанное
        markMessagesAsRead(other_user_id);
    }
});

// При получении сообщений через AJAX
function checkNewMessages() {
    fetch(`/chat_history/${other_user_id}`)
        .then(response => response.json())
        .then(messages => {
            if (messages.length > lastMessageCount) {
                const newMessages = messages.slice(lastMessageCount);
                let hasNewMessagesFromOther = false;
                
                newMessages.forEach(msg => {
                    if (msg.sender !== user_id) {
                        addMessage(msg.text, msg.sender, msg.timestamp);
                        hasNewMessagesFromOther = true;
                    }
                });
                
                // Если есть новые сообщения от собеседника, отмечаем их как прочитанные
                if (hasNewMessagesFromOther) {
                    markMessagesAsRead(other_user_id);
                }
            }
        });
}
```

### 5. Отметка сообщений как прочитанные при загрузке чата
```javascript
window.addEventListener('load', function() {
    window.scrollTo(0, document.body.scrollHeight);
    // Отмечаем все сообщения от собеседника как прочитанные при загрузке чата
    markMessagesAsRead(other_user_id);
});
```

## Когда происходит автоматическая отметка как прочитанные

### ✅ При загрузке страницы чата
- Все существующие сообщения от собеседника отмечаются как прочитанные

### ✅ При получении нового сообщения через Socket.IO
- Новое сообщение сразу отмечается как прочитанное
- Счетчик в конвертике обновляется

### ✅ При получении новых сообщений через AJAX
- Все новые сообщения от собеседника отмечаются как прочитанные
- Счетчик обновляется

## Результат
- ✅ Счетчик непрочитанных сообщений автоматически сбрасывается при получении сообщений в открытом чате
- ✅ Нет путаницы - если пользователь видит сообщение, счетчик обновляется
- ✅ Улучшенный пользовательский опыт
- ✅ Автоматическое обновление счетчиков в реальном времени

## Файлы изменены
- `app.py` - добавлен API endpoint и обновлена логика чата
- `CHAT_AUTO_READ_FIX.md` - данная документация 