# нужно вводить https://192.168.255.137
# Тестовое изменение для демонстрации коммита

from flask import Flask, render_template_string, request, redirect, url_for, make_response, jsonify
from flask_socketio import SocketIO, emit, join_room
import os
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from functools import wraps
import requests

app = Flask(__name__)
app.secret_key = 'super-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Увеличиваем лимит размера файла до 16MB (по умолчанию 1MB)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
db = SQLAlchemy(app)

# Максимальное расстояние для регистрации (в метрах) - СТРОКА 29
MAX_REGISTRATION_DISTANCE = 3000  # 3 км = 3000 метров

# Время жизни анкеты в часах - НАСТРАИВАЕМАЯ ПЕРЕМЕННАЯ
PROFILE_LIFETIME_HOURS = 24  # Измените это значение для настройки времени жизни анкет


def get_location_name(lat, lon):
    """
    Определяет название города/поселка по координатам
    Возвращает только название города/поселка без районов и областей
    """
    try:
        # Используем Nominatim API для получения адреса с более детальными параметрами
        url = f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}&zoom=18&addressdetails=1"
        headers = {
            'User-Agent': 'DatingApp/1.0 (https://example.com; contact@example.com)'
        }

        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Извлекаем название населенного пункта
        address = data.get('address', {})

        # Приоритет поиска только города/поселка (исключаем районы и области)
        location_name = (
                address.get('city') or
                address.get('town') or
                address.get('village') or
                address.get('hamlet') or
                address.get('suburb') or
                address.get('neighbourhood') or
                address.get('place')
        )

        if location_name:
            return location_name

        # Если не найдено, пытаемся извлечь из полного адреса
        display_name = data.get('display_name', '')
        if display_name:
            # Разбиваем адрес по запятым
            parts = display_name.split(',')

            # Ищем название населенного пункта в частях адреса
            for part in parts:
                part = part.strip()
                # Исключаем административные единицы
                if any(keyword in part.lower() for keyword in
                       ['район', 'область', 'край', 'федерация', 'федеральный', 'сельское поселение',
                        'городское поселение', 'муниципальный', 'россия']):
                    continue
                # Ищем ключевые слова для населенных пунктов
                if any(keyword in part.lower() for keyword in
                       ['поселок', 'пос.', 'село', 'деревня', 'город', 'станица', 'хутор', 'аул']):
                    return part
                # Если часть не содержит административных терминов, считаем её названием населенного пункта
                if part and len(part) > 2 and not any(char.isdigit() for char in part):
                    return part

        return None

    except Exception as e:
        print(f"Ошибка при получении названия населенного пункта: {e}")
        return None


def get_starry_night_css():
    return '''
        body { 
            font-family: Arial, sans-serif; 
            background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%);
            background-size: 400% 400%;
            animation: starryNight 15s ease infinite;
            position: relative;
            min-height: 100vh;
        }

        @keyframes starryNight {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        body::before {
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-image: 
                radial-gradient(2px 2px at 20px 30px, #eee, transparent),
                radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
                radial-gradient(1px 1px at 90px 40px, #fff, transparent),
                radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.6), transparent),
                radial-gradient(2px 2px at 160px 30px, #ddd, transparent);
            background-repeat: repeat;
            background-size: 200px 100px;
            animation: twinkle 4s ease-in-out infinite alternate;
            pointer-events: none;
            z-index: 1;
        }

        @keyframes twinkle {
            0% { opacity: 0.3; }
            100% { opacity: 1; }
        }
    '''


