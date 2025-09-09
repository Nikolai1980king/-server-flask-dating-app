#!/usr/bin/env python3
"""
Скрипт для просмотра всех пользователей в базе данных
"""

from app import app, db, Profile, Like, Message

def list_all_users():
    """Показывает всех пользователей в базе данных"""
    with app.app_context():
        print("👥 Все пользователи в базе данных:")
        print("=" * 50)
        
        profiles = Profile.query.all()
        
        if not profiles:
            print("❌ Пользователей не найдено")
            return
        
        for i, profile in enumerate(profiles, 1):
            print(f"{i}. ID: {profile.id}")
            print(f"   Имя: {profile.name}")
            print(f"   Возраст: {profile.age}")
            print(f"   Пол: {profile.gender}")
            print(f"   Создан: {profile.created_at}")
            print(f"   Заведение: {profile.venue}")
            print("-" * 30)
        
        print(f"\n📊 Всего пользователей: {len(profiles)}")
        
        # Проверяем лайки
        likes = Like.query.all()
        print(f"💕 Всего лайков: {len(likes)}")
        
        # Проверяем сообщения
        messages = Message.query.all()
        print(f"💬 Всего сообщений: {len(messages)}")

if __name__ == "__main__":
    list_all_users() 