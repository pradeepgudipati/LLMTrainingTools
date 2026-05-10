import csv
import json
import re

ALLOWED_ROLES = {"system", "user", "assistant", "tool"}
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
SECRET_RE = re.compile(r"(api[_-]?key|secret|token|password)\s*[:=]", re.IGNORECASE)


def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if line.strip():
                records.append((line_number, json.loads(line)))
    return records


def normalize_record(record):
    if "messages" in record:
        return normalize_messages_record(record)
    if {"prompt", "chosen", "rejected"}.issubset(record):
        return normalize_preference_record(record)
    if "tool_calls" in record or "tools" in record:
        return normalize_tool_record(record)
    if "text" in record and "metadata" in record:
        return normalize_rag_record(record)
    if "expected_answer" in record or "rubric" in record:
        return normalize_eval_record(record)
    if "Question" in record and "Answer" in record:
        return normalize_qa_record(record["Question"], record["Answer"])
    if "question" in record and "answer" in record:
        return normalize_qa_record(record["question"], record["answer"])

    return {
        "dataset_type": "unknown",
        "question": "",
        "answer": "",
        "payload": record,
        "errors": ["Unsupported JSONL shape."],
        "warnings": [],
    }


def normalize_messages_record(record):
    messages = record.get("messages", [])
    errors = []
    if not isinstance(messages, list) or not messages:
        errors.append("messages must be a non-empty list.")

    user_messages = []
    assistant_messages = []
    for index, message in enumerate(messages):
        role = message.get("role") if isinstance(message, dict) else None
        content = message.get("content") if isinstance(message, dict) else None
        if role not in ALLOWED_ROLES:
            errors.append(f"messages[{index}].role is invalid.")
        if content in (None, "") and not message.get("tool_calls"):
            errors.append(f"messages[{index}].content is empty.")
        if role == "user":
            user_messages.append(str(content or ""))
        if role == "assistant":
            assistant_messages.append(str(content or ""))

    return with_common_warnings({
        "dataset_type": "chat",
        "question": "\n".join(user_messages).strip(),
        "answer": "\n".join(assistant_messages).strip(),
        "payload": record,
        "errors": errors,
        "warnings": [],
    })


def normalize_preference_record(record):
    return with_common_warnings({
        "dataset_type": "preference",
        "question": str(record.get("prompt", "")).strip(),
        "answer": str(record.get("chosen", "")).strip(),
        "payload": record,
        "errors": [],
        "warnings": [],
    })


def normalize_tool_record(record):
    normalized = normalize_messages_record(record) if "messages" in record else normalize_qa_record("", "")
    normalized["dataset_type"] = "tool_trace"
    normalized["payload"] = record
    return with_common_warnings(normalized)


def normalize_rag_record(record):
    return with_common_warnings({
        "dataset_type": "rag_chunk",
        "question": str(record.get("metadata", {}).get("source", "RAG chunk")).strip(),
        "answer": str(record.get("text", "")).strip(),
        "payload": record,
        "errors": [],
        "warnings": [],
    })


def normalize_eval_record(record):
    question = record.get("question") or record.get("input") or record.get("prompt") or ""
    answer = record.get("expected_answer") or record.get("answer") or record.get("rubric") or ""
    return with_common_warnings({
        "dataset_type": "eval",
        "question": str(question).strip(),
        "answer": str(answer).strip(),
        "payload": record,
        "errors": [],
        "warnings": [],
    })


def normalize_qa_record(question, answer):
    errors = []
    if not str(question).strip():
        errors.append("Question is empty.")
    if not str(answer).strip():
        errors.append("Answer is empty.")
    payload = {
        "messages": [
            {"role": "user", "content": str(question).strip()},
            {"role": "assistant", "content": str(answer).strip()},
        ]
    }
    return with_common_warnings({
        "dataset_type": "chat",
        "question": str(question).strip(),
        "answer": str(answer).strip(),
        "payload": payload,
        "errors": errors,
        "warnings": [],
    })


def with_common_warnings(normalized):
    serialized = json.dumps(normalized["payload"], ensure_ascii=False)
    if len(serialized) > 100_000:
        normalized["warnings"].append("Example is over 100KB.")
    if EMAIL_RE.search(serialized):
        normalized["warnings"].append("Potential PII email detected.")
    if SECRET_RE.search(serialized):
        normalized["warnings"].append("Potential secret-like key detected.")
    return normalized


def validate_jsonl_records(path):
    records = load_jsonl(path)
    seen_questions = {}
    results = []
    for line_number, record in records:
        normalized = normalize_record(record)
        question_key = normalized["question"].strip().lower()
        if question_key:
            if question_key in seen_questions:
                normalized["warnings"].append(
                    f"Duplicate question also appears on line {seen_questions[question_key]}."
                )
            else:
                seen_questions[question_key] = line_number
        normalized["line_number"] = line_number
        results.append(normalized)
    return results


def validate_jsonl_file(path):
    try:
        results = validate_jsonl_records(path)
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    return bool(results) and all(not result["errors"] for result in results)


def validate_csv_file(path):
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as input_file:
            reader = csv.DictReader(input_file)
            if not reader.fieldnames:
                return False
            normalized_headers = {header.strip().lower() for header in reader.fieldnames}
            if not {"question", "answer"}.issubset(normalized_headers):
                return False
            return all(row.get("Question") or row.get("question") for row in reader)
    except (UnicodeDecodeError, csv.Error):
        return False
