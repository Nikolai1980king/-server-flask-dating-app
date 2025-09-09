#!/usr/bin/env python3
"""
Скрипт для отладки проблемы с расстоянием
"""

import requests
import json

def test_create_profile():
    """Тестируем создание профиля с разными расстояниями"""
    
    # URL вашего приложения
    base_url = "http://localhost:5000"  # Локальное приложение
    
    # Тестовые данные
    test_data = {
        'name': 'Тест_Пользователь',
        'age': '25',
        'gender': 'female',
        'hobbies': 'Тестирование',
        'goal': 'Тестирование',
        'venue': 'Тестовое кафе',
        'latitude': '55.7558',  # Москва
        'longitude': '37.6176',
        'venue_lat': '55.7485',  # ~1.5 км от пользователя
        'venue_lng': '37.6374'
    }
    
    # Создаем файл для теста
    with open('test_photo.jpg', 'wb') as f:
        f.write(b'fake_image_data')
    
    try:
        # Отправляем POST запрос
        with open('test_photo.jpg', 'rb') as photo:
            files = {'photo': ('test.jpg', photo, 'image/jpeg')}
            
            response = requests.post(
                f"{base_url}/create",
                data=test_data,
                files=files,
                timeout=10
            )
        
        print(f"📡 Статус ответа: {response.status_code}")
        print(f"📋 Заголовки: {dict(response.headers)}")
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                print(f"❌ Ошибка: {error_data.get('error', 'Неизвестная ошибка')}")
            except:
                print(f"❌ Текст ошибки: {response.text}")
        elif response.status_code == 200:
            try:
                success_data = response.json()
                print(f"✅ Успех: {success_data}")
            except:
                print(f"✅ Ответ: {response.text}")
        else:
            print(f"⚠️ Неожиданный статус: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")

if __name__ == "__main__":
    print("🔍 Тестирование создания профиля с превышением расстояния...")
    test_create_profile() 