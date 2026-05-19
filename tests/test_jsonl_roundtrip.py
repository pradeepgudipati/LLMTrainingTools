import json
import sqlite3

from src.data_tools.import_utils.db_to_jsonl import sqlite_to_jsonl
from src.data_tools.import_utils.jsonl_to_sqllite import import_jsonl_to_sqlite


def test_jsonl_import_export_roundtrip_preserves_supported_shapes(tmp_path):
    jsonl_path = tmp_path / "input.jsonl"
    db_path = tmp_path / "training.db"
    exported_path = tmp_path / "exported.jsonl"
    records = [
        {
            "messages": [
                {"role": "system", "content": "Answer briefly."},
                {"role": "user", "content": "What is JSONL?"},
                {"role": "assistant", "content": "One JSON object per line."},
            ]
        },
        {"prompt": "Pick A or B", "chosen": "A", "rejected": "B"},
        {"text": "Chunk body", "metadata": {"source": "doc-1", "page": 4}},
        {"question": "Score this answer", "expected_answer": "Correct", "rubric": "Exact match"},
    ]
    jsonl_path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    lines_read, inserted = import_jsonl_to_sqlite(jsonl_path, db_path)
    assert (lines_read, inserted) == (4, 4)

    conn = sqlite3.connect(db_path)
    rows = conn.execute("SELECT dataset_type, question, answer FROM messages").fetchall()
    conn.close()
    assert [row[0] for row in rows] == ["chat", "preference", "rag_chunk", "eval"]

    assert sqlite_to_jsonl(db_path, exported_path, "messages") is True
    exported_records = [
        json.loads(line) for line in exported_path.read_text(encoding="utf-8").splitlines()
    ]
    assert exported_records == records
