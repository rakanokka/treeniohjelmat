import database
from werkzeug.security import check_password_hash, generate_password_hash

def add_user(username: str, email: str, password: str) -> bool:
    try:
        pw_hash = generate_password_hash(password)
        sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
        database.execute(sql, [username.strip(), email.strip(), pw_hash])
    except Exception as e:
        print(e)
        return False
    return True

def get_user(user_id: int) -> dict | None:
    sql = 'SELECT id, username, password_hash FROM "user" WHERE id = ?'
    r = database.query(sql, [user_id])
    return r[0] if r else None

def get_auth_user_id(username: str, password: str) -> int:
    sql = 'SELECT id, password_hash FROM "user" WHERE username = ?'
    r = database.query(sql, [username.strip()])
    if r:
        pw_hash = r[0]["password_hash"]
        if check_password_hash(pw_hash, password.strip()):
            return int(r[0]["id"])
    return -1

def get_other_users(user_id: int) -> list[dict]:
    sql = 'SELECT id, username FROM "user" WHERE id <> ?'
    return database.query(sql, [user_id])

def get_user_profile_info(user_id: int) -> dict | None:
    sql = """
    SELECT 
        u.username AS username,
        (SELECT COUNT(*) FROM workout_template WHERE creator_id = u.id) AS created_templates_count,
        (SELECT COUNT(*) FROM user_workout_template WHERE user_id = u.id) AS adopted_templates_count,
        (SELECT COUNT(*) FROM exercise_template WHERE creator_id = u.id) AS created_exercises_count,
        (SELECT COUNT(*) FROM user_exercise_template WHERE user_id = u.id) AS adopted_exercises_count,
        (SELECT COUNT(*) FROM workout_log WHERE user_id = u.id) AS completed_workouts_count,
        (SELECT COUNT(*) 
         FROM exercise_log e
         JOIN workout_log w 
            ON e.workout_id = w.id
         WHERE w.user_id = u.id) AS completed_exercises_count
    FROM "user" u
    WHERE u.id = ?
    """
    r = database.query(sql, [user_id])
    return r[0] if r else None

def get_favourite_exercise_categories(user_id: int, limit = 5) -> list[dict]:
    sql = """
    SELECT 
        et.category AS category_name,
        COUNT(DISTINCT CASE 
            WHEN wt.creator_id = ? THEN wet.id 
            ELSE NULL 
        END) AS templates_usage_count,
        COUNT(DISTINCT CASE 
            WHEN et.creator_id = ? THEN et.id 
            ELSE NULL 
        END) AS created_exercises_count
    FROM exercise_template et
    LEFT JOIN workout_exercise_template wet 
        ON et.id = wet.exercise_template_id
    LEFT JOIN workout_template wt 
        ON wet.workout_template_id = wt.id
    WHERE wt.creator_id = ? OR et.creator_id = ?
    GROUP BY et.category
    ORDER BY templates_usage_count DESC, created_exercises_count DESC 
    LIMIT ?
    """
    return database.query(sql, [user_id, user_id, user_id, user_id, limit])

def get_workout_templates_usage_count(user_id: int, limit = 5) -> list[dict]:
    sql = """
    SELECT 
        wt.id,
        wt.name,
        wt.description,
        wt.created_at,
        COUNT(DISTINCT uwt.user_id) AS adopted_by_others_count,
        COUNT(DISTINCT wet.id) AS exercise_count
    FROM workout_template wt
    LEFT JOIN user_workout_template uwt 
        ON wt.id = uwt.workout_template_id
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    WHERE wt.creator_id = ?
    GROUP BY wt.id
    ORDER BY adopted_by_others_count DESC, wt.created_at DESC
    LIMIT ?
    """
    return database.query(sql, [user_id, limit])

def get_recent_workouts(user_id: int, limit: int = 5) -> list[dict]:
    sql = """
    SELECT 
        w.id AS workout_id,
        w.started_at AS date,
        w.name AS workout_name,
        CAST(
            ROUND((JULIANDAY(w.ended_at) - JULIANDAY(w.started_at)) * 86400 / 60)
        AS INTEGER) AS duration_min,
        COUNT(DISTINCT e.id) AS exercise_count,
        COUNT(es.id) AS total_sets
    FROM workout_log w
    LEFT JOIN workout_template wt 
        ON w.workout_template_id = wt.id
    LEFT JOIN exercise_log e 
        ON e.workout_id = w.id
    LEFT JOIN exercise_set es 
        ON es.exercise_id = e.id
    WHERE w.user_id = ?
    GROUP BY w.id
    ORDER BY w.started_at DESC
    LIMIT ?
    """
    return database.query(sql, [user_id, limit])
