import requests
from datetime import datetime
from typing import Dict, Optional


class WeatherParser:
    """Парсер погоды с Open-Meteo"""

    @staticmethod
    def get_weather_forecast(latitude: float, longitude: float, timezone: str = "auto") -> Optional[Dict]:
        """Получение прогноза погоды (ежедневно + почасово)"""

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "current": [  # 👈 ТЕКУЩАЯ ПОГОДА
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "precipitation",
                "rain",
                "showers",
                "snowfall",
                "weather_code",
                "cloud_cover",
                "pressure_msl",
                "surface_pressure",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m"
            ],
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "weathercode",
                "sunrise",
                "sunset",
                "precipitation_sum",
                "rain_sum",
                "snowfall_sum"
            ],
            "hourly": [
                "temperature_2m",
                "wind_speed_10m",
                "wind_gusts_10m",
                "weathercode"
            ],
            "forecast_days": 8
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
            return None

    @staticmethod
    def get_current_weather_only(latitude: float, longitude: float, timezone: str = "auto") -> Optional[Dict]:
        """Получение только текущей погоды (быстрый запрос)"""

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "current": [
                "temperature_2m",
                "relative_humidity_2m",
                "apparent_temperature",
                "is_day",
                "precipitation",
                "rain",
                "showers",
                "snowfall",
                "weather_code",
                "cloud_cover",
                "pressure_msl",
                "wind_speed_10m",
                "wind_direction_10m",
                "wind_gusts_10m"
            ]
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе: {e}")
            return None

    @staticmethod
    def get_weather_condition(weather_code: int) -> str:
        """Расшифровка кодов погоды"""
        weather_codes = {
            0: "☀️ Ясно",
            1: "🌤 Преимущественно ясно",
            2: "⛅️ Переменная облачность",
            3: "☁️ Облачно",
            45: "🌫 Туман",
            48: "🌫 Туман с изморозью",
            51: "🌧 Легкая морось",
            53: "🌧 Морось",
            55: "🌧 Сильная морось",
            56: "🌧 Ледяная морось",
            57: "🌧 Сильная ледяная морось",
            61: "🌧 Небольшой дождь",
            63: "🌧 Дождь",
            65: "🌧 Сильный дождь",
            66: "🌧 Ледяной дождь",
            67: "🌧 Сильный ледяной дождь",
            71: "🌨 Небольшой снег",
            73: "🌨 Снег",
            75: "🌨 Сильный снег",
            77: "❄️ Снежные зерна",
            80: "🌧 Ливень",
            81: "🌧 Сильный ливень",
            82: "🌧 Очень сильный ливень",
            85: "❄️ Снегопад",
            86: "❄️ Сильный снегопад",
            95: "⛈ Гроза",
            96: "⛈ Гроза с градом",
            99: "⛈ Сильная гроза с градом"
        }
        return weather_codes.get(weather_code, "❓ Неизвестно")

    @staticmethod
    def get_wind_direction(degrees: float) -> str:
        """Преобразование градусов в направление ветра"""
        if degrees is None:
            return "❓ неизвестно"

        directions = [
            "северный", "северо-восточный", "восточный", "юго-восточный",
            "южный", "юго-западный", "западный", "северо-западный"
        ]
        idx = round(degrees / 45) % 8
        return directions[idx]

    @staticmethod
    def format_wind_speed(kmh: float) -> str:
        """Форматирование скорости ветра"""
        if kmh < 5:
            desc = "штиль"
        elif kmh < 15:
            desc = "слабый"
        elif kmh < 30:
            desc = "умеренный"
        elif kmh < 50:
            desc = "сильный"
        else:
            desc = "штормовой"
        return f"{kmh:.1f} км/ч ({desc})"

    @staticmethod
    def format_current_weather(weather_data: Dict, city_name: str) -> str:
        """Форматирование текущей погоды"""

        if not weather_data or 'current' not in weather_data:
            return f"❌ Не удалось получить текущую погоду для города {city_name}"

        current = weather_data['current']
        current_units = weather_data.get('current_units', {})

        # Получаем время
        current_time = datetime.now().strftime("%H:%M")

        # Определяем время суток
        is_day = current.get('is_day', 1)
        day_emoji = "☀️" if is_day else "🌙"

        # Температура
        temp = current.get('temperature_2m')
        temp_unit = current_units.get('temperature_2m', '°C')

        # Ощущается как
        feels_like = current.get('apparent_temperature')

        # Влажность
        humidity = current.get('relative_humidity_2m')
        humidity_unit = current_units.get('relative_humidity_2m', '%')

        # Давление
        pressure = current.get('pressure_msl')
        pressure_unit = current_units.get('pressure_msl', 'hPa')

        # Осадки
        precipitation = current.get('precipitation', 0)
        rain = current.get('rain', 0)
        snow = current.get('snowfall', 0)
        precip_unit = current_units.get('precipitation', 'mm')

        # Облачность
        cloud_cover = current.get('cloud_cover')
        cloud_unit = current_units.get('cloud_cover', '%')

        # Ветер
        wind_speed = current.get('wind_speed_10m')
        wind_gusts = current.get('wind_gusts_10m')
        wind_dir_deg = current.get('wind_direction_10m')
        wind_dir = WeatherParser.get_wind_direction(wind_dir_deg)

        # Погодные условия
        weather_code = current.get('weather_code')
        condition = WeatherParser.get_weather_condition(weather_code) if weather_code else "❓ Неизвестно"

        # Формируем сообщение
        message = f"🌍 **{city_name}** {day_emoji}\n"
        message += "═" * 35 + "\n\n"

        # Основная информация
        message += f"🕐 **Сейчас** ({current_time})\n"
        message += f"🌡 **Температура:** {temp:.1f}{temp_unit}\n"

        if feels_like:
            message += f"🤔 **Ощущается как:** {feels_like:.1f}{temp_unit}\n"

        message += f"\n🎯 **Погода:** {condition}\n"

        # Ветер
        wind_str = WeatherParser.format_wind_speed(wind_speed) if wind_speed else "Нет данных"
        message += f"💨 **Ветер:** {wind_str}"
        if wind_dir and wind_dir != "❓ неизвестно":
            message += f", {wind_dir}"
        message += "\n"

        if wind_gusts and wind_gusts > 0:
            gusts_str = WeatherParser.format_wind_speed(wind_gusts)
            message += f"⚡️ **Порывы:** {gusts_str}\n"

        # Дополнительные параметры
        if humidity:
            message += f"💧 **Влажность:** {humidity:.0f}{humidity_unit}\n"

        if pressure:
            # Конвертация в мм рт. ст. если нужно
            if pressure_unit == 'hPa':
                pressure_mm = pressure * 0.750062
                message += f"📊 **Давление:** {pressure:.1f} {pressure_unit} ({pressure_mm:.1f} мм рт. ст.)\n"
            else:
                message += f"📊 **Давление:** {pressure:.1f} {pressure_unit}\n"

        if cloud_cover is not None:
            cloud_emoji = "☁️" if cloud_cover > 50 else "🌤"
            message += f"{cloud_emoji} **Облачность:** {cloud_cover:.0f}{cloud_unit}\n"

        # Осадки
        if precipitation and precipitation > 0:
            message += f"🌧 **Осадки:** {precipitation:.1f}{precip_unit}"
            if rain and rain > 0:
                message += f" (дождь: {rain:.1f}{precip_unit})"
            if snow and snow > 0:
                message += f" (снег: {snow:.1f}{precip_unit})"
            message += "\n"

        return message

    @staticmethod
    def format_forecast_message(weather_data: Dict, city_name: str, include_current: bool = True) -> str:
        """Форматирование полного прогноза (текущий + на дни)"""

        if not weather_data:
            return f"❌ Не удалось получить данные о погоде для города {city_name}"

        message = ""

        # Добавляем текущую погоду, если запрошено
        if include_current and 'current' in weather_data:
            message += WeatherParser.format_current_weather(weather_data, city_name)
            message += "\n" + "═" * 35 + "\n\n"

        daily = weather_data['daily']

        # Прогноз на 7 дней
        message += "📅 **Прогноз на 7 дней:**\n\n"

        for i in range(min(7, len(daily['time']))):
            date = datetime.fromisoformat(daily['time'][i])
            day_label = "🔴 СЕГОДНЯ" if i == 0 else date.strftime("%A")

            temp_min = daily['temperature_2m_min'][i]
            temp_max = daily['temperature_2m_max'][i]
            wind = daily['wind_speed_10m_max'][i]
            gusts = daily['wind_gusts_10m_max'][i]
            weather_code = daily['weathercode'][i]

            condition = WeatherParser.get_weather_condition(weather_code)
            wind_str = WeatherParser.format_wind_speed(wind)

            # Осадки за день
            precip_sum = daily.get('precipitation_sum', [0])[i] if 'precipitation_sum' in daily else 0
            rain_sum = daily.get('rain_sum', [0])[i] if 'rain_sum' in daily else 0
            snow_sum = daily.get('snowfall_sum', [0])[i] if 'snowfall_sum' in daily else 0

            # Восход/закат
            sunrise = daily.get('sunrise', [''])[i] if 'sunrise' in daily else ''
            sunset = daily.get('sunset', [''])[i] if 'sunset' in daily else ''

            message += f"**{day_label}** ({date.strftime('%d.%m.%Y')})\n"
            message += f"🌡 {temp_min:.1f}°C → {temp_max:.1f}°C\n"
            message += f"💨 Ветер: {wind_str}\n"

            if gusts and gusts > wind + 5:
                message += f"⚡️ Порывы: {gusts:.1f} км/ч\n"

            message += f"🎯 {condition}\n"

            # Добавляем информацию об осадках
            if precip_sum and precip_sum > 0:
                message += f"🌧 Осадки: {precip_sum:.1f} мм"
                if rain_sum and rain_sum > 0:
                    message += f" (дождь: {rain_sum:.1f} мм)"
                if snow_sum and snow_sum > 0:
                    message += f" (снег: {snow_sum:.1f} мм)"
                message += "\n"

            # Добавляем время восхода/заката
            if sunrise and sunset:
                sunrise_time = datetime.fromisoformat(sunrise).strftime("%H:%M") if isinstance(sunrise,
                                                                                               str) else sunrise
                sunset_time = datetime.fromisoformat(sunset).strftime("%H:%M") if isinstance(sunset, str) else sunset
                message += f"🌅 Восход: {sunrise_time} | 🌇 Закат: {sunset_time}\n"

            message += "\n"

        return message

    @staticmethod
    def format_compact_forecast(weather_data: Dict, city_name: str) -> str:
        """Компактный формат (только основное)"""

        if not weather_data:
            return f"❌ Не удалось получить данные для {city_name}"

        message = f"🌍 **{city_name}**\n"
        message += "═" * 30 + "\n"

        # Текущая погода
        if 'current' in weather_data:
            current = weather_data['current']
            temp = current.get('temperature_2m')
            condition = WeatherParser.get_weather_condition(current.get('weather_code'))
            wind = current.get('wind_speed_10m')

            message += f"🕐 Сейчас: {temp:.1f}°C | {condition}\n"
            message += f"💨 Ветер: {WeatherParser.format_wind_speed(wind)}\n\n"

        # Прогноз на 3 дня
        daily = weather_data['daily']
        message += "📅 **Ближайшие 3 дня:**\n"

        for i in range(min(3, len(daily['time']))):
            date = datetime.fromisoformat(daily['time'][i])
            day_name = "Сегодня" if i == 0 else date.strftime("%a")

            temp_min = daily['temperature_2m_min'][i]
            temp_max = daily['temperature_2m_max'][i]
            condition = WeatherParser.get_weather_condition(daily['weathercode'][i])

            message += f"• {day_name}: {temp_min:.0f}°C→{temp_max:.0f}°C | {condition}\n"

        return message