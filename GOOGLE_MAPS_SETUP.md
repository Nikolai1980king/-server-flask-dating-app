# Настройка Google Maps API

## Текущая версия

Сейчас приложение работает с упрощенной версией геолокации без Google Maps API. Это позволяет:
- ✅ Определять местоположение пользователя
- ✅ Сохранять координаты в базе данных
- ❌ Показывать карту
- ❌ Искать кафе на карте

## Для полной функциональности с картами

### 1. Получение API ключа

1. Перейдите на [Google Cloud Console](https://console.cloud.google.com/)
2. Создайте новый проект или выберите существующий
3. Включите следующие API:
   - **Maps JavaScript API**
   - **Places API**
   - **Geocoding API**
4. Создайте API ключ в разделе "Credentials"
5. Ограничьте ключ только необходимыми API для безопасности

### 2. Настройка в приложении

#### Вариант 1: Через переменную окружения (рекомендуется)

```bash
export GOOGLE_MAPS_API_KEY="ваш_ключ_здесь"
python app.py
```

#### Вариант 2: Прямое редактирование

Откройте файл `config.py` и замените строку:

```python
GOOGLE_MAPS_API_KEY = os.environ.get('GOOGLE_MAPS_API_KEY', 'YOUR_GOOGLE_MAPS_API_KEY')
```

на:

```python
GOOGLE_MAPS_API_KEY = 'ваш_ключ_здесь'
```

### 3. Восстановление полной версии шаблона

После получения API ключа, замените содержимое файла `templates/geolocation.html` на полную версию с картами:

```html
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{ title }}</title>
    <style>
        /* ... стили ... */
    </style>
    <script src="https://maps.googleapis.com/maps/api/js?key={{ config.GOOGLE_MAPS_API_KEY }}&libraries=places"></script>
    <script>
        let map, marker, infoWindow;
        let userLocation = null;
        
        function initMap() {
            // Инициализация карты с центром по умолчанию или сохраненными координатами
            const defaultCenter = {% if profile and profile.latitude and profile.longitude %}
                { lat: {{ profile.latitude }}, lng: {{ profile.longitude }} }
            {% else %}
                { lat: 55.7558, lng: 37.6176 }
            {% endif %};
            
            map = new google.maps.Map(document.getElementById('map'), {
                center: defaultCenter,
                zoom: 13,
                styles: [
                    {
                        "featureType": "poi",
                        "elementType": "labels",
                        "stylers": [{ "visibility": "on" }]
                    }
                ]
            });
            
            // Если есть сохраненные координаты, показываем маркер
            {% if profile and profile.latitude and profile.longitude %}
            placeMarker(defaultCenter);
            searchNearbyCafes(defaultCenter);
            {% endif %}
            
            // Добавляем поиск кафе
            const service = new google.maps.places.PlacesService(map);
            
            // Обработчик клика по карте
            map.addListener('click', function(event) {
                placeMarker(event.latLng);
                searchNearbyCafes(event.latLng);
            });
            
            // Попытка получить местоположение пользователя
            getCurrentLocation();
        }
        
        function getCurrentLocation() {
            const statusDiv = document.getElementById('location-status');
            const locationBtn = document.getElementById('get-location-btn');
            
            if (navigator.geolocation) {
                statusDiv.textContent = 'Определяем ваше местоположение...';
                locationBtn.style.display = 'none';
                
                navigator.geolocation.getCurrentPosition(
                    function(position) {
                        const pos = {
                            lat: position.coords.latitude,
                            lng: position.coords.longitude
                        };
                        
                        userLocation = pos;
                        map.setCenter(pos);
                        placeMarker(pos);
                        searchNearbyCafes(pos);
                        
                        statusDiv.textContent = 'Местоположение определено!';
                        locationBtn.style.display = 'inline-block';
                        locationBtn.textContent = '📍 Обновить местоположение';
                    },
                    function() {
                        statusDiv.textContent = 'Не удалось определить местоположение';
                        locationBtn.style.display = 'inline-block';
                        locationBtn.textContent = '📍 Попробовать снова';
                    }
                );
            } else {
                statusDiv.textContent = 'Геолокация не поддерживается';
                locationBtn.style.display = 'inline-block';
            }
            
            locationBtn.onclick = getCurrentLocation;
        }
        
        function placeMarker(location) {
            if (marker) {
                marker.setMap(null);
            }
            
            marker = new google.maps.Marker({
                position: location,
                map: map,
                draggable: true,
                title: 'Выбранное место'
            });
            
            // Обновляем скрытые поля
            document.getElementById('latitude-input').value = location.lat();
            document.getElementById('longitude-input').value = location.lng();
            
            // Обработчик перетаскивания маркера
            marker.addListener('dragend', function() {
                const newPos = marker.getPosition();
                searchNearbyCafes(newPos);
                document.getElementById('latitude-input').value = newPos.lat();
                document.getElementById('longitude-input').value = newPos.lng();
            });
        }
        
        function searchNearbyCafes(location) {
            const service = new google.maps.places.PlacesService(map);
            
            const request = {
                location: location,
                radius: '500',
                type: ['cafe', 'restaurant', 'food']
            };
            
            service.nearbySearch(request, function(results, status) {
                if (status === google.maps.places.PlacesServiceStatus.OK) {
                    // Очищаем предыдущие маркеры кафе
                    clearCafeMarkers();
                    
                    // Добавляем маркеры кафе
                    results.forEach(function(place) {
                        const cafeMarker = new google.maps.Marker({
                            position: place.geometry.location,
                            map: map,
                            icon: {
                                url: 'https://maps.google.com/mapfiles/ms/icons/red-dot.png',
                                scaledSize: new google.maps.Size(30, 30)
                            },
                            title: place.name
                        });
                        
                        const infowindow = new google.maps.InfoWindow({
                            content: '<div><strong>' + place.name + '</strong><br>' + 
                                    (place.vicinity || place.formatted_address) + 
                                    '<br><button onclick="selectCafe(\'' + place.name + '\', \'' + 
                                    place.geometry.location.lat() + '\', \'' + 
                                    place.geometry.location.lng() + '\')" style="margin-top: 5px; padding: 5px 10px; background: #4CAF50; color: white; border: none; border-radius: 3px; cursor: pointer;">Выбрать это кафе</button></div>'
                        });
                        
                        cafeMarker.addListener('click', function() {
                            infowindow.open(map, cafeMarker);
                        });
                        
                        // Сохраняем маркер для последующего удаления
                        if (!window.cafeMarkers) window.cafeMarkers = [];
                        window.cafeMarkers.push(cafeMarker);
                    });
                }
            });
        }
        
        function clearCafeMarkers() {
            if (window.cafeMarkers) {
                window.cafeMarkers.forEach(function(marker) {
                    marker.setMap(null);
                });
                window.cafeMarkers = [];
            }
        }
        
        function selectCafe(name, lat, lng) {
            document.getElementById('venue-input').value = name;
            document.getElementById('latitude-input').value = lat;
            document.getElementById('longitude-input').value = lng;
            
            // Перемещаем основной маркер к выбранному кафе
            const location = { lat: parseFloat(lat), lng: parseFloat(lng) };
            placeMarker(location);
            map.setCenter(location);
            
            // Закрываем все инфоокна
            if (infoWindow) {
                infoWindow.close();
            }
        }
        
        // Инициализация карты при загрузке страницы
        window.onload = function() {
            initMap();
        };
    </script>
</head>
<body>
    <div class="form-container">
        <h2>{{ title }}</h2>
        <form method="post" enctype="multipart/form-data">
            <!-- ... поля формы ... -->
            <label for="venue">Выберите кафе на карте:</label>
            <div id="map-container" style="width: 100%; height: 300px; margin: 10px 0; border-radius: 10px; overflow: hidden; position: relative;">
                <div id="map" style="width: 100%; height: 100%;"></div>
                <div id="location-info" style="position: absolute; top: 10px; left: 10px; background: rgba(255,255,255,0.9); padding: 10px; border-radius: 5px; font-size: 0.9em; z-index: 1000;">
                    <div id="location-status">Определяем ваше местоположение...</div>
                    <button type="button" id="get-location-btn" class="modern-btn" style="padding: 8px 16px; font-size: 0.9em; margin-top: 5px;">📍 Определить местоположение</button>
                </div>
            </div>
            <input type="text" name="venue" id="venue-input" placeholder="Название заведения" value="{{ profile.venue if profile else '' }}" required readonly>
            <input type="hidden" name="latitude" id="latitude-input" value="{{ profile.latitude if profile else '' }}">
            <input type="hidden" name="longitude" id="longitude-input" value="{{ profile.longitude if profile else '' }}">
            <!-- ... остальные поля ... -->
        </form>
    </div>
</body>
</html>
```

## Безопасность

⚠️ **Важно**: Никогда не публикуйте ваш API ключ в открытых репозиториях. Используйте переменные окружения или файлы конфигурации, которые не попадают в систему контроля версий.

## Стоимость

Google Maps API имеет бесплатный лимит:
- Maps JavaScript API: 28,500 загрузок карт в месяц
- Places API: 1,000 запросов в день
- Geocoding API: 2,500 запросов в день

Для большинства небольших приложений этого достаточно. 