#!/usr/bin/env python3
"""
Скрипт для управления временем жизни анкет
"""

import os
import sys
import sqlite3
from datetime import datetime, timedelta

def show_current_settings():
    """Показывает текущие настройки времени жизни анкет"""
    print("🔧 Текущие настройки времени жизни анкет:")
    print("=" * 50)
    
    # Читаем значение из app.py
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if 'PROFILE_LIFETIME_HOURS =' in line:
                    hours = line.split('=')[1].strip().split('#')[0].strip()
                    print(f"📝 Время жизни в коде: {hours} часов")
                    break
    except Exception as e:
        print(f"❌ Ошибка чтения app.py: {e}")
    
    # Проверяем базу данных
    db_path = 'instance/dating_app.db'
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Количество анкет
        cursor.execute("SELECT COUNT(*) FROM profile")
        total_profiles = cursor.fetchone()[0]
        print(f"📊 Всего анкет в базе: {total_profiles}")
        
        # Анкеты по возрасту
        if total_profiles > 0:
            cursor.execute("SELECT created_at FROM profile ORDER BY created_at DESC")
            profiles = cursor.fetchall()
            
            now = datetime.utcnow()
            recent_24h = 0
            recent_7d = 0
            old_7d = 0
            
            for profile in profiles:
                if profile[0]:
                    created = datetime.fromisoformat(profile[0].replace('Z', '+00:00'))
                    age = now - created.replace(tzinfo=None)
                    
                    if age <= timedelta(hours=24):
                        recent_24h += 1
                    if age <= timedelta(days=7):
                        recent_7d += 1
                    else:
                        old_7d += 1
            
            print(f"📅 Анкет за последние 24 часа: {recent_24h}")
            print(f"📅 Анкет за последние 7 дней: {recent_7d}")
            print(f"📅 Анкет старше 7 дней: {old_7d}")
        
        conn.close()
    else:
        print("❌ База данных не найдена")

def change_lifetime(hours):
    """Изменяет время жизни анкет в коде"""
    print(f"🔧 Изменение времени жизни на {hours} часов...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем значение
        new_content = content.replace(
            'PROFILE_LIFETIME_HOURS = 24',
            f'PROFILE_LIFETIME_HOURS = {hours}'
        ).replace(
            'PROFILE_LIFETIME_HOURS = 168',
            f'PROFILE_LIFETIME_HOURS = {hours}'
        ).replace(
            'PROFILE_LIFETIME_HOURS = 1',
            f'PROFILE_LIFETIME_HOURS = {hours}'
        ).replace(
            'PROFILE_LIFETIME_HOURS = 6',
            f'PROFILE_LIFETIME_HOURS = {hours}'
        ).replace(
            'PROFILE_LIFETIME_HOURS = 12',
            f'PROFILE_LIFETIME_HOURS = {hours}'
        ).replace(
            'PROFILE_LIFETIME_HOURS = 48',
            f'PROFILE_LIFETIME_HOURS = {hours}'
        )
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"✅ Время жизни изменено на {hours} часов")
        print("🔄 Перезапустите сервер для применения изменений")
        
    except Exception as e:
        print(f"❌ Ошибка изменения времени жизни: {e}")

