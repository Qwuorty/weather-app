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

''' функция для получения текущих погодных данных по ключу локации '''
def get_current_weather(location_key):
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

''' функция для получения прогноза погоды по ключу локации '''
def get_forecast_data(location_key):
    forecast_url = f"http://dataservice.accuweather.com/forecasts/v1/daily/1day/{location_key}"
    params = {
        'apikey': API_KEY,
        'language': 'ru',
        'details': 'true',
        'metric': 'true'
    }
    response = requests.get(forecast_url, params=params)
    data = response.json()
    if data:
        return data
    else:
        return None

''' функция для оценки неблагоприятных погодных условий '''
def check_bad_weather(temperature, wind_speed, precipitation_probability):
    warnings = []
    if temperature < 0 or temperature > 35:
        warnings.append("Экстремальная температура.")
    if wind_speed > 50:
        warnings.append("Сильный ветер.")
    if precipitation_probability > 70:
        warnings.append("Высокая вероятность осадков.")
    if warnings:
        return "Неблагоприятные погодные условия: " + " ".join(warnings)
    else:
        return "Погодные условия благоприятные."

''' основной маршрут приложения '''
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    start_city = None
    end_city = None
    start_weather_info = None
    end_weather_info = None

    if request.method == 'POST':
        start_city = request.form.get('start_city')
        end_city = request.form.get('end_city')
        if not start_city or not end_city:
            result = "Пожалуйста, введите названия обоих городов."
        else:
            try:
                # получаем ключи локации для начального и конечного города
                start_location_key = get_location_key(start_city)
                end_location_key = get_location_key(end_city)
                if not start_location_key:
                    result = f"Не удалось найти город: {start_city}"
                    return render_template('index.html', result=result)
                if not end_location_key:
                    result = f"Не удалось найти город: {end_city}"
                    return render_template('index.html', result=result)
                # получаем текущие погодные данные для начального и конечного города
                start_current_weather = get_current_weather(start_location_key)
                end_current_weather = get_current_weather(end_location_key)
                if not start_current_weather:
                    result = f"Не удалось получить данные о погоде для города {start_city}."
                    return render_template('index.html', result=result)
                if not end_current_weather:
                    result = f"Не удалось получить данные о погоде для города {end_city}."
                    return render_template('index.html', result=result)
                # получаем прогноз погоды для начального и конечного города
                start_forecast = get_forecast_data(start_location_key)
                end_forecast = get_forecast_data(end_location_key)
                if not start_forecast:
                    result = f"Не удалось получить прогноз погоды для города {start_city}."
                    return render_template('index.html', result=result)
                if not end_forecast:
                    result = f"Не удалось получить прогноз погоды для города {end_city}."
                    return render_template('index.html', result=result)
                # собираем информацию для отображения
                start_weather_info = {
                    'city': start_city,
                    'current_temperature': start_current_weather['Temperature']['Metric']['Value'],
                    'weather_text': start_current_weather['WeatherText'],
                    'wind_speed': start_current_weather['Wind']['Speed']['Metric']['Value'],
                    'humidity': start_current_weather['RelativeHumidity'],
                    'pressure': start_current_weather['Pressure']['Metric']['Value'],
                    'min_temp': start_forecast['DailyForecasts'][0]['Temperature']['Minimum']['Value'],
                    'max_temp': start_forecast['DailyForecasts'][0]['Temperature']['Maximum']['Value'],
                    'precipitation_probability': start_forecast['DailyForecasts'][0]['Day']['PrecipitationProbability'],
                }

                end_weather_info = {
                    'city': end_city,
                    'current_temperature': end_current_weather['Temperature']['Metric']['Value'],
                    'weather_text': end_current_weather['WeatherText'],
                    'wind_speed': end_current_weather['Wind']['Speed']['Metric']['Value'],
                    'humidity': end_current_weather['RelativeHumidity'],
                    'pressure': end_current_weather['Pressure']['Metric']['Value'],
                    'min_temp': end_forecast['DailyForecasts'][0]['Temperature']['Minimum']['Value'],
                    'max_temp': end_forecast['DailyForecasts'][0]['Temperature']['Maximum']['Value'],
                    'precipitation_probability': end_forecast['DailyForecasts'][0]['Day']['PrecipitationProbability'],
                }

                # оцениваем неблагоприятные погодные условия для начального и конечного города
                start_bad_weather = check_bad_weather(
                    start_weather_info['current_temperature'],
                    start_weather_info['wind_speed'],
                    start_weather_info['precipitation_probability']
                )

                end_bad_weather = check_bad_weather(
                    end_weather_info['current_temperature'],
                    end_weather_info['wind_speed'],
                    end_weather_info['precipitation_probability']
                )

                result = {
                    'start_weather_info': start_weather_info,
                    'end_weather_info': end_weather_info,
                    'start_bad_weather': start_bad_weather,
                    'end_bad_weather': end_bad_weather
                }

            except requests.exceptions.RequestException:
                result = "Ошибка подключения к сервису погоды."
            except Exception as e:
                result = f"Произошла ошибка: {str(e)}"

    return render_template('index.html', result=result, start_city=start_city, end_city=end_city)

if __name__ == '__main__':
    app.run(debug=True)