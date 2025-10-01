#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

import sqlite3
import os

def init_database():
    """Создает базу данных с правильными таблицами"""
    
    # Удаляем старую базу данных если она существует
    if os.path.exists('dating_app.db'):
        os.remove('dating_app.db')
        print("🗑️ Старая база данных удалена")
    
    # Создаем новую базу данных
    conn = sqlite3.connect('dating_app.db')
    cursor = conn.cursor()
    
    # Создаем таблицы
    tables = [
        """
        CREATE TABLE profile (
            id VARCHAR PRIMARY KEY,
            name VARCHAR NOT NULL,
            age INTEGER NOT NULL,
            gender VARCHAR NOT NULL,
            hobbies VARCHAR NOT NULL,
            goal VARCHAR NOT NULL,
            city VARCHAR,
            venue VARCHAR,
            photo VARCHAR,
            likes INTEGER DEFAULT 0,
            latitude FLOAT,
            longitude FLOAT,
            created_at DATETIME
        )
        """,
        """
        CREATE TABLE message (
            id INTEGER PRIMARY KEY,
            chat_key VARCHAR NOT NULL,
            sender VARCHAR NOT NULL,
            text VARCHAR NOT NULL,
            timestamp DATETIME,
            read_by VARCHAR
        )
        """,
        """
        CREATE TABLE like (
            id INTEGER PRIMARY KEY,
            user_id VARCHAR NOT NULL,
            liked_id VARCHAR NOT NULL
        )
        """,
        """
        CREATE TABLE user_settings (
            id INTEGER PRIMARY KEY,
            user_id VARCHAR NOT NULL UNIQUE,
            sound_notifications BOOLEAN DEFAULT 1,
            created_at DATETIME,
            updated_at DATETIME
        )
        """
    ]
    
    for table_sql in tables:
        cursor.execute(table_sql)
        print("✅ Таблица создана")
    
    conn.commit()
    conn.close()
    
    print("🎉 База данных успешно инициализирована!")
    print("📊 Созданные таблицы:")
    
    # Проверяем созданные таблицы
    conn = sqlite3.connect('dating_app.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        print(f"   - {table[0]}")
    
    conn.close()

if __name__ == "__main__":
    init_database() 