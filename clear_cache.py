#!/usr/bin/env python3
"""
Скрипт для очистки кеша и базы данных на сервере
"""
from app import db, Profile, Like, Match, PendingProfile, Message
from app import app
import os

def clear_all_data():
    """Полная очистка всех данных"""
    with app.app_context():
        print("\n" + "="*60)
        print("⚠️  ПОЛНАЯ ОЧИСТКА БАЗЫ ДАННЫХ")
        print("="*60)
        
        # Считаем что есть
        profiles = Profile.query.count()
        pending = PendingProfile.query.count()
        likes = Like.query.count()
        matches = Match.query.count()
        messages = Message.query.count()
        
        print(f"\n📊 Текущее состояние:")
        print(f"  - Профилей: {profiles}")
        print(f"  - Временных профилей: {pending}")
        print(f"  - Лайков: {likes}")
        print(f"  - Метчей: {matches}")
        print(f"  - Сообщений: {messages}")
        
        if profiles + pending + likes + matches + messages == 0:
            print("\n✅ База данных уже пустая!")
            return
        
        print("\n⚠️  Удаление всех данных...")
        
        # Удаляем все
        Like.query.delete()
        print("  ✓ Лайки удалены")
        
        Match.query.delete()
        print("  ✓ Метчи удалены")
        
        Message.query.delete()
        print("  ✓ Сообщения удалены")
        
        Profile.query.delete()
        print("  ✓ Профили удалены")
        
        PendingProfile.query.delete()
        print("  ✓ Временные профили удалены")
        
        db.session.commit()
        
        print("\n✅ База данных полностью очищена!")
        print("="*60)

def clear_likes_only():
    """Очистка только лайков и метчей"""
    with app.app_context():
        print("\n" + "="*60)
        print("🧹 ОЧИСТКА ЛАЙКОВ И МЕТЧЕЙ")
        print("="*60)
        
        likes_count = Like.query.count()
        matches_count = Match.query.count()
        
        print(f"\nТекущее состояние:")
        print(f"  - Лайков: {likes_count}")
        print(f"  - Метчей: {matches_count}")
        
        if likes_count + matches_count == 0:
            print("\n✅ Лайки и метчи уже удалены!")
            return
        
        Like.query.delete()
        Match.query.delete()
        db.session.commit()
        
        print("\n✅ Лайки и метчи удалены!")
        print(f"  ✓ Удалено лайков: {likes_count}")
        print(f"  ✓ Удалено метчей: {matches_count}")
        print("="*60)

def clear_old_profiles():
    """Удаление только временных профилей"""
    with app.app_context():
        print("\n" + "="*60)
        print("🧹 ОЧИСТКА ВРЕМЕННЫХ ПРОФИЛЕЙ")
        print("="*60)
        
        pending_count = PendingProfile.query.count()
        
        print(f"\nВременных профилей: {pending_count}")
        
        if pending_count == 0:
            print("\n✅ Временных профилей нет!")
            return
        
        PendingProfile.query.delete()
        db.session.commit()
        
        print(f"\n✅ Удалено временных профилей: {pending_count}")
        print("="*60)

if __name__ == '__main__':
    import sys
    
    print("\n🔧 ИНСТРУМЕНТ ОЧИСТКИ БАЗЫ ДАННЫХ")
    print("\nВыберите действие:")
    print("  1 - Проверить состояние БД (check_db.py)")
    print("  2 - Удалить только лайки и метчи")
    print("  3 - Удалить только временные профили")
    print("  4 - ПОЛНАЯ ОЧИСТКА (все данные)")
    print("  0 - Выход")
    
    try:
        choice = input("\nВведите номер: ").strip()
        
        if choice == '1':
            os.system('python3 check_db.py')
        elif choice == '2':
            confirm = input("⚠️  Удалить все лайки и метчи? (yes/no): ").strip().lower()
            if confirm == 'yes':
                clear_likes_only()
            else:
                print("Отменено")
        elif choice == '3':
            confirm = input("⚠️  Удалить все временные профили? (yes/no): ").strip().lower()
            if confirm == 'yes':
                clear_old_profiles()
            else:
                print("Отменено")
        elif choice == '4':
            confirm = input("⚠️⚠️⚠️  УДАЛИТЬ ВСЕ ДАННЫЕ? Это необратимо! (yes/no): ").strip().lower()
            if confirm == 'yes':
                clear_all_data()
            else:
                print("Отменено")
        elif choice == '0':
            print("Выход")
        else:
            print("Неверный выбор")
    except KeyboardInterrupt:
        print("\n\nОтменено")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
