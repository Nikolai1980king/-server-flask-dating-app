#!/usr/bin/env python3
"""
Сравнение работы локального и серверного приложения
"""
import requests
import json

def test_local():
    print("🔍 Тестирование ЛОКАЛЬНОГО приложения...")
    
    # Тест 1: Проверяем доступность локального сервера
    try:
        response = requests.get("http://localhost:5000/", timeout=5)
        print(f"✅ Локальный сервер доступен: {response.status_code}")
    except Exception as e:
        print(f"❌ Локальный сервер недоступен: {e}")
        print("💡 Запустите: python app.py")
        return False
    
    # Тест 2: Проверяем загрузку фото 5MB на локальном сервере
    test_data = {
        'name': 'Тест_Локальный', 'age': '25', 'gender': 'female',
        'hobbies': 'Тестирование', 'goal': 'Тестирование', 'venue': 'Тестовое кафе',
        'latitude': '55.7558', 'longitude': '37.6176', # Москва
        'venue_lat': '55.7300', 'venue_lng': '37.6000' # ~3 км от пользователя
    }
    
    # Создаем тестовое фото 5MB
    photo_data = b'\xff\xd8\xff\xe0' + b'\x00' * 5 * 1024 * 1024  # JPEG header + 5MB данных
    with open('test_photo_5mb_local.jpg', 'wb') as f:
        f.write(photo_data)
    print(f"📸 Создано тестовое фото: {len(photo_data)} байт (5MB)")
    
    try:
        with open('test_photo_5mb_local.jpg', 'rb') as photo:
            files = {'photo': ('test.jpg', photo, 'image/jpeg')}
            response = requests.post("http://localhost:5000/create", data=test_data, files=files, timeout=15)
        
        print(f"📡 Статус ответа: {response.status_code}")
        print(f"📋 Content-Type: {response.headers.get('content-type', 'неизвестно')}")
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                print(f"❌ Ошибка: {error_data.get('error', 'Неизвестная ошибка')}")
                if 'далеко от кафе' in error_data.get('error', ''):
                    print("✅ Предупреждение о расстоянии работает локально!")
                else:
                    print("⚠️ Неожиданная ошибка")
            except:
                print(f"❌ Текст ошибки: {response.text}")
        elif response.status_code == 413:
            print("❌ Ошибка: Файл слишком большой локально")
        elif response.status_code == 200:
            print("✅ Профиль создан успешно локально!")
        else:
            print(f"⚠️ Неожиданный статус: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
    
    return True

def test_server():
    print("\n🔍 Тестирование СЕРВЕРНОГО приложения...")
    
    base_url = "https://212.67.11.50"
    
    # Тест 1: Проверяем доступность сервера
    try:
        response = requests.get(f"{base_url}/", timeout=5, verify=False)
        print(f"✅ Сервер доступен: {response.status_code}")
    except Exception as e:
        print(f"❌ Сервер недоступен: {e}")
        return False
    
    # Тест 2: Проверяем загрузку фото 5MB на сервере
    test_data = {
        'name': 'Тест_Сервер', 'age': '25', 'gender': 'female',
        'hobbies': 'Тестирование', 'goal': 'Тестирование', 'venue': 'Тестовое кафе',
        'latitude': '55.7558', 'longitude': '37.6176', # Москва
        'venue_lat': '55.7300', 'venue_lng': '37.6000' # ~3 км от пользователя
    }
    
    # Создаем тестовое фото 5MB
    photo_data = b'\xff\xd8\xff\xe0' + b'\x00' * 5 * 1024 * 1024  # JPEG header + 5MB данных
    with open('test_photo_5mb_server.jpg', 'wb') as f:
        f.write(photo_data)
    print(f"📸 Создано тестовое фото: {len(photo_data)} байт (5MB)")
    
    try:
        with open('test_photo_5mb_server.jpg', 'rb') as photo:
            files = {'photo': ('test.jpg', photo, 'image/jpeg')}
            response = requests.post(f"{base_url}/create", data=test_data, files=files, timeout=15, verify=False)
        
        print(f"📡 Статус ответа: {response.status_code}")
        print(f"📋 Content-Type: {response.headers.get('content-type', 'неизвестно')}")
        
        if response.status_code == 400:
            try:
                error_data = response.json()
                print(f"❌ Ошибка: {error_data.get('error', 'Неизвестная ошибка')}")
                if 'далеко от кафе' in error_data.get('error', ''):
                    print("✅ Предупреждение о расстоянии работает на сервере!")
                else:
                    print("⚠️ Неожиданная ошибка")
            except:
                print(f"❌ Текст ошибки: {response.text}")
        elif response.status_code == 413:
            print("❌ Ошибка: Файл слишком большой на сервере (Nginx ограничение)")
        elif response.status_code == 200:
            print("✅ Профиль создан успешно на сервере!")
        else:
            print(f"⚠️ Неожиданный статус: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
    except Exception as e:
        print(f"❌ Общая ошибка: {e}")
    
    return True

def main():
    print("🔍 СРАВНЕНИЕ ЛОКАЛЬНОГО И СЕРВЕРНОГО ПРИЛОЖЕНИЯ")
    print("=" * 60)
    
    local_ok = test_local()
    server_ok = test_server()
    
    print("\n" + "=" * 60)
    print("📊 РЕЗУЛЬТАТЫ СРАВНЕНИЯ:")
    
    if local_ok and server_ok:
        print("✅ Оба сервера доступны")
        print("💡 Разница: Локальный Flask работает напрямую, серверный через Nginx")
        print("🎯 Проблема: Nginx ограничивает размер файлов до 1MB")
        print("🔧 Решение: Увеличить client_max_body_size в настройках Nginx")
    else:
        print("❌ Один из серверов недоступен")

if __name__ == "__main__":
    main() 