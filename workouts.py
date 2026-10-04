import database

def add_my_workout_template(user_id: int, name: str, description: str, tags: list[str]):
    connection = database.get_connection()
    sql = "INSERT INTO workout_template (creator_id, workout_plan_id, name, description) VALUES (?, ?, ?, ?)"
    template_id = database.execute_with(connection, sql, [
        user_id, 
        None, 
        name.strip(), 
        description.strip() or None
    ])
    if template_id == -1:
        print("INSERT INTO workout_template failed")
        return
    for tag in tags:
        sql = "INSERT OR IGNORE INTO tag (name) VALUES (?)"
        database.execute_with(connection, sql, [tag])
        sql = """
        INSERT INTO workout_template_tag (workout_template_id, tag_id)
        VALUES (?, (SELECT id FROM tag WHERE name = ?))
        """
        database.execute_with(connection, sql, [template_id, tag])
    connection.close()

def add_adopted_workout_template(user_id: int, template_id: int):
    sql = "INSERT INTO user_workout_template (user_id, workout_template_id) VALUES (?, ?)"
    database.execute(sql, [user_id, template_id])

def add_workout_exercise_template(workout_template_id: int, exercise_template_id: int, order_index: int):
    sql = "INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES (?, ?, ?)"
    database.execute(sql, [workout_template_id, exercise_template_id, order_index])

def add_workout_log(user_id: int, workout_template_id: int, name: str, description: str):
    sql = """
    INSERT INTO workout_log (user_id, workout_template_id, name, notes, started_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    database.execute(sql, [user_id, workout_template_id, name.strip(), description.strip() or None])

def add_exercise_to_workout(user_id: int, workout_template_id: int, exercise_template_id: int):
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
    database.execute(sql, [
        workout_template_id,
        exercise_template_id,
        workout_template_id,
        workout_template_id,
        user_id
    ])

def add_exercise_to_workout_log(workout_id: int, exercise_template_id: int, name: str, reps: list[int], weights: list[float]):
    connection = database.get_connection()
    sql = """
    INSERT INTO exercise_log (workout_id, exercise_template_id, name)
    VALUES (?, ?, ?)
    """
    exercise_id = database.execute_with(connection, sql, [workout_id, exercise_template_id, name.strip()])
    if exercise_id == -1: 
        print("INSERT INTO exercise_log failed")
        return
    sql = """
    INSERT INTO exercise_set (exercise_id, order_index, reps, weight)
    VALUES (?, ?, ?, ?)
    """
    for order_index, (rep, weight) in enumerate(zip(reps, weights)):
        connection.execute(sql, [exercise_id, order_index, rep, weight])
    connection.commit()
    connection.close()

def add_workout_template_comment(user_id: int, template_id: int, content: str):
    sql = "INSERT INTO user_comment (user_id, workout_template_id, content) VALUES (?, ?, ?)"
    database.execute(sql, [user_id, template_id, content])

def add_workout_template_tag(template_id: int, tag_id: int):
    sql = "INSERT INTO workout_template_tag (workout_template_id, tag_id) VALUES (?, ?)"
    database.execute(sql, [template_id, tag_id])

def get_workout_template_comments(template_id: int) -> list[dict]:
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
    WHERE c.workout_template_id = ?
    ORDER BY c.created_at ASC
    """
    return database.query(sql, [template_id])

def get_workout_template_exercises(user_id: int, workout_template_id: int) -> list[dict]:
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
    return database.query(sql, [user_id, workout_template_id, user_id])

def get_workout_template_creator_id(template_id: int) -> int:
    sql = "SELECT creator_id FROM workout_template WHERE id = ?"
    r = database.query(sql, [template_id])
    return r[0]["creator_id"] if r else -1

def get_workout_template(template_id: int) -> dict | None:
    sql = """
    SELECT 
        wt.id AS id,
        wt.name AS name,
        wt.description AS description,
        wt.creator_id AS creator_id,
        u.username AS creator_name,
        GROUP_CONCAT(t.name, ',') AS tags
    FROM workout_template wt
    JOIN "user" u
        ON wt.creator_id = u.id
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id
    WHERE wt.id = ? 
    GROUP BY wt.id
    """ 
    r = database.query(sql, [template_id])
    return r[0] if r else None

