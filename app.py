# нужно вводить https://192.168.255.137
# Тестовое изменение для демонстрации коммита

from flask import Flask, render_template_string, request, redirect, url_for, make_response, jsonify, send_from_directory
from flask_socketio import SocketIO, emit, join_room
import os
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from functools import wraps
import requests
import threading
import time

app = Flask(__name__)
app.secret_key = 'super-secret-key'
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# Увеличиваем лимит размера файла до 16MB (по умолчанию 1MB)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
db = SQLAlchemy(app)

# Максимальное расстояние для регистрации (в метрах) - СТРОКА 29
MAX_REGISTRATION_DISTANCE = 10000000  # 10000 км = 1000000 метров

# Время жизни анкеты в часах - НАСТРАИВАЕМАЯ ПЕРЕМЕННАЯ
# ⚠️ ВАЖНО: После изменения этих значений ОБЯЗАТЕЛЬНО ПЕРЕЗАПУСТИТЕ СЕРВЕР!
PROFILE_LIFETIME_HOURS = 1  # Время жизни ОПЛАЧЕННОЙ анкеты в часах (10 часов)
PENDING_PROFILE_LIFETIME_HOURS = 0.25  # Время жизни ВРЕМЕННОЙ анкеты до оплаты в часах (10 часов)

# ============================================================================
# ЮKASSA КОНФИГУРАЦИЯ - ПРОДАКШН РЕЖИМ
# ============================================================================
# ⚠️ ВНИМАНИЕ: Это РЕАЛЬНЫЕ ключи для продакшена!
# Реальные деньги будут списываться при оплате!

# Продакшн режим (True = тест, False = продакшн)
YOOKASSA_TEST_MODE = False

# Реальные ключи ЮKassa для продакшена
YOOKASSA_SHOP_ID = "1167146"  # Ваш реальный Shop ID
YOOKASSA_SECRET_KEY = "live_X2q1FnC0N9VBhbl93xfNhgPHc3iBLQWvV1DtAT2mNlk"  # Реальный ключ
YOOKASSA_WEBHOOK_SECRET = "real_webhook_secret_2024"  # Реальный webhook secret

# Цена создания профиля в рублях
PROFILE_CREATION_PRICE = 10.00

# URL для webhook'ов (замените на ваш реальный домен)
YOOKASSA_WEBHOOK_URL = "https://yourdomain.com/yookassa/webhook"  # ЗАМЕНИТЕ НА ВАШ ДОМЕН!


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
    # Поля для оплаты
    is_paid = db.Column(db.Boolean, default=False)
    payment_date = db.Column(db.DateTime, nullable=True)
    # Поле для безопасности - IP-адрес создания профиля
    creation_ip = db.Column(db.String, nullable=True)


class PendingProfile(db.Model):
    """Временная анкета до оплаты"""
    id = db.Column(db.String, primary_key=True)
    name = db.Column(db.String, nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String, nullable=False)
    hobbies = db.Column(db.String, nullable=False)
    goal = db.Column(db.String, nullable=False)
    city = db.Column(db.String, nullable=True)
    venue = db.Column(db.String, nullable=True)
    photo = db.Column(db.String, nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    creation_ip = db.Column(db.String, nullable=True)
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


class Match(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user1_id = db.Column(db.String, nullable=False)
    user2_id = db.Column(db.String, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user1_viewed_at = db.Column(db.DateTime, nullable=True)
    user2_viewed_at = db.Column(db.DateTime, nullable=True)
    __table_args__ = (db.UniqueConstraint('user1_id', 'user2_id', name='unique_match'),)


class Payment(db.Model):
    """Модель для хранения информации о платежах"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String, nullable=False, default='pending')  # pending, succeeded, canceled
    description = db.Column(db.String, nullable=True)
    payment_method = db.Column(db.String, nullable=True)
    yookassa_payment_id = db.Column(db.String, nullable=True)
    yookassa_payment_url = db.Column(db.String, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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


# ============================================================================
# ЮKASSA ФУНКЦИИ - ТЕСТОВЫЙ РЕЖИМ
# ============================================================================

def get_base_url():
    """Получает базовый URL для текущего запроса"""
    if request:
        scheme = 'https' if request.is_secure else 'http'
        host = request.host
        return f"{scheme}://{host}"
    else:
        # Fallback для случаев когда request недоступен
        # Можно задать через переменную окружения DEPLOY_DOMAIN
        import os
        deploy_domain = os.getenv('DEPLOY_DOMAIN', 'https://your-domain.com')
        return deploy_domain


def create_yookassa_payment(user_id, amount, description="Создание профиля"):
    """Создает платеж в ЮKassa"""
    try:
        import base64
        import json

        # Подготавливаем данные для создания платежа
        payment_data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": f"{get_base_url()}/payment/success?user_id={user_id}"
            },
            "capture": True,
            "description": description,
            "metadata": {
                "user_id": user_id,
                "test_mode": str(YOOKASSA_TEST_MODE).lower()
            },
            "receipt": {
                "customer": {
                    "email": f"user_{user_id}@example.com"
                },
                "items": [
                    {
                        "description": description,
                        "amount": {
                            "value": f"{amount:.2f}",
                            "currency": "RUB"
                        },
                        "vat_code": "1",
                        "quantity": "1"
                    }
                ]
            }
        }

        # Формируем URL для API ЮKassa
        if YOOKASSA_TEST_MODE:
            api_url = "https://api.yookassa.ru/v3/payments"
        else:
            api_url = "https://api.yookassa.ru/v3/payments"

        # Создаем заголовки авторизации
        credentials = f"{YOOKASSA_SHOP_ID}:{YOOKASSA_SECRET_KEY}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        headers = {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "Idempotence-Key": str(uuid.uuid4())
        }

        # В тестовом режиме создаем фиктивный платеж
        if YOOKASSA_TEST_MODE:
            # Создаем тестовый результат
            test_payment_id = f"test_payment_{uuid.uuid4().hex[:8]}"
            test_payment_url = f"{get_base_url()}/payment/test-success?payment_id={test_payment_id}"

            result = {
                'id': test_payment_id,
                'confirmation': {
                    'confirmation_url': test_payment_url
                },
                'status': 'pending'
            }

            print(f"🧪 ТЕСТОВЫЙ РЕЖИМ: создан фиктивный платеж {test_payment_id}")
        else:
            # Отправляем запрос к ЮKassa
            print(f"🔍 Отправляем запрос к YooKassa API...")
            print(f"🔍 URL: {api_url}")
            print(f"🔍 Данные: {json.dumps(payment_data, ensure_ascii=False, indent=2)}")

            response = requests.post(api_url, json=payment_data, headers=headers, timeout=30)

            print(f"🔍 Статус ответа: {response.status_code}")
            print(f"🔍 Ответ: {response.text}")

            # Проверяем статус ответа
            if response.status_code == 401:
                raise Exception("Ошибка аутентификации YooKassa: неверные ключи API")
            elif response.status_code == 400:
                error_detail = response.text
                raise Exception(f"Ошибка запроса YooKassa (400): {error_detail}")
            elif response.status_code != 201:
                response.raise_for_status()

            result = response.json()

        # Сохраняем платеж в базу данных
        payment = Payment(
            user_id=user_id,
            amount=amount,
            status='pending',
            description=description,
            yookassa_payment_id=result.get('id'),
            yookassa_payment_url=result.get('confirmation', {}).get('confirmation_url')
        )
        db.session.add(payment)
        db.session.commit()

        print(f"✅ Платеж создан для пользователя {user_id}: {result.get('id')}")
        return {
            'success': True,
            'payment_id': result.get('id'),
            'payment_url': result.get('confirmation', {}).get('confirmation_url'),
            'amount': amount
        }

    except Exception as e:
        print(f"❌ Ошибка создания платежа: {e}")
        return {
            'success': False,
            'error': str(e)
        }


def verify_yookassa_webhook(data, signature):
    """Проверяет подпись webhook'а от ЮKassa"""
    try:
        import hmac
        import hashlib

        # В тестовом режиме пропускаем проверку подписи
        if YOOKASSA_TEST_MODE:
            print("🧪 Тестовый режим: пропускаем проверку подписи webhook'а")
            return True

        # Создаем подпись из данных
        expected_signature = hmac.new(
            YOOKASSA_WEBHOOK_SECRET.encode(),
            data.encode(),
            hashlib.sha256
        ).hexdigest()

        # Сравниваем подписи
        return hmac.compare_digest(signature, expected_signature)

    except Exception as e:
        print(f"❌ Ошибка проверки подписи webhook'а: {e}")
        return False


def process_payment_completion(user_id, payment_id, status):
    """Обрабатывает завершение платежа"""
    try:
        # Находим платеж в базе данных
        payment = Payment.query.filter_by(
            user_id=user_id,
            yookassa_payment_id=payment_id
        ).first()

        if not payment:
            print(f"❌ Платеж не найден: {payment_id}")
            return False

        # Обновляем статус платежа
        payment.status = status
        payment.updated_at = datetime.utcnow()

        # Если платеж успешен, создаем настоящую анкету из временной
        if status == 'succeeded':
            profile = Profile.query.get(user_id)
            if profile and profile.is_paid:
                print(f"✅ Профиль {user_id} уже оплачен")
            else:
                # Получаем временную анкету
                pending = PendingProfile.query.get(user_id)
                if pending:
                    # Создаем настоящую анкету из временной
                    profile = Profile(
                        id=pending.id,
                        name=pending.name,
                        age=pending.age,
                        gender=pending.gender,
                        hobbies=pending.hobbies,
                        goal=pending.goal,
                        city=pending.city,
                        venue=pending.venue,
                        photo=pending.photo,
                        likes=0,
                        latitude=pending.latitude,
                        longitude=pending.longitude,
                        creation_ip=pending.creation_ip,
                        is_paid=True,
                        payment_date=datetime.utcnow(),
                        created_at=datetime.utcnow()  # Таймер запускается после оплаты!
                    )
                    db.session.add(profile)
                    # Удаляем временную анкету
                    db.session.delete(pending)
                    print(f"✅ Профиль пользователя {user_id} создан после оплаты, таймер запущен!")
                else:
                    print(f"❌ Временная анкета пользователя {user_id} не найдена")
                    return False

        db.session.commit()
        print(f"✅ Платеж {payment_id} обновлен: {status}")
        return True

    except Exception as e:
        print(f"❌ Ошибка обработки платежа: {e}")
        db.session.rollback()
        return False


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
    if not user_id:
        return 0
    # Считаем непросмотренные метчи
    unread_matches = Match.query.filter(
        ((Match.user1_id == user_id) & (Match.user1_viewed_at.is_(None))) |
        ((Match.user2_id == user_id) & (Match.user2_viewed_at.is_(None)))
    ).count()
    return unread_matches


def get_profile_lifetime_remaining(user_id):
    """
    Возвращает оставшееся время жизни анкеты в часах и минутах
    """
    if not user_id:
        return None

    profile = Profile.query.get(user_id)
    if not profile or not profile.created_at:
        return None

    from datetime import datetime, timezone, timedelta

    # Преобразуем created_at в UTC если нужно
    created_at = profile.created_at
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=timezone.utc)

    # Вычисляем время истечения
    expiration_time = created_at + timedelta(hours=PROFILE_LIFETIME_HOURS)
    current_time = datetime.now(timezone.utc)

    # Вычисляем оставшееся время
    remaining = expiration_time - current_time

    if remaining.total_seconds() <= 0:
        return "Истекла"

    # Преобразуем в часы и минуты
    total_hours = int(remaining.total_seconds() // 3600)
    total_minutes = int((remaining.total_seconds() % 3600) // 60)

    if total_hours > 0:
        return f"{total_hours}ч {total_minutes}м"
    else:
        return f"{total_minutes}м"


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
        <a href="/settings" style="font-size:2em;margin:0 10px;{{'font-weight:bold;color:#ff6b6b;' if active=='settings' else ''}}" title="Настройки">⚙️</a>
    </nav>
    <div style="height:48px"></div>
    <style>
        /* Предотвращение масштабирования на мобильных устройствах */
        html, body {
            touch-action: manipulation;
            -webkit-touch-callout: none;
            -webkit-user-select: none;
            -khtml-user-select: none;
            -moz-user-select: none;
            -ms-user-select: none;
            user-select: none;
            -webkit-tap-highlight-color: transparent;
        }

        /* Отключаем двойное нажатие для масштабирования */
        * {
            touch-action: manipulation;
        }
    </style>
    <script>
    // Глобальные переменные для отслеживания предыдущих значений счетчиков
    let previousUnreadMessages = {{ unread_messages }};
    let previousUnreadLikes = {{ unread_likes }};
    let previousUnreadMatches = {{ unread_matches }};

    // Глобальная функция воспроизведения звука колокольчика
    function playNotificationSound() {
        // Проверяем настройки пользователя перед воспроизведением
        fetch('/api/get_settings')
            .then(response => response.json())
            .then(settings => {
                if (!settings.sound_notifications) {
                    console.log('🔕 Звук отключен в настройках');
                    return;
                }

                try {
                    // Создаем простой звук колокольчика
                    const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const oscillator = audioContext.createOscillator();
                    const gainNode = audioContext.createGain();

                    // Классический звук колокольчика
                    oscillator.type = 'sine';
                    oscillator.frequency.setValueAtTime(800, audioContext.currentTime); // 800 Гц
                    oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1); // 600 Гц через 0.1 сек
                    oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.2); // 1000 Гц через 0.2 сек
                    oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.3); // 400 Гц через 0.3 сек

                    gainNode.gain.setValueAtTime(0.3, audioContext.currentTime); // Громкость 30%
                    gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

                    oscillator.connect(gainNode);
                    gainNode.connect(audioContext.destination);

                    oscillator.start(audioContext.currentTime);
                    oscillator.stop(audioContext.currentTime + 0.5); // Длительность 0.5 секунды

                    console.log('🔔 Звук колокольчика воспроизведен для уведомления');

                } catch (error) {
                    console.error('❌ Ошибка воспроизведения звука:', error);
                }
            })
            .catch(error => {
                console.error('❌ Ошибка получения настроек:', error);
            });
    }

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

                        // Воспроизводим звук только при появлении новых сообщений
                        if (data.unread_messages > previousUnreadMessages) {
                            playNotificationSound();
                        }
                    } else {
                        msgBadge.style.display = 'none';
                    }
                    previousUnreadMessages = data.unread_messages;
                }

                let likeBadge = document.getElementById('like-badge');
                if (likeBadge) {
                    if (data.unread_likes > 0) {
                        likeBadge.innerText = data.unread_likes;
                        likeBadge.style.display = '';

                        // Воспроизводим звук только при появлении новых лайков
                        if (data.unread_likes > previousUnreadLikes) {
                            playNotificationSound();
                        }
                    } else {
                        likeBadge.style.display = 'none';
                    }
                    previousUnreadLikes = data.unread_likes;
                }

                let matchBadge = document.getElementById('match-badge');
                if (matchBadge) {
                    if (data.unread_matches > 0) {
                        matchBadge.innerText = data.unread_matches;
                        matchBadge.style.display = '';

                        // Воспроизводим звук только при появлении новых матчей
                        if (data.unread_matches > previousUnreadMatches) {
                            playNotificationSound();
                        }
                    } else {
                        matchBadge.style.display = 'none';
                    }
                    previousUnreadMatches = data.unread_matches;
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
                                       window.location.hostname === '127.0.0.1' ||
                                       window.location.hostname.startsWith('192.168.') ||
                                       window.location.hostname.startsWith('10.') ||
                                       window.location.hostname.includes('.local');

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
    # Автоматически запускаем очистку просроченных анкет на главной странице
    try:
        cleanup_expired_profiles()
    except Exception as e:
        print(f"⚠️ Ошибка при автоматической очистке: {e}")

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
        unread_likes=get_unread_likes_count(user_id),
        unread_matches=get_unread_matches_count(user_id)
    )
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
            <title>Знакомства в кафе</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { 
                    text-align: center; 
                    padding: 20px; 
                }
                h1 { 
                    color: white; 
                    margin-top: 0; 
                    margin-bottom: 20px;
                    font-size: 2.5em;
                }
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
                    background: #a709b5;
                    color: #fff;
                    border: none;
                    border-radius: 40px;
                    box-shadow: 0 6px 24px rgba(167, 9, 181, 0.3);
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    gap: 12px;
                }
                .big-create-btn:hover {
                    box-shadow: 0 12px 32px rgba(167, 9, 181, 0.4);
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
            <h1>Добро пожаловать в приложение</h1>
            {% for notification in unread_notifications %}
                <div class="notification">{{ notification.message }}</div>
            {% endfor %}
            <div class="welcome-message">
                <p class="welcome-text">Хотите найти приятную компанию за чашечкой кофе? ☕</p>
                <p class="welcome-description">Наше приложение поможет вам познакомиться с интересными людьми в заведениях — для душевных бесед, новых знакомств или просто хорошего времени.</p>
                <p class="welcome-price">Регистрация — всего {{ PROFILE_CREATION_PRICE }} рублей, а возможности — бесценны! 😊</p>
            </div>
            <p style="color: white;">Здесь вы можете найти интересных людей для общения.</p>
            <div id="create-profile-section" style="display: {% if not has_profile %}block{% else %}none{% endif %};">
                <a href="/create" class="big-create-btn">
                    Создать анкету
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
                                  get_starry_night_css=get_starry_night_css,
                                  PROFILE_CREATION_PRICE=PROFILE_CREATION_PRICE)


