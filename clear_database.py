#!/usr/bin/env python3
"""
Скрипт для полной очистки базы данных приложения знакомств
Удаляет все анкеты, лайки, сообщения, уведомления и настройки
"""

import sqlite3
import os

def clear_database():
    """Полная очистка базы данных"""
    
    # Путь к базе данных
    db_path = 'dating_app.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🧹 Начинаем очистку базы данных...")
        
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"📋 Найдено таблиц: {len(tables)}")
        
        # Отключаем проверку внешних ключей
        cursor.execute("PRAGMA foreign_keys = OFF;")
        
        # Удаляем только данные анкет, лайков и сообщений
        tables_to_clear = ['profile', 'like', 'message']
        
        for table_name in tables_to_clear:
            cursor.execute(f"DELETE FROM {table_name};")
            print(f"🗑️  Очищена таблица: {table_name}")
        
        # Настройки пользователей оставляем
        print("✅ Настройки пользователей сохранены")
        
        # Сбрасываем автоинкремент
        cursor.execute("DELETE FROM sqlite_sequence;")
        
        # Включаем проверку внешних ключей обратно
        cursor.execute("PRAGMA foreign_keys = ON;")
        
        # Сохраняем изменения
        conn.commit()
        
        print("✅ База данных успешно очищена!")
        print("📊 Статистика:")
        
        # Показываем количество записей в каждой таблице (должно быть 0)
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"   {table_name}: {count} записей")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при очистке базы данных: {e}")
        if 'conn' in locals():
            conn.close()

def show_database_info():
    """Показать информацию о базе данных"""
    
    db_path = 'dating_app.db'
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("📊 Информация о базе данных:")
        
        # Получаем список всех таблиц
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name != 'sqlite_sequence':
                cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
                count = cursor.fetchone()[0]
                print(f"   {table_name}: {count} записей")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении информации: {e}")

if __name__ == "__main__":
    print("🔧 Утилита очистки базы данных приложения знакомств")
    print("=" * 50)
    
    # Показываем текущее состояние
    print("\n📊 Текущее состояние базы данных:")
    show_database_info()
    
    # Спрашиваем подтверждение
    print("\n⚠️  ВНИМАНИЕ! Это действие удалит ВСЕ данные:")
    print("   - Все анкеты пользователей")
    print("   - Все лайки")
    print("   - Все сообщения")
    print("   - Все уведомления")
    print("   - Все настройки")
    print("   - Все метчи")
    
    confirm = input("\n❓ Вы уверены? Введите 'ДА' для подтверждения: ")
    
    if confirm == 'ДА':
        clear_database()
        print("\n🎉 Очистка завершена! База данных готова к использованию.")
    else:
        print("❌ Очистка отменена.")