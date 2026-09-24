from typing import Any
from database import query, execute, insert_id, get_connection

def add_my_exercise_template(user_id: int, name: str, category: str, target_sets: int, target_reps: int) -> int:
    category_or_null = (category.strip() or None) if category else None 
    sql = "INSERT INTO exercise_template (creator_id, name, category, target_sets, target_reps) VALUES (?, ?, ?, ?, ?)"
    execute(sql, [
        user_id, 
        name.strip(), 
        category_or_null, 
        target_sets, 
        target_reps
    ])
    return insert_id()

def add_adopted_exercise_template(user_id: int, template_id: int) -> int:
    sql = "INSERT INTO user_exercise_template (user_id, exercise_template_id) VALUES (?, ?)"
    execute(sql, [user_id, template_id])
    return insert_id()

def get_exercise_template_creator_id(template_id: int) -> int:
    sql = "SELECT creator_id FROM exercise_template WHERE id = ?"
    r = query(sql, [template_id])
    return r[0]["creator_id"] if r else -1

def get_exercise_template(template_id: int) -> Any:
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
    WHERE e.id = ? 
    """ 
    r = query(sql, [template_id])
    return r[0] if r else None

def get_exercise_templates(user_id: int) -> list:
    sql = """
    SELECT 
        e.id AS id,
        e.creator_id AS creator_id,
        e.name AS name,
        e.category AS category,
        e.target_sets AS sets,
        e.target_reps AS reps,
        u.username AS creator_name
    FROM exercise_template e
    JOIN "user" u ON e.creator_id = u.id
    WHERE e.creator_id = ?
    ORDER BY e.name ASC
    """
    return query(sql, [user_id])

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

def get_adopted_exercise_templates(user_id: int) -> list:
    sql = """
    SELECT 
        e.id AS id,
        e.name AS name,
        e.category AS category,
        e.target_sets AS sets,
        e.target_reps AS reps,
        e.creator_id AS creator_id,
        u.username AS creator_name
    FROM user_exercise_template uet
    JOIN exercise_template e 
        ON uet.exercise_template_id = e.id
    JOIN "user" u 
        ON e.creator_id = u.id
    WHERE uet.user_id = ?
    ORDER BY e.name ASC
    """
    return query(sql, [user_id])

def get_exercise_logs(user_id: int) -> list:
    sql = """
    SELECT DISTINCT
        COALESCE(e.exercise_template_id, e.id) AS id,
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