def get_workout_templates(user_id: int) -> list[dict]:
    sql = """
    SELECT 
        wt.id AS id,
        wt.creator_id AS creator_id,
        wt.name AS name,
        wt.description AS description,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        GROUP_CONCAT(DISTINCT t.name) AS tags, 
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
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id 
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id 
    WHERE wt.creator_id = ?
    GROUP BY wt.id
    ORDER BY wt.name ASC
    """
    return database.query(sql, [user_id, user_id])

def get_adopted_workout_templates(user_id: int) -> list[dict]:
    sql = """
    SELECT 
        wt.id AS id,
        wt.creator_id AS creator_id,
        wt.name AS name,
        wt.description AS description,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        COUNT(DISTINCT wet.id) AS exercise_count,
        GROUP_CONCAT(DISTINCT t.name) AS tags,
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
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id 
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id 
    WHERE uwt_my.user_id = ?
    GROUP BY wt.id
    ORDER BY wt.name ASC
    """
    return database.query(sql, [user_id, user_id])

def find_workout_templates_by_tag(tag: str, user_id: int) -> list[dict]:
    sql = """
    SELECT 
        wt.id AS id,
        wt.name AS name,
        wt.description AS description,
        wt.creator_id AS creator_id,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        GROUP_CONCAT(DISTINCT t_all.name) AS tags,
        COUNT(DISTINCT wet.id) AS exercise_count,
        COUNT(DISTINCT w.id) AS workout_count,
        COUNT(DISTINCT uwt_all.user_id) AS user_count
    FROM workout_template wt
    JOIN "user" u 
        ON wt.creator_id = u.id
    JOIN workout_template_tag wtt_filter 
        ON wt.id = wtt_filter.workout_template_id
    JOIN tag t_filter 
        ON wtt_filter.tag_id = t_filter.id
    LEFT JOIN workout_template_tag wtt_all 
        ON wt.id = wtt_all.workout_template_id
    LEFT JOIN tag t_all 
        ON wtt_all.tag_id = t_all.id
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    LEFT JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    LEFT JOIN user_workout_template uwt_all 
        ON wt.id = uwt_all.workout_template_id
    LEFT JOIN workout_log w 
        ON wt.id = w.workout_template_id AND w.user_id = ?
    WHERE LOWER(t_filter.name) = LOWER(?)
    GROUP BY wt.id
    ORDER BY wt.name ASC
    """
    return database.query(sql, [user_id, tag.strip()]) 

def find_workout_templates_by_name(name: str, user_id: int) -> list[dict]:
    sql = """
    SELECT 
        wt.id AS id,
        wt.name AS name,
        wt.description AS description,
        wt.creator_id AS creator_id,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT t.name) AS tags,
        (SELECT COUNT(*) 
        FROM workout_exercise_template wet 
        WHERE wet.workout_template_id = wt.id) AS exercise_count
    FROM workout_template wt
    JOIN "user" u 
        ON wt.creator_id = u.id
    LEFT JOIN user_workout_template uwt 
        ON wt.id = uwt.workout_template_id AND uwt.user_id = ?
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id 
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id 
    WHERE wt.creator_id != ? 
        AND uwt.workout_template_id IS NULL 
        AND LOWER(wt.name) LIKE LOWER(?)
    GROUP BY wt.id
    ORDER BY wt.name ASC 
    """
    return database.query(sql, [user_id, user_id, f"%{name.strip()}%"])

def get_workout_template_name(template_id: int) -> str | None:
    sql = "SELECT name FROM workout_template WHERE id = ?"
    r = database.query(sql, [template_id])
    return r[0]["name"] if r else None

