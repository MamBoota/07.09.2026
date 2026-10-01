import sys
from pathlib import Path
import math
import sqlite3

# ==========================================
# НАСТРОЙКА ПУТЕЙ
# Файл лежит в: 29.09.2026/Разработка ядра алгоритма расчета материалов/
# ВАЖНО: partner_service импортирует calculate_partner_discount,
# поэтому нужно добавить ОБЕ папки в sys.path ДО импорта partner_service
# ==========================================
CURRENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = CURRENT_DIR.parent.parent
STAGE2_DIR = REPO_ROOT / "14.09.2026" / "Интеграция с БД и агрегация данных (SQL + Backend)"
STAGE1_DIR = REPO_ROOT / "14.09.2026" / "Разработка ядра бизнес-логики (Расчет скидки)"

# СНАЧАЛА добавляем обе папки в sys.path
sys.path.insert(0, str(STAGE1_DIR))  # для calculate_partner_discount (нужен partner_service)
sys.path.insert(0, str(STAGE2_DIR))  # для partner_service

# ТЕПЕРЬ импортируем partner_service — его внутренний импорт calculate_partner_discount найдёт модуль
from partner_service import DB_PATH

# ==========================================
# СПРАВОЧНИКИ БД: таблицы типов продукции и материалов
# ==========================================
# Демо-данные для справочников (коэффициенты и % брака)
DEMO_PRODUCT_TYPES = [
    (1, 'Электроника', 1.2),
    (2, 'Бытовая химия', 0.8),
    (3, 'Продукты питания', 1.0),
    (4, 'Текстиль', 0.95),
]

DEMO_MATERIAL_TYPES = [
    (1, 'Пластик', 3.0),
    (2, 'Металл', 5.0),
    (3, 'Бумага', 2.0),
    (4, 'Стекло', 7.5),
]


def ensure_materials_tables(db_path: str = DB_PATH) -> None:
    """Создаёт таблицы справочников product_types и material_types, если их нет."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS product_types (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                coefficient REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS material_types (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                defect_percent REAL NOT NULL
            )
        """)
        conn.commit()
    finally:
        conn.close()


def seed_materials_data(db_path: str = DB_PATH) -> None:
    """Заполняет справочники демо-данными, если они пустые."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        # Проверяем, есть ли уже данные
        cursor.execute("SELECT COUNT(*) FROM product_types")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO product_types (id, name, coefficient) VALUES (?, ?, ?)",
                DEMO_PRODUCT_TYPES
            )
        cursor.execute("SELECT COUNT(*) FROM material_types")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO material_types (id, name, defect_percent) VALUES (?, ?, ?)",
                DEMO_MATERIAL_TYPES
            )
        conn.commit()
    finally:
        conn.close()


def get_product_type_coefficient(db_path: str, product_type_id: int):
    """Возвращает коэффициент типа продукции или None, если ID не найден."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT coefficient FROM product_types WHERE id = ?",
            (product_type_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


def get_material_defect_percent(db_path: str, material_type_id: int):
    """Возвращает процент брака материала или None, если ID не найден."""
    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT defect_percent FROM material_types WHERE id = ?",
            (material_type_id,)
        )
        row = cursor.fetchone()
        return row[0] if row else None
    finally:
        conn.close()


# ==========================================
# ЯДРО АЛГОРИТМА: расчёт расхода материалов
# ==========================================
def calculate_material_required(
    product_type_id: int,
    material_type_id: int,
    quantity: int,
    param_1: float,
    param_2: float,
    db_path: str = DB_PATH
) -> int:
    """
    Рассчитывает итоговый расход сырья с учётом коэффициента типа продукции
    и процента брака материала.

    Возвращает:
        int — итоговый расход (округлённый вверх),
        -1  — если входные данные некорректны или ID не найдены в справочниках.

    Формула:
        Базовый расход на 1 ед. = param_1 × param_2 × coefficient
        Общий чистый расход     = Базовый × quantity
        Итог с учётом брака     = ceil(Общий чистый × (1 + defect_percent / 100))
    """
    # === ВАЛИДАЦИЯ ВХОДНЫХ ДАННЫХ ===
    # Проверяем типы и значения параметров
    try:
        if not isinstance(product_type_id, int) or not isinstance(material_type_id, int):
            return -1
        if not isinstance(quantity, int) or quantity <= 0:
            return -1
        # param_1 и param_2 должны быть положительными числами
        param_1 = float(param_1)
        param_2 = float(param_2)
        if param_1 <= 0 or param_2 <= 0:
            return -1
    except (TypeError, ValueError):
        return -1

    # === ПОЛУЧЕНИЕ ДАННЫХ ИЗ СПРАВОЧНИКОВ БД ===
    try:
        coefficient = get_product_type_coefficient(db_path, product_type_id)
        if coefficient is None:
            return -1  # Несуществующий ID типа продукции

        defect_percent = get_material_defect_percent(db_path, material_type_id)
        if defect_percent is None:
            return -1  # Несуществующий ID типа материала
    except sqlite3.Error:
        return -1  # Ошибка работы с БД

    # === РАСЧЁТ ПО ФОРМУЛЕ ===
    try:
        # Базовый расход на 1 единицу продукции
        base_per_unit = param_1 * param_2 * coefficient
        # Общий чистый расход на весь объём
        total_clean = base_per_unit * quantity
        # Итоговый расход с учётом процента брака
        total_with_defect = total_clean * (1 + defect_percent / 100)
        # Округление в большую сторону до целого
        return math.ceil(total_with_defect)
    except (OverflowError, ArithmeticError):
        return -1


