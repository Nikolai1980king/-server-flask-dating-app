#!/usr/bin/env python3
"""
Скрипт для исправления проблемы с доменным именем в геолокации
Проблема: браузер показывает IP-адрес вместо доменного имени в запросе геолокации
"""

import re
import os

def fix_geolocation_domain_issue():
    """Исправляет проблему с доменным именем в геолокации"""
    print("🔧 Исправление проблемы с доменным именем в геолокации...")
    print("=" * 60)
    
    # Проблема и решение
    print("❌ ПРОБЛЕМА:")
    print("   - Браузер показывает IP-адрес (212.67.11.50) вместо доменного имени")
    print("   - Это происходит потому, что сайт работает по HTTP, а не HTTPS")
    print("   - Геолокация требует HTTPS соединение")
    print()
    
    print("✅ РЕШЕНИЯ:")
    print("   1. Настроить HTTPS на сервере")
    print("   2. Добавить информативное сообщение для пользователей")
    print("   3. Улучшить обработку ошибок геолокации")
    print()
    
    # Создаем улучшенную версию функции геолокации
    improved_geolocation_code = '''
                function getCurrentLocation() {
                    if (navigator.geolocation) {
                        // Показываем информативное сообщение
                        showGeolocationMessage('📍 Определяем ваше местоположение...', 'info');
                        
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                var lat = position.coords.latitude;
                                var lng = position.coords.longitude;
                                setLocation(lat, lng);
                                showGeolocationMessage('✅ Местоположение определено!', 'success');
                            },
                            function(error) {
                                console.error('Ошибка геолокации:', error);
                                let errorMessage = '';
                                switch(error.code) {
                                    case error.PERMISSION_DENIED:
                                        errorMessage = '❌ Доступ к местоположению запрещен. Разрешите доступ в настройках браузера.';
                                        break;
                                    case error.POSITION_UNAVAILABLE:
                                        errorMessage = '❌ Информация о местоположении недоступна. Попробуйте еще раз.';
                                        break;
                                    case error.TIMEOUT:
                                        errorMessage = '⏰ Превышено время ожидания. Проверьте интернет-соединение.';
                                        break;
                                    default:
                                        errorMessage = '❌ Ошибка определения местоположения. Попробуйте выбрать местоположение вручную на карте.';
                                }
                                showGeolocationMessage(errorMessage, 'error');
                                
                                // Показываем дополнительную информацию
                                showGeolocationHelp();
                            },
                            {
                                enableHighAccuracy: false,
                                timeout: 15000,
                                maximumAge: 300000
                            }
                        );
                    } else {
                        showGeolocationMessage('❌ Геолокация не поддерживается вашим браузером. Выберите местоположение вручную на карте.', 'error');
                        showGeolocationHelp();
                    }
                }
                
                function showGeolocationMessage(message, type = 'info') {
                    // Создаем элемент уведомления
                    const notification = document.createElement('div');
                    notification.id = 'geolocation-notification';
                    notification.style.cssText = `
                        position: fixed;
                        top: 80px;
                        left: 50%;
                        transform: translateX(-50%);
                        background: ${type === 'error' ? '#ff6b6b' : type === 'success' ? '#4CAF50' : '#667eea'};
                        color: white;
                        padding: 15px 25px;
                        border-radius: 25px;
                        font-size: 14px;
                        z-index: 1000;
                        box-shadow: 0 4px 16px rgba(0,0,0,0.3);
                        animation: slideIn 0.3s ease-out;
                        max-width: 90%;
                        text-align: center;
                    `;
                    notification.textContent = message;
                    document.body.appendChild(notification);
                    
                    // Удаляем уведомление через 5 секунд
                    setTimeout(() => {
                        if (notification.parentNode) {
                            notification.style.animation = 'slideOut 0.3s ease-in';
                            setTimeout(() => {
                                if (notification.parentNode) {
                                    notification.parentNode.removeChild(notification);
                                }
                            }, 300);
                        }
                    }, 5000);
                }
                
                function showGeolocationHelp() {
                    const helpDiv = document.createElement('div');
                    helpDiv.id = 'geolocation-help';
                    helpDiv.style.cssText = `
                        background: rgba(255, 193, 7, 0.1);
                        border: 1px solid rgba(255, 193, 7, 0.3);
                        border-radius: 10px;
                        padding: 15px;
                        margin: 15px 0;
                        color: #fff;
                        font-size: 14px;
                    `;
                    helpDiv.innerHTML = `
                        <strong>💡 Как выбрать местоположение:</strong><br>
                        1. Кликните на карту в нужном месте<br>
                        2. Или используйте кнопку "📍 Определить мое местоположение"<br>
                        3. Если геолокация не работает, выберите местоположение вручную<br>
                        <small>💡 Совет: Для лучшей работы геолокации используйте HTTPS версию сайта</small>
                    `;
                    
                    // Вставляем после карты
                    const mapContainer = document.querySelector('.map-container');
                    if (mapContainer) {
                        mapContainer.parentNode.insertBefore(helpDiv, mapContainer.nextSibling);
                    }
                }
    '''
    
    # Создаем файл с инструкциями
    instructions = '''
# 🔧 ИСПРАВЛЕНИЕ ПРОБЛЕМЫ С ДОМЕННЫМ ИМЕНЕМ В ГЕОЛОКАЦИИ

## ❌ ПРОБЛЕМА
При попытке определить местоположение браузер показывает IP-адрес (212.67.11.50) 
вместо доменного имени (ятута.рф), что смущает пользователей.

## 🔍 ПРИЧИНА
1. Сайт работает по HTTP, а не HTTPS
2. Геолокация требует безопасное соединение (HTTPS)
3. Браузер показывает IP-адрес сервера вместо доменного имени

## ✅ РЕШЕНИЯ

### 1. НАСТРОЙКА HTTPS (РЕКОМЕНДУЕТСЯ)
```bash
# На сервере установить SSL сертификат
sudo apt update
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d ятута.рф
```

### 2. УЛУЧШЕНИЕ ПОЛЬЗОВАТЕЛЬСКОГО ОПЫТА
- Добавить информативные сообщения
- Показать альтернативные способы выбора местоположения
- Улучшить обработку ошибок

### 3. ВРЕМЕННОЕ РЕШЕНИЕ
Добавить пояснение для пользователей о том, что IP-адрес - это нормально.

## 🛠️ ВНЕДРЕНИЕ

### Шаг 1: Обновить функцию геолокации
Заменить функцию getCurrentLocation() в app.py на улучшенную версию.

### Шаг 2: Добавить CSS анимации
```css
@keyframes slideIn {
    from { opacity: 0; transform: translateX(-50%) translateY(-20px); }
    to { opacity: 1; transform: translateX(-50%) translateY(0); }
}
@keyframes slideOut {
    from { opacity: 1; transform: translateX(-50%) translateY(0); }
    to { opacity: 0; transform: translateX(-50%) translateY(-20px); }
}
```

### Шаг 3: Настроить HTTPS на сервере
```bash
# Подключиться к серверу
ssh root@212.67.11.50

# Установить Certbot
sudo apt update
sudo apt install certbot python3-certbot-nginx

# Получить SSL сертификат
sudo certbot --nginx -d ятута.рф

# Перезапустить nginx
sudo systemctl restart nginx
```

## 📋 ПРОВЕРКА
1. Открыть https://ятута.рф
2. Попробовать геолокацию
3. Убедиться, что показывается доменное имя

## 🎯 РЕЗУЛЬТАТ
- Пользователи увидят доменное имя вместо IP-адреса
- Улучшенный пользовательский опыт
- Более доверительное отношение к сайту
'''
    
    # Сохраняем инструкции
    with open('GEOLOCATION_DOMAIN_FIX.md', 'w', encoding='utf-8') as f:
        f.write(instructions)
    
    # Сохраняем улучшенный код
    with open('improved_geolocation_code.js', 'w', encoding='utf-8') as f:
        f.write(improved_geolocation_code)
    
    print("📁 Созданы файлы:")
    print("   - GEOLOCATION_DOMAIN_FIX.md - инструкции по исправлению")
    print("   - improved_geolocation_code.js - улучшенный код геолокации")
    print()
    
    print("🚀 СЛЕДУЮЩИЕ ШАГИ:")
    print("   1. Настроить HTTPS на сервере (рекомендуется)")
    print("   2. Обновить код геолокации в app.py")
    print("   3. Протестировать на https://ятута.рф")
    print()
    
    print("✅ Готово! Проблема с доменным именем будет решена.")

