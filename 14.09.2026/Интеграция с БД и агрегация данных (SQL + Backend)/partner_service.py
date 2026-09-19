import sqlite3
from calculate_partner_discount import calculate_partner_discount

DB_PATH = "partners.db"

def init_db(db_path: str = DB_PATH) -> None:
    """Создаёт таблицы partners и sales_history, если их нет."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        # Добавлены поля phone и rating для соответствия основной версии
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS partners (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                rating REAL
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

def get_partner_with_discount(db_path: str, partner_id: int) -> dict:
    """Возвращает словарь партнёра с РЕАЛЬНЫМИ данными из БД и рассчитанной скидкой."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.id, p.name, p.email, p.phone, p.rating,
                   COALESCE(SUM(s.quantity), 0) AS total_quantity
            FROM partners p
            LEFT JOIN sales_history s ON p.id = s.partner_id
            WHERE p.id = ?
            GROUP BY p.id, p.name, p.email, p.phone, p.rating;
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
        "phone": row[3] if row[3] else "Не указан",
        "rating": row[4] if row[4] is not None else 0.0,
        "total_quantity": row[5],
        "discount_percent": calculate_partner_discount(row[5]),
    }