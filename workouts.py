import database

def add_my_workout_template(user_id: int, name: str, description: str, tags: list[str], exercise_ids: list[int]):
    sql = "INSERT INTO workout_template (creator_id, name, description) VALUES (?, ?, ?)"
    template_id = database.execute_insert(sql, [
        user_id, 
        name.strip(), 
        description.strip() or None
    ])

    sql = "UPDATE workout_template SET root_id = ? WHERE id = ?"
    database.execute_updel(sql, [template_id, template_id])
    for tag in tags:
        sql = "INSERT OR IGNORE INTO tag (name) VALUES (?)"
        database.execute_insert(sql, [tag])
        sql = """
        INSERT OR IGNORE INTO workout_template_tag (workout_template_id, tag_id)
        VALUES (?, (SELECT id FROM tag WHERE name = ?))
        """
        database.execute_insert(sql, [template_id, tag])
    
    sql = """
    INSERT INTO workout_exercise_template 
    (workout_template_id, exercise_template_id, order_index)
    VALUES (?, ?, ?)
    """
    for order_index, exercise_id in enumerate(exercise_ids):    
        database.execute_insert(sql, [template_id, exercise_id, order_index])

def add_adopted_workout_template(user_id: int, template_id: int):
    sql = "INSERT INTO user_workout_template (user_id, workout_template_id) VALUES (?, ?)"
    database.execute_insert(sql, [user_id, template_id])

def add_workout_exercise_template(workout_template_id: int, exercise_template_id: int, order_index: int):
    sql = "INSERT INTO workout_exercise_template (workout_template_id, exercise_template_id, order_index) VALUES (?, ?, ?)"
    database.execute_insert(sql, [workout_template_id, exercise_template_id, order_index])

def add_workout_log(user_id: int, workout_template_id: int, name: str, description: str):
    sql = """
    INSERT INTO workout_log (user_id, workout_template_id, name, notes, started_at)
    VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
    """
    database.execute_insert(sql, [
        user_id, 
        workout_template_id, 
        name.strip(), 
        description.strip() or None
    ])

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
    database.execute_insert(sql, [
        workout_template_id,
        exercise_template_id,
        workout_template_id,
        workout_template_id,
        user_id
    ])

def add_exercise_to_workout_log(workout_id: int, exercise_template_id: int, name: str, reps: list[int], weights: list[float]):
    sql = """
    INSERT INTO exercise_log (workout_id, exercise_template_id, name)
    VALUES (?, ?, ?)
    """
    exercise_id = database.execute_insert(sql, [
        workout_id, 
        exercise_template_id, 
        name.strip()
    ])

    sql = """
    INSERT INTO exercise_set (exercise_id, order_index, reps, weight)
    VALUES (?, ?, ?, ?)
    """
    for order_index, (rep, weight) in enumerate(zip(reps, weights)):
        database.execute_insert(sql, [exercise_id, order_index, rep, weight])

def add_workout_template_comment(user_id: int, template_id: int, content: str):
    sql = "INSERT INTO user_comment (user_id, workout_template_id, content) VALUES (?, ?, ?)"
    return database.execute_insert(sql, [user_id, template_id, content])

def add_workout_template_tag(template_id: int, tag_id: int):
    sql = "INSERT INTO workout_template_tag (workout_template_id, tag_id) VALUES (?, ?)"
    return database.execute_insert(sql, [template_id, tag_id])

def get_previous_workout_template_id(template_id: int) -> int:
    sql = "SELECT root_id FROM workout_template WHERE id = ?"
    r = database.query(sql, [template_id])
    if not r:
        return template_id     
    root_id = r[0]["root_id"]
    if root_id == template_id:
        return template_id
    sql = "SELECT id FROM workout_template WHERE next_version_id = ?"
    database.query(sql, [template_id])
    return r[0]["id"]
        
def get_exercise_template(template_id: int) -> dict | None:
    sql = """
    SELECT 
        et.id AS exercise_template_id,
        et.name AS name,
        et.category AS category,
        et.target_sets AS sets,
        et.target_reps AS reps
    FROM exercise_template et
    JOIN "user" u
        ON et.creator_id = u.id
    WHERE et.id = ? 
    """ 
    r = database.query(sql, [template_id])
    return r[0] if r else None

def get_workout_template_previous_version_id(template_id: int) -> int | None:
    sql = "SELECT id FROM workout_template WHERE next_version_id = ?"
    r = database.query(sql, [template_id])
    return r[0]["id"] if r else None

def get_workout_template_next_version_id(template_id: int) -> int | None:
    sql = "SELECT next_version_id FROM workout_template WHERE id = ?"
    r = database.query(sql, [template_id])
    if r:
        return r[0]["next_version_id"] or None
    return None

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

