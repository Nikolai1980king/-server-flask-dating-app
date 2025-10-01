#!/usr/bin/env python3
"""
Скрипт для добавления столбца creation_ip в таблицу profile
"""

import sqlite3
import os

def migrate_database():
    """Добавляет столбец creation_ip в таблицу profile"""
    
    # Путь к базе данных
    db_path = 'instance/dating_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли уже столбец creation_ip
        cursor.execute("PRAGMA table_info(profile)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'creation_ip' in columns:
            print("✅ Столбец creation_ip уже существует")
            return True
        
        # Добавляем столбец creation_ip
        print("🔄 Добавляем столбец creation_ip...")
        cursor.execute("ALTER TABLE profile ADD COLUMN creation_ip VARCHAR")
        
        # Сохраняем изменения
        conn.commit()
        print("✅ Столбец creation_ip успешно добавлен")
        
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