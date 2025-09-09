import os

class Config:
    SECRET_KEY = 'super-secret-key'
    UPLOAD_FOLDER = 'static/uploads'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dating_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google Maps API Key - замените на ваш ключ
    # Получите ключ на: https://console.cloud.google.com/
    GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY')
    
    # Для тестирования можно использовать тестовый ключ
    # GOOGLE_MAPS_API_KEY = 'AIzaSyB41DRUbKWJHPxaFjMAwdrzWgyVbBo7qgE'  # Пример ключа 