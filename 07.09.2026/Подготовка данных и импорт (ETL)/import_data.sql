-- ============================================================
-- import_data.sql — Импорт очищенных данных
-- ============================================================

-- 1. Импортируем партнёров (сначала их, так как на них ссылаются продажи)
INSERT INTO partners (id, company_name, inn, contact_email, phone, rating) VALUES
(1, 'ООО "Логистик-Экспресс"', '7701234567', 'info@logex.ru', '+7 (999) 111-22-33', 4.8),
(2, 'ИП Петров А.В.', '5001098765', 'petrov_delivery@mail.ru', NULL, 4.2),
(3, 'ТК "Быстрый Путь"', '7812345678', 'speedway@yandex.ru', '+78125554433', NULL),
(4, 'Неизвестный партнер', '0000000000', 'unknown@mail.ru', NULL, 0.0);

-- Сбрасываем счётчик автоинкремента, чтобы следующие записи шли с id=5
ALTER TABLE partners AUTO_INCREMENT = 5;

-- 2. Импортируем товары (если их ещё нет в базе)
-- В sales.txt есть 3 уникальных товара. Добавим их в products.
INSERT INTO products (sku, name, description, unit_price) VALUES
('SKU-101', 'Стиральный порошок "Альфа"', 'Бытовая химия', 500.00),
('SKU-102', 'Мыло жидкое "Стандарт"', 'Бытовая химия', 90.00),
('SKU-103', 'Кондиционер для белья', 'Бытовая химия', 350.00);

-- 3. Импортируем продажи (в таблицу deliveries)
-- sale_id маппим в id, sale_date в delivery_date, статус ставим 'delivered'
INSERT INTO deliveries (id, partner_id, delivery_date, status, notes) VALUES
(101, 1, '2026-03-01', 'delivered', 'Импорт из sales.txt'),
(102, 2, '2026-03-15', 'delivered', 'Импорт из sales.txt (дата исправлена)'),
(103, 1, '2026-03-20', 'delivered', 'Импорт из sales.txt'),
(104, 4, '2026-03-22', 'delivered', 'Импорт из sales.txt (партнер добавлен)'),
(105, 3, '2026-03-25', 'delivered', 'Импорт из sales.txt');

ALTER TABLE deliveries AUTO_INCREMENT = 106;

-- 4. Импортируем позиции продаж (в таблицу delivery_items)
INSERT INTO delivery_items (delivery_id, product_id, quantity, unit_price) VALUES
(101, 1, 50, 500.00),   -- Стиральный порошок
(102, 2, 200, 90.00),   -- Мыло жидкое
(103, 3, 30, 350.00),   -- Кондиционер
(104, 1, 10, 500.00),   -- Стиральный порошок
(105, 2, 150, 90.00);   -- Мыло жидкое