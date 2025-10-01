#!/usr/bin/env python3
"""
Скрипт для изменения цвета шапки с белого на темно-серый #080707
"""

def change_navbar_color():
    """Изменяет цвет шапки в файле app.py"""
    
    # Читаем файл
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Заменяем белый цвет на темно-серый
    old_color = 'background:#fff'
    new_color = 'background:#080707'
    
    if old_color in content:
        content = content.replace(old_color, new_color)
        
        # Записываем обратно
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        
        print("✅ Цвет шапки изменен с белого на темно-серый #080707")
        print("📝 Изменение: background:#fff → background:#080707")
    else:
        print("❌ Белый цвет шапки не найден в файле")

if __name__ == "__main__":
    change_navbar_color() 