#!/bin/bash

echo "🚀 Подготовка кода для деплоя на удаленный сервер..."

# Создаем резервную копию
echo "📦 Создаем резервную копию..."
tar -czf flask_server_backup_$(date +%Y%m%d_%H%M%S).tar.gz app.py *.py *.md *.sh *.html 2>/dev/null || true

# Проверяем наличие всех необходимых файлов
echo "🔍 Проверяем файлы..."
required_files=("app.py" "deploy_config.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file найден"
    else
        echo "❌ $file отсутствует"
        exit 1
    fi
done

# Проверяем, что нет проблемных ссылок на localhost в app.py
echo "🔍 Проверяем проблемные ссылки на localhost..."
# Ищем только проблемные ссылки (исключаем JavaScript проверки)
problematic_links=$(grep -n "localhost" app.py | grep -v "window.location.hostname === 'localhost'" | grep -v "isLocalhost" | grep -v "localhost:" || true)

if [ -n "$problematic_links" ]; then
    echo "⚠️ Найдены проблемные ссылки на localhost в app.py:"
    echo "$problematic_links"
    echo ""
    echo "❌ Нужно исправить эти ссылки перед деплоем!"
    exit 1
else
    echo "✅ Проблемные ссылки на localhost не найдены"
fi

# Создаем директорию для загрузок
echo "📁 Создаем директорию для загрузок..."
mkdir -p uploads
chmod 755 uploads

# Создаем .env файл для примера
echo "📝 Создаем пример .env файла..."
cat > .env.example << EOF
# Настройки для деплоя
DEPLOY_DOMAIN=https://your-domain.com
YOOKASSA_SHOP_ID=your_shop_id
YOOKASSA_SECRET_KEY=your_secret_key
YOOKASSA_TEST_MODE=False
DATABASE_URL=sqlite:///dating_app.db
SECRET_KEY=your-secret-key-here
FLASK_ENV=production
FLASK_DEBUG=False
UPLOAD_FOLDER=/var/www/uploads
EOF

echo "✅ Подготовка завершена!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Скопируйте файлы на сервер"
echo "2. Установите переменные окружения (см. .env.example)"
echo "3. Установите зависимости: pip install -r requirements.txt"
echo "4. Запустите приложение: python app.py"
echo ""
echo "🔧 Важные настройки:"
echo "   - Установите DEPLOY_DOMAIN на ваш реальный домен"
echo "   - Настройте ЮKassa (SHOP_ID и SECRET_KEY)"
echo "   - Установите YOOKASSA_TEST_MODE=False для продакшена"
echo "   - Настройте SECRET_KEY для безопасности"
