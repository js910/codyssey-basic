INSERT INTO users (username, email) VALUES 
('Dev_Kim', 'kim@codyssey.com'), ('Coder_Lee', 'lee@codyssey.com'), ('Hacker_Park', 'park@codyssey.com'), 
('User_IU', 'iu@codyssey.com'), ('Dev_Gong', 'gong@codyssey.com'), ('Coder_Ko', 'ko@codyssey.com'), 
('Hacker_Lee', 'hlee@codyssey.com'), ('User_Yoo', 'yoo@codyssey.com'), ('Dev_Nam', 'nam@codyssey.com'), ('User_Suzy', 'suzy@codyssey.com');

INSERT INTO products (product_name, price, stock) VALUES 
('Mechanical Keyboard', 120000, 10), ('Gaming Mouse', 30000, 50), ('4K Monitor', 300000, 20), 
('USB-C Hub', 25000, 100), ('Headset', 150000, 15), ('Webcam', 70000, 10), 
('Mouse Pad', 10000, 200), ('Speaker', 50000, 40), ('Laptop Stand', 40000, 25), ('Cable Organizer', 5000, 300);

INSERT INTO orders (user_id) VALUES (1), (2), (3), (4), (5), (6), (7), (8), (9), (10);

INSERT INTO order_items (order_id, product_id, quantity) VALUES 
(1, 1, 1), (2, 2, 2), (3, 3, 1), (4, 4, 1), (5, 5, 1), (6, 6, 1), (7, 7, 3), (8, 8, 1), (9, 9, 2), (10, 10, 5);

select * from users;