@app.route('/create', methods=['GET', 'POST'])
def create_profile():
    # Автоматически запускаем очистку просроченных анкет при создании профиля
    try:
        cleanup_expired_profiles()
        cleanup_expired_pending_profiles()  # Очищаем временные анкеты
    except Exception as e:
        print(f"⚠️ Ошибка при автоматической очистке: {e}")

    # Получаем user_id из cookie или генерируем новый
    user_id = request.cookies.get('user_id')

    # Проверяем, есть ли уже анкета у пользователя
    if user_id:
        # Проверяем оплаченный профиль
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
                return redirect(url_for('my_profile'))

        # Проверяем временную анкету (не оплачена)
        pending_profile = PendingProfile.query.get(user_id)
        if pending_profile:
            if request.method == 'POST':
                return jsonify({
                    'success': False,
                    'error': 'Анкета уже создана, ожидает оплаты.',
                    'has_active_profile': False
                }), 400
            else:
                # Для GET запроса перенаправляем на оплату
                return redirect(url_for('payment'))

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

        photo = request.files.get('photo')
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
                # Получаем IP-адрес клиента для безопасности
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

                # Создаем ВРЕМЕННУЮ анкету (до оплаты)
                pending_profile = PendingProfile(
                    id=user_id,
                    name=name,
                    age=int(request.form['age']),
                    gender=request.form['gender'],
                    hobbies=hobbies,
                    goal=goal,
                    city=location_name,
                    venue=venue,
                    photo=filename,
                    latitude=float(latitude) if latitude else None,
                    longitude=float(longitude) if longitude else None,
                    creation_ip=client_ip
                )
                db.session.add(pending_profile)
                db.session.commit()

                # Возвращаем JSON ответ для AJAX запроса
                resp = jsonify({
                    'success': True,
                    'user_id': user_id,
                    'redirect': url_for('payment')
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
    # Навигационная панель убрана со страницы создания анкеты
    return render_template_string(r'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
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
            <div class="form-container">
                <h2 style="text-align: center; margin-top: 10px;">Создать анкету</h2>
                <p style="color: #fff; opacity: 0.8; margin-bottom: 20px; text-align: center;">
                    📍 Ваше местоположение будет определено автоматически
                </p>
                <div id="location-status" style="background: rgba(76, 175, 80, 0.1); border: 1px solid rgba(76, 175, 80, 0.3); padding: 15px; border-radius: 10px; margin: 10px 0; color: #fff; text-align: center; display: none; font-size: 0.9em; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                    📍 Определяем ваше местоположение...
                </div>
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

                    <p style="color: #fff; font-size: 0.9em; margin-bottom: 15px; text-align: center; opacity: 0.8;">
                        На карте кликните на заведение, чтобы выбрать его
                    </p>
                    <div style="text-align: center; margin-bottom: 10px;">
                        <button type="button" class="location-btn" onclick="getCurrentLocation()" style="background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%); color: white; border: none; padding: 12px 24px; border-radius: 20px; font-size: 1em; cursor: pointer; margin: 5px; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(76,175,80,0.3);">
                            📍 Определить мое местоположение
                        </button>
                    </div>
                    <div class="map-container">
                        <div id="map"></div>
                        <button type="button" id="return-to-location-btn" class="location-return-btn" onclick="returnToMyLocation()" style="display: block;">
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
            <div style="text-align: center; margin-top: 15px; padding: 10px; background: rgba(76, 175, 80, 0.1); border-radius: 10px; border: 1px solid rgba(76, 175, 80, 0.3);">
                <p style="color: #4CAF50; font-size: 0.9em; margin: 0; text-shadow: 0 0 5px rgba(76, 175, 80, 0.3);">
                    ⏰ Анкета удалится через {{ PROFILE_LIFETIME_HOURS|int if PROFILE_LIFETIME_HOURS|int == PROFILE_LIFETIME_HOURS else PROFILE_LIFETIME_HOURS * 60|int }} {{ 'час' if PROFILE_LIFETIME_HOURS|int == PROFILE_LIFETIME_HOURS and PROFILE_LIFETIME_HOURS|int == 1 else 'часа' if PROFILE_LIFETIME_HOURS|int == PROFILE_LIFETIME_HOURS and PROFILE_LIFETIME_HOURS|int in [2,3,4] else 'часов' if PROFILE_LIFETIME_HOURS|int == PROFILE_LIFETIME_HOURS else 'минут' }}
                </p>
            </div>
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
                        // Добавляем небольшую задержку для полной загрузки страницы
                        setTimeout(function() {
                            console.log('🚀 Автоматически определяем местоположение...');
                            getCurrentLocation();
                        }, 1000);

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
                    console.log('🔍 Ищем кнопку "Я тут":', returnBtn);
                    if (returnBtn) {
                        returnBtn.style.display = 'block';
                        console.log('✅ Кнопка "Я тут" показана');
                    } else {
                        console.log('❌ Кнопка "Я тут" не найдена!');
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
                    console.log('📍 Начинаем определение местоположения...');

                    // Показываем статус пользователю
                    const statusDiv = document.getElementById('location-status');
                    if (statusDiv) {
                        statusDiv.innerHTML = '📍 Определяем ваше местоположение...';
                        statusDiv.style.display = 'block';
                    }

                    if (navigator.geolocation) {
                        console.log('✅ Геолокация поддерживается браузером');

                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                console.log('✅ Местоположение получено успешно!');
                                console.log('📍 Координаты:', position.coords.latitude, position.coords.longitude);

                                var lat = position.coords.latitude;
                                var lng = position.coords.longitude;

                                // Обновляем статус
                                if (statusDiv) {
                                    statusDiv.innerHTML = '✅ Местоположение определено успешно!';
                                    setTimeout(() => {
                                        statusDiv.style.display = 'none';
                                    }, 3000);
                                }

                                setLocation(lat, lng);
                            },
                            function(error) {
                                console.error('❌ Ошибка геолокации:', error);

                                let errorMessage = '❌ Ошибка определения местоположения: ';
                                switch(error.code) {
                                    case error.PERMISSION_DENIED:
                                        errorMessage += 'Доступ к геолокации запрещен. Нажмите на иконку замка в адресной строке и разрешите геолокацию, или используйте кнопку "Определить местоположение" ниже.';
                                        break;
                                    case error.POSITION_UNAVAILABLE:
                                        errorMessage += 'Местоположение недоступно. Возможно, нет GPS или WiFi. Попробуйте кнопку "Определить местоположение".';
                                        break;
                                    case error.TIMEOUT:
                                        errorMessage += 'Время ожидания истекло. Попробуйте кнопку "Определить местоположение" или разрешите геолокацию в настройках браузера.';
                                        break;
                                    default:
                                        errorMessage += 'Неизвестная ошибка. Попробуйте кнопку "Определить местоположение" ниже.';
                                        break;
                                }

                                console.log(errorMessage);

                                // Показываем ошибку пользователю
                                if (statusDiv) {
                                    statusDiv.innerHTML = errorMessage;
                                    statusDiv.style.background = 'rgba(244, 67, 54, 0.1)';
                                    statusDiv.style.borderColor = 'rgba(244, 67, 54, 0.3)';
                                    statusDiv.style.color = '#f44336';
                                }

                                // Пытаемся определить местоположение по IP
                                console.log('📍 Пытаемся определить местоположение по IP...');
                                getLocationByIP();
                            },
                            {
                                enableHighAccuracy: true,  // Включаем высокую точность
                                timeout: 10000,           // 10 секунд ожидания
                                maximumAge: 60000         // 1 минута кэширования
                            }
                        );
                    } else {
                        console.log('❌ Геолокация не поддерживается вашим браузером');

                        // Показываем ошибку пользователю
                        if (statusDiv) {
                            statusDiv.innerHTML = '❌ Ваш браузер не поддерживает геолокацию. Используется местоположение по умолчанию.';
                            statusDiv.style.background = 'rgba(255, 152, 0, 0.1)';
                            statusDiv.style.borderColor = 'rgba(255, 152, 0, 0.3)';
                            statusDiv.style.color = '#ff9800';
                        }

                        // Устанавливаем местоположение по умолчанию
                        setLocation(55.76, 37.64);
                    }
                }

                // Функция определения местоположения по IP-адресу
                function getLocationByIP() {
                    console.log('🌐 Определяем местоположение по IP...');

                    // Используем бесплатный сервис для определения местоположения по IP
                    fetch('https://ipapi.co/json/')
                        .then(response => response.json())
                        .then(data => {
                            if (data.latitude && data.longitude) {
                                console.log('✅ Местоположение определено по IP:', data.latitude, data.longitude);
                                console.log('📍 Город:', data.city, data.region, data.country);

                                // Обновляем статус
                                const statusDiv = document.getElementById('location-status');
                                if (statusDiv) {
                                    statusDiv.innerHTML = `✅ Местоположение определено по IP: ${data.city}, ${data.region}`;
                                    statusDiv.style.background = 'rgba(76, 175, 80, 0.1)';
                                    statusDiv.style.borderColor = 'rgba(76, 175, 80, 0.3)';
                                    statusDiv.style.color = '#4CAF50';
                                    setTimeout(() => {
                                        statusDiv.style.display = 'none';
                                    }, 5000);
                                }

                                setLocation(data.latitude, data.longitude);
                            } else {
                                console.log('❌ Не удалось определить местоположение по IP');
                                fallbackToDefaultLocation();
                            }
                        })
                        .catch(error => {
                            console.error('❌ Ошибка при определении местоположения по IP:', error);
                            fallbackToDefaultLocation();
                        });
                }

                // Функция fallback к местоположению по умолчанию
                function fallbackToDefaultLocation() {
                    console.log('📍 Устанавливаем местоположение по умолчанию (Москва)');

                    const statusDiv = document.getElementById('location-status');
                    if (statusDiv) {
                        statusDiv.innerHTML = '📍 Используется местоположение по умолчанию (Москва)';
                        statusDiv.style.background = 'rgba(255, 152, 0, 0.1)';
                        statusDiv.style.borderColor = 'rgba(255, 152, 0, 0.3)';
                        statusDiv.style.color = '#ff9800';
                        setTimeout(() => {
                            statusDiv.style.display = 'none';
                        }, 5000);
                    }

                    setLocation(55.76, 37.64);
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
                                venueInput.value = `${venueName} (${distanceText})`;
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
    ''', get_photo_url=get_photo_url, get_starry_night_css=get_starry_night_css,
                                  PROFILE_LIFETIME_HOURS=PROFILE_LIFETIME_HOURS)


# Функции для работы с настройками пользователя
def get_user_settings(user_id):
    """Получает настройки пользователя из базы данных"""
    try:
        import sqlite3
        conn = sqlite3.connect('dating_app.db')
        cursor = conn.cursor()

        cursor.execute('SELECT sound_notifications FROM user_settings WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            return {'sound_notifications': bool(result[0])}
        else:
            # Создаем настройки по умолчанию
            return {'sound_notifications': True}

    except Exception as e:
        print(f"❌ Ошибка получения настроек для {user_id}: {e}")
        return {'sound_notifications': True}


def update_user_settings(user_id, sound_notifications):
    """Обновляет настройки пользователя в базе данных"""
    try:
        import sqlite3
        conn = sqlite3.connect('dating_app.db')
        cursor = conn.cursor()

        # Проверяем, есть ли уже настройки для пользователя
        cursor.execute('SELECT id FROM user_settings WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()

        if existing:
            # Обновляем существующие настройки
            cursor.execute('''
                UPDATE user_settings 
                SET sound_notifications = ?, updated_at = ? 
                WHERE user_id = ?
            ''', (1 if sound_notifications else 0, datetime.utcnow(), user_id))
        else:
            # Создаем новые настройки
            cursor.execute('''
                INSERT INTO user_settings (user_id, sound_notifications, created_at, updated_at) 
                VALUES (?, ?, ?, ?)
            ''', (user_id, 1 if sound_notifications else 0, datetime.utcnow(), datetime.utcnow()))

        conn.commit()
        conn.close()

        print(f"✅ Настройки обновлены для {user_id}: sound_notifications = {sound_notifications}")
        return True

    except Exception as e:
        print(f"❌ Ошибка обновления настроек для {user_id}: {e}")
        return False


def require_profile(check_payment=True):
    """Декоратор для проверки наличия профиля и опционально оплаты"""

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(*args, **kwargs):
            # Автоматически запускаем очистку просроченных анкет при каждом запросе
            try:
                cleanup_expired_profiles()
                cleanup_expired_pending_profiles()  # Очищаем временные анкеты
            except Exception as e:
                print(f"⚠️ Ошибка при автоматической очистке: {e}")

            user_id = request.cookies.get('user_id')
            print(f"🔍 @require_profile: проверяем пользователя {user_id}")

            if not user_id:
                print(f"❌ @require_profile: нет user_id в cookie, перенаправляем на создание")
                return redirect(url_for('create_profile'))

            profile = Profile.query.get(user_id)
            if profile is None:
                print(f"❌ @require_profile: профиль {user_id} не найден, перенаправляем на создание")
                return redirect(url_for('create_profile'))

            print(f"✅ @require_profile: профиль найден - {profile.name}, оплачен: {profile.is_paid}")

            # Проверяем оплату только если требуется
            if check_payment and profile and not profile.is_paid:
                print(f"💰 @require_profile: профиль не оплачен, перенаправляем на оплату")
                return redirect(url_for('payment'))

            # Дополнительная проверка безопасности: проверяем, что IP-адрес совпадает
            # Это предотвращает доступ к чужим анкетам через общие cookies
            if profile and hasattr(profile, 'creation_ip') and profile.creation_ip:
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                if profile.creation_ip != client_ip:
                    return redirect(url_for('create_profile'))

            return view_func(*args, **kwargs)

        return wrapper

    return decorator


def calculate_distance_between_users(user_profile, other_profile):
    """Рассчитывает расстояние между двумя пользователями в метрах"""
    try:
        # Проверяем, что у обоих пользователей есть координаты
        if not all([user_profile.latitude, user_profile.longitude,
                    other_profile.latitude, other_profile.longitude]):
            return None

        # Используем geopy.distance.geodesic для расчета расстояния
        from geopy.distance import geodesic

        user_point = (float(user_profile.latitude), float(user_profile.longitude))
        other_point = (float(other_profile.latitude), float(other_profile.longitude))

        distance = geodesic(user_point, other_point).meters
        return distance

    except (ValueError, TypeError) as e:
        print(f"❌ Ошибка расчета расстояния между пользователями: {e}")
        return None


@app.route('/visitors')
@require_profile()
def view_visitors():
    user_id = request.cookies.get('user_id')
    user_profile = Profile.query.get(user_id)

    # Получаем фильтры из query-параметров
    venue_query = request.args.get('venue', '').strip().lower()
    gender_query = request.args.get('gender', '')

    # Фильтруем профили
    other_profiles = [p for p in Profile.query.all() if p.id != user_id]

    # Применяем фильтр по расстоянию MAX_REGISTRATION_DISTANCE
    if user_profile and user_profile.latitude and user_profile.longitude:
        filtered_profiles = []
        for profile in other_profiles:
            distance = calculate_distance_between_users(user_profile, profile)
            if distance is not None and distance <= MAX_REGISTRATION_DISTANCE:
                # Добавляем расстояние к профилю для отображения
                profile.distance_to_user = distance
                filtered_profiles.append(profile)
        other_profiles = filtered_profiles

    if venue_query:
        other_profiles = [p for p in other_profiles if p.venue and venue_query in p.venue.lower()]
    if gender_query:
        other_profiles = [p for p in other_profiles if p.gender == gender_query]
    # liked_ids включает лайки и метчи
    liked_ids = set(l.liked_id for l in Like.query.filter_by(user_id=user_id).all())

    # Добавляем пользователей из метчей
    matches = Match.query.filter(
        (Match.user1_id == user_id) | (Match.user2_id == user_id)
    ).all()

    for match in matches:
        if match.user1_id == user_id:
            liked_ids.add(match.user2_id)
        else:
            liked_ids.add(match.user1_id)
    navbar = render_navbar(user_id, active='visitors', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
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
                // Функция воспроизведения звука колокольчика
                function playNotificationSound() {
                    try {
                        // Создаем простой звук колокольчика
                        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        const oscillator = audioContext.createOscillator();
                        const gainNode = audioContext.createGain();

                        // Классический звук колокольчика
                        oscillator.type = 'sine';
                        oscillator.frequency.setValueAtTime(800, audioContext.currentTime); // 800 Гц
                        oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1); // 600 Гц через 0.1 сек
                        oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.2); // 1000 Гц через 0.2 сек
                        oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.3); // 400 Гц через 0.3 сек

                        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime); // Громкость 30%
                        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

                        oscillator.connect(gainNode);
                        gainNode.connect(audioContext.destination);

                        oscillator.start(audioContext.currentTime);
                        oscillator.stop(audioContext.currentTime + 0.5); // Длительность 0.5 секунды

                        console.log('🔔 Звук колокольчика воспроизведен');

                    } catch (error) {
                        console.error('❌ Ошибка воспроизведения звука:', error);
                    }
                }

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

                    // Звук теперь воспроизводится только при обновлении счетчиков в навигации

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
                            if (data.match_created) {
                                btn.classList.add('liked'); // Оставляем красным при метче
                                showNotification('✨ У вас мэтч! Теперь вы можете общаться!', 'success');
                                setTimeout(() => location.reload(), 2000);
                            } else if (data.liked) {
                                btn.classList.add('liked');
                                if (data.already_liked) {
                                    // Уже лайкал - ничего не показываем
                            } else {
                                    showNotification('❤️ Лайк отправлен!', 'success');
                                }
                            } else {
                                // Убираем лайк (отмена лайка) - этого больше не должно происходить
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
            <div class="visitor-count">
                Посетителей: {{ other_profiles|length }}
                {% if get_profile_lifetime_remaining(user_id) %}
                <span id="lifetime-timer" style="margin-left: 20px; color: #fff; font-weight: normal;">
                    Анкета удалится через: {{ get_profile_lifetime_remaining(user_id) }}
                </span>
                {% endif %}
            </div>
            <h1 style="text-align: center;">Посетители кафе</h1>
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
                            <p style="color: #666; font-size: 0.9em;">🏪 {{ profile.venue.split(' (')[0] }}{% if profile.distance_to_user is defined and profile.distance_to_user %} ({{ (profile.distance_to_user/1000)|round(1) if profile.distance_to_user >= 1000 else profile.distance_to_user|round(0)|int }}{{ 'км' if profile.distance_to_user >= 1000 else 'м' }}){% endif %}</p>
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

            <script>
            // Обновление таймера жизни анкеты в реальном времени
            function updateLifetimeTimer() {
                const timerElement = document.getElementById('lifetime-timer');
                if (!timerElement) return;

                fetch('/api/profile-lifetime')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.remaining_time) {
                            timerElement.textContent = 'Анкета удалится через: ' + data.remaining_time;

                            // Если время истекло, перенаправляем на создание анкеты
                            if (data.remaining_time === 'Истекла') {
                                setTimeout(() => {
                                    window.location.href = '/create';
                                }, 2000);
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка обновления таймера:', error);
                    });
            }

            // Обновляем таймер каждые 30 секунд
            setInterval(updateLifetimeTimer, 30000);

            // Обновляем таймер при загрузке страницы
            document.addEventListener('DOMContentLoaded', updateLifetimeTimer);
            </script>
        </body>
        </html>
    ''', other_profiles=other_profiles, liked_ids=liked_ids, navbar=navbar, get_photo_url=get_photo_url,
                                  get_starry_night_css=get_starry_night_css,
                                  get_profile_lifetime_remaining=get_profile_lifetime_remaining, user_id=user_id)


@app.route('/edit_pending_profile', methods=['GET', 'POST'])
def edit_pending_profile():
    """Редактирование временной анкеты (до оплаты)"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    # Проверяем, есть ли уже оплаченный профиль
    profile = Profile.query.get(user_id)
    if profile:
        return redirect(url_for('my_profile'))

    # Получаем временную анкету
    pending = PendingProfile.query.get(user_id)
    if not pending:
        return redirect(url_for('create_profile'))

    if request.method == 'POST':
        pending.name = request.form['name']
        pending.age = int(request.form['age'])
        pending.gender = request.form['gender']
        pending.hobbies = request.form['hobbies']
        pending.goal = request.form['goal']
        pending.venue = request.form.get('venue')

        # Обработка координат
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        if latitude and longitude:
            pending.latitude = float(latitude)
            pending.longitude = float(longitude)

        # Смена фото
        photo = request.files.get('photo')
        if photo and photo.filename:
            try:
                if pending.photo:
                    os.remove(os.path.join(app.config['UPLOAD_FOLDER'], pending.photo))
            except:
                pass
            filename = f"{user_id}_{photo.filename}"
            photo_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            photo.save(photo_path)
            pending.photo = filename

        db.session.commit()
        return redirect(url_for('payment'))

    # Используем полный шаблон со страницы создания анкеты с картой
    return render_template_string(r'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
            <title>Редактировать анкету</title>
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
                    position: relative;
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
            </style>
        </head>
        <body>
            <div class="form-container">
                <h2 style="text-align: center; margin-top: 10px;">Редактировать анкету</h2>
                <p style="color: #fff; opacity: 0.8; margin-bottom: 20px; text-align: center;">
                    📍 Ваше местоположение: {{ pending.city or 'Определяется...' }}
                </p>
                <div id="location-status" style="background: rgba(76, 175, 80, 0.1); border: 1px solid rgba(76, 175, 80, 0.3); padding: 15px; border-radius: 10px; margin: 10px 0; color: #fff; text-align: center; display: none; font-size: 0.9em; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);">
                    📍 Определяем ваше местоположение...
                </div>
                <form method="post" enctype="multipart/form-data">
                <div class="field-container">
                    <input type="text" name="name" value="{{ pending.name }}" placeholder="Ваше имя" required maxlength="12" oninput="checkFieldLength(this, 12)">
                </div>
                <div class="field-container">
                    <input type="number" name="age" value="{{ pending.age }}" placeholder="Ваш возраст" required>
                </div>
                <div class="field-container">
                    <select name="gender" required>
                        <option value="">Выберите пол</option>
                        <option value="male" {% if pending.gender == 'male' %}selected{% endif %}>Мужской</option>
                        <option value="female" {% if pending.gender == 'female' %}selected{% endif %}>Женский</option>
                        <option value="other" {% if pending.gender == 'other' %}selected{% endif %}>Другое</option>
                    </select>
                </div>
                <div class="field-container">
                    <textarea name="hobbies" placeholder="Ваши увлечения" required maxlength="70" oninput="checkFieldLength(this, 70)">{{ pending.hobbies }}</textarea>
                </div>
                <div class="field-container">
                    <textarea name="goal" placeholder="Цель знакомства" required maxlength="70" oninput="checkFieldLength(this, 70)">{{ pending.goal }}</textarea>
                </div>

                    <p style="color: #fff; font-size: 0.9em; margin-bottom: 15px; text-align: center; opacity: 0.8;">
                        На карте кликните на заведение, чтобы выбрать его
                    </p>
                    <div style="text-align: center; margin-bottom: 10px;">
                        <button type="button" class="location-btn" onclick="getCurrentLocation()" style="background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%); color: white; border: none; padding: 12px 24px; border-radius: 20px; font-size: 1em; cursor: pointer; margin: 5px; transition: all 0.3s ease; box-shadow: 0 4px 16px rgba(76,175,80,0.3);">
                            📍 Определить мое местоположение
                        </button>
                    </div>
                    <div class="map-container">
                        <div id="map"></div>
                        <button type="button" id="return-to-location-btn" class="location-return-btn" onclick="returnToMyLocation()" style="display: block;">
                            📍 Я тут
                        </button>
                    </div>

                <div class="field-container">
                    <input type="text" name="venue" id="venue-input" value="{{ pending.venue or '' }}" placeholder="Название заведения (кафе, ресторан и т.д.)" required onchange="updateVenueCoordinates()">
                </div>
                <input type="hidden" name="latitude" id="latitude-input" value="{{ pending.latitude or '' }}">
                <input type="hidden" name="longitude" id="longitude-input" value="{{ pending.longitude or '' }}">
                <input type="hidden" name="venue_lat" id="venue-lat-input">
                <input type="hidden" name="venue_lng" id="venue-lng-input">

                <!-- Скрытые поля для координат и расстояния -->
                <input type="hidden" id="visitor-coordinates-display">
                <input type="hidden" id="venue-coordinates-display">
                <input type="hidden" id="distance-display">

                <div class="field-container">
                    <input type="file" name="photo" accept="image/*">
                    {% if pending.photo %}
                    <p style="color: #fff; font-size: 0.9em; margin-top: 5px;">Текущее фото: {{ pending.photo }}</p>
                    {% endif %}
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <button type="submit" class="modern-btn">Сохранить изменения</button>
                </div>
            </form>
            <div style="text-align: center; margin-top: 15px;">
                <a href="/payment" class="back-btn">← Назад к оплате</a>
            </div>
            </div>

            <script>
                function checkFieldLength(field, maxLength) {
                    // Функциональность ограничений
                }

                let myMap, myPlacemark;
                let currentLocation = { lat: {{ pending.latitude or 55.76 }}, lng: {{ pending.longitude or 37.64 }} };

                function initMap() {
                    ymaps.ready(function () {
                        myMap = new ymaps.Map('map', {
                            center: [currentLocation.lat, currentLocation.lng],
                            zoom: 15,
                            controls: ['zoomControl', 'fullscreenControl']
                        });

                        // Устанавливаем метку пользователя
                        myPlacemark = new ymaps.Placemark([currentLocation.lat, currentLocation.lng], {
                            balloonContent: 'Ваше местоположение'
                        }, {
                            preset: 'islands#redDotIcon'
                        });
                        myMap.geoObjects.add(myPlacemark);

                        // Устанавливаем координаты в скрытые поля
                        document.getElementById('latitude-input').value = currentLocation.lat;
                        document.getElementById('longitude-input').value = currentLocation.lng;
                        document.getElementById('visitor-coordinates-display').value = `${currentLocation.lat.toFixed(6)}, ${currentLocation.lng.toFixed(6)}`;

                        // Обработчик открытия балуна
                        myMap.events.add('balloonopen', function (e) {
                            setTimeout(function() {
                                parseBalloonAndFillVenue();
                            }, 500);
                        });
                    });
                }

                function getCurrentLocation() {
                    const statusDiv = document.getElementById('location-status');
                    if (statusDiv) {
                        statusDiv.innerHTML = '📍 Определяем ваше местоположение...';
                        statusDiv.style.display = 'block';
                    }

                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                var lat = position.coords.latitude;
                                var lng = position.coords.longitude;

                                if (statusDiv) {
                                    statusDiv.innerHTML = '✅ Местоположение определено успешно!';
                                    setTimeout(() => statusDiv.style.display = 'none', 3000);
                                }

                                setLocation(lat, lng);
                            },
                            function(error) {
                                if (statusDiv) {
                                    statusDiv.innerHTML = '❌ Ошибка определения местоположения';
                                    statusDiv.style.background = 'rgba(244, 67, 54, 0.1)';
                                }
                                getLocationByIP();
                            },
                            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
                        );
                    } else {
                        setLocation(currentLocation.lat, currentLocation.lng);
                    }
                }

                function setLocation(lat, lng) {
                    currentLocation = {lat: lat, lng: lng};
                    document.getElementById('latitude-input').value = lat;
                    document.getElementById('longitude-input').value = lng;
                    document.getElementById('visitor-coordinates-display').value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;

                    if (myPlacemark) myMap.geoObjects.remove(myPlacemark);
                    myPlacemark = new ymaps.Placemark([lat, lng], {
                        balloonContent: 'Ваше местоположение'
                    }, {
                        preset: 'islands#redDotIcon'
                    });
                    myMap.geoObjects.add(myPlacemark);
                    myMap.setCenter([lat, lng], 15);
                }

                function returnToMyLocation() {
                    if (currentLocation) {
                        myMap.setCenter([currentLocation.lat, currentLocation.lng], 15);
                    } else {
                        getCurrentLocation();
                    }
                }

                function getLocationByIP() {
                    fetch('https://ipapi.co/json/')
                        .then(response => response.json())
                        .then(data => {
                            if (data.latitude && data.longitude) {
                                setLocation(data.latitude, data.longitude);
                            }
                        })
                        .catch(error => console.error('Ошибка IP геолокации:', error));
                }

                function parseBalloonAndFillVenue() {
                    const result = extractNameFromBalloon();
                    if (result && result.name) {
                        document.getElementById('venue-input').value = result.name;
                        const mapCenter = myMap.getCenter();
                        showVenueCoordinates(result.name, mapCenter[0], mapCenter[1]);
                    }
                }

                function extractNameFromBalloon() {
                    let balloonContent = document.querySelector('.ymaps-2-1-79-balloon') || 
                                        document.querySelector('.ymaps-balloon') ||
                                        document.querySelector('[class*="balloon"]');
                    if (!balloonContent) return { name: null };

                    const links = balloonContent.querySelectorAll('a');
                    for (let link of links) {
                        const linkText = link.textContent.trim();
                        if (isValidVenueName(linkText)) {
                            return { name: linkText };
                        }
                    }
                    return { name: null };
                }

                function isValidVenueName(name) {
                    return name && name.length > 2 && name.length < 100 &&
                        !name.includes('Share') && !name.includes('Поделиться') &&
                        !name.includes('Телефон') && !name.includes('www.') &&
                        !name.includes('http') && !name.match(/^\d+$/);
                }

                function showVenueCoordinates(venueName, lat, lng) {
                    document.getElementById('venue-coordinates-display').value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                    document.getElementById('venue-lat-input').value = lat.toFixed(6);
                    document.getElementById('venue-lng-input').value = lng.toFixed(6);
                    calculateDistanceAndUpdateVenueField(venueName);
                }

                function calculateDistanceAndUpdateVenueField(venueName) {
                    const visitorCoords = document.getElementById('visitor-coordinates-display').value.trim();
                    const venueCoords = document.getElementById('venue-coordinates-display').value.trim();
                    const venueInput = document.getElementById('venue-input');

                    if (!visitorCoords || !venueCoords) {
                        venueInput.value = venueName;
                        return;
                    }

                    const [visitorLat, visitorLng] = visitorCoords.split(',').map(c => parseFloat(c.trim()));
                    const [venueLat, venueLng] = venueCoords.split(',').map(c => parseFloat(c.trim()));

                    fetch('/api/calculate-distance', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
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
                            const distanceText = distance < 1000 ? `${Math.round(distance)} м` : `${(distance / 1000).toFixed(1)} км`;
                            venueInput.value = `${venueName} (${distanceText})`;
                        }
                    })
                    .catch(error => console.error('Ошибка расчета расстояния:', error));
                }

                function updateVenueCoordinates() {
                    const venueInput = document.getElementById('venue-input');
                    let venueName = venueInput.value.trim().replace(/\s*\(\d+\.?\d*\s*(м|км)\)$/, '');
                    if (!venueName) {
                        document.getElementById('venue-coordinates-display').value = '';
                        document.getElementById('venue-lat-input').value = '';
                        document.getElementById('venue-lng-input').value = '';
                    }
                }

                window.onload = function() {
                    initMap();
                    // Автоматически определяем местоположение
                    setTimeout(() => getCurrentLocation(), 1000);
                };
            </script>
        </body>
        </html>
    ''', pending=pending, get_starry_night_css=get_starry_night_css)


@app.route('/toggle_like/<string:profile_id>', methods=['POST'])
@require_profile()
def toggle_like(profile_id):
    user_id = request.cookies.get('user_id')
    if not user_id or Profile.query.get(profile_id) is None or profile_id == user_id:
        return jsonify({'liked': False, 'already_liked': False, 'likes_count': 0, 'match_created': False})

    # Проверяем, лайкал ли уже текущий пользователь
    already_liked = Like.query.filter(and_(Like.user_id == user_id, Like.liked_id == profile_id)).first()

    if already_liked:
        # Уже лайкал - ничего не делаем, сердечко остается красным
        likes_count = Like.query.filter_by(liked_id=profile_id).count()
        return jsonify({'liked': True, 'already_liked': True, 'likes_count': likes_count, 'match_created': False})

    # Проверяем, лайкал ли уже целевой пользователь текущего
    mutual_like = Like.query.filter(and_(Like.user_id == profile_id, Like.liked_id == user_id)).first()

    if mutual_like:
        # Взаимный лайк - создаем метч и удаляем лайк
        db.session.delete(mutual_like)
        db.session.commit()

        # Создаем метч в базе данных
        user_profile = Profile.query.get(user_id)
        matched_profile = Profile.query.get(profile_id)
        if user_profile and matched_profile:
            # Проверяем, что метч еще не существует
            existing_match = Match.query.filter(
                ((Match.user1_id == user_id) & (Match.user2_id == profile_id)) |
                ((Match.user1_id == profile_id) & (Match.user2_id == user_id))
            ).first()

            if not existing_match:
                # Создаем метч (всегда user1_id < user2_id для консистентности)
                user1_id, user2_id = sorted([user_id, profile_id])
                match = Match(user1_id=user1_id, user2_id=user2_id)
                db.session.add(match)
                db.session.commit()

            add_notification(user_id, f"✨ У вас мэтч с {matched_profile.name}! Теперь вы можете общаться.")
            add_notification(profile_id, f"✨ У вас мэтч с {user_profile.name}! Теперь вы можете общаться.")

        likes_count = Like.query.filter_by(liked_id=profile_id).count()
        return jsonify({'liked': False, 'already_liked': False, 'likes_count': likes_count, 'match_created': True})

    # Обычный лайк
    db.session.add(Like(user_id=user_id, liked_id=profile_id))
    db.session.commit()

    # Добавляем уведомление получателю лайка
    user_profile = Profile.query.get(user_id)
    liked_profile = Profile.query.get(profile_id)
    if user_profile and liked_profile:
        add_notification(profile_id, f"💖 {user_profile.name} лайкнул(а) вас!")

    likes_count = Like.query.filter_by(liked_id=profile_id).count()
    return jsonify({'liked': True, 'already_liked': False, 'likes_count': likes_count, 'match_created': False})


@app.route('/my_profile')
@require_profile()
def my_profile():
    # Получаем user_id из cookie или из URL параметров
    user_id = request.cookies.get('user_id') or request.args.get('user_id')

    # Если user_id из URL, устанавливаем его в cookie
    if request.args.get('user_id') and not request.cookies.get('user_id'):
        user_id = request.args.get('user_id')
        print(f"🔄 Устанавливаем user_id из URL в cookie: {user_id}")

    profile = Profile.query.get(user_id)
    print(f"👤 Загружаем профиль для {user_id}: {profile.name if profile else 'не найден'}")
    navbar = render_navbar(user_id, active='profile', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
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
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
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
                <form action="/delete/{{ profile.id }}" method="post" style="display:inline;" id="deleteForm1">
                    <button type="button" class="modern-btn delete-btn" style="background: #b00020;" onclick="confirmDelete(this, 'deleteForm1')">Удалить анкету</button>
                </form>
                <a href="/" class="back-btn">← На главную</a>
            </div>
        </body>
        <script>
            // Устанавливаем cookie user_id если он пришел из URL
            const urlParams = new URLSearchParams(window.location.search);
            const userIdFromUrl = urlParams.get('user_id');

            if (userIdFromUrl) {
                console.log('🆔 User ID из URL параметров:', userIdFromUrl);

                // Проверяем, есть ли уже cookie
                const currentUserId = document.cookie.match(/user_id=([^;]+)/);
                if (!currentUserId || currentUserId[1] !== userIdFromUrl) {
                    // Устанавливаем cookie
                    document.cookie = 'user_id=' + userIdFromUrl + '; path=/; max-age=' + (365*24*60*60) + '; SameSite=Lax';
                    console.log('🍪 Cookie user_id установлен из URL:', userIdFromUrl);

                    // Также сохраняем в localStorage
                    try {
                        localStorage.setItem('dating_app_user_id', userIdFromUrl);
                        sessionStorage.setItem('dating_app_user_id', userIdFromUrl);
                        console.log('💾 Сохранено в localStorage и sessionStorage');
                    } catch (e) {
                        console.warn('⚠️ Не удалось сохранить в localStorage:', e);
                    }
                } else {
                    console.log('✅ Cookie user_id уже установлен правильно');
                }
            }
            
            // Функция подтверждения удаления анкеты
            function confirmDelete(button, formId) {
                if (button.classList.contains('confirm-delete')) {
                    // Второе нажатие - удаляем
                    document.getElementById(formId).submit();
                } else {
                    // Первое нажатие - меняем кнопку
                    button.classList.add('confirm-delete');
                    button.innerHTML = '⚠️ Точно удалить?';
                    button.style.background = '#d32f2f';
                    button.style.animation = 'pulse 0.5s ease-in-out';
                    
                    // Через 3 секунды возвращаем кнопку в исходное состояние
                    setTimeout(function() {
                        button.classList.remove('confirm-delete');
                        button.innerHTML = 'Удалить анкету';
                        button.style.background = '#b00020';
                    }, 3000);
                }
            }
        </script>
        </html>
    ''', profile=profile, navbar=navbar, get_photo_url=get_photo_url, get_starry_night_css=get_starry_night_css)


@app.route('/edit_profile', methods=['GET', 'POST'])
@require_profile(check_payment=False)
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
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
            <title>Редактировать анкету</title>
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
                    console.log('🔍 Ищем кнопку "Я тут":', returnBtn);
                    if (returnBtn) {
                        returnBtn.style.display = 'block';
                        console.log('✅ Кнопка "Я тут" показана');
                    } else {
                        console.log('❌ Кнопка "Я тут" не найдена!');
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

                // Функция очистки расстояния
                function clearDistance() {
                    const distanceDisplay = document.getElementById('distance-display');
                    if (distanceDisplay) {
                        distanceDisplay.value = '';
                    }
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
                                venueInput.value = `${venueName} (${distanceText})`;
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

                    // На странице редактирования профиля карта должна инициализироваться всегда
                    console.log('🗺️ Инициализируем карту на странице редактирования профиля...');
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
            <div class="form-container">
                <h2 style="text-align: center; margin-top: 10px;">Редактировать анкету</h2>
                <p style="color: #fff; opacity: 0.8; margin-bottom: 20px; text-align: center;">
                    📍 Ваше местоположение будет определено автоматически
                </p>
            <form method="post" enctype="multipart/form-data">
                <div class="field-container">
                    <input type="text" name="name" placeholder="Ваше имя" value="{{ profile.name }}" required maxlength="12" oninput="checkFieldLength(this, 12)">
                </div>
                <div class="field-container">
                <input type="number" name="age" placeholder="Ваш возраст" value="{{ profile.age }}" required>
                </div>
                <div class="field-container">
                <select name="gender" required>
                    <option value="">Выберите пол</option>
                    <option value="male" {% if profile.gender == 'male' %}selected{% endif %}>Мужской</option>
                    <option value="female" {% if profile.gender == 'female' %}selected{% endif %}>Женский</option>
                    <option value="other" {% if profile.gender == 'other' %}selected{% endif %}>Другое</option>
                </select>
                </div>
                <div class="field-container">
                    <textarea name="hobbies" placeholder="Ваши увлечения" required maxlength="70" oninput="checkFieldLength(this, 70)">{{ profile.hobbies }}</textarea>
                </div>
                <div class="field-container">
                    <textarea name="goal" placeholder="Цель знакомства" required maxlength="70" oninput="checkFieldLength(this, 70)">{{ profile.goal }}</textarea>
                </div>

                <div class="map-container">
                    <div id="map"></div>
                        <button type="button" id="return-to-location-btn" class="location-return-btn" onclick="returnToMyLocation()" style="display: none;">
                            📍 Я тут
                        </button>
                </div>

                <div class="field-container">
                    <input type="text" name="venue" id="venue-input" placeholder="Название заведения (кафе, ресторан и т.д.)" value="{{ profile.venue or '' }}" required onchange="updateVenueCoordinates()">
                </div>
                <input type="hidden" name="latitude" id="latitude-input" value="{{ profile.latitude or '' }}">
                <input type="hidden" name="longitude" id="longitude-input" value="{{ profile.longitude or '' }}">
                <input type="hidden" name="venue_lat" id="venue-lat-input">
                <input type="hidden" name="venue_lng" id="venue-lng-input">

                <!-- Скрытые поля для координат и расстояния (используются для расчетов) -->
                <input type="hidden" id="visitor-coordinates-display">
                <input type="hidden" id="venue-coordinates-display">
                <input type="hidden" id="distance-display">

                <div class="field-container">
                <input type="file" name="photo" accept="image/*">
                </div>

                <div style="text-align: center; margin-top: 20px;">
                <button type="submit" class="modern-btn">Сохранить</button>
                </div>
            </form>
            <div style="text-align: center; margin-top: 15px;">
            <a href="/my_profile" class="back-btn">← Назад</a>
            </div>
            </div>
        </body>
        </html>
    ''', profile=profile, navbar=navbar, get_photo_url=get_photo_url, get_starry_night_css=get_starry_night_css)


@app.route('/my_likes')
@require_profile()
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

    # liked_ids включает лайки и метчи
    liked_ids = set(l.liked_id for l in Like.query.filter_by(user_id=user_id).all())

    # Добавляем пользователей из метчей
    matches = Match.query.filter(
        (Match.user1_id == user_id) | (Match.user2_id == user_id)
    ).all()

    for match in matches:
        if match.user1_id == user_id:
            liked_ids.add(match.user2_id)
        else:
            liked_ids.add(match.user1_id)

    navbar = render_navbar(user_id, active='likes', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
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
                            if (data.match_created) {
                                btn.classList.add('liked'); // Оставляем красным при метче
                                showNotification('✨ У вас мэтч! Теперь вы можете общаться!', 'success');
                                setTimeout(() => location.reload(), 2000);
                            } else if (data.liked) {
                                btn.classList.add('liked');
                                if (data.already_liked) {
                                    // Уже лайкал - ничего не показываем
                            } else {
                                    showNotification('❤️ Лайк отправлен!', 'success');
                                }
                            } else {
                                // Убираем лайк (отмена лайка) - этого больше не должно происходить
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
            <h1 style="text-align: center;">Меня лайкнули</h1>
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
                                  liked_ids=liked_ids,
                                  get_starry_night_css=get_starry_night_css)


@app.route('/profile/<string:id>')
@require_profile()
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
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
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
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
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

                    fetch('/toggle_like/' + profileId, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.liked && !data.already_liked) {
                            // Успешный новый лайк
                            showNotification('❤️ Лайк отправлен!', 'success');
                            // Скрываем кнопку после успешного лайка
                            button.textContent = '❤️ Лайкнуто';
                            button.style.background = '#4CAF50';
                            button.disabled = true;
                        } else if (data.already_liked) {
                            // Уже лайкал ранее
                            showNotification('💔 Вы уже лайкнули этого пользователя', 'warning');
                            button.textContent = '❤️ Лайкнуто';
                            button.style.background = '#4CAF50';
                            button.disabled = true;
                        } else if (data.match_created) {
                            // Создан мэтч!
                            showNotification('✨ У вас мэтч! Теперь вы можете общаться.', 'success');
                            button.textContent = '✨ Мэтч!';
                            button.style.background = '#ff6b6b';
                            button.disabled = true;
                        } else {
                            // Неожиданный ответ
                            showNotification('⚠️ Неожиданный ответ сервера', 'warning');
                            button.textContent = originalText;
                            button.disabled = false;
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка:', error);
                        showNotification('❌ Ошибка сети', 'error');
                        // Восстанавливаем кнопку при ошибке
                        button.textContent = originalText;
                        button.disabled = false;
                    });
                }
                
                // Функция подтверждения удаления анкеты
                function confirmDelete(button, formId) {
                    if (button.classList.contains('confirm-delete')) {
                        // Второе нажатие - удаляем
                        document.getElementById(formId).submit();
                    } else {
                        // Первое нажатие - меняем кнопку
                        button.classList.add('confirm-delete');
                        button.innerHTML = '⚠️ Точно удалить?';
                        button.style.background = '#d32f2f';
                        button.style.animation = 'pulse 0.5s ease-in-out';
                        
                        // Через 3 секунды возвращаем кнопку в исходное состояние
                        setTimeout(function() {
                            button.classList.remove('confirm-delete');
                            button.innerHTML = 'Удалить анкету';
                            button.style.background = '#b00020';
                        }, 3000);
                    }
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
                    <form action="/delete/{{ profile.id }}" method="post" id="deleteForm2">
                        <button type="button" class="modern-btn delete-btn" style="background: #b00020;" onclick="confirmDelete(this, 'deleteForm2')">Удалить анкету</button>
                    </form>
                {% endif %}
                <a href="/visitors" class="back-btn">← Назад к посетителям</a>
            </div>
        </body>
        </html>
    ''', profile=profile, is_owner=is_owner, navbar=navbar, get_photo_url=get_photo_url,
                                  get_starry_night_css=get_starry_night_css)


@app.route('/like/<string:id>', methods=['POST'])
@require_profile()
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
@require_profile()
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
@require_profile()
def my_matches():
    user_id = request.cookies.get('user_id')
    # Получаем метчи из базы данных
    matches = Match.query.filter(
        (Match.user1_id == user_id) | (Match.user2_id == user_id)
    ).all()

    # Отмечаем метчи как просмотренные
    current_time = datetime.utcnow()
    for match in matches:
        if match.user1_id == user_id and match.user1_viewed_at is None:
            match.user1_viewed_at = current_time
        elif match.user2_id == user_id and match.user2_viewed_at is None:
            match.user2_viewed_at = current_time
    db.session.commit()

    matched_ids = set()
    for match in matches:
        if match.user1_id == user_id:
            matched_ids.add(match.user2_id)
        else:
            matched_ids.add(match.user1_id)

    matched_profiles = [Profile.query.get(mid) for mid in matched_ids if Profile.query.get(mid)]
    navbar = render_navbar(user_id, active='matches', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
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
            <h1 style="text-align: center;">Мои мэтчи</h1>
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
@require_profile()
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

    # Добавляем всех пользователей из метчей из базы данных
    matches = Match.query.filter(
        (Match.user1_id == user_id) | (Match.user2_id == user_id)
    ).all()

    for match in matches:
        if match.user1_id == user_id:
            chat_partners.add(match.user2_id)
        else:
            chat_partners.add(match.user1_id)

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
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
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
            <h1 style="text-align: center;">Мои сообщения</h1>
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
@require_profile()
def chat(other_user_id):
    user_id = request.cookies.get('user_id')
    # Проверяем метчи в базе данных
    match_exists = Match.query.filter(
        ((Match.user1_id == user_id) & (Match.user2_id == other_user_id)) |
        ((Match.user1_id == other_user_id) & (Match.user2_id == user_id))
    ).first()

    if not match_exists:
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
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
            <title>Чат</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 600px; margin: 0 auto; padding: 20px; }
                .chat-header {
                    background: #030202;
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
                    color: #fff;
                }
                .chat-info p {
                    margin: 5px 0 0 0;
                    color: #ccc;
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
                    background: #030202; 
                    margin-right: auto; 
                    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
                    color: #fff;
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
                    background: #030202;
                    color: #fff;
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
                    background: #030202;
                    border-radius: 15px;
                    padding: 10px 15px;
                    margin: 10px;
                    font-size: 0.9em;
                    color: #fff;
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

                // Переменные для звука
                let chatAudioContext = null;
                let chatUserInteracted = false;

                // Инициализация аудио для чата
                function initChatAudio() {
                    try {
                        chatAudioContext = new (window.AudioContext || window.webkitAudioContext)();
                        console.log('✅ Аудио контекст инициализирован в чате');
                    } catch (error) {
                        console.log('⚠️ Аудио не поддерживается в чате:', error.message);
                    }
                }

                // Функция воспроизведения звука колокольчика
                function playNotificationSound() {
                    // Проверяем настройки пользователя перед воспроизведением
                    fetch('/api/get_settings')
                        .then(response => response.json())
                        .then(settings => {
                            if (!settings.sound_notifications) {
                                console.log('🔕 Звук отключен в настройках');
                                return;
                            }

                            if (!chatUserInteracted) {
                                chatUserInteracted = true;
                            }

                            try {
                                if (!chatAudioContext) {
                                    initChatAudio();
                                }

                                if (chatAudioContext && chatAudioContext.state === 'suspended') {
                                    chatAudioContext.resume();
                                }

                                const oscillator = chatAudioContext.createOscillator();
                                const gainNode = chatAudioContext.createGain();

                                // Классический звук колокольчика
                                oscillator.type = 'sine';
                                oscillator.frequency.setValueAtTime(800, chatAudioContext.currentTime); // 800 Гц
                                oscillator.frequency.setValueAtTime(600, chatAudioContext.currentTime + 0.1); // 600 Гц через 0.1 сек
                                oscillator.frequency.setValueAtTime(1000, chatAudioContext.currentTime + 0.2); // 1000 Гц через 0.2 сек
                                oscillator.frequency.setValueAtTime(400, chatAudioContext.currentTime + 0.3); // 400 Гц через 0.3 сек

                                gainNode.gain.setValueAtTime(0.3, chatAudioContext.currentTime); // Громкость 30%
                                gainNode.gain.exponentialRampToValueAtTime(0.01, chatAudioContext.currentTime + 0.5);

                                oscillator.connect(gainNode);
                                gainNode.connect(chatAudioContext.destination);

                                oscillator.start(chatAudioContext.currentTime);
                                oscillator.stop(chatAudioContext.currentTime + 0.5); // Длительность 0.5 секунды

                                console.log('🔔 Звук колокольчика воспроизведен при новом сообщении');

                            } catch (error) {
                                console.error('❌ Ошибка воспроизведения звука:', error);
                            }
                        })
                        .catch(error => {
                            console.error('❌ Ошибка получения настроек:', error);
                        });
                }

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

                    // Звук теперь воспроизводится только при обновлении счетчиков в навигации
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

                // Функция обновления счетчиков в навбаре (упрощенная версия)
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
                                        // Звук теперь воспроизводится только при обновлении счетчиков в навигации
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
                        // Звук теперь воспроизводится только при обновлении счетчиков в навигации
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

                // Отмечаем взаимодействие пользователя для активации аудио
                document.addEventListener('click', () => {
                    chatUserInteracted = true;
                    if (chatAudioContext && chatAudioContext.state === 'suspended') {
                        chatAudioContext.resume();
                    }
                });
            </script>
        </body>
        </html>
    ''', other_profile=other_profile, user_id=user_id, chat_key=chat_key, navbar=navbar, get_photo_url=get_photo_url,
                                  messages_db=messages_db, get_starry_night_css=get_starry_night_css)


@app.route('/chat_history/<string:other_user_id>')
@require_profile()
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
    # Эта функция больше не используется, так как метчи создаются напрямую в toggle_like
    # Оставляем для совместимости, но она не выполняет никаких действий
    pass


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


@app.route('/api/profile-lifetime', methods=['GET'])
def api_profile_lifetime():
    """
    API endpoint для получения оставшегося времени жизни анкеты
    """
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return jsonify({'error': 'No user ID'}), 400

        remaining_time = get_profile_lifetime_remaining(user_id)
        return jsonify({
            'success': True,
            'remaining_time': remaining_time,
            'user_id': user_id
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


@app.route('/api/update_settings', methods=['POST'])
@require_profile()
def api_update_settings():
    """API для обновления настроек пользователя"""
    user_id = request.cookies.get('user_id')
    data = request.get_json()

    if not data or 'sound_notifications' not in data:
        return jsonify({"error": "Неверные данные"}), 400

    sound_enabled = data['sound_notifications']
    success = update_user_settings(user_id, sound_enabled)

    if success:
        return jsonify({"success": True, "sound_notifications": sound_enabled})
    else:
        return jsonify({"error": "Ошибка обновления настроек"}), 500


@app.route('/api/get_settings')
@require_profile()
def api_get_settings():
    """API для получения настроек пользователя"""
    user_id = request.cookies.get('user_id')
    settings = get_user_settings(user_id)
    return jsonify(settings)


@app.route('/settings')
@require_profile()
def settings():
    user_id = request.cookies.get('user_id')
    navbar = render_navbar(user_id, active='settings', unread_messages=get_unread_messages_count(user_id),
                           unread_likes=get_unread_likes_count(user_id),
                           unread_matches=get_unread_matches_count(user_id))
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
            <title>Настройки</title>
            <style>
                {{ get_starry_night_css()|safe }}
                body { max-width: 500px; margin: 0 auto; padding: 20px; }
                h1 { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                    text-align: center;
                }
                .settings-card {
                    background: #030202;
                    border-radius: 15px;
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                    padding: 25px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    color: #fff;
                }
                .setting-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 15px 0;
                    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
                }
                .setting-item:last-child {
                    border-bottom: none;
                }
                .setting-label {
                    font-size: 1.1em;
                    color: #fff;
                }
                .bell-button {
                    background: #ff6b6b;
                    color: #fff;
                    border: none;
                    padding: 15px 20px;
                    border-radius: 10px;
                    cursor: pointer;
                    font-size: 1.2em;
                    transition: all 0.3s ease;
                }
                .bell-button:hover {
                    background: #ff5252;
                    transform: scale(1.05);
                }
                .bell-button:active {
                    transform: scale(0.95);
                }
                .setting-description {
                    font-size: 0.9em;
                    color: #ccc;
                    margin-top: 5px;
                }
            </style>
        </head>
        <body>
            {{ navbar|safe }}
            <h1>⚙️ Настройки</h1>
            <div class="settings-card">
                <div class="setting-item">
                    <div>
                        <div class="setting-label">🔔 Звуковые уведомления</div>
                        <div class="setting-description">Включить/выключить звук при получении сообщений</div>
                    </div>
                    <button id="sound-toggle" class="bell-button" onclick="toggleSound()">🔔</button>
                </div>
            </div>

            <script>
                let audioContext = null;
                let userInteracted = false;
                let soundEnabled = true;

                // Загружаем настройки при загрузке страницы
                window.addEventListener('load', function() {
                    loadSettings();
                });

                // Загрузка настроек
                function loadSettings() {
                    fetch('/api/get_settings')
                        .then(response => response.json())
                        .then(settings => {
                            soundEnabled = settings.sound_notifications;
                            updateBellAppearance();
                            console.log('📋 Настройки загружены:', settings);
                        })
                        .catch(error => {
                            console.error('❌ Ошибка загрузки настроек:', error);
                        });
                }

                // Обновление внешнего вида колокольчика
                function updateBellAppearance() {
                    const bellButton = document.getElementById('sound-toggle');
                    if (soundEnabled) {
                        bellButton.textContent = '🔔';
                        bellButton.style.filter = 'none';
                        bellButton.style.background = '#ff6b6b';
                    } else {
                        bellButton.textContent = '🔕';
                        bellButton.style.filter = 'grayscale(100%)';
                        bellButton.style.background = '#666';
                    }
                }

                // Переключение звука
                function toggleSound() {
                    soundEnabled = !soundEnabled;

                    // Обновляем внешний вид
                    updateBellAppearance();

                    // Сохраняем настройки
                    fetch('/api/update_settings', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            sound_notifications: soundEnabled
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('✅ Настройки сохранены:', data);
                            // Воспроизводим звук только если включен
                            if (soundEnabled) {
                                playBellSound();
                            }
                        } else {
                            console.error('❌ Ошибка сохранения настроек:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('❌ Ошибка сохранения настроек:', error);
                    });
                }

                // Инициализация аудио
                function initAudio() {
                    try {
                        audioContext = new (window.AudioContext || window.webkitAudioContext)();
                        console.log('✅ Аудио контекст инициализирован в настройках');
                    } catch (error) {
                        console.log('⚠️ Аудио не поддерживается в настройках:', error.message);
                    }
                }

                // Функция воспроизведения классического звука колокольчика
                function playBellSound() {
                    if (!userInteracted) {
                        userInteracted = true;
                    }

                    try {
                        if (!audioContext) {
                            initAudio();
                        }

                        if (audioContext && audioContext.state === 'suspended') {
                            audioContext.resume();
                        }

                        const oscillator = audioContext.createOscillator();
                        const gainNode = audioContext.createGain();

                        // Классический звук колокольчика
                        oscillator.type = 'sine';
                        oscillator.frequency.setValueAtTime(800, audioContext.currentTime); // 800 Гц
                        oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1); // 600 Гц через 0.1 сек
                        oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.2); // 1000 Гц через 0.2 сек
                        oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.3); // 400 Гц через 0.3 сек

                        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime); // Громкость 30%
                        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);

                        oscillator.connect(gainNode);
                        gainNode.connect(audioContext.destination);

                        oscillator.start(audioContext.currentTime);
                        oscillator.stop(audioContext.currentTime + 0.5); // Длительность 0.5 секунды

                        console.log('🔔 Классический звук колокольчика воспроизведен');

                    } catch (error) {
                        console.error('❌ Ошибка воспроизведения звука:', error);
                    }
                }

                // Отмечаем взаимодействие пользователя
                document.addEventListener('click', () => {
                    userInteracted = true;
                    if (audioContext && audioContext.state === 'suspended') {
                        audioContext.resume();
                    }
                });
            </script>
        </body>
        </html>
    ''', navbar=navbar, get_starry_night_css=get_starry_night_css)


def cleanup_expired_profiles():
    """
    Удаляет анкеты, которые старше PROFILE_LIFETIME_HOURS часов
    """
    try:
        from datetime import timedelta
        from datetime import datetime, timezone, timedelta
        
        current_time = datetime.now(timezone.utc)
        cutoff_time = current_time - timedelta(hours=PROFILE_LIFETIME_HOURS)
        
        print(f"⏰ ДИАГНОСТИКА УДАЛЕНИЯ АНКЕТ:")
        print(f"   - Используется время жизни: {PROFILE_LIFETIME_HOURS} часов")
        print(f"   - Текущее время UTC: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   - Граница удаления (cutoff): {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   - Анкеты, созданные ДО {cutoff_time.strftime('%Y-%m-%d %H:%M:%S')} будут удалены")

        # Находим просроченные анкеты
        # Получаем все анкеты и фильтруем вручную для корректной работы с timezone
        all_profiles = Profile.query.all()
        expired_profiles = []

        print(f"🔍 Проверяем {len(all_profiles)} анкет(ы):")
        for profile in all_profiles:
            created_at = profile.created_at
            # Если created_at без timezone, добавляем UTC
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            age_hours = (current_time - created_at).total_seconds() / 3600
            if created_at < cutoff_time:
                expired_profiles.append(profile)
                print(f"   ❌ {profile.name} ({profile.id[:8]}...): создана {created_at.strftime('%Y-%m-%d %H:%M:%S')}, возраст {age_hours:.2f}ч - УДАЛИТЬ")
            else:
                print(f"   ✅ {profile.name} ({profile.id[:8]}...): создана {created_at.strftime('%Y-%m-%d %H:%M:%S')}, возраст {age_hours:.2f}ч - ОК")

        print(f"🔍 Найдено {len(expired_profiles)} просроченных анкет для удаления")

        deleted_count = 0
        for profile in expired_profiles:
            print(f"🗑️ Удаляем анкету {profile.id} (создана: {profile.created_at})")

            # Удаляем ВСЕ связанные записи
            # 1. Удаляем лайки (где пользователь лайкал других)
            likes_sent = Like.query.filter_by(user_id=profile.id).all()
            for like in likes_sent:
                db.session.delete(like)
            print(f"  🗑️ Удалено лайков отправленных: {len(likes_sent)}")

            # 2. Удаляем лайки (где лайкали этого пользователя)
            likes_received = Like.query.filter_by(liked_id=profile.id).all()
            for like in likes_received:
                db.session.delete(like)
            print(f"  🗑️ Удалено лайков полученных: {len(likes_received)}")

            # 3. Удаляем сообщения
            messages = Message.query.filter(
                (Message.chat_key.contains(profile.id))
            ).all()
            for message in messages:
                db.session.delete(message)
            print(f"  🗑️ Удалено сообщений: {len(messages)}")

            # 4. Удаляем матчи (где пользователь участвует)
            matches = Match.query.filter(
                (Match.user1_id == profile.id) | (Match.user2_id == profile.id)
            ).all()
            for match in matches:
                db.session.delete(match)
            print(f"  🗑️ Удалено матчей: {len(matches)}")

            # 5. Удаляем фото файл
            if profile.photo:
                try:
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], profile.photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                        print(f"  🗑️ Удален файл фото: {profile.photo}")
                except Exception as e:
                    print(f"  ❌ Ошибка удаления файла {profile.photo}: {e}")

            # 6. Удаляем саму анкету
            db.session.delete(profile)
            deleted_count += 1
            print(f"  ✅ Анкета {profile.id} полностью удалена")

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


def cleanup_expired_pending_profiles():
    """
    Удаляет временные анкеты (PendingProfile), которые старше PENDING_PROFILE_LIFETIME_HOURS часов
    """
    try:
        from datetime import datetime, timezone, timedelta
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=PENDING_PROFILE_LIFETIME_HOURS)

        # Находим просроченные временные анкеты
        all_pending = PendingProfile.query.all()
        expired_pending = []

        for pending in all_pending:
            created_at = pending.created_at
            # Если created_at без timezone, добавляем UTC
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)

            if created_at < cutoff_time:
                expired_pending.append(pending)

        print(f"🔍 Найдено {len(expired_pending)} просроченных временных анкет для удаления")

        deleted_count = 0
        for pending in expired_pending:
            print(f"🗑️ Удаляем временную анкету {pending.id} (создана: {pending.created_at})")

            # Удаляем фото
            try:
                if pending.photo:
                    photo_path = os.path.join(app.config['UPLOAD_FOLDER'], pending.photo)
                    if os.path.exists(photo_path):
                        os.remove(photo_path)
                        print(f"  🗑️ Фото удалено: {pending.photo}")
            except Exception as e:
                print(f"  ⚠️ Ошибка удаления фото: {e}")

            # Удаляем временную анкету
            db.session.delete(pending)
            deleted_count += 1

        db.session.commit()

        if deleted_count > 0:
            print(f"✅ Удалено {deleted_count} просроченных временных анкет")
        else:
            print("✅ Просроченных временных анкет не найдено")

        return deleted_count
    except Exception as e:
        print(f"❌ Ошибка при очистке временных анкет: {e}")
        db.session.rollback()
        return 0


# ============================================================================
# МАРШРУТЫ ОПЛАТЫ ЮKASSA
# ============================================================================

@app.route('/payment')
def payment():
    """Страница оплаты создания профиля"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return redirect(url_for('home'))

    # Проверяем, есть ли уже оплаченный профиль
    profile = Profile.query.get(user_id)
    if profile and profile.is_paid:
        return redirect(url_for('my_profile'))

    # Проверяем, есть ли временная анкета (до оплаты)
    pending = PendingProfile.query.get(user_id)
    if not pending:
        return redirect(url_for('create_profile'))

    # Дополнительная проверка безопасности: проверяем, что IP-адрес совпадает
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    if pending.creation_ip and pending.creation_ip != client_ip:
        return redirect(url_for('home'))

    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Оплата профиля - Кафе знакомств</title>
        <style>
            {get_starry_night_css()}
            body {{
                text-align: center;
                padding: 20px;
                font-family: Arial, sans-serif;
            }}
            .payment-container {{
                max-width: 500px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .price {{
                font-size: 2em;
                color: #a709b5;
                font-weight: bold;
                margin: 20px 0;
            }}
            .payment-btn {{
                background: #a709b5;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 25px;
                font-size: 1.2em;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
                transition: all 0.3s ease;
            }}
            .payment-btn:hover {{
                background: #8a077a;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(167, 9, 181, 0.4);
            }}
            .test-mode {{
                background: #ff9800;
                color: white;
                padding: 10px;
                border-radius: 10px;
                margin: 20px 0;
                font-weight: bold;
            }}
            .back-btn {{
                background: #666;
                color: white;
                padding: 10px 20px;
                border: none;
                border-radius: 20px;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="payment-container">
            <h1>💳 Оплата профиля</h1>
            <p>Для активации вашего профиля необходимо произвести оплату</p>
            <div class="price">{PROFILE_CREATION_PRICE} руб.</div>

            {"<div class='test-mode'>🧪 ТЕСТОВЫЙ РЕЖИМ - платежи не реальные</div>" if YOOKASSA_TEST_MODE else ""}

            <button class="payment-btn" onclick="createPayment()">
                Оплатить картой
            </button>

            <br>
            <a href="/edit_pending_profile" class="back-btn">← Вернуться к анкете</a>
        </div>

        <script>
        function createPayment() {{
            const btn = document.querySelector('.payment-btn');
            btn.textContent = 'Создаю платеж...';
            btn.disabled = true;

            fetch('/payment/create', {{
                method: 'POST',
                headers: {{
                    'Content-Type': 'application/json',
                }},
                body: JSON.stringify({{
                    user_id: '{user_id}'
                }})
            }})
            .then(response => response.json())
            .then(data => {{
                if (data.success && data.payment_url) {{
                    window.location.href = data.payment_url;
                }} else {{
                    alert('Ошибка создания платежа: ' + (data.error || 'Неизвестная ошибка'));
                    btn.textContent = 'Оплатить картой';
                    btn.disabled = false;
                }}
            }})
            .catch(error => {{
                console.error('Ошибка:', error);
                alert('Ошибка создания платежа');
                btn.textContent = 'Оплатить картой';
                btn.disabled = false;
            }});
        }}
        </script>
    </body>
    </html>
    '''


@app.route('/payment/create', methods=['POST'])
def create_payment():
    """Создание платежа через ЮKassa"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')

        if not user_id:
            return jsonify({'success': False, 'error': 'Отсутствует user_id'})

        # Проверяем наличие временной анкеты (до оплаты)
        pending_profile = PendingProfile.query.get(user_id)
        if not pending_profile:
            return jsonify({'success': False, 'error': 'Временная анкета не найдена'})

        # Проверяем, не оплачен ли уже профиль
        existing_profile = Profile.query.get(user_id)
        if existing_profile and existing_profile.is_paid:
            return jsonify({'success': False, 'error': 'Профиль уже оплачен'})

        # Создаем платеж через ЮKassa
        payment_result = create_yookassa_payment(
            user_id=user_id,
            amount=PROFILE_CREATION_PRICE,
            description="Создание профиля в приложении знакомств"
        )

        if payment_result['success']:
            return jsonify({
                'success': True,
                'payment_url': payment_result['payment_url']
            })
        else:
            return jsonify({
                'success': False,
                'error': payment_result.get('error', 'Ошибка создания платежа')
            })

    except Exception as e:
        print(f"❌ Ошибка создания платежа: {e}")
        return jsonify({'success': False, 'error': 'Внутренняя ошибка сервера'})


@app.route('/payment/test-success')
def payment_test_success():
    """Тестовая страница успешной оплаты"""
    payment_id = request.args.get('payment_id')

    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Тестовая оплата успешна</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; padding: 50px; }}
            .success {{ color: green; font-size: 24px; }}
            .test-mode {{ background: #fff3cd; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="success">✅ Платеж успешно выполнен!</div>
        <div class="test-mode">
            <h3>🧪 ТЕСТОВЫЙ РЕЖИМ</h3>
            <p>Это тестовая оплата - реальные деньги не списывались</p>
            <p><strong>ID платежа:</strong> {payment_id}</p>
        </div>
        <p><a href="/">← Вернуться на главную</a></p>
        <p><a href="/admin/payments">👁️ Посмотреть в админ панели</a></p>
    </body>
    </html>
    '''


@app.route('/payment/success')
def payment_success():
    """Страница успешной оплаты"""
    payment_id = request.args.get('payment_id')
    user_id = request.args.get('user_id')

    if user_id:
        # Создаем настоящую анкету из временной после успешной оплаты
        try:
            print(f"🔄 Обрабатываем оплату для пользователя: {user_id}")

            # Проверяем, есть ли уже оплаченный профиль
            profile = Profile.query.get(user_id)
            if profile and profile.is_paid:
                print(f"✅ Профиль {user_id} уже оплачен и существует")
            else:
                # Получаем временную анкету
                pending = PendingProfile.query.get(user_id)
                if pending:
                    print(f"📝 Найдена временная анкета для {user_id}, создаем постоянную...")

                    # Удаляем старый профиль если он есть (но не оплачен)
                    if profile:
                        print(f"🗑️ Удаляем старый неоплаченный профиль {user_id}")
                        db.session.delete(profile)

                    # Создаем настоящую анкету из временной
                    new_profile = Profile(
                        id=pending.id,
                        name=pending.name,
                        age=pending.age,
                        gender=pending.gender,
                        hobbies=pending.hobbies,
                        goal=pending.goal,
                        city=pending.city,
                        venue=pending.venue,
                        photo=pending.photo,
                        likes=0,
                        latitude=pending.latitude,
                        longitude=pending.longitude,
                        creation_ip=pending.creation_ip,
                        is_paid=True,
                        payment_date=datetime.utcnow(),
                        created_at=datetime.utcnow()  # Таймер запускается СЕЙЧАС после оплаты!
                    )
                    db.session.add(new_profile)
                    # Удаляем временную анкету
                    db.session.delete(pending)
                    db.session.commit()
                    print(f"✅ Профиль {user_id} создан после оплаты, таймер запущен!")
                    print(f"📊 Данные профиля: {new_profile.name}, {new_profile.age}, {new_profile.gender}")
                else:
                    print(f"⚠️ Временная анкета {user_id} не найдена")
                    print(f"🔍 Ищем все временные анкеты...")
                    all_pending = PendingProfile.query.all()
                    for p in all_pending:
                        print(f"   - Временная анкета: {p.id} ({p.name})")
        except Exception as e:
            print(f"❌ Ошибка создания профиля после оплаты: {e}")
            import traceback
            traceback.print_exc()
            db.session.rollback()

    if payment_id and user_id:
        # Проверяем статус платежа
        process_payment_completion(user_id, payment_id, 'succeeded')

    return '''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Оплата успешна - Кафе знакомств</title>
        <style>
            ''' + get_starry_night_css() + '''
            body {
                text-align: center;
                padding: 20px;
                font-family: Arial, sans-serif;
            }
            .success-container {
                max-width: 500px;
                margin: 0 auto;
                background: rgba(255, 255, 255, 0.95);
                padding: 30px;
                border-radius: 15px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                backdrop-filter: blur(10px);
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            .success-icon {
                font-size: 4em;
                color: #4CAF50;
                margin-bottom: 20px;
            }
            h1 {
                color: #333;
                margin-bottom: 20px;
            }
            .success-btn {
                background: #4CAF50;
                color: white;
                padding: 15px 30px;
                border: none;
                border-radius: 25px;
                font-size: 1.2em;
                cursor: pointer;
                text-decoration: none;
                display: inline-block;
                margin: 10px;
                transition: all 0.3s ease;
            }
            .success-btn:hover {
                background: #45a049;
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(76, 175, 80, 0.4);
            }
        </style>
    </head>
    <body>
        <div class="success-container">
            <div class="success-icon">✅</div>
            <h1>Оплата успешна!</h1>
            <p>Ваш профиль активирован и готов к использованию</p>
            <div style="margin-top: 30px;">
                <a href="/my_profile" class="success-btn" id="profile-link" style="font-size: 1.3em; padding: 18px 40px;">Перейти к профилю</a>
            </div>
            <p id="countdown" style="margin-top: 20px; color: #4CAF50; font-size: 1em;">
                Автоматический переход через <span id="timer">3</span> секунды...
            </p>
        </div>

        <script>
            // Устанавливаем cookie user_id и обновляем ссылку
            const urlParams = new URLSearchParams(window.location.search);
            const userId = urlParams.get('user_id');

            if (userId) {
                console.log('🆔 User ID из URL:', userId);

                // Сохраняем user_id в cookie
                document.cookie = 'user_id=' + userId + '; path=/; max-age=' + (365*24*60*60) + '; SameSite=Lax';
                console.log('🍪 Cookie установлен:', document.cookie);

                // Также сохраняем в localStorage для надежности
                try {
                    localStorage.setItem('dating_app_user_id', userId);
                    sessionStorage.setItem('dating_app_user_id', userId);
                    console.log('💾 Сохранено в localStorage и sessionStorage');
                } catch (e) {
                    console.warn('⚠️ Не удалось сохранить в localStorage:', e);
                }

                // Обновляем ссылку на профиль с user_id
                const profileLink = document.getElementById('profile-link');
                if (profileLink) {
                    profileLink.href = '/my_profile?user_id=' + userId;
                    console.log('🔗 Ссылка на профиль обновлена:', profileLink.href);
                }
            } else {
                console.warn('⚠️ User ID не найден в URL');
            }

            // Автоматическое перенаправление на профиль через 3 секунды
            let countdown = 3;
            const timerElement = document.getElementById('timer');
            const countdownElement = document.getElementById('countdown');

            const interval = setInterval(function() {
                countdown--;
                if (timerElement) {
                    timerElement.textContent = countdown;
                }

                if (countdown <= 0) {
                    clearInterval(interval);
                    if (countdownElement) {
                        countdownElement.innerHTML = 'Переходим к вашему профилю...';
                    }
                    // Принудительно перенаправляем на профиль пользователя
                    const profileLink = document.getElementById('profile-link');
                    const redirectUrl = profileLink ? profileLink.href : '/my_profile';
                    console.log('🚀 Автоматическое перенаправление на:', redirectUrl);
                    window.location.href = redirectUrl;
                }
            }, 1000);

            // Останавливаем автоматическое перенаправление при клике на кнопку
            document.querySelector('.success-btn').addEventListener('click', function() {
                clearInterval(interval);
                if (countdownElement) {
                    countdownElement.style.display = 'none';
                }
                console.log('👆 Клик по кнопке профиля, переход на:', this.href);
            });
        </script>
    </body>
    </html>
    '''


@app.route('/yookassa/webhook', methods=['POST'])
def yookassa_webhook():
    """Webhook для получения уведомлений от ЮKassa"""
    try:
        # Получаем данные от ЮKassa
        webhook_data = request.get_json()

        if not webhook_data:
            print("❌ Webhook: пустые данные")
            return jsonify({'status': 'error', 'message': 'Пустые данные'}), 400

        # Проверяем подпись (в тестовом режиме пропускаем)
        if not YOOKASSA_TEST_MODE:
            signature = request.headers.get('X-YooMoney-Signature')
            if not verify_yookassa_webhook(webhook_data, signature):
                print("❌ Webhook: неверная подпись")
                return jsonify({'status': 'error', 'message': 'Неверная подпись'}), 400

        # Обрабатываем уведомление
        event = webhook_data.get('event')
        payment_id = webhook_data.get('object', {}).get('id')

        if event == 'payment.succeeded' and payment_id:
            print(f"✅ Webhook: платеж {payment_id} успешен")
            process_payment_completion(user_id, payment_id, 'succeeded')
            return jsonify({'status': 'success'})
        elif event == 'payment.canceled' and payment_id:
            print(f"⚠️ Webhook: платеж {payment_id} отменен")
            return jsonify({'status': 'success'})
        else:
            print(f"ℹ️ Webhook: неизвестное событие {event}")
            return jsonify({'status': 'success'})

    except Exception as e:
        print(f"❌ Ошибка webhook: {e}")
        return jsonify({'status': 'error', 'message': 'Внутренняя ошибка'}), 500


def _generate_payment_rows(payments):
    """Генерирует HTML строки для таблицы платежей"""
    rows = []
    for p in payments:
        row = f'''
        <tr>
            <td>{p.id}</td>
            <td>{p.user_id}</td>
            <td>{p.amount} руб.</td>
            <td class="status-{p.status}">{p.status}</td>
            <td>{p.created_at.strftime('%d.%m.%Y %H:%M') if p.created_at else 'N/A'}</td>
            <td>{p.yookassa_payment_id or 'N/A'}</td>
        </tr>
        '''
        rows.append(row)
    return ''.join(rows)


@app.route('/admin/payments')
def admin_payments():
    """Админ-панель для просмотра платежей"""
    payments = Payment.query.order_by(Payment.created_at.desc()).limit(50).all()

    return f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Админ - Платежи</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f2f2f2; }}
            .status-pending {{ color: orange; }}
            .status-succeeded {{ color: green; }}
            .status-canceled {{ color: red; }}
        </style>
    </head>
    <body>
        <h1>Админ - Платежи</h1>
        <p><strong>Тестовый режим:</strong> {"Да" if YOOKASSA_TEST_MODE else "Нет"}</p>

        <table>
            <tr>
                <th>ID</th>
                <th>User ID</th>
                <th>Сумма</th>
                <th>Статус</th>
                <th>Создан</th>
                <th>ЮKassa ID</th>
            </tr>
            {_generate_payment_rows(payments)}
        </table>

        <p><a href="/">← На главную</a></p>
    </body>
    </html>
    '''


def periodic_cleanup():
    """
    Функция для периодической очистки просроченных анкет
    Запускается каждые 5 минут
    """
    while True:
        try:
            time.sleep(5 * 60)  # Ждем 5 минут
            with app.app_context():
                print("🔄 Запуск периодической очистки просроченных анкет...")
                print(f"⏰ Используемое время жизни ОПЛАЧЕННОЙ анкеты: {PROFILE_LIFETIME_HOURS} часов")
                print(f"⏰ Используемое время жизни ВРЕМЕННОЙ анкеты: {PENDING_PROFILE_LIFETIME_HOURS} часов")
                deleted_count = cleanup_expired_profiles()
                pending_deleted_count = cleanup_expired_pending_profiles()
                if deleted_count > 0:
                    print(f"✅ Периодическая очистка: удалено {deleted_count} оплаченных анкет")
                if pending_deleted_count > 0:
                    print(f"✅ Периодическая очистка: удалено {pending_deleted_count} временных анкет")
                if deleted_count == 0 and pending_deleted_count == 0:
                    print("✅ Периодическая очистка: просроченных анкет не найдено")
        except Exception as e:
            print(f"❌ Ошибка в периодической очистке: {e}")


@app.route('/debug/lifetime-settings')
def debug_lifetime_settings():
    """Диагностический endpoint для проверки настроек времени жизни анкет"""
    from datetime import datetime, timezone
    
    # Получаем все анкеты
    all_profiles = Profile.query.all()
    all_pending = PendingProfile.query.all()
    
    current_time = datetime.now(timezone.utc)
    cutoff_time_profile = current_time - timedelta(hours=PROFILE_LIFETIME_HOURS)
    cutoff_time_pending = current_time - timedelta(hours=PENDING_PROFILE_LIFETIME_HOURS)
    
    # Информация по каждой анкете
    profiles_info = []
    for p in all_profiles:
        created_at = p.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_hours = (current_time - created_at).total_seconds() / 3600
        remaining_hours = PROFILE_LIFETIME_HOURS - age_hours
        
        profiles_info.append({
            'id': p.id[:12] + '...',
            'name': p.name,
            'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'age_hours': f"{age_hours:.2f}",
            'remaining_hours': f"{remaining_hours:.2f}",
            'will_expire': created_at < cutoff_time_profile,
            'is_paid': p.is_paid
        })
    
    pending_info = []
    for p in all_pending:
        created_at = p.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)
        age_hours = (current_time - created_at).total_seconds() / 3600
        remaining_hours = PENDING_PROFILE_LIFETIME_HOURS - age_hours
        
        pending_info.append({
            'id': p.id[:12] + '...',
            'name': p.name,
            'created_at': created_at.strftime('%Y-%m-%d %H:%M:%S UTC'),
            'age_hours': f"{age_hours:.2f}",
            'remaining_hours': f"{remaining_hours:.2f}",
            'will_expire': created_at < cutoff_time_pending
        })
    
    # Генерируем HTML для таблицы оплаченных анкет
    profiles_table_html = ''
    if profiles_info:
        profiles_table_html = '<table><tr><th>ID</th><th>Имя</th><th>Создана</th><th>Возраст (ч)</th><th>Осталось (ч)</th><th>Оплачена</th><th>Статус</th></tr>'
        for p in profiles_info:
            expire_class = 'expire' if p['will_expire'] else 'ok'
            status_text = 'БУДЕТ УДАЛЕНА' if p['will_expire'] else 'АКТИВНА'
            paid_icon = '✅' if p['is_paid'] else '❌'
            profiles_table_html += f'<tr><td>{p["id"]}</td><td>{p["name"]}</td><td>{p["created_at"]}</td><td>{p["age_hours"]}</td><td class="{expire_class}">{p["remaining_hours"]}</td><td>{paid_icon}</td><td class="{expire_class}">{status_text}</td></tr>'
        profiles_table_html += '</table>'
    else:
        profiles_table_html = '<p>Нет оплаченных анкет</p>'
    
    # Генерируем HTML для таблицы временных анкет
    pending_table_html = ''
    if pending_info:
        pending_table_html = '<table><tr><th>ID</th><th>Имя</th><th>Создана</th><th>Возраст (ч)</th><th>Осталось (ч)</th><th>Статус</th></tr>'
        for p in pending_info:
            expire_class = 'expire' if p['will_expire'] else 'ok'
            status_text = 'БУДЕТ УДАЛЕНА' if p['will_expire'] else 'АКТИВНА'
            pending_table_html += f'<tr><td>{p["id"]}</td><td>{p["name"]}</td><td>{p["created_at"]}</td><td>{p["age_hours"]}</td><td class="{expire_class}">{p["remaining_hours"]}</td><td class="{expire_class}">{status_text}</td></tr>'
        pending_table_html += '</table>'
    else:
        pending_table_html = '<p>Нет временных анкет</p>'
    
    warning_html = '<div class="warning">⚠️ ВНИМАНИЕ: Комментарии в коде не соответствуют значениям! Проверьте строки 35-36 в app.py</div>' if PROFILE_LIFETIME_HOURS == 10 else ''
    
    html = f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔧 Диагностика времени жизни анкет</title>
        <style>
            body {{
                font-family: monospace;
                padding: 20px;
                background: #1a1a1a;
                color: #00ff00;
            }}
            .section {{
                background: #2a2a2a;
                padding: 15px;
                margin: 15px 0;
                border-radius: 8px;
                border: 2px solid #00ff00;
            }}
            h1, h2 {{
                color: #00ff00;
                text-shadow: 0 0 10px #00ff00;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
                border: 1px solid #00ff00;
            }}
            th {{
                background: #003300;
            }}
            .expire {{
                color: #ff0000;
                font-weight: bold;
            }}
            .ok {{
                color: #00ff00;
            }}
            .warning {{
                background: #ff9800;
                color: #000;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <h1>🔧 ДИАГНОСТИКА ВРЕМЕНИ ЖИЗНИ АНКЕТ</h1>
        
        <div class="section">
            <h2>⚙️ Текущие настройки</h2>
            <p><strong>Время жизни ОПЛАЧЕННОЙ анкеты:</strong> {PROFILE_LIFETIME_HOURS} часов</p>
            <p><strong>Время жизни ВРЕМЕННОЙ анкеты:</strong> {PENDING_PROFILE_LIFETIME_HOURS} часов</p>
            <p><strong>Текущее время UTC:</strong> {current_time.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Граница удаления оплаченных:</strong> {cutoff_time_profile.strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Граница удаления временных:</strong> {cutoff_time_pending.strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
        
        {warning_html}
        
        <div class="section">
            <h2>📋 Оплаченные анкеты ({len(profiles_info)})</h2>
            {profiles_table_html}
        </div>
        
        <div class="section">
            <h2>⏳ Временные анкеты ({len(pending_info)})</h2>
            {pending_table_html}
        </div>
        
        <div class="section">
            <h2>📝 Инструкции</h2>
            <ol>
                <li>Чтобы изменить время жизни анкеты, отредактируйте строки 36-37 в app.py</li>
                <li><strong>ОБЯЗАТЕЛЬНО ПЕРЕЗАПУСТИТЕ СЕРВЕР</strong> после изменения</li>
                <li>Проверьте, что значения PROFILE_LIFETIME_HOURS и комментарии совпадают</li>
                <li>Обновите эту страницу, чтобы увидеть новые значения</li>
                <li>Периодическая очистка запускается каждые 5 минут</li>
            </ol>
        </div>
        
        <div class="section">
            <p><a href="/" style="color: #00ff00;">← Вернуться на главную</a></p>
            <p><a href="/debug/lifetime-settings" style="color: #00ff00;">🔄 Обновить данные</a></p>
        </div>
        
        <script>
            // Автообновление каждые 10 секунд
            setTimeout(() => location.reload(), 10000);
        </script>
    </body>
    </html>
    '''
    
    return html


@app.route('/debug/likes-and-matches')
def debug_likes_and_matches():
    """Диагностический endpoint для проверки лайков и метчей"""
    user_id = request.cookies.get('user_id')
    
    if not user_id:
        return "⚠️ Нет user_id в cookie. Сначала создайте профиль."
    
    # Получаем профиль текущего пользователя
    current_profile = Profile.query.get(user_id)
    if not current_profile:
        return "⚠️ Профиль не найден"
    
    # Получаем все лайки ОТ текущего пользователя
    my_likes = Like.query.filter_by(user_id=user_id).all()
    
    # Получаем все лайки К текущему пользователю
    likes_to_me = Like.query.filter_by(liked_id=user_id).all()
    
    # Получаем все метчи
    all_matches = Match.query.filter(
        (Match.user1_id == user_id) | (Match.user2_id == user_id)
    ).all()
    
    # Получаем liked_ids (как на странице visitors)
    liked_ids = set(l.liked_id for l in my_likes)
    for match in all_matches:
        if match.user1_id == user_id:
            liked_ids.add(match.user2_id)
        else:
            liked_ids.add(match.user1_id)
    
    # Все профили
    all_profiles = Profile.query.filter(Profile.id != user_id).all()
    
    html = f'''
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🔍 Диагностика лайков и метчей</title>
        <style>
            body {{
                font-family: monospace;
                padding: 20px;
                background: #1a1a1a;
                color: #00ff00;
                max-width: 1200px;
                margin: 0 auto;
            }}
            .section {{
                background: #2a2a2a;
                padding: 15px;
                margin: 15px 0;
                border-radius: 8px;
                border: 2px solid #00ff00;
            }}
            h1, h2 {{
                color: #00ff00;
                text-shadow: 0 0 10px #00ff00;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 10px 0;
            }}
            th, td {{
                padding: 8px;
                text-align: left;
                border: 1px solid #00ff00;
            }}
            th {{
                background: #003300;
            }}
            .red {{
                color: #ff0000;
                font-weight: bold;
            }}
            .green {{
                color: #00ff00;
            }}
            .yellow {{
                color: #ffff00;
            }}
            .info-box {{
                background: #003366;
                padding: 10px;
                border-radius: 5px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <h1>🔍 ДИАГНОСТИКА ЛАЙКОВ И МЕТЧЕЙ</h1>
        
        <div class="section">
            <h2>👤 Текущий пользователь</h2>
            <p><strong>ID:</strong> {user_id[:12]}...</p>
            <p><strong>Имя:</strong> {current_profile.name}</p>
        </div>
        
        <div class="section">
            <h2>❤️ Мои лайки (я лайкнул)</h2>
    '''
    
    if my_likes:
        html += '<table><tr><th>ID получателя</th><th>Имя получателя</th><th>Like ID</th></tr>'
        for like in my_likes:
            liked_profile = Profile.query.get(like.liked_id)
            name = liked_profile.name if liked_profile else 'Удален'
            html += f'<tr><td>{like.liked_id[:12]}...</td><td>{name}</td><td>{like.id}</td></tr>'
        html += f'</table><p><strong>Всего:</strong> {len(my_likes)}</p>'
    else:
        html += '<p class="yellow">Вы еще никого не лайкнули</p>'
    
    html += '''
        </div>
        
        <div class="section">
            <h2>💖 Лайки мне (меня лайкнули)</h2>
    '''
    
    if likes_to_me:
        html += '<table><tr><th>ID отправителя</th><th>Имя отправителя</th><th>Like ID</th></tr>'
        for like in likes_to_me:
            sender_profile = Profile.query.get(like.user_id)
            name = sender_profile.name if sender_profile else 'Удален'
            html += f'<tr><td>{like.user_id[:12]}...</td><td>{name}</td><td>{like.id}</td></tr>'
        html += f'</table><p><strong>Всего:</strong> {len(likes_to_me)}</p>'
    else:
        html += '<p class="yellow">Вас еще никто не лайкнул</p>'
    
    html += '''
        </div>
        
        <div class="section">
            <h2>✨ Мои метчи</h2>
    '''
    
    if all_matches:
        html += '<table><tr><th>ID партнера</th><th>Имя партнера</th><th>Match ID</th></tr>'
        for match in all_matches:
            partner_id = match.user2_id if match.user1_id == user_id else match.user1_id
            partner_profile = Profile.query.get(partner_id)
            name = partner_profile.name if partner_profile else 'Удален'
            html += f'<tr><td>{partner_id[:12]}...</td><td>{name}</td><td>{match.id}</td></tr>'
        html += f'</table><p><strong>Всего:</strong> {len(all_matches)}</p>'
    else:
        html += '<p class="yellow">У вас пока нет метчей</p>'
    
    html += '''
        </div>
        
        <div class="section">
            <h2>👥 Все профили и их статус</h2>
            <div class="info-box">
                <p><strong>Логика отображения сердечка на странице /visitors:</strong></p>
                <p>Сердечко красное ❤️ если ID профиля есть в <code>liked_ids</code></p>
                <p><code>liked_ids</code> содержит: тех, кого я лайкнул + тех, с кем у меня метч</p>
            </div>
            <table>
                <tr>
                    <th>ID</th>
                    <th>Имя</th>
                    <th>Я лайкнул?</th>
                    <th>Есть метч?</th>
                    <th>В liked_ids?</th>
                    <th>Сердечко</th>
                </tr>
    '''
    
    my_likes_ids = [l.liked_id for l in my_likes]
    matches_ids = [(m.user2_id if m.user1_id == user_id else m.user1_id) for m in all_matches]
    
    for profile in all_profiles:
        i_liked = profile.id in my_likes_ids
        has_match = profile.id in matches_ids
        in_liked_ids = profile.id in liked_ids
        
        i_liked_class = 'green' if i_liked else 'red'
        i_liked_icon = '✅' if i_liked else '❌'
        
        match_class = 'green' if has_match else 'red'
        match_icon = '✅' if has_match else '❌'
        
        liked_class = 'green' if in_liked_ids else 'red'
        liked_icon = '✅' if in_liked_ids else '❌'
        
        heart = '❤️' if in_liked_ids else '🤍'
        
        html += f'''
                <tr>
                    <td>{profile.id[:12]}...</td>
                    <td>{profile.name}</td>
                    <td class="{i_liked_class}">{i_liked_icon}</td>
                    <td class="{match_class}">{match_icon}</td>
                    <td class="{liked_class}">{liked_icon}</td>
                    <td>{heart}</td>
                </tr>
        '''
    
    html += '''
            </table>
        </div>
        
        <div class="section">
            <h2>🔧 Что делать, если видите проблему</h2>
            <ol>
                <li>Проверьте таблицу "Мои лайки" - там должны быть только те, кого вы сами лайкнули</li>
                <li>Если там есть лайк, которого вы не ставили - это БАГ!</li>
                <li>Проверьте "Все профили" - сердечко должно быть красным только если "В liked_ids?" = ✅</li>
                <li>Если есть метч, но вы не лайкали - это СТРАННО, проверьте таблицу "Мои лайки"</li>
            </ol>
        </div>
        
        <div class="section">
            <p><a href="/visitors" style="color: #00ff00;">← Вернуться к посетителям</a></p>
            <p><a href="/debug/likes-and-matches" style="color: #00ff00;">🔄 Обновить данные</a></p>
        </div>
        
        <script>
            // Автообновление каждые 5 секунд
            setTimeout(() => location.reload(), 5000);
        </script>
    </body>
    </html>
    '''
    
    return html


@app.route('/test_create_and_pay')
def test_create_and_pay():
    return send_from_directory('.', 'test_create_and_pay.html')


@app.route('/test_payment_success_fix')
def test_payment_success_fix():
    return send_from_directory('.', 'test_payment_success_fix.html')


@app.route('/debug_create')
def debug_create():
    return send_from_directory('.', 'debug_create.html')


@app.route('/simple_create_test')
def simple_create_test():
    return send_from_directory('.', 'simple_create_test.html')


@app.route('/quick_create')
def quick_create():
    return send_from_directory('.', 'quick_create.html')


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Запускаем очистку просроченных анкет при старте сервера
        print("🧹 Запуск автоматической очистки просроченных анкет...")
        deleted_count = cleanup_expired_profiles()
        pending_deleted_count = cleanup_expired_pending_profiles()
        print(f"⏰ Время жизни оплаченной анкеты: {PROFILE_LIFETIME_HOURS} часов")
        print(f"⏰ Время жизни временной анкеты: {PENDING_PROFILE_LIFETIME_HOURS} часов")

        # Запускаем фоновую задачу для периодической очистки
        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()
        print("🔄 Запущена периодическая очистка анкет (каждые 5 минут)")

    socketio.run(app, host='0.0.0.0', port=5000
                 , debug=True, allow_unsafe_werkzeug=True)