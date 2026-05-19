import sqlite3

from src.data_tools.database_utils import backup_db, restore_db


def test_backup_and_restore_db(tmp_path):
    db_path = tmp_path / "training.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE messages (id INTEGER PRIMARY KEY, question TEXT, answer TEXT)")
    conn.execute("INSERT INTO messages (question, answer) VALUES ('q1', 'a1')")
    conn.commit()
    conn.close()

    backup_path = backup_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.execute("UPDATE messages SET answer = 'changed'")
    conn.commit()
    conn.close()

    restore_db(db_path, backup_path)

    conn = sqlite3.connect(db_path)
    restored_answer = conn.execute("SELECT answer FROM messages").fetchone()[0]
    conn.close()
    assert restored_answer == "a1"
