import csv
import json
import os


# Process CSV file and convert to JSONL
def process_csv_file(csv_file, all_data):
    """
    Process a CSV file and convert to JSONL
    :param csv_file: csv file path
    :param all_data: data
    :return: None
    """
    with open(csv_file, "r", encoding="utf-8") as csv_input:
        csv_reader = csv.DictReader(csv_input)
        for row in csv_reader:
            prompt = row.get("question", "").strip()
            completion = row.get("answer", "").strip()

            if not prompt or not completion:
                print(f"Skipped row due to empty content: {row}")
                continue

            each_line_json_obj = {
                "messages": [
                    {"role": "user", "content": prompt},
                    {"role": "assistant", "content": completion},
                ]
            }
            all_data.append(each_line_json_obj)


# Convert a single CSV to JSONL
def convert_single_csv_to_jsonl(csv_file, output_jsonl_file):
    """
    Convert a single CSV file to JSONL
    :param csv_file: the CSV file
    :param output_jsonl_file: the JSONL file
    :return: None
    """
    all_data = []
    process_csv_file(csv_file, all_data)
    write_to_jsonl(all_data, output_jsonl_file)


# Convert all CSV files in a folder to JSONL
def convert_folder_csv_to_jsonl(csv_folder_path, output_jsonl_file):
    """
    Convert all CSV files in a folder to JSONL
    :param csv_folder_path: The folder containing the CSV files
    :param output_jsonl_file: the output JSONL file
    :return: none
    """
    all_data = []

    for filename in os.listdir(csv_folder_path):
        print(f"Processing -- {filename}")
        if filename.endswith(".csv"):
            csv_file = os.path.join(csv_folder_path, filename)
            process_csv_file(csv_file, all_data)

    write_to_jsonl(all_data, output_jsonl_file)


def write_to_jsonl(data, output_file):
    """
    Write the data to a JSONL file
    :param data: data to write
    :param output_file: the output JSONL file path
    :return:
    """
    with open(output_file, "w", encoding="utf-8") as jsonl_output:
        for each_data in data:
            jsonl_output.write(json.dumps(each_data) + "\n")

# # Paths
# csv_files_path = "./docs"
# output_jsonl_file = "training_data.jsonl"
# # Uncomment the line below to process a single CSV file
# # convert_single_csv_to_jsonl(csv_file_path, output_jsonl_file)
#
# # Uncomment the line below to process all CSV files in a folder
# # convert_folder_csv_to_jsonl(csv_files_path, output_jsonl_file)
# print(
#     f"Finished converting all CSV files in path --  {csv_files_path}  to JSONL: {output_jsonl_file}"
# )
