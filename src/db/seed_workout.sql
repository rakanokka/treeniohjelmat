DELETE FROM exercise_set;
DELETE FROM exercise;
DELETE FROM exercise_template;
DELETE FROM workout_session;
DELETE FROM workout_session_template;
DELETE FROM workout_plan;

-- NOTE: user_id = 1 must exist in the user table when this script is run

-- When a workout or exercise is created, the creator must create a template for it. 
-- Then other users (including the creator) may add workouts or exercises using the existing template
INSERT INTO workout_session_template (creator_id, workout_plan_id, description) VALUES 
(1, NULL, 'Rintatreeni'); -- session_template_id = 1

INSERT INTO exercise_template (creator_id, session_template_id, name, target_sets, target_reps, order_index) VALUES 
(1, NULL, 'Penkkipunnerrus', 3, 10, 1); -- exercise_template_id = 1

INSERT INTO exercise (workout_session_id, template_id, name, notes) VALUES 
(1, 1, 'Penkkipunnerrus', 'Viimeisessä sarjassa tiukka 10.'); -- exercise_id = 1

INSERT INTO exercise_set (exercise_id, set_number, reps, weight) VALUES 
(1, 1, 10, 80.0);
(1, 2, 10, 80.0);
(1, 3, 10, 80.0);
