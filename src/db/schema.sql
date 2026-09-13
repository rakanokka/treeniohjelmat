DROP TABLE IF EXISTS exercise_set;
DROP TABLE IF EXISTS exercise_log;
DROP TABLE IF EXISTS user_exercise_template;
DROP TABLE IF EXISTS exercise_template;
DROP TABLE IF EXISTS workout_log;
DROP TABLE IF EXISTS workout_template;
DROP TABLE IF EXISTS workout_plan;
DROP TABLE IF EXISTS "user";

CREATE TABLE "user" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workout_plan (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	name TEXT NOT NULL,
	description TEXT,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE workout_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
    workout_plan_id INTEGER, -- NULL if not part of a workout plan
    description TEXT NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plan(id) ON DELETE CASCADE
);

CREATE TABLE workout_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    workout_template_id INTEGER, -- NULL if the template is deleted
    description TEXT NOT NULL,
    date TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
    workout_template_id INTEGER, -- NULL if not part of a workout
    name TEXT NOT NULL,
    target_sets INTEGER NOT NULL,
    target_reps INTEGER NOT NULL,
    order_index INTEGER DEFAULT 0,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS user_exercise_template (
    user_id INTEGER NOT NULL,
    exercise_template_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, exercise_template_id),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_template_id) REFERENCES exercise_template(id) ON DELETE CASCADE
);

CREATE TABLE exercise_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    exercise_template_id INTEGER, -- NULL if the template is deleted
    name TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (workout_id) REFERENCES workout_log(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_template_id) REFERENCES exercise_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_set (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    FOREIGN KEY (exercise_id) REFERENCES exercise(id) ON DELETE CASCADE
);
