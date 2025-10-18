# 🚀 Команды для развертывания черно-белого режима

## 📋 **Замените на ваши реальные данные:**

### **Вариант 1: Если у вас есть IP адрес сервера**
```bash
# Замените на ваш IP адрес и путь
scp grayscale_deployment.tar.gz root@192.168.1.100:/var/www/your-project/
# или
scp grayscale_deployment.tar.gz user@192.168.1.100:/home/user/your-project/
```

### **Вариант 2: Если у вас есть доменное имя**
```bash
# Замените на ваше доменное имя
scp grayscale_deployment.tar.gz user@your-domain.com:/path/to/project/
```

### **Вариант 3: Если используете SSH ключи**
```bash
# С SSH ключом
scp -i ~/.ssh/your-key.pem grayscale_deployment.tar.gz user@your-server:/path/to/project/
```

## 🔧 **На удаленном сервере выполните:**

```bash
# 1. Остановите текущий сервер
sudo systemctl stop your-flask-app
# или найдите процесс и остановите
ps aux | grep python
kill -9 <PID>

# 2. Создайте резервную копию
cp dating_app.db dating_app_backup_$(date +%Y%m%d_%H%M%S).db

# 3. Распакуйте архив
tar -xzf grayscale_deployment.tar.gz

# 4. Запустите миграцию (если нужно)
python migrate_add_grayscale_mode.py

# 5. Запустите сервер
python app.py
# или
sudo systemctl start your-flask-app
```

## 🧪 **Тестирование:**

1. Откройте браузер и перейдите на адрес сервера
2. Войдите в систему
3. Перейдите в настройки (⚙️)
4. Найдите кнопку черно-белого режима (⚫)
5. Переключите режим и проверьте работу

## ❓ **Если не знаете данные сервера:**

### **Найдите IP адрес сервера:**
```bash
# Если сервер в локальной сети
ip route | grep default
# или
nmap -sn 192.168.1.0/24
```

### **Найдите путь к проекту:**
```bash
# На сервере найдите где находится ваш проект
find / -name "app.py" 2>/dev/null
# или
ps aux | grep python
```

### **Проверьте SSH доступ:**
```bash
# Проверьте подключение к серверу
ssh user@your-server-ip
```

## 📞 **Нужна помощь?**

Если не знаете данные сервера, сообщите:
- Какой у вас тип сервера (VPS, облачный, локальный)?
- Как вы обычно подключаетесь к серверу?
- Есть ли у вас SSH доступ?
- Какой IP адрес или доменное имя сервера?

