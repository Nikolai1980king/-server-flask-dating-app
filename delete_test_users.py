#!/usr/bin/env python3
"""
Скрипт для удаления тестовых пользователей
"""

from app import app, db, Profile, Like, Message

def delete_test_users():
    """Удаляет тестовых пользователей из базы данных"""
    with app.app_context():
        print("🗑️ Удаление тестовых пользователей...")
        
        # Находим тестовых пользователей
        test_users = Profile.query.filter(
            Profile.name.like('Тест_Пользователь_%')
        ).all()
        
        if not test_users:
            print("✅ Тестовых пользователей не найдено")
            return
        
        print(f"📋 Найдено тестовых пользователей: {len(test_users)}")
        
        for user in test_users:
            print(f"🗑️ Удаляем пользователя: {user.name} (ID: {user.id})")
            
            # Удаляем все лайки, связанные с этим пользователем
            likes_to_delete = Like.query.filter(
                (Like.user_id == user.id) | (Like.liked_id == user.id)
            ).all()
            
            for like in likes_to_delete:
                print(f"   💕 Удаляем лайк: {like.user_id} -> {like.liked_id}")
                db.session.delete(like)
            
            # Удаляем все сообщения, связанные с этим пользователем
            messages_to_delete = Message.query.filter(
                (Message.sender == user.id) | (Message.chat_key.like(f'%{user.id}%'))
            ).all()
            
            for message in messages_to_delete:
                print(f"   💬 Удаляем сообщение: {message.sender} -> {message.chat_key}")
                db.session.delete(message)
            
            # Удаляем самого пользователя
            db.session.delete(user)
        
        # Сохраняем изменения
        try:
            db.session.commit()
            print("✅ Тестовые пользователи успешно удалены!")
            
            # Показываем оставшихся пользователей
            remaining_users = Profile.query.all()
            print(f"\n👥 Оставшиеся пользователи: {len(remaining_users)}")
            for user in remaining_users:
                print(f"   - {user.name} ({user.id})")
                
        except Exception as e:
            db.session.rollback()
            print(f"❌ Ошибка при удалении: {e}")

if __name__ == "__main__":
    delete_test_users() 