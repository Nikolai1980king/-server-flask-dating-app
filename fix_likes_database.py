#!/usr/bin/env python3
"""
Скрипт для исправления проблем с лайками в базе данных
"""

import sqlite3
import os
from datetime import datetime

def fix_likes_database():
    """Исправляет проблемы с лайками в базе данных"""
    print("🔧 Исправление проблем с лайками в базе данных...")
    
    db_path = 'instance/dating_app.db'
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 1. Удаляем дублирующие лайки
        print("🧹 Удаление дублирующих лайков...")
        
        # Находим дублирующие лайки
        cursor.execute("""
            SELECT user_id, liked_id, COUNT(*) as count
            FROM like
            GROUP BY user_id, liked_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"📋 Найдено {len(duplicates)} групп дублирующих лайков:")
            for duplicate in duplicates:
                print(f"  - Пользователь {duplicate[0]} лайкнул {duplicate[1]} {duplicate[2]} раз")
            
            # Удаляем дублирующие лайки, оставляя только один
            for duplicate in duplicates:
                user_id, liked_id, count = duplicate
                # Оставляем только первый лайк, удаляем остальные
                cursor.execute("""
                    DELETE FROM like 
                    WHERE user_id = ? AND liked_id = ? 
                    AND id NOT IN (
                        SELECT MIN(id) 
                        FROM like 
                        WHERE user_id = ? AND liked_id = ?
                    )
                """, (user_id, liked_id, user_id, liked_id))
            
            deleted_count = cursor.rowcount
            print(f"✅ Удалено {deleted_count} дублирующих лайков")
        else:
            print("✅ Дублирующих лайков не найдено")
        
        # 2. Обновляем счетчики лайков в профилях
        print("📊 Обновление счетчиков лайков...")
        
        cursor.execute("SELECT id FROM profile")
        profiles = cursor.fetchall()
        
        updated_count = 0
        for profile in profiles:
            profile_id = profile[0]
            # Подсчитываем количество лайков для профиля
            cursor.execute("SELECT COUNT(*) FROM like WHERE liked_id = ?", (profile_id,))
            likes_count = cursor.fetchone()[0]
            
            # Обновляем счетчик в профиле
            cursor.execute("UPDATE profile SET likes = ? WHERE id = ?", (likes_count, profile_id))
            if cursor.rowcount > 0:
                updated_count += 1
        
        print(f"✅ Обновлено {updated_count} профилей")
        
        # 3. Проверяем целостность данных
        print("🔍 Проверка целостности данных...")
        
        # Проверяем, что все лайки ссылаются на существующие профили
        cursor.execute("""
            SELECT COUNT(*) FROM like l
            LEFT JOIN profile p ON l.user_id = p.id
            WHERE p.id IS NULL
        """)
        orphaned_user_likes = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COUNT(*) FROM like l
            LEFT JOIN profile p ON l.liked_id = p.id
            WHERE p.id IS NULL
        """)
        orphaned_liked_likes = cursor.fetchone()[0]
        
        if orphaned_user_likes > 0:
            print(f"⚠️ Найдено {orphaned_user_likes} лайков от несуществующих пользователей")
            # Удаляем лайки от несуществующих пользователей
            cursor.execute("""
                DELETE FROM like WHERE user_id NOT IN (SELECT id FROM profile)
            """)
            print(f"✅ Удалено {cursor.rowcount} лайков от несуществующих пользователей")
        
        if orphaned_liked_likes > 0:
            print(f"⚠️ Найдено {orphaned_liked_likes} лайков на несуществующие профили")
            # Удаляем лайки на несуществующие профили
            cursor.execute("""
                DELETE FROM like WHERE liked_id NOT IN (SELECT id FROM profile)
            """)
            print(f"✅ Удалено {cursor.rowcount} лайков на несуществующие профили")
        
        # 4. Создаем уникальный индекс, если его нет
        print("🔒 Создание уникального индекса...")
        
        try:
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS unique_user_like 
                ON like (user_id, liked_id)
            """)
            print("✅ Уникальный индекс создан/проверен")
        except sqlite3.IntegrityError as e:
            print(f"⚠️ Ошибка создания индекса: {e}")
        
        # 5. Финальная статистика
        cursor.execute("SELECT COUNT(*) FROM like")
        total_likes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM profile")
        total_profiles = cursor.fetchone()[0]
        
        print(f"\n📊 Финальная статистика:")
        print(f"  - Всего профилей: {total_profiles}")
        print(f"  - Всего лайков: {total_likes}")
        
        conn.commit()
        conn.close()
        
        print("\n✅ Исправление базы данных завершено успешно!")
        
    except Exception as e:
        print(f"❌ Ошибка при исправлении базы данных: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()

def show_likes_statistics():
    """Показывает статистику лайков"""
    print("📊 Статистика лайков:")
    print("=" * 40)
    
    db_path = 'instance/dating_app.db'
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Общая статистика
        cursor.execute("SELECT COUNT(*) FROM like")
        total_likes = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM profile")
        total_profiles = cursor.fetchone()[0]
        
        print(f"📈 Всего лайков: {total_likes}")
        print(f"👥 Всего профилей: {total_profiles}")
        
        # Топ профилей по лайкам
        cursor.execute("""
            SELECT p.name, p.likes, p.id
            FROM profile p
            ORDER BY p.likes DESC
            LIMIT 10
        """)
        top_profiles = cursor.fetchall()
        
        if top_profiles:
            print(f"\n🏆 Топ-10 профилей по лайкам:")
            for i, profile in enumerate(top_profiles, 1):
                print(f"  {i}. {profile[0]} (ID: {profile[2]}) - {profile[1]} лайков")
        
        # Проверка дублирующих лайков
        cursor.execute("""
            SELECT user_id, liked_id, COUNT(*) as count
            FROM like
            GROUP BY user_id, liked_id
            HAVING COUNT(*) > 1
        """)
        duplicates = cursor.fetchall()
        
        if duplicates:
            print(f"\n⚠️ Найдено {len(duplicates)} групп дублирующих лайков:")
            for duplicate in duplicates:
                print(f"  - Пользователь {duplicate[0]} лайкнул {duplicate[1]} {duplicate[2]} раз")
        else:
            print(f"\n✅ Дублирующих лайков не найдено")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при получении статистики: {e}")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 Исправление проблем с лайками")
        print("=" * 40)
        print("Команды:")
        print("  fix     - Исправить проблемы с лайками")
        print("  stats   - Показать статистику лайков")
        print("  help    - Показать эту справку")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'fix':
        fix_likes_database()
    elif command == 'stats':
        show_likes_statistics()
    elif command == 'help':
        print("🔧 Исправление проблем с лайками")
        print("=" * 40)
        print("Команды:")
        print("  fix     - Исправить проблемы с лайками")
        print("  stats   - Показать статистику лайков")
        print("  help    - Показать эту справку")
    else:
        print("❌ Неизвестная команда")
        print("Используйте: python fix_likes_database.py help")

if __name__ == '__main__':
    main() 