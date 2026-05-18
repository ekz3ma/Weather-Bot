import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.enums.parse_mode import ParseMode

from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, get_all_cities, add_city, delete_city, get_city_by_name
from parser import WeatherParser

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

weather_parser = WeatherParser()
admin_states = {}


def is_admin(user_id: int) -> bool:
    # Проверка, является ли пользователь администратором
    return user_id in ADMIN_IDS


def get_cities_keyboard() -> InlineKeyboardMarkup:
    # Клавиатура с городами
    cities = get_all_cities()
    keyboard = []

    row = []
    for i, (city_id, city_name, _, _) in enumerate(cities):
        row.append(InlineKeyboardButton(text=city_name, callback_data=f"weather_{city_id}"))
        if len(row) == 2 or i == len(cities) - 1:
            keyboard.append(row)
            row = []

    # Добавляем кнопку обновления и админ-панель
    keyboard.append([InlineKeyboardButton(text="🔄 Обновить", callback_data="refresh")])

    if is_admin(bot.id):  # Здесь нужно будет передавать user_id
        keyboard.append([InlineKeyboardButton(text="👑 Админ-панель", callback_data="admin_panel")])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_keyboard() -> InlineKeyboardMarkup:
    # Клавиатура админ-панели
    keyboard = [
        [InlineKeyboardButton(text="➕ Добавить город", callback_data="admin_add_city")],
        [InlineKeyboardButton(text="❌ Удалить город", callback_data="admin_delete_city")],
        [InlineKeyboardButton(text="📋 Список городов", callback_data="admin_list_cities")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_delete_city_keyboard() -> InlineKeyboardMarkup:
    # Клавиатура для удаления города
    cities = get_all_cities()
    keyboard = []

    for city_id, city_name, _, _ in cities:
        keyboard.append([
            InlineKeyboardButton(text=f"❌ {city_name}", callback_data=f"delete_city_{city_id}")
        ])

    keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    # Обработчик команды /start
    welcome_text = (
        "🌤 **Добро пожаловать в погодный бот!**\n\n"
        "Я покажу вам прогноз погоды на сегодня и ближайшие 7 дней.\n"
        "Выберите город из меню ниже, чтобы узнать погоду.\n\n"
        "📊 Данные предоставлены Open-Meteo.com"
    )

    await message.answer(
        welcome_text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_cities_keyboard()
    )


@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    # Обработчик команды /help
    help_text = (
        "🤖 **Помощь по боту:**\n\n"
        "🔹 /start - Запустить бота\n"
        "🔹 /help - Показать эту справку\n"
        "🔹 /weather - Показать клавиатуру с городами\n\n"
        "📌 **Как пользоваться:**\n"
        "1. Выберите город из списка\n"
        "2. Получите подробный прогноз на 7 дней\n"
        "3. Используйте кнопку 'Обновить' для обновления списка"
    )

    if is_admin(message.from_user.id):
        help_text += "\n\n👑 **Админ-команды:**\n"
        help_text += "🔹 /admin - Открыть админ-панель"

    await message.answer(help_text, parse_mode=ParseMode.MARKDOWN)


@dp.message(Command("weather"))
async def cmd_weather(message: types.Message):
    # Обработчик команды /weather
    await message.answer("🌍 Выберите город:", reply_markup=get_cities_keyboard())


@dp.message(Command("admin"))
async def cmd_admin(message: types.Message):
    # Обработчик команды /admin
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У вас нет доступа к админ-панели!")
        return

    await message.answer(
        "👑 **Админ-панель**\n\nВыберите действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )


@dp.message(Command("now"))
async def cmd_now(message: types.Message):
    """Быстрый прогноз текущей погоды"""
    # Можно добавить логику для определения города пользователя
    # или использовать город по умолчанию
    default_city = get_all_cities()[0] if get_all_cities() else None

    if not default_city:
        await message.answer("❌ Нет доступных городов")
        return

    city_id, city_name, lat, lon = default_city

    loading_msg = await message.answer(f"⏳ Загрузка текущей погоды для {city_name}...")

    weather_data = weather_parser.get_current_weather_only(lat, lon)

    if weather_data:
        forecast_text = weather_parser.format_current_weather(weather_data, city_name)
        await loading_msg.edit_text(forecast_text, parse_mode=ParseMode.MARKDOWN)
    else:
        await loading_msg.edit_text(f"❌ Не удалось получить данные для {city_name}")


@dp.callback_query(lambda c: c.data.startswith("weather_"))
async def process_weather_callback(callback_query: CallbackQuery):
    """Обработчик выбора города"""
    await callback_query.answer()

    city_id = int(callback_query.data.split("_")[1])
    cities = get_all_cities()

    city = None
    for cid, name, lat, lon in cities:
        if cid == city_id:
            city = (name, lat, lon)
            break

    if not city:
        await callback_query.message.edit_text("❌ Город не найден!")
        return

    city_name, lat, lon = city

    # Отправляем сообщение о загрузке
    loading_msg = await callback_query.message.edit_text(
        f"⏳ Загрузка прогноза для города {city_name}..."
    )

    # Получаем погоду
    weather_data = weather_parser.get_weather_forecast(lat, lon)

    if weather_data:
        # Полный прогноз с текущей погодой
        forecast_text = weather_parser.format_forecast_message(weather_data, city_name, include_current=True)

        # Альтернативно, можно использовать компактный формат:
        # forecast_text = weather_parser.format_compact_forecast(weather_data, city_name)

        await loading_msg.edit_text(
            forecast_text,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=get_cities_keyboard()
        )
    else:
        await loading_msg.edit_text(
            f"❌ Не удалось получить данные о погоде для города {city_name}",
            reply_markup=get_cities_keyboard()
        )


@dp.callback_query(lambda c: c.data == "refresh")
async def process_refresh_callback(callback_query: CallbackQuery):
    # Обработчик обновления
    await callback_query.answer()
    await callback_query.message.edit_reply_markup(reply_markup=get_cities_keyboard())


@dp.callback_query(lambda c: c.data == "back_to_menu")
async def process_back_to_menu(callback_query: CallbackQuery):
    # Возврат в главное меню
    await callback_query.answer()
    await callback_query.message.edit_text(
        "🌍 Выберите город:",
        reply_markup=get_cities_keyboard()
    )


@dp.callback_query(lambda c: c.data == "admin_panel")
async def process_admin_panel(callback_query: CallbackQuery):
    # Открытие админ-панели
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("⛔ Нет доступа!", show_alert=True)
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        "👑 **Админ-панель**\n\nВыберите действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )


@dp.callback_query(lambda c: c.data == "admin_add_city")
async def process_add_city(callback_query: CallbackQuery):
    # Добавление нового города
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("⛔ Нет доступа!", show_alert=True)
        return

    await callback_query.answer()
    admin_states[callback_query.from_user.id] = {"action": "awaiting_city_name"}

    await callback_query.message.edit_text(
        "🏙 **Добавление нового города**\n\n"
        "Введите название города:\n"
        "(например: Сочи или New York)\n\n"
        "🔹 Для отмены введите /cancel",
        parse_mode=ParseMode.MARKDOWN
    )


@dp.callback_query(lambda c: c.data == "admin_delete_city")
async def process_delete_city(callback_query: CallbackQuery):
    # Удаление города
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("⛔ Нет доступа!", show_alert=True)
        return

    await callback_query.answer()
    await callback_query.message.edit_text(
        "🗑 **Удаление города**\n\nВыберите город для удаления:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_delete_city_keyboard()
    )


@dp.callback_query(lambda c: c.data == "admin_list_cities")
async def process_list_cities(callback_query: CallbackQuery):
    # Список городов
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("⛔ Нет доступа!", show_alert=True)
        return

    cities = get_all_cities()

    if not cities:
        text = "📋 **Список городов:**\n\nГородов пока нет"
    else:
        text = "📋 **Список городов:**\n\n"
        for i, (city_id, city_name, lat, lon) in enumerate(cities, 1):
            text += f"{i}. {city_name} (ID: {city_id})\n"
            text += f"   📍 {lat}, {lon}\n\n"

    await callback_query.answer()
    await callback_query.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_panel")]
        ])
    )


