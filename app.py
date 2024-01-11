import os
from math import ceil

from flask import Flask, render_template, request, jsonify, session

from db_init import db
from llm_training_data_model import LLMDataModel

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
print(f"BASE_DIR: {BASE_DIR}")
# .. in the path means go up one directory
DB_PATH = os.path.join(BASE_DIR, '../jsonl_data_to_db/data/merged_data.db')
print(f"DB_PATH: {DB_PATH}")
app = Flask(__name__)
app.config['SECRET_KEY'] = 'NFi2d0K45FYcX1ZXAXJ6NM'  # Change this to a random secret key

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + DB_PATH
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
try:
    db.init_app(app)
except Exception as e:
    print(f"DB initializing Exception: {e}")


@app.route('/', methods=['GET'])
@app.route('/page/<int:page>', methods=['GET'])
def index(page=None):
    # Initialize the search queries with values from session
    query_qa = session.get('query-qa', '')
    query_ans = session.get('query-ans', '')
    per_page = request.args.get('per_page', default=session.get('per_page', 20), type=int)

    # Check for new search queries in the request
    if 'query-qa' in request.args:
        query_qa = request.args.get('query-qa')
        if query_qa != session.get('query-qa', ''):
            session['query-qa'] = query_qa
            page = 1  # Reset page to 1 if there's a new search
    if 'query-ans' in request.args:
        query_ans = request.args.get('query-ans')
        if query_ans != session.get('query-ans', ''):
            session['query-ans'] = query_ans
            page = 1  # Reset page to 1 if there's a new search

    # Set the page number
    if page is None:
        page = request.args.get('page', default=session.get('page', 1), type=int)

    # Save the session values.
    session['per_page'] = per_page
    session['page'] = page
    session['query-qa'] = query_qa
    session['query-ans'] = query_ans

    # Ensure the page number is within the valid range
    total_items = LLMDataModel.query.count()
    total_pages = ceil(total_items / per_page)
    page = max(1, min(page, total_pages))

    # Construct the query based on filters
    query = LLMDataModel.query
    if query_qa:
        query = query.filter(LLMDataModel.user.contains(query_qa))
    if query_ans:
        query = query.filter(LLMDataModel.assistant.contains(query_ans))

    # Apply pagination
    data = query.paginate(page=page, per_page=per_page, error_out=False)
    count = query.count()

    return render_template('table_view.html', data=data, count=count,
                           page=page,
                           per_page=session['per_page'],
                           query_qa=session['query-qa'],
                           query_ans=session['query-ans'])


@app.route('/save/<int:item_id>', methods=['POST'])
def save_content(item_id):
    content = request.form['content']
    item = LLMDataModel.query.get(item_id)
    if item:
        item.assistant = content
        db.session.commit()
        return jsonify(status="success", message="Content saved.")
    return jsonify(status="error", message="Item not found.")


@app.route('/update_answer', methods=['POST'])
def update_answer():
    data = request.json
    print(f"API received {data}")
    item_id = data.get('item_id')
    content = data.get('content')

    # Update the content in the database based on 'item_id'
    item = LLMDataModel.query.get(item_id)
    print(f"Item: {item} , Assistant content -- {item.assistant}")
    if item:
        item.assistant = content
        db.session.commit()
        db.session.close()
        return 'Content updated successfully', 200
    else:
        return 'Item not found', 404


@app.route('/add', methods=['POST'])
def add_new_qa():
    data = request.json
    new_item = LLMDataModel(user=data['user'], assistant=data['assistant'])
    print(f"Adding new item: {new_item}")
    db.session.add(new_item)
    db.session.commit()
    return jsonify(status="success", message="New item added.")


@app.route('/delete/<int:item_id>', methods=['DELETE'])
def delete_qa(item_id):
    print(f"Delete item_id: {item_id}")
    item = LLMDataModel.query.get(item_id)
    print(f"Deleting Item: {item}")

    if item is not None:
        db.session.delete(item)
        db.session.commit()
        return jsonify(status="success", message="Item deleted.")
    return jsonify(status="error", message="Item not found.")


@app.route('/update_question', methods=['POST'])
def update_question():
    data = request.json
    item_id = data.get('item_id')
    new_question = data.get('new_question')

    if not item_id or not new_question:
        return jsonify(status="error", message="Missing item ID or new question."), 400

    try:
        item = LLMDataModel.query.get(item_id)
        if not item:
            return jsonify(status="error", message="Item not found."), 404

        item.user = new_question
        db.session.commit()
        return jsonify(status="success", message="Question updated successfully.")
    except Exception as e:
        return jsonify(status="error", message=str(e)), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # This will create the database using the defined models
    app.run(debug=True)
