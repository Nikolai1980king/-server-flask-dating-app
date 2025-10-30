#!/usr/bin/env python3
"""
Миграция базы данных: добавление таблицы sent_puzzle для отслеживания отправленных головоломок
"""

import sqlite3
import os

# Определяем путь к базе данных
DB_PATH = os.path.join(os.path.dirname(__file__), 'instance', 'dating_app.db')

def migrate():
    """Применить миграцию"""
    print(f"🔄 Начинаем миграцию базы данных: {DB_PATH}")
    
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных не найдена: {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # Проверяем, существует ли таблица sent_puzzle
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='sent_puzzle'
        """)
        
        if cursor.fetchone():
            print("✅ Таблица sent_puzzle уже существует")
        else:
            # Создаем таблицу sent_puzzle
            cursor.execute("""
                CREATE TABLE sent_puzzle (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id VARCHAR NOT NULL,
                    receiver_id VARCHAR NOT NULL,
                    puzzle_id INTEGER NOT NULL,
                    sent_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (sender_id, receiver_id, puzzle_id)
                )
            """)
            print("✅ Таблица sent_puzzle создана успешно")
        
        conn.commit()
        print("✅ Миграция завершена успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    migrate()















