import csv
import datetime
import json
import os
import sqlite3

from werkzeug.utils import secure_filename

from src.models.llm_training_data_model import LLMDataModel


# Validate the CSV file
def validate_csv_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        if headers != ['question', 'answer']:
            return False
        for row in reader:
            if len(row) != 2:
                return False
    return True


# Validate the JSONL file
def validate_jsonl_file(file_path):
    with open(file_path, 'r') as file:
        for line in file:
            data = json.loads(line)
            if 'messages' not in data:
                return False
            messages = data['messages']
            if len(messages) != 2:
                return False
            if not all('role' in message and 'content' in message for message in messages):
                return False
            roles = [message['role'] for message in messages]
            if roles != ['user', 'assistant']:
                return False
    return True


# Save file to folder
def save_file(file, folder):
    filename = secure_filename(file.filename)
    if not os.path.exists(folder):
        os.makedirs(folder)
        print("Directory ", folder, " Created ")
    file_path = os.path.join(folder, filename)
    file.save(file_path)
    return file_path


# Get all items from the database
def get_all_items(model=LLMDataModel):
    total_items = model.query.all()
    total_items_count = model.query.count()
    print(f"Total Items: {total_items_count}")
    return total_items


# Backup the SQLite database
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
    os.system(f'cp {backup_file} {db_path}')
    print(f"Database restored from {backup_file}")
    return db_path
