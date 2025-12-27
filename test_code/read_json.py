import json


# Function to read JSON data from file "test.json"

if __name__ == "__main__":
    print("Reading JSON data from test.json")
    data = None
    with open("test.json", "r") as f:
        data = json.load(f)
    
    # Get the list of item names from the JSON data
    items_list = []
    if "value" in data:
        items_list = [item["name"] for item in data["value"]]
    print("Items List:", items_list)