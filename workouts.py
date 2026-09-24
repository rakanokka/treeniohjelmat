from database import query, execute, insert_id

def insert_workout_exercise_template(workout_template_id: int, exercise_template_id: int, order_index: int) -> int:
    sql = "INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES (?, ?, ?)"
    execute(sql, [workout_template_id, exercise_template_id, order_index])
    return insert_id()
    
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
