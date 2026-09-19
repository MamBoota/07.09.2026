def calculate_partner_discount(total_quantity: int) -> int:
    """Возвращает процент скидки партнёра по суммарному объёму покупок."""
    if total_quantity < 10_000:
        return 0
    elif total_quantity < 50_000:
        return 5
    elif total_quantity < 300_000:
        return 10
    else:
        return 15
    