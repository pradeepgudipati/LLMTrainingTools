import json
import logging
import os
import sqlite3

from ..dataset_validation import normalize_record, validate_jsonl_records


def resolve_sqlite_path(sqlite_path):
    if os.path.isabs(sqlite_path):
        return sqlite_path
    return os.path.join(os.getcwd(), "src/data", sqlite_path)


def ensure_messages_schema(conn):
    cursor = conn.cursor()
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT,
                dataset_type TEXT DEFAULT 'chat',
                payload TEXT,
                validation_errors TEXT,
                validation_warnings TEXT
            )
        """)

    existing_columns = {
        row[1] for row in cursor.execute("PRAGMA table_info(messages)").fetchall()
    }
    columns = {
        "dataset_type": "TEXT DEFAULT 'chat'",
        "payload": "TEXT",
        "validation_errors": "TEXT",
        "validation_warnings": "TEXT",
    }
    for column_name, column_type in columns.items():
        if column_name not in existing_columns:
            cursor.execute(f"ALTER TABLE messages ADD COLUMN {column_name} {column_type}")
    conn.commit()


def import_jsonl_to_sqlite(jsonl_path, sqlite_part_path):
    print(
        "import_jsonl_to_sqlite "
        f"jsonl_path: {jsonl_path} sqlite_path: {sqlite_part_path}"
    )
    sqlite_full_path = resolve_sqlite_path(sqlite_part_path)
    print(f"Finally sqlite_path: {sqlite_full_path}")
    os.makedirs(os.path.dirname(sqlite_full_path), exist_ok=True)
    conn = sqlite3.connect(sqlite_full_path)
    cursor = conn.cursor()
    ensure_messages_schema(conn)
    cursor.execute("DELETE FROM messages")
    print("Table ready")

    lines_read = 0
    insertions_attempted = 0
    for normalized in validate_jsonl_records(jsonl_path):
        lines_read += 1
        try:
            if normalized["errors"]:
                logging.warning(
                    "Skipping line %s due to validation errors: %s",
                    normalized["line_number"],
                    normalized["errors"],
                )
                continue

            cursor.execute(
                """
                INSERT INTO messages (
                    question,
                    answer,
                    dataset_type,
                    payload,
                    validation_errors,
                    validation_warnings
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized["question"],
                    normalized["answer"],
                    normalized["dataset_type"],
                    json.dumps(normalized["payload"], ensure_ascii=False),
                    json.dumps(normalized["errors"]),
                    json.dumps(normalized["warnings"]),
                ),
            )
            insertions_attempted += 1
        except (sqlite3.DatabaseError, TypeError, ValueError) as error:
            logging.error("Error inserting data: %s", error)
            continue

    try:
        conn.commit()
    except sqlite3.DatabaseError as error:
        logging.error("Error committing transaction: %s", error)

    conn.close()
    print(
        "Data written to "
        f"lines_read: {lines_read}, insertions_attempted: {insertions_attempted}"
    )
    return lines_read, insertions_attempted


def test_jsonl_to_sqlite(json_path, sqlite_path):
    jsonl_data = []
    with open(json_path, "r", encoding="utf-8") as file:
        for line in file:
            normalized = normalize_record(json.loads(line))
            if not normalized["errors"]:
                jsonl_data.append((normalized["question"], normalized["answer"]))

    conn = sqlite3.connect(resolve_sqlite_path(sqlite_path))
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM messages")
    db_data = cursor.fetchall()
    conn.close()
    if jsonl_data == db_data:
        print("Length of Data is the same -- Copy successful")
    else:
        print("Length of Data is different -- Copy failed ")
