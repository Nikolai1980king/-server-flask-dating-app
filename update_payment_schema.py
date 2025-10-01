#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для обновления схемы базы данных
Добавляет столбцы для платежей в существующую базу
"""

import sqlite3
import os
from datetime import datetime

def update_database_schema():
    """Обновляет схему базы данных для поддержки платежей"""
    print("🔄 Обновление схемы базы данных для платежей...")
    
    # Путь к базе данных
    db_path = "instance/dating_app.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("✅ Подключение к базе данных установлено")
        
        # Проверяем, есть ли уже столбцы для платежей
        cursor.execute("PRAGMA table_info(profile)")
        columns = [column[1] for column in cursor.fetchall()]
        
        print(f"📋 Текущие столбцы в таблице profile: {', '.join(columns)}")
        
        # Добавляем столбец is_paid, если его нет
        if 'is_paid' not in columns:
            print("➕ Добавляем столбец is_paid...")
            cursor.execute("ALTER TABLE profile ADD COLUMN is_paid BOOLEAN DEFAULT FALSE")
            print("✅ Столбец is_paid добавлен")
        else:
            print("✅ Столбец is_paid уже существует")
        
        # Добавляем столбец payment_date, если его нет
        if 'payment_date' not in columns:
            print("➕ Добавляем столбец payment_date...")
            cursor.execute("ALTER TABLE profile ADD COLUMN payment_date DATETIME")
            print("✅ Столбец payment_date добавлен")
        else:
            print("✅ Столбец payment_date уже существует")
        
        # Создаем таблицу payments, если её нет
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                amount REAL NOT NULL,
                status TEXT DEFAULT 'pending',
                payment_method TEXT,
                yookassa_payment_id TEXT,
                yookassa_payment_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("✅ Таблица payments создана/проверена")
        
        # Создаем индексы для оптимизации
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_user_id ON payments(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_status ON payments(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_payments_yookassa_id ON payments(yookassa_payment_id)")
        print("✅ Индексы созданы/проверены")
        
        # Сохраняем изменения
        conn.commit()
        print("✅ Изменения сохранены")
        
        # Проверяем обновленную схему
        cursor.execute("PRAGMA table_info(profile)")
        updated_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Обновленные столбцы в таблице profile: {', '.join(updated_columns)}")
        
        # Проверяем таблицу payments
        cursor.execute("PRAGMA table_info(payments)")
        payment_columns = [column[1] for column in cursor.fetchall()]
        print(f"📋 Столбцы в таблице payments: {', '.join(payment_columns)}")
        
        conn.close()
        print("🎉 Схема базы данных успешно обновлена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка обновления схемы: {e}")
        if 'conn' in locals():
            conn.close()
        return False

def verify_database_structure():
    """Проверяет структуру обновленной базы данных"""
    print("\n🔍 Проверка структуры базы данных...")
    
    db_path = "instance/dating_app.db"
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем таблицы
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [table[0] for table in cursor.fetchall()]
        print(f"📊 Таблицы в базе: {', '.join(tables)}")
        
        # Проверяем столбцы profile
        cursor.execute("PRAGMA table_info(profile)")
        profile_columns = cursor.fetchall()
        print(f"📋 Столбцы profile:")
        for col in profile_columns:
            print(f"   - {col[1]} ({col[2]})")
        
        # Проверяем столбцы payments
        if 'payments' in tables:
            cursor.execute("PRAGMA table_info(payments)")
            payment_columns = cursor.fetchall()
            print(f"📋 Столбцы payments:")
            for col in payment_columns:
                print(f"   - {col[1]} ({col[2]})")
        
        conn.close()
        print("✅ Проверка завершена")
        
    except Exception as e:
        print(f"❌ Ошибка проверки: {e}")

if __name__ == "__main__":
    print("🚀 Обновление схемы базы данных для платежей")
    print("=" * 60)
    
    success = update_database_schema()
    
    if success:
        verify_database_structure()
        print("\n🎉 База данных готова для работы с платежами!")
    else:
        print("\n❌ Обновление не удалось. Проверьте ошибки выше.")