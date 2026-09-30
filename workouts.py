from typing import Any
from database import get_connection, query, execute, insert_id, row_count

def add_my_workout_template(user_id: int, name: str, description: str) -> int:
    sql = "INSERT INTO workout_template (creator_id, workout_plan_id, name, description) VALUES (?, ?, ?, ?)"
    execute(sql, [user_id, None, name, description or None])
    return insert_id()

def add_workout_exercise_template(workout_template_id: int, exercise_template_id: int, order_index: int) -> int:
    sql = "INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES (?, ?, ?)"
    execute(sql, [workout_template_id, exercise_template_id, order_index])
    return insert_id()

def add_exercise_to_workout(user_id: int, workout_template_id: int, exercise_template_id):
    print("add_exercise_to_workout")
    sql = """
    INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index)
    SELECT 
        ?, 
        ?,
        COALESCE(
            (SELECT MAX(order_index) + 1 
             FROM workout_exercise_template 
             WHERE workout_template_id = ?), 
            0
        )
    WHERE EXISTS (
        SELECT 1 
        FROM workout_template 
        WHERE id = ? AND creator_id = ?
    )
    """
    execute(sql, [
        workout_template_id,
        exercise_template_id,
        workout_template_id,
        workout_template_id,
        user_id
    ])
    #return insert_id()

def get_workout_template_exercises(user_id: int, workout_template_id: int) -> list:
    sql = """
    SELECT 
        wet.id AS id,
        wet.workout_template_id AS workout_template_id,
        wet.exercise_template_id AS exercise_template_id,
        wet.order_index AS order_index,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps
    FROM workout_exercise_template wet
    JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    JOIN workout_template wt 
        ON wet.workout_template_id = wt.id
    LEFT JOIN user_workout_template uwt 
        ON wt.id = uwt.workout_template_id AND uwt.user_id = ?
    WHERE wet.workout_template_id = ?
    AND (wt.creator_id = ? OR uwt.user_id IS NOT NULL)
    ORDER BY wet.order_index ASC, wet.id ASC
    """
    return query(sql, [user_id, workout_template_id, user_id])

def get_workout_template_creator_id(template_id: int) -> int:
    sql = "SELECT creator_id FROM workout_template WHERE id = ?"
    r = query(sql, [template_id])
    return r[0]["creator_id"] if r else -1

def get_workout_template(template_id: int) -> Any:
    sql = """
    SELECT 
        wt.id AS id,
        wt.name AS name,
        wt.description AS description,
        wt.creator_id AS creator_id,
        u.username AS creator_name
    FROM workout_template wt
    JOIN "user" u
        ON wt.creator_id = u.id
    WHERE wt.id = ? 
    """ 
    r = query(sql, [template_id])
    return r[0] if r else None


def get_workout_templates(user_id: int) -> list:
    sql = """
    SELECT 
        wt.id AS id,
        wt.creator_id AS creator_id,
        wt.name AS name,
        wt.description AS description,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        COUNT(DISTINCT wet.id) AS exercise_count,
        COUNT(DISTINCT w.id) AS workout_count,
        COUNT(DISTINCT uwt.user_id) AS user_count
    FROM workout_template wt
    JOIN "user" u 
        ON wt.creator_id = u.id
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    LEFT JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    LEFT JOIN user_workout_template uwt 
        ON wt.id = uwt.workout_template_id
    LEFT JOIN workout_log w 
        ON wt.id = w.workout_template_id AND w.user_id = ?
    WHERE wt.creator_id = ?
    GROUP BY wt.id
    ORDER BY wt.name ASC
    """
    return query(sql, [user_id, user_id])

def get_adopted_workout_templates(user_id: int) -> list:
    sql = """
    SELECT 
        wt.id AS id,
        wt.creator_id AS creator_id,
        wt.name AS name,
        wt.description AS description,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        COUNT(DISTINCT wet.id) AS exercise_count,
        COUNT(DISTINCT w.id) AS workout_count,
        COUNT(DISTINCT uwt_all.user_id) AS user_count
    FROM user_workout_template uwt_my
    JOIN workout_template wt 
        ON uwt_my.workout_template_id = wt.id
    JOIN "user" u 
        ON wt.creator_id = u.id
    LEFT JOIN user_workout_template uwt_all 
        ON wt.id = uwt_all.workout_template_id
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    LEFT JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    LEFT JOIN workout_log w 
        ON wt.id = w.workout_template_id AND w.user_id = ?
    WHERE uwt_my.user_id = ?
    GROUP BY wt.id
    ORDER BY wt.name ASC
    """
    return query(sql, [user_id, user_id])

def get_workout_log_user_id(workout_id: int) -> int:
    sql = "SELECT user_id FROM workout_log WHERE id = ?"
    r = query(sql, [workout_id])
    return r[0]["user_id"] if r else -1

def get_workout_logs(user_id: int) -> list:
    sql = """
    SELECT 
        w.id AS id,
        w.name AS name,
        w.notes AS notes,
        w.started_at AS started_at,
        w.ended_at AS ended_at,
        w.user_id AS creator_id,
        u.username AS creator_name
    FROM workout_log w
    JOIN "user" u 
        ON w.user_id = u.id
    LEFT JOIN exercise_log e 
        ON e.workout_id = w.id
    WHERE w.user_id = ?
    GROUP BY w.id, w.name, w.notes, w.started_at, w.ended_at, w.user_id, u.username
    ORDER BY w.started_at DESC
    """
    return query(sql, [user_id])

def update_workout_template(user_id: int, template_id: int, name: str, description):
    description_or_null = (description.strip() or None) if description else None 
    sql = """
    UPDATE workout_template
    SET name = ?, description = ?
    WHERE id = ? AND creator_id = ?
    """
    execute(sql, [
        name.strip(),
        description_or_null,
        template_id,
        user_id
    ])

def delete_workout_template(user_id: int, template_id: int):
    creator_id = get_workout_template_creator_id(template_id)
    if creator_id != -1:
        user_is_creator = creator_id == user_id
        if user_is_creator:
            connection = get_connection()
            with connection:
                sql = "DELETE FROM workout_exercise_template WHERE workout_template_id = ?"
                connection.execute(sql, [template_id])
                sql = "DELETE FROM workout_template WHERE id = ? AND creator_id = ?"
                connection.execute(sql, [template_id, user_id])
            connection.close()
        else:
            sql = "DELETE FROM user_workout_template WHERE user_id = ? AND workout_template_id = ?"
            execute(sql, [user_id, template_id])

def remove_exercise_from_workout(user_id: int, workout_template_id: int, exercise_template_id: int):
    sql = """
    DELETE FROM workout_exercise_template
    WHERE workout_template_id = ?
    AND exercise_template_id = ?
    AND EXISTS (
        SELECT 1 
        FROM workout_template 
        WHERE id = ? AND creator_id = ?
    )
    """
    execute(sql, [
        workout_template_id,
        exercise_template_id,
        workout_template_id,
        user_id,
    ])
