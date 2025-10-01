#!/usr/bin/env python3
"""
Скрипт для обновления таблиц системы отслеживания устройств
"""

import sqlite3
import os

def update_device_tables():
    """Обновляет таблицы device_control и ip_control"""
    
    db_path = 'dating_app.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔧 Обновление таблиц системы отслеживания устройств...")
        
        # Проверяем существование таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='device_control'")
        device_table_exists = cursor.fetchone() is not None
        
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='ip_control'")
        ip_table_exists = cursor.fetchone() is not None
        
        # Удаляем старые таблицы если они существуют
        if device_table_exists:
            print("🗑️ Удаление старой таблицы device_control...")
            cursor.execute("DROP TABLE device_control")
        
        if ip_table_exists:
            print("🗑️ Удаление старой таблицы ip_control...")
            cursor.execute("DROP TABLE ip_control")
        
        # Создаем новые таблицы с правильной структурой
        print("📱 Создание таблицы device_control...")
        cursor.execute('''
            CREATE TABLE device_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_fingerprint VARCHAR UNIQUE NOT NULL,
                profile_id VARCHAR NOT NULL,
                ip_address VARCHAR NOT NULL,
                user_agent VARCHAR,
                is_mobile BOOLEAN DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        print("🌐 Создание таблицы ip_control...")
        cursor.execute('''
            CREATE TABLE ip_control (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ip_address VARCHAR UNIQUE NOT NULL,
                profile_id VARCHAR NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        print("✅ Таблицы успешно обновлены")
        
        # Проверяем структуру таблиц
        print("\n📋 Структура таблицы device_control:")
        cursor.execute("PRAGMA table_info(device_control)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        print("\n📋 Структура таблицы ip_control:")
        cursor.execute("PRAGMA table_info(ip_control)")
        columns = cursor.fetchall()
        for col in columns:
            print(f"  - {col[1]} ({col[2]})")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления таблиц: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == '__main__':
    success = update_device_tables()
    if success:
        print("\n🎉 Обновление завершено успешно!")
        print("Теперь можно запускать сервер: python app.py")
    else:
        print("\n💥 Обновление не удалось")