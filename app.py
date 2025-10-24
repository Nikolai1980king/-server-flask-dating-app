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
import base64
import io
import qrcode
from PIL import Image

app = Flask(__name__)

def compress_image(image_file, max_size=(800, 800), quality=85, max_file_size=5*1024*1024):
    """
    Сжимает изображение до оптимального размера
    max_size: максимальные размеры (ширина, высота)
    quality: качество JPEG (1-100)
    max_file_size: максимальный размер файла в байтах (5MB)
    """
    try:
        # Открываем изображение
        img = Image.open(image_file)
        
        # Конвертируем в RGB если нужно (для PNG с прозрачностью)
        if img.mode in ('RGBA', 'LA', 'P'):
            # Создаем белый фон
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Получаем размеры
        original_width, original_height = img.size
        max_width, max_height = max_size
        
        # Вычисляем новые размеры с сохранением пропорций
        if original_width > max_width or original_height > max_height:
            ratio = min(max_width/original_width, max_height/original_height)
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            
            # Изменяем размер
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"📸 Изображение сжато: {original_width}x{original_height} → {new_width}x{new_height}")
        
        # Сохраняем в буфер с заданным качеством
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=quality, optimize=True)
        output.seek(0)
        
        # Проверяем размер файла
        file_size = len(output.getvalue())
        print(f"📊 Размер файла после сжатия: {file_size / 1024 / 1024:.2f} MB")
        
        # Если файл все еще слишком большой, уменьшаем качество
        if file_size > max_file_size:
            quality = max(50, int(quality * (max_file_size / file_size)))
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output.seek(0)
            print(f"🔧 Качество уменьшено до {quality}% для соответствия лимиту размера")
        
        return output
        
    except Exception as e:
        print(f"❌ Ошибка сжатия изображения: {e}")
        # Возвращаем оригинальный файл если сжатие не удалось
        image_file.seek(0)
        return image_file
# 🔐 БЕЗОПАСНЫЙ СЕКРЕТНЫЙ КЛЮЧ ДЛЯ ПРОДАКШЕНА
app.secret_key = os.environ.get('SECRET_KEY', 'yatuta-rf-2024-secure-key-change-in-production')
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True)

# 🔐 НАСТРОЙКИ БЕЗОПАСНОСТИ ДЛЯ СОВМЕСТИМОСТИ HTTP/HTTPS
# Настройки безопасности куки для совместимости
app.config['SESSION_COOKIE_SECURE'] = False  # False для совместимости HTTP/HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = False  # False для доступа JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Защита от CSRF
app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 часа

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
PROFILE_LIFETIME_HOURS = 24  # Время жизни ОПЛАЧЕННОЙ анкеты в часах (10 часов)
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

# Цена функции "Удивить" (один раз навсегда)
SURPRISE_FEATURE_PRICE = 10.00

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

        /* Стили для черно-белого режима */
        .grayscale-mode {
            filter: grayscale(100%);
            -webkit-filter: grayscale(100%);
            -moz-filter: grayscale(100%);
            -ms-filter: grayscale(100%);
            -o-filter: grayscale(100%);
        }

        .grayscale-mode * {
            filter: grayscale(100%);
            -webkit-filter: grayscale(100%);
            -moz-filter: grayscale(100%);
            -ms-filter: grayscale(100%);
            -o-filter: grayscale(100%);
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
    # Поле для оплаты функции "Удивить"
    surprise_feature_paid = db.Column(db.Boolean, default=False)
    surprise_feature_payment_date = db.Column(db.DateTime, nullable=True)
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


class SentJoke(db.Model):
    """Модель для хранения отправленных анекдотов (для отслеживания повторов)"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, nullable=False)  # Кто отправил
    receiver_id = db.Column(db.String, nullable=False)  # Кто получил
    joke_id = db.Column(db.Integer, nullable=False)  # ID анекдота из списка
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('sender_id', 'receiver_id', 'joke_id', name='unique_sent_joke'),)


class SentPuzzle(db.Model):
    """Модель для хранения отправленных головоломок (для отслеживания повторов)"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, nullable=False)  # Кто отправил
    receiver_id = db.Column(db.String, nullable=False)  # Кто получил
    puzzle_id = db.Column(db.Integer, nullable=False)  # ID головоломки из списка
    sent_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('sender_id', 'receiver_id', 'puzzle_id', name='unique_sent_puzzle'),)


class ChatPermission(db.Model):
    """Модель для отслеживания разрешений на общение после отправки сюрприза"""
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.String, nullable=False)  # Кто отправил сюрприз
    receiver_id = db.Column(db.String, nullable=False)  # Кто получил сюрприз
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class QRLoginToken(db.Model):
    """Модель для QR-код авторизации"""
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String, unique=True, nullable=False)  # Уникальный токен
    user_id = db.Column(db.String, nullable=False)  # ID пользователя
    expires_at = db.Column(db.DateTime, nullable=False)  # Время истечения
    used = db.Column(db.Boolean, default=False)  # Использован ли токен
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Удаляю in-memory структуру сообщений:
# messages = defaultdict(list)
notifications = defaultdict(list)


# ============================================================================
# QR-КОД АВТОРИЗАЦИЯ ДЛЯ ЯТУТА.РФ
# ============================================================================

def generate_qr_login_token(user_id):
    """Генерирует токен для QR-код входа"""
    token = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(minutes=10)  # Токен действует 10 минут

    # Удаляем старые токены этого пользователя
    QRLoginToken.query.filter_by(user_id=user_id).delete()

    # Создаем новый токен
    qr_token = QRLoginToken(
        token=token,
        user_id=user_id,
        expires_at=expires_at
    )
    db.session.add(qr_token)
    db.session.commit()

    return token


def cleanup_expired_qr_tokens():
    """Очищает просроченные QR-токены"""
    current_time = datetime.utcnow()
    expired_tokens = QRLoginToken.query.filter(QRLoginToken.expires_at < current_time).all()

    for token in expired_tokens:
        db.session.delete(token)

    db.session.commit()
    return len(expired_tokens)


def generate_google_search_url(query):
    """Генерирует URL для поиска в Google"""
    import urllib.parse
    encoded_query = urllib.parse.quote_plus(query)
    return f"https://www.google.com/search?q={encoded_query}"


def get_user_qr_url(user_id):
    """Генерирует QR-код URL, который ведет на главную страницу ятута.рф"""
    # Используем Punycode для лучшей совместимости с QR-сканерами
    return "https://xn--80a9aad2d.xn--p1ai"


def generate_qr_code_server_side(user_id):
    """Генерирует QR-код на сервере через наш endpoint"""
    import time
    # Генерируем изображение QR-кода через наш endpoint
    timestamp = int(time.time())  # Добавляем timestamp для принудительного обновления
    return f"https://ятута.рф/qr-image/{user_id}?v={timestamp}"


@app.route('/qr-image/<string:user_id>')
def qr_image(user_id):
    """Endpoint для генерации QR-кода изображения"""
    try:
        # Проверяем, существует ли пользователь
        profile = Profile.query.get(user_id)
        if not profile:
            return "Пользователь не найден", 404

        # Создаем URL для QR-кода
        qr_url = get_user_qr_url(user_id)

        # Генерируем QR-код локально
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,  # Высокая коррекция для логотипа
            box_size=10,
            border=4,
        )
        qr.add_data(qr_url)
        qr.make(fit=True)

        # Создаем изображение
        img = qr.make_image(fill_color="black", back_color="white")

        # Добавляем текст снизу
        img = add_text_below_qr(img)

        # Конвертируем в PNG
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        # Возвращаем изображение
        return make_response(img_buffer.getvalue(), 200, {
            'Content-Type': 'image/png',
            'Cache-Control': 'no-cache, no-store, must-revalidate'  # Отключаем кеширование
        })

    except Exception as e:
        print(f"Ошибка генерации QR-кода: {e}")
        # Возвращаем простой QR-код в случае ошибки
        qr_url = get_user_qr_url(user_id)
        return generate_simple_qr(qr_url)


def add_text_below_qr(qr_img):
    """Добавляет текст 'ятута.рф' снизу QR-кода на белом фоне"""
    try:
        from PIL import ImageDraw, ImageFont

        # Получаем размеры QR-кода
        qr_width, qr_height = qr_img.size

        # Размер текста (увеличиваем высоту)
        text_height = 60  # Увеличиваем высоту области для текста
        new_height = qr_height + text_height

        # Создаем новое изображение с дополнительным местом для текста
        new_img = Image.new('RGB', (qr_width, new_height), 'white')

        # Копируем QR-код в верхнюю часть
        new_img.paste(qr_img, (0, 0))

        # Создаем область для текста
        text_area = Image.new('RGB', (qr_width, text_height), 'white')
        draw = ImageDraw.Draw(text_area)

        # Текст
        text = "ятута.рф"
        font_size = 28  # Возвращаем размер для короткого текста

        # Добавляем подсказку
        browser_hint = "Откройте в Chrome"
        hint_font_size = 12

        # Пытаемся использовать системный шрифт
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size=font_size)
        except:
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Arial.ttf", size=font_size)
            except:
                font = ImageFont.load_default()

        # Получаем размеры текста
        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height_actual = bbox[3] - bbox[1]
        except:
            # Fallback для проблем с кодировкой
            text_width = len(text) * 16  # Увеличиваем для большего шрифта
            text_height_actual = 28

        # Смещаем текст вправо и поднимаем от края
        text_x = (qr_width - text_width) // 2  # Смещаем на 0px вправо
        text_y = (text_height - text_height_actual) // 2 - 20  # Поднимаем на 20px от центра

        print(f"🔧 Отладка: text_x={text_x}, text_y={text_y}, text_width={text_width}")

        # Рисуем основной текст
        try:
            draw.text((text_x, text_y), text, fill='black', font=font)
        except:
            # Если не получается с кириллицей, рисуем простой текст
            draw.text((text_x, text_y), "ятута.рф", fill='black', font=font)

        # Рисуем подсказку о браузере
        try:
            hint_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size=hint_font_size)
        except:
            hint_font = ImageFont.load_default()

        # Позиция подсказки (под основным текстом)
        hint_y = text_y + 35
        hint_x = (qr_width - len(browser_hint) * 6) // 2  # Примерное центрирование

        draw.text((hint_x, hint_y), browser_hint, fill='gray', font=hint_font)

        # Вставляем область с текстом в нижнюю часть
        new_img.paste(text_area, (0, qr_height))

        return new_img

    except Exception as e:
        print(f"Ошибка добавления текста: {e}")
        return qr_img  # Возвращаем оригинальный QR-код без текста


def generate_simple_qr(url):
    """Генерирует простой QR-код в случае ошибки"""
    # Создаем простой SVG QR-код
    svg_content = f'''
    <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
        <rect width="200" height="200" fill="white"/>
        <text x="100" y="100" text-anchor="middle" font-family="Arial" font-size="12" fill="black">
            QR-код недоступен
        </text>
        <text x="100" y="120" text-anchor="middle" font-family="Arial" font-size="8" fill="gray">
            Используйте ссылку
        </text>
    </svg>
    '''
    return make_response(svg_content, 200, {'Content-Type': 'image/svg+xml'})


read_likes = defaultdict(set)  # user_id -> set(profile_id)
new_matches = defaultdict(set)  # user_id -> set of new matched user_ids

