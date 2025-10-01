#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для инициализации таблиц платежей в базе данных
Добавляет поля is_paid и payment_date в таблицу profiles
Создает таблицу payments
"""

import sqlite3
import os
from datetime import datetime

def init_payment_tables():
    """Инициализация таблиц для системы платежей"""
    
    # Путь к базе данных
    db_path = 'instance/profiles.db'
    
    if not os.path.exists(db_path):
        print(f"❌ База данных не найдена: {db_path}")
        return False
    
    try:
        # Подключаемся к базе данных
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        print("🔄 Инициализация таблиц платежей...")
        
        # Проверяем, существуют ли уже поля is_paid и payment_date
        cursor.execute("PRAGMA table_info(profiles)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'is_paid' not in columns:
            print("➕ Добавляем поле is_paid в таблицу profiles...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN is_paid BOOLEAN DEFAULT 0")
        else:
            print("✅ Поле is_paid уже существует")
        
        if 'payment_date' not in columns:
            print("➕ Добавляем поле payment_date в таблицу profiles...")
            cursor.execute("ALTER TABLE profiles ADD COLUMN payment_date DATETIME")
        else:
            print("✅ Поле payment_date уже существует")
        
        # Создаем таблицу payments
        print("➕ Создаем таблицу payments...")
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id VARCHAR(255) NOT NULL,
                amount REAL NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                description TEXT,
                payment_method VARCHAR(100),
                yookassa_payment_id VARCHAR(255),
                yookassa_payment_url TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Обновляем существующие профили - помечаем как неоплаченные
        print("🔄 Обновляем существующие профили...")
        cursor.execute("UPDATE profiles SET is_paid = 0 WHERE is_paid IS NULL")
        
        # Сохраняем изменения
        conn.commit()
        
        print("✅ Таблицы платежей успешно инициализированы!")
        
        # Показываем статистику
        cursor.execute("SELECT COUNT(*) FROM profiles")
        profiles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM profiles WHERE is_paid = 1")
        paid_profiles_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM payments")
        payments_count = cursor.fetchone()[0]
        
        print(f"📊 Статистика:")
        print(f"   - Всего профилей: {profiles_count}")
        print(f"   - Оплаченных профилей: {paid_profiles_count}")
        print(f"   - Всего платежей: {payments_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Ошибка инициализации таблиц: {e}")
        if 'conn' in locals():
            conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Инициализация таблиц платежей ЮKassa")
    print("=" * 50)
    
    success = init_payment_tables()
    
    if success:
        print("\n🎉 Готово! Теперь можно тестировать систему платежей.")
        print("\n📝 Следующие шаги:")
        print("   1. Запустите сервер: python3 app.py")
        print("   2. Создайте профиль")
        print("   3. Перейдите на страницу оплаты")
        print("   4. Протестируйте платеж")
        print("   5. Проверьте админ-панель: /admin/payments")
    else:
        print("\n❌ Ошибка инициализации. Проверьте логи выше.")