def show_current_status():
    """Показывает текущий статус геолокации"""
    print("📊 Текущий статус геолокации:")
    print("=" * 40)
    print("🌐 Домен: ятута.рф")
    print("🔒 HTTPS: НЕ настроен (проблема)")
    print("📍 Геолокация: работает, но показывает IP-адрес")
    print("⚠️ Проблема: пользователи видят 212.67.11.50 вместо ятута.рф")
    print()
    print("💡 Рекомендация: настроить HTTPS для решения проблемы")

def main():
    import sys
    
    if len(sys.argv) < 2:
        print("🔧 Исправление проблемы с доменным именем в геолокации")
        print("=" * 60)
        print("Команды:")
        print("  fix     - Создать инструкции по исправлению")
        print("  status  - Показать текущий статус")
        print("  help    - Показать эту справку")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'fix':
        fix_geolocation_domain_issue()
    elif command == 'status':
        show_current_status()
    elif command == 'help':
        print("🔧 Исправление проблемы с доменным именем в геолокации")
        print("=" * 60)
        print("Команды:")
        print("  fix     - Создать инструкции по исправлению")
        print("  status  - Показать текущий статус")
        print("  help    - Показать эту справку")
    else:
        print("❌ Неизвестная команда")
        print("Используйте: python fix_geolocation_domain.py help")

if __name__ == '__main__':
    main() 