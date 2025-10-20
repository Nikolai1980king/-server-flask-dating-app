#!/usr/bin/env python3
"""
Скрипт для копирования app.py на удаленный сервер
"""

import subprocess
import sys
import os

def copy_to_server():
    """Копирует app.py на удаленный сервер"""
    
    # Проверяем, что файл существует
    if not os.path.exists('app.py'):
        print("❌ Файл app.py не найден!")
        return False
    
    print("📤 Копируем app.py на сервер...")
    
    try:
        # Пробуем разные способы копирования
        commands = [
            ['scp', 'app.py', 'root@212.67.11.50:/home/flaskapp/app/'],
            ['scp', '-o', 'StrictHostKeyChecking=no', 'app.py', 'root@212.67.11.50:/home/flaskapp/app/'],
            ['rsync', '-avz', 'app.py', 'root@212.67.11.50:/home/flaskapp/app/']
        ]
        
        for cmd in commands:
            try:
                print(f"🔄 Пробуем: {' '.join(cmd)}")
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)
                print("✅ Файл успешно скопирован!")
                return True
            except subprocess.CalledProcessError as e:
                print(f"❌ Ошибка: {e}")
                continue
        
        print("❌ Все способы копирования не удались")
        return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Копирование app.py на удаленный сервер")
    print("=" * 50)
    
    if copy_to_server():
        print("\n✅ Копирование завершено!")
        print("\n📋 Следующие шаги на сервере:")
        print("1. Подключитесь к серверу: ssh root@212.67.11.50")
        print("2. Перейдите в папку: cd /home/flaskapp/app")
        print("3. Перезапустите приложение: systemctl restart flaskapp")
        print("4. Проверьте статус: systemctl status flaskapp")
    else:
        print("\n❌ Копирование не удалось!")
        print("\n🔧 Альтернативные способы:")
        print("1. Используйте SFTP клиент (FileZilla, WinSCP)")
        print("2. Скопируйте содержимое app.py вручную")
        print("3. Используйте git для синхронизации")









