#!/usr/bin/env python3
"""
Скрипт для обновления таблицы Device - добавление поля client_ip
"""

from app import app, db, Device

def update_device_table():
    """Обновляет таблицу Device, добавляя поле client_ip"""
    with app.app_context():
        try:
            # Создаем все таблицы (включая новые поля)
            db.create_all()
            print("✅ Таблица Device обновлена")
            
            # Проверяем количество записей
            device_count = Device.query.count()
            print(f"📊 Количество устройств в базе: {device_count}")
            
            # Показываем структуру таблицы
            if device_count > 0:
                sample_device = Device.query.first()
                print(f"📋 Пример записи: ID={sample_device.id}, IP={sample_device.client_ip}")
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении таблицы Device: {e}")

if __name__ == '__main__':
    update_device_table()