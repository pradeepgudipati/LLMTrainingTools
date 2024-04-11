import json
import os
import sqlite3


def sqlite_to_jsonl(sql_file_path, jsonl_path, table_name):
    print(f"sqllite_to_jsonl   sql_file_path: {sql_file_path} jsonl_path: {jsonl_path}")

    # Check if the SQLite database file exists
    if not os.path.exists(sql_file_path):
        print("Database file not found.")
        return False

    # Ensure the directory for the JSONL file exists
    os.makedirs(os.path.dirname(jsonl_path), exist_ok=True)

    try:
        # Connect to the SQLite database
        conn = sqlite3.connect(sql_file_path)
        cursor = conn.cursor()

        # Execute a query to fetch the data
        query = (
            f"SELECT User, Assistant FROM {table_name}"  # Replace with your table name
        )
        cursor.execute(query)
        # Print the number of rows fetched
        print(f"Number of rows fetched: {cursor.rowcount}")
        # Open a file to write
        with open(jsonl_path, "w") as file:
            for row in cursor.fetchall():
                # Format the row into the specified JSON structure
                data = {
                    "messages": [
                        {"role": "user", "content": row[0]},
                        {"role": "assistant", "content": row[1]},
                    ]
                }
                # Write the JSON object to the file
                file.write(json.dumps(data) + "\n")
        print(f"Data written to {jsonl_path}")
        # Close the database connection
        conn.close()
    except Exception as e:
        print(f"Exception: {e}")
        return False

# # Paths for the JSONL file and SQLite database
# jsonl_file_path = "data/qa_data.jsonl"
# sqlite_db_path = "data/merged_data.db"
# # print CWD
# print(f"CWD: {os.getcwd()}")
#
# # Call the function
# sqllite_to_jsonl(sqlite_db_path, jsonl_file_path, "messages")
