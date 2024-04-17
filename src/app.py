import os
from math import ceil

from flask import Flask, render_template, request, jsonify, session, app, redirect, url_for
from flask import send_file
from sqlalchemy import inspect

from data_tools.clean_data_in_db import clean_items
from data_tools.database_utils import backup_db
from data_tools.db_init import db
from data_tools.duplicate_checker import duplicate_checker_vectors
from data_tools.import_utils.csv_to_jsonl import convert_single_csv_to_jsonl
from data_tools.import_utils.db_to_jsonl import sqlite_to_jsonl
from data_tools.import_utils.jsonl_to_sqllite import import_jsonl_to_sqlite, test_jsonl_to_sqlite
from models.llm_training_data_model import LLMDataModel
from utils import validate_jsonl_file, validate_csv_file, save_file

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "data/qa_data.db")

# noinspection PyRedeclaration
app = Flask(__name__, template_folder="frontend/templates", static_folder="frontend/static")


# Set up the app with the database and default configurations
def create_app():
    """
    This function is used to create the app with the database and default configurations
    :return: app
    """
    app.config["SECRET_KEY"] = (
        "NFi2d0K45FYcX1ZXAXJ6NM"  # Change this to a random secret key
    )

    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + DB_PATH
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config['UPLOAD_FOLDER'] = 'user_uploads/jsonl/'
    try:
        db.init_app(app)
    except Exception as e:
        print(f"DB initializing Exception: {e}")


# API for getting the question and answer from the database
@app.route("/", methods=["GET"])
@app.route("/page/<int:page>", methods=["GET"])
def index(page=None):
    """
    This function is used to get the questions and answers from the database
    :param page: Page number
    :return:
    """
    # Initialize the search queries with values from session
    query_qa = session.get("query-qa", "")
    query_ans = session.get("query-ans", "")
    per_page = request.args.get(
        "per_page", default=session.get("per_page", 20), type=int
    )

    # Check for new search queries in the request
    if "query-qa" in request.args:
        query_qa = request.args.get("query-qa")
        if query_qa != session.get("query-qa", ""):
            session["query-qa"] = query_qa
            page = 1  # Reset page to 1 if there's a new search
    if "query-ans" in request.args:
        query_ans = request.args.get("query-ans")
        if query_ans != session.get("query-ans", ""):
            session["query-ans"] = query_ans
            page = 1  # Reset page to 1 if there's a new search

    # Set the page number
    if page is None:
        page = request.args.get("page", default=session.get("page", 1), type=int)

    # Save the session values.
    session["per_page"] = per_page
    session["page"] = page
    session["query-qa"] = query_qa
    session["query-ans"] = query_ans

    # Check if the 'messages' table exists
    inspector = inspect(db.engine)
    if 'messages' not in inspector.get_table_names():
        return jsonify(status="error", message="The messages table does not exist in the database."), 500

    # Ensure the page number is within the valid range
    total_items = LLMDataModel.query.count()
    total_pages = ceil(total_items / per_page)
    page = max(1, min(page, total_pages))

    # Construct the query based on filters
    query = LLMDataModel.query
    if query_qa:
        query = query.filter(LLMDataModel.question.contains(query_qa))
    if query_ans:
        query = query.filter(LLMDataModel.answer.contains(query_ans))

    # Apply pagination
    data = query.paginate(page=page, per_page=per_page, error_out=False)
    count = query.count()

    return render_template(
        "table_view.html",
        data=data,
        count=count,
        page=page,
        per_page=session["per_page"],
        query_qa=session["query-qa"],
        query_ans=session["query-ans"],
    )


# API for getting the question and answer from the database
@app.route("/save/<int:item_id>", methods=["POST"])
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
@app.route("/update_answer", methods=["POST"])
def update_answer():
    """
    This function is used to update the answer in the database
    :return: response
    """
    data = request.json
    print(f"API received {data}")
    item_id = data.get("item_id")
    content = data.get("content")

    # Update the content in the database based on 'item_id'
    item = LLMDataModel.query.get(item_id)
    print(f"Item: {item} , Assistant content -- {item.answer}")
    if item:
        item.answer = content
        db.session.commit()
        db.session.close()
        return jsonify(status="success", message=f"Answer for {item_id} updated successfully"), 200
    else:
        return jsonify(status="error", message=f"Item {item_id} not found"), 404


# API for adding the question to the database
@app.route("/add_question", methods=["POST"])
def add_new_qa():
    """
    This function is used to add the question and answer to the database
    :return: response
    """
    data = request.json
    new_item = LLMDataModel(user=data["question"], assistant=data["answer"])
    print(f"Adding new item: {new_item}")
    db.session.add(new_item)
    db.session.commit()
    return jsonify(status="success", message=f"New item added."), 200


