import json

from src.data_tools.import_utils.csv_to_jsonl import convert_single_csv_to_jsonl


def test_csv_to_jsonl_converts_question_answer_rows(tmp_path):
    csv_path = tmp_path / "sample.csv"
    jsonl_path = tmp_path / "out" / "training_data.jsonl"
    csv_path.write_text(
        "Question,Answer\n"
        "What is uv?,A Python package and project manager.\n",
        encoding="utf-8",
    )

    convert_single_csv_to_jsonl(csv_path, jsonl_path)

    rows = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines()]
    assert rows == [
        {
            "messages": [
                {"role": "user", "content": "What is uv?"},
                {"role": "assistant", "content": "A Python package and project manager."},
            ]
        }
    ]
