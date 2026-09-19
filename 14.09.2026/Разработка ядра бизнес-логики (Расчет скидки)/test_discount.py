import unittest
from calculate_partner_discount import calculate_partner_discount


class TestCalculatePartnerDiscount(unittest.TestCase):
    """Тесты пограничных значений для calculate_partner_discount."""

    def test_below_first_threshold(self):
        self.assertEqual(calculate_partner_discount(9_999), 0)

    def test_first_threshold_exact(self):
        self.assertEqual(calculate_partner_discount(10_000), 5)

    def test_upper_bound_of_second_tier(self):
        self.assertEqual(calculate_partner_discount(49_999), 5)

    def test_second_threshold_exact(self):
        self.assertEqual(calculate_partner_discount(50_000), 10)

    def test_third_threshold_exact(self):
        self.assertEqual(calculate_partner_discount(300_000), 15)

    def test_above_third_threshold(self):
        self.assertEqual(calculate_partner_discount(500_000), 15)

    def test_zero_quantity(self):
        self.assertEqual(calculate_partner_discount(0), 0)

    def test_negative_quantity(self):
        self.assertEqual(calculate_partner_discount(-1), 0)


if __name__ == "__main__":
    unittest.main()