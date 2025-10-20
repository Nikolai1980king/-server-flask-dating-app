# 🔧 ИСПРАВЛЕНИЕ ОШИБКИ NGINX

## ❌ **ПРОБЛЕМА:**
```
nginx: [emerg] unknown directive "Secure" in /etc/nginx/sites-enabled/yatuta-rf:34
```

## ✅ **РЕШЕНИЕ:**

### **Вариант 1: Использовать исправленный скрипт (РЕКОМЕНДУЕТСЯ)**
```bash
# На сервере выполните:
./deploy_to_server_fixed.sh
```

### **Вариант 2: Ручное исправление**
```bash
# 1. Остановите Nginx
sudo systemctl stop nginx

# 2. Скопируйте исправленную конфигурацию
sudo cp nginx_https_fixed.conf /etc/nginx/sites-available/yatuta-rf

# 3. Проверьте конфигурацию
sudo nginx -t

# 4. Если все ОК, перезапустите
sudo systemctl start nginx
```

### **Вариант 3: Быстрое исправление через sed**
```bash
# Удалите проблемную строку
sudo sed -i '/proxy_cookie_path.*Secure/d' /etc/nginx/sites-available/yatuta-rf

# Проверьте конфигурацию
sudo nginx -t

# Перезапустите Nginx
sudo systemctl reload nginx
```

## 🔍 **ПРОВЕРКА:**
```bash
# Проверьте, что Nginx работает
sudo systemctl status nginx

# Проверьте сайт
curl -I https://ятута.рф
```

## 📋 **ЧТО БЫЛО ИСПРАВЛЕНО:**
- ❌ Удалена неправильная директива `proxy_cookie_path / /; Secure; SameSite=Lax;`
- ✅ Оставлена только правильная директива `proxy_cookie_path / /;`
- ✅ Secure атрибут для куки теперь добавляется через Flask настройки
- ✅ Все заголовки безопасности сохранены

## 🎯 **РЕЗУЛЬТАТ:**
После исправления:
- ✅ Nginx запустится без ошибок
- ✅ Все функции безопасности будут работать
- ✅ Куки будут защищены через Flask настройки
- ✅ Сайт будет доступен по HTTPS

