import sys
from pathlib import Path

# Добавляем путь к файлу calculate_partner_discount.py
BASE_DIR = Path(__file__).resolve().parent.parent  # Поднимаемся на уровень выше
FIRST_TASK_DIR = BASE_DIR / "Разработка ядра бизнес-логики (Расчет скидки)"
sys.path.insert(0, str(FIRST_TASK_DIR))

# Теперь импорт сработает
import os
import sqlite3
import tempfile
import unittest
from calculate_partner_discount import calculate_partner_discount
from partner_service import (
    init_db,
    get_partner_sales_volume,
    get_partner_with_discount,
)


def _seed_db(db_path: str) -> None:
    """Заполняет тестовую БД демо-данными."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.executemany(
            "INSERT INTO partners (id, name, email) VALUES (?, ?, ?);",
            [
                (1, "Alice", "alice@example.com"),
                (2, "Bob", "bob@example.com"),
                (3, "Charlie", "charlie@example.com"),
            ],
        )
        cursor.executemany(
            "INSERT INTO sales_history (partner_id, quantity) VALUES (?, ?);",
            [
                (1, 5_000),
                (1, 6_000),
                (2, 50_000),
                (2, 250_000),
            ],
        )
        conn.commit()
    finally:
        conn.close()


class TestPartnerService(unittest.TestCase):
    """Тесты интеграции БД и расчёта скидки."""

    def setUp(self) -> None:
        # Создаём временный файл для БД
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        init_db(self.db_path)
        _seed_db(self.db_path)

    def tearDown(self) -> None:
        # Удаляем временный файл после теста
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_sales_volume_for_active_partner(self):
        self.assertEqual(get_partner_sales_volume(self.db_path, 1), 11_000)

    def test_sales_volume_for_high_volume_partner(self):
        self.assertEqual(get_partner_sales_volume(self.db_path, 2), 300_000)

    def test_sales_volume_for_partner_without_sales(self):
        self.assertEqual(get_partner_sales_volume(self.db_path, 3), 0)

    def test_sales_volume_for_unknown_partner(self):
        self.assertEqual(get_partner_sales_volume(self.db_path, 999), 0)

    def test_partner_with_discount_5_percent(self):
        partner = get_partner_with_discount(self.db_path, 1)
        self.assertEqual(partner["discount_percent"], 5)
        self.assertEqual(partner["total_quantity"], 11_000)

    def test_partner_with_discount_15_percent(self):
        partner = get_partner_with_discount(self.db_path, 2)
        self.assertEqual(partner["discount_percent"], 15)

    def test_partner_with_discount_0_percent(self):
        partner = get_partner_with_discount(self.db_path, 3)
        self.assertEqual(partner["discount_percent"], 0)

    def test_partner_not_found(self):
        result = get_partner_with_discount(self.db_path, 999)
        self.assertEqual(result, {"error": "Partner not found"})

    def test_partner_structure(self):
        partner = get_partner_with_discount(self.db_path, 1)
        self.assertIn("id", partner)
        self.assertIn("name", partner)
        self.assertIn("email", partner)
        self.assertIn("total_quantity", partner)
        self.assertIn("discount_percent", partner)

    def test_calculate_discount_directly_15_percent(self):
        """Прямой вызов функции для покрытия ветки >= 300_000."""
        self.assertEqual(calculate_partner_discount(300_000), 15)
        self.assertEqual(calculate_partner_discount(500_000), 15)

    def test_calculate_discount_10_percent(self):
        """Прямой вызов для покрытия ветки 10% (50_000 - 299_999)."""
        self.assertEqual(calculate_partner_discount(100_000), 10)

if __name__ == "__main__":
    unittest.main()