# API for deleting the question from the database
@app.route("/delete_question/<int:item_id>", methods=["DELETE"])
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
@app.route("/update_question", methods=["POST"])
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
@app.route('/convert_jsonl_to_sqlite', methods=['POST'])
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
@app.route('/convert_csv_to_jsonl', methods=['POST'])
def csv_to_jsonl():
    """
    This function is used to convert the CSV file to JSONL
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
        csv_path = save_file(file, app.config['UPLOAD_FOLDER'])
        jsonl_path = "data_tools/import_utils/data/qa_data.jsonl"  # Replace with your JSONL file path
        try:
            if validate_csv_file(csv_path):
                convert_single_csv_to_jsonl(csv_path, jsonl_path)
                return send_file(jsonl_path, as_attachment=True)  # Send the SQLite file to the client
            else:
                return jsonify(status="error", message="Invalid CSV file."), 400
        except Exception as e:
            return jsonify(status="error", message=f"Error converting CSV to JSONL: CSV format issue - {e}"), 500


# API for exporting SQLite to JSONL
@app.route('/export_jsonl_from_sqlite', methods=['GET'])
def export_jsonl():
    """
    This function is used to export the SQLite database to JSONL
    :return: response
    """
    # Define the path to the SQLite database and the path where you want to save the JSONL file
    sql_file_path = os.path.join(BASE_DIR, "data/qa_data.db")
    print(f"BASE_DIR == {BASE_DIR}, sql_file_path: {sql_file_path}")
    jsonl_path = os.path.join(BASE_DIR, "data/qa_data.jsonl")
    print(f"jsonl_path: {jsonl_path}")
    table_name = "messages"  # Replace with your table name

    # Call the sqllite_to_jsonl function
    sqlite_to_jsonl(sql_file_path, jsonl_path, table_name)

    # Send the JSONL file to the client
    return send_file(jsonl_path, as_attachment=True)


# API for importing JSONL file to SQLite
@app.route('/import_jsonl_to_sqlite', methods=['POST'])
def jsonl_to_sqlite():
    """
    This function is used to import the JSONL file to SQLite
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
            jsonl_path = save_file(file, app.config['UPLOAD_FOLDER'])
            if validate_jsonl_file(jsonl_path):
                backup_db(DB_PATH)
                import_jsonl_to_sqlite(jsonl_path, "qa_data.db")
                return jsonify(status="success",
                               message=f"File successfully uploaded and data imported to SQLite."), 200
            else:
                return jsonify(status="error", message=f"Invalid JSONL file."), 400
        except Exception as e:
            return jsonify(status="error", message=f"Error importing JSONL to SQLite: JSONL format error - {e}"), 500


# API for checking duplicates in the questions or answers from the database.
# The API will have true or false in the request
@app.route('/duplicate_checker', methods=['GET'])
def duplicate_checker():
    """
    This function is used to check the duplicates in the questions or answers from the database
    :return: response
    """
    is_question = request.args.get('isQuestion', default="true").lower() == "true"
    print(f"Is Question: {is_question}")
    duplicate_checker_vectors(is_question)
    # TODO - Implement the duplicate items view in the UI.
    return jsonify(status="success", message=f"Duplicate Checker API called."), 200


# API for cleaning the questions or answers in the database
@app.route('/clean_items', methods=['POST'])
def clean_items_api():
    """
    This function is used to clean the questions or answers in the database
    :return: response
    """
    print(f"Request JSON: {request.json}")
    # First backup the database
    backup_db(DB_PATH)
    is_question = request.args.get('isQuestion', default="true").lower() == "true"
    wrong_string = request.json.get('wrong_string')
    is_question_str = request.json.get('isQuestion')
    print(f"Is Question: {is_question}, Wrong String: {wrong_string}, isQuestion_str: {is_question_str}")
    items, count = clean_items(wrong_string, is_question)
    print(f"Items: {items}, Count: {count}")
    # Convert items to a format that can be JSON serialized
    items_json = [item.to_dict() for item in items]  # Assuming each item has a to_dict() method
    db.session.commit()
    db.session.close()
    return jsonify(status="success", total_items=len(items_json), items_with_text=count,
                   message="Questions cleaned successfully."), 200


# Backup database and return the db file for download
@app.route('/backup_db', methods=['GET'])
def backup_database():
    """
    This function is used to back up the database
    :return: response
    """
    backup_file = backup_db(DB_PATH)
    return send_file(backup_file, as_attachment=True)


# API to restore a database from a backup file
@app.route('/restore_db', methods=['POST'])
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


if __name__ == "__main__":
    create_app()
    with app.app_context():
        db.create_all()  # This will create the database using the defined models
    app.run(debug=True)
