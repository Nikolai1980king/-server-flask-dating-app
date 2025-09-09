#!/usr/bin/env python3
"""
Скрипт для очистки всех анкет из базы данных
Используется для тестирования новой функциональности
"""

import sqlite3
import os

def clear_all_profiles():
    """Очищает все анкеты из базы данных"""
    
    db_path = 'instance/dating_app.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем количество анкет до очистки
        cursor.execute("SELECT COUNT(*) FROM profile")
        count_before = cursor.fetchone()[0]
        
        print(f"📊 Найдено анкет в базе данных: {count_before}")
        
        if count_before == 0:
            print("✅ База данных уже пуста")
            return
        
        # Очищаем все таблицы
        print("🧹 Очищаем таблицу profile...")
        cursor.execute("DELETE FROM profile")
        
        print("🧹 Очищаем таблицу like...")
        cursor.execute("DELETE FROM like")
        
        print("🧹 Очищаем таблицу message...")
        cursor.execute("DELETE FROM message")
        
        # Сохраняем изменения
        conn.commit()
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) FROM profile")
        count_after = cursor.fetchone()[0]
        
        print(f"✅ Очистка завершена! Анкет в базе данных: {count_after}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при очистке базы данных: {e}")

if __name__ == "__main__":
    print("🗑️ Очистка всех анкет из базы данных...")
    clear_all_profiles()
    print("🎉 Готово!") 