import os
import subprocess
import sys


def test_app_starts_with_empty_temp_database(tmp_path):
    db_path = tmp_path / "app.db"
    code = """
import os
os.environ["LLMTOOLS_DB_PATH"] = r"{db_path}"
os.environ["FLASK_SECRET_KEY"] = "test-secret"
from src.app import app, create_app
from src.data_tools.database_utils import ensure_db_schema
from src.data_tools.db_init import db
create_app()
with app.app_context():
    db.create_all()
    ensure_db_schema(os.environ["LLMTOOLS_DB_PATH"])
    response = app.test_client().get("/")
    assert response.status_code == 200
""".format(db_path=db_path)

    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    result = subprocess.run(
        [sys.executable, "-c", code],
        check=False,
        env=env,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
