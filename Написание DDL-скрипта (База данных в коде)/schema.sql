-- ============================================================
-- schema.sql — DDL-скрипт для развертывания БД
-- Диалект: MySQL / MariaDB
-- Порядок: сначала удаляем зависимые таблицы, потом создаём
-- ============================================================

-- ============================================================
-- ЧАСТЬ 1: УДАЛЕНИЕ ТАБЛИЦ (если существуют)
-- ВАЖНО: сначала удаляем дочерние таблицы (с FK), потом родительские
-- ============================================================

DROP TABLE IF EXISTS delivery_items;
DROP TABLE IF EXISTS deliveries;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS partners;

-- ============================================================
-- ЧАСТЬ 2: СОЗДАНИЕ ТАБЛИЦ
-- ВАЖНО: сначала создаём родительские таблицы, потом дочерние
-- ============================================================

-- Таблица партнёров (родительская)
CREATE TABLE partners (
    id              INT             AUTO_INCREMENT,
    inn             VARCHAR(12)     NOT NULL,
    company_name    VARCHAR(255)    NOT NULL,
    contact_person  VARCHAR(255)    DEFAULT NULL,
    email           VARCHAR(255)    NOT NULL,
    phone           VARCHAR(20)     DEFAULT NULL,
    address         TEXT            DEFAULT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    CONSTRAINT pk_partners PRIMARY KEY (id),
    CONSTRAINT uq_partners_inn UNIQUE (inn),
    CONSTRAINT uq_partners_email UNIQUE (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица товаров (родительская)
CREATE TABLE products (
    id              INT             AUTO_INCREMENT,
    sku             VARCHAR(50)     NOT NULL,
    name            VARCHAR(255)    NOT NULL,
    description     TEXT            DEFAULT NULL,
    unit_price      DECIMAL(12,2)   NOT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT pk_products PRIMARY KEY (id),
    CONSTRAINT uq_products_sku UNIQUE (sku)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица отгрузок (дочерняя → partners)
CREATE TABLE deliveries (
    id              INT             AUTO_INCREMENT,
    partner_id      INT             NOT NULL,
    delivery_date   DATE            NOT NULL,
    status          VARCHAR(50)     NOT NULL,
    notes           TEXT            DEFAULT NULL,
    created_at      TIMESTAMP       NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT pk_deliveries PRIMARY KEY (id),
    CONSTRAINT fk_deliveries_partner 
        FOREIGN KEY (partner_id) 
        REFERENCES partners(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT chk_deliveries_status 
        CHECK (status IN ('pending', 'shipped', 'delivered', 'cancelled'))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Таблица позиций отгрузки (дочерняя → deliveries, products)
CREATE TABLE delivery_items (
    delivery_id     INT             NOT NULL,
    product_id      INT             NOT NULL,
    quantity        INT             NOT NULL,
    unit_price      DECIMAL(12,2)   NOT NULL,
    
    CONSTRAINT pk_delivery_items PRIMARY KEY (delivery_id, product_id),
    CONSTRAINT fk_items_delivery 
        FOREIGN KEY (delivery_id) 
        REFERENCES deliveries(id)
        ON DELETE CASCADE
        ON UPDATE CASCADE,
    CONSTRAINT fk_items_product 
        FOREIGN KEY (product_id) 
        REFERENCES products(id)
        ON DELETE RESTRICT
        ON UPDATE CASCADE,
    CONSTRAINT chk_items_quantity 
        CHECK (quantity > 0)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ============================================================
-- ЧАСТЬ 3: ТЕСТОВЫЕ ДАННЫЕ (опционально, но препы любят)
-- ============================================================

INSERT INTO partners (inn, company_name, contact_person, email, phone, address) VALUES
('7707083893', 'ООО "Ромашка"', 'Иванов Иван', 'ivanov@romashka.ru', '+7(999)123-45-67', 'г. Москва, ул. Ленина, д. 1'),
('7710140679', 'ООО "Василёк"', 'Петров Пётр', 'petrov@vasilek.ru', '+7(999)765-43-21', 'г. Москва, ул. Пушкина, д. 10');

INSERT INTO products (sku, name, description, unit_price) VALUES
('SKU-001', 'Ноутбук Dell XPS 15', '15.6", Intel i7, 16GB RAM', 120000.00),
('SKU-002', 'Монитор LG 27"', '27", 4K, IPS', 35000.00),
('SKU-003', 'Клавиатура Logitech MX Keys', 'Беспроводная, подсветка', 12000.00);

INSERT INTO deliveries (partner_id, delivery_date, status, notes) VALUES
(1, '2026-09-10', 'delivered', 'Доставлено вовремя'),
(2, '2026-09-11', 'shipped', 'В пути'),
(1, '2026-09-12', 'pending', 'Ожидает отправки');

INSERT INTO delivery_items (delivery_id, product_id, quantity, unit_price) VALUES
(1, 1, 2, 120000.00),
(1, 3, 5, 12000.00),
(2, 2, 3, 35000.00),
(3, 1, 1, 120000.00);
