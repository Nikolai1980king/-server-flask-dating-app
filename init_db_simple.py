#!/usr/bin/env python3
"""
Простой скрипт для инициализации базы данных
"""

import sqlite3
import os

def init_database():
    """Создает таблицу IPControl в базе данных"""
    db_path = 'instance/dating_app.db'
    
    # Создаем директорию instance если её нет
    os.makedirs('instance', exist_ok=True)
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Создаем таблицу IPControl
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address VARCHAR UNIQUE NOT NULL,
                profile_id VARCHAR NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Создаем таблицу DeviceControl
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS device_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_fingerprint VARCHAR UNIQUE NOT NULL,
                profile_id VARCHAR NOT NULL,
                ip_address VARCHAR NOT NULL,
                user_agent VARCHAR,
                is_mobile BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Таблицы ip_control и device_control созданы успешно")
        
        # Проверяем, что таблицы создались
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ip_control'")
        result1 = cursor.fetchone()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='device_control'")
        result2 = cursor.fetchone()
        
        if result1:
            print("✅ Таблица ip_control существует в базе данных")
        else:
            print("❌ Таблица ip_control не найдена")
            
        if result2:
            print("✅ Таблица device_control существует в базе данных")
        else:
            print("❌ Таблица device_control не найдена")
            
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблицы: {e}")

if __name__ == "__main__":
    init_database()