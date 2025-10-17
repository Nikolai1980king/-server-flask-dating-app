#!/usr/bin/env python3
"""
Конфигурация для деплоя на удаленный сервер
"""

import os

# ============================================================================
# НАСТРОЙКИ ДЛЯ ДЕПЛОЯ
# ============================================================================

# Основной домен сайта (замените на ваш домен)
DEPLOY_DOMAIN = os.getenv('DEPLOY_DOMAIN', 'https://your-domain.com')

# Настройки для ЮKassa
YOOKASSA_SHOP_ID = os.getenv('YOOKASSA_SHOP_ID', 'your_shop_id')
YOOKASSA_SECRET_KEY = os.getenv('YOOKASSA_SECRET_KEY', 'your_secret_key')
YOOKASSA_TEST_MODE = os.getenv('YOOKASSA_TEST_MODE', 'True').lower() == 'true'

# Настройки базы данных
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///dating_app.db')

# Настройки Flask
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

# Настройки безопасности
SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')

# Настройки для загрузки файлов
UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', '/var/www/uploads')
MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', '16 * 1024 * 1024'))  # 16MB

print(f"""
🚀 Конфигурация для деплоя:
   📍 Домен: {DEPLOY_DOMAIN}
   🏪 ЮKassa Shop ID: {YOOKASSA_SHOP_ID}
   🧪 Тестовый режим: {YOOKASSA_TEST_MODE}
   🗄️ База данных: {DATABASE_URL}
   🔧 Flask ENV: {FLASK_ENV}
   🐛 Debug: {FLASK_DEBUG}
   📁 Загрузки: {UPLOAD_FOLDER}
""")











