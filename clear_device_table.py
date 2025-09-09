#!/usr/bin/env python3
"""
Скрипт для очистки таблицы Device
"""

from app import app, db, Device

def clear_device_table():
    """Очищает таблицу Device"""
    with app.app_context():
        try:
            # Удаляем все записи из таблицы Device
            Device.query.delete()
            db.session.commit()
            print("✅ Таблица Device очищена")
            
            # Проверяем количество записей
            device_count = Device.query.count()
            print(f"📊 Количество устройств в базе: {device_count}")
            
        except Exception as e:
            print(f"❌ Ошибка при очистке таблицы Device: {e}")

if __name__ == '__main__':
    clear_device_table()