BEGIN TRANSACTION;

DELETE FROM exercise_set;
DELETE FROM exercise_log;
DELETE FROM exercise_template;
DELETE FROM workout_log;
DELETE FROM workout_template;
DELETE FROM workout_plan;

-- NOTE: user_ids 1, 2, 3 must exist in the user table when this script is executed

-- To create a workout the creator must create a blueprint/template for it. 
-- Then other users (including the creator) may add workouts based on the template
-- If the template is not part of a workout plan, the workout_plan_id is set to NULL 
INSERT INTO workout_template (creator_id, workout_plan_id, description) VALUES 
(1, NULL, 'Rintatreeni A'),      -- session_template_id = 1
(2, NULL, 'Jalkapäivä Volyymi'); -- session_template_id = 2

-- These are the actual workouts that users track through the app
INSERT INTO workout_log (user_id, workout_template_id, description, date, notes) VALUES 
(1, 1, 'Rintatreeni A', '2026-09-10', 'Viimeinen sarja tiukka'),                       -- workout_id = 1
(1, 2, 'Jalkapäivä Volyymi', '2026-09-12', 'Testattiin Pekan jalkatreeniä, hapotti!'), -- workout_id = 2
(2, 2, 'Jalkapäivä Volyymi', '2026-09-11', 'Perustreeni kulki hyvin');                 -- workout_id = 3

-- Users may create stand-alone exercises, without adding them to an existing workout template.
-- For these inserts the workout_template_id is set to NULL 
INSERT INTO exercise_template (creator_id, workout_template_id, name, target_sets, target_reps, order_index) VALUES 
(1, NULL, 'Penkkipunnerrus', 3, 10, 1),       -- exercise_template_id = 1
(1, 1, 'Vinopenkki käsipainoilla', 3, 12, 2), -- exercise_template_id = 2
(1, NULL, 'Ristikkäistalja', 4, 15, 0),       -- exercise_template_id = 3
(2, 2, 'Kyykky', 4, 8, 1),                    -- exercise_template_id = 4
(2, 2, 'Reidenojennus', 3, 12, 2),            -- exercise_template_id = 5
(2, NULL, 'Sjtm maastaveto', 3, 10, 0),       -- exercise_template_id = 6
(3, NULL, 'Leuanveto', 3, 8, 0),              -- exercise_template_id = 7
(3, NULL, 'Pystypunnerrus', 3, 10, 0);        -- exercise_template_id = 8

-- These are the actual exercises that users add to their workouts
INSERT INTO exercise_log (workout_id, exercise_template_id, name, notes) VALUES 
(1, 1, 'Penkkipunnerrus', 'Viimeisessä sarjassa tiukka 10.'), -- exercise_id = 1
(1, 2, 'Vinopenkki käsipainoilla', 'Kevyt paino'),            -- exercise_id = 2
(2, 4, 'Kyykky', 'Syvältä ja puhtaasti'),                     -- exercise_id = 3
(3, 4, 'Kyykky', 'Ennätyspainot!'),                           -- exercise_id = 4
(3, 5, 'Reidenojennus', 'Hapotus loppuun');                   -- exercise_id = 5

INSERT INTO exercise_set (exercise_id, set_number, reps, weight) VALUES 
(1, 1, 10, 80.0),
(1, 2, 10, 80.0),
(1, 3, 10, 80.0),
(2, 1, 12, 28.0),
(2, 2, 12, 28.0),
(3, 1, 8, 100.0),
(3, 2, 8, 100.0),
(3, 3, 8, 100.0),
(4, 1, 8, 120.0),
(4, 2, 8, 125.0),
(4, 3, 8, 130.0),
(4, 4, 6, 135.0),
(5, 1, 12, 60.0),
(5, 2, 12, 65.0),
(5, 3, 12, 65.0);

COMMIT;
