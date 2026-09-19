import sys
from pathlib import Path

# Добавляем путь к файлу calculate_partner_discount.py
BASE_DIR = Path(__file__).resolve().parent.parent  # Поднимаемся на уровень выше
FIRST_TASK_DIR = BASE_DIR / "Разработка ядра бизнес-логики (Расчет скидки)"
sys.path.insert(0, str(FIRST_TASK_DIR))

# Теперь импорт сработает
import sqlite3
from calculate_partner_discount import calculate_partner_discount


DB_PATH = "partners.db"


def init_db(db_path: str = DB_PATH) -> None:
    """Создаёт таблицы partners и sales_history, если их нет."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS partners (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sales_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                partner_id INTEGER NOT NULL,
                quantity INTEGER NOT NULL,
                FOREIGN KEY (partner_id) REFERENCES partners(id)
            );
        """)
        conn.commit()
    finally:
        conn.close()


def get_partner_sales_volume(db_path: str, partner_id: int) -> int:
    """Возвращает суммарный объём продаж партнёра через LEFT JOIN + SUM."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COALESCE(SUM(s.quantity), 0)
            FROM partners p
            LEFT JOIN sales_history s ON p.id = s.partner_id
            WHERE p.id = ?
            GROUP BY p.id;
        """, (partner_id,))
        row = cursor.fetchone()
    finally:
        conn.close()
    return row[0] if row else 0


def get_partner_with_discount(db_path: str, partner_id: int) -> dict:
    """Возвращает словарь партнёра с рассчитанным процентом скидки."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.email,
                   COALESCE(SUM(s.quantity), 0) AS total_quantity
            FROM partners p
            LEFT JOIN sales_history s ON p.id = s.partner_id
            WHERE p.id = ?
            GROUP BY p.id, p.name, p.email;
        """, (partner_id,))
        row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        return {"error": "Partner not found"}

    return {
        "id": row[0],
        "name": row[1],
        "email": row[2],
        "total_quantity": row[3],
        "discount_percent": calculate_partner_discount(row[3]),
    }
