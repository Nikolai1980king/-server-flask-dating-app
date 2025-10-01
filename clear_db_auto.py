#!/usr/bin/env python3
"""
Автоматическая очистка базы данных без подтверждения
"""

import sqlite3
import os

def clear_database():
    db_path = 'instance/dating_app.db'
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        tables = ['profile', 'pending_profile', 'like', 'message', 'match', 'payment']
        deleted_counts = {}
        
        print("🧹 Начинаем очистку базы данных...")
        
        for table in tables:
            try:
                cursor.execute(f"DELETE FROM {table}")
                deleted_counts[table] = cursor.rowcount
                print(f"✅ Удалено записей из таблицы {table}: {deleted_counts[table]}")
            except sqlite3.OperationalError:
                print(f"⚠️ Таблица {table} не найдена, пропускаем.")
                deleted_counts[table] = 0
        
        conn.commit()
        
        # Verify counts
        print("\n📊 Проверка после очистки:")
        for table in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table.capitalize()}: {count}")
            except sqlite3.OperationalError:
                print(f"  {table.capitalize()}: таблица не существует")
        
        conn.close()
        print("\n🎉 База данных полностью очищена!")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при очистке базы данных: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    success = clear_database()
    if not success:
        exit(1)
