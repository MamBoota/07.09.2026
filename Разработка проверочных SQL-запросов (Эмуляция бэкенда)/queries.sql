-- ============================================================
-- queries.sql — Проверочные SQL-запросы (Эмуляция бэкенда)
-- Диалект: MySQL
-- ============================================================

-- ============================================================
-- ЗАПРОС 1: Список партнеров с сортировкой по названию и 
-- общим количеством сделанных ими доставок.
-- Используем LEFT JOIN, чтобы вывести даже тех партнеров, 
-- у которых пока 0 доставок.
-- ============================================================

SELECT 
    p.id AS partner_id,
    p.company_name,
    p.inn,
    COUNT(d.id) AS total_deliveries
FROM partners p
LEFT JOIN deliveries d ON p.id = d.partner_id
GROUP BY p.id, p.company_name, p.inn
ORDER BY p.company_name ASC;


-- ============================================================
-- ЗАПРОС 2: Демонстрация транзакции.
-- Создание нового партнера и запись о его первой тестовой 
-- доставке в рамках одного блока BEGIN...COMMIT.
-- Если на любом шаге возникнет ошибка, транзакция откатится (ROLLBACK).
-- ============================================================

START TRANSACTION;

-- 1. Создаем нового партнера
INSERT INTO partners (company_name, inn, email, phone, address) 
VALUES ('ООО "Тестовый Партнер"', '9900000000', 'test@example.com', '+70000000000', 'г. Тестовск, ул. Тестовая, 1');

-- Запоминаем ID только что созданного партнера (функция MySQL)
SET @new_partner_id = LAST_INSERT_ID();

-- 2. Создаем отгрузку (доставку) для этого партнера
INSERT INTO deliveries (partner_id, delivery_date, status, notes) 
VALUES (@new_partner_id, '2026-09-11', 'pending', 'Тестовая доставка из транзакции');

-- Запоминаем ID созданной отгрузки
SET @new_delivery_id = LAST_INSERT_ID();

-- 3. Добавляем товар в эту отгрузку (например, товар с id = 1)
INSERT INTO delivery_items (delivery_id, product_id, quantity, unit_price) 
VALUES (@new_delivery_id, 1, 10, 120000.00);

-- Подтверждаем все изменения
COMMIT;


-- ============================================================
-- ЗАПРОС 3: Детальная история отгрузок конкретного партнера 
-- за указанный период.
-- Вывод: названия продуктов, даты, объемы в штуках и 
-- итоговая сумма по каждой позиции поставки.
-- ============================================================

SELECT 
    d.id AS delivery_id,
    d.delivery_date,
    pr.name AS product_name,
    di.quantity,
    di.unit_price,
    (di.quantity * di.unit_price) AS line_total_sum
FROM deliveries d
INNER JOIN delivery_items di ON d.id = di.delivery_id
INNER JOIN products pr ON di.product_id = pr.id
WHERE d.partner_id = 1 -- ID конкретного партнера (можно заменить на любой)
  AND d.delivery_date BETWEEN '2026-03-01' AND '2026-03-31' -- Указанный период
ORDER BY d.delivery_date DESC, d.id DESC;