# 보너스: JOIN vs SUBQUERY
SELECT DISTINCT u.username, u.email FROM users u JOIN orders o ON u.user_id = o.user_id; # 합치고 필터링 (중복)
SELECT username, email FROM users WHERE user_id IN (SELECT user_id FROM orders); #필터링해 넣기

# 정합성 깨기
INSERT INTO orders (user_id, order_date) VALUES (999, NOW());

# 미니 리포트: 상품별 판매량
SELECT p.product_name, SUM(oi.quantity) AS total_sold
FROM order_items oi
JOIN products p ON oi.product_id = p.product_id
GROUP BY p.product_id
ORDER BY total_sold DESC
LIMIT 10;

# 미니 리포트: 회원별 주문금액
SELECT u.username, SUM(oi.quantity * p.price) AS total_spent
FROM users u
JOIN orders o ON u.user_id = o.user_id
JOIN order_items oi ON o.order_id = oi.order_id
JOIN products p ON oi.product_id = p.product_id
GROUP BY u.user_id
ORDER BY total_spent DESC;

# 미니 리포트: 월별 주문 건수
SELECT DATE_FORMAT(order_date, '%Y-%m') AS order_month, COUNT(order_id) AS order_count
FROM orders
GROUP BY order_month
ORDER BY order_month ASC;