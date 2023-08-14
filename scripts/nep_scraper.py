import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

# URL of the table to scrape
url = "https://numpy.org/neps/nep-0029-deprecation_policy.html#support-table"

# Send a GET request to the URL
response = requests.get(url)

# Create a BeautifulSoup object with the response content
soup = BeautifulSoup(response.content, "html.parser")

# Find the table element
table = soup.find("table")

# Initialize an empty list to store the table data
data = []

# Iterate over the rows of the table, skipping the header row
for row in table.find_all("tr")[1:]:
    # Extract the columns of each row
    columns = row.find_all("td")
    end_of_life = columns[0].text.strip()
    version = columns[1].text.strip().rstrip("+")
    # Parse the version number and reduce the minor version by 1
    version_number = version.split(".")
    version_number[-1] = str(int(version_number[-1]) - 1)
    parsed_version = ".".join(version_number)

    # Convert end_of_life to datetime object
    end_of_life_date = datetime.strptime(end_of_life, "%b %d, %Y").date()

    # Check if the version already exists in the data list
    existing_data = next((d for d in data if d["Version"] == parsed_version), None)

    if existing_data:
        # Update the existing data with the minimum end_of_life_date
        existing_data["End of Life"] = min(
            existing_data["End of Life"],
            end_of_life_date,
        )
    else:
        # Create a new dictionary for the row data
        row_data = {"Version": parsed_version, "End of Life": end_of_life_date}

        # Append the row data to the list
        data.append(row_data)

# Convert the data list to JSON format
json_data = json.dumps(data, indent=4, default=str)

# Print the JSON data
print(json_data)
