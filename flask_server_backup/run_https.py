#!/usr/bin/env python3
"""
Скрипт для запуска Flask сервера с HTTPS поддержкой
"""

from app import app, socketio, db
from app import cleanup_expired_profiles, PROFILE_LIFETIME_HOURS

if __name__ == '__main__':
    with app.app_context():
        db.create_all()

        # Запускаем очистку просроченных анкет при старте сервера
        print("🧹 Запуск автоматической очистки просроченных анкет...")
        deleted_count = cleanup_expired_profiles()
        print(f"⏰ Время жизни анкеты: {PROFILE_LIFETIME_HOURS} часов")

    print("🔒 Запуск сервера с HTTPS поддержкой...")
    print("📝 Для доступа используйте: https://192.168.255.137:5000")
    print("⚠️  Браузер может показать предупреждение о самоподписанном сертификате")
    print("   Это нормально для разработки. Нажмите 'Дополнительно' -> 'Перейти на сайт'")
    
    # Дополнительные настройки для HTTPS
    import ssl
    ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    
    # Запуск с HTTPS
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, 
                allow_unsafe_werkzeug=True, ssl_context='adhoc') 