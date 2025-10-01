#!/usr/bin/env python3
"""
Альтернативная версия Flask приложения с улучшенными настройками для HTTPS
"""

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
from PIL import Image
import io
import ssl

# Создаем приложение с правильными настройками для HTTPS
app = Flask(__name__)
app.secret_key = 'super-secret-key'

# Настройки для HTTPS
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['SERVER_NAME'] = None

# Настройки загрузки файлов
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'heic', 'heif'}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

# Создаем папку для загрузок
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация базы данных
db = SQLAlchemy(app)

# SocketIO с правильными настройками для HTTPS
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Модель профиля
class Profile(db.Model):
    id = db.Column(db.String(36), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    hobbies = db.Column(db.Text, nullable=False)
    goal = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100))
    venue = db.Column(db.String(200))
    photo = db.Column(db.String(255))
    likes = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# Функции для работы с фотографиями
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_photo(file, user_id):
    """Сохраняет фотографию и возвращает имя файла"""
    print(f"🔄 Сохранение фотографии для пользователя {user_id}")
    print(f"📁 Имя файла: {file.filename}")
    print(f"📏 Размер файла: {file.content_length if hasattr(file, 'content_length') else 'неизвестно'}")
    
    if file and allowed_file(file.filename):
        try:
            # Простое сохранение без сжатия для отладки
            filename = f"{user_id}.jpg"
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            
            # Сохраняем файл
            file.save(file_path)
            
            print(f"✅ Фотография сохранена: {filename}")
            return filename
                
        except Exception as e:
            print(f"❌ Ошибка при сохранении: {e}")
            import traceback
            traceback.print_exc()
            return None
    else:
        print(f"❌ Файл не прошел валидацию")
    return None

# Заголовки безопасности
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    
    return response

# Обработчики ошибок
@app.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'Файл слишком большой. Максимальный размер: 50MB'
    }), 413

@app.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Ошибка при загрузке файла'
    }), 400

# Маршрут для отладки загрузки
@app.route('/debug_upload', methods=['GET', 'POST'])
def debug_upload():
    if request.method == 'POST':
        print(f"🔍 DEBUG: Метод: {request.method}")
        print(f"🔍 DEBUG: Content-Type: {request.content_type}")
        print(f"🔍 DEBUG: Файлы: {list(request.files.keys())}")
        print(f"🔍 DEBUG: HTTPS: {request.is_secure}")
        
        if 'photo' in request.files:
            photo_file = request.files['photo']
            print(f"🔍 DEBUG: Файл: {photo_file.filename}")
            
            result = save_photo(photo_file, 'debug_user')
            return jsonify({
                'success': True,
                'debug_info': {
                    'filename': photo_file.filename,
                    'is_secure': request.is_secure,
                    'save_result': result
                }
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Файл не найден'
            })
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Debug Upload HTTPS</title>
    </head>
    <body>
        <h2>Отладка загрузки файлов (HTTPS)</h2>
        <form action="/debug_upload" method="post" enctype="multipart/form-data">
            <input type="file" name="photo" accept="image/*" required>
            <button type="submit">Загрузить</button>
        </form>
        <div id="result"></div>
        
        <script>
        document.querySelector('form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const resultDiv = document.getElementById('result');
            
            fetch('/debug_upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                resultDiv.innerHTML = '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
            })
            .catch(error => {
                resultDiv.innerHTML = '<p style="color: red;">Ошибка: ' + error.message + '</p>';
            });
        });
        </script>
    </body>
    </html>
    '''

# Простой маршрут для проверки
@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>HTTPS Test</title>
    </head>
    <body>
        <h1>HTTPS Flask Server</h1>
        <p>Сервер работает с HTTPS!</p>
        <a href="/debug_upload">Тест загрузки файлов</a>
    </body>
    </html>
    '''

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    print("🔒 Запуск HTTPS сервера...")
    print("📝 URL: https://192.168.255.137:5000")
    
    # Создаем SSL контекст
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_default_certs()
    
    # Запуск с HTTPS
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                allow_unsafe_werkzeug=True, ssl_context='adhoc') 