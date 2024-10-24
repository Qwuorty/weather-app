from flask import Flask, render_template, request
import requests
from config import API_KEY

app = Flask(__name__)

''' функция для получения ключа локации по названию города '''
def get_location_key(city_name):
    location_url = f"http://dataservice.accuweather.com/locations/v1/cities/search"
    params = {
        'apikey': API_KEY,
        'q': city_name,
        'language': 'ru'
    }
    response = requests.get(location_url, params=params)
    data = response.json()
    if data:
        return data[0]['Key']
    else:
        return None

''' функция для получения погодных данных по ключу локации '''
def get_weather_data(location_key):
    weather_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
    params = {
        'apikey': API_KEY,
        'language': 'ru',
        'details': 'true'
    }
    response = requests.get(weather_url, params=params)
    data = response.json()
    if data:
        return data[0]
    else:
        return None

''' функция для оценки неблагоприятных погодных условий '''
def check_bad_weather(temperature, wind_speed, precipitation_probability):
    if temperature < 0 or temperature > 35:
        return "Неблагоприятные погодные условия: экстремальная температура."
    if wind_speed > 50:
        return "Неблагоприятные погодные условия: сильный ветер."
    if precipitation_probability > 70:
        return "Неблагоприятные погодные условия: высокая вероятность осадков."
    return "Погодные условия благоприятные."

''' основной маршрут приложения '''
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    start_city = None
    end_city = None
    if request.method == 'POST':
        start_city = request.form.get('start_city')
        end_city = request.form.get('end_city')
        if not start_city or not end_city:
            result = "Пожалуйста, введите названия обоих городов."
        else:
            try:
                # получаем ключ локации для начального города
                start_location_key = get_location_key(start_city)
                if not start_location_key:
                    result = f"Не удалось найти город: {start_city}"
                    return render_template('index.html', result=result)
                # получаем погодные данные для начального города
                start_weather = get_weather_data(start_location_key)
                if not start_weather:
                    result = "Не удалось получить данные о погоде."
                    return render_template('index.html', result=result)
                # оцениваем погодные условия
                temperature = start_weather['Temperature']['Metric']['Value']
                wind_speed = start_weather['Wind']['Speed']['Metric']['Value']
                precipitation_probability = start_weather.get('PrecipitationProbability', 0)  # может отсутствовать

                result = check_bad_weather(temperature, wind_speed, precipitation_probability)

            except requests.exceptions.RequestException:
                result = "Ошибка подключения к сервису погоды."
            except Exception as e:
                result = f"Произошла ошибка: {str(e)}"

    return render_template('index.html', result=result, start_city=start_city, end_city=end_city)

if __name__ == '__main__':
    app.run(debug=True)
