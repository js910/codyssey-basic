# 기본 조회 (4)
SELECT * FROM products WHERE price > 50000; # 5만원 이상 상품
SELECT * FROM products WHERE stock < 20; # 재고 20개 미만 상품
SELECT * FROM users ORDER BY username ASC; # 회원 이름순 정렬
SELECT * FROM users ORDER BY username LIMIT 5; # 회원 이름순 5개

# 조인
SELECT o.order_id, u.username FROM orders o JOIN users u ON o.user_id = u.user_id; # 주문자와 회원명
SELECT oi.order_id, p.product_name FROM order_items oi JOIN products p ON oi.product_id = p.product_id; # 주문 아이템과 상품명
SELECT u.username, o.order_id FROM users u LEFT JOIN orders o ON u.user_id = o.user_id; # 주문 없는 회원 포함 조회
SELECT u.username, p.product_name, oi.quantity FROM orders o JOIN users u ON o.user_id = u.user_id
JOIN order_items oi ON o.order_id = oi.order_id JOIN products p ON oi.product_id = p.product_id; # 상세 주문 내역 전체

# 집계 (3)
SELECT user_id, COUNT(*) as order_count FROM orders GROUP BY user_id; # 회원별 주문 횟수
SELECT product_id, SUM(quantity) as total_sold FROM order_items GROUP BY product_id; # 상품별 총 판매량
SELECT AVG(price) as avg_price FROM products; # 전체 상품 평균가

# 서브쿼리 (1)
SELECT username FROM users WHERE user_id IN (SELECT user_id FROM orders); # 주문 기록이 있는 회원

# 수정 및 삭제 (2)
UPDATE products SET stock = stock - 1 WHERE product_id = 1; # 재고 차감
DELETE FROM order_items WHERE order_item_id = 10; # 주문 아이템 삭제
SELECT * FROM products p LEFT JOIN order_items oi ON p.product_id = oi.product_id WHERE p.product_id = 1 OR oi.order_item_id = 10; # 확인

# 기타 (1)
SELECT product_name, price FROM products WHERE price = (SELECT MAX(price) FROM products); # 가장 비싼 상품