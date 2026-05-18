import requests
from datetime import datetime
from typing import Dict, Optional


class WeatherParser:
    @staticmethod
    def get_weather_forecast(latitude: float, longitude: float, timezone: str = "auto") -> Optional[Dict]:

        url = "https://api.open-meteo.com/v1/forecast"

        params = {
            "latitude": latitude,
            "longitude": longitude,
            "timezone": timezone,
            "daily": [
                "temperature_2m_max",
                "temperature_2m_min",
                "wind_speed_10m_max",
                "wind_gusts_10m_max",
                "weathercode"
            ],
            "forecast_days": 8
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException:
            return None

    @staticmethod
    def get_weather_condition(weather_code: int) -> str:
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
            61: "🌧 Небольшой дождь",
            63: "🌧 Дождь",
            65: "🌧 Сильный дождь",
            71: "🌨 Небольшой снег",
            73: "🌨 Снег",
            75: "🌨 Сильный снег",
            80: "🌧 Ливень",
            81: "🌧 Сильный ливень",
            85: "❄️ Снегопад",
            86: "❄️ Сильный снегопад",
            95: "⛈ Гроза",
            96: "⛈ Гроза с градом",
            99: "⛈ Сильная гроза с градом"
        }
        return weather_codes.get(weather_code, "❓ Неизвестно")

    @staticmethod
    def format_wind_speed(kmh: float) -> str:
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
    def format_forecast_message(weather_data: Dict, city_name: str) -> str:

        if not weather_data:
            return f"❌ Не удалось получить данные о погоде для города {city_name}"

        daily = weather_data['daily']

        message = f"🌍 **Прогноз погоды: {city_name}**\n"
        message += "=" * 40 + "\n\n"

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

            message += f"**{day_label}** ({date.strftime('%d.%m.%Y')})\n"
            message += f"🌡 {temp_min:.1f}°C → {temp_max:.1f}°C\n"
            message += f"💨 Ветер: {wind_str}\n"

            if gusts and gusts > wind + 5:
                message += f"⚡️ Порывы: {gusts:.1f} км/ч\n"

            message += f"🎯 {condition}\n\n"

        return message