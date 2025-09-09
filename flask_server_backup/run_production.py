#!/usr/bin/env python3
"""
Скрипт для запуска приложения в продакшене
"""
import os
import sys
from app import app

if __name__ == '__main__':
    # Настройки для продакшена
    port = int(os.environ.get('PORT', 5000))  # Изменили на 5000
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Запуск приложения в продакшене на {host}:{port}")
    print("�� Домен: ятута.рф")
    
    try:
        app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        print("\n�� Приложение остановлено")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)


