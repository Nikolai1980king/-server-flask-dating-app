    return render_template_string(r'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
            <meta name="format-detection" content="telephone=no">
            <meta name="msapplication-tap-highlight" content="no">
            <title>Редактировать анкету</title>
            <script src="https://api-maps.yandex.ru/2.1/?apikey=9a3beffb-a8a0-4d55-850f-d258dd28c104&lang=ru_RU" type="text/javascript"></script>
            <style>
                body { 
                    font-family: Arial, sans-serif; 
                    max-width: 600px; 
                    margin: 0 auto; 
                    padding: 20px; 
                    background: linear-gradient(135deg, #0c0c0c 0%, #1a1a2e 25%, #16213e 50%, #0f3460 75%, #533483 100%);
                    background-size: 400% 400%;
                    animation: starryNight 15s ease infinite;
                    position: relative;
                    min-height: 100vh;
                }

                @keyframes starryNight {
                    0% { background-position: 0% 50%; }
                    50% { background-position: 100% 50%; }
                    100% { background-position: 0% 50%; }
                }

                body::before {
                    content: '';
                    position: fixed;
                    top: 0;
                    left: 0;
                    width: 100%;
                    height: 100%;
                    background-image: 
                        radial-gradient(2px 2px at 20px 30px, #eee, transparent),
                        radial-gradient(2px 2px at 40px 70px, rgba(255,255,255,0.8), transparent),
                        radial-gradient(1px 1px at 90px 40px, #fff, transparent),
                        radial-gradient(1px 1px at 130px 80px, rgba(255,255,255,0.6), transparent),
                        radial-gradient(2px 2px at 160px 30px, #ddd, transparent);
                    background-repeat: repeat;
                    background-size: 200px 100px;
                    animation: twinkle 4s ease-in-out infinite alternate;
                    pointer-events: none;
                    z-index: 1;
                }

                @keyframes twinkle {
                    0% { opacity: 0.3; }
                    100% { opacity: 1; }
                }

                .form-container {
                    position: relative;
                    z-index: 2;
                    background: rgba(255, 255, 255, 0.1);
                    backdrop-filter: blur(10px);
                    border-radius: 20px;
                    padding: 30px;
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                }

                h2 {
                    color: #fff;
                    text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
                    margin-bottom: 25px;
                    font-size: 1.8em;
                }

                input, textarea, select { 
                    width: 100%; 
                    padding: 12px; 
                    margin: 0; 
                    background: rgba(76, 175, 80, 0.1);
                    border: 1px solid rgba(76, 175, 80, 0.3);
                    border-radius: 10px;
                    color: #fff;
                    font-size: 1em;
                    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
                    box-sizing: border-box;
                }

                input::placeholder, textarea::placeholder, select::placeholder {
                    color: rgba(255, 255, 255, 0.7);
                    text-shadow: 0 0 3px rgba(255, 255, 255, 0.2);
                }

                input:focus, textarea:focus, select:focus {
                    outline: none;
                    border-color: #4CAF50;
                    box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);
                    background: rgba(76, 175, 80, 0.15);
                }

                select option {
                    background: rgba(76, 175, 80, 0.9);
                    color: #fff;
                    border: none;
                }

                select option:hover {
                    background: rgba(76, 175, 80, 1);
                }

                .field-container {
                    position: relative;
                    width: 100%;
                    margin-bottom: 10px;
                }

                input[type="file"] {
                    background: rgba(76, 175, 80, 0.1);
                    border: 1px solid rgba(76, 175, 80, 0.3);
                    color: #fff;
                    padding: 12px;
                    border-radius: 10px;
                    cursor: pointer;
                }

                input[type="file"]:focus {
                    outline: none;
                    border-color: #4CAF50;
                    box-shadow: 0 0 15px rgba(76, 175, 80, 0.3);
                    background: rgba(76, 175, 80, 0.15);
                }

                input[type="file"]::-webkit-file-upload-button {
                    background: rgba(76, 175, 80, 0.3);
                    color: #fff;
                    border: 1px solid rgba(76, 175, 80, 0.5);
                    border-radius: 5px;
                    padding: 8px 12px;
                    cursor: pointer;
                    margin-right: 10px;
                }

                input[type="file"]::-webkit-file-upload-button:hover {
                    background: rgba(76, 175, 80, 0.5);
                }

                label {
                    color: #fff;
                    font-weight: bold;
                    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
                }

                .modern-btn {
                    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    border: none;
                    padding: 15px 30px;
                    border-radius: 25px;
                    box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    font-weight: bold;
                }
                .modern-btn:hover {
                    box-shadow: 0 8px 30px rgba(102, 126, 234, 0.6);
                    transform: translateY(-3px) scale(1.05);
                }
                .back-btn {
                    background: linear-gradient(90deg, #6c757d 0%, #495057 100%);
                    color: white;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 25px;
                    box-shadow: 0 4px 14px rgba(108,117,125,0.2);
                    font-size: 1.1em;
                    cursor: pointer;
                    transition: box-shadow 0.2s, transform 0.2s;
                    text-decoration: none;
                    display: inline-block;
                    margin-top: 20px;
                }
                .back-btn:hover {
                    box-shadow: 0 8px 24px rgba(108,117,125,0.3);
                    transform: translateY(-2px) scale(1.03);
                }

                .map-container {
                    margin: 20px 0;
                    border-radius: 15px;
                    overflow: hidden;
                    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
                }

                #map {
                    width: 100%;
                    height: 300px;
                    border-radius: 15px;
                }

                .location-info {
                    background: rgba(76, 175, 80, 0.1);
                    border: 1px solid rgba(76, 175, 80, 0.3);
                    padding: 15px;
                    border-radius: 10px;
                    margin: 10px 0;
                    color: #fff;
                    text-shadow: 0 0 5px rgba(255, 255, 255, 0.3);
                }

                .location-btn {
                    background: linear-gradient(90deg, #4CAF50 0%, #81c784 100%);
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 20px;
                    font-size: 1em;
                    cursor: pointer;
                    margin: 5px;
                    transition: all 0.3s ease;
                }
                .location-btn:hover {
                    box-shadow: 0 4px 16px rgba(76,175,80,0.3);
                    transform: translateY(-2px);
                }

                .location-return-btn {
                    position: absolute;
                    top: 10px;
                    right: 10px;
                    background: linear-gradient(90deg, #2196F3 0%, #64B5F6 100%);
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 20px;
                    font-size: 0.9em;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 10px rgba(33, 150, 243, 0.3);
                    z-index: 1000;
                    font-weight: bold;
                }

                .location-return-btn:hover {
                    box-shadow: 0 4px 16px rgba(33, 150, 243, 0.5);
                    transform: translateY(-2px) scale(1.05);
                    background: linear-gradient(90deg, #1976D2 0%, #42A5F5 100%);
                }

                .map-container {
                    position: relative;
                }
            </style>
        </head>
        <body>
            {{ navbar|safe }}
            <div class="form-container">
                <h2 style="text-align: center; margin-top: 10px;">Редактировать анкету</h2>
                <p style="color: #fff; opacity: 0.8; margin-bottom: 20px; text-align: center;">
                    📍 Ваше местоположение будет определено автоматически
                </p>
                <form method="post" enctype="multipart/form-data">
                <div class="field-container">
                    <input type="text" name="name" placeholder="Ваше имя" value="{{ profile.name }}" required maxlength="12" oninput="checkFieldLength(this, 12)">
                </div>
                <div class="field-container">
                    <input type="number" name="age" placeholder="Ваш возраст" value="{{ profile.age }}" required>
                </div>
                <div class="field-container">
                    <select name="gender" required>
                        <option value="">Выберите пол</option>
                        <option value="male" {% if profile.gender == 'male' %}selected{% endif %}>Мужской</option>
                        <option value="female" {% if profile.gender == 'female' %}selected{% endif %}>Женский</option>
                        <option value="other" {% if profile.gender == 'other' %}selected{% endif %}>Другое</option>
                    </select>
                </div>
                <div class="field-container">
                    <textarea name="hobbies" placeholder="Ваши увлечения" required maxlength="70" oninput="checkFieldLength(this, 70)">{{ profile.hobbies }}</textarea>
                </div>
                <div class="field-container">
                    <textarea name="goal" placeholder="Цель знакомства" required maxlength="70" oninput="checkFieldLength(this, 70)">{{ profile.goal }}</textarea>
                </div>

                    <div class="map-container">
                        <div id="map"></div>
                        <button type="button" id="return-to-location-btn" class="location-return-btn" onclick="returnToMyLocation()" style="display: none;">
                            📍 Я тут
                        </button>
                    </div>

                <div class="field-container">
                    <input type="text" name="venue" id="venue-input" placeholder="Название заведения (кафе, ресторан и т.д.)" value="{{ profile.venue or '' }}" required onchange="updateVenueCoordinates()">
                </div>
                <input type="hidden" name="latitude" id="latitude-input" value="{{ profile.latitude or '' }}">
                <input type="hidden" name="longitude" id="longitude-input" value="{{ profile.longitude or '' }}">
                <input type="hidden" name="venue_lat" id="venue-lat-input">
                <input type="hidden" name="venue_lng" id="venue-lng-input">

                <!-- Скрытые поля для координат и расстояния (используются для расчетов) -->
                <input type="hidden" id="visitor-coordinates-display">
                <input type="hidden" id="venue-coordinates-display">
                <input type="hidden" id="distance-display">

                <div class="field-container">
                    <input type="file" name="photo" accept="image/*">
                </div>

                <div style="text-align: center; margin-top: 20px;">
                    <button type="submit" class="modern-btn">Сохранить</button>
                </div>
            </form>
            <div style="text-align: center; margin-top: 15px;">
                <a href="/my_profile" class="back-btn">← Назад</a>
            </div>
            </div>

            <script>
                // Функция для проверки длины полей (функциональность ограничений сохранена)
                function checkFieldLength(field, maxLength) {
                    // Функциональность ограничений остается, но без визуальных счетчиков
                    // Пользователь не сможет ввести больше символов благодаря maxlength
                }

                // Статическое местоположение: карта автоматически определяет местоположение пользователя
                // и делает его неизменяемым. Пользователь может только выбирать заведения.
                let myMap, myPlacemark;
                let currentLocation = null;

                function initMap() {
                    ymaps.ready(function () {
                        myMap = new ymaps.Map('map', {
                            center: [55.76, 37.64], // Москва по умолчанию
                            zoom: 10,
                            controls: ['zoomControl', 'fullscreenControl']
                        });

                        // Автоматически определяем местоположение при загрузке страницы
                        getCurrentLocation();

                        // Убираем возможность клика по карте для изменения местоположения
                        // myMap.events.add('click', function (e) {
                        //     var coords = e.get('coords');
                        //     setLocation(coords[0], coords[1]);
                        // });

                        // Добавляем обработчик для открытия балунов
                        myMap.events.add('balloonopen', function (e) {
                            console.log('🎈 Балун открыт, начинаем парсинг...');
                            // Добавляем небольшую задержку для полной загрузки балуна
                            setTimeout(function() {
                                parseBalloonAndFillVenue();
                            }, 500);
                        });
                    });
                }

                function setLocation(lat, lng) {
                    currentLocation = {lat: lat, lng: lng};

                    // Обновляем скрытые поля формы
                    document.getElementById('latitude-input').value = lat;
                    document.getElementById('longitude-input').value = lng;

                    // Обновляем поле отображения координат посетителя
                    const visitorCoordsDisplay = document.getElementById('visitor-coordinates-display');
                    if (visitorCoordsDisplay) {
                        visitorCoordsDisplay.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                    }

                    // Удаляем предыдущую метку
                    if (myPlacemark) {
                        myMap.geoObjects.remove(myPlacemark);
                    }

                    // Добавляем новую метку
                    myPlacemark = new ymaps.Placemark([lat, lng], {
                        balloonContent: 'Выбранное местоположение посетителя'
                    }, {
                        preset: 'islands#redDotIcon'
                    });

                    myMap.geoObjects.add(myPlacemark);
                    myMap.setCenter([lat, lng], 15);

                    // Показываем кнопку "Я тут" после определения местоположения
                    const returnBtn = document.getElementById('return-to-location-btn');
                    if (returnBtn) {
                        returnBtn.style.display = 'block';
                    }

                    // Определяем город/поселок (без отображения в интерфейсе)
                    getLocationName(lat, lng);

                    // Рассчитываем расстояние и обновляем поле заведения, если оно есть
                    const venueInput = document.getElementById('venue-input');
                    if (venueInput && venueInput.value.trim()) {
                        // Извлекаем оригинальное название заведения (без расстояния)
                        const venueValue = venueInput.value.trim();
                        const venueName = venueValue.replace(/\s*\(\d+\.?\d*\s*(м|км)\)$/, ''); // Убираем расстояние в скобках
                        calculateDistanceAndUpdateVenueField(venueName);
                    } else {
                        // Если заведения нет, просто рассчитываем расстояние для отображения
                        calculateDistance();
                    }

                    console.log('✅ Координаты посетителя установлены:', lat, lng);
                }

                function getCurrentLocation() {
                    if (navigator.geolocation) {
                        navigator.geolocation.getCurrentPosition(
                            function(position) {
                                var lat = position.coords.latitude;
                                var lng = position.coords.longitude;
                                setLocation(lat, lng);
                            },
                            function(error) {
                                console.error('Ошибка геолокации:', error);
                            },
                            {
                                enableHighAccuracy: false,
                                timeout: 10000,
                                maximumAge: 300000
                            }
                        );
                    } else {
                        console.log('Геолокация не поддерживается вашим браузером');
                    }
                }

                // Функция возврата к своему местоположению
                function returnToMyLocation() {
                    if (currentLocation) {
                        // Возвращаем карту к местоположению пользователя
                        myMap.setCenter([currentLocation.lat, currentLocation.lng], 15);
                        console.log(' Возвращаемся к вашему местоположению:', currentLocation.lat, currentLocation.lng);
                    } else {
                        // Если местоположение не определено, определяем заново
                        console.log('📍 Местоположение не определено, определяем заново...');
                        getCurrentLocation();
                    }
                }

                // Функция clearLocation удалена, так как местоположение теперь статическое
                // function clearLocation() {
                //     // Код удален
                // }

                // Функция очистки координат заведения
                function clearVenueCoordinates() {
                    const venueCoordsDisplay = document.getElementById('venue-coordinates-display');
                    if (venueCoordsDisplay) {
                        venueCoordsDisplay.value = '';
                    }

                    // Очищаем расстояние из поля заведения
                    const venueInput = document.getElementById('venue-input');
                    if (venueInput && venueInput.value.trim()) {
                        const venueValue = venueInput.value.trim();
                        const venueName = venueValue.replace(/\s*\(\d+\.?\d*\s*(м|км)\)$/, ''); // Убираем расстояние в скобках
                        venueInput.value = venueName;
                    }

                    console.log('✅ Координаты заведения очищены');

                    // Очищаем расстояние
                    clearDistance();
                }

                // Функция очистки расстояния
                function clearDistance() {
                    const distanceDisplay = document.getElementById('distance-display');
                    if (distanceDisplay) {
                        distanceDisplay.value = '';
                    }
                }

                // Функция отображения координат заведения
                function showVenueCoordinates(venueName, lat, lng) {
                    // Удаляем предыдущий блок с координатами, если он есть
                    const existingCoordsDiv = document.getElementById('venue-coordinates');
                    if (existingCoordsDiv) {
                        existingCoordsDiv.remove();
                    }

                    // Обновляем поле отображения координат заведения
                    const venueCoordsDisplay = document.getElementById('venue-coordinates-display');
                    if (venueCoordsDisplay) {
                        venueCoordsDisplay.value = `${lat.toFixed(6)}, ${lng.toFixed(6)}`;
                    }

                    // Заполняем скрытые поля для отправки на сервер
                    const venueLatInput = document.getElementById('venue-lat-input');
                    const venueLngInput = document.getElementById('venue-lng-input');
                    if (venueLatInput && venueLngInput) {
                        venueLatInput.value = lat.toFixed(6);
                        venueLngInput.value = lng.toFixed(6);
                    }

                    // Рассчитываем расстояние и обновляем поле заведения
                    calculateDistanceAndUpdateVenueField(venueName);

                    console.log('✅ Координаты заведения отображены:', lat, lng);
                }

                // Функция расчета расстояния и обновления поля заведения
                function calculateDistanceAndUpdateVenueField(venueName) {
                    const visitorCoordsDisplay = document.getElementById('visitor-coordinates-display');
                    const venueCoordsDisplay = document.getElementById('venue-coordinates-display');
                    const venueInput = document.getElementById('venue-input');
                    const distanceDisplay = document.getElementById('distance-display');

                    if (!visitorCoordsDisplay || !venueCoordsDisplay || !venueInput) {
                        return;
                    }

                    const visitorCoords = visitorCoordsDisplay.value.trim();
                    const venueCoords = venueCoordsDisplay.value.trim();

                    if (!visitorCoords || !venueCoords) {
                        // Если нет координат посетителя, просто обновляем поле заведения без расстояния
                        venueInput.value = venueName;
                        if (distanceDisplay) {
                            distanceDisplay.value = '';
                        }
                        return;
                    }

                    try {
                        // Парсим координаты
                        const [visitorLat, visitorLng] = visitorCoords.split(',').map(coord => parseFloat(coord.trim()));
                        const [venueLat, venueLng] = venueCoords.split(',').map(coord => parseFloat(coord.trim()));

                        if (isNaN(visitorLat) || isNaN(visitorLng) || isNaN(venueLat) || isNaN(venueLng)) {
                            venueInput.value = venueName;
                            if (distanceDisplay) {
                                distanceDisplay.value = 'Ошибка в координатах';
                            }
                            return;
                        }

                        // Отправляем запрос на сервер для расчета расстояния
                        fetch('/api/calculate-distance', {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json',
                            },
                            body: JSON.stringify({
                                visitor_lat: visitorLat,
                                visitor_lng: visitorLng,
                                venue_lat: venueLat,
                                venue_lng: venueLng
                            })
                        })
                        .then(response => response.json())
                        .then(data => {
                            if (data.success) {
                                const distance = data.distance;
                                let distanceText;

                                if (distance < 1000) {
                                    distanceText = `${Math.round(distance)} м`;
                                } else {
                                    distanceText = `${(distance / 1000).toFixed(1)} км`;
                                }

                                // Обновляем поле заведения с расстоянием в скобках
                                venueInput.value = `${venueName} (${distanceText})`;

                                // Также обновляем поле расстояния
                                if (distanceDisplay) {
                                    if (distance < 1000) {
                                        distanceDisplay.value = `${Math.round(distance)} метров`;
                                    } else {
                                        distanceDisplay.value = `${(distance / 1000).toFixed(2)} км`;
                                    }
                                }

                                console.log('✅ Расстояние рассчитано и добавлено к названию заведения:', distance, 'метров');
                            } else {
                                venueInput.value = venueName;
                                if (distanceDisplay) {
                                    distanceDisplay.value = 'Ошибка расчета';
                                }
                                console.error('❌ Ошибка расчета расстояния:', data.error);
                            }
                        })
                        .catch(error => {
                            venueInput.value = venueName;
                            if (distanceDisplay) {
                                distanceDisplay.value = 'Ошибка сети';
                            }
                            console.error('❌ Ошибка сети при расчете расстояния:', error);
                        });

                    } catch (error) {
                        venueInput.value = venueName;
                        if (distanceDisplay) {
                            distanceDisplay.value = 'Ошибка в координатах';
                        }
                        console.error('❌ Ошибка парсинга координат:', error);
                    }
                }

                function getLocationName(lat, lng) {
                    // Отправляем запрос на сервер для получения названия города/поселка (без отображения в интерфейсе)
                    fetch('/api/get-location-name', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            latitude: lat,
                            longitude: lng
                        })
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            console.log('📍 Определен город/поселок:', data.location_name);
                        } else {
                            console.log('❌ Не удалось определить город/поселок');
                        }
                    })
                    .catch(error => {
                        console.error('Ошибка при получении названия города/поселка:', error);
                    });
                }

                // Функция парсинга балуна
                function extractNameFromBalloon() {
                    try {
                        console.log('🔍 Начинаем парсинг балуна...');

                        // Ищем балун по всем возможным селекторам
                        let balloonContent = document.querySelector('.ymaps-2-1-79-balloon');
                        if (!balloonContent) {
                            balloonContent = document.querySelector('.ymaps-balloon');
                        }
                        if (!balloonContent) {
                            balloonContent = document.querySelector('.balloon');
                        }
                        if (!balloonContent) {
                            balloonContent = document.querySelector('[class*="balloon"]');
                        }
                        if (!balloonContent) {
                            balloonContent = document.querySelector('[class*="ymaps"]');
                        }

                        if (!balloonContent) {
                            console.log('❌ Балун не найден');
                            return null;
                        }

                        console.log('✅ Балун найден:', balloonContent.className);

                        // Получаем HTML контент
                        const htmlContent = balloonContent.innerHTML;
                        console.log('📏 Размер HTML:', htmlContent.length, 'символов');

                        // Ищем все ссылки в балуне
                        const links = balloonContent.querySelectorAll('a');
                        console.log('🔗 Найдено ссылок:', links.length);

                        const foundLinks = [];
                        let firstValidName = null;

                        if (links.length > 0) {
                            for (let i = 0; i < links.length; i++) {
                                const link = links[i];
                                const linkText = link.textContent.trim();
                                console.log(`🔗 Ссылка ${i + 1}: "${linkText}"`);
                                foundLinks.push(linkText);

                                // Проверяем, что это не служебная ссылка
                                if (isValidVenueName(linkText)) {
                                    // Сохраняем первое валидное название
                                    if (!firstValidName) {
                                        firstValidName = linkText;
                                        console.log(`✅ Найдено первое название в ссылке: "${linkText}"`);
                                    }
                                }
                            }
                        }

                        // Ищем заголовки
                        const headers = balloonContent.querySelectorAll('h1, h2, h3, h4, h5, h6');
                        console.log(' Найдено заголовков:', headers.length);

                        for (let header of headers) {
                            const headerText = header.textContent.trim();
                            console.log(`📋 Заголовок: "${headerText}"`);
                            foundLinks.push(headerText);

                            if (isValidVenueName(headerText)) {
                                // Сохраняем первое валидное название
                                if (!firstValidName) {
                                    firstValidName = headerText;
                                    console.log(`✅ Найдено первое название в заголовке: "${headerText}"`);
                                }
                            }
                        }

                        // Ищем элементы с классами name/title
                        const nameElements = balloonContent.querySelectorAll('[class*="name"], [class*="title"]');
                        console.log('️ Найдено элементов с name/title:', nameElements.length);

                        for (let element of nameElements) {
                            const elementText = element.textContent.trim();
                            console.log(`🏷️ Элемент с name/title: "${elementText}"`);
                            foundLinks.push(elementText);

                            if (isValidVenueName(elementText)) {
                                // Сохраняем первое валидное название
                                if (!firstValidName) {
                                    firstValidName = elementText;
                                    console.log(`✅ Найдено первое название в элементе с name/title: "${elementText}"`);
                                }
                            }
                        }

                        // Последняя попытка - ищем первый значимый текстовый элемент
                        const allElements = balloonContent.querySelectorAll('*');
                        console.log('🔍 Всего элементов в балуне:', allElements.length);

                        for (let element of allElements) {
                            const text = element.textContent.trim();
                            if (isValidVenueName(text)) {
                                // Сохраняем первое валидное название
                                if (!firstValidName) {
                                    firstValidName = text;
                                    console.log(`✅ Найдено первое название в текстовом элементе: "${text}"`);
                                }
                            }
                        }

                        if (firstValidName) {
                            console.log(`✅ Возвращаем первое найденное название: "${firstValidName}"`);
                            return { name: firstValidName, links: foundLinks };
                        } else {
                            console.log('❌ Название не найдено');
                            return { name: null, links: foundLinks };
                        }

                    } catch (error) {
                        console.log('❌ Ошибка при парсинге:', error);
                        return { name: null, links: [] };
                    }
                }

                // Функция валидации названия заведения
                function isValidVenueName(name) {
                    return name && name.length > 2 && name.length < 100 &&
                        !name.includes('Share') && !name.includes('Поделиться') &&
                        !name.includes('Телефон') && !name.includes('Адрес') &&
                        !name.includes('Часы') && !name.includes('Рейтинг') &&
                        !name.includes('Открыто') && !name.includes('Закрыто') &&
                        !name.includes('www.') && !name.includes('http') &&
                        !name.includes('+7') && !name.includes('8-') &&
                        !name.match(/^\d+$/) && !name.match(/^\d+\.\d+$/) &&
                        !name.includes('отзыв') && !name.includes('отзывов') &&
                        !name.includes('Показать') && !name.includes('Написать') &&
                        !name.includes('Позвонить') && !name.includes('Поделиться') &&
                        // Исключаем названия, которые начинаются с цифры и пробела (например "1. Название")
                        !name.match(/^\d+\.\s/) && !name.match(/^\d+\s/) &&
                        // Исключаем названия, которые содержат только цифры и точки
                        !name.match(/^[\d\.\s]+$/);
                }

                // Функция парсинга балуна и заполнения поля заведения
                function parseBalloonAndFillVenue() {
                    console.log('=== ПАРСИНГ БАЛУНА ===');

                    const result = extractNameFromBalloon();

                    if (result.name) {
                        document.getElementById('venue-input').value = result.name;
                        console.log('✅ Название заведения заполнено:', result.name);

                        // Получаем координаты заведения из балуна или API
                        let venueLat = null;
                        let venueLng = null;

                        // Попытка получить координаты из балуна
                        if (result.coordinates) {
                            venueLat = result.coordinates.lat;
                            venueLng = result.coordinates.lng;
                        } else {
                            // Если координаты не найдены в балуне, используем координаты центра карты
                            const mapCenter = myMap.getCenter();
                            venueLat = mapCenter[0];
                            venueLng = mapCenter[1];
                        }

                        // Показываем координаты заведения
                        if (venueLat && venueLng) {
                            showVenueCoordinates(result.name, venueLat, venueLng);
                        }
                    } else {
                        console.log('❌ Название заведения не найдено');
                    }

                    if (result.links && result.links.length > 0) {
                        console.log('🔗 Найдено ссылок:', result.links.length);
                    } else {
                        console.log('❌ Ссылки не найдены');
                    }

                    console.log('=====================');
                }

                // Функция обновления координат при изменении названия заведения
                function updateVenueCoordinates() {
                    const venueInput = document.getElementById('venue-input');
                    let venueName = venueInput.value.trim();

                    // Убираем расстояние в скобках из названия заведения для обработки
                    venueName = venueName.replace(/\s*\(\d+\.?\d*\s*(м|км)\)$/, '');

                    if (venueName) {
                        // Если есть название заведения, очищаем координаты заведения
                        clearVenueCoordinates();
                    } else {
                        // Если название заведения пустое, очищаем координаты заведения
                        clearVenueCoordinates();
                    }
                }

                // Инициализация карты при загрузке страницы
                window.onload = function() {
                    console.log(' Страница загружена, начинаем инициализацию...');

                    // Проверяем, есть ли элемент карты
                    const mapElement = document.getElementById('map');
                    if (mapElement) {
                        console.log('✅ Элемент карты найден');
                    } else {
                        console.error('❌ Элемент карты не найден!');
                    }

                    // На странице редактирования профиля карта должна инициализироваться всегда
                    console.log('🗺️ Инициализируем карту на странице редактирования профиля...');
                    initMap();

                    // Если у профиля есть координаты, устанавливаем их как текущее местоположение
                    {% if profile.latitude and profile.longitude %}
                    currentLocation = {
                        lat: {{ profile.latitude }},
                        lng: {{ profile.longitude }}
                    };

                    // Если есть название заведения, показываем координаты
                    {% if profile.venue %}
                    setTimeout(function() {
                        showVenueCoordinates('{{ profile.venue }}', {{ profile.latitude }}, {{ profile.longitude }});
                    }, 1000);
                    {% endif %}
                    {% endif %}
                };
            </script>
        </body>
        </html>
    ''', profile=profile, navbar=navbar, get_photo_url=get_photo_url, get_starry_night_css=get_starry_night_css)
