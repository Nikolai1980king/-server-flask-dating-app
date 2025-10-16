# ⚙️ Настройка .env файла для продакшена

## 📋 Что нужно настроить в .env файле:

### **1. DEPLOY_DOMAIN (ОБЯЗАТЕЛЬНО!)**
```bash
DEPLOY_DOMAIN=https://192.168.255.137
```
**Что это:** Основной домен вашего сайта
**Зачем нужно:** Для правильных переходов после оплаты

### **2. YOOKASSA_SHOP_ID (ОБЯЗАТЕЛЬНО!)**
```bash
YOOKASSA_SHOP_ID=your_shop_id_here
```
**Как получить:**
1. Зайдите в [личный кабинет ЮKassa](https://yookassa.ru/my)
2. В разделе "Настройки" найдите "Shop ID"
3. Скопируйте его и замените `your_shop_id_here`

### **3. YOOKASSA_SECRET_KEY (ОБЯЗАТЕЛЬНО!)**
```bash
YOOKASSA_SECRET_KEY=your_secret_key_here
```
**Как получить:**
1. В том же разделе "Настройки" найдите "Secret Key"
2. Скопируйте его и замените `your_secret_key_here`
3. **ВНИМАНИЕ:** Не делитесь этим ключом ни с кем!

### **4. YOOKASSA_TEST_MODE**
```bash
YOOKASSA_TEST_MODE=False
```
**Что это:** Режим работы ЮKassa
- `True` - тестовый режим (для разработки)
- `False` - продакшен режим (для реальных платежей)

### **5. SECRET_KEY (уже настроен)**
```bash
SECRET_KEY=21ad30ec69a221f0d740d8053841611cc02cc890e6d1343d4154768d6cbc0098
```
**Что это:** Секретный ключ для Flask (уже настроен)

## 🔧 Как настроить на сервере:

### **Способ 1: Через SSH (рекомендуется)**
```bash
# 1. Подключитесь к серверу
ssh root@212.67.11.50

# 2. Перейдите в папку приложения
cd /home/flaskapp/app

# 3. Отредактируйте .env файл
nano .env

# 4. Добавьте или измените нужные строки
# 5. Сохраните файл (Ctrl+X, затем Y, затем Enter)
```

### **Способ 2: Через файловый менеджер**
1. Подключитесь к серверу через FTP/SFTP
2. Откройте файл `/home/flaskapp/app/.env`
3. Отредактируйте нужные параметры
4. Сохраните файл

## 📝 Пример готового .env файла:

```bash
# Основной домен
DEPLOY_DOMAIN=https://192.168.255.137

# Flask настройки
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=21ad30ec69a221f0d740d8053841611cc02cc890e6d1343d4154768d6cbc0098

# База данных
DATABASE_URL=postgresql://flaskapp:password@localhost:5432/flaskapp

# ЮKassa настройки (ЗАМЕНИТЕ НА ВАШИ!)
YOOKASSA_SHOP_ID=123456
YOOKASSA_SECRET_KEY=test_ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890
YOOKASSA_TEST_MODE=False

# Настройки приложения
MAX_REGISTRATION_DISTANCE=3000
PROFILE_LIFETIME_HOURS=24
UPLOAD_FOLDER=/home/flaskapp/app/uploads
```

## ⚠️ Важные моменты:

1. **DEPLOY_DOMAIN** должен точно соответствовать вашему домену
2. **YOOKASSA_SHOP_ID** и **YOOKASSA_SECRET_KEY** получайте только из официального личного кабинета
3. **YOOKASSA_TEST_MODE=False** только для продакшена
4. После изменения .env файла **перезапустите приложение:**
   ```bash
   systemctl restart flaskapp
   ```

## 🧪 Проверка настроек:

После настройки проверьте:
1. ✅ Сайт открывается: `https://192.168.255.137`
2. ✅ Создание профиля работает
3. ✅ Оплата работает (в тестовом режиме сначала)
4. ✅ **После оплаты переход на профиль работает**

## 🆘 Если что-то не работает:

1. Проверьте логи приложения:
   ```bash
   journalctl -u flaskapp -f
   ```

2. Убедитесь, что все переменные окружения установлены правильно

3. Проверьте, что приложение перезапущено после изменений










