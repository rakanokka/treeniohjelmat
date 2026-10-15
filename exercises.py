import database

def add_my_exercise_template(user_id: int, name: str, category: str, target_sets: int, target_reps: int) -> bool:
    connection = database.get_connection()
    if not connection:
        return False
    try:
        with connection:
            sql = """
            INSERT INTO exercise_template (creator_id, name, category, target_sets, target_reps)
            VALUES (?, ?, ?, ?, ?) 
            """
            c = connection.execute(sql, [
                user_id, 
                name.strip(), 
                category.strip() or None, 
                target_sets, 
                target_reps
            ])
            template_id = c.lastrowid
            sql = "UPDATE exercise_template SET root_id = ? WHERE id = ?"
            connection.execute(sql, [template_id, template_id])
        return True
    except Exception as e:
        print(f"SQLite Error: {e}")
        return False
    finally:
        connection.close()

def add_adopted_exercise_template(user_id: int, template_id: int) -> bool:
    sql = "INSERT INTO user_exercise_template (user_id, exercise_template_id) VALUES (?, ?)"
    return database.execute(sql, [user_id, template_id])

def add_excercise_template_comment(user_id: int, template_id: int, content: str) -> bool:
    sql = "INSERT INTO user_comment (user_id, exercise_template_id, content) VALUES (?, ?, ?)"
    return database.execute(sql, [user_id, template_id, content])

def get_excercise_template_comments(template_id: int) -> list[dict]:
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
    return database.query(sql, [template_id])

def get_exercise_template_creator_id(template_id: int) -> int | None:
    sql = "SELECT creator_id FROM exercise_template WHERE id = ?"
    r = database.query(sql, [template_id])
    return r[0]["creator_id"] if r else None

def get_exercise_user_id(exercise_id: int) -> int | None:
    sql = """
    SELECT w.user_id AS user_id
    FROM exercise_log e
    JOIN workout_log w 
        ON w.id = e.workout_id 
    WHERE e.id = ?
    """
    r = database.query(sql, [exercise_id])
    return r[0]["user_id"] if r else None

def get_exercise_template(template_id: int) -> dict | None:
    sql = """
    SELECT 
        et.id AS id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps,
        et.creator_id AS creator_id,
        u.username AS creator_name,
        (et.root_id != et.id) AS has_previous_version
    FROM exercise_template et
    JOIN "user" u
        ON et.creator_id = u.id
    WHERE et.id = ? 
    """ 
    r = database.query(sql, [template_id])
    return r[0] if r else None

def get_exercise_template_previous_version_id(template_id: int) -> int | None:
    sql = "SELECT id FROM exercise_template WHERE next_version_id = ?"
    r = database.query(sql, [template_id])
    return r[0]["id"] if r else None

def get_exercise_template_next_version_id(template_id: int) -> int | None:
    sql = "SELECT next_version_id FROM exercise_template WHERE id = ?"
    r = database.query(sql, [template_id])
    if r:
        return r[0]["next_version_id"] or None
    return None

def get_exercise_templates(user_id: int) -> list[dict]:
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
        COUNT(DISTINCT uet_all.user_id) AS user_count,
        CASE 
            WHEN NOT EXISTS (
                SELECT 1 FROM exercise_template et_prev WHERE et_prev.next_version_id = et.id
            ) THEN 1 
            ELSE 0 
        END AS is_root
    FROM exercise_template et
    JOIN "user" u 
        ON et.creator_id = u.id
    LEFT JOIN exercise_template et_all 
        ON et.root_id = et_all.root_id
    LEFT JOIN user_exercise_template uet_all 
        ON et_all.id = uet_all.exercise_template_id
    LEFT JOIN exercise_log e 
        ON et.id = e.exercise_template_id
    LEFT JOIN workout_log w 
        ON e.workout_id = w.id AND w.user_id = ?
    WHERE et.creator_id = ? AND et.next_version_id IS NULL
    GROUP BY et.id
    ORDER BY et.name ASC
    """
    return database.query(sql, [user_id, user_id])

def get_exercise_templates_in_workout(workout_template_id: int) -> list[dict]:
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
    return database.query(sql, [workout_template_id])

def get_adopted_exercise_templates(user_id: int) -> list[dict]:
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
        COUNT(DISTINCT uet_all.user_id) AS user_count,
        CASE WHEN et.next_version_id IS NOT NULL THEN 1 ELSE 0 END AS has_next_version,
        CASE 
            WHEN NOT EXISTS (
                SELECT 1 FROM exercise_template et_prev WHERE et_prev.next_version_id = et.id
            ) THEN 1 
            ELSE 0 
        END AS is_root
    FROM user_exercise_template uet_my
    JOIN exercise_template et 
        ON uet_my.exercise_template_id = et.id
    JOIN "user" u  
        ON et.creator_id = u.id
    LEFT JOIN exercise_template et_all 
        ON et.root_id = et_all.root_id
    LEFT JOIN user_exercise_template uet_all
        ON et_all.id = uet_all.exercise_template_id
    LEFT JOIN exercise_log e 
        ON et.id = e.exercise_template_id
    LEFT JOIN workout_log w 
        ON e.workout_id = w.id AND w.user_id = ?
    WHERE uet_my.user_id = ?
    GROUP BY et.id 
    ORDER BY et.name ASC
    """
    return database.query(sql, [user_id, user_id])

