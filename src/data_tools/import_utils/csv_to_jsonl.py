import csv
import json
import os

from ..dataset_validation import normalize_qa_record


def process_csv_file(csv_file):
    """
    Process a CSV file and convert valid Question/Answer rows to chat JSONL payloads.
    """
    all_data = []
    with open(csv_file, "r", encoding="utf-8-sig", newline="") as csv_input:
        csv_reader = csv.DictReader(csv_input)
        for row in csv_reader:
            prompt = row.get("Question", row.get("question", "")).strip()
            completion = row.get("Answer", row.get("answer", "")).strip()
            normalized = normalize_qa_record(prompt, completion)

            if normalized["errors"]:
                print(f"Skipped row due to empty content: {row}")
                continue

            all_data.append(normalized["payload"])
    return all_data


def convert_single_csv_to_jsonl(csv_file, output_jsonl_path):
    all_data = process_csv_file(csv_file)
    write_to_jsonl(all_data, output_jsonl_path)


def convert_folder_csv_to_jsonl(csv_folder_path, output_jsonl_file):
    all_data = []
    for filename in os.listdir(csv_folder_path):
        print(f"Processing -- {filename}")
        if filename.endswith(".csv"):
            csv_file = os.path.join(csv_folder_path, filename)
            all_data.extend(process_csv_file(csv_file))

    write_to_jsonl(all_data, output_jsonl_file)


def write_to_jsonl(data, output_file_path):
    if os.path.exists(output_file_path):
        os.remove(output_file_path)

    os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
    with open(output_file_path, "w", encoding="utf-8") as jsonl_output:
        for each_data in data:
            jsonl_output.write(json.dumps(each_data, ensure_ascii=False) + "\n")
