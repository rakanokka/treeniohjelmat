DROP TABLE IF EXISTS exercise_set;
DROP TABLE IF EXISTS exercise;
DROP TABLE IF EXISTS exercise_template;
DROP TABLE IF EXISTS workout_session;
DROP TABLE IF EXISTS workout_session_template;
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

CREATE TABLE workout_session_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
    workout_plan_id INTEGER, -- NULL if not part of a created plan
    description TEXT NOT NULL,
	created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plan(id) ON DELETE CASCADE
);

CREATE TABLE workout_session (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    template_id INTEGER,
    description TEXT NOT NULL,
    date TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES workout_session_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
    session_template_id INTEGER, -- NULL if not part of a created workout
    name TEXT NOT NULL,
    target_sets INTEGER NOT NULL,
    target_reps INTEGER NOT NULL,
    order_index INTEGER DEFAULT 0,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (session_template_id) REFERENCES workout_session_template(id) ON DELETE CASCADE
);

CREATE TABLE exercise (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_session_id INTEGER NOT NULL,
    template_id INTEGER,
    name TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (workout_session_id) REFERENCES workout_session(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES exercise_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_set (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL,
    set_number INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    weight REAL NOT NULL,
    FOREIGN KEY (exercise_id) REFERENCES exercise(id) ON DELETE CASCADE
);
