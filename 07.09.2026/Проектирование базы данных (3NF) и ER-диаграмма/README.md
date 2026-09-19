1. Выделенные сущности (4 штуки)
#,Таблица,Назначение
1,partners,Справочник партнёров (контрагентов)
2,products,Справочник товаров
3,deliveries,Факт отгрузки (шапка)
4,delivery_items,Позиции внутри отгрузки (связь M:N deliveries ↔ products)

Четыре таблицы — потому что отгрузка и товар связаны «многие-ко-многим», и без связующей таблицы нарушается 1NF (повторяющиеся группы).

2. Атрибуты и ограничения
partners
Столбец,Тип,Ограничения
id,INT,PK", AUTO_INCREMENT"
inn,VARCHAR(12),NOT NULL", "UNIQUE
company_name,VARCHAR(255),NOT NULL
contact_person,VARCHAR(255),—
email,VARCHAR(255),NOT NULL", "UNIQUE
phone,VARCHAR(20),—
address,TEXT,—
created_at,TIMESTAMP,DEFAULT CURRENT_TIMESTAMP
updated_at,TIMESTAMP,DEFAULT CURRENT_TIMESTAMP ON UPDATE

productsСтолбец,Тип,Ограничения
id,INT,PK", AUTO_INCREMENT"
sku,VARCHAR(50),NOT NULL", "UNIQUE
name,VARCHAR(255),NOT NULL
description,TEXT,—
unit_price,"DECIMAL(12,2)",NOT NULL
created_at,TIMESTAMP,DEFAULT CURRENT_TIMESTAMP

deliveries
Столбец,Тип,Ограничения
id,INT,PK", AUTO_INCREMENT"
partner_id,INT,NOT NULL", "FK → partners(id)
delivery_date,DATE,NOT NULL
status,VARCHAR(50),NOT NULL" (CHECK: 'pending','shipped','delivered','cancelled')"
notes,TEXT,—
created_at,TIMESTAMP,DEFAULT CURRENT_TIMESTAMP

delivery_items
Столбец,Тип,Ограничения
delivery_id,INT,PK (часть)", "FK → deliveries(id)
product_id,INT,PK (часть)", "FK → products(id)
quantity,INT,NOT NULL", CHECK > 0"
unit_price,"DECIMAL(12,2)",NOT NULL (цена на момент отгрузки)

3. Обоснование 3NF
НФ,Условие,Проверка
1NF,"Атомарные значения, нет повторяющихся групп",Каждый столбец — скаляр; позиции отгрузки вынесены в delivery_items ✓
2NF,Нет частичных зависимостей от составного PK,В delivery_items" составной PK (delivery_id, product_id); "quantity и unit_price зависят от обоих ключей (конкретная позиция конкретной отгрузки) ✓. Остальные таблицы имеют суррогатный PK — 2NF автоматически ✓
3NF,Нет транзитивных зависимостей,В partners: email", "inn", "company_name зависят напрямую от id", не друг от друга ✓. В "deliveries: partner_id" — это FK, но "status", "delivery_date зависят от id" отгрузки, а не от атрибутов партнёра ✓"
