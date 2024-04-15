import json
import logging
import os
import sqlite3


def import_jsonl_to_sqlite(jsonl_path, sqlite_part_path):
    print(f"import_jsonl_to_sqlite   jsonl_path: {jsonl_path} \n sqlite_path: {sqlite_part_path}")
    #  Get current working directory and then append the path to the sqlite database
    cwd = os.getcwd()
    print(f"cwd: {cwd}")
    sqlite_full_path = os.path.join(cwd, "src/data", sqlite_part_path)
    print(f"Finally sqlite_path: {sqlite_full_path}")
    # Create a SQLite database and table
    os.makedirs(os.path.dirname(sqlite_full_path), exist_ok=True)
    conn = sqlite3.connect(sqlite_full_path)
    cursor = conn.cursor()
    table_exists = cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='messages'").fetchone()
    print(f"table_exists: {table_exists}")
    # if the table does not exist, create it else drop the table and recreate it
    if table_exists is not None:
        cursor.execute("DROP TABLE messages")
        conn.commit()
        print("Table dropped")

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question TEXT,
                answer TEXT
            )
        """)
    print("Table created")

    lines_read = 0
    insertions_attempted = 0
    with open(jsonl_path, "r") as file:
        for line in file:
            lines_read += 1
            try:
                data = json.loads(line)
                question_msg = ''
                answer_msg = ''
                for message in data["messages"]:
                    if message["role"] == "user":
                        question_msg = message["content"]
                    elif message["role"] == "assistant":
                        answer_msg = message["content"]
                if question_msg and answer_msg:
                    # print(f"Inserting: {question_msg}, {answer_msg}")
                    cursor.execute(
                        "INSERT INTO messages (question, answer) VALUES (?, ?)",
                        (question_msg, answer_msg),
                    )
                    insertions_attempted += 1
                # print(f"Number of rows inserted: {cursor.rowcount}")
            except Exception as e:
                logging.error(f"Error inserting data: {e}")
                continue

    try:
        conn.commit()
    except Exception as e:
        logging.error(f"Error committing transaction: {e}")

    conn.close()
    print(f"Data written to lines_read: {lines_read}, insertions_attempted: {insertions_attempted}")
    return lines_read, insertions_attempted


def test_jsonl_to_sqlite(json_path, sqlite_path):
    # Read data from JSONL file
    jsonl_data = []
    with open(json_path, "r") as file:
        for line in file:
            data = json.loads(line)
            question_msg = None
            answer_msg = None
            for message in data["messages"]:
                if message["role"] == "user":
                    question_msg = message["content"]
                elif message["role"] == "assistant":
                    answer_msg = message["content"]
            jsonl_data.append((question_msg, answer_msg))

    # Read data from SQLite database
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute("SELECT question, answer FROM messages")
    db_data = cursor.fetchall()
    conn.close()
    if jsonl_data == db_data:
        print("Length of Data is the same -- Copy successful")
    else:
        print("Length of Data is different -- Copy failed ")

# jsonl_file_path = "data/qa_data.jsonl"
# sqlite_db_path = "data/qa_data.db"
#
# import_jsonl_to_sqlite(jsonl_file_path, sqlite_db_path)
# # Verify that all Records are added to DB.
# test_jsonl_to_sqlite(jsonl_file_path, sqlite_db_path)
