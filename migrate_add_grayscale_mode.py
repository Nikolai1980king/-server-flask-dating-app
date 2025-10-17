#!/usr/bin/env python3
"""
Миграция для добавления поля grayscale_mode в таблицу user_settings
"""

import sqlite3
import os
from datetime import datetime

def migrate_add_grayscale_mode():
    """Добавляет поле grayscale_mode в таблицу user_settings"""
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect('dating_app.db')
        cursor = conn.cursor()

        print("🔄 Начинаем миграцию: добавление поля grayscale_mode...")

        # Проверяем, существует ли уже поле grayscale_mode
        cursor.execute("PRAGMA table_info(user_settings)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if 'grayscale_mode' in column_names:
            print("✅ Поле grayscale_mode уже существует в таблице user_settings")
            return True

        # Добавляем поле grayscale_mode
        cursor.execute('''
            ALTER TABLE user_settings 
            ADD COLUMN grayscale_mode INTEGER DEFAULT 0
        ''')

        # Обновляем существующие записи, устанавливая grayscale_mode = 0 (выключен)
        cursor.execute('''
            UPDATE user_settings 
            SET grayscale_mode = 0 
            WHERE grayscale_mode IS NULL
        ''')

        conn.commit()
        conn.close()

        print("✅ Миграция успешно завершена: поле grayscale_mode добавлено")
        return True

    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Запуск миграции для добавления поля grayscale_mode...")
    success = migrate_add_grayscale_mode()
    
    if success:
        print("🎉 Миграция завершена успешно!")
    else:
        print("💥 Миграция завершилась с ошибкой!")
