#!/usr/bin/env python3
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

def main():
    print("🔍 Ищем свободный порт...")
    
    # Останавливаем все процессы Python
    try:
        subprocess.run(['pkill', '-f', 'python.*app.py'], 
                      capture_output=True, timeout=5)
        print("✅ Остановлены старые процессы")
    except:
        pass
    
    # Ждем освобождения портов
    time.sleep(2)
    
    # Ищем свободный порт
    port = find_free_port()
    if port is None:
        print("❌ Не удалось найти свободный порт")
        sys.exit(1)
    
    print(f"✅ Найден свободный порт: {port}")
    print(f"🌐 Сервер будет доступен по адресу: http://localhost:{port}")
    print("🚀 Запускаем сервер...")
    print("-" * 50)
    
    # Запускаем сервер на найденном порту
    try:
        subprocess.run([sys.executable, 'app.py'], 
                      env={'FLASK_RUN_PORT': str(port)})
    except KeyboardInterrupt:
        print("\n🛑 Сервер остановлен пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска сервера: {e}")

if __name__ == "__main__":
    main() 