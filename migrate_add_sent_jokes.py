#!/usr/bin/env python3
"""
Скрипт миграции для добавления таблицы SentJoke в базу данных
Запустить: python migrate_add_sent_jokes.py
"""

import sqlite3
import os

# Путь к базе данных
DB_PATH = 'dating_app.db'

def migrate():
    """Добавляет таблицу SentJoke в базу данных"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных {DB_PATH} не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже таблица
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sent_joke'
        """)
        
        if cursor.fetchone():
            print("✅ Таблица sent_joke уже существует")
            conn.close()
            return True
        
        # Создаем таблицу SentJoke
        print("📦 Создаем таблицу sent_joke...")
        cursor.execute("""
            CREATE TABLE sent_joke (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id VARCHAR NOT NULL,
                receiver_id VARCHAR NOT NULL,
                joke_id INTEGER NOT NULL,
                sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(sender_id, receiver_id, joke_id)
            )
        """)
        
        # Создаем индексы для быстрого поиска
        print("📑 Создаем индексы...")
        cursor.execute("""
            CREATE INDEX idx_sent_joke_sender 
            ON sent_joke(sender_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_sent_joke_receiver 
            ON sent_joke(receiver_id)
        """)
        
        cursor.execute("""
            CREATE INDEX idx_sent_joke_pair 
            ON sent_joke(sender_id, receiver_id)
        """)
        
        conn.commit()
        print("✅ Миграция успешно завершена!")
        print("✅ Таблица sent_joke создана")
        print("✅ Индексы созданы")
        
        # Проверяем результат
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f"\n📊 Таблицы в базе данных ({len(tables)}):")
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == '__main__':
    print("🚀 Запуск миграции базы данных...")
    print("=" * 50)
    
    if migrate():
        print("\n" + "=" * 50)
        print("✅ МИГРАЦИЯ ЗАВЕРШЕНА УСПЕШНО!")
        print("=" * 50)
    else:
        print("\n" + "=" * 50)
        print("❌ МИГРАЦИЯ НЕ ВЫПОЛНЕНА!")
        print("=" * 50)













