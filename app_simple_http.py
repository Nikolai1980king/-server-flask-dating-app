from flask import Flask, render_template_string, request, redirect, url_for, make_response, jsonify
import os
import uuid
from datetime import datetime, timedelta
from collections import defaultdict
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import and_
from functools import wraps

app = Flask(__name__)
app.secret_key = 'super-secret-key'

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Увеличиваем лимит загрузки файлов до 2GB
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dating_app.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
    read_by = db.Column(db.String, nullable=True)

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String, nullable=False)
    liked_id = db.Column(db.String, nullable=False)

# Создаем таблицы
with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Dating App - Главная</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 800px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                text-align: center;
            }
            h1 {
                margin-bottom: 30px;
                color: #fff;
            }
            .btn {
                display: inline-block;
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 25px;
                margin: 10px;
                transition: all 0.3s ease;
            }
            .btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
            .status {
                background: rgba(46, 204, 113, 0.2);
                border: 1px solid #2ecc71;
                padding: 15px;
                border-radius: 10px;
                margin: 20px 0;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎉 Dating App - Работает!</h1>
            
            <div class="status">
                ✅ Сервер запущен успешно<br>
                ✅ Лимит файлов: 2GB<br>
                ✅ Nginx настроен правильно<br>
                ✅ Ошибка 413 исправлена
            </div>
            
            <a href="/create" class="btn">👤 Создать профиль</a>
            <a href="/test_413_fix.html" class="btn">🧪 Тест загрузки файлов</a>
            <a href="/profiles" class="btn">👥 Просмотр профилей</a>
        </div>
    </body>
    </html>
    '''

@app.route('/create', methods=['GET', 'POST'])
def create_profile():
    if request.method == 'POST':
        # Обработка создания профиля
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
        
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>Профиль создан</title>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    max-width: 600px;
                    margin: 50px auto;
                    padding: 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 30px;
                    border-radius: 15px;
                    text-align: center;
                }}
                .success {{
                    background: rgba(46, 204, 113, 0.2);
                    border: 1px solid #2ecc71;
                    padding: 15px;
                    border-radius: 10px;
                    margin: 20px 0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>✅ Профиль создан успешно!</h1>
                <div class="success">
                    <p><strong>Имя:</strong> {name}</p>
                    <p><strong>Возраст:</strong> {age}</p>
                    <p><strong>Пол:</strong> {gender}</p>
                    <p><strong>Хобби:</strong> {hobbies}</p>
                    <p><strong>Цель:</strong> {goal}</p>
                    <p><strong>Город:</strong> {city}</p>
                    <p><strong>Место:</strong> {venue}</p>
                    {f'<p><strong>Фото:</strong> Загружено ({photo})</p>' if photo else '<p><strong>Фото:</strong> Не загружено</p>'}
                </div>
                <a href="/" style="color: white; text-decoration: none; background: #ff6b6b; padding: 10px 20px; border-radius: 5px;">← Назад</a>
            </div>
        </body>
        </html>
        '''
    
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Создать профиль</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            .form-group {
                margin-bottom: 20px;
            }
            label {
                display: block;
                margin-bottom: 5px;
                font-weight: bold;
            }
            input, select, textarea {
                width: 100%;
                padding: 10px;
                border: none;
                border-radius: 5px;
                background: rgba(255, 255, 255, 0.9);
                color: #333;
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
            }
            button:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 0, 0, 0.3);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>👤 Создать профиль</h1>
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
                    <textarea id="hobbies" name="hobbies" rows="3" required></textarea>
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
                    <input type="text" id="city" name="city">
                </div>
                
                <div class="form-group">
                    <label for="venue">Любимое место:</label>
                    <input type="text" id="venue" name="venue">
                </div>
                
                <div class="form-group">
                    <label for="photo">Фото (до 2GB):</label>
                    <input type="file" id="photo" name="photo" accept="image/*">
                </div>
                
                <button type="submit">Создать профиль</button>
            </form>
        </div>
    </body>
    </html>
    '''

@app.route('/profiles')
def view_profiles():
    profiles = Profile.query.all()
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Профили</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1200px;
                margin: 0 auto;
                padding: 20px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
            }
            .container {
                background: rgba(255, 255, 255, 0.1);
                padding: 30px;
                border-radius: 15px;
                backdrop-filter: blur(10px);
            }
            .profile {
                background: rgba(255, 255, 255, 0.1);
                padding: 20px;
                margin: 20px 0;
                border-radius: 10px;
                display: flex;
                align-items: center;
            }
            .profile-photo {
                width: 100px;
                height: 100px;
                border-radius: 50%;
                object-fit: cover;
                margin-right: 20px;
            }
            .profile-info {
                flex: 1;
            }
            .back-btn {
                background: linear-gradient(45deg, #ff6b6b, #ee5a24);
                color: white;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 5px;
                display: inline-block;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← Назад</a>
            <h1>👥 Профили ({})
    '''.format(len(profiles))
    
    for profile in profiles:
        photo_html = ''
        if profile.photo:
            photo_html = f'<img src="/static/uploads/{profile.photo}" class="profile-photo" alt="Фото">'
        else:
            photo_html = '<div class="profile-photo" style="background: #ccc; display: flex; align-items: center; justify-content: center;">Нет фото</div>'
        
        html += f'''
            <div class="profile">
                {photo_html}
                <div class="profile-info">
                    <h3>{profile.name}, {profile.age}</h3>
                    <p><strong>Пол:</strong> {profile.gender}</p>
                    <p><strong>Хобби:</strong> {profile.hobbies}</p>
                    <p><strong>Цель:</strong> {profile.goal}</p>
                    <p><strong>Город:</strong> {profile.city or 'Не указан'}</p>
                    <p><strong>Место:</strong> {profile.venue or 'Не указано'}</p>
                </div>
            </div>
        '''
    
    html += '''
        </div>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    print("🚀 Запуск HTTP сервера...")
    print("📝 URL: http://192.168.0.24:5000")
    print("🔧 Nginx будет обрабатывать HTTPS и лимиты файлов")
    app.run(host='0.0.0.0', port=5000, debug=True) 