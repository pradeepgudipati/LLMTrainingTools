import json

from src.data_tools.dataset_validation import validate_csv_records, validate_jsonl_records


def test_duplicate_detection_warns_for_repeated_csv_questions(tmp_path):
    csv_path = tmp_path / "duplicates.csv"
    csv_path.write_text(
        "Question,Answer\n"
        "What is JSONL?,One JSON object per line.\n"
        " what is jsonl? ,Case and whitespace should not hide duplicates.\n",
        encoding="utf-8",
    )

    results = validate_csv_records(csv_path)

    assert results[0]["warnings"] == []
    assert results[1]["warnings"] == ["Duplicate question also appears on line 2."]


def test_duplicate_detection_warns_for_repeated_jsonl_questions(tmp_path):
    jsonl_path = tmp_path / "duplicates.jsonl"
    records = [
        {"Question": "What is JSONL?", "Answer": "One JSON object per line."},
        {"Question": " what is jsonl? ", "Answer": "Case and whitespace should not hide duplicates."},
    ]
    jsonl_path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )

    results = validate_jsonl_records(jsonl_path)

    assert results[0]["warnings"] == []
    assert results[1]["warnings"] == ["Duplicate question also appears on line 1."]