# ==========================================
# ДЕМО-ЗАПУСК: проверка работы алгоритма
# ==========================================
def _print_result(description: str, result: int) -> None:
    """Красиво выводит результат расчёта."""
    if result == -1:
        print(f"  ❌ {description}: ОШИБКА (вернул -1)")
    else:
        print(f"  ✅ {description}: {result:,} ед.")


if __name__ == "__main__":
    print("=" * 70)
    print("  МОДУЛЬ РАСЧЁТА РАСХОДА МАТЕРИАЛОВ")
    print("=" * 70)

    # Инициализируем БД и справочники
    ensure_materials_tables(DB_PATH)
    seed_materials_data(DB_PATH)

    print("\n📚 Справочники в БД:")
    print("  Типы продукции: Электроника (коэф. 1.2), Бытовая химия (0.8),")
    print("                  Продукты питания (1.0), Текстиль (0.95)")
    print("  Типы материалов: Пластик (брак 3%), Металл (5%),")
    print("                   Бумага (2%), Стекло (7.5%)")

    print("\n" + "=" * 70)
    print("  ТЕСТОВЫЕ РАСЧЁТЫ")
    print("=" * 70)

    # Тест 1: Нормальный расчёт
    print("\n🧪 Тест 1: Электроника + Пластик, 100 шт., param_1=2.5, param_2=4.0")
    # Ожидаемо: 2.5 × 4.0 × 1.2 × 100 × 1.03 = 1236.0 → 1236
    _print_result(
        "Результат",
        calculate_material_required(1, 1, 100, 2.5, 4.0)
    )

    # Тест 2: Расчёт с дробным результатом (должен округлиться вверх)
    print("\n🧪 Тест 2: Бытовая химия + Металл, 50 шт., param_1=3.3, param_2=2.7")
    # Ожидаемо: 3.3 × 2.7 × 0.8 × 50 × 1.05 = 374.22 → 375
    _print_result(
        "Результат",
        calculate_material_required(2, 2, 50, 3.3, 2.7)
    )

    # Тест 3: Большие объёмы
    print("\n🧪 Тест 3: Продукты питания + Бумага, 10000 шт., param_1=1.5, param_2=2.0")
    # Ожидаемо: 1.5 × 2.0 × 1.0 × 10000 × 1.02 = 30600
    _print_result(
        "Результат",
        calculate_material_required(3, 3, 10000, 1.5, 2.0)
    )

    print("\n" + "=" * 70)
    print("  ПРОВЕРКА ОБРАБОТКИ ОШИБОК (должны вернуть -1)")
    print("=" * 70)

    # Тест 4: Несуществующий product_type_id
    print("\n🧪 Тест 4: Несуществующий product_type_id = 999")
    _print_result(
        "Результат",
        calculate_material_required(999, 1, 100, 2.5, 4.0)
    )

    # Тест 5: Несуществующий material_type_id
    print("\n🧪 Тест 5: Несуществующий material_type_id = 999")
    _print_result(
        "Результат",
        calculate_material_required(1, 999, 100, 2.5, 4.0)
    )

    # Тест 6: quantity <= 0
    print("\n🧪 Тест 6: quantity = 0")
    _print_result(
        "Результат",
        calculate_material_required(1, 1, 0, 2.5, 4.0)
    )

    # Тест 7: Отрицательный param_1
    print("\n🧪 Тест 7: param_1 = -1.5 (отрицательный)")
    _print_result(
        "Результат",
        calculate_material_required(1, 1, 100, -1.5, 4.0)
    )

    # Тест 8: param_2 = 0
    print("\n🧪 Тест 8: param_2 = 0")
    _print_result(
        "Результат",
        calculate_material_required(1, 1, 100, 2.5, 0)
    )

    # Тест 9: quantity отрицательный
    print("\n🧪 Тест 9: quantity = -10")
    _print_result(
        "Результат",
        calculate_material_required(1, 1, -10, 2.5, 4.0)
    )

    print("\n" + "=" * 70)
    print("  ✅ Все тесты завершены")
    print("=" * 70)