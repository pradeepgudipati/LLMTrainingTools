import csv
import json
import re

ALLOWED_ROLES = {"system", "user", "assistant", "tool"}
HF_ROLE_MAP = {
    "human": "user",
    "user": "user",
    "gpt": "assistant",
    "assistant": "assistant",
    "system": "system",
    "tool": "tool",
}
MAX_EXAMPLE_BYTES = 100_000
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{20,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"(api[_-]?key|secret|token|password)\s*[:=])",
    re.IGNORECASE,
)
CSV_REQUIRED_HEADERS = {"question", "answer"}


def empty_result(line_number, message, dataset_type="unknown"):
    return {
        "dataset_type": dataset_type,
        "question": "",
        "answer": "",
        "payload": {},
        "errors": [message],
        "warnings": [],
        "line_number": line_number,
    }


def load_jsonl(path):
    records = []
    with open(path, "r", encoding="utf-8-sig") as input_file:
        for line_number, line in enumerate(input_file, start=1):
            if line.strip():
                records.append((line_number, json.loads(line)))
    return records


def normalize_record(record):
    if "messages" in record:
        return normalize_messages_record(record)
    if "conversations" in record:
        return normalize_hf_conversations_record(record)
    if "instruction" in record and ("output" in record or "response" in record):
        return normalize_instruction_record(record)
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
        tool_calls = message.get("tool_calls") if isinstance(message, dict) else None
        if role not in ALLOWED_ROLES:
            errors.append(f"messages[{index}].role is invalid.")
        if content in (None, "") and not tool_calls:
            errors.append(f"messages[{index}].content is empty.")
        if role == "user":
            user_messages.append(str(content or ""))
        if role == "assistant":
            assistant_messages.append(str(content or ""))
    if not user_messages:
        errors.append("messages must include at least one user message.")
    if not assistant_messages:
        errors.append("messages must include at least one assistant message.")

    return with_common_warnings({
        "dataset_type": "chat",
        "question": "\n".join(user_messages).strip(),
        "answer": "\n".join(assistant_messages).strip(),
        "payload": record,
        "errors": errors,
        "warnings": [],
    })


def normalize_hf_conversations_record(record):
    conversations = record.get("conversations", [])
    errors = []
    messages = []
    if not isinstance(conversations, list) or not conversations:
        errors.append("conversations must be a non-empty list.")

    for index, turn in enumerate(conversations):
        if not isinstance(turn, dict):
            errors.append(f"conversations[{index}] must be an object.")
            continue
        source_role = turn.get("from") or turn.get("role")
        content = turn.get("value") if "value" in turn else turn.get("content")
        role = HF_ROLE_MAP.get(str(source_role).lower()) if source_role else None
        if not role:
            errors.append(f"conversations[{index}].from is invalid.")
            role = str(source_role or "")
        messages.append({"role": role, "content": content})

    normalized = normalize_messages_record({"messages": messages})
    normalized["payload"] = record
    normalized["errors"].extend(errors)
    return normalized


def normalize_instruction_record(record):
    prompt_parts = [str(record.get("instruction", "")).strip()]
    input_text = str(record.get("input", "")).strip()
    if input_text:
        prompt_parts.append(input_text)
    answer = record.get("output", record.get("response", ""))
    return normalize_qa_record("\n".join(part for part in prompt_parts if part), answer, record)


def normalize_preference_record(record):
    errors = []
    if not str(record.get("prompt", "")).strip():
        errors.append("Prompt is empty.")
    if not str(record.get("chosen", "")).strip():
        errors.append("Chosen answer is empty.")
    if not str(record.get("rejected", "")).strip():
        errors.append("Rejected answer is empty.")
    if str(record.get("chosen", "")).strip() == str(record.get("rejected", "")).strip():
        errors.append("Chosen and rejected answers are identical.")
    return with_common_warnings({
        "dataset_type": "preference",
        "question": str(record.get("prompt", "")).strip(),
        "answer": str(record.get("chosen", "")).strip(),
        "payload": record,
        "errors": errors,
        "warnings": [],
    })


def normalize_tool_record(record):
    if "messages" in record:
        normalized = normalize_messages_record(record)
    else:
        tool_payload = record.get("tool_calls") or record.get("tools") or []
        errors = []
        if not tool_payload:
            errors.append("Tool trace must include tool_calls or tools.")
        normalized = {
            "dataset_type": "tool_trace",
            "question": str(record.get("prompt", "Tool trace")).strip() or "Tool trace",
            "answer": json.dumps(tool_payload, ensure_ascii=False),
            "payload": record,
            "errors": errors,
            "warnings": [],
        }
    normalized["dataset_type"] = "tool_trace"
    normalized["payload"] = record
    return with_common_warnings(normalized)


def normalize_rag_record(record):
    errors = []
    if not str(record.get("text", "")).strip():
        errors.append("RAG chunk text is empty.")
    return with_common_warnings({
        "dataset_type": "rag_chunk",
        "question": str(record.get("metadata", {}).get("source", "RAG chunk")).strip(),
        "answer": str(record.get("text", "")).strip(),
        "payload": record,
        "errors": errors,
        "warnings": [],
    })


