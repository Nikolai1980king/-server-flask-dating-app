from app import db, Profile, Like, Match
from app import app

with app.app_context():
    profiles = Profile.query.all()
    likes = Like.query.all()
    
    print("\n" + "="*60)
    print("📊 ПРОВЕРКА БАЗЫ ДАННЫХ ПОСЛЕ СОЗДАНИЯ ПРОФИЛЕЙ")
    print("="*60)
    
    print(f"\n👤 Профилей: {len(profiles)}")
    for p in profiles:
        print(f"  • {p.name} (ID: {p.id[:12]}...)")
    
    print(f"\n❤️ Лайков: {len(likes)}")
    if likes:
        print("⚠️ ВНИМАНИЕ! Лайки уже есть:")
        for like in likes:
            from_p = Profile.query.get(like.user_id)
            to_p = Profile.query.get(like.liked_id)
            print(f"  • {from_p.name if from_p else '???'} лайкнул {to_p.name if to_p else '???'}")
    else:
        print("✅ Лайков нет - это правильно!")
    
    print("\n" + "="*60)