@dp.callback_query(lambda c: c.data.startswith("delete_city_"))
async def process_delete_city_confirm(callback_query: CallbackQuery):
    # Подтверждение удаления города
    if not is_admin(callback_query.from_user.id):
        await callback_query.answer("⛔ Нет доступа!", show_alert=True)
        return

    city_id = int(callback_query.data.split("_")[2])

    if delete_city(city_id):
        await callback_query.answer("✅ Город удален!", show_alert=True)
    else:
        await callback_query.answer("❌ Город не найден!", show_alert=True)

    await callback_query.message.edit_text(
        "👑 **Админ-панель**\n\nВыберите действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=get_admin_keyboard()
    )


@dp.message()
async def handle_admin_input(message: types.Message):
    # Обработка ввода админа
    if message.from_user.id not in admin_states:
        return

    state = admin_states[message.from_user.id]

    if message.text == "/cancel":
        del admin_states[message.from_user.id]
        await message.answer("❌ Действие отменено", reply_markup=get_cities_keyboard())
        return

    if state.get("action") == "awaiting_city_name":
        city_name = message.text.strip()
        admin_states[message.from_user.id] = {
            "action": "awaiting_coordinates",
            "city_name": city_name
        }
        await message.answer(
            f"🏙 Город: {city_name}\n\n"
            "Теперь введите координаты в формате:\n"
            "`широта, долгота`\n\n"
            "Пример: `43.5855, 39.7231` (Сочи)\n\n"
            "🔹 Для отмены введите /cancel",
            parse_mode=ParseMode.MARKDOWN
        )

    elif state.get("action") == "awaiting_coordinates":
        try:
            coords = message.text.strip().split(",")
            lat = float(coords[0].strip())
            lon = float(coords[1].strip())

            city_name = state["city_name"]

            if add_city(city_name, lat, lon):
                await message.answer(
                    f"✅ Город '{city_name}' успешно добавлен!\n"
                    f"📍 Координаты: {lat}, {lon}",
                    reply_markup=get_cities_keyboard()
                )
            else:
                await message.answer(
                    f"❌ Город '{city_name}' уже существует в базе данных!",
                    reply_markup=get_cities_keyboard()
                )

            del admin_states[message.from_user.id]

        except (ValueError, IndexError):
            await message.answer(
                "❌ Неверный формат координат!\n\n"
                "Введите в формате: `широта, долгота`\n"
                "Пример: `43.5855, 39.7231`\n\n"
                "Попробуйте еще раз или введите /cancel",
                parse_mode=ParseMode.MARKDOWN
            )


async def main():
    # Инициализация базы данных
    init_db()

    print("🤖 Бот запущен!")
    print(f"📊 База данных: weather_bot.db")
    print(f"👑 Администраторы: {ADMIN_IDS}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())