# --- Модели ---
class Profile(db.Model):
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String, nullable=False)
    hobbies = db.Column(db.String, nullable=False)
    goal = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=True)
    venue = db.Column(db.String, nullable=True)
    photo = db.Column(db.String, nullable=True)
    likes = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_key = db.Column(db.String, nullable=False)
    sender = db.Column(db.String, nullable=False)
    text = db.Column(db.String, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    read_by = db.Column(db.String, nullable=True)  # user_id, можно расширить до JSON


class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    liked_id = db.Column(db.String, nullable=False)


# Удаляю in-memory структуру сообщений:
# messages = defaultdict(list)
notifications = defaultdict(list)

read_likes = defaultdict(set)  # user_id -> set(profile_id)
new_matches = defaultdict(set)  # user_id -> set of new matched user_ids


def add_notification(user_id, message):
    notifications[user_id].append({
        'id': str(uuid.uuid4()),
        'message': message,
        'timestamp': datetime.now()
    })


def get_unread_messages_count(user_id):
    if not user_id:
        return 0
    # Найти все чаты, где участвует user_id
    chat_keys = set()
    for msg in Message.query.all():
        ids = msg.chat_key.split('_')
        if user_id in ids:
            chat_keys.add(msg.chat_key)
    # Считать только сообщения в этих чатах, отправленные не user_id и не прочитанные user_id
    count = 0
    for chat_key in chat_keys:
        count += Message.query.filter_by(chat_key=chat_key).filter(
            Message.sender != user_id,
            (Message.read_by.is_(None)) | (Message.read_by != user_id)
        ).count()
    return count


def get_unread_likes_count(user_id):
    if not user_id:
        return 0
    # Получаем id всех, кто меня лайкнул
    all_likes = set(l.user_id for l in Like.query.filter_by(liked_id=user_id).all())
    # Получаем id просмотренных
    viewed = read_likes.get(user_id, set())
    # Считаем только непросмотренные
    unread_count = len(all_likes - viewed)
    
    # Дополнительная проверка: если счетчик отрицательный, сбрасываем его
    if unread_count < 0:
        read_likes[user_id] = set()
        unread_count = len(all_likes)
    
    return unread_count


def get_unread_matches_count(user_id):
    return len(new_matches[user_id])


def render_navbar(user_id, active=None, unread_messages=0, unread_likes=0, unread_matches=0):
    avatar_html = ''
    if user_id and Profile.query.get(user_id):
        photo_url = get_photo_url(Profile.query.get(user_id))
        avatar_html = f'<a href="/my_profile" style="display:inline-block;margin:0 18px 0 10px;vertical-align:middle;" title="Мой профиль">'
        avatar_html += f'<img src="{photo_url}" alt="Аватар" style="width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid #6c757d;vertical-align:middle;">'
        avatar_html += '</a>'
    return render_template_string('''
    <nav id="navbar" style="position:fixed;top:0;left:0;width:100%;background:#0a0909;box-shadow:0 2px 8px rgba(0,0,0,0.07);z-index:100;display:flex;justify-content:center;align-items:center;padding:8px 0;">
        {{ avatar_html|safe }}
        <a href="/visitors" style="font-size:2em;margin:0 10px;{{'font-weight:bold;color:#ff6b6b;' if active=='visitors' else ''}}" title="Посетители">👥</a>
        <a href="/my_likes" style="font-size:2em;margin:0 10px;position:relative;{{'font-weight:bold;color:#ff6b6b;' if active=='likes' else ''}}" title="Меня лайкнули" onclick="markLikesAsRead()">
            ❤️
            <span id="like-badge" style="display:{% if unread_likes > 0 %}inline{% else %}none{% endif %};position:absolute;top:-8px;right:-8px;background:#ff6b6b;color:#fff;border-radius:50%;padding:2px 7px;font-size:0.8em;">{{ unread_likes if unread_likes > 0 else '' }}</span>
        </a>
        <a href="/my_matches" style="font-size:2em;margin:0 10px;position:relative;{{'font-weight:bold;color:#ff6b6b;' if active=='matches' else ''}}" title="Мои мэтчи">🤝
            <span id="match-badge" style="display:{% if unread_matches > 0 %}inline{% else %}none{% endif %};position:absolute;top:-8px;right:-8px;background:#4CAF50;color:#fff;border-radius:50%;padding:2px 7px;font-size:0.8em;">{{ unread_matches if unread_matches > 0 else '' }}</span>
        </a>
        <a href="/my_messages" style="font-size:2em;margin:0 10px;position:relative;{{'font-weight:bold;color:#ff6b6b;' if active=='messages' else ''}}" title="Мои сообщения">
            ✉️
            <span id="msg-badge" style="display:{% if unread_messages > 0 %}inline{% else %}none{% endif %};position:absolute;top:-8px;right:-8px;background:#ff6b6b;color:#fff;border-radius:50%;padding:2px 7px;font-size:0.8em;">{{ unread_messages if unread_messages > 0 else '' }}</span>
        </a>
    </nav>
    <div style="height:48px"></div>
    <script>
    function markLikesAsRead() {
        // Отмечаем все лайки как прочитанные при клике на иконку
        fetch('/api/mark_likes_read', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Скрываем счетчик лайков
                let likeBadge = document.getElementById('like-badge');
                if (likeBadge) {
                    likeBadge.style.display = 'none';
                }
            }
        })
        .catch(error => {
            console.error('Ошибка при отметке лайков как прочитанных:', error);
        });
    }
    
    setInterval(function() {
        fetch('/api/unread')
            .then(r => r.json())
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
                let likeBadge = document.getElementById('like-badge');
                if (likeBadge) {
                    if (data.unread_likes > 0) {
                        likeBadge.innerText = data.unread_likes;
                        likeBadge.style.display = '';
                    } else {
                        likeBadge.style.display = 'none';
                    }
                }
                let matchBadge = document.getElementById('match-badge');
                if (matchBadge) {
                    if (data.unread_matches > 0) {
                        matchBadge.innerText = data.unread_matches;
                        matchBadge.style.display = '';
                    } else {
                        matchBadge.style.display = 'none';
                    }
                }
            });
    }, 5000);
    </script>
    ''', active=active, unread_messages=unread_messages, unread_likes=unread_likes, unread_matches=unread_matches,
                                  avatar_html=avatar_html)


@app.route('/api/unread')
def api_unread():
    user_id = request.cookies.get('user_id')
    return jsonify({
        "unread_messages": get_unread_messages_count(user_id) if user_id else 0,
        "unread_likes": get_unread_likes_count(user_id) if user_id else 0,
        "unread_matches": get_unread_matches_count(user_id) if user_id else 0
    })


@app.route('/api/mark_likes_read', methods=['POST'])
def api_mark_likes_read():
    """API для отметки всех лайков как прочитанных"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({"error": "Пользователь не авторизован"}), 401

    try:
        # Получаем все лайки, которые получил пользователь
        all_likes = set(l.user_id for l in Like.query.filter_by(liked_id=user_id).all())
        # Добавляем их в просмотренные
        read_likes[user_id].update(all_likes)
        
        return jsonify({
            "success": True,
            "marked_read": len(all_likes),
            "unread_likes": get_unread_likes_count(user_id)
        })

    except Exception as e:
        return jsonify({"error": f"Ошибка при отметке лайков: {str(e)}"}), 500


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


@app.route('/api/geolocation')
def api_geolocation():
    """API для получения геолокации пользователя"""
    return jsonify({
        "success": True,
        "message": "Геолокация доступна"
    })


@app.route('/api/get-location-name', methods=['POST'])
def api_get_location_name():
    """API для получения названия населенного пункта по координатам"""
    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')

    if not lat or not lon:
        return jsonify({'error': 'Координаты не предоставлены'}), 400

    try:
        lat = float(lat)
        lon = float(lon)
        location_name = get_location_name(lat, lon)

        if location_name:
            return jsonify({
                'success': True,
                'location_name': location_name
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Не удалось определить населенный пункт'
            }), 404

    except ValueError:
        return jsonify({'error': 'Некорректные координаты'}), 400
    except Exception as e:
        return jsonify({'error': f'Ошибка сервера: {str(e)}'}), 500


@app.route('/api/calculate-distance', methods=['POST'])
def api_calculate_distance():
    """API для расчета расстояния между двумя точками по координатам"""
    data = request.get_json()

    visitor_lat = data.get('visitor_lat')
    visitor_lng = data.get('visitor_lng')
    venue_lat = data.get('venue_lat')
    venue_lng = data.get('venue_lng')

    if not all([visitor_lat, visitor_lng, venue_lat, venue_lng]):
        return jsonify({'error': 'Не все координаты предоставлены'}), 400

    try:
        visitor_lat = float(visitor_lat)
        visitor_lng = float(visitor_lng)
        venue_lat = float(venue_lat)
        venue_lng = float(venue_lng)

        # Используем geopy.distance.geodesic для расчета расстояния
        from geopy.distance import geodesic

        visitor_point = (visitor_lat, visitor_lng)
        venue_point = (venue_lat, venue_lng)

        distance = geodesic(visitor_point, venue_point).meters

        return jsonify({
            'success': True,
            'distance': distance,
            'visitor_coords': f"{visitor_lat}, {visitor_lng}",
            'venue_coords': f"{venue_lat}, {venue_lng}"
        })

    except ValueError:
        return jsonify({'error': 'Некорректные координаты'}), 400
    except Exception as e:
        return jsonify({'error': f'Ошибка расчета расстояния: {str(e)}'}), 500


@app.route('/test-balloon-integration')
def test_balloon_integration():
    """Тестовая страница для проверки интеграции парсинга балунов"""
    return render_template_string(open('test_balloon_integration.html').read())


@app.route('/test-mobile-profile-restore')
def test_mobile_profile_restore():
    """Тестовая страница для проверки восстановления профиля на мобильных устройствах"""
    return render_template_string(open('test_mobile_profile_restore.html').read())


@app.route('/test-mobile-debug')
def test_mobile_debug():
    """Простая страница для диагностики проблем с мобильными устройствами"""
    return render_template_string(open('test_mobile_debug.html').read())


@app.route('/test-profile-redirect')
def test_profile_redirect():
    """Тестовая страница для проверки перенаправления профиля"""
    return render_template_string(open('test_profile_redirect.html').read())


@app.route('/test-map-load')
def test_map_load():
    """Тестовая страница для проверки загрузки карты"""
    return render_template_string(open('test_map_load.html').read())


@app.route('/test-simple-map')
def test_simple_map():
    """Простая тестовая страница для проверки карты"""
    return render_template_string(open('test_simple_map.html').read())


@app.route('/clear-cookie')
def clear_cookie():
    """Страница для очистки cookie"""
    return render_template_string(open('clear_cookie.html').read())


@app.route('/test-field-limits')
def test_field_limits():
    """Тестовая страница для демонстрации ограничений полей"""
    return render_template_string(open('test_field_limits.html').read())


@app.route('/test-alignment')
def test_alignment():
    """Тестовая страница для демонстрации выравнивания полей"""
    return render_template_string(open('test_alignment.html').read())


@app.route('/test-chat-debug')
def test_chat_debug():
    """Тестовая страница для отладки отправки сообщений"""
    return render_template_string(open('test_chat_debug.html').read())


@app.route('/debug-geolocation')
def debug_geolocation():
    """Страница для диагностики проблем с геолокацией"""
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Тест геолокации</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; }
                .test-section { margin: 20px 0; padding: 15px; border: 1px solid #ccc; border-radius: 5px; }
                .success { background-color: #d4edda; border-color: #c3e6cb; }
                .error { background-color: #f8d7da; border-color: #f5c6cb; }
                .info { background-color: #d1ecf1; border-color: #bee5eb; }
                button { padding: 10px 20px; margin: 5px; cursor: pointer; }
                #results { margin-top: 20px; }
            </style>
        </head>
        <body>
            <h1>🔍 Диагностика геолокации</h1>

            <div class="test-section info">
                <h3>📋 Проверка поддержки геолокации</h3>
                <button onclick="checkGeolocationSupport()">Проверить поддержку</button>
                <div id="support-result"></div>
            </div>

            <div class="test-section info">
                <h3>📍 Тест получения местоположения</h3>
                <button onclick="getCurrentLocation()">Получить местоположение</button>
                <div id="location-result"></div>
            </div>

            <div class="test-section info">
                <h3>🌐 Проверка HTTPS</h3>
                <button onclick="checkHTTPS()">Проверить протокол</button>
                <div id="https-result"></div>
            </div>

            <div class="test-section info">
                <h3>🔧 Настройки браузера</h3>
                <div id="browser-settings">
                    <p><strong>Проверьте настройки:</strong></p>
                    <ul>
                        <li>Разрешен ли доступ к местоположению для этого сайта</li>
                        <li>Не заблокирована ли геолокация в настройках браузера</li>
                        <li>Нет ли расширений, блокирующих геолокацию</li>
                    </ul>
                </div>
            </div>

            <div id="results"></div>

            <script>
                function log(message, type = 'info') {
                    const results = document.getElementById('results');
                    const div = document.createElement('div');
                    div.className = `test-section ${type}`;
                    div.innerHTML = `<strong>${new Date().toLocaleTimeString()}:</strong> ${message}`;
                    results.appendChild(div);
                }

                function checkGeolocationSupport() {
                    const resultDiv = document.getElementById('support-result');

                    if (navigator.geolocation) {
                        resultDiv.innerHTML = '<div class="success">✅ Геолокация поддерживается браузером</div>';
                        log('Геолокация поддерживается браузером', 'success');
                    } else {
                        resultDiv.innerHTML = '<div class="error">❌ Геолокация не поддерживается браузером</div>';
                        log('Геолокация не поддерживается браузером', 'error');
                    }
                }

                function getCurrentLocation() {
                    const resultDiv = document.getElementById('location-result');
                    resultDiv.innerHTML = '<div class="info">⏳ Получаем местоположение...</div>';

                    if (!navigator.geolocation) {
                        resultDiv.innerHTML = '<div class="error">❌ Геолокация не поддерживается</div>';
                        return;
                    }

                    navigator.geolocation.getCurrentPosition(
                        function(position) {
                            const coords = position.coords;
                            const accuracy = coords.accuracy;
                            const timestamp = new Date(position.timestamp);

                            resultDiv.innerHTML = `
                                <div class="success">
                                    ✅ Местоположение получено успешно!<br>
                                    <strong>Координаты:</strong> ${coords.latitude}, ${coords.longitude}<br>
                                    <strong>Точность:</strong> ±${accuracy} метров<br>
                                    <strong>Время:</strong> ${timestamp.toLocaleString()}
                                </div>
                            `;

                            log(`Местоположение получено: ${coords.latitude}, ${coords.longitude}`, 'success');
                        },
                        function(error) {
                            let errorMessage = '';
                            switch(error.code) {
                                case error.PERMISSION_DENIED:
                                    errorMessage = '❌ Доступ к местоположению запрещен пользователем';
                                    break;
                                case error.POSITION_UNAVAILABLE:
                                    errorMessage = '❌ Информация о местоположении недоступна';
                                    break;
                                case error.TIMEOUT:
                                    errorMessage = '❌ Превышено время ожидания получения местоположения';
                                    break;
                                case error.UNKNOWN_ERROR:
                                    errorMessage = '❌ Произошла неизвестная ошибка';
                                    break;
                            }

                            resultDiv.innerHTML = `<div class="error">${errorMessage}</div>`;
                            log(`Ошибка геолокации: ${errorMessage}`, 'error');
                        },
                        {
                            enableHighAccuracy: true,
                            timeout: 10000,
                            maximumAge: 60000
                        }
                    );
                }

                function checkHTTPS() {
                    const resultDiv = document.getElementById('https-result');
                    const isHTTPS = window.location.protocol === 'https:';
                    const isLocalhost = window.location.hostname === 'localhost' || 
                                       window.location.hostname === '127.0.0.1';

                    if (isHTTPS || isLocalhost) {
                        resultDiv.innerHTML = '<div class="success">✅ Протокол подходит для геолокации</div>';
                        log('Протокол подходит для геолокации', 'success');
                    } else {
                        resultDiv.innerHTML = '<div class="error">❌ Для геолокации требуется HTTPS</div>';
                        log('Для геолокации требуется HTTPS', 'error');
                    }
                }

                // Автоматические проверки при загрузке
                window.onload = function() {
                    log('Страница загружена, начинаем диагностику...', 'info');
                    checkGeolocationSupport();
                    checkHTTPS();
                };
            </script>
        </body>
        </html>
    ''')


@app.route('/')
def home():
    user_id = request.cookies.get('user_id')
    user_notifications = notifications.get(user_id, [])
    unread_notifications = [
        n for n in user_notifications
        if datetime.now() - n['timestamp'] < timedelta(minutes=5)
    ]
    has_profile = Profile.query.get(user_id)
    navbar = render_navbar(
        user_id,
        active=None,
        unread_messages=get_unread_messages_count(user_id),
        unread_likes=get_unread_likes_count(user_id)
    )
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Знакомства в кафе</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { text-align: center; padding: 20px; }
                h1 { color: #ff6b6b; margin-top: 20px; }
                .welcome-message {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    padding: 30px;
                    border-radius: 20px;
                    margin: 20px auto;
                    max-width: 600px;
                    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
                    text-align: center;
                }
                .welcome-text {
                    font-size: 1.4em;
                    font-weight: bold;
                    margin: 0 0 15px 0;
                    color: #fff;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .welcome-description {
                    font-size: 1.1em;
                    line-height: 1.6;
                    margin: 0 0 20px 0;
                    color: #f8f9fa;
                    opacity: 0.95;
                }
                .welcome-price {
                    font-size: 1.2em;
                    font-weight: bold;
                    margin: 0;
                    color: #ffd700;
                    text-shadow: 0 2px 4px rgba(0,0,0,0.2);
                    background: rgba(255,255,255,0.1);
                    padding: 10px 20px;
                    border-radius: 25px;
                    display: inline-block;
                }
                .notification { position: fixed; top: 60px; left: 50%; transform: translateX(-50%); background: #4CAF50; color: white; padding: 15px 25px; border-radius: 30px; animation: fadeInOut 4s forwards; }
                @keyframes fadeInOut {
                    0% { opacity: 0; top: 0; }
                    10% { opacity: 1; top: 60px; }
                    90% { opacity: 1; top: 60px; }
                    100% { opacity: 0; top: 0; }
                }
                .big-create-btn {
                    display: inline-flex;
                    align-items: center;
                    justify-content: center;
                    margin: 20px auto 0 auto;
                    padding: 22px 40px;
                    font-size: 1.3em;
                    font-weight: bold;
                    background: linear-gradient(90deg, #ff6b6b 0%, #ffb86b 100%);
                    color: #fff;
                    border: none;
                    border-radius: 40px;
                    box-shadow: 0 6px 24px rgba(255,107,107,0.15);
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    gap: 12px;
                }
                .big-create-btn:hover {
                    box-shadow: 0 12px 32px rgba(255,107,107,0.25);
                    transform: translateY(-2px) scale(1.04);
                }
                .big-create-btn .icon {
                    font-size: 1.5em;
                    margin-right: 10px;
                }
                .session-restore-notification {
                    position: fixed;
                    top: 60px;
                    left: 50%;
                    transform: translateX(-50%);
                    background: #2196F3;
                    color: white;
                    padding: 15px 25px;
                    border-radius: 30px;
                    z-index: 1000;
                    animation: fadeInOut 4s forwards;
                }
            </style>
        </head>
        <body>
            {{ navbar|safe }}
            {% for notification in unread_notifications %}
                <div class="notification">{{ notification.message }}</div>
            {% endfor %}
            <div class="welcome-message">
                <p class="welcome-text">Хотите найти приятную компанию за чашечкой кофе? ☕</p>
                <p class="welcome-description">Наше приложение поможет вам познакомиться с интересными людьми в кафе — для душевных бесед, новых знакомств или просто хорошего времени.</p>
                <p class="welcome-price">Регистрация — всего 50 рублей, а возможности — бесценны! 😊</p>
            </div>
            <h1>Добро пожаловать в наше кафе! 🎉</h1>
            <p style="color: white;">Здесь вы можете найти интересных людей для общения.</p>
            <div id="create-profile-section" style="display: {% if not has_profile %}block{% else %}none{% endif %};">
                <a href="/create" class="big-create-btn">
                    <span class="icon">📝</span> Создать анкету
                </a>
            </div>

            <script>
                // Функции для работы с cookie и localStorage
                function getCookie(name) {
                    const value = `; ${document.cookie}`;
                    const parts = value.split(`; ${name}=`);
                    if (parts.length === 2) return parts.pop().split(';').shift();
                    return null;
                }

                function setCookie(name, value, days = 365) {
                    const expires = new Date();
                    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
                    document.cookie = `${name}=${value}; expires=${expires.toUTCString()}; path=/`;
                }

                function saveUserId(userId) {
                    if (userId) {
                        localStorage.setItem('dating_app_user_id', userId);
                        sessionStorage.setItem('dating_app_user_id', userId);
                    }
                }

                function getUserIdFromStorage() {
                    return localStorage.getItem('dating_app_user_id') || sessionStorage.getItem('dating_app_user_id');
                }

                function showNotification(message, type = 'info') {
                    const notification = document.createElement('div');
                    notification.className = 'session-restore-notification';
                    notification.textContent = message;
                    document.body.appendChild(notification);

                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.parentNode.removeChild(notification);
                        }
                    }, 4000);
                }

                // Автоматическое восстановление сессии
                async function autoRestoreSession() {
                    console.log('🔄 Начинаем автоматическое восстановление сессии...');

                    const cookie = getCookie('user_id');
                    const storage = getUserIdFromStorage();

                    console.log('🍪 Cookie user_id:', cookie);
                    console.log('💾 Storage user_id:', storage);

                    const userId = cookie || storage;

                    if (userId) {
                        console.log('✅ Найден user_id:', userId);

                        try {
                            console.log('🌐 Проверяем профиль через API...');
                            const response = await fetch(`/api/check-profile/${userId}`);
                            const data = await response.json();

                            console.log('📊 Ответ API:', data);

                            if (data.success && data.exists) {
                                console.log('✅ Профиль найден! Восстанавливаем сессию...');

                                // Восстанавливаем сессию
                                setCookie('user_id', userId);
                                saveUserId(userId);

                                // Скрываем кнопку создания анкеты
                                const createSection = document.getElementById('create-profile-section');
                                if (createSection) {
                                    createSection.style.display = 'none';
                                    console.log('✅ Кнопка создания анкеты скрыта');
                                }

                                console.log('✅ Сессия восстановлена, возвращаем true для перенаправления');
                                return true;
                            } else {
                                console.log('❌ Профиль не найден или ошибка API');

                                // Показываем кнопку создания анкеты, если профиль не найден
                                const createSection = document.getElementById('create-profile-section');
                                if (createSection) {
                                    createSection.style.display = 'block';
                                    console.log('✅ Кнопка создания анкеты показана');
                                }
                            }
                        } catch (error) {
                            console.error('❌ Ошибка при восстановлении сессии:', error);
                        }
                    } else {
                        console.log('❌ User ID не найден');
                    }

                    return false;
                }

                // Функция для обновления состояния кнопки создания анкеты
                async function updateCreateButtonState() {
                    const userId = getCookie('user_id') || getUserIdFromStorage();
                    const createSection = document.getElementById('create-profile-section');

                    if (userId && createSection) {
                        try {
                            const response = await fetch(`/api/check-profile/${userId}`);
                            const data = await response.json();

                            if (data.success && data.exists) {
                                // Профиль существует - скрываем кнопку
                                createSection.style.display = 'none';
                                console.log('✅ Профиль существует, кнопка создания скрыта');
                            } else {
                                // Профиль не существует - показываем кнопку
                                createSection.style.display = 'block';
                                console.log('❌ Профиль не существует, кнопка создания показана');
                            }
                        } catch (error) {
                            console.error('❌ Ошибка при проверке состояния профиля:', error);
                            // В случае ошибки показываем кнопку
                            createSection.style.display = 'block';
                        }
                    } else if (createSection) {
                        // Нет user_id - показываем кнопку
                        createSection.style.display = 'block';
                        console.log('❌ Нет user_id, кнопка создания показана');
                    }
                }

                // Запускаем восстановление сессии при загрузке страницы
                window.onload = function() {
                    console.log('🚀 Страница загружена, начинаем восстановление сессии...');

                    // Проверяем тип устройства
                    const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
                    console.log('📱 Тип устройства:', isMobile ? 'Мобильное' : 'Десктопное');

                    // На мобильных устройствах увеличиваем задержку
                    const delay = isMobile ? 1000 : 500;

                    setTimeout(async () => {
                        console.log('⏰ Запускаем восстановление сессии с задержкой:', delay + 'ms');
                        const restored = await autoRestoreSession();
                        if (!restored) {
                            console.log('❌ Сессия не восстановлена, пользователь может создать новую анкету');
                            // Обновляем состояние кнопки
                            await updateCreateButtonState();
                        } else {
                            // Если сессия восстановлена, сразу перенаправляем на профиль
                            console.log('✅ Сессия восстановлена, перенаправляем на профиль');
                            window.location.href = '/my_profile';
                        }
                    }, delay);
                };
            </script>
        </body>
        </html>
    ''', unread_notifications=unread_notifications, navbar=navbar, has_profile=has_profile,
                                  get_starry_night_css=get_starry_night_css)


@app.route('/create', methods=['GET', 'POST'])
def create_profile():
    # Получаем user_id из cookie или генерируем новый
    user_id = request.cookies.get('user_id')

    # Проверяем, есть ли уже анкета у пользователя (для GET и POST запросов)
    if user_id:
        existing_profile = Profile.query.get(user_id)
        if existing_profile:
            if request.method == 'POST':
                return jsonify({
                    'success': False,
                    'error': 'У вас уже есть анкета. Вы можете создать только одну анкету.',
                    'has_active_profile': True
                }), 400
            else:
                # Для GET запроса перенаправляем на профиль
                return redirect(url_for('view_profile', id=user_id))

    if request.method == 'POST':
        # Если нет user_id, генерируем новый
        if not user_id:
            user_id = str(uuid.uuid4())
    if request.method == 'POST':
        # Валидация длины полей
        name = request.form.get('name', '').strip()
        hobbies = request.form.get('hobbies', '').strip()
        goal = request.form.get('goal', '').strip()
        
        if len(name) > 12:
            return jsonify({
                'success': False,
                'error': 'Имя не должно превышать 12 символов'
            }), 400
            
        if len(hobbies) > 70:
            return jsonify({
                'success': False,
                'error': 'Увлечения не должны превышать 70 символов'
            }), 400
            
        if len(goal) > 70:
            return jsonify({
                'success': False,
                'error': 'Цель знакомства не должна превышать 70 символов'
            }), 400
        
        photo = request.files['photo']
        venue = request.form.get('venue')
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        venue_lat = request.form.get('venue_lat')
        venue_lng = request.form.get('venue_lng')

        # Проверяем расстояние между пользователем и заведением
        if latitude and longitude and venue_lat and venue_lng:
            try:
                from geopy.distance import geodesic

                user_point = (float(latitude), float(longitude))
                venue_point = (float(venue_lat), float(venue_lng))

                distance = geodesic(user_point, venue_point).meters

                if distance > MAX_REGISTRATION_DISTANCE:
                    return jsonify({
                        'success': False,
                        'error': f'Уважаемый, Вы далеко от кафе, подойдите ближе. Расстояние: {distance / 1000:.1f} км, максимум: {MAX_REGISTRATION_DISTANCE / 1000:.1f} км'
                    }), 400

            except (ValueError, TypeError) as e:
                return jsonify({
                    'success': False,
                    'error': 'Ошибка при расчете расстояния'
                }), 400

        # Автоматически определяем город/поселок по координатам
        location_name = None
        if latitude and longitude:
            try:
                lat = float(latitude)
                lon = float(longitude)
                location_name = get_location_name(lat, lon)
            except (ValueError, TypeError):
                pass

        try:
            if photo and photo.filename:
                filename = f"{user_id}_{photo.filename}"
                photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                photo.save(photo_path)
                profile = Profile(
                    id=user_id,
                    name=name,
                    age=int(request.form['age']),
                    gender=request.form['gender'],
                    hobbies=hobbies,
                    goal=goal,
                    city=location_name,
                    venue=venue,
                    photo=filename,
                    likes=0,
                    latitude=float(latitude) if latitude else None,
                    longitude=float(longitude) if longitude else None
                )
                db.session.add(profile)
                db.session.commit()

                # Возвращаем JSON ответ для AJAX запроса
                resp = jsonify({
                    'success': True,
                    'user_id': user_id,
                    'redirect': url_for('view_profile', id=user_id)
                })
                resp.set_cookie('user_id', user_id)
                return resp
            else:
                return jsonify({
                    'success': False,
                    'error': 'Фото обязательно для создания анкеты'
                }), 400
        except Exception as e:
            db.session.rollback()
            return jsonify({
                'success': False,
                'error': f'Ошибка при создании анкеты: {str(e)}'
            }), 500
    navbar = render_navbar(user_id, active=None, unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Создать анкету</title>
            <script src="https://api-maps.yandex.ru/2.1/?apikey=9a3beffb-a8a0-4d55-850f-d258dd28c104&lang=ru_RU" type="text/javascript"></script>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%);
                    background-size: 400% 400%;
                    animation: starryNight 15s ease infinite;
                    position: relative;
                    min-height: 100vh;
                }

                @keyframes starryNight {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }

                body::before {
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-image: 
                        radial-gradient(2px 2px at 20px 30px, #eee, transparent),
                        radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
                        radial-gradient(1px 1px at 90px 40px, #fff, transparent),
                        radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.6), transparent),
                        radial-gradient(2px 2px at 160px 30px, #ddd, transparent);
                    background-repeat: repeat;
                    background-size: 200px 100px;
                    animation: twinkle 4s ease-in-out infinite alternate;
                    pointer-events: none;
                    z-index: 1;
                }

                @keyframes twinkle {
                    0% { opacity: 0.3; }
                    100% { opacity: 1; }
                }

                .form-container {
                    position: relative;
                    z-index: 2;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }

                h2 {
                    color: #fff;
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                }

                input, textarea, select { 
                    width: 100%; 
                    padding: 12px; 
                    margin: 0; 
                    background: rgba(76, 175, 80, 0.1);
                    border: 1px solid rgba(76, 175, 80, 0.3);
                    border-radius: 10px;
                    color: #fff;
                    font-size: 1em;
                    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
                    box-sizing: border-box;
                }

                input::placeholder, textarea::placeholder, select::placeholder {
                    color: rgba(255, 255, 255, 0.7);
                    text-shadow: 0 0 3px rgba(255, 255, 255, 0.2);
                }

                input:focus, textarea:focus, select:focus {
                    outline: none;
                    border-color: #4CAF50;
                    box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);
                    background: rgba(76, 175, 80, 0.15);
                }

                select option {
                    background: rgba(76, 175, 80, 0.9);
                    color: #fff;
                    border: none;
                }

                select option:hover {
                    background: rgba(76, 175, 80, 1);
                }
                

                
                .field-container {
                    position: relative;
                    width: 100%;
                    margin-bottom: 10px;
                }

                input[type="file"] {
                    background: rgba(76, 175, 80, 0.1);
                    border: 1px solid rgba(76, 175, 80, 0.3);
                    color: #fff;
                    padding: 12px;
                    border-radius: 10px;
                    cursor: pointer;
                }

                input[type="file"]:focus {
                    outline: none;
                    border-color: #4CAF50;
                    box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);
                    background: rgba(76, 175, 80, 0.15);
                }

                input[type="file"]::-webkit-file-upload-button {
                    background: rgba(76, 175, 80, 0.3);
                    color: #fff;
                    border: 1px solid rgba(76, 175, 80, 0.5);
                    border-radius: 5px;
                    padding: 8px 12px;
                    cursor: pointer;
                    margin-right: 10px;
                }

                input[type="file"]::-webkit-file-upload-button:hover {
                    background: rgba(76, 175, 80, 0.5);
                }

                label {
                    color: #fff;
                    font-weight: bold;
                    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
                }

                .modern-btn {
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: bold;
                }
                .modern-btn:hover {
                    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
                    transform: translateY(-3px) scale(1.05);
                }
                .back-btn {
                    background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(108,117,125,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                }
                .back-btn:hover {
                    box-shadow: 0 8px 24px rgba(108,117,125,0.3);
                    transform: translateY(-2px) scale(1.03);
                }

                .map-container {
                    margin: 20px 0;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                }

                #map {
                    width: 100%;
                    height: 300px;
                    border-radius: 15px;
                }

                .location-info {
                    background: rgba(76, 175, 80, 0.1);
                    border: 1px solid rgba(76, 175, 80, 0.3);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                    color: #fff;
                    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
                }

                .location-btn {
                    background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 20px;
                    font-size: 1em;
                    cursor: pointer;
                    margin: 5px;
                    transition: all 0.3s ease;
                }
                .location-btn:hover {
                    box-shadow: 0 4px 16px rgba(76,175,80,0.3);
                    transform: translateY(-2px);
                }

                .location-return-btn {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: linear-gradient(90deg, #2196F3 0%, #64B5F6 100%);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 10px rgba(33, 150, 243, 0.3);
                    z-index: 1000;
                    font-weight: bold;
                }

                .location-return-btn:hover {
                    box-shadow: 0 4px 16px rgba(33, 150, 243, 0.5);
                    transform: translateY(-2px) scale(1.05);
                    background: linear-gradient(90deg, #1976D2 0%, #42A5F5 100%);
                }

                .map-container {
                    position: relative;
                }
            </style>
        </head>
        <body>
            {{ navbar|safe }}
            <div class="form-container">
                <h2 style="text-align: center; margin-top: 10px;">Создать анкету</h2>
                <p style="color: #fff; opacity: 0.8; margin-bottom: 20px; text-align: center;">
                    📍 Ваше местоположение будет определено автоматически
                </p>
                <form method="post" enctype="multipart/form-data">
                <div class="field-container">
                    <input type="text" name="name" placeholder="Ваше имя" required maxlength="12" oninput="checkFieldLength(this, 12)">
                </div>
                <div class="field-container">
                    <input type="number" name="age" placeholder="Ваш возраст" required>
                </div>
                <div class="field-container">
                    <select name="gender" required>
                        <option value="">Выберите пол</option>
                        <option value="male">Мужской</option>
                        <option value="female">Женский</option>
                        <option value="other">Другое</option>
                    </select>
                </div>
                <div class="field-container">
                    <textarea name="hobbies" placeholder="Ваши увлечения" required maxlength="70" oninput="checkFieldLength(this, 70)"></textarea>
                </div>
                <div class="field-container">
                    <textarea name="goal" placeholder="Цель знакомства" required maxlength="70" oninput="checkFieldLength(this, 70)"></textarea>
                </div>

                    <div class="map-container">
                        <div id="map"></div>
                        <button type="button" id="return-to-location-btn" class="location-return-btn" onclick="returnToMyLocation()" style="display: none;">
                            📍 Я тут
                        </button>
                    </div>



                <div class="field-container">
                    <input type="text" name="venue" id="venue-input" placeholder="Название заведения (кафе, ресторан и т.д.)" required onchange="updateVenueCoordinates()">
                </div>
                <input type="hidden" name="latitude" id="latitude-input">
                <input type="hidden" name="longitude" id="longitude-input">
                <input type="hidden" name="venue_lat" id="venue-lat-input">
                <input type="hidden" name="venue_lng" id="venue-lng-input">

                <!-- Скрытые поля для координат и расстояния (используются для расчетов) -->
                <input type="hidden" id="visitor-coordinates-display">
                <input type="hidden" id="venue-coordinates-display">
                <input type="hidden" id="distance-display">

                <div class="field-container">
                    <input type="file" name="photo" accept="image/*" required>
                </div>

                <div class="terms-checkbox-container" style="margin: 20px 0; padding: 15px; background: rgba(76, 175, 80, 0.1); border-radius: 10px; border: 1px solid rgba(76, 175, 80, 0.3);">
                    <label style="display: flex; align-items: center; gap: 10px; cursor: pointer; color: #fff; font-size: 1em;">
                        <input type="checkbox" id="terms-checkbox" name="terms_accepted" required style="width: 18px; height: 18px; accent-color: #4CAF50;">
                        <span>Я ознакомился и согласен с <a href="/terms" target="_blank" style="color: #4CAF50; text-decoration: underline;">пользовательским соглашением</a></span>
                    </label>
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <button type="submit" class="modern-btn" id="create-btn" disabled>Создать</button>
                </div>
            </form>
            <div style="text-align: center; margin-top: 15px;">
                <a href="/" class="back-btn">← На главную</a>
            </div>
            </div>

            <script>
                // Функция для проверки длины полей (функциональность ограничений сохранена)
                function checkFieldLength(field, maxLength) {
                    // Функциональность ограничений остается, но без визуальных счетчиков
                    // Пользователь не сможет ввести больше символов благодаря maxlength
                }
                
                // Статическое местоположение: карта автоматически определяет местоположение пользователя
                // и делает его неизменяемым. Пользователь может только выбирать заведения.
                let myMap, myPlacemark;
                let currentLocation = null;



                function initMap() {
                    ymaps.ready(function () {
                        myMap = new ymaps.Map('map', {
                            center: [55.76, 37.64], // Москва по умолчанию
                            zoom: 10,
                            controls: ['zoomControl', 'fullscreenControl']
                        });

                        // Автоматически определяем местоположение при загрузке страницы
                        getCurrentLocation();

                        // Убираем возможность клика по карте для изменения местоположения
                        // myMap.events.add('click', function (e) {
                        //     var coords = e.get('coords');
                        //     setLocation(coords[0], coords[1]);
                        // });

                        // Добавляем обработчик для открытия балунов
                        myMap.events.add('balloonopen', function (e) {
                            console.log('🎈 Балун открыт, начинаем парсинг...');
                            // Добавляем небольшую задержку для полной загрузки балуна
                            setTimeout(function() {
                                parseBalloonAndFillVenue();
                            }, 500);
                        });
                    });
                }

                function setLocation(lat, lng) {
                    currentLocation = {lat: lat, lng: lng};

                    // Обновляем скрытые поля формы
                    document.getElementById('latitude-input').value = lat;
                    document.getElementById('longitude-input').value = lng;

                    // Обновляем поле отображения координат посетителя
                    const visitorCoordsDisplay = document.getElementById('visitor-coordinates-display');
                    if (visitorCoordsDisplay) {
                        visitorCoordsDisplay.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                    }

                    // Удаляем предыдущую метку
                    if (myPlacemark) {
                        myMap.geoObjects.remove(myPlacemark);
                    }

                    // Добавляем новую метку
                    myPlacemark = new ymaps.Placemark([lat, lng], {
                        balloonContent: 'Выбранное местоположение посетителя'
                    }, {
                        preset: 'islands#redDotIcon'
                    });

                    myMap.geoObjects.add(myPlacemark);
                    myMap.setCenter([lat, lng], 15);

                    // Показываем кнопку "Я тут" после определения местоположения
                    const returnBtn = document.getElementById('return-to-location-btn');
                    if (returnBtn) {
                        returnBtn.style.display = 'block';
                    }

                    // Определяем город/поселок (без отображения в интерфейсе)
                    getLocationName(lat, lng);

                    // Рассчитываем расстояние и обновляем поле заведения, если оно есть
                    const venueInput = document.getElementById('venue-input');
                    if (venueInput && venueInput.value.trim()) {
                        // Извлекаем оригинальное название заведения (без расстояния)
                        const venueValue = venueInput.value.trim();
                        const venueName = venueValue.replace(/\s*\(\d+\.?\d*\s*(м|км)\)$/, ''); // Убираем расстояние в скобках
                        calculateDistanceAndUpdateVenueField(venueName);
                    } else {
                        // Если заведения нет, просто рассчитываем расстояние для отображения
                        calculateDistance();
                    }

                    console.log('✅ Координаты посетителя установлены:', lat, lng);
                }

                function getCurrentLocation() {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                var lat = position.coords.latitude;
                                var lng = position.coords.longitude;
                                setLocation(lat, lng);
                            },
                            function(error) {
                                console.error('Ошибка геолокации:', error);
                            },
                            {
                                enableHighAccuracy: false,
                                timeout: 10000,
                                maximumAge: 300000
                            }
                        );
                    } else {
                        console.log('Геолокация не поддерживается вашим браузером');
                    }
                }

                // Функция возврата к своему местоположению
                function returnToMyLocation() {
                    if (currentLocation) {
                        // Возвращаем карту к местоположению пользователя
                        myMap.setCenter([currentLocation.lat, currentLocation.lng], 15);
                        console.log('📍 Возвращаемся к вашему местоположению:', currentLocation.lat, currentLocation.lng);
                    } else {
                        // Если местоположение не определено, определяем заново
                        console.log('📍 Местоположение не определено, определяем заново...');
                        getCurrentLocation();
                    }
                }

                // Функция clearLocation удалена, так как местоположение теперь статическое
                // function clearLocation() {
                //     // Код удален
                // }

                // Функция очистки координат заведения
                function clearVenueCoordinates() {
                    const venueCoordsDisplay = document.getElementById('venue-coordinates-display');
                    if (venueCoordsDisplay) {
                        venueCoordsDisplay.value = '';
                    }

                    // Очищаем расстояние из поля заведения
                    const venueInput = document.getElementById('venue-input');
                    if (venueInput && venueInput.value.trim()) {
                        const venueValue = venueInput.value.trim();
                        const venueName = venueValue.replace(/\s*\(\d+\.?\d*\s*(м|км)\)$/, ''); // Убираем расстояние в скобках
                        venueInput.value = venueName;
                    }

                    console.log('✅ Координаты заведения очищены');

                    // Очищаем расстояние
                    clearDistance();
                }

                // Функция расчета расстояния между посетителем и заведением
                function calculateDistance() {
                    const visitorCoordsDisplay = document.getElementById('visitor-coordinates-display');
                    const venueCoordsDisplay = document.getElementById('venue-coordinates-display');
                    const distanceDisplay = document.getElementById('distance-display');

                    if (!visitorCoordsDisplay || !venueCoordsDisplay || !distanceDisplay) {
                        return;
                    }

                    const visitorCoords = visitorCoordsDisplay.value.trim();
                    const venueCoords = venueCoordsDisplay.value.trim();

                    if (!visitorCoords || !venueCoords) {
                        distanceDisplay.value = '';
                        return;
                    }

                    try {
                        // Парсим координаты
                        const [visitorLat, visitorLng] = visitorCoords.split(',').map(coord => parseFloat(coord.trim()));
                        const [venueLat, venueLng] = venueCoords.split(',').map(coord => parseFloat(coord.trim()));

                        if (isNaN(visitorLat) || isNaN(visitorLng) || isNaN(venueLat) || isNaN(venueLng)) {
                            distanceDisplay.value = 'Ошибка в координатах';
                            return;
                        }

                        // Отправляем запрос на сервер для расчета расстояния
                        fetch('/api/calculate-distance', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                visitor_lat: visitorLat,
                                visitor_lng: visitorLng,
                                venue_lat: venueLat,
                                venue_lng: venueLng
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                const distance = data.distance;
                                if (distance < 1000) {
                                    distanceDisplay.value = `${Math.round(distance)} метров`;
                                } else {
                                    distanceDisplay.value = `${(distance / 1000).toFixed(2)} км`;
                                }
                                console.log('✅ Расстояние рассчитано:', distance, 'метров');
                            } else {
                                distanceDisplay.value = 'Ошибка расчета';
                                console.error('❌ Ошибка расчета расстояния:', data.error);
                            }
                        })
                        .catch(error => {
                            distanceDisplay.value = 'Ошибка сети';
                            console.error('❌ Ошибка сети при расчете расстояния:', error);
                        });

                    } catch (error) {
                        distanceDisplay.value = 'Ошибка в координатах';
                        console.error('❌ Ошибка парсинга координат:', error);
                    }
                }

                // Функция расчета расстояния и обновления поля заведения
                function calculateDistanceAndUpdateVenueField(venueName) {
                    const visitorCoordsDisplay = document.getElementById('visitor-coordinates-display');
                    const venueCoordsDisplay = document.getElementById('venue-coordinates-display');
                    const venueInput = document.getElementById('venue-input');
                    const distanceDisplay = document.getElementById('distance-display');

                    if (!visitorCoordsDisplay || !venueCoordsDisplay || !venueInput) {
                        return;
                    }

                    const visitorCoords = visitorCoordsDisplay.value.trim();
                    const venueCoords = venueCoordsDisplay.value.trim();

                    if (!visitorCoords || !venueCoords) {
                        // Если нет координат посетителя, просто обновляем поле заведения без расстояния
                        venueInput.value = venueName;
                        if (distanceDisplay) {
                            distanceDisplay.value = '';
                        }
                        return;
                    }

                    try {
                        // Парсим координаты
                        const [visitorLat, visitorLng] = visitorCoords.split(',').map(coord => parseFloat(coord.trim()));
                        const [venueLat, venueLng] = venueCoords.split(',').map(coord => parseFloat(coord.trim()));

                        if (isNaN(visitorLat) || isNaN(visitorLng) || isNaN(venueLat) || isNaN(venueLng)) {
                            venueInput.value = venueName;
                            if (distanceDisplay) {
                                distanceDisplay.value = 'Ошибка в координатах';
                            }
                            return;
                        }

                        // Отправляем запрос на сервер для расчета расстояния
                        fetch('/api/calculate-distance', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                visitor_lat: visitorLat,
                                visitor_lng: visitorLng,
                                venue_lat: venueLat,
                                venue_lng: venueLng
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                const distance = data.distance;
                                let distanceText;

                                if (distance < 1000) {
                                    distanceText = `${Math.round(distance)} м`;
                                } else {
                                    distanceText = `${(distance / 1000).toFixed(1)} км`;
                                }

                                // Обновляем поле заведения с расстоянием в скобках
                                venueInput.value = `${venueName} (${distanceText})`;

                                // Также обновляем поле расстояния
                                if (distanceDisplay) {
                                    if (distance < 1000) {
                                        distanceDisplay.value = `${Math.round(distance)} метров`;
                                    } else {
                                        distanceDisplay.value = `${(distance / 1000).toFixed(2)} км`;
                                    }
                                }

                                console.log('✅ Расстояние рассчитано и добавлено к названию заведения:', distance, 'метров');
                            } else {
                                venueInput.value = venueName;
                                if (distanceDisplay) {
                                    distanceDisplay.value = 'Ошибка расчета';
                                }
                                console.error('❌ Ошибка расчета расстояния:', data.error);
                            }
                        })
                        .catch(error => {
                            venueInput.value = venueName;
                            if (distanceDisplay) {
                                distanceDisplay.value = 'Ошибка сети';
                            }
                            console.error('❌ Ошибка сети при расчете расстояния:', error);
                        });

                    } catch (error) {
                        venueInput.value = venueName;
                        if (distanceDisplay) {
                            distanceDisplay.value = 'Ошибка в координатах';
                        }
                        console.error('❌ Ошибка парсинга координат:', error);
                    }
                }

                // Функция очистки расстояния
                function clearDistance() {
                    const distanceDisplay = document.getElementById('distance-display');
                    if (distanceDisplay) {
                        distanceDisplay.value = '';
                    }
                }

                function getLocationName(lat, lng) {
                    // Отправляем запрос на сервер для получения названия города/поселка (без отображения в интерфейсе)
                    fetch('/api/get-location-name', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            latitude: lat,
                            longitude: lng
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('📍 Определен город/поселок:', data.location_name);
                        } else {
                            console.log('❌ Не удалось определить город/поселок');
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка при получении названия города/поселка:', error);
                    });
                }

                // Функция парсинга балуна
                function extractNameFromBalloon() {
                    try {
                        console.log('🔍 Начинаем парсинг балуна...');

                        // Ищем балун по всем возможным селекторам
                        let balloonContent = document.querySelector('.ymaps-2-1-79-balloon');
                        if (!balloonContent) {
                            balloonContent = document.querySelector('.ymaps-balloon');
                        }
                        if (!balloonContent) {
                            balloonContent = document.querySelector('.balloon');
                        }
                        if (!balloonContent) {
                            balloonContent = document.querySelector('[class*="balloon"]');
                        }
                        if (!balloonContent) {
                            balloonContent = document.querySelector('[class*="ymaps"]');
                        }

                        if (!balloonContent) {
                            console.log('❌ Балун не найден');
                            return null;
                        }

                        console.log('✅ Балун найден:', balloonContent.className);

                        // Получаем HTML контент
                        const htmlContent = balloonContent.innerHTML;
                        console.log('📏 Размер HTML:', htmlContent.length, 'символов');

                        // Ищем все ссылки в балуне
                        const links = balloonContent.querySelectorAll('a');
                        console.log('🔗 Найдено ссылок:', links.length);

                        const foundLinks = [];
                        let firstValidName = null;

                        if (links.length > 0) {
                            for (let i = 0; i < links.length; i++) {
                                const link = links[i];
                                const linkText = link.textContent.trim();
                                console.log(`🔗 Ссылка ${i + 1}: "${linkText}"`);
                                foundLinks.push(linkText);

                                // Проверяем, что это не служебная ссылка
                                if (isValidVenueName(linkText)) {
                                    // Сохраняем первое валидное название
                                    if (!firstValidName) {
                                        firstValidName = linkText;
                                        console.log(`✅ Найдено первое название в ссылке: "${linkText}"`);
                                    }
                                }
                            }
                        }

                        // Ищем заголовки
                        const headers = balloonContent.querySelectorAll('h1, h2, h3, h4, h5, h6');
                        console.log('📋 Найдено заголовков:', headers.length);

                        for (let header of headers) {
                            const headerText = header.textContent.trim();
                            console.log(`📋 Заголовок: "${headerText}"`);
                            foundLinks.push(headerText);

                            if (isValidVenueName(headerText)) {
                                // Сохраняем первое валидное название
                                if (!firstValidName) {
                                    firstValidName = headerText;
                                    console.log(`✅ Найдено первое название в заголовке: "${headerText}"`);
                                }
                            }
                        }

                        // Ищем элементы с классами name/title
                        const nameElements = balloonContent.querySelectorAll('[class*="name"], [class*="title"]');
                        console.log('🏷️ Найдено элементов с name/title:', nameElements.length);

                        for (let element of nameElements) {
                            const elementText = element.textContent.trim();
                            console.log(`🏷️ Элемент с name/title: "${elementText}"`);
                            foundLinks.push(elementText);

                            if (isValidVenueName(elementText)) {
                                // Сохраняем первое валидное название
                                if (!firstValidName) {
                                    firstValidName = elementText;
                                    console.log(`✅ Найдено первое название в элементе с name/title: "${elementText}"`);
                                }
                            }
                        }

                        // Последняя попытка - ищем первый значимый текстовый элемент
                        const allElements = balloonContent.querySelectorAll('*');
                        console.log('🔍 Всего элементов в балуне:', allElements.length);

                        for (let element of allElements) {
                            const text = element.textContent.trim();
                            if (isValidVenueName(text)) {
                                // Сохраняем первое валидное название
                                if (!firstValidName) {
                                    firstValidName = text;
                                    console.log(`✅ Найдено первое название в текстовом элементе: "${text}"`);
                                }
                            }
                        }

                        if (firstValidName) {
                            console.log(`✅ Возвращаем первое найденное название: "${firstValidName}"`);
                            return { name: firstValidName, links: foundLinks };
                        } else {
                            console.log('❌ Название не найдено');
                            return { name: null, links: foundLinks };
                        }

                    } catch (error) {
                        console.log('❌ Ошибка при парсинге:', error);
                        return { name: null, links: [] };
                    }
                }

                // Функция валидации названия заведения
                function isValidVenueName(name) {
                    return name && name.length > 2 && name.length < 100 &&
                        !name.includes('Share') && !name.includes('Поделиться') &&
                        !name.includes('Телефон') && !name.includes('Адрес') &&
                        !name.includes('Часы') && !name.includes('Рейтинг') &&
                        !name.includes('Открыто') && !name.includes('Закрыто') &&
                        !name.includes('www.') && !name.includes('http') &&
                        !name.includes('+7') && !name.includes('8-') &&
                        !name.match(/^\d+$/) && !name.match(/^\d+\.\d+$/) &&
                        !name.includes('отзыв') && !name.includes('отзывов') &&
                        !name.includes('Показать') && !name.includes('Написать') &&
                        !name.includes('Позвонить') && !name.includes('Поделиться') &&
                        // Исключаем названия, которые начинаются с цифры и пробела (например "1. Название")
                        !name.match(/^\d+\.\s/) && !name.match(/^\d+\s/) &&
                        // Исключаем названия, которые содержат только цифры и точки
                        !name.match(/^[\d\.\s]+$/);
                }





                // Функция парсинга балуна и заполнения поля заведения
                function parseBalloonAndFillVenue() {
                    console.log('=== ПАРСИНГ БАЛУНА ===');

                    const result = extractNameFromBalloon();

                    if (result.name) {
                        document.getElementById('venue-input').value = result.name;
                        console.log('✅ Название заведения заполнено:', result.name);

                        // Получаем координаты заведения из балуна или API
                        let venueLat = null;
                        let venueLng = null;

                        // Попытка получить координаты из балуна
                        if (result.coordinates) {
                            venueLat = result.coordinates.lat;
                            venueLng = result.coordinates.lng;
                        } else {
                            // Если координаты не найдены в балуне, используем координаты центра карты
                            const mapCenter = myMap.getCenter();
                            venueLat = mapCenter[0];
                            venueLng = mapCenter[1];
                        }

                        // Показываем координаты заведения
                        if (venueLat && venueLng) {
                            showVenueCoordinates(result.name, venueLat, venueLng);
                        }
                    } else {
                        console.log('❌ Название заведения не найдено');
                    }

                    if (result.links && result.links.length > 0) {
                        console.log('🔗 Найдено ссылок:', result.links.length);
                    } else {
                        console.log('❌ Ссылки не найдены');
                    }

                    console.log('=====================');
                }

                // Функция отображения координат заведения
                function showVenueCoordinates(venueName, lat, lng) {
                    // Удаляем предыдущий блок с координатами, если он есть
                    const existingCoordsDiv = document.getElementById('venue-coordinates');
                    if (existingCoordsDiv) {
                        existingCoordsDiv.remove();
                    }

                    // Обновляем поле отображения координат заведения
                    const venueCoordsDisplay = document.getElementById('venue-coordinates-display');
                    if (venueCoordsDisplay) {
                        venueCoordsDisplay.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                    }

                    // Заполняем скрытые поля для отправки на сервер
                    const venueLatInput = document.getElementById('venue-lat-input');
                    const venueLngInput = document.getElementById('venue-lng-input');
                    if (venueLatInput && venueLngInput) {
                        venueLatInput.value = lat.toFixed(6);
                        venueLngInput.value = lng.toFixed(6);
                    }

                    // Рассчитываем расстояние и обновляем поле заведения
                    calculateDistanceAndUpdateVenueField(venueName);

                    console.log('✅ Координаты заведения отображены:', lat, lng);
                }

                // Функция обновления координат при изменении названия заведения
                function updateVenueCoordinates() {
                    const venueInput = document.getElementById('venue-input');
                    let venueName = venueInput.value.trim();

                    // Убираем расстояние в скобках из названия заведения для обработки
                    venueName = venueName.replace(/\s*\(\d+\.?\d*\s*(м|км)\)$/, '');

                    if (venueName) {
                        // Если есть название заведения, очищаем координаты заведения
                        clearVenueCoordinates();
                    } else {
                        // Если название заведения пустое, очищаем координаты заведения
                        clearVenueCoordinates();
                    }
                }

                // Обработчик отправки формы с проверкой расстояния
                document.querySelector('form').addEventListener('submit', function(e) {
                    e.preventDefault();

                    console.log('🚀 Отправка формы...');

                    // Проверяем, что выбрано заведение
                    const venueInput = document.getElementById('venue-input');
                    const venueLatInput = document.getElementById('venue-lat-input');
                    const venueLngInput = document.getElementById('venue-lng-input');

                    console.log('📍 Заведение:', venueInput.value);
                    console.log('📍 Координаты заведения:', venueLatInput.value, venueLngInput.value);

                    if (!venueInput.value.trim()) {
                        alert('Пожалуйста, выберите заведение на карте');
                        return;
                    }

                    if (!venueLatInput.value || !venueLngInput.value) {
                        alert('Пожалуйста, выберите заведение на карте для получения координат');
                        return;
                    }

                    // Проверяем, что пользователь согласился с условиями
                    const termsCheckbox = document.getElementById('terms-checkbox');
                    if (!termsCheckbox.checked) {
                        alert('Пожалуйста, ознакомьтесь и согласитесь с пользовательским соглашением');
                        return;
                    }

                    // Проверяем размер фото
                    const photoInput = document.querySelector('input[name="photo"]');
                    if (photoInput.files.length > 0) {
                        const fileSize = photoInput.files[0].size;
                        const maxSize = 16 * 1024 * 1024; // 16MB
                        if (fileSize > maxSize) {
                            alert('Файл слишком большой. Пожалуйста, выберите фото меньшего размера (максимум 16MB)');
                            return;
                        }
                        console.log(`📸 Размер фото: ${(fileSize / 1024 / 1024).toFixed(2)} MB`);
                    }

                    // Отправляем форму через AJAX
                    const formData = new FormData(this);

                    console.log('📤 Отправляем данные на сервер...');

                    fetch('/create', {
                        method: 'POST',
                        body: formData
                    })
                    .then(response => {
                        console.log('📥 Получен ответ от сервера:', response.status, response.statusText);
                        console.log('📋 Content-Type:', response.headers.get('content-type'));

                        // Проверяем статус ответа
                        if (!response.ok) {
                            if (response.status === 413) {
                                throw new Error('Файл слишком большой. Пожалуйста, выберите фото меньшего размера (максимум 16MB)');
                            }
                            throw new Error(`HTTP error! status: ${response.status}`);
                        }

                        // Проверяем тип ответа
                        const contentType = response.headers.get('content-type');
                        if (contentType && contentType.includes('application/json')) {
                            console.log('📄 Обрабатываем JSON ответ...');
                            return response.json().then(data => {
                                console.log('📊 Данные ответа:', data);
                                if (data.success === false) {
                                    // Показываем ошибку
                                    console.log('❌ Ошибка:', data.error);
                                    alert(data.error);
                                } else {
                                    // Успешная регистрация - устанавливаем cookie, localStorage и перенаправляем
                                    console.log('✅ Успешная регистрация, перенаправляем на:', data.redirect);

                                    // Сохраняем в cookie с дополнительными параметрами для мобильных устройств
                                    const cookieValue = 'user_id=' + data.user_id + '; path=/; max-age=' + (365*24*60*60) + '; SameSite=Lax';
                                    document.cookie = cookieValue;

                                    // Сохраняем в localStorage для мобильных устройств
                                    try {
                                        localStorage.setItem('dating_app_user_id', data.user_id);
                                        sessionStorage.setItem('dating_app_user_id', data.user_id);
                                        console.log('✅ User ID сохранен в localStorage и sessionStorage');
                                    } catch (e) {
                                        console.warn('⚠️ Не удалось сохранить в localStorage:', e);
                                    }

                                    console.log('✅ User ID сохранен в cookie:', data.user_id);

                                    window.location.href = data.redirect || '/';
                                }
                            });
                        } else {
                            // Если ответ не JSON, значит это редирект - перенаправляем
                            console.log('🔄 Получен редирект, перенаправляем на:', response.url);
                            window.location.href = response.url || '/';
                        }
                    })
                    .catch(error => {
                        console.error('❌ Ошибка отправки формы:', error);
                        console.error('❌ Детали ошибки:', error.message);
                        alert('Ошибка при отправке формы: ' + error.message);
                    });
                });

                // Обработчик для галочки пользовательского соглашения
                document.getElementById('terms-checkbox').addEventListener('change', function() {
                    const createBtn = document.getElementById('create-btn');
                    if (this.checked) {
                        createBtn.disabled = false;
                        createBtn.style.opacity = '1';
                        createBtn.style.cursor = 'pointer';
                    } else {
                        createBtn.disabled = true;
                        createBtn.style.opacity = '0.5';
                        createBtn.style.cursor = 'not-allowed';
                    }
                });

                // Функция для проверки существующего профиля
                async function checkExistingProfile() {
                    const userId = getCookie('user_id') || localStorage.getItem('dating_app_user_id');

                    if (userId) {
                        try {
                            const response = await fetch(`/api/check-profile/${userId}`);
                            const data = await response.json();

                            if (data.success && data.exists) {
                                console.log('✅ Профиль уже существует, перенаправляем на профиль');
                                window.location.href = '/my_profile';
                                return true;
                            }
                        } catch (error) {
                            console.error('❌ Ошибка при проверке профиля:', error);
                        }
                    }
                    return false;
                }

                // Инициализация карты при загрузке страницы
                window.onload = function() {
                    console.log('🚀 Страница загружена, начинаем инициализацию...');
                    
                    // Проверяем, есть ли элемент карты
                    const mapElement = document.getElementById('map');
                    if (mapElement) {
                        console.log('✅ Элемент карты найден');
                    } else {
                        console.error('❌ Элемент карты не найден!');
                    }
                    
                    // На странице создания профиля карта должна инициализироваться всегда
                    console.log('🗺️ Инициализируем карту на странице создания профиля...');
                    initMap();

                    // Инициализируем состояние кнопки
                    const createBtn = document.getElementById('create-btn');
                    if (createBtn) {
                        createBtn.disabled = true;
                        createBtn.style.opacity = '0.5';
                        createBtn.style.cursor = 'not-allowed';
                        console.log('✅ Кнопка создания профиля инициализирована');
                    } else {
                        console.error('❌ Кнопка создания профиля не найдена!');
                    }
                };
            </script>
        </body>
        </html>
    ''', navbar=navbar, get_photo_url=get_photo_url, get_starry_night_css=get_starry_night_css)


def require_profile(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = request.cookies.get('user_id')
        if not user_id or Profile.query.get(user_id) is None:
            return redirect(url_for('create_profile'))
        return view_func(*args, **kwargs)

    return wrapper


@app.route('/visitors')
@require_profile
def view_visitors():
    user_id = request.cookies.get('user_id')
    # Получаем фильтры из query-параметров
    venue_query = request.args.get('venue', '').strip().lower()
    gender_query = request.args.get('gender', '')
    # Фильтруем профили
    other_profiles = [p for p in Profile.query.all() if p.id != user_id]
    if venue_query:
        other_profiles = [p for p in other_profiles if p.venue and venue_query in p.venue.lower()]
    if gender_query:
        other_profiles = [p for p in other_profiles if p.gender == gender_query]
    # liked_ids теперь из базы
    liked_ids = set(l.liked_id for l in Like.query.filter_by(user_id=user_id).all())
    navbar = render_navbar(user_id, active='visitors', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Посетители кафе</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 600px; margin: 0 auto; padding: 20px; }
                h1 { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                }
                p { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    font-size: 1.1em;
                }
                .visitor-card { 
                    background: #030202; 
                    border-radius: 15px; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
                    padding: 20px; 
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    position: relative;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .visitor-card:hover {
                    transform: translateY(-3px) scale(1.02);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
                }
                .visitor-card img { 
                    max-width: 80px; 
                    border-radius: 10px; 
                    margin-right: 15px;
                    object-fit: cover;
                    height: 80px;
                }
                .visitor-info { flex: 1; }
                .visitor-card h2 { margin: 0 0 5px 0; color: #fff; }
                .visitor-card p { margin: 5px 0; color: #fff; }
                .like-btn {
                    background: none;
                    border: none;
                    cursor: pointer;
                    outline: none;
                    font-size: 2em;
                    position: absolute;
                    top: 10px;
                    right: 18px;
                    z-index: 2;
                    padding: 0;
                    transition: transform 0.1s;
                }
                .like-btn:active { transform: scale(1.2); }
                .like-heart {
                    color: #bbb;
                    transition: color 0.2s;
                    text-shadow: 0 2px 8px rgba(255,107,107,0.12);
                }
                .like-heart.liked {
                    color: #ff6b6b;
                }
                .visitor-count {
                    font-size: 0.9em;
                    color: #888;
                    margin-bottom: 10px;
                    text-align: left;
                }
                .filter-form {
                    background: #030202;
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    padding: 20px 25px 15px 25px;
                    margin-bottom: 24px;
                    display: flex;
                    flex-wrap: wrap;
                    gap: 12px;
                    align-items: flex-end;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .filter-form label {
                    font-size: 0.95em;
                    color: #fff;
                    margin-right: 6px;
                }
                .filter-form input, .filter-form select {
                    border: 1px solid #ccc;
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-size: 1em;
                    margin-right: 10px;
                }
                .filter-form button {
                    background: linear-gradient(90deg, #ff6b6b 0%, #ffb86b 100%);
                    color: #fff;
                    border: none;
                    border-radius: 20px;
                    padding: 8px 20px;
                    font-size: 1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                }
                .filter-form button:hover {
                    box-shadow: 0 4px 16px rgba(255,107,107,0.15);
                    transform: translateY(-2px) scale(1.03);
                }
            </style>
            <script>
                function showNotification(message, type = 'info') {
                    // Удаляем существующие уведомления
                    const existingNotifications = document.querySelectorAll('.notification');
                    existingNotifications.forEach(notification => notification.remove());
                    
                    // Создаем новое уведомление
                    const notification = document.createElement('div');
                    notification.className = `notification ${type}`;
                    notification.textContent = message;
                    
                    // Добавляем в body
                    document.body.appendChild(notification);
                    
                    // Показываем уведомление
                    setTimeout(() => {
                        notification.classList.add('show');
                    }, 100);
                    
                    // Скрываем через 3 секунды
                    setTimeout(() => {
                        notification.classList.remove('show');
                        setTimeout(() => {
                            if (notification.parentNode) {
                                notification.parentNode.removeChild(notification);
                            }
                        }, 300);
                    }, 3000);
                }
                
                function toggleLike(profileId, btn) {
                    event.stopPropagation();
                    fetch('/toggle_like/' + profileId, {method: 'POST'})
                        .then(r => r.json())
                        .then(data => {
                            if (data.liked) {
                                btn.classList.add('liked');
                                showNotification('❤️ Лайк отправлен!', 'success');
                            } else if (data.already_liked) {
                                btn.classList.add('liked');
                                showNotification('💔 Вы уже лайкали эту анкету!', 'warning');
                            } else {
                                btn.classList.remove('liked');
                            }
                        });
                }
                function goToProfile(profileId) {
                    window.location.href = '/profile/' + profileId;
                }
            </script>
        </head>
        <body>
            {{ navbar|safe }}
            <form class="filter-form" method="get">
                <label>Заведение <input type="text" name="venue" value="{{ request.args.get('venue', '') }}" placeholder="Название заведения"></label>
                <label>Пол
                    <select name="gender">
                        <option value="">Любой</option>
                        <option value="male" {% if request.args.get('gender') == 'male' %}selected{% endif %}>Мужской</option>
                        <option value="female" {% if request.args.get('gender') == 'female' %}selected{% endif %}>Женский</option>
                        <option value="other" {% if request.args.get('gender') == 'other' %}selected{% endif %}>Другое</option>
                    </select>
                </label>
                <button type="submit">Фильтровать</button>
            </form>
            <div class="visitor-count">Посетителей: {{ other_profiles|length }}</div>
            <h1>Посетители кафе</h1>
            {% if other_profiles %}
                {% for profile in other_profiles %}
                    <div class="visitor-card" onclick="goToProfile('{{ profile.id }}')">
                        <img src="{{ get_photo_url(profile) }}" alt="Фото">
                        <div class="visitor-info">
                            <h2>{{ profile.name }}, {{ profile.age }}</h2>
                            <p>{{ profile.hobbies[:50] }}{% if profile.hobbies|length > 50 %}...{% endif %}</p>
                            {% if profile.city %}
                            <p style="color: #666; font-size: 0.9em;">📍 {{ profile.city }}</p>
                            {% endif %}
                            {% if profile.venue %}
                            <p style="color: #666; font-size: 0.9em;">🏪 {{ profile.venue }}</p>
                            {% endif %}
                        </div>
                        <button class="like-btn" title="Лайк" onclick="toggleLike('{{ profile.id }}', this.querySelector('span'))">
                            <span class="like-heart{% if profile.id in liked_ids %} liked{% endif %}">&#10084;</span>
                        </button>
                    </div>
                {% endfor %}
            {% else %}
                <p>Пока нет других посетителей.</p>
            {% endif %}
        </body>
        </html>
    ''', other_profiles=other_profiles, liked_ids=liked_ids, navbar=navbar, get_photo_url=get_photo_url,
                                  get_starry_night_css=get_starry_night_css)


@app.route('/toggle_like/<string:profile_id>', methods=['POST'])
@require_profile
def toggle_like(profile_id):
    user_id = request.cookies.get('user_id')
    if not user_id or Profile.query.get(profile_id) is None or profile_id == user_id:
        return jsonify({'liked': False, 'already_liked': False, 'likes_count': 0})
    # Проверяем, лайкал ли уже
    already = Like.query.filter(and_(Like.user_id == user_id, Like.liked_id == profile_id)).first()
    profile = Profile.query.get(profile_id)
    if already:
        # Уже лайкал
        likes_count = Like.query.filter_by(liked_id=profile_id).count()
        return jsonify({'liked': False, 'already_liked': True, 'likes_count': likes_count})
    # Новый лайк
    db.session.add(Like(user_id=user_id, liked_id=profile_id))
    db.session.commit()
    check_for_matches(user_id)
    likes_count = Like.query.filter_by(liked_id=profile_id).count()
    return jsonify({'liked': True, 'already_liked': False, 'likes_count': likes_count})


@app.route('/my_profile')
@require_profile
def my_profile():
    user_id = request.cookies.get('user_id')
    profile = Profile.query.get(user_id)
    navbar = render_navbar(user_id, active='profile', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Моя анкета</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { text-align: center; padding: 20px; }
                .card { 
                    background: #030202; 
                    border-radius: 15px; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
                    max-width: 400px; 
                    margin: 0 auto; 
                    padding: 25px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #fff;
                }
                img { max-width: 100%; border-radius: 10px; }
                .modern-btn {
                    background: linear-gradient(90deg, #ff6b6b 0%, #ffb86b 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(255,107,107,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    margin: 5px;
                }
                .modern-btn:hover {
                    box-shadow: 0 8px 24px rgba(255,107,107,0.3);
                    transform: translateY(-2px) scale(1.03);
                }
                .back-btn {
                    background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(108,117,125,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                }
                .back-btn:hover {
                    box-shadow: 0 8px 24px rgba(108,117,125,0.3);
                    transform: translateY(-2px) scale(1.03);
                }
            </style>
        </head>
        <body>
            {{ navbar|safe }}
            <div class="card">
                <img src="{{ get_photo_url(profile) }}" alt="Фото">
                <h2>{{ profile.name }}, {{ profile.age }}</h2>
                <p><strong>Увлечения:</strong> {{ profile.hobbies }}</p>
                <p><strong>Цель:</strong> {{ profile.goal }}</p>
                {% if profile.city %}
                <p><strong>📍 Местоположение:</strong> {{ profile.city }}</p>
                {% endif %}
                {% if profile.venue %}
                <p><strong>🏪 Заведение:</strong> {{ profile.venue }}</p>
                {% endif %}
                <form action="/edit_profile" method="get" style="display:inline;">
                    <button type="submit" class="modern-btn" style="background: #4CAF50;">Редактировать</button>
                </form>
                <form action="/delete/{{ profile.id }}" method="post" style="display:inline;">
                    <button type="submit" class="modern-btn" style="background: #b00020;">Удалить анкету</button>
                </form>
                <a href="/" class="back-btn">← На главную</a>
            </div>
        </body>
        </html>
    ''', profile=profile, navbar=navbar, get_photo_url=get_photo_url, get_starry_night_css=get_starry_night_css)


@app.route('/edit_profile', methods=['GET', 'POST'])
@require_profile
def edit_profile():
    user_id = request.cookies.get('user_id')
    profile = Profile.query.get(user_id)
    if request.method == 'POST':
        profile.name = request.form['name']
        profile.age = int(request.form['age'])
        profile.gender = request.form['gender']
        profile.hobbies = request.form['hobbies']
        profile.goal = request.form['goal']
        profile.venue = request.form.get('venue')

        # Обработка координат
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        if latitude and longitude:
            profile.latitude = float(latitude)
            profile.longitude = float(longitude)

        # Смена фото
        photo = request.files.get('photo')
        if photo and photo.filename:
            try:
                if profile.photo:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], profile.photo))
            except:
                pass
            filename = f"{user_id}_{photo.filename}"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            profile.photo = filename
        db.session.commit()
        return redirect(url_for('my_profile'))
    navbar = render_navbar(
        user_id,
        active='profile',
        unread_messages=get_unread_messages_count(user_id),
        unread_likes=get_unread_likes_count(user_id),
        unread_matches=get_unread_matches_count(user_id)
    )
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Редактировать анкету</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 500px; margin: 0 auto; padding: 20px; }
                input, textarea, select { 
                    width: 100%; 
                    padding: 12px; 
                    margin: 10px 0; 
                    background: rgba(255, 255, 255, 0.9);
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    border-radius: 10px;
                    color: #333;
                    font-size: 1em;
                }
                input:focus, textarea:focus, select:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 15px rgba(102, 126, 234, 0.3);
                }
                label {
                    color: #fff;
                    font-weight: bold;
                    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
                }
                h2 {
                    color: #fff;
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                }
                .modern-btn {
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: bold;
                }
                .modern-btn:hover {
                    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
                    transform: translateY(-3px) scale(1.05);
                }
                .back-btn {
                    background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(108,117,125,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                }
                .back-btn:hover {
                    box-shadow: 0 8px 24px rgba(108,117,125,0.3);
                    transform: translateY(-2px) scale(1.03);
                }

                .map-container {
                    margin: 20px 0;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                }

                #map {
                    width: 100%;
                    height: 300px;
                    border-radius: 15px;
                }

                .location-info {
                    background: rgba(255, 255, 255, 0.9);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                    color: #333;
                }

                .location-btn {
                    background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 20px;
                    font-size: 1em;
                    cursor: pointer;
                    margin: 5px;
                    transition: all 0.3s ease;
                }
                .location-btn:hover {
                    box-shadow: 0 4px 16px rgba(76,175,80,0.3);
                    transform: translateY(-2px);
                }
            </style>
            <script src="https://api-maps.yandex.ru/2.1/?apikey=9a3beffb-a8a0-4d55-850f-d258dd28c104&lang=ru_RU" type="text/javascript"></script>
            <script>
                let myMap, myPlacemark;
                let currentLocation = null;

                function initMap() {
                    console.log('🗺️ Начинаем инициализацию карты на странице создания профиля...');
                    ymaps.ready(function () {
                        console.log('✅ ymaps.ready() выполнен');
                        try {
                            myMap = new ymaps.Map('map', {
                                center: [55.76, 37.64], // Москва по умолчанию
                                zoom: 10,
                                controls: ['zoomControl', 'fullscreenControl']
                            });
                            console.log('✅ Карта создана успешно');

                            myMap.events.add('click', function (e) {
                                var coords = e.get('coords');
                                setLocation(coords[0], coords[1]);
                            });
                        } catch (error) {
                            console.error('❌ Ошибка при создании карты:', error);
                        }
                    });
                }

                function setLocation(lat, lng) {
                    currentLocation = {lat: lat, lng: lng};

                    // Обновляем скрытые поля формы
                    document.getElementById('latitude-input').value = lat;
                    document.getElementById('longitude-input').value = lng;

                    // Удаляем предыдущую метку
                    if (myPlacemark) {
                        myMap.geoObjects.remove(myPlacemark);
                    }

                    // Добавляем новую метку
                    myPlacemark = new ymaps.Placemark([lat, lng], {
                        balloonContent: 'Выбранное местоположение'
                    }, {
                        preset: 'islands#redDotIcon'
                    });

                    myMap.geoObjects.add(myPlacemark);
                    myMap.setCenter([lat, lng], 15);

                    // Показываем местоположение в интерфейсе
                    document.getElementById('location-address').textContent = 'Местоположение определено';
                    document.getElementById('location-coords').textContent = 'Координаты: ' + lat.toFixed(4) + ', ' + lng.toFixed(4);
                    document.getElementById('location-info').style.display = 'block';

                    // Обновляем координаты заведения, если оно уже введено
                    const venueInput = document.getElementById('venue-input');
                    if (venueInput && venueInput.value.trim()) {
                        updateVenueCoordinates();
                    }
                }

                function getCurrentLocation() {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                var lat = position.coords.latitude;
                                var lng = position.coords.longitude;
                                setLocation(lat, lng);
                            },
                            function(error) {
                                alert('Не удалось получить местоположение. Попробуйте еще раз.');
                            },
                            {
                                enableHighAccuracy: false,
                                timeout: 5000,
                                maximumAge: 300000
                            }
                        );
                } else {
                        alert('Геолокация не поддерживается вашим браузером. Попробуйте другой браузер.');
                    }
                }

                function clearLocation() {
                    currentLocation = null;
                    document.getElementById('latitude-input').value = '';
                    document.getElementById('longitude-input').value = '';
                    document.getElementById('location-info').style.display = 'none';

                    if (myPlacemark) {
                        myMap.geoObjects.remove(myPlacemark);
                        myPlacemark = null;
                    }

                    // Удаляем блок с координатами заведения
                    const existingCoordsDiv = document.getElementById('venue-coordinates');
                    if (existingCoordsDiv) {
                        existingCoordsDiv.remove();
                    }
                }

                // Функция отображения координат заведения
                function showVenueCoordinates(venueName, lat, lng) {
                    // Удаляем предыдущий блок с координатами, если он есть
                    const existingCoordsDiv = document.getElementById('venue-coordinates');
                    if (existingCoordsDiv) {
                        existingCoordsDiv.remove();
                    }

                    // Создаем новый блок с координатами
                    const coordsDiv = document.createElement('div');
                    coordsDiv.id = 'venue-coordinates';
                    coordsDiv.style.cssText = `
                        background: rgba(76, 175, 80, 0.1);
                        border: 1px solid rgba(76, 175, 80, 0.3);
                        border-radius: 8px;
                        padding: 10px;
                        margin: 10px 0;
                        color: #fff;
                        font-size: 0.9em;
                    `;

                    coordsDiv.innerHTML = `
                        <strong>📍 Координаты заведения "${venueName}":</strong><br>
                        <span style="font-family: monospace; background: rgba(0,0,0,0.2); padding: 2px 6px; border-radius: 4px;">
                            ${lat.toFixed(6)}, ${lng.toFixed(6)}
                        </span>
                    `;

                    // Вставляем блок после поля ввода заведения
                    const venueInput = document.getElementById('venue-input');
                    venueInput.parentNode.insertBefore(coordsDiv, venueInput.nextSibling);

                    console.log('✅ Координаты заведения отображены:', lat, lng);
                }

                // Функция обновления координат при изменении названия заведения
                function updateVenueCoordinates() {
                    const venueInput = document.getElementById('venue-input');
                    const venueName = venueInput.value.trim();

                    if (venueName && currentLocation) {
                        showVenueCoordinates(venueName, currentLocation.lat, currentLocation.lng);
                    } else if (venueName) {
                        // Если есть название заведения, но нет координат, показываем сообщение
                        const existingCoordsDiv = document.getElementById('venue-coordinates');
                        if (existingCoordsDiv) {
                            existingCoordsDiv.remove();
                        }

                        const coordsDiv = document.createElement('div');
                        coordsDiv.id = 'venue-coordinates';
                        coordsDiv.style.cssText = `
                            background: rgba(255, 193, 7, 0.1);
                            border: 1px solid rgba(255, 193, 7, 0.3);
                            color: #fff;
                            border-radius: 8px;
                            padding: 10px;
                            margin: 10px 0;
                            font-size: 0.9em;
                        `;

                        coordsDiv.innerHTML = `
                            <strong>⚠️ Для отображения координат заведения "${venueName}" выберите местоположение на карте</strong>
                        `;

                        venueInput.parentNode.insertBefore(coordsDiv, venueInput.nextSibling);
                    }
                }

                // Инициализация карты при загрузке страницы
                window.onload = function() {
                    initMap();

                    // Если у профиля есть координаты, устанавливаем их как текущее местоположение
                    {% if profile.latitude and profile.longitude %}
                    currentLocation = {
                        lat: {{ profile.latitude }},
                        lng: {{ profile.longitude }}
                    };

                    // Если есть название заведения, показываем координаты
                    {% if profile.venue %}
                    setTimeout(function() {
                        showVenueCoordinates('{{ profile.venue }}', {{ profile.latitude }}, {{ profile.longitude }});
                    }, 1000);
                    {% endif %}
                    {% endif %}
                };
            </script>
        </head>
        <body>
            {{ navbar|safe }}
            <h2>Редактировать анкету</h2>
            <form method="post" enctype="multipart/form-data">
                <input type="text" name="name" placeholder="Ваше имя" value="{{ profile.name }}" required>
                <input type="number" name="age" placeholder="Ваш возраст" value="{{ profile.age }}" required>
                <select name="gender" required>
                    <option value="">Выберите пол</option>
                    <option value="male" {% if profile.gender == 'male' %}selected{% endif %}>Мужской</option>
                    <option value="female" {% if profile.gender == 'female' %}selected{% endif %}>Женский</option>
                    <option value="other" {% if profile.gender == 'other' %}selected{% endif %}>Другое</option>
                </select>
                <textarea name="hobbies" placeholder="Ваши увлечения" required>{{ profile.hobbies }}</textarea>
                <textarea name="goal" placeholder="Цель знакомства" required>{{ profile.goal }}</textarea>

                <div class="map-container">
                    <div id="map"></div>
                    <div class="location-info" id="location-info" style="display: {% if profile.latitude and profile.longitude %}block{% else %}none{% endif %};">
                        <strong>Выбранное местоположение:</strong><br>
                        <span id="location-address">Местоположение определено</span><br>
                        <small>Координаты: <span id="location-coords">{% if profile.latitude and profile.longitude %}{{ profile.latitude }}, {{ profile.longitude }}{% else %}-{% endif %}</span></small>
                    </div>
                    <div style="text-align: center; margin: 10px 0;">
                        <button type="button" class="location-btn" onclick="getCurrentLocation()">📍 Определить мое местоположение</button>
                        <button type="button" class="location-btn" onclick="clearLocation()">🗑️ Очистить</button>
                    </div>
                </div>

                <input type="hidden" name="latitude" id="latitude-input" value="{{ profile.latitude or '' }}">
                <input type="hidden" name="longitude" id="longitude-input" value="{{ profile.longitude or '' }}">

                <input type="text" name="venue" placeholder="Название заведения" value="{{ profile.venue or '' }}" required onchange="updateVenueCoordinates()">
                <input type="file" name="photo" accept="image/*">
                <button type="submit" class="modern-btn">Сохранить</button>
            </form>
            <a href="/my_profile" class="back-btn">← Назад</a>
        </body>
        </html>
    ''', profile=profile, navbar=navbar, get_photo_url=get_photo_url, get_starry_night_css=get_starry_night_css)


@app.route('/my_likes')
@require_profile
def my_likes():
    user_id = request.cookies.get('user_id')
    # Найти всех, кто меня лайкнул
    liked_me_profiles = []
    liked_me_ids = set()
    for like in Like.query.filter_by(liked_id=user_id).all():
        liker_profile = Profile.query.get(like.user_id)
        if liker_profile:
            liked_me_profiles.append(liker_profile)
            liked_me_ids.add(liker_profile.id)
    # Сбросить счетчик лайков - добавляем все текущие лайки в просмотренные
    read_likes[user_id].update(liked_me_ids)
    navbar = render_navbar(user_id, active='likes', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Меня лайкнули</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 600px; margin: 0 auto; padding: 20px; }
                h1 { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                }
                p { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    font-size: 1.1em;
                }
                .like-card { 
                    background: #030202; 
                    border-radius: 15px; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
                    padding: 20px; 
                    margin-bottom: 20px; 
                    display: flex; 
                    align-items: center; 
                    position: relative; 
                    cursor: pointer; 
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #fff;
                }
                .like-card:hover { 
                    transform: translateY(-3px) scale(1.02);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
                }
                .like-card img { max-width: 80px; border-radius: 10px; margin-right: 15px; object-fit: cover; height: 80px; }
                .like-info { flex: 1; }
                .like-card h2 { margin: 0 0 5px 0; color: #fff; }
                .like-card p { margin: 5px 0; color: #fff; }
                .like-btn { background: none; border: none; cursor: pointer; outline: none; font-size: 2em; position: absolute; top: 10px; right: 18px; z-index: 2; padding: 0; transition: transform 0.1s; }
                .like-btn:active { transform: scale(1.2); }
                .like-heart { color: #bbb; transition: color 0.2s; text-shadow: 0 2px 8px rgba(255,107,107,0.12); }
                .like-heart.liked { color: #ff6b6b; }
                .back-btn { background: linear-gradient(90deg, #6c757d 0%, #495057 100%); color: white; border: none; padding: 12px 24px; border-radius: 25px; box-shadow: 0 4px 14px rgba(108,117,125,0.2); font-size: 1.1em; cursor: pointer; transition: box-shadow 0.2s, transform 0.2s; text-decoration: none; display: inline-block; margin-top: 20px; }
                .back-btn:hover { box-shadow: 0 8px 24px rgba(108,117,125,0.3); transform: translateY(-2px) scale(1.03); }
                
                /* Стили для уведомлений */
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 15px 20px;
                    border-radius: 10px;
                    color: white;
                    font-weight: bold;
                    z-index: 1000;
                    transform: translateX(400px);
                    transition: transform 0.3s ease;
                    max-width: 300px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                }
                
                .notification.show {
                    transform: translateX(0);
                }
                
                .notification.success {
                    background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%);
                }
                
                .notification.error {
                    background: linear-gradient(90deg, #f44336 0%, #e57373 100%);
                }
                
                .notification.info {
                    background: linear-gradient(90deg, #2196F3 0%, #64B5F6 100%);
                }
                
                .notification.warning {
                    background: linear-gradient(90deg, #ff9800 0%, #ffb74d 100%);
                }
            </style>
            <script>
                function showNotification(message, type = 'info') {
                    // Удаляем существующие уведомления
                    const existingNotifications = document.querySelectorAll('.notification');
                    existingNotifications.forEach(notification => notification.remove());
                    
                    // Создаем новое уведомление
                    const notification = document.createElement('div');
                    notification.className = `notification ${type}`;
                    notification.textContent = message;
                    
                    // Добавляем в body
                    document.body.appendChild(notification);
                    
                    // Показываем уведомление
                    setTimeout(() => {
                        notification.classList.add('show');
                    }, 100);
                    
                    // Скрываем через 3 секунды
                    setTimeout(() => {
                        notification.classList.remove('show');
                        setTimeout(() => {
                            if (notification.parentNode) {
                                notification.parentNode.removeChild(notification);
                            }
                        }, 300);
                    }, 3000);
                }
                
                function toggleLike(profileId, btn) {
                    event.stopPropagation();
                    fetch('/toggle_like/' + profileId, {method: 'POST'})
                        .then(r => r.json())
                        .then(data => {
                            if (data.liked) {
                                btn.classList.add('liked');
                                showNotification('❤️ Лайк отправлен!', 'success');
                            } else if (data.already_liked) {
                                btn.classList.add('liked');
                                showNotification('💔 Вы уже лайкали эту анкету!', 'warning');
                            } else {
                                btn.classList.remove('liked');
                            }
                        });
                }
                function goToProfile(profileId) {
                    window.location.href = '/profile/' + profileId;
                }
            </script>
        </head>
        <body>
            {{ navbar|safe }}
            <h1>Меня лайкнули</h1>
            {% if liked_me_profiles %}
                {% for profile in liked_me_profiles %}
                    <div class="like-card" onclick="goToProfile('{{ profile.id }}')">
                        <img src="{{ get_photo_url(profile) }}" alt="Фото">
                        <div class="like-info">
                        <h2>{{ profile.name }}, {{ profile.age }}</h2>
                            <p>{{ profile.hobbies[:50] }}{% if profile.hobbies|length > 50 %}...{% endif %}</p>
                            {% if profile.city %}
                            <p style="color: #fff; font-size: 0.9em;">📍 {{ profile.city }}</p>
                            {% endif %}
                            {% if profile.venue %}
                            <p style="color: #fff; font-size: 0.9em;">🏪 {{ profile.venue }}</p>
                            {% endif %}
                        </div>
                        <button class="like-btn" title="Лайк" onclick="toggleLike('{{ profile.id }}', this.querySelector('span'))">
                            <span class="like-heart{% if profile.id in liked_ids %} liked{% endif %}">&#10084;</span>
                        </button>
                    </div>
                {% endfor %}
            {% else %}
                <p>Пока никто не лайкнул вашу анкету.</p>
            {% endif %}
        </body>
        </html>
    ''', liked_me_profiles=liked_me_profiles, navbar=navbar, get_photo_url=get_photo_url,
                                  liked_ids=set(l.liked_id for l in Like.query.filter_by(user_id=user_id).all()),
                                  get_starry_night_css=get_starry_night_css)


@app.route('/profile/<string:id>')
@require_profile
def view_profile(id):
    profile = Profile.query.get(id)
    if not profile:
        return "Анкета не найдена", 404
    user_id = request.cookies.get('user_id')
    is_owner = profile.id == user_id
    navbar = render_navbar(user_id, active=None, unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Анкета</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { text-align: center; padding: 20px; }
                .card { 
                    background: #030202; 
                    border-radius: 15px; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
                    max-width: 400px; 
                    margin: 0 auto; 
                    padding: 25px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #fff;
                }
                img { max-width: 100%; border-radius: 10px; }
                .modern-btn {
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin: 5px;
                    font-weight: bold;
                }
                .modern-btn:hover {
                    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
                    transform: translateY(-3px) scale(1.05);
                }
                .back-btn {
                    background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(108,117,125,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                }
                .back-btn:hover {
                    box-shadow: 0 8px 24px rgba(108,117,125,0.3);
                    transform: translateY(-2px) scale(1.03);
                }
                
                /* Стили для уведомлений */
                .notification {
                    position: fixed;
                    top: 20px;
                    right: 20px;
                    padding: 15px 20px;
                    border-radius: 10px;
                    color: white;
                    font-weight: bold;
                    z-index: 1000;
                    transform: translateX(400px);
                    transition: transform 0.3s ease;
                    max-width: 300px;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                }
                
                .notification.show {
                    transform: translateX(0);
                }
                
                .notification.success {
                    background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%);
                }
                
                .notification.error {
                    background: linear-gradient(90deg, #f44336 0%, #e57373 100%);
                }
                
                .notification.info {
                    background: linear-gradient(90deg, #2196F3 0%, #64B5F6 100%);
                }
                
                .notification.warning {
                    background: linear-gradient(90deg, #ff9800 0%, #ffb74d 100%);
                }
            </style>
            <script>
                function showNotification(message, type = 'info') {
                    // Удаляем существующие уведомления
                    const existingNotifications = document.querySelectorAll('.notification');
                    existingNotifications.forEach(notification => notification.remove());
                    
                    // Создаем новое уведомление
                    const notification = document.createElement('div');
                    notification.className = `notification ${type}`;
                    notification.textContent = message;
                    
                    // Добавляем в body
                    document.body.appendChild(notification);
                    
                    // Показываем уведомление
                    setTimeout(() => {
                        notification.classList.add('show');
                    }, 100);
                    
                    // Скрываем через 3 секунды
                    setTimeout(() => {
                        notification.classList.remove('show');
                        setTimeout(() => {
                            if (notification.parentNode) {
                                notification.parentNode.removeChild(notification);
                            }
                        }, 300);
                    }, 3000);
                }
                
                function likeProfile(profileId) {
                    // Показываем индикатор загрузки
                    const button = event.target;
                    const originalText = button.textContent;
                    button.textContent = '⏳ Отправляем...';
                    button.disabled = true;
                    
                    fetch('/like/' + profileId, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => {
                        if (response.ok) {
                            // Успешный лайк
                            showNotification('❤️ Лайк отправлен!', 'success');
                            // Перенаправляем на страницу профиля
                            setTimeout(() => {
                                window.location.href = '/profile/' + profileId;
                            }, 1000);
                        } else {
                            // Ошибка - пытаемся получить JSON
                            return response.json().catch(() => response.text());
                        }
                    })
                    .then(data => {
                        if (data && typeof data === 'object') {
                            // JSON ответ
                            if (data.error) {
                                if (data.error.includes('уже лайкнули')) {
                                    showNotification('💔 Вы уже лайкнули этого пользователя', 'warning');
                                } else if (data.error.includes('свою анкету')) {
                                    showNotification('🤔 Нельзя лайкнуть свою анкету', 'error');
                                } else {
                                    showNotification('❌ ' + data.error, 'error');
                                }
                            }
                        } else if (data) {
                            // Текстовый ответ (для обратной совместимости)
                            if (data.includes('уже лайкнули')) {
                                showNotification('💔 Вы уже лайкнули этого пользователя', 'warning');
                            } else if (data.includes('свою анкету')) {
                                showNotification('🤔 Нельзя лайкнуть свою анкету', 'error');
                            } else {
                                showNotification('❌ Ошибка: ' + data, 'error');
                            }
                        }
                    })
                    .catch(error => {
                        showNotification('❌ Ошибка сети', 'error');
                    })
                    .finally(() => {
                        // Восстанавливаем кнопку
                        button.textContent = originalText;
                        button.disabled = false;
                    });
                }
            </script>
        </head>
        <body>
            {{ navbar|safe }}
            <div class="card">
                <img src="{{ get_photo_url(profile) }}" alt="Фото">
                <h2>{{ profile.name }}, {{ profile.age }}</h2>
                <p><strong>Увлечения:</strong> {{ profile.hobbies }}</p>
                <p><strong>Цель:</strong> {{ profile.goal }}</p>
                {% if profile.city %}
                <p><strong>📍 Местоположение:</strong> {{ profile.city }}</p>
                {% endif %}
                {% if profile.venue %}
                <p><strong>🏪 Заведение:</strong> {{ profile.venue }}</p>
                {% endif %}
                {% if not is_owner %}
                    <button type="button" class="modern-btn" onclick="likeProfile('{{ profile.id }}')">❤️ Лайк</button>
                {% endif %}
                {% if is_owner %}
                    <form action="/delete/{{ profile.id }}" method="post">
                        <button type="submit" class="modern-btn" style="background: #b00020;">Удалить анкету</button>
                    </form>
                {% endif %}
                <a href="/visitors" class="back-btn">← Назад к посетителям</a>
            </div>
        </body>
        </html>
    ''', profile=profile, is_owner=is_owner, navbar=navbar, get_photo_url=get_photo_url,
                                  get_starry_night_css=get_starry_night_css)


@app.route('/like/<string:id>', methods=['POST'])
@require_profile
def like_profile(id):
    if Profile.query.get(id) is None:
        return jsonify({'error': 'Анкета не найдена'}), 404
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({'error': 'Не авторизован'}), 401
    if Profile.query.get(id).id == user_id:
        return jsonify({'error': 'Нельзя лайкнуть свою анкету'}), 400
    if Like.query.filter_by(user_id=user_id, liked_id=id).first():
        return jsonify({'error': 'Вы уже лайкнули этого пользователя'}), 400
    
    try:
        db.session.add(Like(user_id=user_id, liked_id=id))
        db.session.commit()
        check_for_matches(user_id)
        return jsonify({'success': True, 'message': 'Лайк отправлен'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Ошибка при отправке лайка'}), 500


@app.route('/delete/<string:id>', methods=['POST'])
@require_profile
def delete_profile(id):
    profile = Profile.query.get(id)
    if not profile:
        return "Анкета не найдена", 404
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('home'))
    if profile.id != user_id:
        return "Нельзя удалить чужую анкету", 403
    try:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], profile.photo))
    except:
        pass
    db.session.delete(profile)
    db.session.commit()
    return redirect(url_for('home'))


@app.route('/my_matches')
@require_profile
def my_matches():
    user_id = request.cookies.get('user_id')
    liked_ids = set(l.liked_id for l in Like.query.filter_by(user_id=user_id).all())
    liked_me_ids = set(l.user_id for l in Like.query.filter_by(liked_id=user_id).all())
    matches_ids = liked_ids & liked_me_ids
    matched_profiles = [Profile.query.get(mid) for mid in matches_ids if Profile.query.get(mid)]
    # Сбросить счетчик новых мэтчей
    new_matches[user_id].clear()
    navbar = render_navbar(user_id, active='matches', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id), unread_matches=0)
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Мои мэтчи</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 600px; margin: 0 auto; padding: 20px; }
                h1 { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                }
                p { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    font-size: 1.1em;
                }
                .match-card { 
                    background: #030202; 
                    border-radius: 15px; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
                    padding: 20px; 
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    gap: 20px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    transition: all 0.3s ease;
                    color: #fff;
                }
                .match-card:hover {
                    transform: translateY(-3px) scale(1.02);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
                }
                .match-photo {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 3px solid #4CAF50;
                }
                .match-info {
                    flex: 1;
                }
                .modern-btn {
                    background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(76,175,80,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    margin-top: 10px;
                    text-decoration: none;
                    display: inline-block;
                }
                .modern-btn:hover {
                    box-shadow: 0 8px 24px rgba(76,175,80,0.3);
                    transform: translateY(-2px) scale(1.03);
                }
            </style>
        </head>
        <body>
            {{ navbar|safe }}
            <h1>Мои мэтчи</h1>
            {% if matched_profiles %}
                {% for profile in matched_profiles %}
                    <div class="match-card">
                        <img src="{{ get_photo_url(profile) }}" alt="Фото" class="match-photo">
                        <div class="match-info">
                            <h2 style="margin: 0 0 10px 0;">{{ profile.name }}, {{ profile.age }}</h2>
                            {% if profile.city %}
                            <p style="color: #fff; margin: 5px 0;">📍 {{ profile.city }}</p>
                            {% endif %}
                            {% if profile.venue %}
                            <p style="color: #fff; margin: 5px 0;">🏪 {{ profile.venue }}</p>
                            {% endif %}
                        </div>
                        <a href="/chat/{{ profile.id }}" class="modern-btn">Чат</a>
                    </div>
                {% endfor %}
            {% else %}
                <p>У вас пока нет мэтчей.</p>
            {% endif %}
        </body>
        </html>
    ''', matched_profiles=matched_profiles, navbar=navbar, get_photo_url=get_photo_url,
                                  get_starry_night_css=get_starry_night_css)


@app.route('/my_messages')
@require_profile
def my_messages():
    user_id = request.cookies.get('user_id')
    chat_keys = set()
    for msg in Message.query.all():
        ids = msg.chat_key.split('_')
        if user_id in ids:
            chat_keys.add(msg.chat_key)
    chat_partners = set()
    for chat_key in chat_keys:
        ids = chat_key.split('_')
        for uid in ids:
            if uid != user_id:
                chat_partners.add(uid)
    chat_profiles = [p for p in Profile.query.all() if p.id in chat_partners]
    # Считаем непрочитанные сообщения по каждому собеседнику
    unread_by_partner = {}
    for partner_id in chat_partners:
        chat_key = '_'.join(sorted([user_id, partner_id]))
        unread_by_partner[partner_id] = Message.query.filter_by(chat_key=chat_key).filter(
            Message.sender == partner_id).filter((Message.read_by.is_(None)) | (Message.read_by != user_id)).count()
    unread_messages = get_unread_messages_count(user_id)
    navbar = render_navbar(user_id, active='messages', unread_messages=unread_messages,
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Мои сообщения</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 600px; margin: 0 auto; padding: 20px; }
                h1 { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                }
                p { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    font-size: 1.1em;
                }
                .chat-card { 
                    background: #030202; 
                    border-radius: 15px; 
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3); 
                    padding: 20px; 
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #fff;
                }
                .chat-card:hover {
                    transform: translateY(-3px) scale(1.02);
                    box-shadow: 0 12px 40px rgba(0, 0, 0, 0.4);
                }
                .chat-card img {
                    width:60px;
                    height:60px;
                    border-radius:50%;
                    margin-right:15px;
                    object-fit:cover;
                    border: 2px solid #667eea;
                }
                .chat-info { flex: 1; }
                .chat-card h2 { margin: 0 0 5px 0; color: #fff; }
                .chat-card p { margin: 5px 0; color: #fff; }
                .unread-badge {
                    background: #ff6b6b;
                    color: white;
                    border-radius: 50%;
                    width: 20px;
                    height: 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 0.8em;
                    font-weight: bold;
                }
                .back-btn {
                    background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(108,117,125,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                }
                .back-btn:hover {
                    box-shadow: 0 8px 24px rgba(108,117,125,0.3);
                    transform: translateY(-2px) scale(1.03);
                }
            </style>
            <script>
                function goToChat(profileId) {
                    window.location.href = '/chat/' + profileId;
                }
            </script>
        </head>
        <body>
            {{ navbar|safe }}
            <h1>Мои сообщения</h1>
            {% if chat_profiles %}
                {% for profile in chat_profiles %}
                    <div class="chat-card" onclick="goToChat('{{ profile.id }}')">
                        <img src="{{ get_photo_url(profile) }}" alt="Фото">
                        <div class="chat-info">
                            <h2>{{ profile.name }}, {{ profile.age }}</h2>
                            {% if profile.venue %}
                            <p style="color: #666; font-size: 0.9em;">🏪 {{ profile.venue }}</p>
                            {% endif %}
                        </div>
                        {% if unread_by_partner[profile.id] > 0 %}
                            <div class="unread-badge">{{ unread_by_partner[profile.id] }}</div>
                        {% endif %}
                    </div>
                {% endfor %}
            {% else %}
                <p>У вас пока нет сообщений.</p>
            {% endif %}
        </body>
        </html>
    ''', chat_profiles=chat_profiles, navbar=navbar, get_photo_url=get_photo_url, unread_by_partner=unread_by_partner,
                                  get_starry_night_css=get_starry_night_css)


@app.route('/chat/<string:other_user_id>', methods=['GET', 'POST'])
@require_profile
def chat(other_user_id):
    user_id = request.cookies.get('user_id')
    liked_ids = set(l.liked_id for l in Like.query.filter_by(user_id=user_id).all())
    liked_me_ids = set(l.user_id for l in Like.query.filter_by(liked_id=user_id).all())
    matches_ids = liked_ids & liked_me_ids
    if other_user_id not in matches_ids:
        return "Чат доступен только для мэтчей", 403
    other_profile = Profile.query.get(other_user_id)
    if not other_profile:
        return "Пользователь не найден", 404
    chat_key = '_'.join(sorted([user_id, other_user_id]))
    # Помечаем все сообщения от собеседника как прочитанные
    for msg in Message.query.filter_by(chat_key=chat_key).filter(Message.sender == other_user_id).all():
        if msg.read_by != user_id:
            msg.read_by = user_id
    db.session.commit()
    navbar = render_navbar(user_id, active='messages', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    if request.method == 'POST':
        message = request.form.get('message')
        if message:
            db.session.add(Message(chat_key=chat_key, sender=user_id, text=message))
            db.session.commit()
    messages_db = Message.query.filter_by(chat_key=chat_key).order_by(Message.timestamp).all()
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Чат</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 600px; margin: 0 auto; padding: 20px; }
                .chat-header {
                    background: rgba(255, 255, 255, 0.95);
                    border-radius: 15px;
                    padding: 20px;
                    margin-bottom: 20px;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .chat-photo {
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    object-fit: cover;
                    border: 3px solid #667eea;
                }
                .chat-info h1 {
                    margin: 0;
                    font-size: 1.4em;
                    color: #333;
                }
                .chat-info p {
                    margin: 5px 0 0 0;
                    color: #666;
                    font-size: 0.9em;
                }
                .message { 
                    margin: 10px; 
                    padding: 15px; 
                    border-radius: 15px; 
                    max-width: 70%; 
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .my-message { 
                    background: rgba(220, 248, 198, 0.9); 
                    margin-left: auto; 
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                }
                .their-message { 
                    background: rgba(255, 255, 255, 0.9); 
                    margin-right: auto; 
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                }
                .modern-btn {
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin-top: 10px;
                    font-weight: bold;
                    align-self: center;
                }
                .modern-btn:hover {
                    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
                    transform: translateY(-3px) scale(1.05);
                }
                #messages { min-height: 200px; }
                #chat-form { 
                    display: flex; 
                    flex-direction: column; 
                    align-items: center; 
                    margin-top: 20px; 
                    width: 100%;
                }
                #message-input {
                    width: 100%;
                    max-width: 500px;
                    padding: 15px;
                    font-size: 1.1em;
                    border-radius: 15px;
                    border: 1px solid rgba(255, 255, 255, 0.3);
                    background: rgba(255, 255, 255, 0.9);
                    min-height: 48px;
                    margin-bottom: 10px;
                    resize: none;
                    backdrop-filter: blur(10px);
                    box-sizing: border-box;
                }
                #message-input:focus {
                    outline: none;
                    border-color: #667eea;
                    box-shadow: 0 0 15px rgba(102, 126, 234, 0.3);
                }


                .typing-indicator {
                    background: rgba(255, 255, 255, 0.9);
                    border-radius: 15px;
                    padding: 10px 15px;
                    margin: 10px;
                    font-size: 0.9em;
                    color: #666;
                    display: none;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    align-self: flex-start;
                }

                .typing-indicator.show {
                    display: block;
                }

                .typing-dots {
                    display: inline-block;
                    animation: typing 1.4s infinite;
                }

                @keyframes typing {
                    0%, 20% { opacity: 0; }
                    50% { opacity: 1; }
                    100% { opacity: 0; }
                }
            </style>
            <script src="https://cdn.socket.io/4.7.5/socket.io.min.js"></script>
        </head>
        <body>
            {{ navbar|safe }}
            <div class="chat-header">
                <img src="{{ get_photo_url(other_profile) }}" alt="Фото" class="chat-photo">
                <div class="chat-info">
                    <h1>Чат с {{ other_profile.name }}</h1>
                    {% if other_profile.venue %}
                    <p>🏪 {{ other_profile.venue }}</p>
                    {% endif %}
                </div>
            </div>
            <div id="messages">
                {% for m in messages_db %}
                    <div class="message {{ 'my-message' if m.sender == user_id else 'their-message' }}">
                        {{ m.text }}
                        <div style="font-size: 0.8em; color: #666; margin-top: 5px; text-align: right;">
                            {{ m.timestamp.strftime('%H:%M') }}
                        </div>
                    </div>
                {% endfor %}
            </div>
            <div class="typing-indicator" id="typing-indicator">
                <span>{{ other_profile.name }} печатает</span><span class="typing-dots">...</span>
            </div>
            <form id="chat-form" autocomplete="off">
                <textarea id="message-input" name="message" placeholder="Ваше сообщение..." maxlength="400" required></textarea>
                <button type="submit" class="modern-btn">Отправить</button>
            </form>
            <script>
                const user_id = "{{ user_id }}";
                const chat_key = "{{ chat_key }}";
                const other_user_id = "{{ other_profile.id }}";
                let lastMessageCount = {{ messages_db|length }};
                let lastMessageTimestamp = "{{ messages_db[-1].timestamp.isoformat() if messages_db else '' }}";

                // Инициализация Socket.IO
                const socket = io();
                socket.emit('join', {room: chat_key});

                // Функция добавления сообщения
                function addMessage(msg, sender, timestamp = null) {
                    // Проверяем, нет ли уже такого сообщения на странице
                    const messages = document.querySelectorAll('.message');
                    const lastMessage = messages[messages.length - 1];

                    if (lastMessage && lastMessage.textContent.trim() === msg.trim()) {
                        // Сообщение уже есть, не добавляем дубликат
                        return;
                    }

                    const div = document.createElement('div');
                    div.className = 'message ' + (sender === user_id ? 'my-message' : 'their-message');
                    div.textContent = msg;

                    // Добавляем время, если оно есть
                    if (timestamp) {
                        const timeDiv = document.createElement('div');
                        timeDiv.style.cssText = 'font-size: 0.8em; color: #666; margin-top: 5px; text-align: right;';
                        timeDiv.textContent = new Date(timestamp).toLocaleTimeString('ru-RU', {hour: '2-digit', minute: '2-digit'});
                        div.appendChild(timeDiv);
                    }

                    document.getElementById('messages').appendChild(div);
                    window.scrollTo(0, document.body.scrollHeight);
                }

                // Функция отметки сообщений как прочитанные
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

                // Функция обновления счетчиков в навбаре
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

                // Функция проверки новых сообщений через AJAX
                function checkNewMessages() {
                    fetch(`/chat_history/${other_user_id}`)
                        .then(response => response.json())
                        .then(messages => {
                            if (messages.length > lastMessageCount) {
                                // Есть новые сообщения
                                const newMessages = messages.slice(lastMessageCount);
                                let hasNewMessagesFromOther = false;

                                newMessages.forEach(msg => {
                                    // Добавляем только сообщения от собеседника, не от себя
                                    if (msg.sender !== user_id) {
                                        addMessage(msg.text, msg.sender, msg.timestamp);
                                        hasNewMessagesFromOther = true;
                                    }
                                });

                                lastMessageCount = messages.length;
                                if (newMessages.length > 0) {
                                    lastMessageTimestamp = newMessages[newMessages.length - 1].timestamp;
                                }

                                // Если есть новые сообщения от собеседника, отмечаем их как прочитанные
                                if (hasNewMessagesFromOther) {
                                    markMessagesAsRead(other_user_id);
                                }
                            }
                        })
                        .catch(error => {
                            console.error('Ошибка при получении новых сообщений:', error);
                        });
                }

                // Socket.IO обработчики
                socket.on('message', function(data) {
                    addMessage(data.text, data.sender);
                    // Обновляем счетчик только для сообщений от собеседника
                    if (data.sender !== user_id) {
                        lastMessageCount++;
                        // Автоматически отмечаем сообщение как прочитанное
                        markMessagesAsRead(other_user_id);
                    }
                });

                socket.on('connect', function() {
                    console.log('✅ Socket.IO подключен');
                });

                socket.on('disconnect', function() {
                    console.log('❌ Socket.IO отключен, переключаемся на AJAX');
                });
                
                socket.on('connect_error', function(error) {
                    console.error('❌ Ошибка подключения Socket.IO:', error);
                });
                
                socket.on('error', function(error) {
                    console.error('❌ Ошибка Socket.IO:', error);
                });

                // Обработчик отправки сообщения
                document.getElementById('chat-form').onsubmit = function(e) {
                    e.preventDefault();
                    const input = document.getElementById('message-input');
                    const msg = input.value;
                    if (msg.trim()) {
                        console.log('📤 Отправка сообщения через Socket.IO...');
                        
                        // Отправляем через Socket.IO
                        socket.emit('send_message', {room: chat_key, text: msg, sender: user_id});
                        
                        // Добавляем сообщение локально для мгновенного отображения
                        addMessage(msg, user_id);
                        
                        // Очищаем поле ввода
                        input.value = '';
                        
                        console.log('✅ Сообщение отправлено');
                    }
                };

                // Индикатор печати
                let typingTimer;
                const typingIndicator = document.getElementById('typing-indicator');

                document.getElementById('message-input').addEventListener('input', function() {
                    if (this.value.trim()) {
                        socket.emit('typing', {room: chat_key, user: user_id, isTyping: true});

                        clearTimeout(typingTimer);
                        typingTimer = setTimeout(() => {
                            socket.emit('typing', {room: chat_key, user: user_id, isTyping: false});
                        }, 1000);
                    }
                });

                socket.on('user_typing', function(data) {
                    if (data.user !== user_id) {
                        if (data.isTyping) {
                            typingIndicator.classList.add('show');
                        } else {
                            typingIndicator.classList.remove('show');
                        }
                    }
                });

                // Запускаем периодическую проверку новых сообщений каждые 3 секунды
                setInterval(checkNewMessages, 3000);

                // Проверяем новые сообщения при фокусе на поле ввода
                document.getElementById('message-input').addEventListener('focus', function() {
                    checkNewMessages();
                });

                // Проверяем новые сообщения при прокрутке страницы
                window.addEventListener('scroll', function() {
                    if (window.scrollY + window.innerHeight >= document.body.scrollHeight - 100) {
                        checkNewMessages();
                    }
                });

                // Автоматическая прокрутка к последнему сообщению при загрузке
                window.addEventListener('load', function() {
                    window.scrollTo(0, document.body.scrollHeight);
                    // Отмечаем все сообщения от собеседника как прочитанные при загрузке чата
                    markMessagesAsRead(other_user_id);
                });
            </script>
        </body>
        </html>
    ''', other_profile=other_profile, user_id=user_id, chat_key=chat_key, navbar=navbar, get_photo_url=get_photo_url,
                                  messages_db=messages_db, get_starry_night_css=get_starry_night_css)


@app.route('/chat_history/<string:other_user_id>')
@require_profile
def chat_history(other_user_id):
    user_id = request.cookies.get('user_id')
    chat_key = '_'.join(sorted([user_id, other_user_id]))
    msgs = Message.query.filter_by(chat_key=chat_key).order_by(Message.timestamp).all()
    return jsonify([
        {'sender': m.sender, 'text': m.text, 'timestamp': m.timestamp.isoformat()} for m in msgs
    ])


@socketio.on('join')
def on_join(data):
    try:
        room = data.get('room')
        if room:
            join_room(room)
            print(f"✅ Пользователь присоединился к комнате: {room}")
        else:
            print(f"❌ Некорректные данные для присоединения: {data}")
    except Exception as e:
        print(f"❌ Ошибка при присоединении к комнате: {e}")


@socketio.on('send_message')
def handle_send_message(data):
    try:
        room = data['room']
        text = data['text']
        sender = data['sender']
        
        # Проверяем, что данные корректны
        if not room or not text or not sender:
            print(f"❌ Некорректные данные сообщения: {data}")
            return
            
        # Сохраняем сообщение в базу данных
        new_message = Message(chat_key=room, sender=sender, text=text)
        db.session.add(new_message)
        db.session.commit()
        
        print(f"✅ Сообщение сохранено: {sender} -> {room}: {text[:50]}...")
        
        # Отправляем сообщение всем в комнате
        emit('message', {'text': text, 'sender': sender}, room=room)
        print(f"📤 Сообщение отправлено в комнату {room}")
        
    except Exception as e:
        print(f"❌ Ошибка при обработке сообщения: {e}")
        db.session.rollback()


@socketio.on('typing')
def handle_typing(data):
    try:
        room = data.get('room')
        user = data.get('user')
        is_typing = data.get('isTyping')
        
        if room and user is not None:
            emit('user_typing', {'user': user, 'isTyping': is_typing}, room=room, include_self=False)
            print(f"⌨️ Индикатор печати: {user} {'печатает' if is_typing else 'остановился'} в комнате {room}")
        else:
            print(f"❌ Некорректные данные для индикатора печати: {data}")
    except Exception as e:
        print(f"❌ Ошибка при обработке индикатора печати: {e}")


def check_for_matches(user_id):
    liked_ids = set(l.liked_id for l in Like.query.filter_by(user_id=user_id).all())
    liked_me_ids = set(l.user_id for l in Like.query.filter_by(liked_id=user_id).all())
    matches_ids = liked_ids & liked_me_ids
    for matched_user_id in matches_ids:
        if matched_user_id not in new_matches[user_id]:
            user_profile = Profile.query.get(user_id)
            matched_profile = Profile.query.get(matched_user_id)
            if user_profile and matched_profile:
                add_notification(user_id, f"✨ У вас мэтч с {matched_profile.name}! Теперь вы можете общаться.")
                add_notification(matched_user_id, f"✨ У вас мэтч с {user_profile.name}! Теперь вы можете общаться.")
                new_matches[user_id].add(matched_user_id)
                new_matches[matched_user_id].add(user_id)


# Плейсхолдер для фото
PLACEHOLDER_PHOTO = '/static/uploads/placeholder.png'


def get_photo_url(profile):
    if hasattr(profile, 'photo') and profile.photo and os.path.exists(
            os.path.join(app.config['UPLOAD_FOLDER'], profile.photo)):
        return url_for('static', filename='uploads/' + profile.photo)
    return PLACEHOLDER_PHOTO


@app.route('/test-geolocation')
def test_geolocation():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Тест геолокации</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <style>
                body { font-family: Arial, sans-serif; padding: 20px; text-align: center; }
                .success { color: green; font-weight: bold; }
                .error { color: red; font-weight: bold; }
                button { padding: 10px 20px; margin: 10px; font-size: 16px; }
            </style>
        </head>
        <body>
            <h1>🔗 Тест геолокации</h1>
            <p>Эта страница поможет проверить работу геолокации</p>

            <button onclick="testGeolocation()">📍 Тест геолокации</button>
            <div id="result"></div>

            <script>
                function testGeolocation() {
                    const resultDiv = document.getElementById('result');
                    resultDiv.innerHTML = '<p>Проверяем геолокацию...</p>';

                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                resultDiv.innerHTML = `
                                    <p class="success">✅ Геолокация работает!</p>
                                    <p>Координаты: ${position.coords.latitude}, ${position.coords.longitude}</p>
                                    <p>Точность: ±${position.coords.accuracy} метров</p>
                                `;
                            },
                            function(error) {
                                let errorMessage = '';
                                switch(error.code) {
                                    case error.PERMISSION_DENIED:
                                        errorMessage = '❌ Доступ к местоположению запрещен';
                                        break;
                                    case error.POSITION_UNAVAILABLE:
                                        errorMessage = '❌ Информация о местоположении недоступна';
                                        break;
                                    case error.TIMEOUT:
                                        errorMessage = '❌ Превышено время ожидания';
                                        break;
                                    default:
                                        errorMessage = '❌ Ошибка: ' + error.message;
                                }
                                resultDiv.innerHTML = `<p class="error">${errorMessage}</p>`;
                            },
                            {
                                enableHighAccuracy: false,
                                timeout: 10000,
                                maximumAge: 60000
                            }
                        );
                    } else {
                        resultDiv.innerHTML = '<p class="error">❌ Геолокация не поддерживается</p>';
                    }
                }
            </script>
        </body>
        </html>
    ''')


@app.route('/api/check-profile/<string:user_id>', methods=['GET'])
def api_check_profile(user_id):
    """
    API endpoint для проверки существования профиля по user_id
    """
    try:
        profile = Profile.query.get(user_id)
        exists = profile is not None

        return jsonify({
            'success': True,
            'exists': exists,
            'user_id': user_id,
            'profile_data': {
                'name': profile.name if profile else None,
                'age': profile.age if profile else None,
                'gender': profile.gender if profile else None,
                'city': profile.city if profile else None,
                'created_at': profile.created_at.isoformat() if profile and profile.created_at else None
            } if profile else None
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/restore-session', methods=['POST'])
def api_restore_session():
    """
    API endpoint для восстановления сессии пользователя
    """
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({
                'success': False,
                'error': 'User ID не предоставлен'
            }), 400

        profile = Profile.query.get(user_id)
        if not profile:
            return jsonify({
                'success': False,
                'error': 'Профиль не найден'
            }), 404

        # Устанавливаем cookie для восстановления сессии
        response = jsonify({
            'success': True,
            'user_id': user_id,
            'profile_exists': True,
            'redirect_url': url_for('view_profile', id=user_id)
        })
        response.set_cookie('user_id', user_id, max_age=365 * 24 * 60 * 60)  # 1 год

        return response

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clear-user-cookie', methods=['POST'])
def api_clear_user_cookie():
    """
    API endpoint для очистки cookie пользователя
    """
    try:
        response = jsonify({
            'success': True,
            'message': 'Cookie очищен'
        })
        response.delete_cookie('user_id')
        return response
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/clear-cookie', methods=['GET'])
def api_clear_cookie():
    """API для очистки cookie"""
    response = make_response(jsonify({'success': True, 'message': 'Cookie очищен'}))
    response.delete_cookie('user_id')
    return response


@app.route('/api/delete-profile/<string:user_id>', methods=['POST'])
def api_delete_profile(user_id):
    """
    API endpoint для удаления профиля и очистки сессии
    """
    try:
        # Удаляем профиль из базы данных
        profile = Profile.query.get(user_id)
        if profile:
            # Удаляем связанные данные
            Like.query.filter_by(user_id=user_id).delete()
            Like.query.filter_by(liked_id=user_id).delete()

            # Удаляем сообщения
            messages_to_delete = []
            for msg in Message.query.all():
                if user_id in msg.chat_key.split('_'):
                    messages_to_delete.append(msg)

            for msg in messages_to_delete:
                db.session.delete(msg)

            # Удаляем фото
            if profile.photo:
                try:
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                except Exception as e:
                    print(f"Ошибка при удалении фото: {e}")

            # Удаляем профиль
            db.session.delete(profile)
            db.session.commit()

            response = jsonify({
                'success': True,
                'message': 'Профиль успешно удален'
            })
            response.delete_cookie('user_id')
            return response
        else:
            return jsonify({
                'success': False,
                'error': 'Профиль не найден'
            }), 404

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/profiles', methods=['GET'])
def api_get_profiles_count():
    """
    API endpoint для получения количества анкет в базе данных
    """
    try:
        count = Profile.query.count()
        return jsonify({
            'success': True,
            'count': count
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/cleanup-profiles', methods=['POST'])
def api_cleanup_profiles():
    """
    API endpoint для ручного запуска очистки просроченных анкет
    """
    try:
        deleted_count = cleanup_expired_profiles()
        return jsonify({
            'success': True,
            'deleted_count': deleted_count,
            'lifetime_hours': PROFILE_LIFETIME_HOURS
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/terms')
def terms():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Пользовательское соглашение</title>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 800px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%);
                    background-size: 400% 400%;
                    animation: starryNight 15s ease infinite;
                    position: relative;
                    min-height: 100vh;
                }

                @keyframes starryNight {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }

                .terms-container {
                    position: relative;
                    z-index: 2;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 40px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    color: #fff;
                }

                h1 {
                    color: #fff;
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 30px;
                    font-size: 2.2em;
                    text-align: center;
                }

                h2 {
                    color: #4CAF50;
                    margin: 30px 0 15px 0;
                    font-size: 1.5em;
                    border-bottom: 2px solid rgba(76, 175, 80, 0.3);
                    padding-bottom: 10px;
                }

                p {
                    line-height: 1.6;
                    margin-bottom: 15px;
                    font-size: 1.1em;
                }

                .highlight {
                    background: rgba(76, 175, 80, 0.1);
                    border-left: 4px solid #4CAF50;
                    padding: 15px;
                    margin: 20px 0;
                    border-radius: 5px;
                }

                .back-btn {
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: bold;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 30px;
                }

                .back-btn:hover {
                    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
                    transform: translateY(-3px) scale(1.05);
                }

                .section {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    border: 1px solid rgba(255, 255, 255, 0.1);
                }

                ul {
                    margin: 15px 0;
                    padding-left: 20px;
                }

                li {
                    margin: 8px 0;
                    line-height: 1.5;
                }

                .important {
                    background: rgba(244, 67, 54, 0.1);
                    border: 1px solid rgba(244, 67, 54, 0.3);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                }

                .important h3 {
                    color: #F44336;
                    margin-bottom: 10px;
                }
            </style>
        </head>
        <body>
            <div class="terms-container">
                <h1>📋 Пользовательское соглашение</h1>

                <div class="highlight">
                    <p><strong>Здесь правила приложения, ознакомься пожалуйста</strong></p>
                </div>

                <div class="section">
                    <h2>🎯 Концепция приложения</h2>
                    <p>Наше приложение предназначено для создания анкет и поиска знакомств в реальном мире. Мы поощряем личные встречи и общение в кафе, ресторанах и других общественных местах.</p>
                </div>

                <div class="section">
                    <h2>📍 Геолокация и местоположение</h2>
                    <ul>
                        <li>Приложение автоматически определяет ваше местоположение для поиска ближайших заведений</li>
                        <li>Ваше местоположение используется только для подбора заведений поблизости</li>
                        <li>Координаты не передаются другим пользователям</li>
                        <li>Вы можете выбрать заведение на карте для указания в анкете</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>🚫 Ограничения по расстоянию</h2>
                    <ul>
                        <li>Регистрация возможна только если вы находитесь в пределах 3 км от выбранного заведения</li>
                        <li>Это ограничение помогает избежать "диванных" пользователей</li>
                        <li>Максимальное расстояние может быть изменено администрацией</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>📸 Фотографии и контент</h2>
                    <ul>
                        <li>Загружайте только свои фотографии</li>
                        <li>Не используйте чужие изображения или контент</li>
                        <li>Фотографии должны быть приличными и соответствовать правилам приложения</li>
                        <li>Администрация оставляет за собой право удалить неприемлемый контент</li>
                    </ul>
                </div>

                <div class="section">
                    <h2>🤝 Правила поведения</h2>
                    <ul>
                        <li>Будьте вежливы и уважительны к другим пользователям</li>
                        <li>Не используйте приложение для спама или рекламы</li>
                        <li>Не создавайте фальшивые анкеты</li>
                        <li>Соблюдайте законы и нормы морали</li>
                    </ul>
                </div>

                <div class="important">
                    <h3>⚠️ Важно</h3>
                    <p>Создавая анкету, вы подтверждаете, что ознакомились с правилами приложения и соглашаетесь их соблюдать. Нарушение правил может привести к блокировке аккаунта.</p>
                </div>

                <div style="text-align: center;">
                    <a href="/create" class="back-btn">📝 Создать анкету</a>
                    <a href="/" class="back-btn">🏠 На главную</a>
                </div>
            </div>
        </body>
        </html>
    ''')


def cleanup_expired_profiles():
    """
    Удаляет анкеты, которые старше PROFILE_LIFETIME_HOURS часов
    """
    try:
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=PROFILE_LIFETIME_HOURS)

        # Находим просроченные анкеты
        expired_profiles = Profile.query.filter(Profile.created_at < cutoff_time).all()

        deleted_count = 0
        for profile in expired_profiles:
            # Удаляем связанные записи
            Like.query.filter_by(user_id=profile.id).delete()
            Like.query.filter_by(liked_id=profile.id).delete()

            # Удаляем сообщения
            Message.query.filter(
                (Message.chat_key.contains(profile.id))
            ).delete()

            # Удаляем фото файл
            if profile.photo:
                try:
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                        print(f"🗑️ Удален файл фото: {profile.photo}")
                except Exception as e:
                    print(f"❌ Ошибка удаления файла {profile.photo}: {e}")

            # Удаляем анкету
            db.session.delete(profile)
            deleted_count += 1

        if deleted_count > 0:
            db.session.commit()
            print(f"🧹 Удалено {deleted_count} просроченных анкет")
        else:
            print("✅ Просроченных анкет не найдено")

        return deleted_count

    except Exception as e:
        print(f"❌ Ошибка при очистке просроченных анкет: {e}")
        db.session.rollback()
        return 0


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Запускаем очистку просроченных анкет при старте сервера
        print("🧹 Запуск автоматической очистки просроченных анкет...")
        deleted_count = cleanup_expired_profiles()
        print(f"⏰ Время жизни анкеты: {PROFILE_LIFETIME_HOURS} часов")

    socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)