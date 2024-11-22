import json
import os
import csv


def save_to_json(file_path, data):
    with open(file_path, "w") as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)


def load_json(file_path):
    with open(file_path, "r") as json_file:
        data = json.load(json_file)
        return data


def merge_json_files(directory, output_file):
    merged_data = []

    # Iterate over files in the directory
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)

            with open(filepath, "r") as file:
                data = json.load(file)
                # Merge data
                merged_data.extend(data)

    # Write merged data to output file
    with open(output_file, "w") as outfile:
        json.dump(merged_data, outfile, indent=4)


def convert_to_csv(data: [], path, field_names):
    if not data:
        print("No objects provided. CSV file not created.")
        return

    # Extract fieldnames from the keys of the first object (assuming all objects have identical keys)
    fieldnames = field_names if field_names else list(data[0].keys())

    with open(path, mode="w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        # Write header
        writer.writeheader()

        # Write each object as a row in the CSV
        for obj in data:
            writer.writerow(obj)

    print(f"CSV file '{path}' has been created successfully.")
