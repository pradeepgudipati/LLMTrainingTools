import json
import os
import re
import sqlite3

TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def sqlite_to_jsonl(sql_file_path, jsonl_path, table_name):
    print(f"sqllite_to_jsonl sql_file_path: {sql_file_path} jsonl_path: {jsonl_path}")

    if not os.path.exists(sql_file_path):
        print("Database file not found.")
        return False
    if not TABLE_RE.match(table_name):
        print("Invalid table name.")
        return False

    os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)

    try:
        conn = sqlite3.connect(sql_file_path)
        cursor = conn.cursor()
        column_names = {
            row[1] for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
        }
        select_columns = "question, answer"
        if "payload" in column_names:
            select_columns = "question, answer, payload"

        cursor.execute(f"SELECT {select_columns} FROM {table_name}")
        print(f"Number of rows fetched: {cursor.rowcount}")
        with open(jsonl_path, "w", encoding="utf-8") as file:
            for row in cursor.fetchall():
                payload = row[2] if len(row) > 2 else None
                if payload:
                    data = json.loads(payload)
                else:
                    data = {
                        "messages": [
                            {"role": "user", "content": row[0]},
                            {"role": "assistant", "content": row[1]},
                        ]
                    }
                file.write(json.dumps(data, ensure_ascii=False) + "\n")
        print(f"Data written to {jsonl_path}")
        conn.close()
        return True
    except (sqlite3.DatabaseError, json.JSONDecodeError, OSError) as error:
        print(f"Exception: {error}")
        return False
