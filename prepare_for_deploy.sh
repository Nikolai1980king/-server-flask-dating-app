#!/bin/bash

echo "📦 Подготовка пакета для деплоя на сервер"
echo "=========================================="

# Проверяем, что мы в правильной директории
if [ ! -f "app.py" ]; then
    echo "❌ Ошибка: Файл app.py не найден!"
    echo "Запустите скрипт из корневой папки проекта"
    exit 1
fi

# Удаляем старый архив, если существует
if [ -f "deploy_package.tar.gz" ]; then
    echo "🗑️ Удаляем старый архив..."
    rm deploy_package.tar.gz
fi

# Создаем временную папку для сборки
echo "📁 Создаем временную папку..."
TEMP_DIR="deploy_temp"
rm -rf $TEMP_DIR
mkdir -p $TEMP_DIR

# Копируем необходимые файлы
echo "📋 Копируем файлы приложения..."
cp app.py $TEMP_DIR/
cp requirements.txt $TEMP_DIR/
cp deploy_config.py $TEMP_DIR/

# Копируем миграции
echo "🔄 Копируем миграции..."
cp migrate_*.py $TEMP_DIR/ 2>/dev/null || true

# Копируем файл .env.example если есть
if [ -f "env_production_template.txt" ]; then
    echo "⚙️ Копируем шаблон .env..."
    cp env_production_template.txt $TEMP_DIR/.env.example
fi

# Создаем папки
echo "📁 Создаем структуру папок..."
mkdir -p $TEMP_DIR/instance
mkdir -p $TEMP_DIR/uploads
mkdir -p $TEMP_DIR/static
mkdir -p $TEMP_DIR/templates

# Копируем статику и шаблоны, если они есть
if [ -d "static" ]; then
    echo "🎨 Копируем статические файлы..."
    cp -r static/* $TEMP_DIR/static/ 2>/dev/null || true
fi

if [ -d "templates" ]; then
    echo "📝 Копируем шаблоны..."
    cp -r templates/* $TEMP_DIR/templates/ 2>/dev/null || true
fi

# Создаем архив
echo "🗜️ Создаем архив..."
cd $TEMP_DIR
tar -czf ../deploy_package.tar.gz ./*
cd ..

# Удаляем временную папку
echo "🧹 Очищаем временные файлы..."
rm -rf $TEMP_DIR

# Проверяем размер архива
SIZE=$(du -h deploy_package.tar.gz | cut -f1)
echo ""
echo "✅ Архив создан успешно!"
echo "📦 Размер: $SIZE"
echo "📄 Файл: deploy_package.tar.gz"
echo ""
echo "🚀 Теперь запустите: ./deploy_to_server.sh"
echo ""













