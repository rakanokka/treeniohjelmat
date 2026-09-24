from typing import Any
from database import query, execute
from werkzeug.security import check_password_hash, generate_password_hash

def get_user(user_id: int) -> Any:
    sql = 'SELECT id, username, password_hash FROM "user" WHERE id = ?'
    r = query(sql, [user_id])
    return r[0] if r else None

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
