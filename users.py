from typing import Any
from database import query, execute
from werkzeug.security import check_password_hash, generate_password_hash

def get_user(user_id: int) -> Any:
    sql = 'SELECT id, username, password_hash FROM "user" WHERE id = ?'
    r = query(sql, [user_id])
    return r[0] if r else None

def get_other_users(user_id: int) -> list:
    sql = 'SELECT id, username FROM "user" WHERE id <> ?'
    return query(sql, [user_id])

def get_user_profile_info(user_id: int) -> Any:
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
    r = query(sql, [user_id])
    return r[0] if r else None

def get_favourite_exercise_categories(user_id: int, limit = 5) -> list:
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
    return query(sql, [user_id, user_id, user_id, user_id, limit])

def get_workout_templates_usage_count(user_id: int, limit = 5) -> list:
    sql = """
    SELECT 
        wt.id,
        wt.name,
        wt.description,
        wt.created_at,
        COUNT(uwt.user_id) AS adopted_by_others_count
    FROM workout_template wt
    LEFT JOIN user_workout_template uwt 
        ON wt.id = uwt.workout_template_id
    WHERE wt.creator_id = ?
    GROUP BY wt.id
    ORDER BY adopted_by_others_count DESC, wt.created_at DESC
    LIMIT ?
    """
    return query(sql, [user_id, limit])

def add_user(username: str, email: str, password: str):
    pw_hash = generate_password_hash(password)
    sql = 'INSERT INTO "user" (username, email, password_hash) VALUES (?, ?, ?)'
    execute(sql, [username.strip(), email.strip(), pw_hash])

def has_user(username: str, password: str) -> int:
    sql = 'SELECT id, password_hash FROM "user" WHERE username = ?'
    r = query(sql, [username])
    if r:
        pw_hash = r[0]["password_hash"]
        if check_password_hash(pw_hash, password):
            return int(r[0]["id"])
    return -1
