#!/usr/bin/env python3
"""
Скрипт для обновления базы данных с добавлением поля created_at
для функциональности автоматического удаления анкет по времени жизни
"""

import os
import sys
from datetime import datetime, timedelta

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db, Profile

def update_database():
    """
    Обновляет базу данных, добавляя поле created_at к существующим анкетам
    """
    print("🔄 Начинаем обновление базы данных...")
    
    with app.app_context():
        try:
            # Проверяем, существует ли поле created_at
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('profile')]
            
            if 'created_at' not in columns:
                print("📝 Добавляем поле created_at к таблице profile...")
                
                # Добавляем новое поле
                with db.engine.connect() as conn:
                    conn.execute(db.text('ALTER TABLE profile ADD COLUMN created_at DATETIME'))
                    conn.commit()
                
                # Устанавливаем время создания для существующих анкет
                # Используем время 24 часа назад, чтобы они не удалились сразу
                default_time = datetime.utcnow() - timedelta(hours=23)
                
                print(f"⏰ Устанавливаем время создания для существующих анкет: {default_time}")
                with db.engine.connect() as conn:
                    conn.execute(db.text('UPDATE profile SET created_at = :time WHERE created_at IS NULL'), {'time': default_time})
                    conn.commit()
                
                print("✅ Поле created_at успешно добавлено!")
            else:
                print("✅ Поле created_at уже существует в базе данных")
            
            # Проверяем количество анкет
            profile_count = Profile.query.count()
            print(f"📊 Всего анкет в базе данных: {profile_count}")
            
            # Показываем примеры анкет с временем создания
            profiles = Profile.query.limit(5).all()
            print("\n📋 Примеры анкет:")
            for profile in profiles:
                created_time = profile.created_at if hasattr(profile, 'created_at') else "Не установлено"
                print(f"  - {profile.name} (ID: {profile.id}): {created_time}")
            
            print("\n🎉 Обновление базы данных завершено успешно!")
            
        except Exception as e:
            print(f"❌ Ошибка при обновлении базы данных: {e}")
            return False
    
    return True

def test_cleanup_function():
    """
    Тестирует функцию очистки просроченных анкет
    """
    print("\n🧪 Тестирование функции очистки...")
    
    with app.app_context():
        try:
            from app import cleanup_expired_profiles
            
            # Временно изменяем время жизни на 1 час для тестирования
            from app import PROFILE_LIFETIME_HOURS
            print(f"⏰ Текущее время жизни анкет: {PROFILE_LIFETIME_HOURS} часов")
            
            # Создаем тестовую анкету с временем создания 2 часа назад
            test_time = datetime.utcnow() - timedelta(hours=2)
            
            # Проверяем, есть ли уже тестовая анкета
            test_profile = Profile.query.filter_by(name="ТЕСТОВАЯ_АНКЕТА").first()
            if test_profile:
                print("🗑️ Удаляем старую тестовую анкету...")
                db.session.delete(test_profile)
                db.session.commit()
            
            # Создаем новую тестовую анкету
            test_profile = Profile(
                id="test_lifetime_profile",
                name="ТЕСТОВАЯ_АНКЕТА",
                age=25,
                gender="женский",
                hobbies="тестирование",
                goal="тест",
                created_at=test_time
            )
            
            db.session.add(test_profile)
            db.session.commit()
            print(f"✅ Создана тестовая анкета с временем создания: {test_time}")
            
            # Запускаем очистку
            print("🧹 Запускаем очистку просроченных анкет...")
            deleted_count = cleanup_expired_profiles()
            
            if deleted_count > 0:
                print(f"✅ Очистка работает! Удалено {deleted_count} анкет")
            else:
                print("ℹ️ Просроченных анкет не найдено")
            
            # Проверяем, удалилась ли тестовая анкета
            test_profile = Profile.query.filter_by(id="test_lifetime_profile").first()
            if test_profile:
                print("⚠️ Тестовая анкета не удалилась (возможно, время жизни больше 2 часов)")
            else:
                print("✅ Тестовая анкета успешно удалена")
            
        except Exception as e:
            print(f"❌ Ошибка при тестировании: {e}")

if __name__ == "__main__":
    print("🚀 Скрипт обновления базы данных для функциональности времени жизни анкет")
    print("=" * 70)
    
    # Обновляем базу данных
    if update_database():
        print("\n" + "=" * 70)
        
        # Спрашиваем пользователя о тестировании
        response = input("\n🧪 Хотите протестировать функцию очистки? (y/n): ").lower().strip()
        if response in ['y', 'yes', 'да', 'д']:
            test_cleanup_function()
    
    print("\n🎯 Обновление завершено!")
    print("💡 Теперь анкеты будут автоматически удаляться по истечении времени жизни")
    print("📝 Время жизни настраивается в переменной PROFILE_LIFETIME_HOURS (строка 27 в app.py)") 