# ============================================================================
# КОЛЛЕКЦИЯ АНЕКДОТОВ ПРО РЕСТОРАНЫ И КАФЕ
# ============================================================================
RESTAURANT_JOKES = [
    "Официант спрашивает посетителя:\n— Вам понравился наш фирменный суп?\n— Да, очень! Особенно когда закончился.",
    "В ресторане:\n— Официант, у вас есть лягушачьи лапки?\n— Нет, я просто так хромаю!",
    "Клиент в ресторане:\n— Официант, в моем супе муха!\n— Не волнуйтесь, она не съест много.",
    "— Официант, эта курица очень жесткая!\n— Странно, еще вчера она была такой нежной и пушистой.",
    "В ресторане посетитель долго изучает меню и говорит:\n— А можно мне все без лука?\n— Конечно! Что будете заказывать?\n— Вот этот лук.",
    "— Официант, что это за странный запах?\n— Это наше фирменное блюдо!\n— А что вы туда добавляете?\n— Фирму!",
    "Посетитель ресторана жалуется:\n— В вашем кофе плавает муха!\n— Так это же кофе по-вьетнамски — с тараканом бы было дороже!",
    "— Официант, это кофе или чай?\n— А какая разница?\n— Если это кофе, принесите мне чай. Если чай — принесите кофе.",
    "В ресторане:\n— У вас есть винная карта?\n— Да, конечно!\n— Отлично, тогда сыграем в дурака?",
    "Повар говорит официанту:\n— Если клиенты будут жаловаться на мой борщ, скажи, что это томатный суп!\n— А если на томатный суп?\n— Скажи, что это борщ!",
    "— Официант, принесите мне что-нибудь холодненькое!\n— Может быть, счет?",
    "Официант приносит заказ и говорит:\n— Будьте осторожны, тарелка горячая!\nКлиент трогает тарелку:\n— Да вполне терпимо.\n— Я же предупредил, что буду осторожен!",
    "— Официант, в моем супе волос!\n— Господи, а я целый час на кухне искал!",
    "В ресторане:\n— Это заведение работает круглосуточно?\n— Да!\n— Отлично, тогда приду завтра.",
    "Клиент спрашивает:\n— Официант, у вас есть блюда из курицы?\n— Конечно! У нас курица во всех видах!\n— Хорошо, тогда дайте мне ее в живом.",
    "— Сколько у вас стоит кофе?\n— 500 рублей.\n— А у соседей 100!\n— Так идите к соседям!\n— У них закончился.\n— Когда у нас закончится, тоже будет по 100!",
    "Официант приносит счет.\nКлиент:\n— Молодой человек, я попросил принести ЧЕК, а не ШОК!",
    "— Официант, а это мясо свежее?\n— Абсолютно! Еще вчера бегало по полю!\n— По какому?\n— По минному.",
    "Посетитель:\n— В вашем ресторане вчера у меня украли пальто.\n— Очень сожалеем! Вот ваш столик.\n— Это не мой столик.\n— Значит, и пальто не ваше.",
    "— Официант, это мясо индюка?\n— Да.\n— А почему на вкус как курица?\n— Мы не спрашивали индюка, кем он хочет быть!",
    "В кафе:\n— У вас есть Wi-Fi?\n— Есть.\n— А пароль?\n— Купитечтонибудь, слитно и маленькими буквами.",
    "Клиент в ресторане:\n— Официант, это морская или речная рыба?\n— Не знаю, она мне ничего не сказала.",
    "— Официант, принесите мне комплимент от шефа!\n— Пожалуйста! Шеф-повар сказал, что вы очень красивая.\n— Это все?\n— Он еще добавил, что вы похожи на его бывшую жену.",
    "В ресторане посетитель кричит:\n— Официант, у меня в супе таракан!\n— Тихо! А то все захотят!",
    "— Официант, это диетическое меню?\n— Да.\n— Странно, почему оно такое тяжелое?\n— Это чтобы сжечь калории, пока читаете!",
]

# ============================================================================
# КОЛЛЕКЦИЯ ГОЛОВОЛОМОК И ЗАДАЧ НА ЛОГИКУ (по типу Перельмана)
# ============================================================================
LOGIC_PUZZLES = [
    "📊 У отца шесть сыновей. Каждый сын имеет сестру.\n\nСколько всего детей у этого отца?",
    "🔢 Двое играли в шахматы 4 часа.\n\nСколько времени играл каждый?",
    "🕐 На столе лежат две монеты, в сумме они дают 3 рубля. Одна из них не 1 рубль.\n\nКакие это монеты?",
    "🚗 Человек ехал в город. По дороге он встретил 3 машины.\n\nСколько машин ехало в город?",
    "📐 У треугольника может быть два тупых угла?",
    "🏠 В одноэтажном доме все желтое: стены, двери, мебель.\n\nКакого цвета лестница?",
    "⚖️ На одной чаше весов кирпич, на другой - полкирпича и гиря 1 кг. Весы в равновесии.\n\nСколько весит кирпич?",
    "🔄 Позавчера Пете было 17 лет. В следующем году ему будет 20 лет.\n\nКак такое возможно?",
    "🚶 Мужчина шел под дождем. У него не было ни зонта, ни шляпы. Ни один волос на его голове не промок.\n\nПочему?",
    "🍎 В корзине 5 яблок. Как разделить их между 5 людьми так, чтобы одно яблоко осталось в корзине?",
    "⏱️ Что происходит с яйцом, которое падает в Красное море?",
    "🔢 Два отца и два сына съели на завтрак 3 яйца, причем каждому досталось по целому яйцу.\n\nКак это возможно?",
    "📏 Может ли дождь идти два дня подряд?",
    "🎯 В комнате горело 50 свечей, 20 из них задули.\n\nСколько свечей останется?",
    "🚂 Электричка едет на восток со скоростью 80 км/ч. Ветер дует с запада на восток со скоростью 20 км/ч.\n\nВ какую сторону летит дым?",
    "💰 У Марины было целое яблоко, две половинки и четыре четвертинки.\n\nСколько яблок было у Марины?",
    "🎨 Назовите пять дней недели, не называя их по названиям и числам.",
    "🔍 Что можно держать, не трогая руками?",
    "📖 Вы входите в темную комнату, где есть свеча, лампа и камин. У вас одна спичка.\n\nЧто вы зажжете первым?",
    "🌊 Что может путешествовать по всему миру, оставаясь в углу?",
    "🏃 Вы участвуете в забеге и обогнали бегуна, который бежал вторым.\n\nНа каком месте вы теперь?",
    "🪙 В кошельке лежит 50 копеек двумя монетами. Одна из них не 10 копеек.\n\nКакие это монеты?",
    "🎂 У Ани день рождения. Ей исполнилось 10 лет, но она отпраздновала только 3 дня рождения в жизни.\n\nКак такое возможно?",
    "🔐 Что имеет голову, но не имеет мозгов?",
    "📦 В одной коробке лежит 10 кг песка, в другой - 10 кг пуха.\n\nКакая коробка тяжелее?",
]


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


