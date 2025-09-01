#!/usr/bin/env python3
"""
Скрипт для запуска приложения в продакшене
"""

import os
import sys
from app import app, socketio

if __name__ == '__main__':
    # Настройки для продакшена
    port = int(os.environ.get('PORT', 80))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print(f"🚀 Запуск приложения в продакшене на {host}:{port}")
    print("📱 Домен: ятута.рф")
    
    try:
        socketio.run(
            app, 
            host=host, 
            port=port, 
            debug=False,
            allow_unsafe_werkzeug=False
        )
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1) 