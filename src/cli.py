import os

from .app import DB_PATH, app, create_app
from .data_tools.database_utils import ensure_db_schema
from .data_tools.db_init import db


def serve():
    create_app()
    with app.app_context():
        db.create_all()
        ensure_db_schema(DB_PATH)

    app.run(
        host=os.environ.get("FLASK_RUN_HOST", "127.0.0.1"),
        port=int(os.environ.get("FLASK_RUN_PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "1") == "1",
    )


def main():
    serve()
