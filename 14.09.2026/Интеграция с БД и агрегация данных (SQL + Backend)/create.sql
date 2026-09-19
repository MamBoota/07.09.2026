SELECT
    p.id,
    p.name,
    p.email,
    COALESCE(SUM(s.quantity), 0) AS total_quantity
FROM partners p
LEFT JOIN sales_history s ON p.id = s.partner_id
WHERE p.id = ?
GROUP BY p.id, p.name, p.email;