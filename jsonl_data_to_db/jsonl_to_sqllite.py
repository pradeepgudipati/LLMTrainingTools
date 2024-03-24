import json
import os
import sqlite3


def import_jsonl_to_sqlite(jsonl_path, sqlite_path):
    os.makedirs(os.path.dirname(sqlite_path), exist_ok=True)
    # Connect to SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()

    # Create a table with separate columns for user and assistant content
    cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY,
                user TEXT,
                assistant TEXT
            )
        """)

    # Read and insert data from JSONL file, mapping content to appropriate columns
    with open(jsonl_path, "r") as file:
        for line in file:
            data = json.loads(line)
            for message in data["messages"]:
                if message["role"] == "user":
                    user_msg = message["content"]
                elif message["role"] == "assistant":
                    assistant_msg = message["content"]

                    # Insert the pair of messages into the database
                    cursor.execute(
                        "INSERT INTO messages (user, assistant) VALUES (?, ?)",
                        (user_msg, assistant_msg),
                    )

                    # Reset the variables for the next pair
                    user_msg = None
                    assistant_msg = None

    # Commit changes and close the connection
    conn.commit()
    conn.close()


def test_jsonl_to_sqlite(json_path, sqlite_path):
    # Read data from JSONL file
    jsonl_data = []
    with open(json_path, "r") as file:
        for line in file:
            data = json.loads(line)
            user_msg = None
            assistant_msg = None
            for message in data["messages"]:
                if message["role"] == "user":
                    user_msg = message["content"]
                elif message["role"] == "assistant":
                    assistant_msg = message["content"]
            jsonl_data.append((user_msg, assistant_msg))

    # Read data from SQLite database
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    cursor.execute("SELECT user, assistant FROM messages")
    db_data = cursor.fetchall()
    conn.close()
    if jsonl_data == db_data:
        print("Length of Data is the same -- Copy successful")
    else:
        print("Length of Data is different -- Copy failed ")


jsonl_file_path = "data/qa_data.jsonl"
sqlite_db_path = "data/qa_data.db"

import_jsonl_to_sqlite(jsonl_file_path, sqlite_db_path)
# Verify that all Records are added to DB.
test_jsonl_to_sqlite(jsonl_file_path, sqlite_db_path)