def create_yookassa_payment(user_id, amount, description="Создание профиля", payment_type="profile"):
    """Создает платеж в ЮKassa"""
    try:
        import base64
        import json

        # Формируем URL возврата в зависимости от типа платежа
        return_url = f"{get_base_url()}/payment/success?user_id={user_id}&type={payment_type}"

        # Подготавливаем данные для создания платежа
        payment_data = {
            "amount": {
                "value": f"{amount:.2f}",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": return_url
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

    // Глобальная функция для применения черно-белого режима
    function applyGlobalGrayscaleMode() {
        // Проверяем, есть ли user_id в cookie
        const userId = document.cookie.split('; ').find(row => row.startsWith('user_id='));
        if (!userId) {
            console.log('🔍 Пользователь не авторизован, черно-белый режим не применяется');
            return;
        }

        // Загружаем настройки пользователя
        fetch('/api/get_settings')
            .then(response => {
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(settings => {
                console.log('📋 Настройки черно-белого режима загружены:', settings);
                if (settings.grayscale_mode === true || settings.grayscale_mode === 1) {
                    document.body.classList.add('grayscale-mode');
                    console.log('⚫ Черно-белый режим включен');
                } else {
                    document.body.classList.remove('grayscale-mode');
                    console.log('⚪ Черно-белый режим выключен');
                }
            })
            .catch(error => {
                console.error('❌ Ошибка загрузки настроек черно-белого режима:', error);
            });
    }

    // Применяем черно-белый режим при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        // Добавляем небольшую задержку для полной загрузки
        setTimeout(applyGlobalGrayscaleMode, 100);
    });

    // Применяем черно-белый режим при загрузке страницы (fallback)
    window.addEventListener('load', function() {
        // Добавляем небольшую задержку для полной загрузки
        setTimeout(applyGlobalGrayscaleMode, 200);
    });

    // Применяем черно-белый режим при изменении видимости страницы
    document.addEventListener('visibilitychange', function() {
        if (!document.hidden) {
            setTimeout(applyGlobalGrayscaleMode, 50);
        }
    });
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


@app.route('/api/send-surprise', methods=['POST'])
def api_send_surprise():
    """API для отправки сюрпризов (десерт, шампанское, анекдот) посетителям"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({"error": "Пользователь не авторизован"}), 401

    data = request.get_json()
    receiver_id = data.get('receiver_id')
    surprise_type = data.get('type')  # 'dessert', 'champagne', 'joke'

    if not receiver_id or not surprise_type:
        return jsonify({"error": "Не все параметры предоставлены"}), 400

    # Проверяем существование получателя
    receiver_profile = Profile.query.get(receiver_id)
    if not receiver_profile:
        return jsonify({"error": "Получатель не найден"}), 404

    # Проверяем существование отправителя
    sender_profile = Profile.query.get(user_id)
    if not sender_profile:
        return jsonify({"error": "Отправитель не найден"}), 404

    # НОВАЯ ЛОГИКА: Проверяем, оплачена ли функция "Удивить"
    if not sender_profile.surprise_feature_paid:
        return jsonify({
            "error": "Функция не оплачена",
            "payment_required": True,
            "price": SURPRISE_FEATURE_PRICE
        }), 402  # 402 Payment Required

    try:
        # Формируем chat_key для отправки сообщения
        chat_key = '_'.join(sorted([user_id, receiver_id]))

        # Определяем текст и тип сообщения в зависимости от типа сюрприза
        if surprise_type == 'dessert':
            message_text = "🍰 SURPRISE_DESSERT"  # Специальный маркер для фронтенда

        elif surprise_type == 'champagne':
            message_text = "🍾 SURPRISE_CHAMPAGNE"  # Специальный маркер для фронтенда

        elif surprise_type == 'puzzle':
            # Получаем список уже отправленных головоломок этому получателю
            sent_puzzles = SentPuzzle.query.filter_by(
                sender_id=user_id,
                receiver_id=receiver_id
            ).all()
            sent_puzzle_ids = [sp.puzzle_id for sp in sent_puzzles]

            # Находим доступные головоломки (не отправленные ранее)
            available_puzzle_ids = [i for i in range(len(LOGIC_PUZZLES)) if i not in sent_puzzle_ids]

            if not available_puzzle_ids:
                return jsonify({
                    "error": "Все головоломки уже отправлены этому пользователю",
                    "all_puzzles_sent": True
                }), 400

            # Выбираем случайную головоломку из доступных
            import random
            selected_puzzle_id = random.choice(available_puzzle_ids)
            selected_puzzle = LOGIC_PUZZLES[selected_puzzle_id]

            # Сохраняем информацию об отправленной головоломке
            new_sent_puzzle = SentPuzzle(
                sender_id=user_id,
                receiver_id=receiver_id,
                puzzle_id=selected_puzzle_id
            )
            db.session.add(new_sent_puzzle)

            message_text = f"🧠 SURPRISE_PUZZLE\n\n{selected_puzzle}"

        elif surprise_type == 'joke':
            # Получаем список уже отправленных анекдотов этому получателю
            sent_jokes = SentJoke.query.filter_by(
                sender_id=user_id,
                receiver_id=receiver_id
            ).all()
            sent_joke_ids = [sj.joke_id for sj in sent_jokes]

            # Находим доступные анекдоты (не отправленные ранее)
            available_joke_ids = [i for i in range(len(RESTAURANT_JOKES)) if i not in sent_joke_ids]

            if not available_joke_ids:
                return jsonify({
                    "error": "Все анекдоты уже отправлены этому пользователю",
                    "all_jokes_sent": True
                }), 400

            # Выбираем случайный анекдот из доступных
            import random
            selected_joke_id = random.choice(available_joke_ids)
            selected_joke = RESTAURANT_JOKES[selected_joke_id]

            # Сохраняем информацию об отправленном анекдоте
            new_sent_joke = SentJoke(
                sender_id=user_id,
                receiver_id=receiver_id,
                joke_id=selected_joke_id
            )
            db.session.add(new_sent_joke)

            message_text = f"😄 SURPRISE_JOKE\n\n{selected_joke}"
        else:
            return jsonify({"error": "Неверный тип сюрприза"}), 400

        # Сохраняем сообщение в базу данных
        new_message = Message(
            chat_key=chat_key,
            sender=user_id,
            text=message_text
        )
        db.session.add(new_message)

        # Создаем разрешение на общение (если еще не существует)
        existing_permission = ChatPermission.query.filter_by(
            sender_id=user_id,
            receiver_id=receiver_id
        ).first()

        if not existing_permission:
            chat_permission = ChatPermission(
                sender_id=user_id,
                receiver_id=receiver_id
            )
            db.session.add(chat_permission)
            print(f"✅ Создано разрешение на общение: {user_id} → {receiver_id}")

        db.session.commit()

        # Отправляем сообщение через Socket.IO
        socketio.emit('message', {
            'text': message_text,
            'sender': user_id
        }, room=chat_key)

        return jsonify({
            "success": True,
            "type": surprise_type,
            "message": "Сюрприз успешно отправлен!",
            "chat_enabled": True  # Теперь можно писать сообщения
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка при отправке сюрприза: {str(e)}"}), 500


@app.route('/api/pay-surprise-feature', methods=['POST'])
def api_pay_surprise_feature():
    """API для оплаты функции 'Удивить'"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({"error": "Пользователь не авторизован"}), 401

    try:
        # Проверяем профиль
        profile = Profile.query.get(user_id)
        if not profile:
            return jsonify({"error": "Профиль не найден"}), 404

        # Проверяем, не оплачено ли уже
        if profile.surprise_feature_paid:
            return jsonify({
                "success": True,
                "already_paid": True,
                "message": "Функция уже оплачена"
            })

        # Сохраняем информацию о типе платежа и текущем получателе
        # Это нужно для возврата на правильную страницу после оплаты

        # Создаем платеж через ЮKassa
        payment_result = create_yookassa_payment(
            user_id=user_id,
            amount=SURPRISE_FEATURE_PRICE,
            description="Функция 'Удивить' - отправка сюрпризов",
            payment_type="surprise"  # Указываем тип платежа
        )

        if payment_result and 'payment_url' in payment_result:
            # Сохраняем информацию о платеже
            payment = Payment(
                user_id=user_id,
                amount=SURPRISE_FEATURE_PRICE,
                status='pending',
                description="Функция 'Удивить'",
                yookassa_payment_id=payment_result.get('payment_id'),
                yookassa_payment_url=payment_result.get('payment_url')
            )
            db.session.add(payment)
            db.session.commit()

            return jsonify({
                "success": True,
                "payment_url": payment_result['payment_url'],
                "payment_id": payment_result.get('payment_id'),
                "amount": SURPRISE_FEATURE_PRICE
            })
        else:
            return jsonify({"error": "Не удалось создать платеж"}), 500

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Ошибка при создании платежа: {str(e)}"}), 500


@app.route('/api/check-surprise-feature-status')
def api_check_surprise_feature_status():
    """Проверка статуса оплаты функции 'Удивить'"""
    user_id = request.cookies.get('user_id')
    if not user_id:
        return jsonify({"error": "Пользователь не авторизован"}), 401

    try:
        profile = Profile.query.get(user_id)
        if not profile:
            return jsonify({"error": "Профиль не найден"}), 404

        return jsonify({
            "success": True,
            "paid": profile.surprise_feature_paid,
            "payment_date": profile.surprise_feature_payment_date.isoformat() if profile.surprise_feature_payment_date else None,
            "price": SURPRISE_FEATURE_PRICE
        })

    except Exception as e:
        return jsonify({"error": f"Ошибка: {str(e)}"}), 500


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
    
    # Улучшенная проверка профиля
    has_profile = None
    if user_id:
        profile = Profile.query.get(user_id)
        if profile and profile.is_paid:
            # Проверяем, не истек ли срок жизни профиля
            try:
                remaining_time = get_profile_lifetime_remaining(user_id)
                if remaining_time != 'Истекла':
                    has_profile = profile
                    print(f"✅ Пользователь {user_id} имеет активный оплаченный профиль")
                else:
                    print(f"⏰ Профиль пользователя {user_id} истек")
            except Exception as e:
                print(f"⚠️ Ошибка при проверке времени жизни профиля: {e}")
                has_profile = profile  # В случае ошибки считаем профиль активным
        else:
            print(f"❌ Пользователь {user_id} не имеет оплаченного профиля")
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

                // 🔐 БЕЗОПАСНАЯ ФУНКЦИЯ УСТАНОВКИ КУКИ ДЛЯ HTTPS
                function setCookie(name, value, days = 365) {
                    const expires = new Date();
                    expires.setTime(expires.getTime() + (days * 24 * 60 * 60 * 1000));
                    document.cookie = `${name}=${value}; expires=${expires.toUTCString()}; path=/; SameSite=Lax`;
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

                    // Защита от множественных переадресаций
                    if (sessionStorage.getItem('redirecting')) {
                        console.log('⚠️ Переадресация уже выполняется, пропускаем...');
                        return false;
                    }

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

                            if (data.success && data.exists && data.is_paid && data.is_active) {
                                console.log('✅ Профиль найден, оплачен и активен! Восстанавливаем сессию...');
                                console.log('💰 Профиль оплачен:', data.is_paid);
                                console.log('⏰ Оставшееся время:', data.remaining_time);
                                console.log('👤 Имя пользователя:', data.profile_data?.name || 'Неизвестно');

                                // Восстанавливаем сессию
                                setCookie('user_id', userId);
                                saveUserId(userId);

                                // Скрываем кнопку создания анкеты
                                const createSection = document.getElementById('create-profile-section');
                                if (createSection) {
                                    createSection.style.display = 'none';
                                    console.log('✅ Кнопка создания анкеты скрыта');
                                }

                                // Устанавливаем флаг переадресации
                                sessionStorage.setItem('redirecting', 'true');
                                console.log('✅ Сессия восстановлена, возвращаем true для перенаправления');
                                return true;
                            } else if (data.success && data.exists && !data.is_paid) {
                                console.log('⚠️ Профиль найден, но не оплачен. Перенаправляем на оплату...');
                                // Устанавливаем флаг переадресации
                                sessionStorage.setItem('redirecting', 'true');
                                window.location.href = '/payment';
                                return true;
                            } else if (data.success && data.exists && !data.is_active) {
                                console.log('⏰ Профиль найден, но истек срок жизни. Позволяем создать новый...');
                                // Показываем кнопку создания анкеты
                                const createSection = document.getElementById('create-profile-section');
                                if (createSection) {
                                    createSection.style.display = 'block';
                                    console.log('✅ Кнопка создания анкеты показана (профиль истек)');
                                }
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

                            if (data.success && data.exists && data.is_paid && data.is_active) {
                                // Профиль существует, оплачен и активен - скрываем кнопку
                                createSection.style.display = 'none';
                                console.log('✅ Профиль существует, оплачен и активен, кнопка создания скрыта');
                            } else if (data.success && data.exists && !data.is_paid) {
                                // Профиль существует, но не оплачен - скрываем кнопку (перенаправим на оплату)
                                createSection.style.display = 'none';
                                console.log('⚠️ Профиль существует, но не оплачен, кнопка создания скрыта');
                            } else {
                                // Профиль не существует или истек - показываем кнопку
                                createSection.style.display = 'block';
                                console.log('❌ Профиль не существует или истек, кнопка создания показана');
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

                    // Очищаем флаг переадресации при загрузке страницы
                    sessionStorage.removeItem('redirecting');

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
                            // Устанавливаем флаг переадресации для предотвращения множественных переадресаций
                            sessionStorage.setItem('redirecting', 'true');
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
                
                # 📸 СЖАТИЕ ИЗОБРАЖЕНИЯ
                print(f"🔄 Обрабатываем фото: {photo.filename}")
                compressed_photo = compress_image(photo, max_size=(800, 800), quality=85, max_file_size=5*1024*1024)
                
                # Сохраняем сжатое изображение
                with open(photo_path, 'wb') as f:
                    f.write(compressed_photo.getvalue())
                print(f"✅ Фото сохранено: {photo_path}")
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
                resp.set_cookie('user_id', user_id, max_age=365*24*60*60, path='/', secure=False, httponly=False, samesite='Lax')
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

                /* Стили для readonly полей */
                input[readonly] {
                    background: rgba(76, 175, 80, 0.05) !important;
                    border: 1px solid rgba(76, 175, 80, 0.2) !important;
                    color: rgba(255, 255, 255, 0.8) !important;
                    cursor: not-allowed;
                }

                input[readonly]:focus {
                    outline: none !important;
                    border-color: rgba(76, 175, 80, 0.2) !important;
                    box-shadow: none !important;
                    background: rgba(76, 175, 80, 0.05) !important;
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
                    <input type="text" name="venue" id="venue-input" placeholder="Выберите заведение на карте" readonly required onchange="updateVenueCoordinates()">
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
                                    // 🔐 БЕЗОПАСНАЯ УСТАНОВКА КУКИ ДЛЯ HTTPS
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

                // Функция для проверки существующего профиля (УДАЛЕНА - дублирует autoRestoreSession)
                // Эта логика теперь обрабатывается в autoRestoreSession() на главной странице

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

        cursor.execute('SELECT sound_notifications, grayscale_mode FROM user_settings WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            # Проверяем, есть ли поле grayscale_mode в результате
            grayscale_mode = False
            if len(result) > 1 and result[1] is not None:
                grayscale_mode = bool(result[1])
            elif len(result) > 1 and result[1] is None:
                # Если поле существует, но значение NULL, используем значение по умолчанию
                grayscale_mode = False

            return {
                'sound_notifications': bool(result[0]),
                'grayscale_mode': grayscale_mode
            }
        else:
            # Создаем настройки по умолчанию
            return {
                'sound_notifications': True,
                'grayscale_mode': False
            }

    except Exception as e:
        print(f"❌ Ошибка получения настроек для {user_id}: {e}")
        return {
            'sound_notifications': True,
            'grayscale_mode': False
        }


def update_user_settings(user_id, sound_notifications=None, grayscale_mode=None):
    """Обновляет настройки пользователя в базе данных"""
    try:
        import sqlite3
        conn = sqlite3.connect('dating_app.db')
        cursor = conn.cursor()

        # Проверяем, есть ли уже настройки для пользователя
        cursor.execute('SELECT user_id FROM user_settings WHERE user_id = ?', (user_id,))
        existing = cursor.fetchone()

        if existing:
            # Обновляем существующие настройки
            if sound_notifications is not None and grayscale_mode is not None:
                cursor.execute('''
                    UPDATE user_settings 
                    SET sound_notifications = ?, grayscale_mode = ? 
                    WHERE user_id = ?
                ''', (1 if sound_notifications else 0, 1 if grayscale_mode else 0, user_id))
            elif sound_notifications is not None:
                cursor.execute('''
                    UPDATE user_settings 
                    SET sound_notifications = ? 
                    WHERE user_id = ?
                ''', (1 if sound_notifications else 0, user_id))
            elif grayscale_mode is not None:
                cursor.execute('''
                    UPDATE user_settings 
                    SET grayscale_mode = ? 
                    WHERE user_id = ?
                ''', (1 if grayscale_mode else 0, user_id))
        else:
            # Создаем новые настройки
            sound_val = 1 if sound_notifications else 0 if sound_notifications is not None else 1
            grayscale_val = 1 if grayscale_mode else 0 if grayscale_mode is not None else 0

            cursor.execute('''
                INSERT INTO user_settings (user_id, sound_notifications, grayscale_mode) 
                VALUES (?, ?, ?)
            ''', (user_id, sound_val, grayscale_val))

        conn.commit()
        conn.close()

        print(
            f"✅ Настройки обновлены для {user_id}: sound_notifications = {sound_notifications}, grayscale_mode = {grayscale_mode}")
        return True

    except Exception as e:
        print(f"❌ Ошибка обновления настроек для {user_id}: {e}")
        import traceback
        print(f"❌ Детали ошибки: {traceback.format_exc()}")
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
            
            # Дополнительная проверка для оплаченных профилей
            if profile and profile.is_paid:
                try:
                    remaining_time = get_profile_lifetime_remaining(user_id)
                    if remaining_time == 'Истекла':
                        print(f"⏰ @require_profile: профиль оплачен, но истек срок жизни")
                        # Для истекших профилей разрешаем доступ, но пользователь может создать новый
                    else:
                        print(f"✅ @require_profile: профиль оплачен и активен, оставшееся время: {remaining_time}")
                except Exception as e:
                    print(f"⚠️ @require_profile: ошибка при проверке времени жизни профиля: {e}")
                    # В случае ошибки считаем профиль активным

            # Дополнительная проверка безопасности: проверяем, что IP-адрес совпадает
            # Это предотвращает доступ к чужим анкетам через общие cookies
            # ИСПРАВЛЕНО: Полностью убираем IP-проверку для оплаченных профилей
            if profile and hasattr(profile, 'creation_ip') and profile.creation_ip:
                client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                
                if profile.is_paid:
                    # Для оплаченных профилей НЕ проверяем IP - разрешаем доступ с любого IP
                    if profile.creation_ip != client_ip:
                        print(f"✅ IP изменился для оплаченного профиля {profile.name}: {profile.creation_ip} -> {client_ip} (доступ разрешен)")
                else:
                    # Для неоплаченных профилей проверяем IP
                    if profile.creation_ip != client_ip:
                        print(f"⚠️ IP не совпадает для неоплаченного профиля {profile.name}: {profile.creation_ip} != {client_ip}")
                        print(f"🔄 Перенаправляем на создание профиля")
                        return redirect(url_for('create_profile'))
                    else:
                        print(f"✅ IP совпадает для неоплаченного профиля {profile.name}: {client_ip}")

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

    # Создаем список ID пользователей, с которыми есть матч
    matched_ids = set()
    for match in matches:
        if match.user1_id == user_id:
            liked_ids.add(match.user2_id)
            matched_ids.add(match.user2_id)
        else:
            liked_ids.add(match.user1_id)
            matched_ids.add(match.user1_id)
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

                /* Кнопка "Удивить" */
                .surprise-btn {
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    border: none;
                    border-radius: 50%;
                    width: 45px;
                    height: 45px;
                    cursor: pointer;
                    outline: none;
                    font-size: 1.5em;
                    position: absolute;
                    bottom: 15px;
                    right: 18px;
                    z-index: 2;
                    transition: all 0.3s ease;
                    box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
                }
                .surprise-btn:hover {
                    transform: scale(1.1) rotate(15deg);
                    box-shadow: 0 6px 25px rgba(102, 126, 234, 0.5);
                }
                .surprise-btn:active {
                    transform: scale(0.95);
                }

                /* Модальное окно */
                .modal {
                    display: none;
                    position: fixed;
                    z-index: 1000;
                    left: 0;
                    top: 0;
                    width: 100%;
                    height: 100%;
                    background-color: rgba(0, 0, 0, 0.7);
                    animation: fadeIn 0.3s ease;
                }
                .modal.show {
                    display: flex;
                    justify-content: center;
                    align-items: center;
                }
                @keyframes fadeIn {
                    from { opacity: 0; }
                    to { opacity: 1; }
                }
                .modal-content {
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
                    padding: 30px;
                    border-radius: 20px;
                    max-width: 400px;
                    width: 90%;
                    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    animation: slideUp 0.3s ease;
                    position: relative;
                }
                @keyframes slideUp {
                    from { 
                        transform: translateY(50px);
                        opacity: 0;
                    }
                    to { 
                        transform: translateY(0);
                        opacity: 1;
                    }
                }
                .modal-close {
                    position: absolute;
                    top: 15px;
                    right: 15px;
                    font-size: 1.5em;
                    cursor: pointer;
                    color: #fff;
                    transition: all 0.2s;
                }
                .modal-close:hover {
                    color: #ff6b6b;
                    transform: rotate(90deg);
                }
                .modal-title {
                    color: #fff;
                    font-size: 1.5em;
                    margin-bottom: 20px;
                    text-align: center;
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                }
                .surprise-options {
                    display: flex;
                    flex-direction: column;
                    gap: 15px;
                }
                .surprise-option {
                    background: rgba(255, 255, 255, 0.1);
                    border: 2px solid rgba(255, 255, 255, 0.2);
                    border-radius: 15px;
                    padding: 20px;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    display: flex;
                    align-items: center;
                    gap: 15px;
                }
                .surprise-option:hover {
                    background: rgba(255, 255, 255, 0.2);
                    border-color: #667eea;
                    transform: translateY(-3px);
                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
                }
                .surprise-icon {
                    font-size: 3em;
                }
                .surprise-text {
                    color: #fff;
                    font-size: 1.1em;
                    flex: 1;
                }
                .surprise-text h3 {
                    margin: 0 0 5px 0;
                    color: #fff;
                }
                .surprise-text p {
                    margin: 0;
                    font-size: 0.9em;
                    opacity: 0.8;
                    color: #ccc;
                }

                /* Анимация шампанского с вылетающей пробкой */
                .champagne-animation {
                    position: relative;
                    width: 100%;
                    height: 200px;
                    display: flex;
                    justify-content: center;
                    align-items: flex-end;
                }
                .champagne-bottle {
                    font-size: 5em;
                    position: relative;
                }
                .champagne-cork {
                    position: absolute;
                    font-size: 0.3em;
                    top: -10px;
                    left: 50%;
                    transform: translateX(-50%);
                }
                .champagne-cork.pop {
                    animation: corkPop 1s ease-out forwards;
                }
                @keyframes corkPop {
                    0% {
                        transform: translateX(-50%) translateY(0) rotate(0deg);
                        opacity: 1;
                    }
                    50% {
                        transform: translateX(-50%) translateY(-100px) rotate(360deg);
                        opacity: 1;
                    }
                    100% {
                        transform: translateX(-50%) translateY(-150px) rotate(720deg);
                        opacity: 0;
                    }
                }
                .champagne-sparkles {
                    position: absolute;
                    top: 0;
                    left: 50%;
                    transform: translateX(-50%);
                    font-size: 0.5em;
                }
                .champagne-sparkles.show {
                    animation: sparkles 1s ease-out forwards;
                }
                @keyframes sparkles {
                    0% {
                        opacity: 0;
                        transform: translateX(-50%) translateY(0) scale(0.5);
                    }
                    50% {
                        opacity: 1;
                        transform: translateX(-50%) translateY(-50px) scale(1.2);
                    }
                    100% {
                        opacity: 0;
                        transform: translateX(-50%) translateY(-80px) scale(0.8);
                    }
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
                                btn.classList.add('liked');
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
                                btn.classList.remove('liked');
                            }
                        });
                }

                function goToProfile(profileId) {
                    window.location.href = '/profile/' + profileId;
                }

                // ============================================================================
                // ФУНКЦИИ ДЛЯ РАБОТЫ С СЮРПРИЗАМИ
                // ============================================================================

                // Переменные для модального окна
                let currentReceiverId = null;
                let currentReceiverName = null;

                // Открыть модальное окно выбора сюрприза
                function openSurpriseModal(profileId, profileName) {
                    event.stopPropagation(); // Предотвращаем переход на профиль
                    currentReceiverId = profileId;
                    currentReceiverName = profileName;

                    // Проверяем статус оплаты функции
                    fetch('/api/check-surprise-feature-status')
                        .then(response => response.json())
                        .then(data => {
                            if (data.success && data.paid) {
                                // Функция оплачена - показываем выбор сюрпризов
                                const modal = document.getElementById('surpriseModal');
                                modal.classList.add('show');
                                console.log('Открыто модальное окно для:', profileName, profileId);
                            } else {
                                // Функция не оплачена - показываем окно оплаты
                                const paymentModal = document.getElementById('paymentModal');
                                paymentModal.classList.add('show');
                                console.log('Требуется оплата функции');
                            }
                        })
                        .catch(error => {
                            console.error('Ошибка проверки статуса:', error);
                            showNotification('Ошибка при проверке статуса оплаты', 'error');
                        });
                }

                // Закрыть модальное окно
                function closeSurpriseModal() {
                    const modal = document.getElementById('surpriseModal');
                    modal.classList.remove('show');
                    currentReceiverId = null;
                    currentReceiverName = null;
                }

                // Закрыть модальное окно оплаты
                function closePaymentModal() {
                    const modal = document.getElementById('paymentModal');
                    modal.classList.remove('show');
                }

                // Перейти к оплате
                function proceedToPayment() {
                    fetch('/api/pay-surprise-feature', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success && data.payment_url) {
                            // Перенаправляем на страницу оплаты ЮKassa
                            window.location.href = data.payment_url;
                        } else if (data.already_paid) {
                            showNotification('Функция уже оплачена!', 'success');
                            closePaymentModal();
                            // Обновляем страницу
                            setTimeout(() => location.reload(), 1000);
                        } else {
                            showNotification(data.error || 'Ошибка при создании платежа', 'error');
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка:', error);
                        showNotification('Ошибка при создании платежа', 'error');
                    });
                }

                // Закрытие модального окна при клике вне его
                window.onclick = function(event) {
                    const surpriseModal = document.getElementById('surpriseModal');
                    const paymentModal = document.getElementById('paymentModal');
                    if (event.target == surpriseModal) {
                        closeSurpriseModal();
                    }
                    if (event.target == paymentModal) {
                        closePaymentModal();
                    }
                }

                // Отправить сюрприз
                function sendSurprise(type) {
                    if (!currentReceiverId) {
                        console.error('Не выбран получатель сюрприза');
                        return;
                    }

                    console.log('Отправка сюрприза:', type, 'для:', currentReceiverName);

                    // Показываем анимацию для шампанского
                    if (type === 'champagne') {
                        showChampagneAnimation();
                    }

                    // Отправляем запрос на сервер
                    fetch('/api/send-surprise', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            receiver_id: currentReceiverId,
                            type: type
                        })
                    })
                    .then(response => {
                        // Проверяем статус ответа
                        if (response.status === 402) {
                            // 402 Payment Required - функция не оплачена
                            closeSurpriseModal();
                            const paymentModal = document.getElementById('paymentModal');
                            paymentModal.classList.add('show');
                            showNotification('Требуется оплата функции "Удивить"', 'info');
                            return null;
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (!data) return; // Если требуется оплата, data будет null

                        if (data.success) {
                            let message = '';
                            if (type === 'dessert') {
                                message = `🍰 Десерт отправлен ${currentReceiverName}!`;
                            } else if (type === 'champagne') {
                                message = `🍾 Шампанское отправлено ${currentReceiverName}!`;
                            } else if (type === 'joke') {
                                message = `😄 Анекдот отправлен ${currentReceiverName}!`;
                            } else if (type === 'puzzle') {
                                message = `🧠 Головоломка отправлена ${currentReceiverName}!`;
                            }

                            if (data.chat_enabled) {
                                message += ' Теперь вы можете писать сообщения!';
                            }

                            showNotification(message, 'success');
                            closeSurpriseModal();
                        } else {
                            if (data.all_jokes_sent) {
                                showNotification(`Все анекдоты уже отправлены ${currentReceiverName}`, 'info');
                            } else if (data.all_puzzles_sent) {
                                showNotification(`Все головоломки уже отправлены ${currentReceiverName}`, 'info');
                            } else if (data.payment_required) {
                                // Показываем окно оплаты
                                closeSurpriseModal();
                                const paymentModal = document.getElementById('paymentModal');
                                paymentModal.classList.add('show');
                            } else {
                                showNotification(data.error || 'Ошибка при отправке сюрприза', 'error');
                            }
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка:', error);
                        showNotification('Ошибка при отправке сюрприза', 'error');
                    });
                }

                // Показать анимацию вылета пробки шампанского
                function showChampagneAnimation() {
                    // Создаем контейнер для анимации
                    const animContainer = document.createElement('div');
                    animContainer.className = 'champagne-animation';
                    animContainer.style.position = 'fixed';
                    animContainer.style.top = '50%';
                    animContainer.style.left = '50%';
                    animContainer.style.transform = 'translate(-50%, -50%)';
                    animContainer.style.zIndex = '2000';

                    // Бутылка
                    const bottle = document.createElement('div');
                    bottle.className = 'champagne-bottle';
                    bottle.innerHTML = '🍾';

                    // Пробка
                    const cork = document.createElement('div');
                    cork.className = 'champagne-cork';
                    cork.innerHTML = '🟤';

                    // Искры/брызги
                    const sparkles = document.createElement('div');
                    sparkles.className = 'champagne-sparkles';
                    sparkles.innerHTML = '✨💫✨';

                    bottle.appendChild(cork);
                    bottle.appendChild(sparkles);
                    animContainer.appendChild(bottle);
                    document.body.appendChild(animContainer);

                    // Запускаем анимацию
                    setTimeout(() => {
                        cork.classList.add('pop');
                        sparkles.classList.add('show');
                    }, 100);

                    // Удаляем анимацию после завершения
                    setTimeout(() => {
                        document.body.removeChild(animContainer);
                    }, 1500);
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
                        <!-- Кнопка "Удивить" видна ВСЕМ посетителям -->
                        <button class="surprise-btn" title="Удивить" onclick="openSurpriseModal('{{ profile.id }}', '{{ profile.name }}')">
                            ✨
                        </button>
                    </div>
                {% endfor %}
            {% else %}
                <p>Пока нет других посетителей.</p>
            {% endif %}

            <!-- Модальное окно для выбора сюрприза -->
            <div id="surpriseModal" class="modal">
                <div class="modal-content">
                    <span class="modal-close" onclick="closeSurpriseModal()">×</span>
                    <h2 class="modal-title">Удивить собеседника</h2>
                    <div class="surprise-options">
                        <div class="surprise-option" onclick="sendSurprise('dessert')">
                            <div class="surprise-icon">🍰</div>
                            <div class="surprise-text">
                                <h3>Подарить десерт</h3>
                                <p>Отправить изображение вкусного десерта</p>
                            </div>
                        </div>
                        <div class="surprise-option" onclick="sendSurprise('champagne')">
                            <div class="surprise-icon">🍾</div>
                            <div class="surprise-text">
                                <h3>Шампанское</h3>
                                <p>Отправить анимацию с вылетающей пробкой</p>
                            </div>
                        </div>
                        <div class="surprise-option" onclick="sendSurprise('joke')">
                            <div class="surprise-icon">😄</div>
                            <div class="surprise-text">
                                <h3>Рассмешить</h3>
                                <p>Отправить смешной анекдот про ресторан</p>
                            </div>
                        </div>
                        <div class="surprise-option" onclick="sendSurprise('puzzle')">
                            <div class="surprise-icon">🧠</div>
                            <div class="surprise-text">
                                <h3>Напрягись</h3>
                                <p>Отправить головоломку или задачку на логику</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Модальное окно оплаты функции "Удивить" -->
            <div id="paymentModal" class="modal">
                <div class="modal-content">
                    <span class="modal-close" onclick="closePaymentModal()">×</span>
                    <h2 class="modal-title">💳 Оплата функции "Удивить"</h2>
                    <div style="padding: 20px; text-align: center;">
                        <div style="font-size: 4em; margin-bottom: 20px;">✨</div>
                        <p style="color: #fff; font-size: 1.1em; margin-bottom: 15px;">
                            Функция "Удивить" позволяет отправлять сюрпризы любым посетителям!
                        </p>
                        <div style="background: rgba(255, 255, 255, 0.1); border-radius: 15px; padding: 20px; margin: 20px 0;">
                            <p style="color: #4CAF50; font-size: 1.8em; font-weight: bold; margin: 0;">
                                {{ SURPRISE_FEATURE_PRICE|int }} ₽
                            </p>
                            <p style="color: #ccc; font-size: 0.9em; margin: 10px 0 0 0;">
                                Один раз навсегда
                            </p>
                        </div>
                        <p style="color: #fff; font-size: 0.95em; margin-bottom: 25px;">
                            ✅ Отправляйте десерты, шампанское и анекдоты<br>
                            ✅ Начинайте общение без мэтча<br>
                            ✅ Безлимитное использование
                        </p>
                        <button onclick="proceedToPayment()" style="
                            background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%);
                            color: white;
                            border: none;
                            padding: 15px 40px;
                            border-radius: 25px;
                            font-size: 1.2em;
                            cursor: pointer;
                            font-weight: bold;
                            box-shadow: 0 4px 20px rgba(76, 175, 80, 0.4);
                            transition: all 0.3s ease;
                        " onmouseover="this.style.transform='translateY(-3px) scale(1.05)'" onmouseout="this.style.transform=''">
                            💳 Оплатить
                        </button>
                    </div>
                </div>
            </div>

            <script>
            // Проверяем параметр surprise_paid в URL
            const urlParams = new URLSearchParams(window.location.search);
            if (urlParams.get('surprise_paid') === '1') {
                // Функция только что оплачена - показываем уведомление
                setTimeout(() => {
                    showNotification('✨ Функция "Удивить" активирована! Теперь вы можете отправлять сюрпризы всем посетителям!', 'success');
                    // Убираем параметр из URL
                    window.history.replaceState({}, document.title, '/visitors');
                }, 500);
            }

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
    ''', other_profiles=other_profiles, liked_ids=liked_ids, matched_ids=matched_ids, navbar=navbar,
                                  get_photo_url=get_photo_url,
                                  get_starry_night_css=get_starry_night_css,
                                  get_profile_lifetime_remaining=get_profile_lifetime_remaining, user_id=user_id,
                                  SURPRISE_FEATURE_PRICE=SURPRISE_FEATURE_PRICE)


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
            
            # 📸 СЖАТИЕ ИЗОБРАЖЕНИЯ
            print(f"🔄 Обрабатываем фото для редактирования: {photo.filename}")
            compressed_photo = compress_image(photo, max_size=(800, 800), quality=85, max_file_size=5*1024*1024)
            
            # Сохраняем сжатое изображение
            with open(photo_path, 'wb') as f:
                f.write(compressed_photo.getvalue())
            print(f"✅ Фото сохранено: {photo_path}")
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

                /* Стили для readonly полей */
                input[readonly] {
                    background: rgba(76, 175, 80, 0.05) !important;
                    border: 1px solid rgba(76, 175, 80, 0.2) !important;
                    color: rgba(255, 255, 255, 0.8) !important;
                    cursor: not-allowed;
                }

                input[readonly]:focus {
                    outline: none !important;
                    border-color: rgba(76, 175, 80, 0.2) !important;
                    box-shadow: none !important;
                    background: rgba(76, 175, 80, 0.05) !important;
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
                    <input type="text" name="venue" id="venue-input" value="{{ pending.venue or '' }}" placeholder="Выберите заведение на карте" readonly required onchange="updateVenueCoordinates()">
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
        # Взаимный лайк - создаем метч и удаляем ОБА лайка
        db.session.delete(mutual_like)  # Удаляем лайк от целевого пользователя

        # Добавляем лайк от текущего пользователя
        new_like = Like(user_id=user_id, liked_id=profile_id)
        db.session.add(new_like)
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
        return jsonify({'liked': True, 'already_liked': False, 'likes_count': likes_count, 'match_created': True})

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
                    // 🔐 БЕЗОПАСНАЯ УСТАНОВКА КУКИ ДЛЯ HTTPS
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
            
            # 📸 СЖАТИЕ ИЗОБРАЖЕНИЯ
            print(f"🔄 Обрабатываем фото для основного профиля: {photo.filename}")
            compressed_photo = compress_image(photo, max_size=(800, 800), quality=85, max_file_size=5*1024*1024)
            
            # Сохраняем сжатое изображение
            with open(photo_path, 'wb') as f:
                f.write(compressed_photo.getvalue())
            print(f"✅ Фото сохранено: {photo_path}")
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

                /* Стили для readonly полей */
                input[readonly] {
                    background: rgba(76, 175, 80, 0.05) !important;
                    border: 1px solid rgba(76, 175, 80, 0.2) !important;
                    color: rgba(255, 255, 255, 0.8) !important;
                    cursor: not-allowed;
                }

                input[readonly]:focus {
                    outline: none !important;
                    border-color: rgba(76, 175, 80, 0.2) !important;
                    box-shadow: none !important;
                    background: rgba(76, 175, 80, 0.05) !important;
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
                    <input type="text" name="venue" id="venue-input" placeholder="Выберите заведение на карте" value="{{ profile.venue or '' }}" readonly required onchange="updateVenueCoordinates()">
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
                                btn.classList.add('liked');
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

    # Проверяем, лайкал ли текущий пользователь этот профиль
    already_liked = False
    if user_id and not is_owner:
        # Проверяем в лайках
        like_exists = Like.query.filter_by(user_id=user_id, liked_id=id).first()
        # Проверяем в метчах
        match_exists = Match.query.filter(
            ((Match.user1_id == user_id) & (Match.user2_id == id)) |
            ((Match.user1_id == id) & (Match.user2_id == user_id))
        ).first()
        already_liked = bool(like_exists or match_exists)

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
                    const button = event.target;

                    // Если кнопка уже disabled - не делаем ничего
                    if (button.disabled) {
                        return;
                    }

                    // Временно делаем кнопку неактивной
                    const originalContent = button.innerHTML;
                    button.innerHTML = '⏳';
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
                            button.innerHTML = '❤️';
                            button.style.background = '#ff6b6b';
                            button.style.cursor = 'not-allowed';
                            button.disabled = true;
                        } else if (data.already_liked) {
                            // Уже лайкал ранее
                            showNotification('💔 Вы уже лайкнули этого пользователя', 'warning');
                            button.innerHTML = '❤️';
                            button.style.background = '#ff6b6b';
                            button.style.cursor = 'not-allowed';
                            button.disabled = true;
                        } else if (data.match_created) {
                            // Создан мэтч!
                            showNotification('✨ У вас мэтч! Теперь вы можете общаться.', 'success');
                            button.innerHTML = '❤️';
                            button.style.background = '#ff6b6b';
                            button.style.cursor = 'not-allowed';
                            button.disabled = true;
                        } else {
                            // Неожиданный ответ - восстанавливаем кнопку
                            showNotification('⚠️ Неожиданный ответ сервера', 'warning');
                            button.innerHTML = originalContent;
                            button.disabled = false;
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка:', error);
                        showNotification('❌ Ошибка сети', 'error');
                        // Восстанавливаем кнопку при ошибке
                        button.innerHTML = originalContent;
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
                    <button type="button" 
                            id="likeBtn" 
                            class="modern-btn" 
                            onclick="likeProfile('{{ profile.id }}')"
                            {% if already_liked %}disabled{% endif %}
                            style="font-size: 2em; padding: 10px 20px; {% if already_liked %}background: #ff6b6b; cursor: not-allowed;{% else %}background: #666;{% endif %}">
                        {% if already_liked %}❤️{% else %}🤍{% endif %}
                    </button>
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
    ''', profile=profile, is_owner=is_owner, already_liked=already_liked, navbar=navbar, get_photo_url=get_photo_url,
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

    # Добавляем пользователей, которым мы отправили сюрпризы (есть ChatPermission)
    chat_permissions = ChatPermission.query.filter_by(sender_id=user_id).all()
    for permission in chat_permissions:
        chat_partners.add(permission.receiver_id)

    # Добавляем пользователей, которые отправили нам сюрпризы
    received_permissions = ChatPermission.query.filter_by(receiver_id=user_id).all()
    for permission in received_permissions:
        chat_partners.add(permission.sender_id)

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

    # Проверяем разрешение на общение после отправки сюрприза
    chat_permission_exists = ChatPermission.query.filter(
        ((ChatPermission.sender_id == user_id) & (ChatPermission.receiver_id == other_user_id)) |
        ((ChatPermission.sender_id == other_user_id) & (ChatPermission.receiver_id == user_id))
    ).first()

    # Доступ разрешен, если есть мэтч ИЛИ есть разрешение на общение
    if not match_exists and not chat_permission_exists:
        return "Чат доступен только для мэтчей или после отправки сюрприза", 403
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
                <!-- Сообщения будут загружены через JavaScript для правильной обработки сюрпризов -->
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
                let lastMessageCount = 0;  // Будет обновлено после загрузки истории
                let lastMessageTimestamp = "";

                // Socket.IO отключен для продакшн сервера (проблемы с конфигурацией)
                const socket = null;
                const socketConnected = false;

                console.log('⚠️ Socket.IO отключен, используется только AJAX');

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
                    // Проверяем дубликаты по содержимому и отправителю
                    const existingMessages = document.querySelectorAll('.message');
                    for (let existingMsg of existingMessages) {
                        const existingText = existingMsg.textContent.trim();
                        const existingSender = existingMsg.classList.contains('my-message') ? user_id : 'other';
                        const currentSender = sender === user_id ? user_id : 'other';

                        // Если сообщение с таким же текстом и отправителем уже есть
                        if (existingText === msg.trim() && existingSender === currentSender) {
                            console.log('⚠️ Дубликат сообщения обнаружен, пропускаем:', msg);
                            return;
                        }
                    }

                    // Дополнительная проверка по timestamp если есть
                    if (timestamp) {
                        for (let existingMsg of existingMessages) {
                            const existingTimestamp = existingMsg.getAttribute('data-timestamp');
                            if (existingTimestamp === timestamp) {
                                console.log('⚠️ Дубликат по timestamp обнаружен, пропускаем:', msg);
                                return;
                            }
                        }
                    }

                    const div = document.createElement('div');
                    div.className = 'message ' + (sender === user_id ? 'my-message' : 'their-message');

                    // Сохраняем timestamp как атрибут для проверки дубликатов
                    if (timestamp) {
                        div.setAttribute('data-timestamp', timestamp);
                    }

                    // ============================================================================
                    // ОБРАБОТКА СПЕЦИАЛЬНЫХ СЮРПРИЗОВ
                    // ============================================================================

                    // Обработка десерта
                    if (msg.includes('SURPRISE_DESSERT')) {
                        div.innerHTML = `
                            <div style="text-align: center; padding: 10px;">
                                <div style="font-size: 1em; color: #fff; margin-bottom: 8px; font-weight: bold;">
                                    🎁 Вам отправили сюрприз!
                                </div>
                                <div style="
                                    background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #ffecd2 100%);
                                    border-radius: 15px;
                                    padding: 15px 20px;
                                    box-shadow: 0 5px 20px rgba(255, 154, 158, 0.5);
                                    animation: dessertPulse 2s ease-in-out infinite;
                                    max-width: 280px;
                                    margin: 0 auto;
                                ">
                                    <div style="font-size: 4em; line-height: 0.9; margin-bottom: 10px;">🍰</div>
                                    <div style="font-size: 1.1em; color: #d63384; font-weight: bold; text-shadow: 2px 2px 4px rgba(0,0,0,0.2); line-height: 1.2; margin-bottom: 8px;">
                                        Вкусный десерт для вас!
                                    </div>
                                    <div style="font-size: 0.9em; color: #666; font-weight: 600; line-height: 1.3;">
                                        Напишите за какой столик принести
                                    </div>
                                </div>
                            </div>
                            <style>
                                @keyframes dessertPulse {
                                    0%, 100% { transform: scale(1); box-shadow: 0 5px 20px rgba(255, 154, 158, 0.5); }
                                    50% { transform: scale(1.03); box-shadow: 0 8px 30px rgba(255, 154, 158, 0.7); }
                                }
                            </style>
                        `;
                    }
                    // Обработка шампанского
                    else if (msg.includes('SURPRISE_CHAMPAGNE')) {
                        div.innerHTML = `
                            <div style="text-align: center; padding: 10px;">
                                <div style="font-size: 1em; color: #fff; margin-bottom: 8px; font-weight: bold;">
                                    🎁 Вам отправили сюрприз!
                                </div>
                                <div style="
                                    background: linear-gradient(135deg, #fff9e6 0%, #ffe5b4 30%, #ffd700 60%, #ffcc00 100%);
                                    border-radius: 15px;
                                    padding: 15px 20px;
                                    box-shadow: 0 8px 25px rgba(255, 215, 0, 0.6);
                                    animation: champagneBubbles 3s ease-in-out infinite;
                                    position: relative;
                                    overflow: hidden;
                                    max-width: 280px;
                                    margin: 0 auto;
                                ">
                                    <div style="font-size: 4.5em; line-height: 0.9; margin-bottom: 10px; filter: drop-shadow(0 4px 10px rgba(255,215,0,0.5));">🍾</div>
                                    <div style="font-size: 1.2em; color: #996515; font-weight: bold; text-shadow: 2px 2px 4px rgba(255,255,255,0.5); line-height: 1.2; margin-bottom: 6px;">
                                        Шампанское!
                                    </div>
                                    <div style="font-size: 1em; color: #b8860b; font-weight: 600; line-height: 1.3; margin-bottom: 6px;">
                                        За ваше знакомство! 🥂✨
                                    </div>
                                    <div style="font-size: 0.9em; color: #996515; font-weight: 600; line-height: 1.3;">
                                        Напишите за какой столик принести
                                    </div>
                                    <div style="position: absolute; top: 8px; left: 8px; font-size: 1.2em; animation: sparkle1 2s ease-in-out infinite;">✨</div>
                                    <div style="position: absolute; top: 8px; right: 8px; font-size: 1em; animation: sparkle2 2.5s ease-in-out infinite;">💫</div>
                                    <div style="position: absolute; bottom: 8px; left: 8px; font-size: 1.1em; animation: sparkle3 3s ease-in-out infinite;">⭐</div>
                                    <div style="position: absolute; bottom: 8px; right: 8px; font-size: 1.2em; animation: sparkle1 2.2s ease-in-out infinite;">✨</div>
                                </div>
                            </div>
                            <style>
                                @keyframes champagneBubbles {
                                    0%, 100% { 
                                        transform: scale(1); 
                                        box-shadow: 0 8px 25px rgba(255, 215, 0, 0.6);
                                    }
                                    50% { 
                                        transform: scale(1.03); 
                                        box-shadow: 0 12px 35px rgba(255, 215, 0, 0.8), 0 0 20px rgba(255, 255, 255, 0.4);
                                    }
                                }
                                @keyframes sparkle1 {
                                    0%, 100% { opacity: 0.3; transform: scale(0.8) rotate(0deg); }
                                    50% { opacity: 1; transform: scale(1.1) rotate(180deg); }
                                }
                                @keyframes sparkle2 {
                                    0%, 100% { opacity: 0.4; transform: translateY(0) scale(0.9); }
                                    50% { opacity: 1; transform: translateY(-5px) scale(1); }
                                }
                                @keyframes sparkle3 {
                                    0%, 100% { opacity: 0.5; transform: rotate(0deg) scale(1); }
                                    50% { opacity: 1; transform: rotate(360deg) scale(1.2); }
                                }
                            </style>
                        `;
                    }
                    // Обработка анекдота
                    else if (msg.includes('SURPRISE_JOKE')) {
                        const jokeText = msg.replace('😄 SURPRISE_JOKE', '').trim();
                        div.innerHTML = `
                            <div style="text-align: center; padding: 10px;">
                                <div style="font-size: 1em; color: #fff; margin-bottom: 8px; font-weight: bold; text-shadow: 0 0 8px rgba(255,255,255,0.5);">
                                    🎁 Вам отправили сюрприз!
                                </div>
                                <div style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 35%, #f093fb 70%, #f5576c 100%);
                                    border-radius: 15px;
                                    padding: 15px;
                                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
                                    animation: jokePulse 4s ease-in-out infinite;
                                    position: relative;
                                    overflow: hidden;
                                    max-width: 300px;
                                    margin: 0 auto;
                                ">
                                    <div style="position: absolute; top: -30px; left: -30px; width: 80px; height: 80px; background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%); border-radius: 50%; animation: shimmer1 3s ease-in-out infinite;"></div>
                                    <div style="position: absolute; bottom: -20px; right: -20px; width: 60px; height: 60px; background: radial-gradient(circle, rgba(255,255,255,0.2) 0%, transparent 70%); border-radius: 50%; animation: shimmer2 4s ease-in-out infinite;"></div>

                                    <div style="font-size: 3em; margin-bottom: 10px; filter: drop-shadow(0 3px 10px rgba(0,0,0,0.3)); animation: laughBounce 2s ease-in-out infinite; line-height: 0.9;">😄</div>
                                    <div style="font-size: 1.2em; color: #fff; font-weight: bold; margin-bottom: 10px; text-shadow: 1px 1px 4px rgba(0,0,0,0.3); line-height: 1.2;">
                                        Держите анекдот!
                                    </div>
                                    <div style="
                                        background: rgba(255, 255, 255, 0.95);
                                        border-radius: 10px;
                                        padding: 12px;
                                        font-size: 0.95em;
                                        color: #333;
                                        line-height: 1.4;
                                        white-space: pre-line;
                                        text-align: left;
                                        box-shadow: 0 3px 12px rgba(0,0,0,0.2);
                                        font-weight: 500;
                                        position: relative;
                                        z-index: 1;
                                    ">
                                        ${jokeText}
                                    </div>
                                    <div style="font-size: 1.8em; margin-top: 10px; animation: laughRotate 3s ease-in-out infinite; line-height: 0.9;">🤣</div>
                                </div>
                            </div>
                            <style>
                                @keyframes jokePulse {
                                    0%, 100% { 
                                        transform: scale(1); 
                                        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
                                    }
                                    50% { 
                                        transform: scale(1.02); 
                                        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.8), 0 0 25px rgba(245, 87, 108, 0.4);
                                    }
                                }
                                @keyframes laughBounce {
                                    0%, 100% { transform: translateY(0) scale(1); }
                                    25% { transform: translateY(-6px) scale(1.08); }
                                    75% { transform: translateY(-3px) scale(1.04); }
                                }
                                @keyframes laughRotate {
                                    0%, 100% { transform: rotate(-10deg) scale(1); }
                                    50% { transform: rotate(10deg) scale(1.08); }
                                }
                                @keyframes shimmer1 {
                                    0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.3; }
                                    50% { transform: translate(15px, 15px) scale(1.15); opacity: 0.5; }
                                }
                                @keyframes shimmer2 {
                                    0%, 100% { transform: translate(0, 0) scale(1); opacity: 0.2; }
                                    50% { transform: translate(-10px, -10px) scale(1.2); opacity: 0.4; }
                                }
                            </style>
                        `;
                    }
                    // Обработка головоломки
                    else if (msg.includes('SURPRISE_PUZZLE')) {
                        const puzzleText = msg.replace('🧠 SURPRISE_PUZZLE', '').trim();
                        div.innerHTML = `
                            <div style="text-align: center; padding: 15px;">
                                <div style="
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    border-radius: 20px;
                                    padding: 20px;
                                    box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
                                    position: relative;
                                    margin: 0 auto;
                                    max-width: 350px;
                                    border: 2px solid rgba(255, 255, 255, 0.2);
                                ">
                                    <div style="font-size: 2.5em; margin-bottom: 15px;">🧠</div>
                                    <div style="font-size: 1.3em; color: #fff; font-weight: bold; margin-bottom: 15px;">
                                        Напрягись! 💪
                                    </div>
                                    <div style="
                                        background: rgba(255, 255, 255, 0.95);
                                        border-radius: 12px;
                                        padding: 15px;
                                        font-size: 1em;
                                        color: #333;
                                        line-height: 1.5;
                                        white-space: pre-line;
                                        text-align: left;
                                        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
                                        font-weight: 500;
                                    ">
                                        ${puzzleText}
                                    </div>
                                </div>
                            </div>
                        `;
                    }
                    // Обычное текстовое сообщение
                    else {
                        div.textContent = msg;
                    }

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

                // Socket.IO обработчики отключены для продакшн
                console.log('⚠️ Socket.IO обработчики отключены, используется только AJAX');

                // Обработчик отправки сообщения
                document.getElementById('chat-form').onsubmit = function(e) {
                    e.preventDefault();
                    const input = document.getElementById('message-input');
                    const msg = input.value;
                    if (msg.trim()) {
                        if (socketConnected) {
                            console.log('📤 Отправка сообщения через Socket.IO...');
                            socket.emit('send_message', {room: chat_key, text: msg, sender: user_id});
                        } else {
                            console.log('📤 Отправка сообщения через AJAX (Socket.IO недоступен)...');
                            // Fallback на AJAX
                            fetch('/chat/' + other_user_id, {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/x-www-form-urlencoded',
                                },
                                body: 'message=' + encodeURIComponent(msg)
                            })
                            .then(response => {
                                if (response.ok) {
                                    console.log('✅ Сообщение отправлено через AJAX');
                                    // Добавляем сообщение локально
                                    addMessage(msg, user_id);
                                } else {
                                    console.error('❌ Ошибка отправки через AJAX');
                                }
                            })
                            .catch(error => {
                                console.error('❌ Ошибка AJAX:', error);
                            });
                        }

                        // Очищаем поле ввода
                        input.value = '';

                        console.log('✅ Сообщение отправлено');
                    }
                };

                // Индикатор печати
                let typingTimer;
                const typingIndicator = document.getElementById('typing-indicator');

                // Socket.IO typing отключен для продакшн
                document.getElementById('message-input').addEventListener('input', function() {
                    // Typing индикатор отключен (Socket.IO не работает)
                    console.log('⚠️ Typing индикатор отключен');
                });

                // Socket.IO typing обработчик отключен
                console.log('⚠️ Socket.IO typing отключен');

                // Загружаем ВСЕ сообщения при открытии страницы через JavaScript
                // Это нужно для правильной обработки маркеров сюрпризов
                function loadInitialMessages() {
                    fetch(`/chat_history/${other_user_id}`)
                        .then(response => response.json())
                        .then(messages => {
                            console.log(`📥 Загружено сообщений: ${messages.length}`);
                            messages.forEach(msg => {
                                addMessage(msg.text, msg.sender, msg.timestamp);
                            });
                            lastMessageCount = messages.length;
                            if (messages.length > 0) {
                                lastMessageTimestamp = messages[messages.length - 1].timestamp;
                            }
                        })
                        .catch(error => {
                            console.error('Ошибка при загрузке истории:', error);
                        });
                }

                // Загружаем историю при открытии страницы
                loadInitialMessages();

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
    ИСПРАВЛЕНО: Добавлена проверка оплаты и активности профиля
    """
    try:
        profile = Profile.query.get(user_id)
        exists = profile is not None
        
        # Дополнительные проверки для существующего профиля
        is_paid = False
        is_active = False
        remaining_time = None
        
        if profile:
            is_paid = profile.is_paid
            # Проверяем активность профиля
            try:
                remaining_time = get_profile_lifetime_remaining(user_id)
                is_active = remaining_time != 'Истекла'
            except:
                is_active = True  # Если не можем проверить, считаем активным
        
        return jsonify({
            'success': True,
            'exists': exists,
            'is_paid': is_paid,
            'is_active': is_active,
            'remaining_time': remaining_time,
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
        # 🔐 БЕЗОПАСНАЯ УСТАНОВКА КУКИ ДЛЯ HTTPS
        response.set_cookie('user_id', user_id, max_age=365 * 24 * 60 * 60,
                            secure=False, httponly=False, samesite='Lax')  # 1 год, совместимость HTTP/HTTPS

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


# ============================================================================
# QR-КОД АВТОРИЗАЦИЯ API ENDPOINTS
# ============================================================================

@app.route('/api/generate-qr-login', methods=['POST'])
@require_profile()
def api_generate_qr_login():
    """API для генерации QR-код токена для входа"""
    try:
        user_id = request.cookies.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Пользователь не авторизован'}), 401

        # Очищаем просроченные токены
        cleanup_expired_qr_tokens()

        # Генерируем новый токен
        token = generate_qr_login_token(user_id)

        # Создаем URL для QR-кода
        qr_url = f"https://ятута.рф/qr-login/{token}"

        return jsonify({
            'success': True,
            'token': token,
            'qr_url': qr_url,
            'expires_in_minutes': 10
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/qr-login/<string:user_id>')
def qr_login_page(user_id):
    """Страница автоматического входа по QR-коду"""
    try:
        # Проверяем, существует ли пользователь
        profile = Profile.query.get(user_id)

        if not profile:
            return render_template_string('''
                <!DOCTYPE html>
                <html>
                <head>
                    <title>QR-код вход - ятута.рф</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                </head>
                <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5;">
                    <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto;">
                        <h2 style="color: #e74c3c;">❌ Профиль не найден</h2>
                        <p>Пользователь не найден или анкета удалена</p>
                        <a href="/" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">На главную</a>
                    </div>
                </body>
                </html>
            ''')

        # Устанавливаем cookie и перенаправляем
        response = make_response(redirect(url_for('my_profile')))
        # 🔐 БЕЗОПАСНАЯ УСТАНОВКА КУКИ ДЛЯ HTTPS
        response.set_cookie('user_id', profile.id, max_age=365 * 24 * 60 * 60,
                            secure=False, httponly=False, samesite='Lax')  # Cookie на год, совместимость HTTP/HTTPS

        return response

    except Exception as e:
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>QR-код вход - ятута.рф</title>
                <meta name="viewport" content="width=device-width, initial-scale=1.0">
            </head>
            <body style="font-family: Arial, sans-serif; text-align: center; padding: 50px; background: #f5f5f5;">
                <div style="background: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); max-width: 400px; margin: 0 auto;">
                    <h2 style="color: #e74c3c;">❌ Ошибка сервера</h2>
                    <p>Произошла ошибка при входе</p>
                    <a href="/" style="background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">На главную</a>
                </div>
            </body>
            </html>
        ''')


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

    if not data:
        return jsonify({"error": "Неверные данные"}), 400

    # Поддерживаем обновление как звуковых уведомлений, так и черно-белого режима
    sound_enabled = data.get('sound_notifications')
    grayscale_enabled = data.get('grayscale_mode')

    if sound_enabled is None and grayscale_enabled is None:
        return jsonify({"error": "Не указаны настройки для обновления"}), 400

    success = update_user_settings(user_id, sound_enabled, grayscale_enabled)

    if success:
        result = {"success": True}
        if sound_enabled is not None:
            result["sound_notifications"] = sound_enabled
        if grayscale_enabled is not None:
            result["grayscale_mode"] = grayscale_enabled
        return jsonify(result)
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

    # Генерируем QR-код на сервере
    qr_code_url = generate_qr_code_server_side(user_id) if user_id else None
    qr_login_url = get_user_qr_url(user_id) if user_id else None
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

                /* Стили для черно-белого режима */
                .grayscale-mode {
                    filter: grayscale(100%);
                    -webkit-filter: grayscale(100%);
                    -moz-filter: grayscale(100%);
                    -ms-filter: grayscale(100%);
                    -o-filter: grayscale(100%);
                }

                .grayscale-mode * {
                    filter: grayscale(100%);
                    -webkit-filter: grayscale(100%);
                    -moz-filter: grayscale(100%);
                    -ms-filter: grayscale(100%);
                    -o-filter: grayscale(100%);
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
                <div class="setting-item">
                    <div>
                        <div class="setting-label">⚫ Черно-белый режим</div>
                        <div class="setting-description">Переключить сайт в черно-белый режим</div>
                    </div>
                    <button id="grayscale-toggle" class="bell-button" onclick="toggleGrayscale()" style="background: #6c757d;">⚫</button>
                </div>
            </div>

            <div class="settings-card" style="margin-top: 20px;">
                <div class="setting-item">
                    <div>
                        <div class="setting-label">📱 QR-код для входа</div>
                        <div class="setting-description">Отсканируйте QR-код для входа с другого устройства</div>
                    </div>
                    <button class="bell-button" onclick="toggleQR()" style="background: #3498db;">📱</button>
                </div>
                <div id="qr-container" style="display: none; text-align: center; margin-top: 20px;">
                    <div id="qr-code" style="width: 200px; height: 200px; margin: 0 auto; background: white; border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 2em;">
                        {% if qr_code_url %}
                        <img src="{{ qr_code_url }}" alt="QR Code" style="width: 200px; height: 200px; border-radius: 10px;">
                        {% else %}
                        🔄 Загрузка QR-кода...
                        {% endif %}
                    </div>
                    <!-- URL ссылка скрыта по запросу пользователя -->
                    <div style="margin-top: 15px; color: #ccc; font-size: 0.9em;">
                        Отсканируйте QR-код камерой телефона или откройте ссылку на другом устройстве
                    </div>
                </div>
            </div>

            <script>
                let audioContext = null;
                let userInteracted = false;
                let soundEnabled = true;
                let grayscaleEnabled = false;

                // Загружаем настройки при загрузке страницы
                window.addEventListener('load', function() {
                    loadSettings();
                });

                // Загрузка настроек
                function loadSettings() {
                    fetch('/api/get_settings')
                        .then(response => {
                            if (!response.ok) {
                                throw new Error(`HTTP error! status: ${response.status}`);
                            }
                            return response.json();
                        })
                        .then(settings => {
                            soundEnabled = settings.sound_notifications;
                            grayscaleEnabled = settings.grayscale_mode || false;
                            updateBellAppearance();
                            updateGrayscaleAppearance();
                            applyGrayscaleMode();
                            console.log('📋 Настройки загружены:', settings);
                            console.log('⚫ Черно-белый режим:', grayscaleEnabled ? 'включен' : 'выключен');
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

                // Обновление внешнего вида кнопки черно-белого режима
                function updateGrayscaleAppearance() {
                    const grayscaleButton = document.getElementById('grayscale-toggle');
                    if (grayscaleEnabled) {
                        grayscaleButton.textContent = '⚫';
                        grayscaleButton.style.background = '#000';
                        grayscaleButton.style.color = '#fff';
                    } else {
                        grayscaleButton.textContent = '⚪';
                        grayscaleButton.style.background = '#6c757d';
                        grayscaleButton.style.color = '#fff';
                    }
                }

                // Применение черно-белого режима к странице
                function applyGrayscaleMode() {
                    if (grayscaleEnabled) {
                        document.body.classList.add('grayscale-mode');
                    } else {
                        document.body.classList.remove('grayscale-mode');
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

                // Переключение черно-белого режима
                function toggleGrayscale() {
                    grayscaleEnabled = !grayscaleEnabled;

                    // Обновляем внешний вид
                    updateGrayscaleAppearance();
                    applyGrayscaleMode();

                    // Сохраняем настройки
                    fetch('/api/update_settings', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            grayscale_mode: grayscaleEnabled
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('✅ Настройки черно-белого режима сохранены:', data);
                            // Принудительно применяем режим после сохранения
                            setTimeout(() => {
                                applyGrayscaleMode();
                                console.log('🔄 Черно-белый режим принудительно применен');
                            }, 100);
                        } else {
                            console.error('❌ Ошибка сохранения настроек черно-белого режима:', data.error);
                        }
                    })
                    .catch(error => {
                        console.error('❌ Ошибка сохранения настроек черно-белого режима:', error);
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

                // Функция для переключения QR-кода
                function toggleQR() {
                    const qrContainer = document.getElementById('qr-container');

                    if (qrContainer.style.display === 'none') {
                        qrContainer.style.display = 'block';
                    } else {
                        qrContainer.style.display = 'none';
                    }
                }

            </script>
        </body>
        </html>
    ''', navbar=navbar, get_starry_night_css=get_starry_night_css, qr_code_url=qr_code_url, qr_login_url=qr_login_url)


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
                print(
                    f"   ❌ {profile.name} ({profile.id[:8]}...): создана {created_at.strftime('%Y-%m-%d %H:%M:%S')}, возраст {age_hours:.2f}ч - УДАЛИТЬ")
            else:
                print(
                    f"   ✅ {profile.name} ({profile.id[:8]}...): создана {created_at.strftime('%Y-%m-%d %H:%M:%S')}, возраст {age_hours:.2f}ч - ОК")

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
# QR-КОД СТРАНИЦА ДЛЯ ВХОДА
# ============================================================================

@app.route('/qr-login-generator')
@require_profile()
def qr_login_generator():
    """Страница для генерации QR-кода для входа с другого устройства"""
    user_id = request.cookies.get('user_id')
    profile = Profile.query.get(user_id)

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
            <title>QR-код вход - ятута.рф</title>
            <style>
                ''' + get_starry_night_css() + '''
                body { max-width: 500px; margin: 0 auto; padding: 20px; }
                h1 { 
                    color: #fff; 
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                    text-align: center;
                }
                .qr-container {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    padding: 30px;
                    text-align: center;
                    margin: 20px 0;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                .qr-code {
                    width: 200px;
                    height: 200px;
                    margin: 20px auto;
                    background: white;
                    border-radius: 10px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    font-size: 2em;
                }
                .qr-url {
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 10px;
                    padding: 15px;
                    margin: 20px 0;
                    word-break: break-all;
                    font-family: monospace;
                    font-size: 0.9em;
                    color: #fff;
                }
                .generate-btn {
                    background: linear-gradient(90deg, #3498db 0%, #2980b9 100%);
                    color: white;
                    border: none;
                    border-radius: 25px;
                    padding: 15px 30px;
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    margin: 10px;
                }
                .generate-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 5px 15px rgba(52, 152, 219, 0.4);
                }
                .info-text {
                    color: #fff;
                    text-align: center;
                    margin: 20px 0;
                    line-height: 1.6;
                }
                .timer {
                    color: #f39c12;
                    font-weight: bold;
                    font-size: 1.2em;
                    margin: 10px 0;
                }
                .instructions {
                    background: rgba(255, 255, 255, 0.05);
                    border-radius: 10px;
                    padding: 20px;
                    margin: 20px 0;
                    color: #fff;
                }
                .instructions h3 {
                    color: #3498db;
                    margin-top: 0;
                }
                .instructions ol {
                    text-align: left;
                    padding-left: 20px;
                }
                .instructions li {
                    margin: 10px 0;
                }
            </style>
            <script src="https://cdn.jsdelivr.net/npm/qrcode@1.5.3/build/qrcode.min.js"></script>
        </head>
        <body>
            {{ navbar|safe }}
            <h1>📱 QR-код для входа</h1>

            <div class="instructions">
                <h3>Как войти с другого устройства:</h3>
                <ol>
                    <li>Нажмите "Сгенерировать QR-код"</li>
                    <li>Отсканируйте QR-код камерой телефона</li>
                    <li>Или откройте ссылку на другом устройстве</li>
                    <li>QR-код действителен 10 минут</li>
                </ol>
            </div>

            <div class="qr-container" id="qrContainer" style="display: none;">
                <div class="qr-code" id="qrCode"></div>
                <!-- URL ссылка скрыта по запросу пользователя -->
                <!-- <div class="qr-url" id="qrUrl"></div> -->
                <div class="timer" id="timer">⏰ Осталось: <span id="timeLeft">10:00</span></div>
            </div>

            <div style="text-align: center;">
                <button class="generate-btn" onclick="generateQR()">🔗 Сгенерировать QR-код</button>
                <button class="generate-btn" onclick="refreshQR()" style="background: linear-gradient(90deg, #e74c3c 0%, #c0392b 100%);">🔄 Обновить</button>
            </div>

            <div class="info-text">
                <p>💡 <strong>Совет:</strong> QR-код позволяет войти в ваш профиль с любого устройства без повторной регистрации!</p>
            </div>

            <script>
                let currentToken = null;
                let countdownInterval = null;

                function generateQR() {
                    fetch('/api/generate-qr-login', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            currentToken = data.token;
                            const qrUrl = data.qr_url;

                            // Показываем контейнер
                            document.getElementById('qrContainer').style.display = 'block';

                            // Генерируем QR-код
                            const qrCodeElement = document.getElementById('qrCode');
                            qrCodeElement.innerHTML = '';

                            QRCode.toCanvas(qrCodeElement, qrUrl, {
                                width: 200,
                                height: 200,
                                color: {
                                    dark: '#000000',
                                    light: '#FFFFFF'
                                }
                            }, function (error) {
                                if (error) {
                                    console.error('Ошибка генерации QR-кода:', error);
                                    qrCodeElement.innerHTML = '❌ Ошибка QR-кода';
                                } else {
                                    console.log('✅ QR-код сгенерирован');
                                }
                            });

                            // URL скрыт по запросу пользователя
                            // document.getElementById('qrUrl').textContent = qrUrl;

                            // Запускаем таймер
                            startCountdown(10 * 60); // 10 минут

                        } else {
                            alert('Ошибка: ' + (data.error || 'Неизвестная ошибка'));
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка:', error);
                        alert('Ошибка при генерации QR-кода');
                    });
                }

                function refreshQR() {
                    if (currentToken) {
                        generateQR();
                    }
                }

                function startCountdown(seconds) {
                    if (countdownInterval) {
                        clearInterval(countdownInterval);
                    }

                    countdownInterval = setInterval(() => {
                        const minutes = Math.floor(seconds / 60);
                        const secs = seconds % 60;
                        const timeString = `${minutes}:${secs.toString().padStart(2, '0')}`;

                        document.getElementById('timeLeft').textContent = timeString;

                        if (seconds <= 0) {
                            clearInterval(countdownInterval);
                            document.getElementById('qrContainer').style.display = 'none';
                            document.getElementById('timeLeft').textContent = 'Истекло';
                        }

                        seconds--;
                    }, 1000);
                }

                // Автоматически генерируем QR-код при загрузке страницы
                document.addEventListener('DOMContentLoaded', function() {
                    generateQR();
                });
            </script>
        </body>
        </html>
    ''')


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
    payment_type = request.args.get('type', 'profile')  # profile или surprise

    # ===================================================================
    # ОБРАБОТКА ОПЛАТЫ ФУНКЦИИ "УДИВИТЬ"
    # ===================================================================
    if payment_type == 'surprise':
        try:
            print(f"💰 Обрабатываем оплату функции 'Удивить' для пользователя: {user_id}")

            profile = Profile.query.get(user_id)
            if profile:
                profile.surprise_feature_paid = True
                profile.surprise_feature_payment_date = datetime.utcnow()
                db.session.commit()
                print(f"✅ Функция 'Удивить' активирована для {user_id}")

                # Перенаправляем на страницу visitors
                return '''
                <!DOCTYPE html>
                <html lang="ru">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>Оплата успешна</title>
                    <style>
                        ''' + get_starry_night_css() + '''
                        body {
                            text-align: center;
                            padding: 20px;
                            font-family: Arial, sans-serif;
                        }
                        .success-container {
                            max-width: 500px;
                            margin: 100px auto;
                            background: rgba(255, 255, 255, 0.95);
                            padding: 40px;
                            border-radius: 20px;
                            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                        }
                        .success-icon { font-size: 5em; margin-bottom: 20px; }
                        h1 { color: #4CAF50; margin-bottom: 15px; }
                        p { color: #666; font-size: 1.1em; margin-bottom: 30px; }
                    </style>
                </head>
                <body>
                    <div class="success-container">
                        <div class="success-icon">✨</div>
                        <h1>Оплата успешна!</h1>
                        <p>Функция "Удивить" активирована!<br>Теперь вы можете отправлять сюрпризы любым посетителям.</p>
                        <p style="color: #999; font-size: 0.9em;">Перенаправление на страницу посетителей...</p>
                    </div>
                    <script>
                        setTimeout(function() {
                            window.location.href = '/visitors?surprise_paid=1';
                        }, 2000);
                    </script>
                </body>
                </html>
                '''
            else:
                print(f"❌ Профиль {user_id} не найден")
        except Exception as e:
            print(f"❌ Ошибка активации функции 'Удивить': {e}")
            db.session.rollback()

    # ===================================================================
    # ОБРАБОТКА ОПЛАТЫ ПРОФИЛЯ (существующая логика)
    # ===================================================================
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
                // 🔐 БЕЗОПАСНАЯ УСТАНОВКА КУКИ ДЛЯ HTTPS
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

            # Находим пользователя по payment_id
            payment = Payment.query.filter_by(yookassa_payment_id=payment_id).first()
            if not payment:
                print(f"❌ Webhook: платеж {payment_id} не найден в базе данных")
                return jsonify({'status': 'error', 'message': 'Платеж не найден'}), 404

            user_id = payment.user_id
            print(f"✅ Webhook: найден пользователь {user_id} для платежа {payment_id}")

            process_payment_completion(user_id, payment_id, 'succeeded')
            return jsonify({'status': 'success'})
        elif event == 'payment.canceled' and payment_id:
            print(f"⚠️ Webhook: платеж {payment_id} отменен")

            # Находим пользователя по payment_id
            payment = Payment.query.filter_by(yookassa_payment_id=payment_id).first()
            if payment:
                user_id = payment.user_id
                print(f"✅ Webhook: найден пользователь {user_id} для отмененного платежа {payment_id}")
                process_payment_completion(user_id, payment_id, 'canceled')

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


@app.route('/test_qr_login')
def test_qr_login():
    """Тестовая страница для QR-код авторизации"""
    return send_from_directory('.', 'test_qr_login.html')


@app.route('/test_qr_logo')
def test_qr_logo():
    """Тестовая страница для проверки логотипа в QR-коде"""
    try:
        # Создаем тестовый QR-код с логотипом
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data('https://ятута.рф/qr-login/test-user')
        qr.make(fit=True)

        img = qr.make_image(fill_color='black', back_color='white')
        img = add_text_below_qr(img)

        # Сохраняем в буфер
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)

        return make_response(img_buffer.getvalue(), 200, {
            'Content-Type': 'image/png',
            'Cache-Control': 'no-cache'
        })

    except Exception as e:
        return f"Ошибка: {e}", 500


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