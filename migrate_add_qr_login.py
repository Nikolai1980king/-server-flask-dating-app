#!/usr/bin/env python3
"""
Миграция для добавления таблицы QRLoginToken
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db

def migrate_add_qr_login():
    """Добавляет таблицу QRLoginToken для QR-код авторизации"""
    try:
        print("🔄 Запуск миграции: добавление таблицы QRLoginToken...")
        
        with app.app_context():
            # Создаем таблицу QRLoginToken
            db.create_all()
            print("✅ Таблица QRLoginToken создана")
            
            # Проверяем, что таблица создалась
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'qr_login_token' in tables:
                print("✅ Миграция успешно завершена")
                print("📱 Теперь доступна QR-код авторизация для ятута.рф")
                return True
            else:
                print("❌ Ошибка: таблица не создана")
                return False
                
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        return False

if __name__ == "__main__":
    migrate_add_qr_login()
