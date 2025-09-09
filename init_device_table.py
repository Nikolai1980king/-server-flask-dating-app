#!/usr/bin/env python3
"""
Скрипт для инициализации таблицы Device в базе данных
"""

from app import app, db, Device

def init_device_table():
    """Создает таблицу Device если она не существует"""
    with app.app_context():
        try:
            # Создаем таблицу Device
            db.create_all()
            print("✅ Таблица Device успешно создана")
            
            # Проверяем количество записей
            device_count = Device.query.count()
            print(f"📊 Количество устройств в базе: {device_count}")
            
        except Exception as e:
            print(f"❌ Ошибка при создании таблицы Device: {e}")

if __name__ == '__main__':
    init_device_table()