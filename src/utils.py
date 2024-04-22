import csv
import json
import os

from werkzeug.utils import secure_filename


# Validate the CSV file
def validate_csv_file(file_path):
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        headers = next(reader)
        if headers != ['Question', 'Answer']:
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
