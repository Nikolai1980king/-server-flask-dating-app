#!/usr/bin/env python3
"""
Простой скрипт для очистки базы данных SQLite
"""

import sqlite3
import os

def clear_database():
    """Очищает базу данных от всех записей"""
    
    db_path = 'instance/dating_app.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Подсчитываем количество записей
        cursor.execute("SELECT COUNT(*) FROM profile")
        profiles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM like")
        likes_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message")
        messages_count = cursor.fetchone()[0]
        
        print("🗑️ ОЧИСТКА БАЗЫ ДАННЫХ")
        print("=" * 40)
        print(f"📊 Найдено записей:")
        print(f"   - Анкет: {profiles_count}")
        print(f"   - Лайков: {likes_count}")
        print(f"   - Сообщений: {messages_count}")
        
        if profiles_count == 0:
            print("✅ База данных уже пуста!")
            return
        
        # Удаляем все записи
        print("\n🗑️ Удаляем все записи...")
        
        cursor.execute("DELETE FROM message")
        print(f"   💬 Удалено сообщений: {messages_count}")
        
        cursor.execute("DELETE FROM like")
        print(f"   💕 Удалено лайков: {likes_count}")
        
        cursor.execute("DELETE FROM profile")
        print(f"   👤 Удалено анкет: {profiles_count}")
        
        # Сохраняем изменения
        conn.commit()
        
        print(f"\n✅ УСПЕШНО УДАЛЕНО:")
        print(f"   - {profiles_count} анкет")
        print(f"   - {likes_count} лайков")
        print(f"   - {messages_count} сообщений")
        
        # Проверяем, что база пуста
        cursor.execute("SELECT COUNT(*) FROM profile")
        remaining_profiles = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM like")
        remaining_likes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM message")
        remaining_messages = cursor.fetchone()[0]
        
        print(f"\n📊 Проверка после удаления:")
        print(f"   - Осталось анкет: {remaining_profiles}")
        print(f"   - Осталось лайков: {remaining_likes}")
        print(f"   - Осталось сообщений: {remaining_messages}")
        
        if remaining_profiles == 0 and remaining_likes == 0 and remaining_messages == 0:
            print("🎉 База данных полностью очищена!")
        else:
            print("⚠️ В базе остались записи!")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при очистке базы данных: {e}")

if __name__ == "__main__":
    clear_database() 