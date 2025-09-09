# 🔧 Ручное исправление сервера

## 🚨 Проблема: Внутренняя ошибка сервера

### 📋 Шаги для исправления:

#### 1. **Подключитесь к серверу вручную:**
```bash
ssh root@212.67.11.50
```

#### 2. **Проверьте статус Flask приложения:**
```bash
systemctl status flaskapp
```

#### 3. **Остановите все процессы Python:**
```bash
pkill -f python
pkill -f flask
systemctl stop flaskapp
```

#### 4. **Проверьте логи ошибок:**
```bash
journalctl -u flaskapp -n 20
```

#### 5. **Проверьте права доступа:**
```bash
ls -la /home/flaskapp/app/
ls -la /home/flaskapp/app/instance/
```

#### 6. **Исправьте права доступа:**
```bash
chown -R flaskapp:flaskapp /home/flaskapp/app/
chmod -R 755 /home/flaskapp/app/
```

#### 7. **Проверьте базу данных:**
```bash
ls -lh /home/flaskapp/app/instance/dating_app.db
```

#### 8. **Если база данных повреждена, создайте новую:**
```bash
cd /home/flaskapp/app
rm -f instance/dating_app.db
python3 -c "
from app import db
db.create_all()
print('✅ Новая база данных создана')
"
```

#### 9. **Запустите приложение:**
```bash
systemctl start flaskapp
systemctl status flaskapp
```

#### 10. **Проверьте логи после запуска:**
```bash
journalctl -u flaskapp -n 10
```

#### 11. **Проверьте, что приложение отвечает:**
```bash
curl http://localhost:5000/
```

### 🔍 Возможные причины ошибки:

1. **Поврежденная база данных**
2. **Неправильные права доступа**
3. **Конфликт портов**
4. **Ошибки в коде**
5. **Недостаточно места на диске**

### 📞 Если ничего не помогает:

1. **Перезагрузите сервер:**
   ```bash
   reboot
   ```

2. **После перезагрузки запустите приложение:**
   ```bash
   systemctl start flaskapp
   ```

3. **Проверьте статус:**
   ```bash
   systemctl status flaskapp
   ```

### 🎯 Ожидаемый результат:

После исправления:
- ✅ Flask приложение запущено
- ✅ Статус: `active (running)`
- ✅ Сайт отвечает в браузере
- ✅ Карта работает
- ✅ Ограничение на одну анкету работает

---

**💡 Совет:** Если проблема повторяется, возможно, нужно обновить код на сервере или проверить зависимости Python. 