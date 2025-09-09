#!/usr/bin/env python3
"""
Простая версия с HTTPS для загрузки файлов
"""

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Настройки для HTTPS
app.config['PREFERRED_URL_SCHEME'] = 'https'
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB

UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Заголовки безопасности
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    if request.is_secure:
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>HTTPS Загрузка файлов</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            .form-group { margin: 15px 0; }
            input[type="file"] { padding: 10px; border: 2px solid #ddd; border-radius: 5px; }
            button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            #result { margin-top: 20px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background: #f9f9f9; }
            .error { color: red; }
            .success { color: green; }
        </style>
    </head>
    <body>
        <h1>HTTPS Загрузка файлов</h1>
        <p>Лимит: 2GB | Протокол: HTTPS</p>
        
        <form action="/upload" method="post" enctype="multipart/form-data">
            <div class="form-group">
                <label for="file">Выберите файл:</label><br>
                <input type="file" name="file" id="file" required>
            </div>
            <button type="submit">Загрузить</button>
        </form>
        
        <div id="result"></div>
        
        <script>
        document.querySelector('form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const resultDiv = document.getElementById('result');
            const submitBtn = document.querySelector('button');
            
            submitBtn.disabled = true;
            submitBtn.textContent = 'Загрузка...';
            resultDiv.innerHTML = '<p>Загрузка файла...</p>';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                console.log('Response status:', response.status);
                return response.text();
            })
            .then(text => {
                try {
                    const data = JSON.parse(text);
                    resultDiv.innerHTML = '<pre class="success">' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (e) {
                    console.error('Response text:', text);
                    resultDiv.innerHTML = '<p class="error">Ошибка парсинга: ' + text.substring(0, 200) + '</p>';
                }
            })
            .catch(error => {
                console.error('Error:', error);
                resultDiv.innerHTML = '<p class="error">Ошибка: ' + error.message + '</p>';
            })
            .finally(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = 'Загрузить';
            });
        });
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    try:
        print(f"🔍 DEBUG: Метод: {request.method}")
        print(f"🔍 DEBUG: Content-Type: {request.content_type}")
        print(f"🔍 DEBUG: Файлы: {list(request.files.keys())}")
        print(f"🔍 DEBUG: HTTPS: {request.is_secure}")
        print(f"🔍 DEBUG: Размер запроса: {request.content_length}")
        
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'})
        
        file = request.files['file']
        print(f"🔍 DEBUG: Файл: {file.filename}, размер: {file.content_length}")
        
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'})
        
        # Сохраняем файл
        filename = f"https_upload_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'message': 'Файл загружен успешно через HTTPS',
            'filename': filename,
            'size': file.content_length,
            'is_secure': request.is_secure
        })
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return jsonify({'error': str(e)})

# Обработчики ошибок
@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'Файл слишком большой. Максимальный размер: 2GB'}), 413

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    print("🔒 Запуск HTTPS сервера...")
    print("📝 URL: https://192.168.255.137:5003")
    print("⚠️  Браузер может показать предупреждение о самоподписанном сертификате")
    print("   Это нормально для разработки. Нажмите 'Дополнительно' -> 'Перейти на сайт'")
    print("📏 Лимит файлов: 2GB")
    
    # Запуск с HTTPS
    app.run(host='0.0.0.0', port=5003, debug=True, ssl_context='adhoc') 