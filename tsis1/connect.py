# connect.py
# Простая функция, которая открывает соединение с базой данных.

import psycopg2
from config import DB_CONFIG


def get_connection():
    """
    Открывает и возвращает соединение с PostgreSQL.
    Если что-то не так (неверный пароль, база не запущена и т.д.)
    - выведет понятную ошибку и завершит программу.
    """
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except psycopg2.OperationalError as e:
        print("Не получилось подключиться к базе данных.")
        print("Проверь, что PostgreSQL запущен и данные в config.py верные.")
        print("Подробности ошибки:", e)
        raise SystemExit(1)
