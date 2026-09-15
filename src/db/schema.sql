DROP TABLE IF EXISTS exercise_set;
DROP TABLE IF EXISTS exercise_log;
DROP TABLE IF EXISTS user_exercise_template;
DROP TABLE IF EXISTS workout_exercise_template;
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
    name TEXT NOT NULL,
	description TEXT,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plan(id) ON DELETE CASCADE
);

CREATE TABLE workout_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    workout_template_id INTEGER,
    name TEXT NOT NULL,
	notes TEXT,
	started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,	
	ended_at TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
    name TEXT NOT NULL,
	category TEXT,
    target_sets INTEGER NOT NULL CHECK(target_sets >= 0),
    target_reps INTEGER NOT NULL CHECK(target_reps >= 0),
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE workout_exercise_template (
    workout_template_id INTEGER NOT NULL,
    exercise_template_id INTEGER NOT NULL,
    order_index INTEGER DEFAULT 0 CHECK(order_index >= 0),
    PRIMARY KEY (workout_template_id, exercise_template_id),
    FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_template_id) REFERENCES exercise_template(id) ON DELETE CASCADE
);

CREATE TABLE user_exercise_template (
    user_id INTEGER NOT NULL,
    exercise_template_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, exercise_template_id),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_template_id) REFERENCES exercise_template(id) ON DELETE CASCADE
);

CREATE TABLE exercise_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_id INTEGER NOT NULL,
    exercise_template_id INTEGER,
    name TEXT NOT NULL,
	notes TEXT,
    FOREIGN KEY (workout_id) REFERENCES workout_log(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_template_id) REFERENCES exercise_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_set (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL,
    order_index INTEGER DEFAULT 0 CHECK(order_index >= 0),
    reps INTEGER NOT NULL CHECK(reps >= 0),
    weight REAL NOT NULL CHECK(weight >= 0),
    FOREIGN KEY (exercise_id) REFERENCES exercise_log(id) ON DELETE CASCADE
);
