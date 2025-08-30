#!/usr/bin/env python3
"""
Скрипт для обновления базы данных - удаление поля city
"""

import sqlite3
import os

def update_database():
    """Удаляет поле city из таблицы Profile"""
    
    db_path = 'instance/dating_app.db'
    
    if not os.path.exists(db_path):
        print(f"База данных не найдена: {db_path}")
        return
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли поле city
        cursor.execute("PRAGMA table_info(profile)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'city' in columns:
            print("Удаляем поле 'city' из таблицы Profile...")
            
            # Создаем временную таблицу без поля city
            cursor.execute("""
                CREATE TABLE profile_temp (
                    id VARCHAR PRIMARY KEY,
                    name VARCHAR NOT NULL,
                    age INTEGER NOT NULL,
                    gender VARCHAR NOT NULL,
                    hobbies VARCHAR NOT NULL,
                    goal VARCHAR NOT NULL,
                    venue VARCHAR,
                    photo VARCHAR,
                    likes INTEGER DEFAULT 0,
                    latitude FLOAT,
                    longitude FLOAT
                )
            """)
            
            # Копируем данные из старой таблицы в новую (без поля city)
            cursor.execute("""
                INSERT INTO profile_temp 
                (id, name, age, gender, hobbies, goal, venue, photo, likes, latitude, longitude)
                SELECT id, name, age, gender, hobbies, goal, venue, photo, likes, latitude, longitude
                FROM profile
            """)
            
            # Удаляем старую таблицу
            cursor.execute("DROP TABLE profile")
            
            # Переименовываем новую таблицу
            cursor.execute("ALTER TABLE profile_temp RENAME TO profile")
            
            print("✅ Поле 'city' успешно удалено из базы данных!")
            
        else:
            print("✅ Поле 'city' уже отсутствует в таблице Profile")
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при обновлении базы данных: {e}")
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    print("🔄 Обновление базы данных...")
    update_database()
    print("✅ Обновление завершено!") 