import os
import time

from flask import Flask, render_template, request, jsonify, session, app, redirect, url_for
from flask import send_file

from data_tools.clean_data_in_db import clean_items
from data_tools.database_utils import backup_db
from data_tools.db_init import db
from data_tools.dup_checker_chromadb import duplicate_checker_chromadb
from data_tools.duplicate_checker import duplicate_checker_vectors
from data_tools.import_utils.csv_to_jsonl import convert_single_csv_to_jsonl
from data_tools.import_utils.db_to_jsonl import sqlite_to_jsonl
from data_tools.import_utils.jsonl_to_sqllite import import_jsonl_to_sqlite, test_jsonl_to_sqlite
from models.llm_training_data_model import LLMDataModel
from src.ai_api import call_openai_sdk
from utils import validate_jsonl_file, validate_csv_file, save_file

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data/qa_data.db")

# noinspection PyRedeclaration
app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")

# variables
page_num = 1
per_page = 50
total_pages = 1
query_qa = ""
query_ans = ""


# Set up the app with the database and default configurations
def create_app():
    """
    This function is used to create the app with the database and default configurations
    :return: app
    """
    app.config["SECRET_KEY"] = "NFi2d0K45FYcX1ZXAXJ6NM"  # Change this to a random secret key

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['UPLOAD_FOLDER_JSONL'] = 'user_uploads/jsonl/'
    app.config['UPLOAD_FOLDER_CSV'] = 'user_uploads/csv/'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    try:
        db.init_app(app)
    except Exception as e:
        print(f"DB initializing Exception: {e}")


# API for getting the question and answer from the database
@app.route("/", methods=["GET"])
@app.route("/api/ui/page/<int:page>", methods=["GET"])
def index(page=None):
    """
    This function is used to get the questions and answers from the database
    :param page: Page number
    :return:
    """
    global page_num, per_page, total_pages, query_qa, query_ans
    # Get the session variables for page and per_page and set them as the default values
    page_num = request.args.get('page', default=session.get('page', 1), type=int)
    per_page = session.get("per_page", 50)
    total_pages = session.get("total_pages", 1)
    query_qa = session.get("query-qa", "")
    query_ans = session.get("query-ans", "")
    print(f"INDEX ::: Page: {page_num}, Per Page: {per_page}, Total Pages: {total_pages}, Query QA: {query_qa}, ")
    # Initialize the search queries with values from session
    data, count, per_page, page, total_pages, query_qa, query_ans = get_data()
    return render_template(
        "table_view.html",
        data=data,
        count=count,
        total_pages=total_pages,
        page=page,
        per_page=per_page,
        query_qa=query_qa,
        query_ans=query_ans,
    )


@app.route("/api/data", methods=["GET"])
def api_data():
    global page_num, per_page, total_pages, query_qa, query_ans
    # Get the session variables for page and per_page and set them as the default values
    page_num = request.args.get('page', default=session.get('page', 1), type=int)
    per_page = request.args.get("per_page", default=50, type=int)
    query_qa = request.args.get("query_qa", "")
    query_ans = request.args.get("query_ans", "")
    print(f"api_data ::: Page: {page_num}, Per Page: {per_page}, Query QA: {query_qa}, Query Ans: {query_ans}")

    data, count, per_page, page, total_pages, query_qa, query_ans = get_data()
    # Convert the data to a format that can be JSON serialized
    # items = [item.to_dict() for item in data]  # Assuming each item has a to_dict() method

    # Return the data as JSON
    return jsonify(count=count, page_num=page, per_page_num=per_page, total_pages=total_pages, qa_query_txt=query_qa,
                   ans_query_txt=query_ans, items=data)


