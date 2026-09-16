BEGIN TRANSACTION;

DELETE FROM exercise_set;
DELETE FROM exercise_log;
DELETE FROM exercise_template;
DELETE FROM workout_log;
DELETE FROM workout_template;
DELETE FROM workout_plan;

-- NOTE: user_ids 1, 2, 3 must exist in the user table when this script is executed
-- To start with a clean slate, first run seed_users.sql and then run seed_workouts.sql

INSERT INTO workout_template (creator_id, workout_plan_id, name) VALUES 
(1, NULL, 'Rintatreeni A'),
(2, NULL, 'Jalkapäivä Volyymi');

INSERT INTO workout_log (user_id, workout_template_id, name, notes, started_at, ended_at) VALUES 
(1, 1, 'Rintatreeni A', 'Viimeinen sarja tiukka', '2026-09-10 10:00:00', '2026-09-10 11:15:00'),
(1, 2, 'Jalkapäivä Volyymi', 'Testattiin Pekan jalkatreeniä, hapotti!', '2026-09-12 14:30:00', '2026-09-12 16:00:00'),
(2, 2, 'Jalkapäivä Volyymi', 'Perustreeni kulki hyvin', '2026-09-11 18:00:00', '2026-09-11 19:10:00');

INSERT INTO exercise_template (id, creator_id, name, category, target_sets, target_reps) VALUES 
(1, 1, 'Penkkipunnerrus', 'Rinta', 3, 10),
(2, 1, 'Vinopenkki käsipainoilla', 'Rinta', 3, 12),
(3, 1, 'Ristikkäistalja', 'Rinta', 4, 15),
(4, 2, 'Kyykky', 'Jalat', 4, 8),
(5, 2, 'Reidenojennus', 'Jalat', 3, 12),
(6, 2, 'Sjtm maastaveto', 'Jalat', 3, 10),
(7, 3, 'Leuanveto', 'Selkä', 3, 8),
(8, 3, 'Pystypunnerrus', 'Olkapäät', 3, 10);

INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES 
(1, 2, 0),
(2, 4, 0),
(2, 5, 1);

INSERT INTO exercise_log (workout_id, exercise_template_id, name, notes) VALUES 
(1, 1, 'Penkkipunnerrus', 'Viimeisessä sarjassa tiukka 10.'),
(1, 2, 'Vinopenkki käsipainoilla', 'Kevyt paino'),
(2, 4, 'Kyykky', 'Syvältä ja puhtaasti'),
(3, 4, 'Kyykky', 'Ennätyspainot!'),
(3, 5, 'Reidenojennus', 'Hapotus loppuun');

INSERT INTO exercise_set (exercise_id, order_index, reps, weight) VALUES 
(1, 0, 10, 80.0),
(1, 1, 10, 80.0),
(1, 2, 10, 80.0),
(2, 0, 12, 28.0),
(2, 1, 12, 28.0),
(3, 0, 8, 100.0),
(3, 1, 8, 100.0),
(3, 2, 8, 100.0),
(4, 0, 8, 120.0),
(4, 1, 8, 125.0),
(4, 2, 8, 130.0),
(4, 3, 6, 135.0),
(5, 0, 12, 60.0),
(5, 1, 12, 65.0),
(5, 2, 12, 65.0);

COMMIT;
