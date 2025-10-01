#!/usr/bin/env python3
import sqlite3

# Подключаемся к базе данных
conn = sqlite3.connect('dating_app.db')
cursor = conn.cursor()

# Проверяем количество анкет
cursor.execute('SELECT COUNT(*) FROM profile')
count = cursor.fetchone()[0]
print(f"Анкет в базе: {count}")

if count > 0:
    # Показываем первые 3 анкеты
    cursor.execute('SELECT id, name, age FROM profile LIMIT 3')
    profiles = cursor.fetchall()
    print("Первые 3 анкеты:")
    for p in profiles:
        print(f"  ID: {p[0]}, Имя: {p[1]}, Возраст: {p[2]}")
    
    # Удаляем все анкеты
    cursor.execute('DELETE FROM profile')
    cursor.execute('DELETE FROM like')
    cursor.execute('DELETE FROM message')
    conn.commit()
    print("✅ Все анкеты, лайки и сообщения удалены!")
else:
    print("✅ Анкет нет, база уже пустая")

# Проверяем финальное состояние
cursor.execute('SELECT COUNT(*) FROM profile')
final_count = cursor.fetchone()[0]
print(f"Анкет после очистки: {final_count}")

conn.close()