def disable_auto_cleanup():
    """Отключает автоматическое удаление анкет"""
    print("🚫 Отключение автоматического удаления анкет...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Комментируем строки с автоматической очисткой
        new_content = content.replace(
            '# Запускаем очистку просроченных анкет при старте сервера',
            '# ЗАКЛЮЧЕНО: Запускаем очистку просроченных анкет при старте сервера'
        ).replace(
            'print("🧹 Запуск автоматической очистки просроченных анкет...")',
            '# print("🧹 Запуск автоматической очистки просроченных анкет...")'
        ).replace(
            'deleted_count = cleanup_expired_profiles()',
            '# deleted_count = cleanup_expired_profiles()'
        ).replace(
            'print(f"⏰ Время жизни анкеты: {PROFILE_LIFETIME_HOURS} часов")',
            '# print(f"⏰ Время жизни анкеты: {PROFILE_LIFETIME_HOURS} часов")'
        )
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Автоматическое удаление анкет отключено")
        print("🔄 Перезапустите сервер для применения изменений")
        
    except Exception as e:
        print(f"❌ Ошибка отключения автоматической очистки: {e}")

def enable_auto_cleanup():
    """Включает автоматическое удаление анкет"""
    print("✅ Включение автоматического удаления анкет...")
    
    try:
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Раскомментируем строки с автоматической очисткой
        new_content = content.replace(
            '# ЗАКЛЮЧЕНО: Запускаем очистку просроченных анкет при старте сервера',
            '# Запускаем очистку просроченных анкет при старте сервера'
        ).replace(
            '# print("🧹 Запуск автоматической очистки просроченных анкет...")',
            'print("🧹 Запуск автоматической очистки просроченных анкет...")'
        ).replace(
            '# deleted_count = cleanup_expired_profiles()',
            'deleted_count = cleanup_expired_profiles()'
        ).replace(
            '# print(f"⏰ Время жизни анкеты: {PROFILE_LIFETIME_HOURS} часов")',
            'print(f"⏰ Время жизни анкеты: {PROFILE_LIFETIME_HOURS} часов")'
        )
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("✅ Автоматическое удаление анкет включено")
        print("🔄 Перезапустите сервер для применения изменений")
        
    except Exception as e:
        print(f"❌ Ошибка включения автоматической очистки: {e}")

def cleanup_old_profiles():
    """Ручная очистка старых анкет"""
    print("🧹 Ручная очистка старых анкет...")
    
    db_path = 'instance/dating_app.db'
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем текущее время жизни из кода
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
            for line in content.split('\n'):
                if 'PROFILE_LIFETIME_HOURS =' in line:
                    hours = int(line.split('=')[1].strip().split('#')[0].strip())
                    break
            else:
                hours = 24  # По умолчанию
        
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Находим старые анкеты
        cursor.execute("SELECT id, name, created_at FROM profile WHERE created_at < ?", (cutoff_time,))
        old_profiles = cursor.fetchall()
        
        if not old_profiles:
            print("✅ Старых анкет не найдено")
            return
        
        print(f"📋 Найдено {len(old_profiles)} старых анкет:")
        for profile in old_profiles:
            print(f"  - {profile[1]} (ID: {profile[0]}, создана: {profile[2]})")
        
        # Удаляем старые анкеты
        cursor.execute("DELETE FROM profile WHERE created_at < ?", (cutoff_time,))
        deleted_count = cursor.rowcount
        
        # Удаляем связанные лайки
        cursor.execute("DELETE FROM like WHERE user_id NOT IN (SELECT id FROM profile)")
        cursor.execute("DELETE FROM like WHERE liked_id NOT IN (SELECT id FROM profile)")
        
        # Удаляем связанные сообщения
        cursor.execute("DELETE FROM message WHERE chat_key NOT LIKE '%' || (SELECT id FROM profile LIMIT 1) || '%'")
        
        conn.commit()
        conn.close()
        
        print(f"✅ Удалено {deleted_count} старых анкет")
        
    except Exception as e:
        print(f"❌ Ошибка очистки: {e}")

def show_help():
    """Показывает справку"""
    print("🔧 Управление временем жизни анкет")
    print("=" * 40)
    print("Команды:")
    print("  show          - Показать текущие настройки")
    print("  change <часы> - Изменить время жизни (например: change 168)")
    print("  disable       - Отключить автоматическое удаление")
    print("  enable        - Включить автоматическое удаление")
    print("  cleanup       - Ручная очистка старых анкет")
    print("  help          - Показать эту справку")
    print()
    print("Примеры:")
    print("  python manage_profile_lifetime.py show")
    print("  python manage_profile_lifetime.py change 168")
    print("  python manage_profile_lifetime.py disable")
    print("  python manage_profile_lifetime.py cleanup")

def main():
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'show':
        show_current_settings()
    elif command == 'change' and len(sys.argv) > 2:
        try:
            hours = int(sys.argv[2])
            change_lifetime(hours)
        except ValueError:
            print("❌ Ошибка: укажите количество часов (число)")
    elif command == 'disable':
        disable_auto_cleanup()
    elif command == 'enable':
        enable_auto_cleanup()
    elif command == 'cleanup':
        cleanup_old_profiles()
    elif command == 'help':
        show_help()
    else:
        print("❌ Неизвестная команда")
        show_help()

if __name__ == '__main__':
    main() 