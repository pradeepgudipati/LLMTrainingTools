# Get all items from the database
import datetime
import os
import shutil
import sqlite3

from ..models.llm_training_data_model import LLMDataModel
from .import_utils.jsonl_to_sqllite import ensure_messages_schema


# Function to get all items from the database
def get_all_items(model=LLMDataModel):
    total_items = model.query.all()
    total_items_count = model.query.count()
    print(f"Total Items: {total_items_count}")
    return total_items


# Backup the SQLite database to a file
def backup_db(db_path):
    # backup file name with time stamp
    backup_file_name = 'llm_training_data_' + datetime.datetime.now().strftime("%d_%b_%y_t%H_%M") + '.db'
    backup_path = os.path.join(os.path.dirname(db_path), 'backup')
    if not os.path.exists(backup_path):
        os.makedirs(backup_path)
        print("Directory ", backup_path, " Created ")
    backup_file = os.path.join(backup_path, backup_file_name)
    # Connect to the current database
    conn = sqlite3.connect(db_path)
    # Connect to the backup database
    b_conn = sqlite3.connect(backup_file)
    # Use the backup() method to create a backup
    conn.backup(b_conn)
    # Close the connections
    b_conn.close()
    conn.close()

    print(f"Database backed up to {backup_file}")
    return backup_file


# Restore the selected SQLite database
def restore_db(db_path, backup_file):
    shutil.copy2(backup_file, db_path)
    print(f"Database restored from {backup_file}")
    return db_path


def ensure_db_schema(db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        ensure_messages_schema(conn)
    finally:
        conn.close()