def get_data():
    """
    This function is used to get the data from the database
    :return: count of items, per page, page number, query_qa, query_ans and array of objects
    """
    # Initialize the search queries with values from session
    # Construct the query based on filters
    global page_num, per_page, total_pages, query_qa, query_ans
    print(f"GET DATA ::: Query QA: {query_qa}, Query Ans: {query_ans}, Page: {page_num}, Per Page: {per_page}")
    query = LLMDataModel.query
    if query_qa:
        query = query.filter(LLMDataModel.question.contains(query_qa))
    if query_ans:
        query = query.filter(LLMDataModel.answer.contains(query_ans))

    # Apply pagination
    data = query.paginate(page=page_num, per_page=per_page, error_out=False)
    count = query.count()

    # Convert the data to a format that can be JSON serialized
    items = [item.to_dict() for item in data.items]  # Assuming each item has a to_dict() method
    total_pages = max(1, count / per_page)

    # Verify that the page number is valid
    if page_num < 1:
        page_num = 1
    if total_pages < page_num:
        page_num = total_pages

    return items, count, per_page, page_num, total_pages, query_qa, query_ans


# API for getting the question and answer from the database
@app.route("/api/save/<int:item_id>", methods=["POST"])
def save_content(item_id):
    """
    This function is used to save the content in the database
    :param item_id: item id
    :return: response
    """
    content = request.form["content"]
    item = LLMDataModel.query.get(item_id)
    if item:
        item.answer = content
        db.session.commit()
        return jsonify(status="success", message=f"Content for row {item_id} saved."), 200
    return jsonify(status="error", message=f"Item {item_id} not found."), 400


# API for updating the answer in the database
@app.route("/api/update_answer", methods=["POST"])
def update_answer():
    """
    This function is used to update the answer in the database
    :return: response
    """
    data = request.json
    item_id = data.get("item_id")
    content = data.get("content")

    # Update the content in the database based on 'item_id'
    item = LLMDataModel.query.get(item_id)
    if item:
        item.answer = content
        db.session.commit()
        db.session.close()
        return jsonify(status="success", message=f"Answer for {item_id} updated successfully"), 200
    else:
        return jsonify(status="error", message=f"Item {item_id} not found"), 404


# API for adding the question to the database
@app.route("/api/add_question", methods=["POST"])
def add_new_qa():
    """
    This function is used to add the question and answer to the database
    :return: response
    """
    data = request.json
    new_item = LLMDataModel(question=data["question"], answer=data["answer"])
    db.session.add(new_item)
    db.session.commit()
    return jsonify(status="success", message=f"New item added."), 200


# API for deleting the question from the database
@app.route("/api/delete_question/<int:item_id>", methods=["DELETE"])
def delete_qa(item_id):
    """
    This function is used to delete the question and answer from the database
    :param item_id: item id
    :return: response
    """
    item = LLMDataModel.query.get(item_id)

    if item is not None:
        db.session.delete(item)
        db.session.commit()
        return jsonify(status="success", message=f"Item {item_id} deleted.")
    return jsonify(status="error", message=f"Item {item_id} not found."), 400


# API for updating the question in the database
@app.route("/api/update_question", methods=["POST"])
def update_question():
    """
    This function is used to update the question in the database
    :return: response
    """
    data = request.json
    item_id = data.get("item_id")
    new_question = data.get("new_question")

    if not item_id or not new_question:
        return jsonify(status="error", message="Missing item ID or new question."), 400

    try:
        item = LLMDataModel.query.get(item_id)
        if not item:
            return jsonify(status="error", message=f"Item {item_id} not found."), 404

        item.question = new_question
        db.session.commit()
        return jsonify(status="success", message=f"Question for row {item_id} updated successfully."), 200
    except Exception as ex:
        return jsonify(status="error", message=f"Update Question error :: {ex}"), 500


