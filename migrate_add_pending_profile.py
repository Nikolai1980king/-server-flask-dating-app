#!/usr/bin/env python3
"""
Скрипт для создания таблицы PendingProfile (временные анкеты до оплаты)
"""

import sqlite3
import os

def migrate_database():
    """Создает таблицу PendingProfile"""
    
    # Путь к базе данных
    db_path = 'instance/dating_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже таблица pending_profile
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pending_profile'")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("✅ Таблица pending_profile уже существует")
            return True
        
        # Создаем таблицу pending_profile
        print("🔄 Создаем таблицу pending_profile...")
        cursor.execute('''
            CREATE TABLE pending_profile (
                id VARCHAR PRIMARY KEY,
                name VARCHAR NOT NULL,
                age INTEGER NOT NULL,
                gender VARCHAR NOT NULL,
                hobbies VARCHAR NOT NULL,
                goal VARCHAR NOT NULL,
                city VARCHAR,
                venue VARCHAR,
                photo VARCHAR,
                latitude FLOAT,
                longitude FLOAT,
                creation_ip VARCHAR,
                created_at DATETIME
            )
        ''')
        
        # Сохраняем изменения
        conn.commit()
        print("✅ Таблица pending_profile успешно создана")
        
        # Закрываем соединение
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции базы данных: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Начинаем миграцию базы данных...")
    success = migrate_database()
    
    if success:
        print("✅ Миграция завершена успешно!")
    else:
        print("❌ Миграция не удалась!")
        exit(1)








