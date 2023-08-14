import json
from datetime import datetime

import requests

# URL of the API
api_url = "https://endoflife.date/api/python.json"

# Send a GET request to the API
response = requests.get(api_url)

# Parse the JSON response
data = json.loads(response.content)

# Initialize an empty list to store the processed data
processed_data = []

# Iterate over the entries in the API response
for entry in data:
    raw_version = entry["latest"]
    # Strip out the patch part of the version
    major_minor_parts = raw_version.split(".")[:2]
    parsed_version = ".".join(major_minor_parts)

    # Convert end_of_life to datetime object
    end_of_life_date = datetime.strptime(entry["eol"], "%Y-%m-%d").date()

    # Create a new dictionary for the entry data
    entry_data = {"Version": parsed_version, "End of Life": end_of_life_date}

    # Append the entry data to the list
    processed_data.append(entry_data)

# Convert the processed data list to JSON format
json_data = json.dumps(processed_data, indent=4, default=str)

# Print the JSON data
print(json_data)
