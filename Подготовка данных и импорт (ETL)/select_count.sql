-- Проверка количества партнёров (должно быть 4)
SELECT COUNT(*) AS partners_count FROM partners;

-- Проверка количества товаров (должно быть 3, если добавляли из sales)
SELECT COUNT(*) AS products_count FROM products;

-- Проверка количества отгрузок/продаж (должно быть 5)
SELECT COUNT(*) AS deliveries_count FROM deliveries;

-- Проверка количества позиций в отгрузках (должно быть 5)
SELECT COUNT(*) AS items_count FROM delivery_items;