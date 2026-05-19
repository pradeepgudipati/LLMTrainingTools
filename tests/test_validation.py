import json

from src.data_tools.dataset_validation import build_validation_report, validate_csv_file, validate_jsonl_records


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


def test_validation_report_surfaces_jsonl_parse_encoding_and_length_issues(tmp_path):
    jsonl_path = tmp_path / "mixed.jsonl"
    long_answer = "x" * 100_001
    jsonl_path.write_text(
        "\n".join([
            json.dumps({"Question": "Long?", "Answer": long_answer}),
            '{"messages": [{"role": "user", "content": "Broken"}]',
        ]),
        encoding="utf-8",
    )

    report = build_validation_report(jsonl_path, "jsonl")

    assert report["status"] == "invalid"
    assert report["total_examples"] == 2
    assert any(issue["severity"] == "warning" and "over 100KB" in issue["message"] for issue in report["issues"])
    assert any(issue["severity"] == "error" and "not valid JSON" in issue["message"] for issue in report["issues"])

    invalid_encoding_path = tmp_path / "latin1.jsonl"
    invalid_encoding_path.write_bytes('{"Question":"Olá","Answer":"Mundo"}\n'.encode("latin-1"))

    encoding_report = build_validation_report(invalid_encoding_path, "jsonl")

    assert encoding_report["status"] == "invalid"
    assert any("not valid UTF-8" in issue["message"] for issue in encoding_report["issues"])


def test_validation_supports_hf_conversations_and_instruction_records(tmp_path):
    jsonl_path = tmp_path / "hf.jsonl"
    write_jsonl(
        jsonl_path,
        [
            {
                "conversations": [
                    {"from": "human", "value": "What is JSONL?"},
                    {"from": "gpt", "value": "One JSON object per line."},
                ]
            },
            {"instruction": "Summarize", "input": "JSONL", "output": "Line-delimited JSON."},
        ],
    )

    results = validate_jsonl_records(jsonl_path)

    assert [result["dataset_type"] for result in results] == ["chat", "chat"]
    assert all(not result["errors"] for result in results)
    assert results[0]["question"] == "What is JSONL?"
    assert results[1]["question"] == "Summarize\nJSONL"


def test_validation_report_surfaces_csv_header_and_row_errors(tmp_path):
    bad_header_path = tmp_path / "bad_headers.csv"
    bad_header_path.write_text("prompt,response\nHello,World\n", encoding="utf-8")

    bad_header_report = build_validation_report(bad_header_path, "csv")

    assert bad_header_report["status"] == "invalid"
    assert any("CSV headers must include Question and Answer" in issue["message"] for issue in bad_header_report["issues"])

    bad_row_path = tmp_path / "bad_rows.csv"
    bad_row_path.write_text("Question,Answer\nQuestion one,\nQuestion one,Answer two\n", encoding="utf-8")

    bad_row_report = build_validation_report(bad_row_path, "csv")

    assert bad_row_report["status"] == "invalid"
    assert any(issue["message"] == "Answer is empty." for issue in bad_row_report["issues"])
    assert any("Duplicate question" in issue["message"] for issue in bad_row_report["issues"])
