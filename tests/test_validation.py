import json

from src.data_tools.dataset_validation import validate_csv_file, validate_jsonl_records


def write_jsonl(path, records):
    path.write_text(
        "\n".join(json.dumps(record) for record in records) + "\n",
        encoding="utf-8",
    )


def test_validation_detects_empty_answer_duplicate_bad_role_pii_and_secret(tmp_path):
    jsonl_path = tmp_path / "bad.jsonl"
    write_jsonl(
        jsonl_path,
        [
            {"messages": [{"role": "user", "content": "Same?"}, {"role": "assistant", "content": ""}]},
            {"messages": [{"role": "customer", "content": "Same?"}, {"role": "assistant", "content": "Ok"}]},
            {"Question": "Email?", "Answer": "Contact user@example.com. api_key=abc"},
            {"Question": "Email?", "Answer": "Duplicate"},
        ],
    )

    results = validate_jsonl_records(jsonl_path)

    assert "messages[1].content is empty." in results[0]["errors"]
    assert "messages[0].role is invalid." in results[1]["errors"]
    assert "Potential PII email detected." in results[2]["warnings"]
    assert "Potential secret-like key detected." in results[2]["warnings"]
    assert any("Duplicate question" in warning for warning in results[3]["warnings"])


def test_validation_rejects_bad_csv_headers(tmp_path):
    csv_path = tmp_path / "bad.csv"
    csv_path.write_text("prompt,response\nHello,World\n", encoding="utf-8")

    assert validate_csv_file(csv_path) is False