# API for converting JSONL to SQLite
@app.route('/api/convert_jsonl_to_sqlite', methods=['POST'])
def jsonl_to_db():
    """
    This function is used to convert the JSONL file to SQLite
    :return: response
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify(status="error", message="No file part in the request."), 400

    file = request.files['file']

    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify(status="error", message="No selected file."), 400

    if file:
        upload_folder = app.config['UPLOAD_FOLDER']
        jsonl_path = save_file(file, upload_folder)

        try:
            backup_db(DB_PATH)
            import_jsonl_to_sqlite(jsonl_path, DB_PATH)
            test_jsonl_to_sqlite(jsonl_path, DB_PATH)
            backup_db(DB_PATH)
            jsonify(status="success", message=f"File successfully uploaded and data imported to SQLite."), 200
        except Exception as e:
            return jsonify(status="error", message=f"Error converting JSONL to SQLite: {e}"), 500
    #     Now refresh the page
    return redirect(url_for('index'))


# API for converting CSV to JSONL
@app.route('/api/convert_csv_to_jsonl', methods=['POST'])
def csv_to_jsonl():
    """
    This function is used to convert the CSV file to JSONL
    :return: response
    """
    print("Request data ::", request)
    print("Request data ::", request.files)
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify(status="error", message=f"No File uploaded"), 400

    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify(status="error", message=f"No selected file."), 400

    if file:
        csv_file_path = os.path.join(app.config['UPLOAD_FOLDER_CSV'], file.filename)
        if os.path.exists(csv_file_path):
            os.remove(csv_file_path)
        csv_path = save_file(file, app.config['UPLOAD_FOLDER_CSV'])
        output_jsonl_path = os.path.join(app.config['UPLOAD_FOLDER_JSONL'], "downloads/training_data.jsonl")
        print(f"CSV Path: {csv_path}, Output JSONL Path: {output_jsonl_path}")
        try:
            if validate_csv_file(csv_path):
                try:
                    convert_single_csv_to_jsonl(csv_path, output_jsonl_path)
                    # Send the JSONL file to the client
                    time.sleep(3)
                    if os.path.exists(output_jsonl_path) and os.access(output_jsonl_path, os.R_OK):
                        file = open(output_jsonl_path, 'rb')
                        return send_file(file, as_attachment=True, download_name="training_data.jsonl",
                                         mimetype="application/jsonl")
                    else:
                        print(f"File not present at the location: {output_jsonl_path}")
                except Exception as e:
                    return jsonify(status="error", message=f"Error converting CSV to JSONL: {e}"), 500
            else:
                return jsonify(status="error", message="Invalid CSV file."), 400
        except Exception as e:
            print(f"Error converting CSV to JSONL: {e}")
            return jsonify(status="error", message=f"Error converting CSV to JSONL: CSV format issue - {e}"), 500


# API for importing JSONL file to SQLite
@app.route('/api/import_jsonl_to_sqlite', methods=['POST'])
def jsonl_to_sqlite():
    """
    This function is used to import the JSONL file to SQLite
    :return: response
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify(status="error", message=f"No File uploaded"), 400

    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify(status="error", message=f"No selected file."), 400

    if file:
        try:
            jsonl_path = save_file(file, app.config['UPLOAD_FOLDER_JSONL'])
            if validate_jsonl_file(jsonl_path):
                backup_db(DB_PATH)
                import_jsonl_to_sqlite(jsonl_path, "qa_data.db")
                return jsonify(status="success",
                               message=f"File successfully uploaded and data imported to SQLite."), 200
            else:
                return jsonify(status="error", message=f"Invalid JSONL file."), 400
        except Exception as e:
            return jsonify(status="error", message=f"Error importing JSONL to SQLite: JSONL format error - {e}"), 500


# API for exporting SQLite to JSONL
@app.route('/api/export_jsonl_from_sqlite', methods=['GET'])
def export_jsonl():
    """
    This function is used to export the SQLite database to JSONL
    :return: response
    """
    # Define the path to the SQLite database and the path where you want to save the JSONL file
    sql_file_path = os.path.join(BASE_DIR, "data/qa_data.db")
    jsonl_path = os.path.join(BASE_DIR, "data/qa_data.jsonl")
    table_name = "messages"  # Replace with your table name

    # Call the sqlite_to_jsonl function
    sqlite_to_jsonl(sql_file_path, jsonl_path, table_name)

    # Send the JSONL file to the client
    return send_file(jsonl_path, as_attachment=True)


