#!/usr/bin/env python3
"""
Скрипт для пересоздания таблицы Device с новым полем client_ip
"""

from app import app, db, Device

def recreate_device_table():
    """Пересоздает таблицу Device с новым полем client_ip"""
    with app.app_context():
        try:
            # Удаляем старую таблицу
            Device.__table__.drop(db.engine, checkfirst=True)
            print("🗑️ Старая таблица Device удалена")
            
            # Создаем новую таблицу
            db.create_all()
            print("✅ Новая таблица Device создана с полем client_ip")
            
            # Проверяем количество записей
            device_count = Device.query.count()
            print(f"📊 Количество устройств в базе: {device_count}")
            
        except Exception as e:
            print(f"❌ Ошибка при пересоздании таблицы Device: {e}")

if __name__ == '__main__':
    recreate_device_table()