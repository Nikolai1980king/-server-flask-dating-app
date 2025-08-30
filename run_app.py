#!/usr/bin/env python3
"""
Скрипт для запуска приложения с автоматическим выбором порта
"""

import socket
import subprocess
import sys
import time

def find_free_port(start_port=5000, max_attempts=10):
    """Находит свободный порт начиная с start_port"""
    for port in range(start_port, start_port + max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('localhost', port))
                return port
        except OSError:
            continue
    return None

def kill_process_on_port(port):
    """Убивает процесс, использующий указанный порт"""
    try:
        result = subprocess.run(['lsof', '-ti', f':{port}'], 
                              capture_output=True, text=True)
        if result.stdout.strip():
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    subprocess.run(['kill', '-9', pid])
                    print(f"Процесс {pid} на порту {port} остановлен")
    except Exception as e:
        print(f"Ошибка при остановке процесса: {e}")

def main():
    """Основная функция запуска"""
    print("🚀 Запуск приложения знакомств с геолокацией")
    print("=" * 50)
    
    # Проверяем порт 5000
    port = 5000
    print(f"Проверяем порт {port}...")
    
    # Пытаемся освободить порт 5000
    kill_process_on_port(5000)
    time.sleep(1)
    
    # Проверяем, свободен ли порт
    free_port = find_free_port(5000, 5)
    
    if free_port == 5000:
        print("✅ Порт 5000 свободен")
        port = 5000
    else:
        print(f"⚠️  Порт 5000 занят, используем порт {free_port}")
        port = free_port
    
    print(f"🌐 Приложение будет доступно по адресу: http://localhost:{port}")
    print("=" * 50)
    
    # Запускаем приложение
    try:
        # Изменяем порт в app.py временно
        with open('app.py', 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Заменяем порт в строке запуска
        new_content = content.replace(
            "socketio.run(app, host='0.0.0.0', port=5000, debug=True, allow_unsafe_werkzeug=True)",
            f"socketio.run(app, host='0.0.0.0', port={port}, debug=True, allow_unsafe_werkzeug=True)"
        )
        
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print("🚀 Запускаем приложение...")
        subprocess.run([sys.executable, 'app.py'])
        
    except KeyboardInterrupt:
        print("\n⏹️  Приложение остановлено пользователем")
    except Exception as e:
        print(f"❌ Ошибка при запуске: {e}")

if __name__ == "__main__":
    main() 