from database import query, execute, insert_id

def add_my_workout_template(user_id: int, name: str, description: str) -> int:
    sql = "INSERT INTO workout_template (creator_id, workout_plan_id, name, description) VALUES (?, ?, ?, ?)"
    execute(sql, [user_id, None, name, description or None])
    return insert_id()

def add_workout_exercise_template(workout_template_id: int, exercise_template_id: int, order_index: int) -> int:
    sql = "INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES (?, ?, ?)"
    execute(sql, [workout_template_id, exercise_template_id, order_index])
    return insert_id()

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