def find_exercise_templates_by_category(category: str) -> list[dict]:
    sql = """
    SELECT 
        et.id AS id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps,
        et.creator_id AS creator_id,
        u.username AS creator_name,
        COUNT(DISTINCT e.id) AS exercise_count,
        COUNT(DISTINCT uet_all.user_id) AS user_count
    FROM exercise_template et
    JOIN "user" u 
        ON et.creator_id = u.id
    LEFT JOIN exercise_template et_all 
        ON et.root_id = et_all.root_id
    LEFT JOIN user_exercise_template uet_all
        ON et_all.id = uet_all.exercise_template_id
    LEFT JOIN exercise_log e 
        ON et.id = e.exercise_template_id
    WHERE et.next_version_id IS NULL 
        AND LOWER(et.category) LIKE LOWER(?)
    GROUP BY et.id
    ORDER BY et.name ASC
    """
    return database.query(sql, [f"%{category.strip()}%"])

def find_exercise_templates_by_name(name: str) -> list[dict]:
    sql = """
    SELECT 
        et.id AS id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps,
        et.creator_id AS creator_id,
        u.username AS creator_name,
        COUNT(DISTINCT e.id) AS exercise_count,
        COUNT(DISTINCT uet_all.user_id) AS user_count
    FROM exercise_template et
    JOIN "user" u 
        ON et.creator_id = u.id
    LEFT JOIN exercise_template et_all 
        ON et.root_id = et_all.root_id
    LEFT JOIN user_exercise_template uet_all
        ON et_all.id = uet_all.exercise_template_id
    LEFT JOIN exercise_log e 
        ON et.id = e.exercise_template_id
    WHERE et.next_version_id IS NULL 
        AND LOWER(et.name) LIKE LOWER(?)
    GROUP BY et.id
    ORDER BY et.name ASC
    """
    return database.query(sql, [f"%{name.strip()}%"])

def get_all_exercise_template_ids(user_id: int) -> list[int]:
    sql = """
    SELECT id FROM exercise_template WHERE creator_id = ? AND next_version_id IS NULL
    UNION
    SELECT exercise_template_id AS id FROM user_exercise_template WHERE user_id = ?
    """
    rows = database.query(sql, [user_id, user_id])
    return [row["id"] for row in rows]

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
    r = database.query(sql, [exercise_id])
    return r[0] if r else None

def get_exercise_logs(user_id: int) -> list[dict]:
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
    return database.query(sql, [user_id])

def update_exercise_template(user_id: int, template_id: int, name: str, category: str, target_sets: int, target_reps: int) -> bool:
    connection = database.get_connection()
    if not connection:
        return False
    sql = "SELECT root_id FROM exercise_template WHERE creator_id = ? AND id = ?"
    r = database.query_with(connection, sql, [user_id, template_id])
    if not r:
        connection.close()
        return False
    root_id = r[0]["root_id"]
    try: 
        with connection:
            sql = """
            INSERT INTO exercise_template (creator_id, root_id, name, category, target_sets, target_reps)
            VALUES (?, ?, ?, ?, ?, ?)
            """
            c = connection.execute(sql, [
                user_id,
                root_id,
                name.strip(),
                category.strip() or None,
                target_sets,
                target_reps
            ])
            next_version_id = c.lastrowid
    
            sql = """
            UPDATE exercise_template
            SET next_version_id = ?
            WHERE id = ?
            """
            connection.execute(sql, [next_version_id, template_id])
        return True
    except Exception as e:
        print(f"SQLite Error: {e}")
        return False
    finally:
        connection.close()

def update_adopted_exercise_template(user_id: int, old_template_id: int, new_template_id: int) -> bool:
    sql = """
    UPDATE user_exercise_template 
    SET exercise_template_id = ? 
    WHERE user_id = ? AND exercise_template_id = ?
    """
    database.execute(sql, [new_template_id, user_id, old_template_id])
    return database.row_count() > 0

def delete_my_exercise_template(user_id: int, template_id: int) -> bool:
    connection = database.get_connection()
    if not connection:
        return False
    sql = "SELECT root_id FROM exercise_template WHERE creator_id = ? AND id = ?"
    r = database.query_with(connection, sql, [user_id, template_id])
    if not r:
        connection.close()
        return False
    root_id = r[0]["root_id"]
    sql = "DELETE FROM exercise_template WHERE creator_id = ? AND root_id = ?"
    row_count = database.execute_updel_with(connection, sql, [user_id, root_id])

    connection.close()
    return row_count > 0

def delete_adopted_exercise_template(user_id: int, template_id: int) -> bool: 
    sql = "DELETE FROM user_exercise_template WHERE user_id = ? AND exercise_template_id = ?"
    database.execute(sql, [user_id, template_id])
    return database.row_count() > 0

def delete_my_exercise_template_latest_version(user_id: int, template_id: int) -> bool:
    connection = database.get_connection()
    if not connection:
        return False
    sql = "SELECT id FROM exercise_template WHERE creator_id = ? AND next_version_id = ?"
    r = database.query_with(connection, sql, [user_id, template_id])
    if not r:
        connection.close()
        return False
    prev_template_id = r[0]["id"]
    try:
        with connection:
            sql = """
            UPDATE user_exercise_template 
            SET exercise_template_id = ? 
            WHERE exercise_template_id = ?
            """
            connection.execute(sql, [prev_template_id, template_id])

            sql = "UPDATE exercise_template SET next_version_id = NULL WHERE id = ?"
            connection.execute(sql, [prev_template_id])
    
            sql = "DELETE FROM exercise_template WHERE id = ?"
            connection.execute(sql, [template_id])
        return True
    except Exception as e:
        print(f"SQLite Error: {e}")
        return False
    finally:
        connection.close()

def delete_exercise_log(user_id: int, exercise_id: int) -> bool:
    sql = """
    DELETE FROM exercise_log
    WHERE id = ? 
    AND workout_id IN (
        SELECT id 
        FROM workout_log 
        WHERE user_id = ?
    )
    """
    database.execute(sql, [exercise_id, user_id])
    return database.row_count() > 0
