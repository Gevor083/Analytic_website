import json
import csv
import os

def convert_json_to_csv(json_file_path, csv_file_path=None):
    """
    Convert JSON file to CSV format.

    Args:
        json_file_path (str): Path to the JSON file
        csv_file_path (str, optional): Path for the output CSV file. If not provided,
                                      will use the JSON filename with .csv extension

    Returns:
        str: Path to the created CSV file
    """
    if csv_file_path is None:
        csv_file_path = os.path.splitext(json_file_path)[0] + '.csv'

    # Read JSON file
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Handle different JSON structures
    if isinstance(data, list):
        if len(data) == 0:
            # Empty list - create empty CSV
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([])  # Empty header
        else:
            # List of objects
            with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
    elif isinstance(data, dict):
        # Single object - convert to list
        data = [data]
        with open(csv_file_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
    else:
        raise ValueError(f"Unsupported JSON structure: {type(data)}")

    return csv_file_path

if __name__ == "__main__":
    # Example usage
    json_files = [
        'test materials/test_files/valid_array.json',
        'test materials/test_files/valid_single_object.json',
        'test materials/test_files/empty_data.json'
    ]

    for json_file in json_files:
        try:
            csv_file = convert_json_to_csv(json_file)
            print(f"Converted {json_file} to {csv_file}")
        except Exception as e:
            print(f"Error converting {json_file}: {e}")
