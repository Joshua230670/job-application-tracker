import json
import os

import mysql.connector


def get_db():
    # Open a new connection to the job_tracker database.
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD", ""),
        database=os.environ.get("DB_NAME", "job_tracker"),
    )


def fetch_all(sql, params=()):
    # Run a SELECT and return every row as a dict.
    conn = get_db()
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql, params)
        return cursor.fetchall()
    finally:
        conn.close()


def fetch_one(sql, params=()):
    # Run a SELECT and return the first row as a dict (or None).
    rows = fetch_all(sql, params)
    return rows[0] if rows else None


def execute(sql, params=()):
    # Run an INSERT/UPDATE/DELETE, commit, and return the new row id.
    conn = get_db()
    try:
        cursor = conn.cursor()
        cursor.execute(sql, params)
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def load_json(value):
    #Turn a JSON column value into Python data.
    if value is None:
        return None
    if isinstance(value, (bytes, bytearray)):
        value = value.decode("utf-8")
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return None
    return value
