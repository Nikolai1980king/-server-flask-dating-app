#!/usr/bin/env python3
import sys
import os
sys.path.append('.')

from app import app, db, Profile, cleanup_expired_profiles
from datetime import datetime, timezone, timedelta

def debug_cleanup():
    with app.app_context():
        print("🔍 Диагностика системы очистки анкет...")
        
        # Проверим все анкеты и их время создания
        profiles = Profile.query.all()
        print(f"📊 Всего анкет в базе: {len(profiles)}")
        
        if not profiles:
            print("❌ Анкеты не найдены")
            return
        
        expired_count = 0
        for profile in profiles:
            created_at = profile.created_at
            if created_at.tzinfo is None:
                created_at = created_at.replace(tzinfo=timezone.utc)
            
            now = datetime.now(timezone.utc)
            age_hours = (now - created_at).total_seconds() / 3600
            
            print(f"👤 Анкета {profile.id}: создана {created_at.strftime('%Y-%m-%d %H:%M:%S')}, возраст {age_hours:.1f} часов")
            
            # Проверим, должна ли быть удалена
            if age_hours > 24:
                expired_count += 1
                print(f"  ⚠️  ДОЛЖНА БЫТЬ УДАЛЕНА! (возраст {age_hours:.1f} часов)")
        
        print(f"\n📈 Найдено просроченных анкет: {expired_count}")
        
        if expired_count > 0:
            print("\n🧹 Запускаем очистку...")
            try:
                cleanup_expired_profiles()
                print("✅ Очистка завершена")
                
                # Проверим результат
                profiles_after = Profile.query.all()
                print(f"📊 Анкет после очистки: {len(profiles_after)}")
                
                if len(profiles_after) < len(profiles):
                    print(f"🎉 Удалено анкет: {len(profiles) - len(profiles_after)}")
                else:
                    print("❌ Анкеты не были удалены!")
                    
            except Exception as e:
                print(f"❌ Ошибка при очистке: {e}")
        else:
            print("✅ Просроченных анкет не найдено")

if __name__ == "__main__":
    debug_cleanup()