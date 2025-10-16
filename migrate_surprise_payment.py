#!/usr/bin/env python3
"""
Скрипт миграции для добавления платной функции "Удивить"
Добавляет:
1. Поля surprise_feature_paid и surprise_feature_payment_date в таблицу profile
2. Таблицу chat_permission для отслеживания разрешений на общение

Запустить: python migrate_surprise_payment.py
"""

import sqlite3
import os

# Путь к базе данных (ВАЖНО: используем instance/)
DB_PATH = 'instance/dating_app.db'

def migrate():
    """Добавляет новые поля и таблицы для платной функции 'Удивить'"""
    
    if not os.path.exists(DB_PATH):
        print(f"❌ База данных {DB_PATH} не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # ===================================================================
        # 1. Добавляем поля в таблицу profile
        # ===================================================================
        print("📦 Добавляем поля surprise_feature_paid и surprise_feature_payment_date...")
        
        # Проверяем, существует ли уже поле surprise_feature_paid
        cursor.execute("PRAGMA table_info(profile)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'surprise_feature_paid' not in columns:
            cursor.execute("""
                ALTER TABLE profile 
                ADD COLUMN surprise_feature_paid BOOLEAN DEFAULT 0
            """)
            print("✅ Добавлено поле surprise_feature_paid")
        else:
            print("✅ Поле surprise_feature_paid уже существует")
        
        if 'surprise_feature_payment_date' not in columns:
            cursor.execute("""
                ALTER TABLE profile 
                ADD COLUMN surprise_feature_payment_date DATETIME
            """)
            print("✅ Добавлено поле surprise_feature_payment_date")
        else:
            print("✅ Поле surprise_feature_payment_date уже существует")
        
        # ===================================================================
        # 2. Создаем таблицу chat_permission
        # ===================================================================
        print("\n📦 Создаем таблицу chat_permission...")
        
        # Проверяем, существует ли уже таблица
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='chat_permission'
        """)
        
        if cursor.fetchone():
            print("✅ Таблица chat_permission уже существует")
        else:
            cursor.execute("""
                CREATE TABLE chat_permission (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id VARCHAR NOT NULL,
                    receiver_id VARCHAR NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(sender_id, receiver_id)
                )
            """)
            print("✅ Таблица chat_permission создана")
            
            # Создаем индексы
            print("📑 Создаем индексы для chat_permission...")
            
            cursor.execute("""
                CREATE INDEX idx_chat_permission_sender 
                ON chat_permission(sender_id)
            """)
            
            cursor.execute("""
                CREATE INDEX idx_chat_permission_receiver 
                ON chat_permission(receiver_id)
            """)
            
            cursor.execute("""
                CREATE INDEX idx_chat_permission_pair 
                ON chat_permission(sender_id, receiver_id)
            """)
            
            print("✅ Индексы созданы")
        
        conn.commit()
        
        print("\n" + "="*60)
        print("✅ МИГРАЦИЯ УСПЕШНО ЗАВЕРШЕНА!")
        print("="*60)
        
        # Проверяем результат
        print("\n📊 Структура таблицы profile:")
        cursor.execute("PRAGMA table_info(profile)")
        for column in cursor.fetchall():
            if 'surprise' in column[1].lower():
                print(f"  ✓ {column[1]} ({column[2]})")
        
        print("\n📊 Таблица chat_permission:")
        cursor.execute("SELECT COUNT(*) FROM chat_permission")
        count = cursor.fetchone()[0]
        print(f"  Записей: {count}")
        
        print("\n📊 Все таблицы в базе данных:")
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка при миграции: {e}")
        if conn:
            conn.rollback()
            conn.close()
        return False


if __name__ == '__main__':
    print("🚀 Запуск миграции для платной функции 'Удивить'...")
    print("=" * 60)
    
    if migrate():
        print("\n" + "=" * 60)
        print("✅ ВСЕ ГОТОВО!")
        print("=" * 60)
        print("\n💡 Теперь перезапустите приложение:")
        print("   python app.py")
    else:
        print("\n" + "=" * 60)
        print("❌ МИГРАЦИЯ НЕ ВЫПОЛНЕНА!")
        print("=" * 60)
