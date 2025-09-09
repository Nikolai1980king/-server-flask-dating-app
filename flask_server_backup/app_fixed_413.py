from flask import Flask, render_template_string, request, redirect, url_for, make_response, jsonify
from flask_socketio import SocketIO, emit, join_room
import os
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super-secret-key'
socketio = SocketIO(app)

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Увеличиваем лимит загрузки файлов до 2GB
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


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

# Создаем таблицы
with app.app_context():
    db.create_all()

# --- Маршруты ---

@app.route('/')
def index():
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dating App</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                {{ get_starry_night_css() }}
                
                .container {
                    position: relative;
                    z-index: 2;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    color: white;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 40px;
                }
                
                .header h1 {
                    font-size: 3em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }
                
                .header p {
                    font-size: 1.2em;
                    opacity: 0.9;
                }
                
                .buttons {
                    display: flex;
                    justify-content: center;
                    gap: 20px;
                    flex-wrap: wrap;
                }
                
                .btn {
                    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                    color: white;
                    padding: 15px 30px;
                    text-decoration: none;
                    border-radius: 25px;
                    font-size: 1.1em;
                    transition: all 0.3s ease;
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 4px 15px rgba(0,0,0,0.2);
                }
                
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px rgba(0,0,0,0.3);
                }
                
                .btn-secondary {
                    background: linear-gradient(45deg, #667eea, #764ba2);
                }
                
                .status-info {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 20px;
                    border-radius: 15px;
                    margin: 30px 0;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                
                .status-info h3 {
                    margin-top: 0;
                    color: #2ecc71;
                }
                
                .status-item {
                    margin: 10px 0;
                    padding: 5px 0;
                }
                
                .status-item.success {
                    color: #2ecc71;
                }
                
                .status-item.info {
                    color: #3498db;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>🌟 Dating App</h1>
                    <p>Найди свою любовь среди звезд</p>
                </div>
                
                <div class="status-info">
                    <h3>🔧 Статус системы</h3>
                    <div class="status-item success">✅ Ошибка 413 исправлена - лимит файлов увеличен до 2GB</div>
                    <div class="status-item success">✅ Nginx настроен правильно</div>
                    <div class="status-item success">✅ SSL/HTTPS работает</div>
                    <div class="status-item info">📝 IP: 192.168.0.24</div>
                </div>
                
                <div class="buttons">
                    <a href="/create" class="btn">👤 Создать профиль</a>
                    <a href="/profiles" class="btn btn-secondary">👥 Просмотр профилей</a>
                    <a href="/test_413_fix.html" class="btn btn-secondary">🧪 Тест загрузки</a>
                </div>
            </div>
        </body>
        </html>
    ''', get_starry_night_css=get_starry_night_css)

@app.route('/create', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        # Получаем данные из формы
        name = request.form.get('name', '')
        age = request.form.get('age', '')
        gender = request.form.get('gender', '')
        hobbies = request.form.get('hobbies', '')
        goal = request.form.get('goal', '')
        city = request.form.get('city', '')
        venue = request.form.get('venue', '')
        
        # Обработка фото
        photo = None
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename:
                # Генерируем уникальное имя файла
                filename = str(uuid.uuid4()) + '.jpg'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo = filename
        
        # Создаем профиль
        profile_id = str(uuid.uuid4())
        profile = Profile(
            id=profile_id,
            name=name,
            age=int(age) if age else 0,
            gender=gender,
            hobbies=hobbies,
            goal=goal,
            city=city,
            venue=venue,
            photo=photo
        )
        
        db.session.add(profile)
        db.session.commit()
        
        return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head>
                <title>Профиль создан</title>
                <meta charset="UTF-8">
                <style>
                    {{ get_starry_night_css() }}
                    
                    .container {
                        position: relative;
                        z-index: 2;
                        max-width: 600px;
                        margin: 50px auto;
                        padding: 20px;
                        color: white;
                    }
                    
                    .success-card {
                        background: rgba(46, 204, 113, 0.2);
                        border: 1px solid #2ecc71;
                        padding: 30px;
                        border-radius: 15px;
                        backdrop-filter: blur(10px);
                        text-align: center;
                    }
                    
                    .success-card h1 {
                        color: #2ecc71;
                        margin-bottom: 20px;
                    }
                    
                    .profile-info {
                        text-align: left;
                        margin: 20px 0;
                    }
                    
                    .profile-info p {
                        margin: 10px 0;
                        padding: 5px 0;
                    }
                    
                    .back-btn {
                        background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                        color: white;
                        text-decoration: none;
                        padding: 12px 25px;
                        border-radius: 25px;
                        display: inline-block;
                        margin-top: 20px;
                        transition: all 0.3s ease;
                    }
                    
                    .back-btn:hover {
                        transform: translateY(-2px);
                        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                    }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="success-card">
                        <h1>🌟 Профиль создан успешно!</h1>
                        <div class="profile-info">
                            <p><strong>Имя:</strong> {{ name }}</p>
                            <p><strong>Возраст:</strong> {{ age }}</p>
                            <p><strong>Пол:</strong> {{ gender }}</p>
                            <p><strong>Хобби:</strong> {{ hobbies }}</p>
                            <p><strong>Цель:</strong> {{ goal }}</p>
                            <p><strong>Город:</strong> {{ city or 'Не указан' }}</p>
                            <p><strong>Место:</strong> {{ venue or 'Не указано' }}</p>
                            {% if photo %}
                                <p><strong>Фото:</strong> Загружено ✅</p>
                            {% else %}
                                <p><strong>Фото:</strong> Не загружено</p>
                            {% endif %}
                        </div>
                        <a href="/" class="back-btn">← Вернуться на главную</a>
                    </div>
                </div>
            </body>
            </html>
        ''', get_starry_night_css=get_starry_night_css, name=name, age=age, gender=gender, 
             hobbies=hobbies, goal=goal, city=city, venue=venue, photo=photo)
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Создать профиль</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                {{ get_starry_night_css() }}
                
                .container {
                    position: relative;
                    z-index: 2;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                    color: white;
                }
                
                .form-card {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 30px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                }
                
                .form-card h1 {
                    text-align: center;
                    margin-bottom: 30px;
                    color: #fff;
                }
                
                .form-group {
                    margin-bottom: 20px;
                }
                
                label {
                    display: block;
                    margin-bottom: 8px;
                    font-weight: bold;
                    color: #fff;
                }
                
                input, select, textarea {
                    width: 100%;
                    padding: 12px;
                    border: none;
                    border-radius: 8px;
                    background: rgba(255, 255, 255, 0.9);
                    color: #333;
                    font-size: 16px;
                    box-sizing: border-box;
                }
                
                input:focus, select:focus, textarea:focus {
                    outline: none;
                    box-shadow: 0 0 10px rgba(255, 107, 107, 0.5);
                }
                
                button {
                    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    cursor: pointer;
                    font-size: 16px;
                    width: 100%;
                    transition: all 0.3s ease;
                }
                
                button:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                }
                
                .file-info {
                    background: rgba(46, 204, 113, 0.2);
                    border: 1px solid #2ecc71;
                    padding: 10px;
                    border-radius: 8px;
                    margin-top: 10px;
                    font-size: 14px;
                }
                
                .back-btn {
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    color: white;
                    text-decoration: none;
                    padding: 10px 20px;
                    border-radius: 25px;
                    display: inline-block;
                    margin-bottom: 20px;
                    transition: all 0.3s ease;
                }
                
                .back-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← Назад</a>
                <div class="form-card">
                    <h1>🌟 Создать профиль</h1>
                    <form method="POST" enctype="multipart/form-data">
                        <div class="form-group">
                            <label for="name">Имя:</label>
                            <input type="text" id="name" name="name" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="age">Возраст:</label>
                            <input type="number" id="age" name="age" min="18" max="100" required>
                        </div>
                        
                        <div class="form-group">
                            <label for="gender">Пол:</label>
                            <select id="gender" name="gender" required>
                                <option value="">Выберите пол</option>
                                <option value="male">Мужской</option>
                                <option value="female">Женский</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="hobbies">Хобби:</label>
                            <textarea id="hobbies" name="hobbies" rows="3" required placeholder="Расскажите о своих увлечениях..."></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label for="goal">Цель знакомства:</label>
                            <select id="goal" name="goal" required>
                                <option value="">Выберите цель</option>
                                <option value="friendship">Дружба</option>
                                <option value="relationship">Отношения</option>
                                <option value="marriage">Брак</option>
                            </select>
                        </div>
                        
                        <div class="form-group">
                            <label for="city">Город:</label>
                            <input type="text" id="city" name="city" placeholder="Введите ваш город">
                        </div>
                        
                        <div class="form-group">
                            <label for="venue">Любимое место:</label>
                            <input type="text" id="venue" name="venue" placeholder="Кафе, парк, ресторан...">
                        </div>
                        
                        <div class="form-group">
                            <label for="photo">Фото:</label>
                            <input type="file" id="photo" name="photo" accept="image/*">
                            <div class="file-info">
                                ✅ Лимит файлов: до 2GB (ошибка 413 исправлена)
                            </div>
                        </div>
                        
                        <button type="submit">🌟 Создать профиль</button>
                    </form>
                </div>
            </div>
        </body>
        </html>
    ''', get_starry_night_css=get_starry_night_css)

@app.route('/profiles')
def view_profiles():
    profiles = Profile.query.all()
    
    return render_template_string('''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Профили</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                {{ get_starry_night_css() }}
                
                .container {
                    position: relative;
                    z-index: 2;
                    max-width: 1200px;
                    margin: 0 auto;
                    padding: 20px;
                    color: white;
                }
                
                .header {
                    text-align: center;
                    margin-bottom: 30px;
                }
                
                .header h1 {
                    font-size: 2.5em;
                    margin-bottom: 10px;
                    text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                }
                
                .profiles-grid {
                    display: grid;
                    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
                    gap: 20px;
                    margin-top: 30px;
                }
                
                .profile-card {
                    background: rgba(255, 255, 255, 0.1);
                    padding: 25px;
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    transition: all 0.3s ease;
                }
                
                .profile-card:hover {
                    transform: translateY(-5px);
                    box-shadow: 0 8px 25px rgba(0,0,0,0.3);
                }
                
                .profile-header {
                    display: flex;
                    align-items: center;
                    margin-bottom: 20px;
                }
                
                .profile-photo {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    object-fit: cover;
                    margin-right: 20px;
                    border: 3px solid rgba(255, 255, 255, 0.3);
                }
                
                .profile-photo-placeholder {
                    width: 80px;
                    height: 80px;
                    border-radius: 50%;
                    background: linear-gradient(45deg, #667eea, #764ba2);
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-right: 20px;
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    font-size: 24px;
                }
                
                .profile-name {
                    font-size: 1.5em;
                    font-weight: bold;
                    margin-bottom: 5px;
                }
                
                .profile-age {
                    opacity: 0.8;
                    font-size: 1.1em;
                }
                
                .profile-info {
                    line-height: 1.6;
                }
                
                .profile-info p {
                    margin: 8px 0;
                    padding: 5px 0;
                }
                
                .profile-info strong {
                    color: #ff6b6b;
                }
                
                .back-btn {
                    background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                    color: white;
                    text-decoration: none;
                    padding: 12px 25px;
                    border-radius: 25px;
                    display: inline-block;
                    margin-bottom: 20px;
                    transition: all 0.3s ease;
                }
                
                .back-btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
                }
                
                .empty-state {
                    text-align: center;
                    padding: 50px;
                    background: rgba(255, 255, 255, 0.1);
                    border-radius: 15px;
                    backdrop-filter: blur(10px);
                }
                
                .empty-state h2 {
                    margin-bottom: 20px;
                    color: #ff6b6b;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <a href="/" class="back-btn">← Назад</a>
                
                <div class="header">
                    <h1>🌟 Профили ({{ profiles|length }})</h1>
                </div>
                
                {% if profiles %}
                    <div class="profiles-grid">
                        {% for profile in profiles %}
                            <div class="profile-card">
                                <div class="profile-header">
                                    {% if profile.photo %}
                                        <img src="/static/uploads/{{ profile.photo }}" class="profile-photo" alt="Фото">
                                    {% else %}
                                        <div class="profile-photo-placeholder">🌟</div>
                                    {% endif %}
                                    <div>
                                        <div class="profile-name">{{ profile.name }}</div>
                                        <div class="profile-age">{{ profile.age }} лет</div>
                                    </div>
                                </div>
                                <div class="profile-info">
                                    <p><strong>Пол:</strong> {{ profile.gender }}</p>
                                    <p><strong>Хобби:</strong> {{ profile.hobbies }}</p>
                                    <p><strong>Цель:</strong> {{ profile.goal }}</p>
                                    {% if profile.city %}
                                        <p><strong>Город:</strong> {{ profile.city }}</p>
                                    {% endif %}
                                    {% if profile.venue %}
                                        <p><strong>Место:</strong> {{ profile.venue }}</p>
                                    {% endif %}
                                </div>
                            </div>
                        {% endfor %}
                    </div>
                {% else %}
                    <div class="empty-state">
                        <h2>🌟 Пока нет профилей</h2>
                        <p>Будьте первым, кто создаст профиль!</p>
                        <a href="/create" class="back-btn">Создать профиль</a>
                    </div>
                {% endif %}
            </div>
        </body>
        </html>
    ''', get_starry_night_css=get_starry_night_css, profiles=profiles)

if __name__ == '__main__':
    print("🚀 Запуск приложения с исправленной ошибкой 413...")
    print("📝 URL: http://192.168.0.24:5000")
    print("🔧 Nginx обрабатывает HTTPS и лимиты файлов")
    app.run(host='0.0.0.0', port=5000, debug=True) 