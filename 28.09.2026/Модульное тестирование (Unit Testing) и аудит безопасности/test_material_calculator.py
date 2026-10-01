import sys
from pathlib import Path
import unittest
import sqlite3
import tempfile
import os

# ==========================================
# НАСТРОЙКА ПУТЕЙ ДЛЯ ИМПОРТА ЯДРА РАСЧЕТА
# ==========================================
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent

# ИСПРАВЛЕНО: строгое соответствие дате 28.09.2026
MATERIAL_DIR = REPO_ROOT / "28.09.2026" / "Разработка ядра алгоритма расчета материалов"
STAGE2_DIR = REPO_ROOT / "14.09.2026" / "Интеграция с БД и агрегация данных (SQL + Backend)"
STAGE1_DIR = REPO_ROOT / "14.09.2026" / "Разработка ядра бизнес-логики (Расчет скидки)"

sys.path.insert(0, str(MATERIAL_DIR))
sys.path.insert(0, str(STAGE1_DIR))  # Для calculate_partner_discount внутри partner_service
sys.path.insert(0, str(STAGE2_DIR))

# Импортируем тестируемые функции
# Убедись, что файл с ядром называется f4_2_material_calculator.py (с нижним подчеркиванием!)
try:
    from f4_2_material_calculator import (
        calculate_material_required,
        ensure_materials_tables,
        seed_materials_data
    )
except ImportError:
    print("❌ Ошибка импорта! Убедись, что файл с ядром расчета переименован из 'f4.2...' в 'f4_2...'")
    sys.exit(1)


class TestMaterialCalculator(unittest.TestCase):
    """Unit-тесты для метода расчета материалов."""
    
    def setUp(self):
        """Создаёт временную чистую базу данных для каждого теста."""
        fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        
        # Инициализируем структуру справочников
        ensure_materials_tables(self.db_path)
        seed_materials_data(self.db_path)
        
        # Добавляем специфичные данные для предсказуемости проверок
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            # Чистим демо-данные и ставим свои для точности
            cursor.execute("DELETE FROM product_types")
            cursor.execute("DELETE FROM material_types")
            
            # Тип продукции ID=1: Коэффициент 2.0
            cursor.execute(
                "INSERT INTO product_types (id, name, coefficient) VALUES (?, ?, ?)",
                (1, 'TestProduct', 2.0)
            )
            # Тип материала ID=1: Брак 10%
            cursor.execute(
                "INSERT INTO material_types (id, name, defect_percent) VALUES (?, ?, ?)",
                (1, 'TestMaterial', 10.0)
            )
            conn.commit()
        finally:
            conn.close()

    def tearDown(self):
        """Удаляет временную базу после теста."""
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_standard_calculation(self):
        """Тест 1: Стандартный корректный расчет."""
        # param_1=5, param_2=10, quantity=100
        # Base = 5 * 10 * 2.0 = 100
        # Total Clean = 100 * 100 = 10000
        # With Defect = 10000 * 1.10 = 11000
        result = calculate_material_required(1, 1, 100, 5.0, 10.0, db_path=self.db_path)
        self.assertEqual(result, 11000)

    def test_rounding_up(self):
        """Тест 2: Проверка округления в большую сторону (ceil)."""
        # param_1=1, param_2=1, quantity=1
        # Base = 1 * 1 * 2.0 = 2.0
        # Total Clean = 2.0
        # With Defect = 2.0 * 1.10 = 2.2
        # Ceil(2.2) -> 3
        result = calculate_material_required(1, 1, 1, 1.0, 1.0, db_path=self.db_path)
        self.assertEqual(result, 3)
        self.assertNotEqual(result, 2)  # Не должно быть обычного округления вниз

    def test_invalid_product_type_id(self):
        """Тест 3: Несуществующий ID типа продукции."""
        # ID 999 не существует в справочнике
        result = calculate_material_required(999, 1, 100, 5.0, 10.0, db_path=self.db_path)
        self.assertEqual(result, -1)

    def test_negative_parameters(self):
        """Тест 4: Отрицательные параметры изделия."""
        # param_1 = -5.0
        result_neg_p1 = calculate_material_required(1, 1, 100, -5.0, 10.0, db_path=self.db_path)
        self.assertEqual(result_neg_p1, -1)
        # param_2 = -10.0
        result_neg_p2 = calculate_material_required(1, 1, 100, 5.0, -10.0, db_path=self.db_path)
        self.assertEqual(result_neg_p2, -1)

    def test_zero_or_negative_quantity(self):
        """Тест 5: Нулевое или отрицательное количество."""
        # quantity = 0
        result_zero = calculate_material_required(1, 1, 0, 5.0, 10.0, db_path=self.db_path)
        self.assertEqual(result_zero, -1)
        # quantity = -10
        result_neg_qty = calculate_material_required(1, 1, -10, 5.0, 10.0, db_path=self.db_path)
        self.assertEqual(result_neg_qty, -1)


if __name__ == '__main__':
    unittest.main()