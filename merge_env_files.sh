#!/bin/bash

echo "🔧 Объединение настроек .env файлов..."
echo "=" * 50

# Создаем объединенный .env файл
cat > .env.merged << 'EOF'
# Объединенные настройки для локальной разработки и деплоя
# ============================================================================

# Flask настройки
FLASK_ENV=production
FLASK_DEBUG=False
SECRET_KEY=21ad30ec69a221f0d740d8053841611cc02cc890e6d1343d4154768d6cbc0098

# База данных
DATABASE_URL=postgresql://flaskapp:password@localhost:5432/flaskapp

# Настройки приложения
MAX_REGISTRATION_DISTANCE=3000
PROFILE_LIFETIME_HOURS=24
UPLOAD_FOLDER=/home/flaskapp/app/uploads

# Настройки для деплоя (для сервера)
DEPLOY_DOMAIN=https://192.168.255.137
YOOKASSA_SHOP_ID=your_shop_id_here
YOOKASSA_SECRET_KEY=your_secret_key_here
YOOKASSA_TEST_MODE=False

# ============================================================================
# ИНСТРУКЦИЯ:
# 1. Скопируйте этот файл в .env на сервере
# 2. Замените your_shop_id_here и your_secret_key_here на ваши данные ЮKassa
# 3. Для локальной разработки можете оставить YOOKASSA_TEST_MODE=True
# ============================================================================
EOF

echo "✅ Создан объединенный .env файл: .env.merged"
echo ""
echo "📋 Сравнение файлов:"
echo ""
echo "=== Ваш текущий .env ==="
cat .env
echo ""
echo "=== Новый объединенный .env ==="
cat .env.merged
echo ""
echo "📋 Что добавилось:"
echo "  ✅ DEPLOY_DOMAIN=https://192.168.255.137"
echo "  ✅ YOOKASSA_SHOP_ID=your_shop_id_here"
echo "  ✅ YOOKASSA_SECRET_KEY=your_secret_key_here"
echo "  ✅ YOOKASSA_TEST_MODE=False"
echo "  ✅ UPLOAD_FOLDER=/home/flaskapp/app/uploads"
echo ""
echo "🔄 Для применения на сервере:"
echo "  1. Скопируйте .env.merged на сервер"
echo "  2. Переименуйте его в .env"
echo "  3. Отредактируйте настройки ЮKassa"
echo ""
echo "📁 Файл готов: .env.merged"

















