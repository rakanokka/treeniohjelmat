DROP TABLE IF EXISTS user_comment;
DROP TABLE IF EXISTS workout_template_tag;
DROP TABLE IF EXISTS tag;
DROP TABLE IF EXISTS exercise_set;
DROP TABLE IF EXISTS exercise_log;
DROP TABLE IF EXISTS user_exercise_template;
DROP TABLE IF EXISTS workout_exercise_template;
DROP TABLE IF EXISTS exercise_template;
DROP TABLE IF EXISTS user_workout_template;
DROP TABLE IF EXISTS workout_log;
DROP TABLE IF EXISTS workout_template;
DROP TABLE IF EXISTS workout_plan;
DROP TABLE IF EXISTS "user";

CREATE TABLE "user" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL CHECK(trim(username) != ''),
    email TEXT UNIQUE NOT NULL CHECK(trim(email) != ''),
    password_hash TEXT NOT NULL CHECK(password_hash != ''),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE workout_plan (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
	name TEXT NOT NULL CHECK(trim(name) != ''),
	description TEXT,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE workout_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
    workout_plan_id INTEGER, -- NULL if not part of a workout plan
    name TEXT NOT NULL CHECK(trim(name) != ''),
	description TEXT,
	created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_plan_id) REFERENCES workout_plan(id) ON DELETE CASCADE
);

CREATE TABLE user_workout_template (
    user_id INTEGER NOT NULL,
    workout_template_id INTEGER NOT NULL,
    PRIMARY KEY (user_id, workout_template_id),
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE CASCADE
);

CREATE TABLE workout_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    workout_template_id INTEGER,
    name TEXT NOT NULL CHECK(trim(name) != ''),
	notes TEXT,
	started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
	ended_at TIMESTAMP,
	FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_template (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
	creator_id INTEGER NOT NULL,
    name TEXT NOT NULL CHECK(trim(name) != ''),
	category TEXT,
    target_sets INTEGER NOT NULL CHECK(target_sets >= 0),
    target_reps INTEGER NOT NULL CHECK(target_reps >= 0),
	FOREIGN KEY (creator_id) REFERENCES "user"(id) ON DELETE CASCADE
);

CREATE TABLE workout_exercise_template (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	workout_template_id INTEGER NOT NULL,
    exercise_template_id INTEGER NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0 CHECK(order_index >= 0),
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
    name TEXT NOT NULL CHECK(trim(name) != ''),
	notes TEXT,
    FOREIGN KEY (workout_id) REFERENCES workout_log(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_template_id) REFERENCES exercise_template(id) ON DELETE SET NULL
);

CREATE TABLE exercise_set (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    exercise_id INTEGER NOT NULL,
    order_index INTEGER NOT NULL DEFAULT 0 CHECK(order_index >= 0),
    reps INTEGER NOT NULL CHECK(reps >= 0),
    weight REAL NOT NULL CHECK(weight >= 0),
    FOREIGN KEY (exercise_id) REFERENCES exercise_log(id) ON DELETE CASCADE
);

CREATE TABLE tag (
	id INTEGER PRIMARY KEY AUTOINCREMENT,
	name TEXT UNIQUE NOT NULL CHECK(trim(name) != '')
);

CREATE TABLE workout_template_tag (
	workout_template_id INTEGER NOT NULL,
	tag_id INTEGER NOT NULL,
	PRIMARY KEY (workout_template_id, tag_id),
	FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE CASCADE,
	FOREIGN KEY (tag_id) REFERENCES tag(id) ON DELETE CASCADE
);

CREATE TABLE user_comment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL CHECK(trim(content) != ''),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    workout_template_id INTEGER,
    exercise_template_id INTEGER,
    FOREIGN KEY (user_id) REFERENCES "user"(id) ON DELETE CASCADE,
    FOREIGN KEY (workout_template_id) REFERENCES workout_template(id) ON DELETE CASCADE,
    FOREIGN KEY (exercise_template_id) REFERENCES exercise_template(id) ON DELETE CASCADE,
	CHECK (
		(CASE WHEN workout_template_id IS NOT NULL THEN 1 ELSE 0 END +
		CASE WHEN exercise_template_id IS NOT NULL THEN 1 ELSE 0 END) = 1
	)	
);