def normalize_eval_record(record):
    question = record.get("question") or record.get("input") or record.get("prompt") or ""
    answer = record.get("expected_answer") or record.get("answer") or record.get("rubric") or ""
    errors = []
    if not str(question).strip():
        errors.append("Eval question/input is empty.")
    if not str(answer).strip():
        errors.append("Eval expected answer/rubric is empty.")
    return with_common_warnings({
        "dataset_type": "eval",
        "question": str(question).strip(),
        "answer": str(answer).strip(),
        "payload": record,
        "errors": errors,
        "warnings": [],
    })


def normalize_qa_record(question, answer, source_payload=None):
    errors = []
    if not str(question).strip():
        errors.append("Question is empty.")
    if not str(answer).strip():
        errors.append("Answer is empty.")
    payload = source_payload or {
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
    if len(serialized.encode("utf-8")) > MAX_EXAMPLE_BYTES:
        normalized["warnings"].append("Example is over 100KB.")
    if EMAIL_RE.search(serialized):
        normalized["warnings"].append("Potential PII email detected.")
    if PHONE_RE.search(serialized):
        normalized["warnings"].append("Potential PII phone number detected.")
    if SSN_RE.search(serialized):
        normalized["warnings"].append("Potential PII SSN detected.")
    if SECRET_RE.search(serialized):
        normalized["warnings"].append("Potential secret-like key detected.")
    return normalized


def validate_jsonl_records(path):
    seen_questions = {}
    results = []
    try:
        with open(path, "r", encoding="utf-8-sig") as input_file:
            for line_number, line in enumerate(input_file, start=1):
                if not line.strip():
                    continue
                try:
                    normalized = normalize_record(json.loads(line))
                except json.JSONDecodeError as error:
                    normalized = empty_result(line_number, f"Line is not valid JSON: {error.msg}.")
                add_duplicate_warning(normalized, seen_questions, line_number)
                normalized["line_number"] = line_number
                results.append(normalized)
    except UnicodeDecodeError as error:
        return [empty_result(0, f"File is not valid UTF-8: {error.reason}.")]
    return results


def validate_csv_records(path):
    results = []
    seen_questions = {}
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as input_file:
            reader = csv.DictReader(input_file)
            if not reader.fieldnames:
                return [empty_result(1, "CSV file is missing a header row.", "csv")]
            header_map = {header.strip().lower(): header for header in reader.fieldnames if header}
            missing_headers = sorted(CSV_REQUIRED_HEADERS - set(header_map))
            if missing_headers:
                actual_headers = ", ".join(reader.fieldnames)
                return [
                    empty_result(
                        1,
                        "CSV headers must include Question and Answer. "
                        f"Missing: {', '.join(missing_headers)}. Found: {actual_headers}.",
                        "csv",
                    )
                ]

            for row_number, row in enumerate(reader, start=2):
                normalized = normalize_qa_record(row.get(header_map["question"], ""), row.get(header_map["answer"], ""))
                add_duplicate_warning(normalized, seen_questions, row_number)
                normalized["dataset_type"] = "csv"
                normalized["line_number"] = row_number
                results.append(normalized)
    except UnicodeDecodeError as error:
        return [empty_result(0, f"File is not valid UTF-8: {error.reason}.", "csv")]
    except csv.Error as error:
        return [empty_result(0, f"CSV parsing failed: {error}.", "csv")]
    return results


def add_duplicate_warning(normalized, seen_questions, line_number):
    question_key = normalized["question"].strip().lower()
    if question_key:
        if question_key in seen_questions:
            normalized["warnings"].append(
                f"Duplicate question also appears on line {seen_questions[question_key]}."
            )
        else:
            seen_questions[question_key] = line_number


def build_validation_report(path, file_type=None):
    file_type = (file_type or str(path).rsplit(".", 1)[-1]).lower()
    if file_type == "jsonl":
        records = validate_jsonl_records(path)
    elif file_type == "csv":
        records = validate_csv_records(path)
    else:
        records = [empty_result(0, "Only CSV and JSONL files are supported.")]

    issues = []
    for result in records:
        for message in result["errors"]:
            issues.append({
                "severity": "error",
                "line_number": result["line_number"],
                "dataset_type": result["dataset_type"],
                "message": message,
            })
        for message in result["warnings"]:
            issues.append({
                "severity": "warning",
                "line_number": result["line_number"],
                "dataset_type": result["dataset_type"],
                "message": message,
            })

    error_count = sum(1 for issue in issues if issue["severity"] == "error")
    warning_count = sum(1 for issue in issues if issue["severity"] == "warning")
    valid_examples = sum(1 for result in records if not result["errors"])
    return {
        "status": "valid" if records and error_count == 0 else "invalid",
        "file_type": file_type,
        "total_examples": len(records),
        "valid_examples": valid_examples,
        "invalid_examples": len(records) - valid_examples,
        "error_count": error_count,
        "warning_count": warning_count,
        "issues": issues,
    }


def validate_jsonl_file(path):
    results = validate_jsonl_records(path)
    return bool(results) and all(not result["errors"] for result in results)


def validate_csv_file(path):
    results = validate_csv_records(path)
    return bool(results) and all(not result["errors"] for result in results)
