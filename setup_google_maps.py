#!/usr/bin/env python3
"""
Скрипт для настройки Google Maps API
"""

import os
import sys

def main():
    print("🌍 Настройка Google Maps API для приложения знакомств")
    print("=" * 50)
    
    print("\n📋 Инструкция по получению API ключа:")
    print("1. Перейдите на https://console.cloud.google.com/")
    print("2. Создайте новый проект или выберите существующий")
    print("3. Включите следующие API:")
    print("   - Maps JavaScript API")
    print("   - Places API")
    print("   - Geocoding API")
    print("4. Создайте API ключ в разделе 'Credentials'")
    print("5. Скопируйте ключ")
    
    print("\n🔑 Введите ваш Google Maps API ключ:")
    api_key = input("API Key: ").strip()
    
    if not api_key or api_key == "YOUR_GOOGLE_MAPS_API_KEY":
        print("❌ Ключ не введен или недействителен!")
        return
    
    # Обновляем конфигурацию
    config_content = f'''import os

class Config:
    SECRET_KEY = 'super-secret-key'
    UPLOAD_FOLDER = 'static/uploads'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///dating_app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Google Maps API Key
    GOOGLE_MAPS_API_KEY = '{api_key}'
'''
    
    try:
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)
        print("✅ Конфигурация обновлена!")
        
        # Копируем полную версию шаблона
        if os.path.exists('templates/geolocation_full.html'):
            import shutil
            shutil.copy('templates/geolocation_full.html', 'templates/geolocation.html')
            print("✅ Полная версия шаблона с картами активирована!")
        
        print("\n🚀 Теперь запустите приложение:")
        print("python app.py")
        print("\n🌐 Откройте http://localhost:5000")
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении конфигурации: {e}")

if __name__ == "__main__":
    main() 