-- SQL примеры транзакций (эквивалент ActiveRecord операций)

-- Сценарий 1: Размещение заказа с позициями

BEGIN;

  -- 1. Создание нового заказа
  INSERT INTO orders (customer_id, order_date, total_amount, created_at, updated_at)
  VALUES (1, NOW(), 0, NOW(), NOW())
  RETURNING id INTO @order_id;

  -- 2. Добавление позиций заказа с вычислением промежуточных итогов
  INSERT INTO order_items (order_id, product_id, quantity, subtotal, created_at, updated_at)
  VALUES (@order_id, 1, 1, 999.99, NOW(), NOW());

  INSERT INTO order_items (order_id, product_id, quantity, subtotal, created_at, updated_at)
  VALUES (@order_id, 2, 2, 59.98, NOW(), NOW());

  -- 3. Обновление общей суммы заказа (сумма всех промежуточных итогов)
  UPDATE orders
  SET total_amount = (
    SELECT SUM(subtotal) FROM order_items WHERE order_id = @order_id
  ),
  updated_at = NOW()
  WHERE id = @order_id;

COMMIT;

-- Сценарий 2: Обновление адреса электронной почты клиента

BEGIN;
  UPDATE customers
  SET email = 'john.doe@example.com',
      updated_at = NOW()
  WHERE id = 1;
COMMIT;

-- Сценарий 3: Добавление нового продукта

BEGIN;
  -- Добавление нового продукта с проверкой валидации
  INSERT INTO products (product_name, price, created_at, updated_at)
  VALUES ('Keyboard', 79.99, NOW(), NOW());
COMMIT;
=====================

-- Проверка заказа и его позиций
SELECT 
  o.id as order_id,
  c.first_name,
  c.last_name,
  o.order_date,
  o.total_amount,
  oi.quantity,
  p.product_name,
  p.price,
  oi.subtotal
FROM orders o
JOIN customers c ON o.customer_id = c.id
LEFT JOIN order_items oi ON o.id = oi.order_id
LEFT JOIN products p ON oi.product_id = p.id
WHERE o.id = 1;

-- Проверка, что сумма заказа соответствует сумме позиций
SELECT 
  o.id,
  o.total_amount as order_total,
  COALESCE(SUM(oi.subtotal), 0) as items_sum
FROM orders o
LEFT JOIN order_items oi ON o.id = oi.order_id
GROUP BY o.id
HAVING o.total_amount != COALESCE(SUM(oi.subtotal), 0);

-- Проверка уникальности email
SELECT email, COUNT(*) as count
FROM customers
GROUP BY email
HAVING COUNT(*) > 1;

BEGIN;
  INSERT INTO orders (customer_id, order_date, total_amount, created_at, updated_at)
  VALUES (9999, NOW(), 0, NOW(), NOW());
COMMIT;

BEGIN;
  UPDATE customers SET email = 'existing@example.com' WHERE id = 1;
COMMIT;

