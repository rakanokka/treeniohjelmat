from typing import Any
from database import query, execute, get_connection

def add_my_exercise_template(user_id: int, name: str, category: str, target_sets: int, target_reps: int):
    category_or_null = (category.strip() or None) if category else None 
    sql = "INSERT INTO exercise_template (creator_id, name, category, target_sets, target_reps) VALUES (?, ?, ?, ?, ?)"
    execute(sql, [
        user_id, 
        name.strip(), 
        category_or_null, 
        target_sets, 
        target_reps
    ])

def add_adopted_exercise_template(user_id: int, template_id: int):
    sql = "INSERT INTO user_exercise_template (user_id, exercise_template_id) VALUES (?, ?)"
    execute(sql, [user_id, template_id])

def add_excercise_template_comment(user_id: int, template_id: int, content: str):
    sql = "INSERT INTO user_comment (user_id, exercise_template_id, content) VALUES (?, ?, ?)"
    execute(sql, [user_id, template_id, content])

def get_excercise_template_comments(template_id: int) -> list:
    sql = """
    SELECT 
        c.id AS id,
        c.content AS content,
        c.created_at AS created_at,
        c.user_id AS author_id,
        u.username AS author_name
    FROM user_comment c
    JOIN "user" u 
        ON c.user_id = u.id
    WHERE c.exercise_template_id = ?
    ORDER BY c.created_at ASC
    """
    return query(sql, [template_id])

def get_exercise_template_creator_id(template_id: int) -> int:
    sql = "SELECT creator_id FROM exercise_template WHERE id = ?"
    r = query(sql, [template_id])
    return r[0]["creator_id"] if r else -1

def get_exercise_user_id(exercise_id: int) -> int:
    sql = """
    SELECT 
        w.user_id AS user_id
    FROM exercise_log e
    JOIN workout_log w 
        ON w.id = e.workout_id 
    WHERE e.id = ?
    """
    r = query(sql, [exercise_id])
    return r[0]["user_id"] if r else -1

def get_exercise_template(template_id: int) -> Any:
    sql = """
    SELECT 
        et.id AS id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps,
        et.creator_id AS creator_id,
        u.username AS creator_name
    FROM exercise_template et
    JOIN "user" u
        ON et.creator_id = u.id
    WHERE et.id = ? 
    """ 
    r = query(sql, [template_id])
    return r[0] if r else None

def get_exercise_templates(user_id: int) -> list:
    sql = """
    SELECT 
        et.id AS id,
        et.creator_id AS creator_id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps,
        u.username AS creator_name,
        COUNT(DISTINCT e.id) AS exercise_count,
        COUNT(DISTINCT uet.user_id) AS user_count
    FROM exercise_template et
    JOIN "user" u 
        ON et.creator_id = u.id
    LEFT JOIN user_exercise_template uet 
        ON et.id = uet.exercise_template_id
    LEFT JOIN exercise_log e 
        ON et.id = e.exercise_template_id
    LEFT JOIN workout_log w 
        ON e.workout_id = w.id AND w.user_id = ?
    WHERE et.creator_id = ?
    GROUP BY et.id
    ORDER BY et.name ASC
    """
    return query(sql, [user_id, user_id])

def get_exercise_templates_in_workout(workout_template_id: int) -> list:
    sql = """
    SELECT 
        et.id AS id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS target_sets,
        et.target_reps AS target_reps,
        wet.order_index AS order_index
    FROM workout_exercise_template wet
    JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    WHERE wet.workout_template_id = ?
    ORDER BY wet.order_index ASC
    """
    return query(sql, [workout_template_id])

def get_adopted_exercise_templates(user_id: int) -> list:
    sql = """
    SELECT 
        et.id AS id,
        et.creator_id AS creator_id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps,
        u.username AS creator_name,
        COUNT(DISTINCT e.id) AS exercise_count,
        COUNT(DISTINCT uet_all.user_id) AS user_count
    FROM user_exercise_template uet_my
    JOIN exercise_template et 
        ON uet_my.exercise_template_id = et.id
    JOIN "user" u  
        ON et.creator_id = u.id
    LEFT JOIN user_exercise_template uet_all
        ON et.id = uet_all.exercise_template_id
    LEFT JOIN exercise_log e 
        ON et.id = e.exercise_template_id
    LEFT JOIN workout_log w 
        ON e.workout_id = w.id AND w.user_id = ?
    WHERE uet_my.user_id = ?
    GROUP BY et.id 
    ORDER BY et.name ASC
    """
    return query(sql, [user_id, user_id])

