#!/usr/bin/env python3
"""
Максимально простой тест загрузки файлов
"""

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# Настройки
app.config['MAX_CONTENT_LENGTH'] = 2 * 1024 * 1024 * 1024  # 2GB
UPLOAD_FOLDER = 'static/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route('/')
def index():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Простой тест загрузки</title>
    </head>
    <body>
        <h1>Простой тест загрузки файлов</h1>
        <form action="/upload" method="post" enctype="multipart/form-data">
            <input type="file" name="file" required>
            <button type="submit">Загрузить</button>
        </form>
        <div id="result"></div>
        
        <script>
        document.querySelector('form').addEventListener('submit', function(e) {
            e.preventDefault();
            
            const formData = new FormData(this);
            const resultDiv = document.getElementById('result');
            
            resultDiv.innerHTML = '<p>Загрузка...</p>';
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.text())
            .then(text => {
                try {
                    const data = JSON.parse(text);
                    resultDiv.innerHTML = '<pre style="color: green;">' + JSON.stringify(data, null, 2) + '</pre>';
                } catch (e) {
                    resultDiv.innerHTML = '<p style="color: red;">Ошибка парсинга JSON: ' + text.substring(0, 200) + '</p>';
                }
            })
            .catch(error => {
                resultDiv.innerHTML = '<p style="color: red;">Ошибка: ' + error.message + '</p>';
            });
        });
        </script>
    </body>
    </html>
    '''

@app.route('/upload', methods=['POST'])
def upload():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'Файл не найден'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'Файл не выбран'})
        
        # Сохраняем файл
        filename = f"upload_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        return jsonify({
            'success': True,
            'filename': filename,
            'size': file.content_length
        })
        
    except Exception as e:
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    print("🚀 Простой тест загрузки файлов")
    print("📝 URL: http://192.168.255.137:5002")
    print("📏 Лимит: 2GB")
    
    app.run(host='0.0.0.0', port=5002, debug=True) 