def get_workout_log_user_id(workout_id: int) -> int:
    sql = "SELECT user_id FROM workout_log WHERE id = ?"
    r = database.query(sql, [workout_id])
    return r[0]["user_id"] if r else -1

def get_workout_logs(user_id: int) -> list[dict]:
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
    return database.query(sql, [user_id])

def get_workout_log(workout_id: int) -> dict | None:
    sql = """
    SELECT 
        w.id AS id,
        w.user_id AS user_id,
        w.workout_template_id AS workout_template_id,
        w.name AS name,
        w.notes AS notes,
        w.started_at AS started_at,
        w.ended_at AS ended_at,
        CASE 
            WHEN w.ended_at IS NOT NULL THEN
                CAST(ROUND((JULIANDAY(w.ended_at) - JULIANDAY(w.started_at)) * 86400 / 60) AS INTEGER)
            ELSE NULL 
        END AS duration_min
    FROM workout_log w
    LEFT JOIN workout_template wt 
        ON w.workout_template_id = wt.id
    WHERE w.id = ? 
    """
    r = database.query(sql, [workout_id])
    return r[0] if r else None

def get_workout_exercises(workout_id: int) -> list[dict]:
    sql = """
    SELECT 
        e.id AS id,
        e.workout_id AS workout_id,
        e.exercise_template_id AS exercise_template_id,
        e.name AS name,
        e.notes AS notes,
        COUNT(es.id) AS sets,
        COALESCE(SUM(es.reps), 0) AS reps,
        COALESCE(MAX(es.weight), 0.0) AS max_weight
    FROM exercise_log e
    LEFT JOIN exercise_set es 
        ON es.exercise_id = e.id
    WHERE e.workout_id = ?
    GROUP BY e.id
    ORDER BY e.id ASC
    """
    return database.query(sql, [workout_id])

def update_workout_template(user_id: int, template_id: int, name: str, description: str, tags: list[str]):
    connection = database.get_connection()
    sql = """
    UPDATE workout_template
    SET name = ?, description = ?
    WHERE id = ? AND creator_id = ?
    """
    c = connection.execute(sql, [
        name.strip(),
        description.strip() or None,
        template_id,
        user_id
    ])
    connection.commit()
    if c.rowcount == 0:
        print("UPDATE workout_template failed")
        return
    with connection:
        sql = "DELETE FROM workout_template_tag WHERE workout_template_id = ?"
        connection.execute(sql, [template_id])
        for tag in tags:
            sql = "INSERT OR IGNORE INTO tag (name) VALUES (?)"
            connection.execute(sql, [tag])
            sql = """
            INSERT INTO workout_template_tag (workout_template_id, tag_id)
            VALUES (?, (SELECT id FROM tag WHERE name = ?))
            """
            connection.execute(sql, [template_id, tag])
    connection.close()

def delete_my_workout_template(user_id: int, template_id: int):
    connection = database.get_connection()
    with connection:
        sql = "DELETE FROM workout_exercise_template WHERE workout_template_id = ?"
        connection.execute(sql, [template_id])
        sql = "DELETE FROM workout_template WHERE id = ? AND creator_id = ?"
        connection.execute(sql, [template_id, user_id])
    connection.close()

def delete_adopted_workout_template(user_id: int, template_id: int):
    sql = "DELETE FROM user_workout_template WHERE user_id = ? AND workout_template_id = ?"
    database.execute(sql, [user_id, template_id])

def delete_workout_log(user_id: int, workout_id: int):
    sql = """
    DELETE FROM workout_log
    WHERE id = ? AND user_id = ?
    """
    database.execute(sql, [workout_id, user_id])

def remove_exercise_from_workout_template(user_id: int, workout_template_id: int, exercise_template_id: int):
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
    database.execute(sql, [
        workout_template_id,
        exercise_template_id,
        workout_template_id,
        user_id,
    ])

def remove_exercise_from_workout_log(workout_id: int, exercise_id: int):
    sql = """
    DELETE FROM exercise_log
    WHERE id = ? AND workout_id = ?;
    """
    database.execute(sql, [exercise_id, workout_id])
