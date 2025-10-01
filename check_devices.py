#!/usr/bin/env python3
"""
Скрипт для проверки зарегистрированных устройств
"""

from app import app, db, Device

def check_devices():
    """Показывает все зарегистрированные устройства"""
    with app.app_context():
        try:
            devices = Device.query.all()
            print(f"📊 Всего устройств в базе: {len(devices)}")
            print()
            
            for device in devices:
                print(f"🔍 Устройство ID: {device.id}")
                print(f"   📱 Отпечаток: {device.device_fingerprint[:16]}...")
                print(f"   🌐 IP-адрес: {device.client_ip}")
                print(f"   👤 User-Agent: {device.user_agent[:50]}..." if device.user_agent else "   👤 User-Agent: None")
                print(f"   🆔 Профиль: {device.profile_id}")
                print(f"   📅 Создано: {device.created_at}")
                print(f"   🔄 Последнее использование: {device.last_used}")
                print()
                
        except Exception as e:
            print(f"❌ Ошибка при проверке устройств: {e}")

if __name__ == '__main__':
    check_devices()