def get_workout_template_exercises(workout_template_id: int) -> list[dict]:
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
    WHERE wet.workout_template_id = ?
    ORDER BY wet.order_index ASC, wet.id ASC
    """
    return database.query(sql, [workout_template_id])

def get_user_workout_template_exercises(user_id: int, workout_template_id: int) -> list[dict]:
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

def get_workout_template_creator_id(template_id: int) -> int | None:
    sql = "SELECT creator_id FROM workout_template WHERE id = ?"
    r = database.query(sql, [template_id])
    return r[0]["creator_id"] if r else None

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
        COUNT(DISTINCT uwt_all.user_id) AS user_count,
        CASE 
            WHEN NOT EXISTS (
                SELECT 1 FROM workout_template wt_prev WHERE wt_prev.next_version_id = wt.id
            ) THEN 1 
            ELSE 0 
        END AS is_root
    FROM workout_template wt
    JOIN "user" u 
        ON wt.creator_id = u.id
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    LEFT JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    LEFT JOIN workout_template wt_all 
        ON wt.root_id = wt_all.root_id
    LEFT JOIN user_workout_template uwt_all 
        ON wt_all.id = uwt_all.workout_template_id
    LEFT JOIN workout_log w 
        ON wt.id = w.workout_template_id AND w.user_id = ? 
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id 
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id 
    WHERE wt.creator_id = ? AND wt.next_version_id IS NULL
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
        COUNT(DISTINCT uwt_all.user_id) AS user_count,
        CASE WHEN wt.next_version_id IS NOT NULL THEN 1 ELSE 0 END AS has_next_version,
        CASE 
            WHEN NOT EXISTS (
                SELECT 1 FROM workout_template wt_prev WHERE wt_prev.next_version_id = wt.id
            ) THEN 1 
            ELSE 0 
        END AS is_root
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

def find_workout_templates_by_tag(tag: str) -> list[dict]:
    sql = """
    SELECT 
        wt.id AS id,
        wt.name AS name,
        wt.description AS description,
        wt.creator_id AS creator_id,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT t.name) AS tags,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        (SELECT COUNT(*) 
         FROM workout_exercise_template wet 
         WHERE wet.workout_template_id = wt.id) AS exercise_count
    FROM workout_template wt
    JOIN "user" u 
        ON wt.creator_id = u.id
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id 
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id 
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    LEFT JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    WHERE wt.next_version_id IS NULL 
        AND wt.id IN (
            SELECT wtt2.workout_template_id 
            FROM workout_template_tag wtt2 
            JOIN tag t2 ON wtt2.tag_id = t2.id 
            WHERE LOWER(t2.name) LIKE LOWER(?)
        )
    GROUP BY wt.id
    ORDER BY wt.name ASC 
    """
    return database.query(sql, [f"%{tag.strip()}%"])

def find_workout_templates_by_category(category: str) -> list[dict]:
    sql = """
    SELECT 
        wt.id AS id,
        wt.name AS name,
        wt.description AS description,
        wt.creator_id AS creator_id,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT t.name) AS tags,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        (SELECT COUNT(*) 
         FROM workout_exercise_template wet 
         WHERE wet.workout_template_id = wt.id) AS exercise_count
    FROM workout_template wt
    JOIN "user" u 
        ON wt.creator_id = u.id
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id 
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id 
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    LEFT JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    WHERE wt.next_version_id IS NULL 
        AND wt.id IN (
            SELECT wet2.workout_template_id 
            FROM workout_exercise_template wet2
            JOIN exercise_template et2 ON wet2.exercise_template_id = et2.id
            WHERE LOWER(et2.category) LIKE LOWER(?)
        )
    GROUP BY wt.id
    ORDER BY wt.name ASC 
    """
    return database.query(sql, [f"%{category.strip()}%"])

def find_workout_templates_by_name(name: str) -> list[dict]:
    sql = """
    SELECT 
        wt.id AS id,
        wt.name AS name,
        wt.description AS description,
        wt.creator_id AS creator_id,
        u.username AS creator_name,
        GROUP_CONCAT(DISTINCT t.name) AS tags,
        GROUP_CONCAT(DISTINCT et.category) AS categories,
        (SELECT COUNT(*) 
         FROM workout_exercise_template wet 
         WHERE wet.workout_template_id = wt.id) AS exercise_count
    FROM workout_template wt
    JOIN "user" u 
        ON wt.creator_id = u.id
    LEFT JOIN workout_template_tag wtt 
        ON wt.id = wtt.workout_template_id 
    LEFT JOIN tag t 
        ON wtt.tag_id = t.id 
    LEFT JOIN workout_exercise_template wet 
        ON wt.id = wet.workout_template_id
    LEFT JOIN exercise_template et 
        ON wet.exercise_template_id = et.id
    WHERE wt.next_version_id IS NULL 
        AND LOWER(wt.name) LIKE LOWER(?)
    GROUP BY wt.id
    ORDER BY wt.name ASC 
    """
    return database.query(sql, [f"%{name.strip()}%"])

def get_all_workout_template_ids(user_id: int) -> list[int]:
    sql = """
    SELECT id FROM workout_template WHERE creator_id = ?
    UNION
    SELECT workout_template_id AS id FROM user_workout_template WHERE user_id = ?
    """
    rows = database.query(sql, [user_id, user_id])
    return [row["id"] for row in rows]

def get_workout_template_name(template_id: int) -> str | None:
    sql = "SELECT name FROM workout_template WHERE id = ?"
    r = database.query(sql, [template_id])
    return r[0]["name"] if r else None

def get_workout_log_user_id(workout_id: int) -> int | None:
    sql = "SELECT user_id FROM workout_log WHERE id = ?"
    r = database.query(sql, [workout_id])
    return r[0]["user_id"] if r else None

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

def update_my_workout_template(user_id: int, template_id: int, name: str, description: str, tags: list[str], exercise_template_ids: list[int]):
    sql = "SELECT root_id FROM workout_template WHERE id = ? AND creator_id = ?"
    r = database.query(sql, [template_id, user_id])
    if not r:
        return
    
    root_id = r[0]["root_id"]
    sql = """
    INSERT INTO workout_template (creator_id, root_id, name, description)
    VALUES (?, ?, ?, ?)
    """
    next_version_id = database.execute_insert(sql, [
        user_id,
        root_id,
        name.strip(),
        description.strip() or None
    ])
    if not next_version_id:
        return

    sql = """
    UPDATE workout_template
    SET next_version_id = ?
    WHERE id = ?
    """
    database.execute_updel(sql, [next_version_id, template_id])
    
    for tag in tags:
        sql = "INSERT OR IGNORE INTO tag (name) VALUES (?)"
        database.execute_insert(sql, [tag])
        sql = """
        INSERT INTO workout_template_tag (workout_template_id, tag_id)
        VALUES (?, (SELECT id FROM tag WHERE name = ?))
        """
        database.execute_insert(sql, [next_version_id, tag])
    
    sql = """
    INSERT INTO workout_exercise_template 
    (workout_template_id, exercise_template_id, order_index)
    VALUES (?, ?, ?)
    """
    for order_index, exercise_template_id in enumerate(exercise_template_ids):    
        database.execute_insert(sql, [next_version_id, exercise_template_id, order_index])    

def update_adopted_workout_template(user_id: int, old_template_id: int, new_template_id: int):
    sql = """
    UPDATE user_workout_template 
    SET workout_template_id = ? 
    WHERE user_id = ? AND workout_template_id = ?
    """
    database.execute_updel(sql, [new_template_id, user_id, old_template_id])

def delete_my_workout_template(user_id: int, template_id: int):
    sql = "SELECT root_id FROM workout_template WHERE creator_id = ? AND id = ?"
    r = database.query(sql, [user_id, template_id])
    if not r:
        return
    root_id = r[0]["root_id"]
    sql = "DELETE FROM workout_template WHERE creator_id = ? AND root_id = ?"
    database.execute_updel(sql, [user_id, root_id])

def delete_my_workout_template_latest_version(user_id: int, template_id: int):
    sql = "SELECT id FROM workout_template WHERE creator_id = ? AND next_version_id = ?"
    r = database.query(sql, [user_id, template_id])
    if not r:
        return
    prev_template_id = r[0]["id"]
    sql = """
    UPDATE user_workout_template 
    SET workout_template_id = ? 
    WHERE workout_template_id = ?
    """
    database.execute_updel(sql, [prev_template_id, template_id])

    sql = "UPDATE workout_template SET next_version_id = NULL WHERE id = ?"
    database.execute_updel(sql, [prev_template_id])
    
    sql = "DELETE FROM workout_template WHERE id = ?"
    database.execute_updel(sql, [template_id])

def delete_adopted_workout_template(user_id: int, template_id: int):
    sql = "DELETE FROM user_workout_template WHERE user_id = ? AND workout_template_id = ?"
    database.execute_updel(sql, [user_id, template_id])

def delete_workout_log(user_id: int, workout_id: int):
    sql = """
    DELETE FROM workout_log
    WHERE id = ? AND user_id = ?
    """
    database.execute_updel(sql, [workout_id, user_id])

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
    database.execute_updel(sql, [
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
    database.execute_updel(sql, [exercise_id, workout_id])