def find_exercise_templates(name: str, user_id: int) -> list:
    sql = """
    SELECT 
        e.id AS id,
        e.name AS name,
        e.category AS category,
        e.target_sets AS sets,
        e.target_reps AS reps,
        e.creator_id AS creator_id,
        u.username AS creator_name
    FROM exercise_template e
    JOIN "user" u 
        ON e.creator_id = u.id
    LEFT JOIN user_exercise_template ue 
        ON e.id = ue.exercise_template_id AND ue.user_id = ?
    WHERE e.creator_id != ? 
        AND ue.exercise_template_id IS NULL 
        AND LOWER(e.name) LIKE LOWER(?)
    ORDER BY e.name ASC
    """ 
    return query(sql, [user_id, user_id, f"%{name.strip()}%"])

def get_exercise_log(exercise_id: int) -> dict | None:
    sql = """
    SELECT 
        e.id AS id,
        e.workout_id AS workout_id,
        e.name AS name,
        e.notes AS notes,
        w.started_at AS date,
        COUNT(es.id) AS sets,
        COALESCE(SUM(es.reps), 0) AS reps,
        COALESCE(et.target_sets, 0) AS target_sets,
        COALESCE(et.target_reps, 0) AS target_reps,
        (COUNT(es.id) - COALESCE(et.target_sets, 0)) AS sets_diff,
        (COALESCE(SUM(es.reps), 0) - (COALESCE(et.target_sets, 0) * COALESCE(et.target_reps, 0))) AS reps_diff
    FROM exercise_log e
    JOIN workout_log w 
        ON e.workout_id = w.id
    LEFT JOIN exercise_set es 
        ON es.exercise_id = e.id
    LEFT JOIN exercise_template et 
        ON e.exercise_template_id = et.id
    WHERE e.id = ?
    GROUP BY e.id
    """
    r = query(sql, [exercise_id])
    return r[0] if r else None

def get_exercise_logs(user_id: int) -> list:
    sql = """
    SELECT
        e.id AS id,
        e.exercise_template_id AS template_id,
        e.name AS name,
        et.category AS category,
        w.user_id AS creator_id,
        u.username AS creator_name,
        e.notes AS notes
    FROM exercise_log e
    JOIN workout_log w 
        ON e.workout_id = w.id
    JOIN "user" u 
        ON w.user_id = u.id
    LEFT JOIN exercise_template et 
        ON e.exercise_template_id = et.id
    WHERE w.user_id = ?
    ORDER BY e.name ASC
    """
    return query(sql, [user_id])

def update_exercise_template(user_id: int, template_id: int, name: str, category: str, target_sets: int, target_reps: int):
    category_or_null = (category.strip() or None) if category else None 
    sql = """
    UPDATE exercise_template 
    SET name = ?, category = ?, target_sets = ?, target_reps = ?
    WHERE id = ? AND creator_id = ?
    """
    execute(sql, [
        name.strip(),
        category_or_null,
        target_sets,
        target_reps,
        template_id,
        user_id
    ])

def delete_exercise_template(user_id: int, template_id: int):
    creator_id = get_exercise_template_creator_id(template_id)
    if creator_id != -1:
        user_is_creator = creator_id == user_id
        if user_is_creator:
            connection = get_connection()
            with connection:
                sql = "DELETE FROM user_exercise_template WHERE exercise_template_id = ?"
                connection.execute(sql, [template_id])
                sql = "DELETE FROM exercise_template WHERE id = ? AND creator_id = ?"
                connection.execute(sql, [template_id, user_id])
            connection.close()
        else:
            sql = "DELETE FROM user_exercise_template WHERE user_id = ? AND exercise_template_id = ?"
            execute(sql, [user_id, template_id])

def delete_exercise_log(user_id: int, exercise_id: int):
    sql = """
    DELETE FROM exercise_log
    WHERE id = ? 
    AND workout_id IN (
        SELECT id 
        FROM workout_log 
        WHERE user_id = ?
    )
    """
    execute(sql, [exercise_id, user_id])
