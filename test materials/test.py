
import json
import csv

# Read JSON file
with open('sales_data.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# If your JSON has a nested list inside (like "users"), extract it:
if isinstance(data, dict):
    # Replace 'users' with the actual key name inside your JSON
    data = data[list(data.keys())[0]]

# Now write CSV
with open('sal_data.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)