# API for checking duplicates in the questions or answers from the database.
# The API will have true or false in the request
@app.route('/api/duplicate_checker', methods=['GET'])
def duplicate_checker():
    """
    This function is used to check the duplicates in the questions or answers from the database
    :return: response
    """
    is_question = request.args.get('isQuestion', default="true").lower() == "true"
    count, dupl_list_file_path = duplicate_checker_vectors(is_question)
    # TODO - Implement the duplicate items view in the UI.
    return jsonify(status="success",
                   message=f"Duplicate Check completed. Found {count} duplicates. \n File name - {dupl_list_file_path}"), 200


# API for checking duplicates in the questions or answers from the database.
# The API will have true or false in the request
@app.route('/api/v2/duplicate_checker', methods=['GET'])
def duplicate_checker_fs():
    """
    This function is used to check the duplicates in the questions or answers from the database
    :return: response
    """
    is_question = request.args.get('isQuestion', default="true").lower() == "true"
    count, dupl_list_file_path = duplicate_checker_chromadb(is_question)
    # TODO - Implement the duplicate items view in the UI.
    return jsonify(status="success",
                   message=f"Duplicate Check completed. Found {count} duplicates. \n File name - {dupl_list_file_path}"), 200


# API for cleaning the questions or answers in the database
@app.route('/api/clean_items', methods=['POST'])
def clean_items_api():
    """
    This function is used to clean the questions or answers in the database
    :return: response
    """
    # First backup the database
    backup_db(DB_PATH)
    is_question = request.args.get('isQuestion', default="true").lower() == "true"
    wrong_string = request.json.get('wrong_string')
    is_question_str = request.json.get('isQuestion')
    items, count = clean_items(wrong_string, is_question)
    # Convert items to a format that can be JSON serialized
    items_json = [item.to_dict() for item in items]  # Assuming each item has a to_dict() method
    db.session.commit()
    db.session.close()
    return jsonify(status="success", total_items=len(items_json), items_with_text=count,
                   message="Questions cleaned successfully."), 200


# Backup database and return the db file for download
@app.route('/api/backup_db', methods=['GET'])
def backup_database():
    """
    This function is used to back up the database
    :return: response
    """
    backup_file = backup_db(DB_PATH)
    return send_file(backup_file, as_attachment=True)


# API to restore a database from a backup file
@app.route('/api/restore_db', methods=['POST'])
def restore_database():
    """
    This function is used to restore the database from a backup file
    :return: response
    """
    # Check if the post request has the file part
    if 'file' not in request.files:
        return jsonify(status="error", message=f"No file part in the request."), 400

    file = request.files['file']
    # If the user does not select a file, the browser submits an
    # empty file without a filename.
    if file.filename == '':
        return jsonify(status="error", message=f"No selected file."), 400

    if file:
        try:
            backup_file_path = save_file(file, app.config['UPLOAD_FOLDER'])
            # Now replace the current DB with the backup
            restored_db_path = backup_db(DB_PATH)
            return send_file(restored_db_path, as_attachment=True)
        except Exception as e:
            return jsonify(status="error", message=f"Error restoring database: {e}"), 500


@app.route('/qa_generator')
def qa_generator():
    """
    This function is used to generate the question and answer
    :return: response
    """
    return render_template("qa_generator.html")


@app.route('/api/openai/qa_generator', methods=['POST'])
def openai_qa_generator():
    """
    This function is used to generate the question and answer using the OpenAI API
    The API calls the call_openai_sdk function from ai_api.py
    :return: response
    """
    data = request.json['input_text']
    result = call_openai_sdk(data)
    return jsonify(status="success", message=f"Question and Answer generated successfully.", result=result), 200


if __name__ == "__main__":
    create_app()
    with app.app_context():
        db.create_all()  # This will create the database using the defined models
    app.run(debug=True)
