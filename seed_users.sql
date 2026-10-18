BEGIN TRANSACTION;

DELETE FROM "user";

-- Each test user has the same password, "hello1234"
INSERT INTO "user" (id, username, email, password_hash) VALUES 
(1, 'pekka', 'pekka@test.com', 'scrypt:32768:8:1$WcdgD5fYKaSb9pzG$3da626662426719a72e0b5bb65908e2c4ae9b2d6c86a249d4ac222cd62d1d586b446d471705d6f091f2b29a030e8e91216a105c8223f64c3612852c03afd422d'),
(2, 'matti', 'matti@test.com', 'scrypt:32768:8:1$WcdgD5fYKaSb9pzG$3da626662426719a72e0b5bb65908e2c4ae9b2d6c86a249d4ac222cd62d1d586b446d471705d6f091f2b29a030e8e91216a105c8223f64c3612852c03afd422d'),
(3, 'teppo', 'teppo@test.com', 'scrypt:32768:8:1$WcdgD5fYKaSb9pzG$3da626662426719a72e0b5bb65908e2c4ae9b2d6c86a249d4ac222cd62d1d586b446d471705d6f091f2b29a030e8e91216a105c8223f64c3612852c03afd422d');

COMMIT;
