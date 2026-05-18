import sqlite3
from typing import List, Tuple, Optional

DB_NAME = "weather_bot.db"


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Таблица городов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            latitude REAL NOT NULL,
            longitude REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Добавляем начальные города
    from config import DEFAULT_COORDINATES
    for city_name, (lat, lon) in DEFAULT_COORDINATES.items():
        cursor.execute('''
            INSERT OR IGNORE INTO cities (name, latitude, longitude)
            VALUES (?, ?, ?)
        ''', (city_name, lat, lon))

    conn.commit()
    conn.close()


def get_all_cities() -> List[Tuple[int, str, float, float]]:
    # Получить все города
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, latitude, longitude FROM cities ORDER BY name")
    cities = cursor.fetchall()
    conn.close()
    return cities


def get_city_by_name(name: str) -> Optional[Tuple[int, str, float, float]]:
    # Получить город по названию
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, latitude, longitude FROM cities WHERE name = ?", (name,))
    city = cursor.fetchone()
    conn.close()
    return city


def add_city(name: str, latitude: float, longitude: float) -> bool:
    # Добавить новый город
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO cities (name, latitude, longitude) VALUES (?, ?, ?)",
            (name, latitude, longitude)
        )
        conn.commit()
        conn.close()
        return True
    except sqlite3.IntegrityError:
        return False


def delete_city(city_id: int) -> bool:
    # Удалить город
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cities WHERE id = ?", (city_id,))
    conn.commit()
    deleted = cursor.rowcount > 0
    conn.close()
    return deleted


def update_city(city_id: int, name: str, latitude: float, longitude: float) -> bool:
    # Обновить информацию о городе
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE cities SET name = ?, latitude = ?, longitude = ? WHERE id = ?",
        (name, latitude, longitude, city_id)
    )
    conn.commit()
    updated = cursor.rowcount > 0
    conn.close()
    return updated