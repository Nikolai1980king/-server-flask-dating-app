#!/usr/bin/env python3
"""
Скрипт миграции базы данных для добавления полей оплаты
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Добавляет недостающие колонки в таблицу profile"""
    
    db_path = 'instance/dating_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена!")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔍 Проверяем структуру таблицы profile...")
        
        # Получаем информацию о колонках
        cursor.execute("PRAGMA table_info(profile)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Существующие колонки: {', '.join(column_names)}")
        
        # Проверяем, какие колонки нужно добавить
        missing_columns = []
        
        if 'is_paid' not in column_names:
            missing_columns.append("is_paid BOOLEAN DEFAULT 0")
            print("➕ Нужно добавить колонку: is_paid")
        
        if 'payment_date' not in column_names:
            missing_columns.append("payment_date DATETIME")
            print("➕ Нужно добавить колонку: payment_date")
        
        if not missing_columns:
            print("✅ Все необходимые колонки уже существуют!")
            return True
        
        # Добавляем недостающие колонки
        for column_def in missing_columns:
            column_name = column_def.split()[0]
            print(f"🔧 Добавляем колонку: {column_name}")
            
            try:
                cursor.execute(f"ALTER TABLE profile ADD COLUMN {column_def}")
                print(f"✅ Колонка {column_name} добавлена успешно!")
            except sqlite3.Error as e:
                if "duplicate column name" in str(e):
                    print(f"⚠️ Колонка {column_name} уже существует")
                else:
                    print(f"❌ Ошибка при добавлении колонки {column_name}: {e}")
                    return False
        
        # Сохраняем изменения
        conn.commit()
        
        # Проверяем результат
        cursor.execute("PRAGMA table_info(profile)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"📋 Обновленные колонки: {', '.join(column_names)}")
        
        # Проверяем, что нужные колонки добавлены
        if 'is_paid' in column_names and 'payment_date' in column_names:
            print("🎉 Миграция завершена успешно!")
            return True
        else:
            print("❌ Не все колонки были добавлены!")
            return False
            
    except sqlite3.Error as e:
        print(f"❌ Ошибка базы данных: {e}")
        return False
    except Exception as e:
        print(f"❌ Неожиданная ошибка: {e}")
        return False
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🚀 Запуск миграции базы данных...")
    print("=" * 50)
    
    success = migrate_database()
    
    print("=" * 50)
    if success:
        print("✅ Миграция завершена успешно!")
        exit(0)
    else:
        print("❌ Миграция не удалась!")
        exit(1)