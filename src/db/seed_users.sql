BEGIN TRANSACTION;

DELETE FROM "user";

-- Each test user has the same password, "hello"
INSERT INTO "user" (username, email, password_hash) VALUES 
('pekka', 'pekka@test.com', 'scrypt:32768:8:1$4ivJstmyATeYShqf$c73443bdcb67035b390ac7faec21478b7c41df1e67c3bd4a894edbd6e9c2c60d627fdd4f96b572cd802b845bd955b1e57e24ef1fed3931e919b0aca00a2548eb'),
('matti', 'matti@test.com', 'scrypt:32768:8:1$4ivJstmyATeYShqf$c73443bdcb67035b390ac7faec21478b7c41df1e67c3bd4a894edbd6e9c2c60d627fdd4f96b572cd802b845bd955b1e57e24ef1fed3931e919b0aca00a2548eb'),
('teppo', 'teppo@test.com', 'scrypt:32768:8:1$4ivJstmyATeYShqf$c73443bdcb67035b390ac7faec21478b7c41df1e67c3bd4a894edbd6e9c2c60d627fdd4f96b572cd802b845bd955b1e57e24ef1fed3931e919b0aca00a2548eb');

COMMIT;
